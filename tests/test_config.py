"""Tests de la configuration IA (US19) : sans clé, l'IA est désactivée, et rien ne plante."""
import pytest

from quizz import config


@pytest.fixture(autouse=True)
def environnement_propre(monkeypatch):
    """Ignore le vrai .env et les variables de la machine pendant ces tests."""
    monkeypatch.setattr(config, "charger_env", lambda *a, **k: None)
    for variable in ("ANTHROPIC_API_KEY", "KWIZZ_IA", "KWIZZ_MODELE"):
        monkeypatch.delenv(variable, raising=False)


def test_sans_cle_l_ia_est_desactivee():
    c = config.config_ia()
    assert not c.activee and not c.cle_presente
    assert c.modele == config.MODELE_PAR_DEFAUT


def test_avec_cle_l_ia_est_active(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    assert config.config_ia().activee


def test_kwizz_ia_non_desactive_meme_avec_une_cle(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setenv("KWIZZ_IA", "non")
    assert not config.config_ia().activee


def test_kwizz_ia_oui_force_sans_cle(monkeypatch):
    monkeypatch.setenv("KWIZZ_IA", "oui")
    assert config.config_ia().activee


def test_modele_personnalise(monkeypatch):
    monkeypatch.setenv("KWIZZ_MODELE", "claude-haiku-5-5")
    assert config.config_ia().modele == "claude-haiku-5-5"


def test_env_example_ne_contient_pas_de_vraie_cle():
    contenu = (config.RACINE / ".env.example").read_text(encoding="utf-8")
    assert "ANTHROPIC_API_KEY=\n" in contenu


def test_env_est_ignore_par_git():
    lignes = (config.RACINE / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert ".env" in lignes
