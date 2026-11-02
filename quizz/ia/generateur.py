"""Génération d'un quizz par l'IA à partir d'un thème ou d'un texte (US16).

L'IA doit répondre dans le format JSON de Kwizz (docs/conception/formats.md), imposé par un schéma.
Sa réponse passe ensuite par le MÊME code de lecture et les MÊMES vérifications qu'un fichier importé.
Le quizz renvoyé n'est PAS enregistré : l'admin le relit d'abord.
"""
from .. import importer, quiz_service as qs
from ..models import Quizz
from . import client
from .client import ErreurIA

NB_QUESTIONS_MAX = 20
TEXTE_MAX = 20_000  # caractères : au-delà, on refuse plutôt que de couper le texte sans prévenir

SCHEMA_QUIZZ = {
    "type": "object",
    "properties": {
        "titre": {"type": "string"},
        "description": {"type": "string"},
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "enonce": {"type": "string"},
                    "choix": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {"texte": {"type": "string"}, "correct": {"type": "boolean"}},
                            "required": ["texte", "correct"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["enonce", "choix"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["titre", "description", "questions"],
    "additionalProperties": False,
}

SYSTEME = """Tu conçois des quizz pédagogiques en français pour l'application Kwizz.
Règles pour chaque quizz :
- exactement le nombre de questions demandé ;
- 3 ou 4 choix par question, dont exactement UN correct (le joueur ne peut cocher qu'une réponse) ;
- des faits vérifiables et non ambigus, sans question piège ;
- des énoncés courts et clairs, des choix de longueur comparable ;
- un titre court (moins de 60 caractères) et une description d'une phrase.
Si le contenu fourni est un texte, toutes les questions doivent pouvoir être répondues à partir de ce texte."""


def generer_quizz(sujet: str, nb_questions: int = 5, depuis_texte: bool = False) -> Quizz:
    """Renvoie un quizz validé (source = « ia »), non enregistré. Lève ErreurIA en cas de problème."""
    sujet = sujet.strip()
    if not sujet:
        raise ErreurIA("Indiquez un thème ou collez un texte.")
    if len(sujet) > TEXTE_MAX:
        raise ErreurIA(f"Texte trop long ({len(sujet)} caractères, maximum {TEXTE_MAX}) : raccourcissez-le.")
    if not 1 <= nb_questions <= NB_QUESTIONS_MAX:
        raise ErreurIA(f"Nombre de questions : entre 1 et {NB_QUESTIONS_MAX}.")

    if depuis_texte:
        prompt = f"Crée un quizz de {nb_questions} questions sur le texte suivant.\n\n<texte>\n{sujet}\n</texte>"
    else:
        prompt = f"Crée un quizz de {nb_questions} questions sur le thème : {sujet}"
    donnees = client.demander_json(SYSTEME, prompt, SCHEMA_QUIZZ)

    try:
        quizz = importer.quizz_depuis_dict({"format": importer.FORMAT_JSON, "version": importer.VERSION_JSON,
                                            "duree_limite": None, **donnees})
        qs.valider(quizz)
    except (importer.ErreurFormat, qs.ErreurQuizz) as e:
        raise ErreurIA(f"Le quizz proposé par l'IA est incomplet ({e}) : réessayez.") from None
    for num, q in enumerate(quizz.questions, 1):
        if len(q.bonnes_reponses()) != 1:
            raise ErreurIA(f"Question {num} : l'IA a donné plusieurs bonnes réponses : réessayez.")
    quizz.source = "ia"
    return quizz
