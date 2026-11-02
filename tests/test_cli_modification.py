"""Tests de l'écran admin « Modifier un quizz » (US08)."""
from quizz import auth, quiz_service as qs
from quizz.models import Choix, Question, Quizz
from quizz.ui import cli


def simuler_saisies(monkeypatch, *saisies):
    reponses = iter(saisies)
    monkeypatch.setattr("builtins.input", lambda _message="": next(reponses))


def preparer(con):
    admin = auth.inscrire(con, "prof", "1234", est_admin=True)
    qs.enregistrer_quizz(con, Quizz("Maths", "Calcul", 60, [
        Question("2 + 2 ?", [Choix("4", True), Choix("5")])]))
    return admin


def test_modifier_titre_et_supprimer_la_minuterie(con, monkeypatch):
    admin = preparer(con)
    simuler_saisies(monkeypatch, "1",            # choisir le 1er quizz
                    "Maths faciles", "",         # nouveau titre, description gardée
                    "0",                         # supprimer la minuterie
                    "n", "o")                    # garder les questions, enregistrer
    cli.ecran_modifier(con, admin)

    [q] = qs.lister_quizz(con)
    assert (q.titre, q.description, q.duree_limite) == ("Maths faciles", "Calcul", None)


def test_remplacer_les_questions(con, monkeypatch):
    admin = preparer(con)
    simuler_saisies(monkeypatch, "1", "", "", "",   # tout garder
                    "o", "1", "3 x 3 ?", "2", "9", "6", "1",   # nouvelles questions
                    "o")
    cli.ecran_modifier(con, admin)

    relu = qs.charger_quizz(con, qs.lister_quizz(con)[0].id_quizz)
    assert [q.enonce for q in relu.questions] == ["3 x 3 ?"]


def test_modification_annulee(con, monkeypatch):
    admin = preparer(con)
    simuler_saisies(monkeypatch, "1", "Autre", "", "", "n", "n")
    cli.ecran_modifier(con, admin)
    assert qs.lister_quizz(con)[0].titre == "Maths"
