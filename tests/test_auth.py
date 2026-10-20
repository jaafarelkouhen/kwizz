import pytest

from quizz import auth


def test_mot_de_passe_jamais_en_clair():
    h = auth.hacher("secret")
    assert "secret" not in h
    assert auth.verifier("secret", h)
    assert not auth.verifier("autre", h)


def test_inscription_puis_connexion(con):
    auth.inscrire(con, "alice", "motdepasse")
    u = auth.connecter(con, "alice", "motdepasse")
    assert u.login == "alice" and not u.est_admin


def test_login_unique(con):
    auth.inscrire(con, "alice", "motdepasse")
    with pytest.raises(auth.ErreurAuth):
        auth.inscrire(con, "alice", "autre1234")


def test_mauvais_mot_de_passe(con):
    auth.inscrire(con, "alice", "motdepasse")
    with pytest.raises(auth.ErreurAuth):
        auth.connecter(con, "alice", "faux")


def test_admin_par_defaut(con):
    auth.creer_admin_par_defaut(con)
    auth.creer_admin_par_defaut(con)  # ne doit pas planter la 2e fois
    assert auth.connecter(con, "admin", "admin").est_admin
