"""Accès à la base SQLite : connexion, création des tables (cf. MLD) et migrations numérotées.

Schéma 1 : colonne quizz.source garantie. Schéma 2 : index des clés étrangères.
"""
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
    id_createur   INTEGER REFERENCES utilisateur(id_utilisateur) ON DELETE SET NULL,
    source        TEXT NOT NULL DEFAULT 'manuel' CHECK (source IN ('manuel', 'fichier', 'ia'))
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
    migrer(con)
    return con


def migrer(con: sqlite3.Connection) -> None:
    """Applique à la base les migrations qu'elle n'a pas encore reçues.

    `PRAGMA user_version` = nombre de migrations déjà appliquées (0 pour une base v2.0 ou neuve,
    car SCHEMA décrit l'état v2.0). Chaque migration et sa nouvelle version sont écrites dans une
    seule transaction : en cas d'échec, la base reste à la version d'avant.
    """
    derniere = len(MIGRATIONS)
    actuelle = con.execute("PRAGMA user_version").fetchone()[0]
    if actuelle > derniere:
        raise RuntimeError(f"Base créée par une version plus récente de Kwizz (schéma {actuelle}, "
                           f"cette version connaît {derniere}) : mettez l'application à jour.")
    if actuelle == derniere:
        return  # cas de chaque requête du serveur web : ni verrou ni écriture
    for numero in range(actuelle + 1, derniere + 1):
        con.execute("BEGIN IMMEDIATE")  # verrou d'écriture : une autre appli ne migre pas en même temps
        try:
            if con.execute("PRAGMA user_version").fetchone()[0] < numero:
                MIGRATIONS[numero - 1](con)
                con.execute(f"PRAGMA user_version = {numero}")
            con.commit()
        except BaseException:
            con.rollback()
            raise


def _m1_colonne_source(con: sqlite3.Connection) -> None:
    """Origine des quizz (sprint IA, T55) ; une base v2.0 l'a déjà, une plus ancienne non."""
    colonnes = {r["name"] for r in con.execute("PRAGMA table_info(quizz)")}
    if "source" not in colonnes:
        con.execute("ALTER TABLE quizz ADD COLUMN source TEXT NOT NULL DEFAULT 'manuel' "
                    "CHECK (source IN ('manuel', 'fichier', 'ia'))")


def _m2_index(con: sqlite3.Connection) -> None:
    """Index des clés étrangères : accueil, classement, historique et chargement d'un quizz."""
    con.execute("CREATE INDEX IF NOT EXISTS ix_tentative_quizz ON tentative(id_quizz, id_utilisateur)")
    con.execute("CREATE INDEX IF NOT EXISTS ix_tentative_joueur ON tentative(id_utilisateur, date_passage)")
    con.execute("CREATE INDEX IF NOT EXISTS ix_question_quizz ON question(id_quizz, ordre)")
    con.execute("CREATE INDEX IF NOT EXISTS ix_choix_question ON choix(id_question)")


# Ajouter à la fin ; ne jamais modifier ni réordonner une migration publiée (n° i = MIGRATIONS[i - 1]).
def _m3_theme(con: sqlite3.Connection) -> None:
    """V2 : chaque quizz appartient à un thème (Culture, Code, Histoire, Maths…) pour filtrer l'accueil."""
    con.execute("ALTER TABLE quizz ADD COLUMN theme TEXT NOT NULL DEFAULT 'Divers'")


def _m4_validation_et_journal(con: sqlite3.Connection) -> None:
    """V2 : cycle brouillon → testé → publié, et journal de toutes les actions des utilisateurs.

    Les quizz déjà en base restent publiés : les joueurs ne perdent rien.
    """
    con.execute("ALTER TABLE quizz ADD COLUMN statut TEXT NOT NULL DEFAULT 'publie' "
                "CHECK (statut IN ('brouillon', 'publie'))")
    con.execute("ALTER TABLE quizz ADD COLUMN teste_le TEXT")
    con.execute("ALTER TABLE quizz ADD COLUMN valide_le TEXT")
    con.execute("""CREATE TABLE journal (
        id_journal     INTEGER PRIMARY KEY AUTOINCREMENT,
        date_action    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        id_utilisateur INTEGER REFERENCES utilisateur(id_utilisateur) ON DELETE SET NULL,
        login          TEXT NOT NULL,
        action         TEXT NOT NULL,
        detail         TEXT NOT NULL DEFAULT ''
    )""")
    con.execute("CREATE INDEX ix_journal_utilisateur ON journal(id_utilisateur, id_journal)")



def _m5_archive(con: sqlite3.Connection) -> None:
    """V2 (audit, point 2) : supprimer un quizz déjà joué l'archive au lieu d'effacer l'historique des joueurs."""
    con.execute("ALTER TABLE quizz ADD COLUMN archive INTEGER NOT NULL DEFAULT 0")



