"""Tests de l'écran admin « Créer un quizz » (US03) : les saisies clavier sont simulées."""
from quizz import auth, quiz_service as qs
from quizz.ui import cli


def simuler_saisies(monkeypatch, *saisies):
    reponses = iter(saisies)
    monkeypatch.setattr("builtins.input", lambda _message="": next(reponses))


UN_QUIZZ = [
    "Capitales", "Géographie", "45",   # titre, description, durée
    "1",                              # nombre de questions
    "Capitale de l'Italie ?", "2",    # énoncé, nombre de choix
    "Rome", "Milan", "1",             # choix 1, choix 2, numéro de la bonne réponse
]


def test_creation_complete_avec_minuterie(con, monkeypatch):
    admin = auth.inscrire(con, "prof", "1234", est_admin=True)
    simuler_saisies(monkeypatch, *UN_QUIZZ, "o")

    cli.ecran_creer_quizz(con, admin)

    [q] = qs.lister_quizz(con)
    relu = qs.charger_quizz(con, q.id_quizz)
    assert (relu.titre, relu.duree_limite, relu.id_createur) == ("Capitales", 45, admin.id_utilisateur)
    assert relu.questions[0].bonnes_reponses()[0].texte == "Rome"


def test_creation_annulee_n_enregistre_rien(con, monkeypatch, capsys):
    admin = auth.inscrire(con, "prof", "1234", est_admin=True)
    simuler_saisies(monkeypatch, *UN_QUIZZ, "n")

    cli.ecran_creer_quizz(con, admin)

    assert qs.lister_quizz(con) == []
    assert "annulée" in capsys.readouterr().out


def test_champs_vides_et_duree_invalide_sont_redemandes(con, monkeypatch):
    admin = auth.inscrire(con, "prof", "1234", est_admin=True)
    saisies = ["", "Capitales",       # titre vide → redemandé
               "",                    # description vide : acceptée
               "abc", "",             # durée invalide → redemandée, puis Entrée = aucune
               "1", "Capitale ?", "2",
               "", "Rome", "Milan",   # choix vide → redemandé
               "1", "o"]
    simuler_saisies(monkeypatch, *saisies)

    cli.ecran_creer_quizz(con, admin)

    [q] = qs.lister_quizz(con)
    assert q.titre == "Capitales" and q.duree_limite is None
