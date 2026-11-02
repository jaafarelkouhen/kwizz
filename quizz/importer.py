"""Import / export de quizz (US06, US10).

Format texte (voir README) :
    # TITRE: Capitales d'Europe
    # DESCRIPTION: ...
    # DUREE: 60
    Q: Quelle est la capitale de l'Italie ?
    - Milan
    + Rome
"""
import json
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


# ---------------------------------------------------------------- JSON (US10, voir docs/conception/formats.md)
FORMAT_JSON, VERSION_JSON = "kwizz-quizz", 1


def quizz_vers_dict(quizz: Quizz) -> dict:
    """Sans les identifiants de la base : le fichier est importable dans n'importe quelle installation."""
    return {
        "format": FORMAT_JSON,
        "version": VERSION_JSON,
        "titre": quizz.titre,
        "description": quizz.description,
        "duree_limite": quizz.duree_limite,
        "questions": [
            {"enonce": q.enonce, "choix": [{"texte": c.texte, "correct": c.est_correct} for c in q.choix]}
            for q in quizz.questions
        ],
    }


def quizz_depuis_dict(donnees: dict) -> Quizz:
    """Construit un Quizz depuis un dict au format kwizz-quizz (fichier JSON ou réponse de l'IA)."""
    if not isinstance(donnees, dict) or donnees.get("format") != FORMAT_JSON:
        raise ErreurFormat(f"Ce n'est pas un quizz Kwizz (clé \"format\": \"{FORMAT_JSON}\" attendue).")
    if donnees.get("version") != VERSION_JSON:
        raise ErreurFormat(f"Version {donnees.get('version')!r} non prise en charge (attendu : {VERSION_JSON}).")
    try:
        duree = donnees.get("duree_limite")
        if duree is not None and (not isinstance(duree, int) or duree <= 0):
            raise ErreurFormat("\"duree_limite\" doit être un entier positif ou null.")
        quizz = Quizz(str(donnees["titre"]).strip(), str(donnees.get("description") or ""), duree)
        for num, q in enumerate(donnees["questions"], 1):
            question = Question(str(q["enonce"]).strip())
            for c in q["choix"]:
                question.choix.append(Choix(str(c["texte"]).strip(), c.get("correct") is True))
            quizz.questions.append(question)
    except (KeyError, TypeError) as e:
        raise ErreurFormat(f"Structure JSON invalide : {e}") from e
    return quizz


def exporter_json(quizz: Quizz, chemin: str | Path) -> None:
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(quizz_vers_dict(quizz), f, ensure_ascii=False, indent=2)


def lire_quizz_json(chemin: str | Path) -> Quizz:
    try:
        with open(chemin, encoding="utf-8") as f:
            donnees = json.load(f)
    except json.JSONDecodeError as e:
        raise ErreurFormat(f"JSON mal formé (ligne {e.lineno}) : {e.msg}") from e
    return quizz_depuis_dict(donnees)


def lire_quizz(chemin: str | Path) -> Quizz:
    """Choisit le bon lecteur selon l'extension : .json → JSON, sinon format texte."""
    quizz = lire_quizz_json(chemin) if Path(chemin).suffix.lower() == ".json" else lire_quizz_texte(chemin)
    quizz.source = "fichier"
    return quizz
