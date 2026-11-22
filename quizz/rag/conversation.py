"""Fil de discussion de l'assistant, propre à chaque compte (v2.2).

Chaque échange est rangé avec l'identifiant de son auteur, et toutes les lectures filtrent sur cet
identifiant : Alice ne voit jamais les questions de Bob. Le fil survit aux redémarrages du serveur et
disparaît avec le compte.
"""
import json
import sqlite3

MAX_GARDES = 200  # échanges conservés par compte : les plus anciens sont effacés au-delà


def lire(con: sqlite3.Connection, id_utilisateur: int, limite: int = 50) -> list[dict]:
    """Les derniers échanges de ce compte, du plus ancien au plus récent."""
    rows = con.execute("SELECT * FROM (SELECT * FROM conversation_assistant WHERE id_utilisateur = ? "
                       "ORDER BY id DESC LIMIT ?) ORDER BY id", (id_utilisateur, limite)).fetchall()
    return [{"question": r["question"], "reponse": r["reponse"], "sources": json.loads(r["sources"]),
             "mode": r["mode"], "date": r["date"]} for r in rows]


def ajouter(con: sqlite3.Connection, id_utilisateur: int, question: str, reponse: dict) -> None:
    with con:
        con.execute("INSERT INTO conversation_assistant (id_utilisateur, question, reponse, sources, mode) "
                    "VALUES (?, ?, ?, ?, ?)", (id_utilisateur, question, reponse["reponse"],
                                               json.dumps(reponse.get("sources", []), ensure_ascii=False),
                                               reponse.get("mode", "")))
        con.execute("DELETE FROM conversation_assistant WHERE id_utilisateur = ? AND id NOT IN ("
                    "SELECT id FROM conversation_assistant WHERE id_utilisateur = ? ORDER BY id DESC LIMIT ?)",
                    (id_utilisateur, id_utilisateur, MAX_GARDES))


def effacer(con: sqlite3.Connection, id_utilisateur: int) -> None:
    with con:
        con.execute("DELETE FROM conversation_assistant WHERE id_utilisateur = ?", (id_utilisateur,))
