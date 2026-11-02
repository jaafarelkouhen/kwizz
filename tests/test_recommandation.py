"""Tests de la recommandation du prochain quizz (US18) — aucune IA nécessaire."""
from quizz import auth, quiz_service as qs
from quizz.ia.recommandation import recommander
from quizz.models import Choix, Question, Quizz


def creer(con, titre, nb_questions=2):
    q = Quizz(titre, questions=[Question(f"Q{i} ?", [Choix("oui", True), Choix("non")])
                                for i in range(nb_questions)])
    return qs.charger_quizz(con, qs.enregistrer_quizz(con, q))


def jouer(con, user, quizz, justes):
    reponses = {q.id_question: {q.bonnes_reponses()[0].id_choix} for q in quizz.questions[:justes]}
    qs.enregistrer_tentative(con, user.id_utilisateur, quizz, reponses)


def test_aucun_quizz(con):
    assert recommander(con, auth.inscrire(con, "bob", "1234").id_utilisateur) is None


def test_quizz_jamais_joue_en_priorite(con):
    bob = auth.inscrire(con, "bob", "1234")
    a, b = creer(con, "A"), creer(con, "B")
    jouer(con, bob, a, 0)
    r = recommander(con, bob.id_utilisateur)
    assert r.quizz.titre == "B" and "jamais" in r.raison


def test_sinon_le_plus_faible_meilleur_score(con):
    bob = auth.inscrire(con, "bob", "1234")
    a, b = creer(con, "A", 2), creer(con, "B", 4)
    jouer(con, bob, a, 1)     # 50 %
    jouer(con, bob, b, 3)     # 75 %
    jouer(con, bob, a, 2)     # A passe à 100 % : c'est son MEILLEUR score qui compte
    r = recommander(con, bob.id_utilisateur)
    assert r.quizz.titre == "B" and "3/4" in r.raison


def test_tout_reussi_rien_a_recommander(con):
    bob = auth.inscrire(con, "bob", "1234")
    a = creer(con, "A")
    jouer(con, bob, a, 2)
    assert recommander(con, bob.id_utilisateur) is None


def test_les_parties_des_autres_ne_comptent_pas(con):
    bob, alice = auth.inscrire(con, "bob", "1234"), auth.inscrire(con, "alice", "1234")
    a = creer(con, "A")
    jouer(con, alice, a, 2)
    assert recommander(con, bob.id_utilisateur).quizz.titre == "A"
