"""Tests des explications IA (US17, gardées en base depuis la v2.1) avec une fausse IA."""
import pytest

from quizz import quiz_service as qs
from quizz.ia import client, explications
from quizz.models import Choix, Question, Quizz


@pytest.fixture
def prompts(monkeypatch):
    envoyes = []
    monkeypatch.setattr(client, "demander_texte", lambda systeme, prompt, **_: envoyes.append(prompt) or "Car…")
    return envoyes


@pytest.fixture
def question(con):
    q = Quizz("Capitales", questions=[Question("Capitale du Portugal ?", [Choix("Lisbonne", True), Choix("Porto")])])
    return qs.charger_quizz(con, qs.enregistrer_quizz(con, q)).questions[0]


def test_explication_de_la_question(con, question, prompts):
    assert explications.expliquer(con, question) == "Car…"
    [p] = prompts
    assert "Capitale du Portugal" in p and "Porto" in p and "Bonne(s) réponse(s) : Lisbonne" in p


def test_explication_gardee_pas_de_second_appel(con, question, prompts):
    explications.expliquer(con, question)
    relue = qs.charger_quizz(con, qs.lister_quizz(con)[0].id_quizz).questions[0]
    assert explications.expliquer(con, relue) == "Car…" and len(prompts) == 1


def test_erreur_ia_remontee_et_rien_garde(con, question, monkeypatch):
    def en_panne(*a, **k):
        raise client.ErreurIA("Impossible de joindre l'IA")
    monkeypatch.setattr(client, "demander_texte", en_panne)
    with pytest.raises(client.ErreurIA):
        explications.expliquer(con, question)
    assert not qs.charger_quizz(con, qs.lister_quizz(con)[0].id_quizz).questions[0].explication