def _m6_v21(con: sqlite3.Connection) -> None:
    """v2.1 « données fiables » (docs/PROCHAINE-VERSION.md, stories V2, V3, V5, V6).

    - question.active : modifier un quizz déjà joué désactive ses anciennes questions au lieu de les effacer,
      donc le corrigé des parties passées reste lisible ;
    - question.explication : l'explication de l'IA est gardée, le 2e « Pourquoi ? » est instantané et gratuit ;
    - resultat_question : juste / faux pour chaque question de chaque partie (corrigé, statistiques) ;
    - session et echec_connexion : connexions et anti-force brute qui survivent à un redémarrage.
    """
    con.execute("ALTER TABLE question ADD COLUMN active INTEGER NOT NULL DEFAULT 1")
    con.execute("ALTER TABLE question ADD COLUMN explication TEXT")
    con.execute("""CREATE TABLE resultat_question (
        id_tentative INTEGER NOT NULL REFERENCES tentative(id_tentative) ON DELETE CASCADE,
        id_question  INTEGER NOT NULL REFERENCES question(id_question) ON DELETE CASCADE,
        juste        INTEGER NOT NULL,
        PRIMARY KEY (id_tentative, id_question)
    )""")
    con.execute("CREATE INDEX ix_resultat_question ON resultat_question(id_question)")
    con.execute("""CREATE TABLE session (
        empreinte_jeton TEXT PRIMARY KEY,
        id_utilisateur  INTEGER NOT NULL REFERENCES utilisateur(id_utilisateur) ON DELETE CASCADE,
        doit_changer    INTEGER NOT NULL DEFAULT 0,
        expire_le       TEXT NOT NULL
    )""")
    con.execute("CREATE TABLE echec_connexion (login TEXT NOT NULL COLLATE NOCASE, instant REAL NOT NULL)")
    # Parties d'avant la v2.1 : on reconstruit leurs résultats depuis les choix cochés quand ils existent
    # encore (une partie sans aucune réponse enregistrée, ou dont le quizz a été modifié, n'en a plus).
    bonnes, cochees = {}, {}
    for r in con.execute("SELECT id_question, id_choix FROM choix WHERE est_correct = 1"):
        bonnes.setdefault(r[0], set()).add(r[1])
    for r in con.execute("SELECT r.id_tentative, c.id_question, r.id_choix FROM reponse r JOIN choix c USING (id_choix)"):
        cochees.setdefault(r[0], {}).setdefault(r[1], set()).add(r[2])
    for id_t, id_quizz in con.execute("SELECT id_tentative, id_quizz FROM tentative").fetchall():
        if id_t not in cochees:
            continue
        con.executemany("INSERT INTO resultat_question VALUES (?, ?, ?)",
                        [(id_t, q, int(cochees[id_t].get(q, set()) == bonnes.get(q, set())))
                         for (q,) in con.execute("SELECT id_question FROM question WHERE id_quizz = ?", (id_quizz,))])



def _m7_partie_en_cours(con: sqlite3.Connection) -> None:
    """v2.2, W2 : la partie en cours est gardée en base pour survivre à un redémarrage du serveur."""
    con.execute("""CREATE TABLE partie_en_cours (
        partie         TEXT PRIMARY KEY,
        id_utilisateur INTEGER NOT NULL UNIQUE REFERENCES utilisateur(id_utilisateur) ON DELETE CASCADE,
        id_quizz       INTEGER NOT NULL REFERENCES quizz(id_quizz) ON DELETE CASCADE,
        debut          REAL NOT NULL,
        test           INTEGER NOT NULL DEFAULT 0,
        ordre          TEXT NOT NULL,
        reponses       TEXT NOT NULL DEFAULT '{}'
    )""")



def _m8_compte_supprime(con: sqlite3.Connection) -> None:
    """v2.2, W3 : un compte qui a joué est anonymisé au lieu d'être effacé (ses parties restent comptées)."""
    con.execute("ALTER TABLE utilisateur ADD COLUMN supprime INTEGER NOT NULL DEFAULT 0")



def _m9_conversation_assistant(con: sqlite3.Connection) -> None:
    """v2.2 : le fil de l'assistant est rangé par compte (privé) et survit aux redémarrages."""
    con.execute("""CREATE TABLE conversation_assistant (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        id_utilisateur INTEGER NOT NULL REFERENCES utilisateur(id_utilisateur) ON DELETE CASCADE,
        date           TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        question       TEXT NOT NULL,
        reponse        TEXT NOT NULL,
        sources        TEXT NOT NULL DEFAULT '[]',
        mode           TEXT NOT NULL DEFAULT ''
    )""")
    con.execute("CREATE INDEX ix_conversation_utilisateur ON conversation_assistant(id_utilisateur, id)")


MIGRATIONS = [
    _m1_colonne_source,
    _m2_index,
    _m3_theme,
    _m4_validation_et_journal,
    _m5_archive,
    _m6_v21,
    _m7_partie_en_cours,
    _m8_compte_supprime,
    _m9_conversation_assistant,
]
