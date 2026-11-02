"""Tests du client IA (T53, US19) avec un FAUX client : aucun appel réseau, aucune clé réelle."""
from types import SimpleNamespace

import pytest

anthropic = pytest.importorskip("anthropic")  # tests ignorés si le SDK n'est pas installé
httpx2 = pytest.importorskip("httpx2")

from quizz import config
from quizz.ia import client


class FauxClient:
    """Imite anthropic.Anthropic() : enregistre la requête et renvoie une réponse prévue."""

    def __init__(self, texte="Bonjour", stop_reason="end_turn", erreur=None):
        self.requetes = []

        def create(**requete):
            self.requetes.append(requete)
            if erreur:
                raise erreur
            return SimpleNamespace(stop_reason=stop_reason, content=[SimpleNamespace(type="text", text=texte)])

        self.beta = SimpleNamespace(messages=SimpleNamespace(create=create))


@pytest.fixture
def ia_active(monkeypatch):
    monkeypatch.setattr(config, "charger_env", lambda *a, **k: None)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.delenv("KWIZZ_IA", raising=False)
    monkeypatch.delenv("KWIZZ_MODELE", raising=False)


def brancher(monkeypatch, faux):
    monkeypatch.setattr(client, "_obtenir_client", lambda: faux)
    return faux


def test_sans_cle_erreur_claire_et_aucun_appel(monkeypatch):
    monkeypatch.setattr(config, "charger_env", lambda *a, **k: None)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("KWIZZ_IA", raising=False)
    faux = brancher(monkeypatch, FauxClient())
    assert not client.ia_disponible()
    with pytest.raises(client.ErreurIA, match="pas configuré"):
        client.demander_texte("sys", "question")
    assert faux.requetes == []


def test_sdk_absent_ia_indisponible(monkeypatch, ia_active):
    monkeypatch.setattr(client, "anthropic", None)
    assert not client.ia_disponible()


def test_requete_envoyee(monkeypatch, ia_active):
    faux = brancher(monkeypatch, FauxClient("Parce que…"))
    assert client.demander_texte("Tu es un prof.", "Pourquoi ?") == "Parce que…"
    [r] = faux.requetes
    assert r["model"] == config.MODELE_PAR_DEFAUT
    assert r["system"] == "Tu es un prof."
    assert r["messages"] == [{"role": "user", "content": "Pourquoi ?"}]
    assert r["output_config"] == {"effort": "low"}
    assert r["fallbacks"] == "default" and r["betas"] == [client.BETA_REPLI]


def test_pas_d_option_de_repli_pour_un_modele_qui_ne_la_propose_pas(monkeypatch, ia_active):
    monkeypatch.setenv("KWIZZ_MODELE", "claude-haiku-5-5")
    faux = brancher(monkeypatch, FauxClient())
    client.demander_texte("s", "p")
    assert "fallbacks" not in faux.requetes[0] and "betas" not in faux.requetes[0]


def test_json_avec_schema(monkeypatch, ia_active):
    faux = brancher(monkeypatch, FauxClient('{"a": 1}'))
    schema = {"type": "object"}
    assert client.demander_json("s", "p", schema) == {"a": 1}
    assert faux.requetes[0]["output_config"]["format"] == {"type": "json_schema", "schema": schema}


@pytest.mark.parametrize("texte, stop_reason, message", [
    ("{pas du json", "end_turn", "illisible"),
    ("", "refusal", "refusé"),
    ('{"a":', "max_tokens", "trop longue"),
    ("   ", "end_turn", "rien répondu"),
])
def test_reponses_inutilisables(monkeypatch, ia_active, texte, stop_reason, message):
    brancher(monkeypatch, FauxClient(texte, stop_reason))
    with pytest.raises(client.ErreurIA, match=message):
        client.demander_json("s", "p", {"type": "object"})


def requete():
    return httpx2.Request("POST", "https://api.anthropic.com/v1/messages")


def reponse(code):
    return httpx2.Response(code, request=requete())


@pytest.mark.parametrize("erreur, message", [
    (anthropic.APIConnectionError(request=requete()), "connexion Internet"),
    (anthropic.APITimeoutError(request=requete()), "trop de temps"),
    (anthropic.AuthenticationError("x", response=reponse(401), body=None), "Clé API refusée"),
    (anthropic.RateLimitError("x", response=reponse(429), body=None), "réessayez dans une minute"),
    (anthropic.InternalServerError("x", response=reponse(500), body=None), "erreur \\(500\\)"),
])
def test_erreurs_de_l_api_traduites(monkeypatch, ia_active, erreur, message):
    brancher(monkeypatch, FauxClient(erreur=erreur))
    with pytest.raises(client.ErreurIA, match=message):
        client.demander_texte("s", "p")
