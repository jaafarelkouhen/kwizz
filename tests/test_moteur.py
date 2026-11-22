"""Moteur des quizz et IA (MyKwizz v2.1, Sami) : thèmes, validation, archivage, résultats par question,
explications gardées, statistiques, règles de l'assistant (sans les fiches de cours)."""
import pytest

from quizz import auth, importer, quiz_service as qs
from quizz.ia import client, explications
from quizz.rag import assistant


@pytest.fixture(autouse=True)
def sans_ia(monkeypatch):
    monkeypatch.setattr(client, "ia_disponible", lambda: False)


def _quizz(con, titre="Q"):
    q = importer.quizz_depuis_dict({"format": "kwizz-quizz", "version": 1, "titre": titre, "questions": [
        {"enonce": "Capitale de l'Italie ?", "choix": [{"texte": "Rome", "correct": True}, {"texte": "Milan"}]},
        {"enonce": "Capitale du Portugal ?", "choix": [{"texte": "Lisbonne", "correct": True}, {"texte": "Porto"}]}]})
    return qs.charger_quizz(con, qs.enregistrer_quizz(con, q))


def _jouer(con, id_utilisateur, q, justes):
    """Coche la bonne réponse des `justes` premières questions, la mauvaise des autres."""
    rep = {x.id_question: {(x.choix[0] if i < justes else x.choix[1]).id_choix} for i, x in enumerate(q.questions)}
    return qs.enregistrer_tentative(con, id_utilisateur, q, rep, 30)


def _brouillon(con):
    q = importer.quizz_depuis_dict({"format": "kwizz-quizz", "version": 1, "titre": "Brouillon",
                                    "questions": [{"enonce": "?", "choix": [{"texte": "a", "correct": True},
                                                                            {"texte": "b"}]}]})
    q.statut = "brouillon"
    return qs.enregistrer_quizz(con, q)


def test_theme_enregistre_et_relu(con):
    q = importer.quizz_depuis_dict({"format": "kwizz-quizz", "version": 1, "titre": "T", "theme": "SVT",
                                    "questions": [{"enonce": "?", "choix": [{"texte": "a", "correct": True},
                                                                            {"texte": "b"}]}]})
    assert qs.charger_quizz(con, qs.enregistrer_quizz(con, q)).theme == "SVT"


def test_brouillon_invisible_puis_valide_apres_test(con):
    id_q = _brouillon(con)
    assert [q.titre for q in qs.lister_quizz(con, publies_seulement=True)] == []
    with pytest.raises(qs.ErreurQuizz):
        qs.valider_publication(con, id_q)          # pas encore testé
    qs.noter_test(con, id_q)
    qs.valider_publication(con, id_q)
    assert [q.titre for q in qs.lister_quizz(con, publies_seulement=True)] == ["Brouillon"]


def test_modifier_repasse_en_brouillon_et_efface_le_test(con):
    id_q = _brouillon(con)
    qs.noter_test(con, id_q)
    qs.valider_publication(con, id_q)
    q = qs.charger_quizz(con, id_q)
    q.titre = "Corrigé"
    qs.modifier_quizz(con, q, repasser_en_brouillon=True)
    q = qs.charger_quizz(con, id_q)
    assert (q.statut, q.teste_le, q.valide_le) == ("brouillon", None, None)


def test_supprimer_un_quizz_joue_l_archive_et_garde_l_historique(con):
    u = auth.inscrire(con, "alice", "motdepasse1")
    joue, jamais = _brouillon(con), _brouillon(con)
    q = qs.charger_quizz(con, joue)
    qs.enregistrer_tentative(con, u.id_utilisateur, q, {q.questions[0].id_question: {q.questions[0].choix[0].id_choix}})

    assert qs.supprimer_quizz(con, joue) == 1            # archivé, 1 partie gardée
    assert qs.supprimer_quizz(con, jamais) == 0          # jamais joué : vraiment effacé
    assert [h.score for h in qs.historique(con, u.id_utilisateur)] == [1]
    assert qs.lister_quizz(con) == []                    # invisible partout…
    assert [x.id_quizz for x in qs.lister_quizz(con, inclure_archives=True)] == [joue]  # …mais toujours en base
    assert con.execute("SELECT COUNT(*) FROM quizz WHERE id_quizz = ?", (jamais,)).fetchone()[0] == 0


