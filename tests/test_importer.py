from pathlib import Path

import pytest

from quizz.importer import ErreurFormat, lire_quizz_texte

EXEMPLE = Path(__file__).resolve().parent.parent / "data" / "exemples" / "capitales.txt"


def test_lecture_exemple():
    q = lire_quizz_texte(EXEMPLE)
    assert q.titre == "Capitales d'Europe"
    assert q.duree_limite == 60
    assert len(q.questions) == 3
    assert [c.texte for c in q.questions[0].bonnes_reponses()] == ["Rome"]


def test_choix_avant_question(tmp_path):
    f = tmp_path / "mauvais.txt"
    f.write_text("# TITRE: X\n+ Réponse orpheline\n", encoding="utf-8")
    with pytest.raises(ErreurFormat):
        lire_quizz_texte(f)


def test_ligne_inconnue(tmp_path):
    f = tmp_path / "mauvais.txt"
    f.write_text("Q: Question ?\n* bizarre\n", encoding="utf-8")
    with pytest.raises(ErreurFormat):
        lire_quizz_texte(f)


def test_fichier_texte_avec_bom_du_bloc_notes(tmp_path):
    """Le Bloc-notes Windows peut enregistrer en « UTF-8 avec BOM » : l'import doit l'accepter."""
    f = tmp_path / "bom.txt"
    f.write_bytes("\ufeff# TITRE: Avec BOM\nQ: 1 + 1 ?\n+ 2\n- 3\n".encode("utf-8"))
    assert lire_quizz_texte(f).titre == "Avec BOM"
