"""Comptes utilisateurs : inscription, connexion, hachage des mots de passe (US01, US02)."""
import hashlib
import hmac
import os
import sqlite3

from .models import Utilisateur

ITERATIONS = 100_000
MDP_ADMIN_DEFAUT = "admin"


class ErreurAuth(Exception):
    """Erreur métier liée aux comptes (login pris, mauvais mot de passe…)."""


def hacher(mot_de_passe: str, sel: str | None = None) -> str:
    """Renvoie 'sel$hash'. Le mot de passe n'est JAMAIS stocké en clair."""
    sel = sel or os.urandom(16).hex()
    h = hashlib.pbkdf2_hmac("sha256", mot_de_passe.encode(), sel.encode(), ITERATIONS).hex()
    return f"{sel}${h}"


def verifier(mot_de_passe: str, stocke: str) -> bool:
    sel, _ = stocke.split("$", 1)
    return hmac.compare_digest(hacher(mot_de_passe, sel), stocke)


def verifier_regles_mot_de_passe(mot_de_passe: str) -> None:
    if len(mot_de_passe) < 4:
        raise ErreurAuth("Le mot de passe doit contenir au moins 4 caractères.")


def inscrire(con: sqlite3.Connection, login: str, mot_de_passe: str, est_admin: bool = False) -> Utilisateur:
    login = login.strip()
    if len(login) < 3:
        raise ErreurAuth("Le login doit contenir au moins 3 caractères.")
    verifier_regles_mot_de_passe(mot_de_passe)
    try:
        cur = con.execute(
            "INSERT INTO utilisateur (login, mot_de_passe_hash, est_admin) VALUES (?, ?, ?)",
            (login, hacher(mot_de_passe), int(est_admin)),
        )
        con.commit()
    except sqlite3.IntegrityError:
        raise ErreurAuth(f"Le login « {login} » est déjà utilisé.")
    return Utilisateur(cur.lastrowid, login, est_admin)


def connecter(con: sqlite3.Connection, login: str, mot_de_passe: str) -> Utilisateur:
    row = con.execute("SELECT * FROM utilisateur WHERE login = ?", (login.strip(),)).fetchone()
    if row is None or not verifier(mot_de_passe, row["mot_de_passe_hash"]):
        raise ErreurAuth("Login ou mot de passe incorrect.")
    return Utilisateur(row["id_utilisateur"], row["login"], bool(row["est_admin"]), row["date_creation"])


def creer_admin_par_defaut(con: sqlite3.Connection, login: str = "admin",
                           mot_de_passe: str = MDP_ADMIN_DEFAUT) -> None:
    """Crée un compte admin au premier lancement s'il n'existe aucun admin.

    Son mot de passe devra être changé à la première connexion (US15).
    """
    if con.execute("SELECT 1 FROM utilisateur WHERE est_admin = 1").fetchone() is None:
        inscrire(con, login, mot_de_passe, est_admin=True)


# ---------------------------------------------------------------- mot de passe admin (US15)
def utilise_mot_de_passe_par_defaut(con: sqlite3.Connection, user: Utilisateur) -> bool:
    """Vrai si cet administrateur a encore le mot de passe par défaut."""
    if not user.est_admin:
        return False
    row = con.execute("SELECT mot_de_passe_hash FROM utilisateur WHERE id_utilisateur = ?",
                      (user.id_utilisateur,)).fetchone()
    return row is not None and verifier(MDP_ADMIN_DEFAUT, row["mot_de_passe_hash"])


def changer_mot_de_passe(con: sqlite3.Connection, id_utilisateur: int, nouveau: str) -> None:
    verifier_regles_mot_de_passe(nouveau)
    if nouveau == MDP_ADMIN_DEFAUT:
        raise ErreurAuth("Choisissez un mot de passe différent de celui par défaut.")
    with con:
        cur = con.execute("UPDATE utilisateur SET mot_de_passe_hash = ? WHERE id_utilisateur = ?",
                          (hacher(nouveau), id_utilisateur))
    if cur.rowcount == 0:
        raise ErreurAuth("Utilisateur introuvable.")
