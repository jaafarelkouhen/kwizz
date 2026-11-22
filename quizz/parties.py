"""Parties en cours, gardées en base (v2.2, W2) : un redémarrage du serveur ne fait plus perdre la partie.

Une seule partie en cours par joueur. On garde l'ordre d'affichage (questions et choix mélangés ou non)
et les réponses déjà cochées, pour que la reprise montre exactement la même partie. L'heure de début
est une heure réelle (time.time) : elle reste juste après un redémarrage, ce qui garde la minuterie.
"""
import json
import secrets
import sqlite3
import time

from .models import Quizz


def commencer(con: sqlite3.Connection, id_utilisateur: int, quizz: Quizz, test: bool = False) -> str:
    """Remplace la partie en cours du joueur par une nouvelle. Renvoie l'identifiant de la partie."""
    partie = secrets.token_hex(8)
    ordre = [[q.id_question, [c.id_choix for c in q.choix]] for q in quizz.questions]
    with con:
        con.execute("DELETE FROM partie_en_cours WHERE id_utilisateur = ?", (id_utilisateur,))
        con.execute("INSERT INTO partie_en_cours (partie, id_utilisateur, id_quizz, debut, test, ordre) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (partie, id_utilisateur, quizz.id_quizz, time.time(), int(test), json.dumps(ordre)))
    return partie


def sauver_reponses(con: sqlite3.Connection, id_utilisateur: int, partie: str,
                    reponses: dict[int, set[int]]) -> bool:
    """Enregistre les réponses cochées jusqu'ici. Faux si la partie n'existe plus."""
    texte = json.dumps({str(q): sorted(c) for q, c in reponses.items()})
    with con:
        cur = con.execute("UPDATE partie_en_cours SET reponses = ? WHERE partie = ? AND id_utilisateur = ?",
                          (texte, partie, id_utilisateur))
    return cur.rowcount == 1


def _depuis_ligne(r: sqlite3.Row) -> dict:
    return {"partie": r["partie"], "id_quizz": r["id_quizz"], "debut": r["debut"], "test": bool(r["test"]),
            "ordre": json.loads(r["ordre"]),
            "reponses": {int(q): set(c) for q, c in json.loads(r["reponses"]).items()}}


def en_cours(con: sqlite3.Connection, id_utilisateur: int) -> dict | None:
    r = con.execute("SELECT * FROM partie_en_cours WHERE id_utilisateur = ?", (id_utilisateur,)).fetchone()
    return None if r is None else _depuis_ligne(r)


def terminer(con: sqlite3.Connection, id_utilisateur: int, partie: str) -> dict | None:
    """Retire la partie (au moment de la corriger) et la renvoie ; None si elle n'existe plus."""
    r = con.execute("SELECT * FROM partie_en_cours WHERE partie = ? AND id_utilisateur = ?",
                    (partie, id_utilisateur)).fetchone()
    if r is None:
        return None
    with con:
        con.execute("DELETE FROM partie_en_cours WHERE partie = ?", (partie,))
    return _depuis_ligne(r)


def remettre_dans_l_ordre(quizz: Quizz, ordre: list) -> Quizz:
    """Remet questions et choix dans l'ordre de la partie (celui du mélange éventuel)."""
    questions = {q.id_question: q for q in quizz.questions}
    rangees = []
    for id_q, ids_choix in ordre:
        q = questions.get(id_q)
        if q is None:  # question retirée depuis (quizz modifié) : la partie ne peut plus être reprise
            raise KeyError(id_q)
        choix = {c.id_choix: c for c in q.choix}
        q.choix = [choix[i] for i in ids_choix if i in choix]
        rangees.append(q)
    quizz.questions = rangees
    return quizz
