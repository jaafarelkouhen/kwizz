import pytest

from quizz import auth, quiz_service as qs
from quizz.models import Choix, Question, Quizz


def quizz_exemple():
    return Quizz("Maths", "Calcul mental", questions=[
        Question("2 + 2 ?", [Choix("3"), Choix("4", True)]),
        Question("3 x 3 ?", [Choix("9", True), Choix("6")]),
    ])


def test_enregistrer_et_charger(con):
    id_q = qs.enregistrer_quizz(con, quizz_exemple())
    q = qs.charger_quizz(con, id_q)
    assert q.titre == "Maths" and len(q.questions) == 2
    assert q.questions[0].bonnes_reponses()[0].texte == "4"


def test_quizz_sans_bonne_reponse_refuse(con):
    q = Quizz("X", questions=[Question("?", [Choix("a"), Choix("b")])])
    with pytest.raises(qs.ErreurQuizz):
        qs.enregistrer_quizz(con, q)


def test_score_et_historique(con):
    u = auth.inscrire(con, "bob", "1234")
    q = qs.charger_quizz(con, qs.enregistrer_quizz(con, quizz_exemple()))
    q1, q2 = q.questions
    reponses = {q1.id_question: {q1.choix[1].id_choix},   # juste
                q2.id_question: {q2.choix[1].id_choix}}   # faux
    t = qs.enregistrer_tentative(con, u.id_utilisateur, q, reponses)
    assert (t.score, t.nb_questions) == (1, 2)
    h = qs.historique(con, u.id_utilisateur)
    assert len(h) == 1 and h[0].titre_quizz == "Maths"


def test_supprimer(con):
    id_q = qs.enregistrer_quizz(con, quizz_exemple())
    qs.supprimer_quizz(con, id_q)
    assert qs.lister_quizz(con) == []
