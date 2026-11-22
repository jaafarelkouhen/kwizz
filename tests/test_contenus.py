"""Contenus (MyKwizz v2.1, Jaafar) : quizz par matière, fiches de cours, couverture des questions."""
import pytest

from quizz import importer, quiz_service as qs
from quizz.ia import client
from quizz.rag import assistant, retriever


@pytest.fixture(autouse=True)
def sans_ia(monkeypatch):
    monkeypatch.setattr(client, "ia_disponible", lambda: False)


def test_tous_les_exemples_ont_theme_et_minuterie():
    from pathlib import Path
    dossier = Path(__file__).resolve().parent.parent / "data" / "exemples"
    themes = set()
    for f in dossier.glob("*.txt"):
        q = importer.lire_quizz(f)
        qs.valider(q)
        assert q.theme != "Divers" and q.duree_limite, f.name
        themes.add(q.theme)
    assert {"Culture générale", "Code", "Histoire", "Mathématiques", "Physique-Chimie", "SVT"} <= themes


@pytest.mark.parametrize("question, fiche", [
    ("combien de chromosomes chez l'humain", "svt.md"),
    ("c'est quoi la loi d'Ohm", "physique_chimie.md"),
    ("comment calculer le discriminant", "mathematiques.md"),
    ("quand est tombé le mur de Berlin", "histoire.md"),
    ("différence entre une pile et une file", "code.md"),
    ("qui a peint la Joconde", "culture_generale.md"),
])
def test_retriever_trouve_la_bonne_fiche(question, fiche):
    assert retriever.chercher(question)[0].passage.fiche == fiche


def test_assistant_sans_ia_repond_avec_les_fiches():
    r = assistant.repondre("combien de chromosomes chez l'humain", [])
    assert r["mode"] == "fiches" and "46" in r["reponse"] and r["sources"][0]["liens"]


def test_assistant_avec_ia_recoit_toutes_les_fiches_en_cache_et_l_historique(monkeypatch):
    vu = {}
    monkeypatch.setattr(client, "ia_disponible", lambda: True)
    monkeypatch.setattr(client, "demander_conversation",
                        lambda systeme, messages, **k: vu.update(s=systeme, m=messages) or "46 chromosomes. (fiche : SVT)")
    r = assistant.repondre("et chez les gamètes ?", [{"question": "combien de chromosomes", "reponse": "46."}])
    fiches = vu["s"][1]
    assert r["mode"] == "ia" and fiches["cache_control"] == {"type": "ephemeral"}
    assert "geographie.md" in fiches["text"] and "46 chromosomes" in fiches["text"]   # toutes les fiches
    assert [m["role"] for m in vu["m"]] == ["user", "assistant", "user"]            # vrai fil de discussion


def test_chaque_question_des_quizz_a_sa_reponse_dans_les_fiches():
    """L'assistant doit pouvoir expliquer chaque question : la bonne réponse est dans une section de fiche,
    et la recherche trouve cette section à partir de l'énoncé. Nouveau quizz d'exemple = compléter les fiches."""
    from pathlib import Path
    sections = [(p, set(retriever.normaliser(p.section + " " + p.texte))) for p in retriever.charger()[0]]
    oublis = []
    for f in sorted((Path(__file__).resolve().parent.parent / "data" / "exemples").glob("*.txt")):
        for x in importer.lire_quizz(f).questions:
            mots = [set(retriever.normaliser(c.texte)) for c in x.bonnes_reponses()]
            couvrantes = [p for p, m in sections if all(mb <= m for mb in mots)]
            trouvees = [r.passage for r in retriever.chercher(x.enonce, k=3)]
            if not any(p in couvrantes for p in trouvees):
                oublis.append(f"{f.name} : {x.enonce}")
    assert not oublis, "Questions sans réponse trouvable dans les fiches :\n" + "\n".join(oublis)
