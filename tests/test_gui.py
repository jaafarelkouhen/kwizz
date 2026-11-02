"""Tests de l'interface graphique (US11) : on pilote les écrans par le code, fenêtre cachée.

Les boîtes de dialogue (confirmation de mot de passe…) sont remplacées par des réponses prévues.
Si aucun affichage n'est disponible (serveur sans écran), les tests sont ignorés.
"""
import tkinter as tk

import pytest

from quizz import auth, quiz_service as qs
from quizz.models import Choix, Question, Quizz
from quizz.ui import gui


@pytest.fixture(scope="module")
def fenetre():
    """UNE seule fenêtre Tk pour tout le fichier : sous Windows, recréer Tk() en boucle
    dans le même processus échoue parfois (« Can't find a usable tk.tcl »)."""
    try:
        application = gui.Application(None)
    except tk.TclError as e:
        pytest.skip(f"pas d'affichage graphique disponible ({e})")
    application.withdraw()
    yield application
    application.destroy()


@pytest.fixture
def app(fenetre, con):
    """Avant chaque test : base neuve, personne de connecté, retour à l'écran de connexion."""
    fenetre.con, fenetre.user = con, None
    fenetre.afficher(gui.EcranConnexion)
    return fenetre


def remplir(ecran, login, mdp):
    ecran.login.insert(0, login)
    ecran.mdp.insert(0, mdp)


def repondre_aux_dialogues(monkeypatch, *reponses):
    suite = iter(reponses)
    monkeypatch.setattr(gui.simpledialog, "askstring", lambda *a, **k: next(suite))


def quizz_deux_questions(con, duree=None):
    q = Quizz("Capitales", duree_limite=duree, questions=[
        Question("Italie ?", [Choix("Milan"), Choix("Rome", True)]),
        Question("Portugal ?", [Choix("Lisbonne", True), Choix("Porto")])])
    return qs.enregistrer_quizz(con, q)


def test_mauvais_mot_de_passe_affiche_une_erreur(app):
    remplir(app.ecran, "inconnu", "faux")
    app.ecran.connecter()
    assert isinstance(app.ecran, gui.EcranConnexion)
    assert "incorrect" in app.ecran.message.cget("text")


def test_inscription_puis_liste(app, monkeypatch):
    repondre_aux_dialogues(monkeypatch, "secret")
    remplir(app.ecran, "alice", "secret")
    app.ecran.inscrire()
    assert isinstance(app.ecran, gui.EcranListe) and app.user.login == "alice"


def test_admin_par_defaut_doit_changer_son_mot_de_passe(app, monkeypatch):
    auth.creer_admin_par_defaut(app.con)
    repondre_aux_dialogues(monkeypatch, "Nouveau42", "Nouveau42")
    remplir(app.ecran, "admin", "admin")
    app.ecran.connecter()
    assert isinstance(app.ecran, gui.EcranListe)
    assert auth.connecter(app.con, "admin", "Nouveau42")


def test_partie_complete(app):
    quizz_deux_questions(app.con)
    app.user = auth.inscrire(app.con, "bob", "1234")
    liste = app.afficher(gui.EcranListe)
    liste.liste.selection_set(0)
    liste.jouer()

    jeu = app.ecran
    assert isinstance(jeu, gui.EcranJeu)
    jeu.valider()                                    # sans choix : refusé
    assert "Choisissez" in jeu.message.cget("text")
    jeu.choix_var.set(1); jeu.valider()             # Rome ✔
    jeu.choix_var.set(1); jeu.valider()             # Porto ✘

    resultat = app.ecran
    assert isinstance(resultat, gui.EcranResultat)
    [t] = qs.historique(app.con, app.user.id_utilisateur)
    assert (t.score, t.nb_questions) == (1, 2)


def test_minuterie_termine_la_partie(app, monkeypatch):
    quizz_deux_questions(app.con, duree=30)
    app.user = auth.inscrire(app.con, "bob", "1234")
    temps = [0.0]
    monkeypatch.setattr(gui.time, "monotonic", lambda: temps[0])
    jeu = app.afficher(gui.EcranJeu, qs.charger_quizz(app.con, 1))
    assert "30" in jeu.chrono.cget("text")

    temps[0] = 31.0
    jeu.tic()

    assert isinstance(app.ecran, gui.EcranResultat)
    assert qs.historique(app.con, app.user.id_utilisateur)[0].duree_secondes == 30


def test_historique_et_classement(app):
    id_q = quizz_deux_questions(app.con)
    app.user = auth.inscrire(app.con, "bob", "1234")
    q = qs.charger_quizz(app.con, id_q)
    qs.enregistrer_tentative(app.con, app.user.id_utilisateur, q, {})

    historique = app.afficher(gui.EcranHistorique)
    assert len(historique.tableau.get_children()) == 1
    classement = app.afficher(gui.EcranClassement, q)
    assert classement.tableau.item(classement.tableau.get_children()[0])["values"][1] == "bob"


def test_selection_obligatoire_avant_de_jouer(app):
    quizz_deux_questions(app.con)
    app.user = auth.inscrire(app.con, "bob", "1234")
    liste = app.afficher(gui.EcranListe)
    liste.jouer()
    assert "Sélectionnez" in liste.message.cget("text")
