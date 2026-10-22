"""Tests du menu d'accueil console : on simule les saisies clavier avec monkeypatch."""
from quizz import auth
from quizz.ui import cli


def simuler_saisies(monkeypatch, *saisies):
    """Simule le clavier : input() ET la saisie masquée des mots de passe lisent la même liste."""
    reponses = iter(saisies)
    monkeypatch.setattr("builtins.input", lambda _message="": next(reponses))
    monkeypatch.setattr(cli.getpass, "getpass", lambda _message="": next(reponses))


def test_inscription_connecte_directement(con, monkeypatch):
    simuler_saisies(monkeypatch, "alice", "secret", "secret")
    user = cli.ecran_inscription(con)
    assert user is not None and user.login == "alice"


def test_inscription_confirmation_differente(con, monkeypatch, capsys):
    simuler_saisies(monkeypatch, "alice", "secret", "autre")
    assert cli.ecran_inscription(con) is None
    assert "ne correspondent pas" in capsys.readouterr().out


def test_inscription_login_trop_court(con, monkeypatch, capsys):
    simuler_saisies(monkeypatch, "al", "secret", "secret")
    assert cli.ecran_inscription(con) is None
    assert "3 caractères" in capsys.readouterr().out


def test_connexion_reussie_au_deuxieme_essai(con, monkeypatch):
    auth.inscrire(con, "bob", "1234")
    simuler_saisies(monkeypatch, "bob", "faux", "bob", "1234")
    assert cli.ecran_connexion(con).login == "bob"


def test_connexion_bloquee_apres_trois_essais(con, monkeypatch, capsys):
    auth.inscrire(con, "bob", "1234")
    simuler_saisies(monkeypatch, *["bob", "faux"] * cli.ESSAIS_CONNEXION)
    assert cli.ecran_connexion(con) is None
    assert "Trop d'essais" in capsys.readouterr().out


def test_premiere_connexion_admin_force_le_changement(con, monkeypatch, capsys):
    auth.creer_admin_par_defaut(con)
    simuler_saisies(monkeypatch, "admin", "admin",          # connexion
                    "abc", "abc",                            # trop court → refusé
                    "solide1", "solide2",                    # confirmation différente → refusé
                    "solide1", "solide1")                    # accepté
    assert cli.ecran_connexion(con).est_admin
    assert auth.connecter(con, "admin", "solide1")
    assert "mot de passe administrateur par défaut" in capsys.readouterr().out
