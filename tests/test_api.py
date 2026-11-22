"""API web (MyKwizz v2.1, Sami), testée par le vrai serveur HTTP : sessions après redémarrage,
anti-force brute, « Pourquoi ? » protégé, explication jamais envoyée avant la correction."""
import http.cookiejar
import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

import serveur
from quizz import auth, importer, quiz_service as qs
from quizz.ia import client, explications


@pytest.fixture
def site(tmp_path, monkeypatch):
    monkeypatch.setattr(serveur, "CHEMIN_BASE", tmp_path / "test.db")
    serveur.preparer_base(demo=False)
    con = serveur.connexion(serveur.CHEMIN_BASE)
    auth.inscrire(con, "alice", "motdepasse1")
    con.close()
    lances = []

    def lancer():
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), serveur.Gestionnaire)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        lances.append(httpd)
        return f"http://127.0.0.1:{httpd.server_port}/api/"

    yield lancer
    for httpd in lances:
        httpd.shutdown()
        httpd.server_close()


def _client():
    ouvreur = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def appel(url, corps=None, methode=None):
        req = urllib.request.Request(url, data=None if corps is None else json.dumps(corps).encode(),
                                     headers={"Content-Type": "application/json"}, method=methode)
        try:
            with ouvreur.open(req) as r:
                return r.status, json.load(r)
        except urllib.error.HTTPError as e:
            return e.code, json.load(e)
    return appel


def test_session_survit_au_redemarrage_du_serveur(site):
    appel, url = _client(), site()
    assert appel(url + "connexion", {"login": "alice", "mdp": "motdepasse1"})[0] == 200
    url2 = site()                                   # …et un nouveau serveur sur la même base
    assert appel(url2 + "etat")[1]["utilisateur"]["login"] == "alice"
    assert appel(url2 + "deconnexion", {})[0] == 200
    assert appel(url2 + "etat")[1]["utilisateur"] is None


def test_blocage_apres_trois_echecs_survit_au_redemarrage(site):
    appel, url = _client(), site()
    for _ in range(3):
        assert appel(url + "connexion", {"login": "alice", "mdp": "faux"})[0] == 401
    assert appel(site() + "connexion", {"login": "alice", "mdp": "motdepasse1"})[0] == 429


def test_expliquer_refuse_une_question_jamais_jouee(site):
    appel, url = _client(), site()
    appel(url + "connexion", {"login": "alice", "mdp": "motdepasse1"})
    id_quizz = appel(url + "quizz")[1][0]["id"]
    partie = appel(url + f"quizz/{id_quizz}/jouer")[1]
    assert appel(url + "expliquer", {"id_question": partie["questions"][0]["id"]})[0] == 403


def test_explication_ecrite_par_l_admin(con, monkeypatch):
    monkeypatch.setattr(client, "demander_texte", lambda *a, **k: pytest.fail("l'IA ne doit pas être appelée"))
    d = {"format": "kwizz-quizz", "version": 1, "titre": "E", "questions": [
        {"enonce": "2 + 2 ?", "explication": "Deux paires font quatre.",
         "choix": [{"texte": "4", "correct": True}, {"texte": "5"}]}]}
    q = qs.charger_quizz(con, qs.enregistrer_quizz(con, importer.quizz_depuis_dict(d)))
    assert q.questions[0].explication == "Deux paires font quatre."
    assert importer.quizz_vers_dict(q)["questions"][0]["explication"] == "Deux paires font quatre."  # export JSON
    assert "explication" not in str(serveur.quizz_pour_joueur(q))            # jamais envoyée avant la correction
    assert qs.detail_correction(q.questions, {})[0]["explication"] == "Deux paires font quatre."
    assert explications.expliquer(con, q.questions[0]) == "Deux paires font quatre."  # « Pourquoi ? » sans IA

    q.titre = "E modifié"                                                    # modifier garde l'explication
    qs.modifier_quizz(con, q)
    assert qs.charger_quizz(con, q.id_quizz).questions[0].explication == "Deux paires font quatre."
