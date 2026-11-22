"""Données et sécurité (MyKwizz v2.1, Akram) : mots de passe, comptes, journal d'activité."""
import hashlib

import pytest

from quizz import auth, importer, quiz_service as qs  # noqa: F401


def test_hash_jamais_en_clair_et_sale(con):
    auth.inscrire(con, "alice", "motdepasse1")
    auth.inscrire(con, "bob", "motdepasse1")
    h1, h2 = [r[0] for r in con.execute("SELECT mot_de_passe_hash FROM utilisateur ORDER BY login")]
    assert "motdepasse1" not in h1 and h1 != h2           # sel différent → empreintes différentes
    assert h1.startswith(f"pbkdf2${auth.ITERATIONS}$")


@pytest.mark.parametrize("mdp", ["court1", "seulementdeslettres", "12345678"])
def test_regles_mot_de_passe(con, mdp):
    with pytest.raises(auth.ErreurAuth):
        auth.inscrire(con, "alice", mdp)


def test_login_insensible_a_la_casse(con):
    auth.inscrire(con, "Alice", "motdepasse1")
    with pytest.raises(auth.ErreurAuth):
        auth.inscrire(con, "alice", "motdepasse2")
    assert auth.connecter(con, "ALICE", "motdepasse1").login == "Alice"


def test_ancien_hash_v20_rehache_au_login(con):
    sel = "abcd"
    ancien = f"{sel}${hashlib.pbkdf2_hmac('sha256', b'vieuxmdp1', sel.encode(), 100_000).hex()}"
    con.execute("INSERT INTO utilisateur (login, mot_de_passe_hash) VALUES ('vieux', ?)", (ancien,))
    auth.connecter(con, "vieux", "vieuxmdp1")
    nouveau = con.execute("SELECT mot_de_passe_hash FROM utilisateur WHERE login = 'vieux'").fetchone()[0]
    assert nouveau.startswith("pbkdf2$") and auth.verifier("vieuxmdp1", nouveau)


def test_changer_mdp_exige_l_ancien(con):
    u = auth.inscrire(con, "alice", "motdepasse1")
    with pytest.raises(auth.ErreurAuth):
        auth.changer_mot_de_passe(con, u.id_utilisateur, "nouveau123", ancien="faux")
    auth.changer_mot_de_passe(con, u.id_utilisateur, "nouveau123", ancien="motdepasse1")
    auth.connecter(con, "alice", "nouveau123")


def test_dernier_admin_protege(con):
    auth.creer_admin_par_defaut(con)
    admin = con.execute("SELECT id_utilisateur FROM utilisateur").fetchone()[0]
    with pytest.raises(auth.ErreurAuth):
        auth.supprimer_utilisateur(con, admin)
    with pytest.raises(auth.ErreurAuth):
        auth.modifier_utilisateur(con, admin, "admin", False)


def test_crud_utilisateur(con):
    u = auth.inscrire(con, "alice", "motdepasse1")
    auth.modifier_utilisateur(con, u.id_utilisateur, "alice2", True)
    assert [(x["login"], x["admin"]) for x in auth.lister_utilisateurs(con)] == [("alice2", True)]
    auth.inscrire(con, "bob", "motdepasse1", est_admin=True)
    auth.supprimer_utilisateur(con, u.id_utilisateur)
    assert [x["login"] for x in auth.lister_utilisateurs(con)] == ["bob"]


def test_journal_filtre_et_survit_a_la_suppression(con):
    from quizz import journal
    u = auth.inscrire(con, "alice", "motdepasse1")
    auth.inscrire(con, "bob", "motdepasse1", est_admin=True)
    journal.noter(con, u.id_utilisateur, "alice", "connexion")
    journal.noter(con, u.id_utilisateur, "alice", "partie", "Capitales : 3/3")
    journal.noter(con, None, "bob", "quizz_valide", "Capitales")
    assert [l["action"] for l in journal.lister(con, u.id_utilisateur)] == ["partie", "connexion"]
    assert [l["login"] for l in journal.lister(con, action="quizz_valide")] == ["bob"]
    auth.supprimer_utilisateur(con, u.id_utilisateur)
    lignes = journal.lister(con, action="partie")
    assert lignes[0]["login"] == "alice" and lignes[0]["id_utilisateur"] is None
