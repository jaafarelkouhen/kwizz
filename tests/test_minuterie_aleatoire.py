"""Tests de la minuterie (US09) et de l'ordre aléatoire (US13)."""
import random

from quizz import auth, quiz_service as qs
from quizz.models import Choix, Question, Quizz
from quizz.ui import cli


def quizz_dix_questions(con, duree=None) -> Quizz:
    q = Quizz("Tables", duree_limite=duree, questions=[
        Question(f"{i} x 2 ?", [Choix(str(i * 2), True), Choix(str(i * 2 + 1)), Choix("0")])
        for i in range(1, 11)])
    return qs.charger_quizz(con, qs.enregistrer_quizz(con, q))


# ---------------------------------------------------------------- minuterie
def test_temps_restant_sans_minuterie():
    assert qs.temps_restant(Quizz("X"), 1000) is None
    assert not qs.temps_ecoule(Quizz("X"), 1000)


def test_temps_restant_avec_minuterie():
    q = Quizz("X", duree_limite=60)
    assert qs.temps_restant(q, 15) == 45
    assert qs.temps_restant(q, 90) == 0          # jamais négatif
    assert not qs.temps_ecoule(q, 59.9) and qs.temps_ecoule(q, 60)


def test_console_arrete_le_quizz_quand_le_temps_est_ecoule(con, monkeypatch, capsys):
    joueur = auth.inscrire(con, "bob", "1234")
    quizz_dix_questions(con, duree=30)
    horloge = iter([0, 0, 5, 5, 40, 40])         # le temps passe à 40 s après la 2e réponse
    monkeypatch.setattr(cli.time, "monotonic", lambda: next(horloge, 40))
    saisies = iter(["1", "n", "1", "1", "1"])    # quizz n°1, ordre normal, puis réponses justes
    monkeypatch.setattr("builtins.input", lambda _m="": next(saisies, ""))

    cli.ecran_jouer(con, joueur)

    [t] = qs.historique(con, joueur.id_utilisateur)
    assert (t.score, t.nb_questions, t.duree_secondes) == (1, 10, 30)
    assert "Temps écoulé" in capsys.readouterr().out


# ---------------------------------------------------------------- ordre aléatoire
def test_melanger_garde_les_memes_questions_et_ne_modifie_pas_l_original(con):
    q = quizz_dix_questions(con)
    ordre_initial = [x.enonce for x in q.questions]

    m = qs.melanger(q, random.Random(42))

    assert [x.enonce for x in q.questions] == ordre_initial      # original intact
    assert sorted(x.enonce for x in m.questions) == sorted(ordre_initial)
    assert [x.enonce for x in m.questions] != ordre_initial       # avec la graine 42, l'ordre change


def test_le_score_ne_depend_pas_de_l_ordre(con):
    q = quizz_dix_questions(con)
    m = qs.melanger(q, random.Random(7))
    justes = {x.id_question: {x.bonnes_reponses()[0].id_choix} for x in m.questions}
    assert qs.corriger(q, justes) == qs.corriger(m, justes) == 10
