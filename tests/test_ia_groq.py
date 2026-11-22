"""Groq, l'IA gratuite utilisée quand il n'y a pas de clé Claude (v2.2). Fausse Groq : ni réseau ni clé."""
import io
import json
import urllib.error

import pytest

from quizz.ia import client


@pytest.fixture
def groq(monkeypatch):
    """Configure Groq seul et capture la requête envoyée ; renvoie la liste des requêtes vues."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("KWIZZ_IA", "auto")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test")
    monkeypatch.delenv("KWIZZ_GROQ_MODELE", raising=False)
    vues = type("Vues", (list,), {})()  # une liste à laquelle on peut ajouter « repondre »

    def fausse_reponse(contenu="Rome.", fin="stop"):
        def urlopen(requete, timeout):
            vues.append(requete)
            corps = {"choices": [{"message": {"content": contenu}, "finish_reason": fin}]}
            return io.BytesIO(json.dumps(corps).encode())
        monkeypatch.setattr(client.urllib.request, "urlopen", urlopen)
    fausse_reponse()
    vues.repondre = fausse_reponse
    return vues


def test_groq_utilise_sans_cle_claude_et_requete_correcte(groq):
    assert client.fournisseur() == "groq" and client.ia_disponible()
    systeme = [{"type": "text", "text": "Règles."}, {"type": "text", "text": "Fiches.", "cache_control": {"type": "ephemeral"}}]
    assert client.demander_conversation(systeme, [{"role": "user", "content": "Capitale de l'Italie ?"}]) == "Rome."
    requete = groq[0]
    corps = json.loads(requete.data)
    assert requete.full_url == client.URL_GROQ and requete.get_header("Authorization") == "Bearer gsk_test"
    assert corps["model"] == "openai/gpt-oss-120b"
    assert corps["messages"][0] == {"role": "system", "content": "Règles.\n\nFiches."}  # blocs Claude aplatis
    assert corps["messages"][1]["content"] == "Capitale de l'Italie ?"


def test_claude_reste_prioritaire_quand_les_deux_cles_sont_la(groq, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    attendu = "claude" if client.anthropic is not None else "groq"
    assert client.fournisseur() == attendu


def test_kwizz_ia_non_coupe_aussi_groq(groq, monkeypatch):
    monkeypatch.setenv("KWIZZ_IA", "non")
    assert client.fournisseur() is None and not client.ia_disponible()


def test_groq_en_mode_json(groq):
    groq.repondre('{"titre": "T", "questions": []}')
    assert client.demander_json("Génère.", "Thème : Rome", {"type": "object"}) == {"titre": "T", "questions": []}
    corps = json.loads(groq[0].data)
    assert corps["response_format"] == {"type": "json_object"} and "schéma JSON" in corps["messages"][0]["content"]


@pytest.mark.parametrize("code, extrait", [(401, "Clé Groq refusée"), (429, "Quota gratuit"), (503, "(503)")])
def test_erreurs_groq_lisibles(groq, monkeypatch, code, extrait):
    def urlopen(requete, timeout):
        raise urllib.error.HTTPError(requete.full_url, code, "erreur", {}, io.BytesIO(b"{}"))
    monkeypatch.setattr(client.urllib.request, "urlopen", urlopen)
    with pytest.raises(client.ErreurIA, match=extrait):
        client.demander_texte("Système.", "Question ?")


def test_reponse_coupee_signalee(groq):
    groq.repondre("Rome est…", fin="length")
    with pytest.raises(client.ErreurIA, match="trop longue"):
        client.demander_texte("Système.", "Question ?")
