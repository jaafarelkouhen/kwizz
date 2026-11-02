"""Tests de l'origine des quizz (T55) et de la migration des anciennes bases."""
import sqlite3
from pathlib import Path

import pytest

from quizz import database, quiz_service as qs
from quizz.importer import lire_quizz
from quizz.models import Choix, Question, Quizz

EXEMPLE = Path(__file__).resolve().parent.parent / "data" / "exemples" / "capitales.txt"


def un_quizz(**kw) -> Quizz:
    return Quizz("X", questions=[Question("?", [Choix("a", True), Choix("b")])], **kw)


def test_source_par_defaut_manuel(con):
    assert qs.charger_quizz(con, qs.enregistrer_quizz(con, un_quizz())).source == "manuel"


def test_un_quizz_importe_est_marque_fichier(con):
    q = lire_quizz(EXEMPLE)
    assert q.source == "fichier"
    assert qs.charger_quizz(con, qs.enregistrer_quizz(con, q)).source == "fichier"


def test_source_ia_conservee(con):
    qs.enregistrer_quizz(con, un_quizz(source="ia"))
    assert qs.lister_quizz(con)[0].source == "ia"


def test_source_inconnue_refusee_par_la_base(con):
    with pytest.raises(sqlite3.IntegrityError):
        qs.enregistrer_quizz(con, un_quizz(source="internet"))


def test_migration_d_une_ancienne_base(tmp_path):
    ancienne = tmp_path / "ancienne.db"
    c = sqlite3.connect(ancienne)  # schéma d'avant le sprint IA : pas de colonne source
    c.execute("CREATE TABLE quizz (id_quizz INTEGER PRIMARY KEY AUTOINCREMENT, titre TEXT NOT NULL, "
              "description TEXT, duree_limite INTEGER, date_creation TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, "
              "id_createur INTEGER)")
    c.execute("INSERT INTO quizz (titre) VALUES ('Ancien quizz')")
    c.commit(); c.close()

    con = database.connexion(ancienne)

    [q] = qs.lister_quizz(con)
    assert (q.titre, q.source) == ("Ancien quizz", "manuel")
    con.close()
