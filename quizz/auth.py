"""Comptes utilisateurs : inscription, connexion, hachage des mots de passe (US01, US02, V2 sécurité).

Hachage : PBKDF2-HMAC-SHA256, 600 000 itérations (recommandation OWASP), sel aléatoire de 16 octets.
Format stocké : « pbkdf2$<itérations>$<sel>$<hash> ». L'ancien format v2.0 « <sel>$<hash> »
(100 000 itérations) reste lisible et est re-haché au prochain login réussi, sans rien demander.
"""
import hashlib
import hmac
import os
import re
import sqlite3

from .models import Utilisateur

ITERATIONS = 600_000
ITERATIONS_V20 = 100_000
MDP_ADMIN_DEFAUT = "admin"
LOGIN_VALIDE = re.compile(r"^[A-Za-z0-9_.-]{3,30}$")


class ErreurAuth(Exception):
    """Erreur métier liée aux comptes (login pris, mauvais mot de passe…)."""


def _pbkdf2(mot_de_passe: str, sel: str, iterations: int) -> str:
    return hashlib.pbkdf2_hmac("sha256", mot_de_passe.encode(), sel.encode(), iterations).hex()


def hacher(mot_de_passe: str, sel: str | None = None, iterations: int = ITERATIONS) -> str:
    """Le mot de passe n'est JAMAIS stocké en clair."""
    sel = sel or os.urandom(16).hex()
    return f"pbkdf2${iterations}${sel}${_pbkdf2(mot_de_passe, sel, iterations)}"


def verifier(mot_de_passe: str, stocke: str) -> bool:
    morceaux = stocke.split("$")
    if len(morceaux) == 4 and morceaux[0] == "pbkdf2":
        _, iterations, sel, attendu = morceaux
        calcule = _pbkdf2(mot_de_passe, sel, int(iterations))
    elif len(morceaux) == 2:  # format v2.0
        sel, attendu = morceaux
        calcule = _pbkdf2(mot_de_passe, sel, ITERATIONS_V20)
    else:
        return False
    return hmac.compare_digest(calcule, attendu)


def doit_rehacher(stocke: str) -> bool:
    return not stocke.startswith(f"pbkdf2${ITERATIONS}$")


def verifier_regles_mot_de_passe(mot_de_passe: str) -> None:
    if len(mot_de_passe) < 8:
        raise ErreurAuth("Le mot de passe doit contenir au moins 8 caractères.")
    if not re.search(r"[A-Za-z]", mot_de_passe) or not re.search(r"\d", mot_de_passe):
        raise ErreurAuth("Le mot de passe doit contenir au moins une lettre et un chiffre.")


def _verifier_login(login: str) -> str:
    login = login.strip()
    if not LOGIN_VALIDE.match(login):
        raise ErreurAuth("Le login doit faire 3 à 30 caractères : lettres, chiffres, « . », « _ » ou « - ».")
    return login


def _inserer(con, login: str, hash_: str, est_admin: bool) -> Utilisateur:
    # Unicité insensible à la casse : « Alice » et « alice » sont le même compte.
    if con.execute("SELECT 1 FROM utilisateur WHERE login = ? COLLATE NOCASE", (login,)).fetchone():
        raise ErreurAuth(f"Le login « {login} » est déjà utilisé.")
    try:
        with con:
            cur = con.execute("INSERT INTO utilisateur (login, mot_de_passe_hash, est_admin) VALUES (?, ?, ?)",
                              (login, hash_, int(est_admin)))
    except sqlite3.IntegrityError:
        raise ErreurAuth(f"Le login « {login} » est déjà utilisé.")
    return Utilisateur(cur.lastrowid, login, est_admin)


def inscrire(con: sqlite3.Connection, login: str, mot_de_passe: str, est_admin: bool = False) -> Utilisateur:
    login = _verifier_login(login)
    verifier_regles_mot_de_passe(mot_de_passe)
    return _inserer(con, login, hacher(mot_de_passe), est_admin)


def connecter(con: sqlite3.Connection, login: str, mot_de_passe: str) -> Utilisateur:
    row = con.execute("SELECT * FROM utilisateur WHERE login = ? COLLATE NOCASE", (login.strip(),)).fetchone()
    if row is None:
        hacher(mot_de_passe)  # même durée que pour un vrai compte : on ne révèle pas si le login existe
        raise ErreurAuth("Login ou mot de passe incorrect.")
    if not verifier(mot_de_passe, row["mot_de_passe_hash"]):
        raise ErreurAuth("Login ou mot de passe incorrect.")
    if doit_rehacher(row["mot_de_passe_hash"]):
        with con:
            con.execute("UPDATE utilisateur SET mot_de_passe_hash = ? WHERE id_utilisateur = ?",
                        (hacher(mot_de_passe), row["id_utilisateur"]))
    return Utilisateur(row["id_utilisateur"], row["login"], bool(row["est_admin"]), row["date_creation"])


def creer_admin_par_defaut(con: sqlite3.Connection, login: str = "admin",
                           mot_de_passe: str = MDP_ADMIN_DEFAUT) -> None:
    """Crée un compte admin au premier lancement s'il n'existe aucun admin.

    Son mot de passe (trop faible exprès) devra être changé à la première connexion (US15).
    """
    if con.execute("SELECT 1 FROM utilisateur WHERE est_admin = 1").fetchone() is None:
        _inserer(con, login, hacher(mot_de_passe), True)


def creer_compte_demo(con: sqlite3.Connection, login: str, mot_de_passe: str) -> Utilisateur:
    """Joueurs de démonstration (option --demo) : mot de passe court accepté, jamais via l'API."""
    return _inserer(con, login, hacher(mot_de_passe), False)


