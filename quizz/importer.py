"""Import / export de quizz (US06, US10).

Format texte (voir README) :
    # TITRE: Capitales d'Europe
    # DESCRIPTION: ...
    # DUREE: 60
    Q: Quelle est la capitale de l'Italie ?
    - Milan
    + Rome
"""
from pathlib import Path

from .models import Choix, Question, Quizz


class ErreurFormat(Exception):
    """Fichier d'import mal formé."""


def lire_quizz_texte(chemin: str | Path) -> Quizz:
    quizz = Quizz(titre="")
    with open(chemin, encoding="utf-8") as f:
        for num, ligne in enumerate(f, 1):
            ligne = ligne.strip()
            if not ligne:
                continue
            if ligne.startswith("#"):
                cle, _, valeur = ligne[1:].partition(":")
                cle, valeur = cle.strip().upper(), valeur.strip()
                if cle == "TITRE":
                    quizz.titre = valeur
                elif cle == "DESCRIPTION":
                    quizz.description = valeur
                elif cle == "DUREE":
                    if not valeur.isdigit():
                        raise ErreurFormat(f"Ligne {num} : DUREE doit être un nombre de secondes.")
                    quizz.duree_limite = int(valeur)
                # tout autre « # ... » est un commentaire
            elif ligne.startswith("Q:"):
                quizz.questions.append(Question(ligne[2:].strip()))
            elif ligne[0] in "+-":
                if not quizz.questions:
                    raise ErreurFormat(f"Ligne {num} : choix trouvé avant toute question (Q:).")
                quizz.questions[-1].choix.append(Choix(ligne[1:].strip(), ligne[0] == "+"))
            else:
                raise ErreurFormat(f"Ligne {num} : ligne non reconnue → {ligne!r}")
    if not quizz.titre:
        quizz.titre = Path(chemin).stem
    return quizz


def exporter_json(quizz: Quizz, chemin: str | Path) -> None:
    """TODO (US10) : écrire le quizz au format JSON (json.dump + dataclasses.asdict)."""
    raise NotImplementedError


def lire_quizz_json(chemin: str | Path) -> Quizz:
    """TODO (US10) : relire un quizz exporté en JSON."""
    raise NotImplementedError
