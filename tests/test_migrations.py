"""Tests des migrations versionnées du schéma (V1, specs/001-migration-user-version)."""
import os
import sqlite3

import pytest

from quizz import database
from quizz.database import SCHEMA, connexion

TABLES = ("utilisateur", "quizz", "question", "choix", "tentative", "reponse")
INDEX_V1 = {"ix_tentative_quizz", "ix_tentative_joueur", "ix_question_quizz", "ix_choix_question"}
DERNIERE = len(database.MIGRATIONS)


def base_v20(chemin, avec_source=True) -> None:
    """Fichier SQLite tel que l'écrivait Kwizz v2.0 (user_version = 0), garni de données."""
    con = sqlite3.connect(chemin)
    schema = SCHEMA if avec_source else SCHEMA.replace(
        "source        TEXT NOT NULL DEFAULT 'manuel' CHECK (source IN ('manuel', 'fichier', 'ia'))", "x TEXT")
    con.executescript(schema)
    con.executescript("""
        INSERT INTO utilisateur (login, mot_de_passe_hash, est_admin) VALUES ('admin', 'h0', 1), ('alice', 'h1', 0);
        INSERT INTO quizz (titre, description, duree_limite, id_createur) VALUES ('Capitales', 'Europe', 60, 1);
        INSERT INTO question (enonce, ordre, id_quizz) VALUES ('France ?', 0, 1), ('Italie ?', 1, 1);
        INSERT INTO choix (texte, est_correct, id_question) VALUES ('Paris', 1, 1), ('Lyon', 0, 1),
                                                                   ('Rome', 1, 2), ('Milan', 0, 2);
        INSERT INTO tentative (score, nb_questions, duree_secondes, id_utilisateur, id_quizz)
            VALUES (2, 2, 30, 2, 1), (1, 2, 45, 2, 1);
        INSERT INTO reponse (id_tentative, id_choix) VALUES (1, 1), (1, 3), (2, 2), (2, 3);
    """)
    con.commit()
    con.close()


def instantane(con) -> dict:
    return {t: sorted(tuple(r) for r in con.execute(f"SELECT * FROM {t}")) for t in TABLES}


def version(con) -> int:
    return con.execute("PRAGMA user_version").fetchone()[0]


def structure(con) -> list:
    return [tuple(r) for r in con.execute(
        "SELECT type, name, tbl_name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY name")]


# ---------------------------------------------------------------- US1 : base v2.0 sans perte
def test_base_v20_migree_sans_perte(tmp_path):
    fichier = tmp_path / "v20.db"
    base_v20(fichier)
    avant = sqlite3.connect(fichier)
    attendu = instantane(avant)
    avant.close()

    con = connexion(fichier)

    apres = instantane(con)
    # migrations 3 et 4 : thème par défaut, quizz existants restés publiés, jamais testés ni validés
    assert [r[-5:] for r in apres["quizz"]] == [("Divers", "publie", None, None, 0)]  # + migration 5 : non archivé
    apres["quizz"] = [r[:-5] for r in apres["quizz"]]
    # migration 6 : questions actives, sans explication, et résultats reconstruits depuis les choix cochés
    assert [r[-2:] for r in apres["question"]] == [(1, None), (1, None)]
    apres["question"] = [r[:-2] for r in apres["question"]]
    # migration 8 : aucun compte supprimé
    assert [r[-1] for r in apres["utilisateur"]] == [0, 0]
    apres["utilisateur"] = [r[:-1] for r in apres["utilisateur"]]
    assert sorted(tuple(r) for r in con.execute("SELECT * FROM resultat_question")) == [
        (1, 1, 1), (1, 2, 1), (2, 1, 0), (2, 2, 1)]  # partie 1 : Paris + Rome ; partie 2 : Lyon (faux) + Rome
    assert apres == attendu
    assert version(con) == DERNIERE
    con.close()


def test_base_sans_colonne_source(tmp_path):
    fichier = tmp_path / "ancienne.db"
    base_v20(fichier, avec_source=False)

    con = connexion(fichier)

    colonnes = {r["name"] for r in con.execute("PRAGMA table_info(quizz)")}
    assert "source" in colonnes
    assert con.execute("SELECT source FROM quizz").fetchone()[0] == "manuel"
    con.close()


def test_base_a_jour_sans_ecriture(tmp_path):
    fichier = tmp_path / "a_jour.db"
    connexion(fichier).close()
    date_avant = os.stat(fichier).st_mtime_ns

    con = connexion(fichier)

    assert con.total_changes == 0
    con.close()
    assert os.stat(fichier).st_mtime_ns == date_avant


# ---------------------------------------------------------------- US2 : base neuve à jour
def test_base_neuve_a_jour(con):
    assert version(con) == DERNIERE
    index = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'index'")}
    assert INDEX_V1 <= index


def test_neuve_identique_a_migree(tmp_path):
    fichier = tmp_path / "v20.db"
    base_v20(fichier)
    migree, neuve = connexion(fichier), connexion(":memory:")

    assert structure(migree) == structure(neuve)
    migree.close()
    neuve.close()


# ---------------------------------------------------------------- US3 : ajouter une migration
def test_migration_ajoutee_appliquee_seule(tmp_path, monkeypatch):
    fichier = tmp_path / "base.db"
    connexion(fichier).close()
    appels = []

    def m_essai(c):
        appels.append(1)
        c.execute("CREATE TABLE essai (x)")

    monkeypatch.setattr(database, "MIGRATIONS", database.MIGRATIONS + [m_essai])
    con = connexion(fichier)

    assert appels == [1]
    assert version(con) == DERNIERE + 1
    assert con.execute("SELECT name FROM sqlite_master WHERE name = 'essai'").fetchone()
    con.close()


def test_migration_en_echec_ne_laisse_rien(tmp_path, monkeypatch):
    fichier = tmp_path / "base.db"
    connexion(fichier).close()

    def m_cassee(c):
        c.execute("CREATE TABLE a_moitie (x)")
        raise RuntimeError("panne au milieu")

    monkeypatch.setattr(database, "MIGRATIONS", database.MIGRATIONS + [m_cassee])
    with pytest.raises(RuntimeError, match="panne"):
        connexion(fichier)

    monkeypatch.undo()
    con = connexion(fichier)
    assert version(con) == DERNIERE
    assert con.execute("SELECT name FROM sqlite_master WHERE name = 'a_moitie'").fetchone() is None
    con.close()


def test_base_plus_recente_refusee(tmp_path):
    fichier = tmp_path / "futur.db"
    connexion(fichier).close()
    c = sqlite3.connect(fichier)
    c.execute("PRAGMA user_version = 99")
    c.close()

    with pytest.raises(RuntimeError, match="plus récente"):
        connexion(fichier)

    c = sqlite3.connect(fichier)
    assert version(c) == 99
    c.close()
