"""Tests de la modification d'un quizz (US08)."""
import pytest

from quizz import auth, quiz_service as qs
from quizz.models import Choix, Question, Quizz


def quizz_enregistre(con) -> Quizz:
    q = Quizz("Maths", "Calcul mental", questions=[
        Question("2 + 2 ?", [Choix("3"), Choix("4", True)]),
        Question("3 x 3 ?", [Choix("9", True), Choix("6")]),
    ])
    return qs.charger_quizz(con, qs.enregistrer_quizz(con, q))


def test_modifier_titre_duree_et_questions(con):
    q = quizz_enregistre(con)
    q.titre, q.duree_limite = "Maths niveau 2", 30
    q.questions = [Question("10 / 2 ?", [Choix("5", True), Choix("2"), Choix("20")])]

    qs.modifier_quizz(con, q)

    relu = qs.charger_quizz(con, q.id_quizz)
    assert (relu.titre, relu.duree_limite, len(relu.questions)) == ("Maths niveau 2", 30, 1)
    assert relu.questions[0].bonnes_reponses()[0].texte == "5"


def test_modifier_garde_les_scores_de_l_historique(con):
    u = auth.inscrire(con, "bob", "1234")
    q = quizz_enregistre(con)
    qs.enregistrer_tentative(con, u.id_utilisateur, q, {})
    q.titre = "Maths (corrigé)"

    qs.modifier_quizz(con, q)

    h = qs.historique(con, u.id_utilisateur)
    assert len(h) == 1 and h[0].titre_quizz == "Maths (corrigé)"


def test_modification_invalide_ne_change_rien(con):
    q = quizz_enregistre(con)
    q.titre = "Nouveau titre"
    q.questions[0].choix = [Choix("seul choix", True)]  # invalide : il faut au moins 2 choix

    with pytest.raises(qs.ErreurQuizz):
        qs.modifier_quizz(con, q)

    relu = qs.charger_quizz(con, q.id_quizz)
    assert relu.titre == "Maths" and len(relu.questions[0].choix) == 2


def test_modifier_un_quizz_inexistant(con):
    q = Quizz("Fantôme", questions=[Question("?", [Choix("a", True), Choix("b")])], id_quizz=999)
    with pytest.raises(qs.ErreurQuizz):
        qs.modifier_quizz(con, q)


def test_modifier_un_quizz_jamais_enregistre(con):
    q = Quizz("Neuf", questions=[Question("?", [Choix("a", True), Choix("b")])])
    with pytest.raises(qs.ErreurQuizz):
        qs.modifier_quizz(con, q)
