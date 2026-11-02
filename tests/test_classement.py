"""Tests du classement par quizz (US12)."""
from quizz import auth, quiz_service as qs
from quizz.models import Choix, Question, Quizz


def preparer(con):
    q = Quizz("Duo", questions=[Question("A ?", [Choix("a", True), Choix("b")]),
                                Question("B ?", [Choix("a"), Choix("b", True)])])
    return qs.charger_quizz(con, qs.enregistrer_quizz(con, q))


def jouer(con, login, quizz, nb_justes):
    user = auth.connecter(con, login, "1234")
    reponses = {q.id_question: {q.bonnes_reponses()[0].id_choix} for q in quizz.questions[:nb_justes]}
    qs.enregistrer_tentative(con, user.id_utilisateur, quizz, reponses)


def test_meilleur_score_par_joueur_trie(con):
    for login in ("alice", "bob", "chloe"):
        auth.inscrire(con, login, "1234")
    q = preparer(con)
    jouer(con, "alice", q, 1)
    jouer(con, "alice", q, 2)      # son meilleur score compte, pas le dernier ni la moyenne
    jouer(con, "bob", q, 0)
    jouer(con, "chloe", q, 1)

    assert qs.classement(con, q.id_quizz) == [("alice", 2), ("chloe", 1), ("bob", 0)]


def test_un_joueur_n_apparait_qu_une_fois_et_limite(con):
    for login in ("alice", "bob"):
        auth.inscrire(con, login, "1234")
    q = preparer(con)
    for _ in range(3):
        jouer(con, "alice", q, 2)
    jouer(con, "bob", q, 1)

    assert qs.classement(con, q.id_quizz) == [("alice", 2), ("bob", 1)]
    assert qs.classement(con, q.id_quizz, limite=1) == [("alice", 2)]


def test_classement_vide(con):
    assert qs.classement(con, preparer(con).id_quizz) == []
