"""Tests des écrans IA (US16 à US19), console et graphique, avec une FAUSSE IA.

On remplace client.demander_json / demander_texte : le vrai générateur et les vrais écrans
tournent, mais aucune requête ne part sur le réseau.
"""
import threading
import time
import tkinter as tk

import pytest

from quizz import auth, quiz_service as qs
from quizz.ia import client
from quizz.models import Choix, Question, Quizz
from quizz.ui import cli, gui

QUIZZ_IA = {"titre": "Volcans", "description": "Généré",
            "questions": [{"enonce": "Plus haut volcan d'Europe ?",
                           "choix": [{"texte": "Etna", "correct": True}, {"texte": "Vésuve", "correct": False}]}]}


@pytest.fixture
def ia(monkeypatch):
    """IA « disponible », qui répond toujours la même chose."""
    monkeypatch.setattr(client, "ia_disponible", lambda: True)
    monkeypatch.setattr(client, "demander_json", lambda *a, **k: QUIZZ_IA)
    monkeypatch.setattr(client, "demander_texte", lambda *a, **k: "Parce que l'Etna culmine à 3 300 m.")


def clavier(monkeypatch, *saisies):
    suite = iter(saisies)
    monkeypatch.setattr("builtins.input", lambda _m="": next(suite))


def attendre_fin(app, objet, delai=5.0):
    """Les appels IA de l'interface tournent en arrière-plan : on fait tourner Tk jusqu'à la fin."""
    fin = time.monotonic() + delai
    while getattr(objet, "en_cours", False):
        assert time.monotonic() < fin, "l'appel IA n'a pas fini à temps"
        app.update()
        time.sleep(0.01)


def un_quizz(con):
    q = Quizz("Capitales", questions=[Question("Italie ?", [Choix("Milan"), Choix("Rome", True)])])
    return qs.charger_quizz(con, qs.enregistrer_quizz(con, q))


# ---------------------------------------------------------------- console
def test_sans_ia_le_menu_admin_n_affiche_pas_la_generation(con, monkeypatch, capsys):
    admin = auth.inscrire(con, "prof", "1234", est_admin=True)
    clavier(monkeypatch, "9")                       # Se déconnecter
    cli.session(con, admin)
    assert "Générer un quizz avec l'IA" not in capsys.readouterr().out


def test_generation_console_avec_relecture(con, monkeypatch, ia, capsys):
    admin = auth.inscrire(con, "prof", "1234", est_admin=True)
    clavier(monkeypatch, "1", "les volcans", "1",   # thème, sujet, 1 question
            "", "o")                                # pas de minuterie, enregistrer
    cli.ecran_generer_ia(con, admin)

    [q] = qs.lister_quizz(con)
    assert (q.titre, q.source, q.id_createur) == ("Volcans", "ia", admin.id_utilisateur)
    sortie = capsys.readouterr().out
    assert "Récapitulatif" in sortie and "une IA peut se tromper" in sortie


def test_generation_console_refusee_par_l_admin(con, monkeypatch, ia):
    admin = auth.inscrire(con, "prof", "1234", est_admin=True)
    clavier(monkeypatch, "2", "Un texte", "sur deux lignes", "FIN", "1", "", "n")
    cli.ecran_generer_ia(con, admin)
    assert qs.lister_quizz(con) == []


def test_generation_console_ia_en_panne(con, monkeypatch, ia, capsys):
    def panne(*a, **k):
        raise client.ErreurIA("Impossible de joindre l'IA")
    monkeypatch.setattr(client, "demander_json", panne)
    admin = auth.inscrire(con, "prof", "1234", est_admin=True)
    clavier(monkeypatch, "1", "les volcans", "3")
    cli.ecran_generer_ia(con, admin)
    assert "Impossible de joindre" in capsys.readouterr().out and qs.lister_quizz(con) == []


def test_explications_apres_une_erreur(con, monkeypatch, ia, capsys):
    joueur = auth.inscrire(con, "bob", "1234")
    un_quizz(con)
    clavier(monkeypatch, "1", "n", "1",             # quizz n°1, ordre normal, Milan (faux)
            "o", "")                                # oui aux explications, pause
    cli.ecran_jouer(con, joueur)
    assert "Parce que l'Etna" in capsys.readouterr().out


