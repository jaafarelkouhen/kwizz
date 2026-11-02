"""Tests de la base SQLite : tables du MLD, contraintes et suppressions en cascade."""
import sqlite3

import pytest

from quizz import auth, quiz_service as qs
from quizz.models import Choix, Question, Quizz

TABLES_DU_MLD = {"utilisateur", "quizz", "question", "choix", "tentative", "reponse"}


def creer_quizz(con, id_createur=None) -> Quizz:
    q = Quizz("Test", questions=[Question("1 + 1 ?", [Choix("2", True), Choix("3")])],
              id_createur=id_createur)
    return qs.charger_quizz(con, qs.enregistrer_quizz(con, q))


def compter(con, table: str) -> int:
    return con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def test_toutes_les_tables_du_mld_existent(con):
    tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert TABLES_DU_MLD <= tables


def test_cles_etrangeres_activees(con):
    assert con.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    with pytest.raises(sqlite3.IntegrityError):
        con.execute("INSERT INTO question (enonce, id_quizz) VALUES ('orpheline', 999)")


def test_login_unique_au_niveau_de_la_base(con):
    con.execute("INSERT INTO utilisateur (login, mot_de_passe_hash) VALUES ('alice', 'x')")
    with pytest.raises(sqlite3.IntegrityError):
        con.execute("INSERT INTO utilisateur (login, mot_de_passe_hash) VALUES ('alice', 'y')")


def test_supprimer_un_quizz_supprime_tout_son_contenu(con):
    u = auth.inscrire(con, "bob", "1234")
    q = creer_quizz(con)
    question = q.questions[0]
    qs.enregistrer_tentative(con, u.id_utilisateur, q, {question.id_question: {question.choix[0].id_choix}})

    qs.supprimer_quizz(con, q.id_quizz)

    for table in ("question", "choix", "tentative", "reponse"):
        assert compter(con, table) == 0, f"la table {table} n'a pas été vidée en cascade"


def test_supprimer_le_createur_garde_ses_quizz(con):
    admin = auth.inscrire(con, "prof", "1234", est_admin=True)
    q = creer_quizz(con, id_createur=admin.id_utilisateur)

    with con:
        con.execute("DELETE FROM utilisateur WHERE id_utilisateur = ?", (admin.id_utilisateur,))

    row = con.execute("SELECT id_createur FROM quizz WHERE id_quizz = ?", (q.id_quizz,)).fetchone()
    assert row is not None and row["id_createur"] is None  # cardinalité 0,1 du MCD (CRÉER)


def test_supprimer_un_joueur_supprime_ses_tentatives(con):
    u = auth.inscrire(con, "bob", "1234")
    q = creer_quizz(con)
    qs.enregistrer_tentative(con, u.id_utilisateur, q, {})

    with con:
        con.execute("DELETE FROM utilisateur WHERE id_utilisateur = ?", (u.id_utilisateur,))

    assert compter(con, "tentative") == 0
