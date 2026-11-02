"""Explication d'une mauvaise réponse par l'IA (US17)."""
from ..models import Question
from . import client

SYSTEME = """Tu es un professeur bienveillant. Un élève vient de se tromper à une question de quizz.
Explique en français, en 3 phrases maximum, pourquoi la bonne réponse est correcte et, si l'élève
a répondu, pourquoi sa réponse ne l'est pas. Pas de titre, pas de liste, pas de formule de politesse."""


def expliquer(question: Question, ids_choisis: set[int]) -> str:
    """Lève client.ErreurIA si l'IA est indisponible ou ne répond pas."""
    choisis = [c.texte for c in question.choix if c.id_choix in ids_choisis]
    bonnes = [c.texte for c in question.bonnes_reponses()]
    tous = ", ".join(c.texte for c in question.choix)
    prompt = (f"Question : {question.enonce}\n"
              f"Choix proposés : {tous}\n"
              f"Réponse de l'élève : {', '.join(choisis) if choisis else '(aucune réponse, temps écoulé)'}\n"
              f"Bonne réponse : {', '.join(bonnes)}")
    return client.demander_texte(SYSTEME, prompt)
