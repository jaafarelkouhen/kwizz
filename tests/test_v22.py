"""Tests v2.2 (docs/PROCHAINE-VERSION.md, section 6)."""
import random

import pytest

import serveur
from quizz import auth, importer, parties, quiz_service as qs
from tests.test_api import _client, site  # noqa: F401  (fixture du vrai serveur HTTP)


def _quizz(con):
    q = importer.quizz_depuis_dict({"format": "kwizz-quizz", "version": 1, "titre": "Q", "duree_limite": 60,
                                    "questions": [
        {"enonce": "Capitale de l'Italie ?", "choix": [{"texte": "Rome", "correct": True}, {"texte": "Milan"}]},
        {"enonce": "Capitale du Portugal ?", "choix": [{"texte": "Lisbonne", "correct": True}, {"texte": "Porto"}]}]})
    return qs.charger_quizz(con, qs.enregistrer_quizz(con, q))


# ---------------------------------------------------------------- W2 : reprendre une partie en cours
def test_partie_en_cours_gardee_avec_son_ordre_et_ses_reponses(con):
    u = auth.inscrire(con, "alice", "motdepasse1")
    q = qs.melanger(_quizz(con), random.Random(3))
    partie = parties.commencer(con, u.id_utilisateur, q)
    premiere = q.questions[0]
    assert parties.sauver_reponses(con, u.id_utilisateur, partie, {premiere.id_question: {premiere.choix[0].id_choix}})

    p = parties.en_cours(con, u.id_utilisateur)
    relu = parties.remettre_dans_l_ordre(qs.charger_quizz(con, q.id_quizz), p["ordre"])
    assert [x.id_question for x in relu.questions] == [x.id_question for x in q.questions]           # même ordre
    assert [c.id_choix for c in relu.questions[0].choix] == [c.id_choix for c in premiere.choix]
    assert p["reponses"] == {premiere.id_question: {premiere.choix[0].id_choix}}

    parties.commencer(con, u.id_utilisateur, q)                     # une nouvelle partie remplace l'ancienne
    assert parties.terminer(con, u.id_utilisateur, partie) is None
    assert con.execute("SELECT COUNT(*) FROM partie_en_cours").fetchone()[0] == 1


def test_reprendre_la_partie_apres_un_redemarrage_du_serveur(site):  # noqa: F811
    appel, url = _client(), site()
    appel(url + "connexion", {"login": "alice", "mdp": "motdepasse1"})
    id_quizz = appel(url + "quizz")[1][0]["id"]
    partie = appel(url + f"quizz/{id_quizz}/jouer")[1]
    q1 = partie["questions"][0]
    reponse = {str(q1["id"]): [q1["choix"][0]["id"]]}
    assert appel(url + f"quizz/{id_quizz}/sauver", {"partie": partie["partie"], "reponses": reponse})[0] == 200

    url2 = site()
    reprise = appel(url2 + "partie/en-cours")[1]
    assert reprise["partie"] == partie["partie"] and reprise["reponses"] == reponse
    assert [x["id"] for x in reprise["questions"]] == [x["id"] for x in partie["questions"]]
    assert reprise["restant"] is None or 0 < reprise["restant"] <= partie["duree"]
    statut, corrige = appel(url2 + f"quizz/{id_quizz}/corriger", {"partie": partie["partie"], "reponses": reponse})
    assert statut == 200 and appel(url2 + "partie/en-cours")[1] is None   # corrigée : plus rien à reprendre


# ---------------------------------------------------------------- W3 : supprimer un compte sans fausser les statistiques
def test_supprimer_un_compte_qui_a_joue_l_anonymise(con):
    from quizz import journal
    alice = auth.inscrire(con, "alice", "motdepasse1")
    bob = auth.inscrire(con, "bob", "motdepasse1")
    jamais = auth.inscrire(con, "zoe", "motdepasse1")
    q = _quizz(con)
    for u, justes in ((alice, 2), (bob, 1)):
        rep = {x.id_question: {x.choix[0].id_choix} for x in q.questions[:justes]}
        qs.enregistrer_tentative(con, u.id_utilisateur, q, rep, 20)
    journal.noter(con, alice.id_utilisateur, "alice", "connexion")

    assert auth.supprimer_utilisateur(con, alice.id_utilisateur) is True          # a joué → anonymisé
    assert auth.supprimer_utilisateur(con, jamais.id_utilisateur) is False        # jamais joué → effacé
    assert con.execute("SELECT COUNT(*) FROM tentative").fetchone()[0] == 2       # ses parties restent comptées
    assert [l for l, _ in qs.classement(con, q.id_quizz)] == ["bob"]              # mais plus au classement
    assert [u["login"] for u in auth.lister_utilisateurs(con)] == ["bob"]         # ni dans la liste des comptes
    with pytest.raises(auth.ErreurAuth):
        auth.connecter(con, "alice", "motdepasse1")                               # ni connectable
    auth.inscrire(con, "alice", "motdepasse2")                                    # son login est libéré
    assert journal.lister(con, action="connexion")[0]["id_utilisateur"] is None   # journal : login gardé, lien coupé
    with pytest.raises(auth.ErreurAuth):
        auth.supprimer_utilisateur(con, alice.id_utilisateur)                     # déjà supprimé


