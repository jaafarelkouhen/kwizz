"""Tests de l'export / import JSON (US10)."""
import json
from pathlib import Path

import pytest

from quizz import quiz_service as qs
from quizz.importer import ErreurFormat, exporter_json, lire_quizz, lire_quizz_json, lire_quizz_texte
from quizz.models import Choix, Question, Quizz

EXEMPLES = Path(__file__).resolve().parent.parent / "data" / "exemples"


def test_aller_retour_sans_perte(tmp_path):
    original = lire_quizz_texte(EXEMPLES / "capitales.txt")
    fichier = tmp_path / "capitales.json"

    exporter_json(original, fichier)
    relu = lire_quizz_json(fichier)

    assert (relu.titre, relu.description, relu.duree_limite) == \
           (original.titre, original.description, original.duree_limite)
    assert [(q.enonce, [(c.texte, c.est_correct) for c in q.choix]) for q in relu.questions] == \
           [(q.enonce, [(c.texte, c.est_correct) for c in q.choix]) for q in original.questions]


def test_export_lisible_et_sans_identifiants(con, tmp_path):
    q = Quizz("Été", questions=[Question("Saison chaude ?", [Choix("Été", True), Choix("Hiver")])])
    charge = qs.charger_quizz(con, qs.enregistrer_quizz(con, q))
    fichier = tmp_path / "ete.json"

    exporter_json(charge, fichier)

    texte = fichier.read_text(encoding="utf-8")
    assert "Été" in texte                    # accents écrits tels quels (ensure_ascii=False)
    assert "id_" not in texte                # pas d'identifiants de la base
    assert json.loads(texte)["format"] == "kwizz-quizz"


def test_exemple_json_fourni_est_valide():
    q = lire_quizz(EXEMPLES / "capitales.json")
    qs.valider(q)
    assert q.titre == "Capitales du monde" and len(q.questions) == 2


@pytest.mark.parametrize("contenu, message", [
    ("{ pas du json", "mal formé"),
    ('{"titre": "X", "questions": []}', "format"),
    ('{"format": "kwizz-quizz", "version": 99, "titre": "X", "questions": []}', "Version"),
    ('{"format": "kwizz-quizz", "version": 1, "titre": "X"}', "Structure"),
    ('{"format": "kwizz-quizz", "version": 1, "titre": "X", "duree_limite": -5, "questions": []}', "duree"),
])
def test_fichiers_json_invalides(tmp_path, contenu, message):
    fichier = tmp_path / "mauvais.json"
    fichier.write_text(contenu, encoding="utf-8")
    with pytest.raises(ErreurFormat, match=message):
        lire_quizz_json(fichier)


def test_tous_les_exemples_s_importent():
    fichiers = sorted(EXEMPLES.glob("*.txt")) + sorted(EXEMPLES.glob("*.json"))
    assert fichiers
    for f in fichiers:
        qs.valider(lire_quizz(f))
