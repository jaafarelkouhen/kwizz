"""Tests du générateur de quizz IA (US16) : la « fausse IA » renvoie un JSON prévu à l'avance."""
import pytest

from quizz import quiz_service as qs
from quizz.ia import client, generateur
from quizz.ia.client import ErreurIA


def reponse_ia(nb=2, bonnes=1):
    return {
        "titre": "Système solaire",
        "description": "Les planètes",
        "questions": [
            {"enonce": f"Question {i} ?",
             "choix": [{"texte": f"choix {j}", "correct": j < bonnes} for j in range(3)]}
            for i in range(1, nb + 1)
        ],
    }


@pytest.fixture
def fausse_ia(monkeypatch):
    appels = []

    def demander_json(systeme, prompt, schema, **_):
        appels.append({"systeme": systeme, "prompt": prompt, "schema": schema})
        return fausse_ia.reponse

    fausse_ia.reponse = reponse_ia()
    monkeypatch.setattr(client, "demander_json", demander_json)
    fausse_ia.appels = appels
    return fausse_ia


def test_genere_un_quizz_valide_marque_ia(fausse_ia, con):
    q = generateur.generer_quizz("le système solaire", nb_questions=2)
    assert (q.titre, len(q.questions), q.source, q.id_quizz) == ("Système solaire", 2, "ia", None)
    qs.enregistrer_quizz(con, q)          # enregistrable tel quel après relecture
    assert qs.lister_quizz(con)[0].source == "ia"


def test_prompt_contient_le_theme_et_le_nombre(fausse_ia):
    generateur.generer_quizz("les volcans", nb_questions=7)
    [appel] = fausse_ia.appels
    assert "les volcans" in appel["prompt"] and "7 questions" in appel["prompt"]
    assert appel["schema"] is generateur.SCHEMA_QUIZZ


def test_mode_texte(fausse_ia):
    generateur.generer_quizz("Le Rhône prend sa source en Suisse.", nb_questions=2, depuis_texte=True)
    assert "<texte>" in fausse_ia.appels[0]["prompt"]


@pytest.mark.parametrize("sujet, nb, message", [
    ("   ", 5, "thème"),
    ("x", 0, "entre 1 et"),
    ("x", 21, "entre 1 et"),
    ("x" * (generateur.TEXTE_MAX + 1), 5, "trop long"),
])
def test_demandes_invalides_refusees_sans_appeler_l_ia(fausse_ia, sujet, nb, message):
    with pytest.raises(ErreurIA, match=message):
        generateur.generer_quizz(sujet, nb_questions=nb)
    assert fausse_ia.appels == []


def test_question_sans_bonne_reponse_refusee(fausse_ia):
    fausse_ia.reponse = reponse_ia(bonnes=0)
    with pytest.raises(ErreurIA, match="incomplet"):
        generateur.generer_quizz("x", 2)


def test_plusieurs_bonnes_reponses_refusees(fausse_ia):
    fausse_ia.reponse = reponse_ia(bonnes=2)
    with pytest.raises(ErreurIA, match="plusieurs bonnes"):
        generateur.generer_quizz("x", 2)


def test_aucune_question_refusee(fausse_ia):
    fausse_ia.reponse = {"titre": "Vide", "description": "", "questions": []}
    with pytest.raises(ErreurIA, match="incomplet"):
        generateur.generer_quizz("x", 2)