# ---------------------------------------------------------------- mot de passe (US15, V2)
def utilise_mot_de_passe_par_defaut(con: sqlite3.Connection, user: Utilisateur) -> bool:
    """Vrai si cet administrateur a encore le mot de passe par défaut."""
    if not user.est_admin:
        return False
    row = con.execute("SELECT mot_de_passe_hash FROM utilisateur WHERE id_utilisateur = ?",
                      (user.id_utilisateur,)).fetchone()
    return row is not None and verifier(MDP_ADMIN_DEFAUT, row["mot_de_passe_hash"])


def changer_mot_de_passe(con: sqlite3.Connection, id_utilisateur: int, nouveau: str,
                         ancien: str | None = None) -> None:
    """`ancien` : exigé quand l'utilisateur change lui-même (pas quand un admin réinitialise)."""
    verifier_regles_mot_de_passe(nouveau)
    if ancien is not None:
        row = con.execute("SELECT mot_de_passe_hash FROM utilisateur WHERE id_utilisateur = ?",
                          (id_utilisateur,)).fetchone()
        if row is None or not verifier(ancien, row["mot_de_passe_hash"]):
            raise ErreurAuth("Mot de passe actuel incorrect.")
    with con:
        cur = con.execute("UPDATE utilisateur SET mot_de_passe_hash = ? WHERE id_utilisateur = ?",
                          (hacher(nouveau), id_utilisateur))
    if cur.rowcount == 0:
        raise ErreurAuth("Utilisateur introuvable.")


# ---------------------------------------------------------------- gestion des comptes par l'admin (V2)
def lister_utilisateurs(con: sqlite3.Connection) -> list[dict]:
    rows = con.execute(
        "SELECT u.id_utilisateur, u.login, u.est_admin, u.date_creation, COUNT(t.id_tentative) AS parties, "
        "       COALESCE(ROUND(100.0 * SUM(t.score) / NULLIF(SUM(t.nb_questions), 0)), 0) AS reussite "
        "FROM utilisateur u LEFT JOIN tentative t USING (id_utilisateur) WHERE u.supprime = 0 "
        "GROUP BY u.id_utilisateur ORDER BY u.est_admin DESC, u.login COLLATE NOCASE").fetchall()
    return [{"id": r["id_utilisateur"], "login": r["login"], "admin": bool(r["est_admin"]),
             "date": r["date_creation"], "parties": r["parties"], "reussite": int(r["reussite"])} for r in rows]


def _nb_admins(con) -> int:
    return con.execute("SELECT COUNT(*) FROM utilisateur WHERE est_admin = 1").fetchone()[0]


def modifier_utilisateur(con: sqlite3.Connection, id_utilisateur: int, login: str, est_admin: bool) -> None:
    login = _verifier_login(login)
    row = con.execute("SELECT est_admin FROM utilisateur WHERE id_utilisateur = ? AND supprime = 0",
                      (id_utilisateur,)).fetchone()
    if row is None:
        raise ErreurAuth("Utilisateur introuvable.")
    if row["est_admin"] and not est_admin and _nb_admins(con) <= 1:
        raise ErreurAuth("Impossible : il doit rester au moins un administrateur.")
    if con.execute("SELECT 1 FROM utilisateur WHERE login = ? COLLATE NOCASE AND id_utilisateur <> ?",
                   (login, id_utilisateur)).fetchone():
        raise ErreurAuth(f"Le login « {login} » est déjà utilisé.")
    with con:
        con.execute("UPDATE utilisateur SET login = ?, est_admin = ? WHERE id_utilisateur = ?",
                    (login, int(est_admin), id_utilisateur))


def supprimer_utilisateur(con: sqlite3.Connection, id_utilisateur: int) -> bool:
    """Supprime un compte (v2.2, W3). Renvoie True s'il a été anonymisé, False s'il a été effacé.

    Un compte qui a déjà joué est anonymisé : login remplacé, mot de passe inutilisable, plus admin,
    sessions et partie en cours retirées. Ses parties restent dans les statistiques, sans son nom, et il
    disparaît des classements et de la liste des comptes. Un compte qui n'a jamais joué est effacé.
    """
    row = con.execute("SELECT est_admin FROM utilisateur WHERE id_utilisateur = ? AND supprime = 0",
                      (id_utilisateur,)).fetchone()
    if row is None:
        raise ErreurAuth("Utilisateur introuvable.")
    if row["est_admin"] and _nb_admins(con) <= 1:
        raise ErreurAuth("Impossible : il doit rester au moins un administrateur.")
    a_joue = con.execute("SELECT 1 FROM tentative WHERE id_utilisateur = ?", (id_utilisateur,)).fetchone()
    with con:
        if not a_joue:
            con.execute("DELETE FROM utilisateur WHERE id_utilisateur = ?", (id_utilisateur,))
            return False
        # « ! » n'est jamais une empreinte valide : verifier() renvoie toujours False
        con.execute("UPDATE utilisateur SET login = ?, mot_de_passe_hash = '!', est_admin = 0, supprime = 1 "
                    "WHERE id_utilisateur = ?", (f"compte supprimé n°{id_utilisateur}", id_utilisateur))
        con.execute("DELETE FROM session WHERE id_utilisateur = ?", (id_utilisateur,))
        con.execute("DELETE FROM partie_en_cours WHERE id_utilisateur = ?", (id_utilisateur,))
        con.execute("DELETE FROM conversation_assistant WHERE id_utilisateur = ?", (id_utilisateur,))
        con.execute("UPDATE journal SET id_utilisateur = NULL WHERE id_utilisateur = ?", (id_utilisateur,))
    return True
