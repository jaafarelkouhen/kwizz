"""Tests des explications IA (US17) avec une fausse IA."""
import pytest

from quizz.ia import client, explications
from quizz.models import Choix, Question

QUESTION = Question("Capitale du Portugal ?", [Choix("Lisbonne", True, 1), Choix("Porto", False, 2)], id_question=1)


@pytest.fixture
def prompts(monkeypatch):
    envoyes = []
    monkeypatch.setattr(client, "demander_texte", lambda systeme, prompt, **_: envoyes.append(prompt) or "Car…")
    return envoyes


def test_explication_avec_la_reponse_de_l_eleve(prompts):
    assert explications.expliquer(QUESTION, {2}) == "Car…"
    [p] = prompts
    assert "Capitale du Portugal" in p
    assert "Réponse de l'élève : Porto" in p and "Bonne réponse : Lisbonne" in p


def test_explication_sans_reponse(prompts):
    explications.expliquer(QUESTION, set())
    assert "aucune réponse" in prompts[0]


def test_erreur_ia_remontee(monkeypatch):
    def en_panne(*a, **k):
        raise client.ErreurIA("Impossible de joindre l'IA")
    monkeypatch.setattr(client, "demander_texte", en_panne)
    with pytest.raises(client.ErreurIA):
        explications.expliquer(QUESTION, {2})