def test_resultats_par_question_et_corrige_garde_apres_modification(con):
    u = auth.inscrire(con, "alice", "motdepasse1")
    q = _quizz(con)
    t = _jouer(con, u.id_utilisateur, q, justes=1)
    assert sorted(r[0] for r in con.execute("SELECT juste FROM resultat_question WHERE id_tentative = ?",
                                            (t.id_tentative,))) == [0, 1]                 # V3 : 1 ligne par question

    q.questions[0].enonce = "Capitale de l'Italie (corrigée) ?"
    qs.modifier_quizz(con, q)                                                             # quizz déjà joué
    assert [x.enonce for x in qs.charger_quizz(con, q.id_quizz).questions][0] == "Capitale de l'Italie (corrigée) ?"

    c = qs.corrige_tentative(con, t.id_tentative)                                         # V7 : corrigé intact
    assert [d["enonce"] for d in c["detail"]] == ["Capitale de l'Italie ?", "Capitale du Portugal ?"]
    assert [d["juste"] for d in c["detail"]] == [True, False]
    assert [ch["coche"] for ch in c["detail"][1]["choix"]] == [False, True]               # Porto coché


def test_modifier_un_quizz_jamais_joue_efface_ses_anciennes_questions(con):
    q = _quizz(con)
    qs.modifier_quizz(con, q)
    assert con.execute("SELECT COUNT(*) FROM question WHERE id_quizz = ?", (q.id_quizz,)).fetchone()[0] == 2


def test_explication_gardee_apres_le_premier_appel(con, monkeypatch):
    appels = []
    monkeypatch.setattr(client, "demander_texte", lambda s, p, **k: appels.append(p) or "Rome est la capitale.")
    question = _quizz(con).questions[0]
    assert explications.expliquer(con, question) == "Rome est la capitale."
    relue, _ = qs.charger_question(con, question.id_question)
    assert explications.expliquer(con, relue) == "Rome est la capitale." and len(appels) == 1  # 2e fois sans IA


def test_restaurer_un_quizz_archive(con):
    u = auth.inscrire(con, "alice", "motdepasse1")
    q = _quizz(con)
    _jouer(con, u.id_utilisateur, q, justes=2)
    qs.supprimer_quizz(con, q.id_quizz)                                 # joué → archivé
    assert qs.charger_quizz(con, q.id_quizz).archive and qs.lister_quizz(con) == []
    qs.restaurer_quizz(con, q.id_quizz)
    restaure = qs.charger_quizz(con, q.id_quizz)
    assert not restaure.archive and restaure.statut == "brouillon"     # revient en brouillon, à revalider
    assert [x.titre for x in qs.lister_quizz(con)] == ["Q"]
    with pytest.raises(qs.ErreurQuizz):
        qs.restaurer_quizz(con, q.id_quizz)                             # déjà restauré


def test_questions_triees_de_la_moins_reussie_a_la_mieux_reussie(con):
    u = auth.inscrire(con, "alice", "motdepasse1")
    a, b = _quizz(con, "A"), _quizz(con, "B")
    _jouer(con, u.id_utilisateur, a, justes=1)          # A : 1re juste, 2e fausse
    _jouer(con, u.id_utilisateur, a, justes=0)          # A : les deux fausses
    _jouer(con, u.id_utilisateur, b, justes=2)
    toutes = qs.stats_questions(con)
    assert [(q["titre"], q["enonce"], q["reussite"]) for q in toutes[:2]] == [
        ("A", "Capitale du Portugal ?", 0), ("A", "Capitale de l'Italie ?", 50)]
    assert [q["reussite"] for q in toutes] == sorted(q["reussite"] for q in toutes)
    assert {q["titre"] for q in qs.stats_questions(con, b.id_quizz)} == {"B"}       # filtre par quizz


def test_assistant_refuse_de_souffler_pendant_une_partie():
    enonce = "Quel est le symbole chimique du sodium ?"
    assert assistant.repondre(enonce, [], [enonce])["intention"] == "triche"


def test_garde_fous_retire_les_liens_inventes():
    texte = assistant.garde_fous("Voir https://invente.example et https://www.lumni.fr", "https://www.lumni.fr")
    assert "invente" not in texte and "https://www.lumni.fr" in texte


def test_reponse_hors_fiches_sans_sources(monkeypatch):
    monkeypatch.setattr(client, "ia_disponible", lambda: True)
    monkeypatch.setattr(client, "demander_conversation", lambda s, m, **k: "Rayleigh… (réponse hors fiches)")
    assert assistant.repondre("pourquoi le ciel est bleu", [])["sources"] == []


def test_modifier_sans_option_garde_le_quizz_publie(con):
    """L'application de bureau n'a pas de cycle de validation : un quizz modifié reste publié."""
    id_q = _brouillon(con)
    qs.noter_test(con, id_q)
    qs.valider_publication(con, id_q)
    q = qs.charger_quizz(con, id_q)
    q.titre = "Corrigé"
    qs.modifier_quizz(con, q)
    assert qs.charger_quizz(con, id_q).statut == "publie"
