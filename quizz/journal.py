"""Journal d'activité (V2) : chaque action d'un utilisateur, consultable par l'administrateur.

Le login est recopié dans chaque ligne : le journal reste lisible même après la suppression du compte
(id_utilisateur passe alors à NULL). Les mots de passe n'y apparaissent jamais.
"""
import sqlite3

LIBELLES = {
    "inscription": "Création de son compte", "connexion": "Connexion", "connexion_echouee": "Connexion refusée",
    "deconnexion": "Déconnexion", "mot_de_passe": "Changement de mot de passe",
    "partie": "Partie jouée", "partie_test": "Test d'un quizz (non compté)",
    "revision": "Révision de ses erreurs (non comptée)",
    "assistant": "Question à l'assistant", "explication": "Explication demandée à l'IA",
    "quizz_cree": "Quizz créé (brouillon)", "quizz_modifie": "Quizz modifié (repasse en brouillon)",
    "quizz_valide": "Quizz validé et publié", "quizz_depublie": "Quizz retiré (brouillon)",
    "quizz_supprime": "Quizz supprimé ou archivé", "quizz_restaure": "Quizz restauré (brouillon)", "compte_cree": "Compte créé par l'admin",
    "compte_modifie": "Compte modifié par l'admin", "compte_supprime": "Compte supprimé par l'admin",
}


def noter(con: sqlite3.Connection, id_utilisateur: int | None, login: str, action: str, detail: str = "") -> None:
    with con:
        con.execute("INSERT INTO journal (id_utilisateur, login, action, detail) VALUES (?, ?, ?, ?)",
                    (id_utilisateur, login[:60], action, detail[:300]))


def lister(con: sqlite3.Connection, id_utilisateur: int | None = None, action: str | None = None,
           limite: int = 500) -> list[dict]:
    sql, params = "SELECT * FROM journal WHERE 1 = 1", []
    if id_utilisateur is not None:
        sql += " AND id_utilisateur = ?"
        params.append(id_utilisateur)
    if action:
        sql += " AND action = ?"
        params.append(action)
    sql += " ORDER BY id_journal DESC LIMIT ?"
    params.append(max(1, min(limite, 2000)))
    return [{"id": r["id_journal"], "date": r["date_action"], "id_utilisateur": r["id_utilisateur"],
             "login": r["login"], "action": r["action"], "libelle": LIBELLES.get(r["action"], r["action"]),
             "detail": r["detail"]} for r in con.execute(sql, params)]
