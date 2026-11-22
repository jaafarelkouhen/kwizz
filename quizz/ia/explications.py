"""Explication d'une question par l'IA (US17), gardée en base après le 1er appel (v2.1, V6).

L'explication ne dépend pas de la réponse de l'élève : elle dit pourquoi la bonne réponse est juste
et pourquoi chaque autre choix est faux. Elle convient donc à tous les joueurs et peut être réutilisée.
"""
import sqlite3

from ..models import Question
from . import client

SYSTEME = """Tu es un professeur bienveillant qui corrige une question de quizz pour des élèves.
Explique en français, en tutoyant, en 4 phrases maximum : pourquoi la bonne réponse est correcte, puis
en quelques mots pourquoi chacun des autres choix est faux. Pas de titre, pas de formule de politesse."""


def expliquer(con: sqlite3.Connection, question: Question) -> str:
    """Renvoie l'explication gardée, ou la demande à l'IA et la garde.

    Lève client.ErreurIA si l'IA est indisponible et qu'aucune explication n'est encore gardée.
    """
    if question.explication:
        return question.explication
    texte = rediger(question)
    garder(con, question, texte)
    return texte


def rediger(question: Question) -> str:
    """Demande l'explication à l'IA, sans toucher à la base (peut tourner dans un autre fil)."""
    bonnes = [c.texte for c in question.bonnes_reponses()]
    prompt = (f"Question : {question.enonce}\n"
              f"Choix proposés : {' ; '.join(c.texte for c in question.choix)}\n"
              f"Bonne(s) réponse(s) : {' ; '.join(bonnes)}")
    return client.demander_texte(SYSTEME, prompt)


def garder(con: sqlite3.Connection, question: Question, texte: str) -> None:
    """Enregistre l'explication : le prochain « Pourquoi ? » ne rappellera pas l'IA."""
    with con:
        con.execute("UPDATE question SET explication = ? WHERE id_question = ?", (texte, question.id_question))
    question.explication = texte