# ---------------------------------------------------------------- W4 : réviser ses erreurs
def test_questions_a_revoir_suivent_la_derniere_vraie_partie(con):
    u = auth.inscrire(con, "alice", "motdepasse1")
    q = _quizz(con)
    italie, portugal = q.questions
    juste = lambda x: {x.id_question: {x.choix[0].id_choix}}          # noqa: E731
    qs.enregistrer_tentative(con, u.id_utilisateur, q, {}, 10)        # tout faux
    assert [x.enonce for x in qs.questions_a_revoir(con, u.id_utilisateur)] == [
        "Capitale de l'Italie ?", "Capitale du Portugal ?"]
    qs.enregistrer_tentative(con, u.id_utilisateur, q, juste(italie), 10)   # l'Italie est réussie ensuite
    assert [x.enonce for x in qs.questions_a_revoir(con, u.id_utilisateur)] == ["Capitale du Portugal ?"]
    assert qs.questions_a_revoir(con, auth.inscrire(con, "bob", "motdepasse1").id_utilisateur) == []  # à chacun ses erreurs
    qs.supprimer_quizz(con, q.id_quizz)                               # quizz archivé : plus rien à revoir
    assert qs.questions_a_revoir(con, u.id_utilisateur) == []


def test_reviser_ses_erreurs_par_le_serveur(site):  # noqa: F811
    appel, url = _client(), site()
    appel(url + "connexion", {"login": "alice", "mdp": "motdepasse1"})
    quizz = appel(url + "quizz")[1]
    partie = appel(url + f"quizz/{quizz[0]['id']}/jouer")[1]
    appel(url + f"quizz/{quizz[0]['id']}/corriger", {"partie": partie["partie"], "reponses": {}})   # tout faux
    revision = appel(url + "revision")[1]
    ids = [x["id"] for x in revision["questions"]]
    assert ids and set(ids) <= {x["id"] for x in partie["questions"]}
    assert all("correct" not in str(x) for x in revision["questions"])                 # pas de réponse avant
    statut, r = appel(url + "revision/corriger", {"questions": ids, "reponses": {}})
    assert statut == 200 and r["revision"] and r["score"] == 0 and len(r["detail"]) == len(ids)
    jamais = appel(url + f"quizz/{quizz[1]['id']}/jouer")[1]["questions"][0]["id"]
    assert appel(url + "revision/corriger", {"questions": [jamais], "reponses": {}})[0] == 403  # jamais jouée
    assert appel(url + "historique")[1][0]["titre"] == quizz[0]["titre"]               # la révision n'est pas une partie


# ---------------------------------------------------------------- assistant privé : à chacun son fil
def test_alice_ne_voit_jamais_le_fil_de_bob(site):  # noqa: F811
    url = site()
    con = serveur.connexion(serveur.CHEMIN_BASE)
    auth.inscrire(con, "bob", "motdepasse1")
    con.close()
    alice, bob = _client(), _client()                         # deux navigateurs
    alice(url + "connexion", {"login": "alice", "mdp": "motdepasse1"})
    bob(url + "connexion", {"login": "bob", "mdp": "motdepasse1"})
    alice(url + "assistant", {"question": "qui a peint la Joconde ?"})
    bob(url + "assistant", {"question": "c'est quoi la loi d'Ohm ?"})
    fil = lambda client, u=url: [e["question"] for e in client(u + "assistant")[1]]  # noqa: E731

    assert fil(alice) == ["qui a peint la Joconde ?"] and fil(bob) == ["c'est quoi la loi d'Ohm ?"]
    assert bob(url + "assistant", methode="DELETE")[0] == 200   # « Nouvelle discussion » de Bob…
    assert fil(bob) == [] and fil(alice) == ["qui a peint la Joconde ?"]   # …n'efface que le sien

    bob(url + "deconnexion", {})                              # Alice se connecte sur le navigateur de Bob
    bob(url + "connexion", {"login": "alice", "mdp": "motdepasse1"})
    assert fil(bob) == ["qui a peint la Joconde ?"]           # elle retrouve SON fil, rien de celui de Bob
    assert fil(alice, site()) == ["qui a peint la Joconde ?"]  # et il survit à un redémarrage du serveur
    assert _client()(url + "assistant")[0] == 401             # sans connexion : rien