def test_recommandation_affichee_dans_le_menu(con, monkeypatch, capsys):
    joueur = auth.inscrire(con, "bob", "1234")
    un_quizz(con)
    clavier(monkeypatch, "4")
    cli.session(con, joueur)
    assert "Recommandé : « Capitales »" in capsys.readouterr().out


# ---------------------------------------------------------------- interface graphique
@pytest.fixture
def app(fenetre, con):
    fenetre.con, fenetre.user = con, None
    fenetre.afficher(gui.EcranConnexion)
    return fenetre


def test_gui_bouton_ia_absent_sans_cle(app):
    app.user = auth.inscrire(app.con, "prof", "1234", est_admin=True)
    liste = app.afficher(gui.EcranListe)
    textes = [w.cget("text") for w in liste.winfo_children() if isinstance(w, tk.Button)]
    assert not any("IA" in t for t in textes)


def test_gui_generation_puis_enregistrement(app, ia):
    app.user = auth.inscrire(app.con, "prof", "1234", est_admin=True)
    liste = app.afficher(gui.EcranListe)
    fenetre_ia = gui.FenetreGenerationIA(liste)
    fenetre_ia.sujet.insert("1.0", "les volcans")

    fenetre_ia.generer()
    attendre_fin(app, fenetre_ia)
    assert "Plus haut volcan" in fenetre_ia.apercu.get("1.0", "end")
    fenetre_ia.enregistrer()

    assert qs.lister_quizz(app.con)[0].source == "ia"
    assert "généré par l'IA" in liste.message.cget("text")


def test_gui_recommandation_et_pourquoi(app, ia, monkeypatch):
    app.user = auth.inscrire(app.con, "bob", "1234")
    q = un_quizz(app.con)
    liste = app.afficher(gui.EcranListe)
    assert "Capitales" in liste.recommandation.cget("text")

    affiches = []
    monkeypatch.setattr(gui.messagebox, "showinfo", lambda titre, texte, **k: affiches.append(texte))
    t = qs.enregistrer_tentative(app.con, app.user.id_utilisateur, q, {})
    resultat = app.afficher(gui.EcranResultat, q, {}, t)
    resultat.expliquer(q.questions[0])
    attendre_fin(app, resultat)
    assert "Parce que l'Etna" in affiches[0]


def test_gui_ne_se_fige_pas_pendant_l_appel_ia(app, ia, monkeypatch):
    """Pendant que l'IA « réfléchit », la fenêtre continue de répondre."""
    feu_vert = threading.Event()
    monkeypatch.setattr(client, "demander_json", lambda *a, **k: (feu_vert.wait(5), QUIZZ_IA)[1])
    app.user = auth.inscrire(app.con, "prof", "1234", est_admin=True)
    fenetre_ia = gui.FenetreGenerationIA(app.afficher(gui.EcranListe))
    fenetre_ia.sujet.insert("1.0", "les volcans")

    fenetre_ia.generer()                      # rend la main tout de suite
    app.update()
    assert fenetre_ia.en_cours and fenetre_ia.bouton_generer.cget("state") == "disabled"

    feu_vert.set()
    attendre_fin(app, fenetre_ia)
    assert fenetre_ia.quizz.titre == "Volcans"
    assert fenetre_ia.bouton_generer.cget("state") == "normal"
    fenetre_ia.destroy()


def test_gui_erreur_ia_affichee(app, ia, monkeypatch):
    def panne(*a, **k):
        raise client.ErreurIA("Impossible de joindre l'IA")
    monkeypatch.setattr(client, "demander_json", panne)
    app.user = auth.inscrire(app.con, "prof", "1234", est_admin=True)
    fenetre_ia = gui.FenetreGenerationIA(app.afficher(gui.EcranListe))
    fenetre_ia.sujet.insert("1.0", "les volcans")
    fenetre_ia.generer()
    attendre_fin(app, fenetre_ia)
    assert "Impossible de joindre" in fenetre_ia.message.cget("text")
    assert fenetre_ia.bouton_enregistrer.cget("state") == "disabled"
    fenetre_ia.destroy()
