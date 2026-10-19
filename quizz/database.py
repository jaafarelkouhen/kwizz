"""Accès à la base SQLite : connexion et création des tables (cf. MLD)."""
import sqlite3
import sys
from pathlib import Path

# En .exe (PyInstaller), __file__ pointe vers un dossier temporaire effacé à la fermeture :
# on range alors la base à côté de l'exécutable.
if getattr(sys, "frozen", False):
    CHEMIN_PAR_DEFAUT = Path(sys.executable).resolve().parent / "quizz.db"
else:
    CHEMIN_PAR_DEFAUT = Path(__file__).resolve().parent.parent / "quizz.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS utilisateur (
    id_utilisateur    INTEGER PRIMARY KEY AUTOINCREMENT,
    login             TEXT UNIQUE NOT NULL,
    mot_de_passe_hash TEXT NOT NULL,
    est_admin         INTEGER NOT NULL DEFAULT 0,
    date_creation     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS quizz (
    id_quizz      INTEGER PRIMARY KEY AUTOINCREMENT,
    titre         TEXT NOT NULL,
    description   TEXT,
    duree_limite  INTEGER,
    date_creation TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    id_createur   INTEGER REFERENCES utilisateur(id_utilisateur) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS question (
    id_question INTEGER PRIMARY KEY AUTOINCREMENT,
    enonce      TEXT NOT NULL,
    ordre       INTEGER NOT NULL DEFAULT 0,
    id_quizz    INTEGER NOT NULL REFERENCES quizz(id_quizz) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS choix (
    id_choix    INTEGER PRIMARY KEY AUTOINCREMENT,
    texte       TEXT NOT NULL,
    est_correct INTEGER NOT NULL DEFAULT 0,
    id_question INTEGER NOT NULL REFERENCES question(id_question) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tentative (
    id_tentative   INTEGER PRIMARY KEY AUTOINCREMENT,
    date_passage   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    score          INTEGER NOT NULL,
    nb_questions   INTEGER NOT NULL,
    duree_secondes INTEGER,
    id_utilisateur INTEGER NOT NULL REFERENCES utilisateur(id_utilisateur) ON DELETE CASCADE,
    id_quizz       INTEGER NOT NULL REFERENCES quizz(id_quizz) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS reponse (
    id_tentative INTEGER NOT NULL REFERENCES tentative(id_tentative) ON DELETE CASCADE,
    id_choix     INTEGER NOT NULL REFERENCES choix(id_choix) ON DELETE CASCADE,
    PRIMARY KEY (id_tentative, id_choix)
);
"""


def connexion(chemin=CHEMIN_PAR_DEFAUT) -> sqlite3.Connection:
    """Ouvre la base (la crée si besoin) et renvoie la connexion.

    Passer ":memory:" pour une base temporaire (utile pour les tests).
    """
    con = sqlite3.connect(chemin)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(SCHEMA)
    return con
