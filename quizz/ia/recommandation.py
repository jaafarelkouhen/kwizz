"""Recommandation du prochain quizz (US18).

Volontairement SANS IA : des règles simples, explicables et testables, qui marchent toujours,
même hors ligne. Ordre des règles :
  1. un quizz jamais joué ;
  2. sinon, le quizz où le meilleur score est le plus faible (en pourcentage) ;
  3. tous réussis à 100 % : rien à recommander.
"""
import sqlite3
from dataclasses import dataclass

from .. import quiz_service as qs
from ..models import Quizz


@dataclass
class Recommandation:
    quizz: Quizz
    raison: str


def recommander(con: sqlite3.Connection, id_utilisateur: int) -> Recommandation | None:
    tous = qs.lister_quizz(con)
    if not tous:
        return None
    meilleurs: dict[int, tuple[int, int]] = {}  # id_quizz → (meilleur score, nb de questions)
    for t in qs.historique(con, id_utilisateur):
        actuel = meilleurs.get(t.id_quizz)
        if actuel is None or t.score / t.nb_questions > actuel[0] / actuel[1]:
            meilleurs[t.id_quizz] = (t.score, t.nb_questions)

    jamais_joues = [q for q in tous if q.id_quizz not in meilleurs]
    if jamais_joues:
        return Recommandation(jamais_joues[0], "vous ne l'avez jamais joué")

    a_retenter = [q for q in tous if meilleurs[q.id_quizz][0] < meilleurs[q.id_quizz][1]]
    if not a_retenter:
        return None
    pire = min(a_retenter, key=lambda q: meilleurs[q.id_quizz][0] / meilleurs[q.id_quizz][1])
    score, total = meilleurs[pire.id_quizz]
    return Recommandation(pire, f"votre meilleur score est {score}/{total} : retentez votre chance")
