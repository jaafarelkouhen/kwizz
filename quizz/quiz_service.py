"""Logique métier des quizz : création, lecture, correction, historique (US03 à US13).

Ce module ne fait aucun print() / input() : l'interface (console ou graphique) l'appelle.
"""
import copy
import random
import sqlite3

from .models import Choix, Question, Quizz, Tentative


class ErreurQuizz(Exception):
    """Quizz invalide ou introuvable."""


# ---------------------------------------------------------------- validation
def valider(quizz: Quizz) -> None:
    if not quizz.titre.strip():
        raise ErreurQuizz("Le quizz doit avoir un titre.")
    if not quizz.questions:
        raise ErreurQuizz("Le quizz doit contenir au moins une question.")
    for i, q in enumerate(quizz.questions, 1):
        if len(q.choix) < 2:
            raise ErreurQuizz(f"Question {i} : il faut au moins 2 choix.")
        if not q.bonnes_reponses():
            raise ErreurQuizz(f"Question {i} : aucune bonne réponse indiquée.")


# ---------------------------------------------------------------- création (US03)
def enregistrer_quizz(con: sqlite3.Connection, quizz: Quizz) -> int:
    """Valide puis enregistre un quizz complet. Renvoie son identifiant."""
    valider(quizz)
    with con:  # transaction : tout ou rien
        cur = con.execute(
            "INSERT INTO quizz (titre, description, duree_limite, id_createur) VALUES (?, ?, ?, ?)",
            (quizz.titre.strip(), quizz.description, quizz.duree_limite, quizz.id_createur),
        )
        quizz.id_quizz = cur.lastrowid
        _inserer_questions(con, quizz)
    return quizz.id_quizz


def _inserer_questions(con: sqlite3.Connection, quizz: Quizz) -> None:
    """Insère les questions et leurs choix (à appeler à l'intérieur d'une transaction)."""
    for ordre, q in enumerate(quizz.questions):
        cur = con.execute(
            "INSERT INTO question (enonce, ordre, id_quizz) VALUES (?, ?, ?)",
            (q.enonce, ordre, quizz.id_quizz),
        )
        q.id_question, q.ordre = cur.lastrowid, ordre
        for c in q.choix:
            cur = con.execute(
                "INSERT INTO choix (texte, est_correct, id_question) VALUES (?, ?, ?)",
                (c.texte, int(c.est_correct), q.id_question),
            )
            c.id_choix = cur.lastrowid


# ---------------------------------------------------------------- lecture (US04)
def lister_quizz(con: sqlite3.Connection) -> list[Quizz]:
    rows = con.execute("SELECT * FROM quizz ORDER BY titre").fetchall()
    return [Quizz(r["titre"], r["description"] or "", r["duree_limite"], [], r["id_quizz"], r["id_createur"])
            for r in rows]


def charger_quizz(con: sqlite3.Connection, id_quizz: int) -> Quizz:
    r = con.execute("SELECT * FROM quizz WHERE id_quizz = ?", (id_quizz,)).fetchone()
    if r is None:
        raise ErreurQuizz(f"Quizz {id_quizz} introuvable.")
    quizz = Quizz(r["titre"], r["description"] or "", r["duree_limite"], [], r["id_quizz"], r["id_createur"])
    for rq in con.execute("SELECT * FROM question WHERE id_quizz = ? ORDER BY ordre", (id_quizz,)):
        choix = [Choix(rc["texte"], bool(rc["est_correct"]), rc["id_choix"])
                 for rc in con.execute("SELECT * FROM choix WHERE id_question = ? ORDER BY id_choix",
                                       (rq["id_question"],))]
        quizz.questions.append(Question(rq["enonce"], choix, rq["ordre"], rq["id_question"]))
    return quizz


# ---------------------------------------------------------------- correction (US05)
def est_juste(question: Question, ids_choisis: set[int]) -> bool:
    """Juste si l'ensemble des choix cochés = exactement l'ensemble des bonnes réponses."""
    return ids_choisis == {c.id_choix for c in question.bonnes_reponses()}


def corriger(quizz: Quizz, reponses: dict[int, set[int]]) -> int:
    """reponses : {id_question: {id_choix cochés}}. Renvoie le nombre de bonnes réponses."""
    return sum(est_juste(q, reponses.get(q.id_question, set())) for q in quizz.questions)


def enregistrer_tentative(con: sqlite3.Connection, id_utilisateur: int, quizz: Quizz,
                          reponses: dict[int, set[int]], duree_secondes: int | None = None) -> Tentative:
    score = corriger(quizz, reponses)
    with con:
        cur = con.execute(
            "INSERT INTO tentative (score, nb_questions, duree_secondes, id_utilisateur, id_quizz) "
            "VALUES (?, ?, ?, ?, ?)",
            (score, len(quizz.questions), duree_secondes, id_utilisateur, quizz.id_quizz),
        )
        id_tentative = cur.lastrowid
        con.executemany(
            "INSERT INTO reponse (id_tentative, id_choix) VALUES (?, ?)",
            [(id_tentative, ic) for ids in reponses.values() for ic in ids],
        )
    return Tentative(id_utilisateur, quizz.id_quizz, score, len(quizz.questions), duree_secondes,
                     id_tentative=id_tentative, titre_quizz=quizz.titre)


# ---------------------------------------------------------------- historique (US07)
def historique(con: sqlite3.Connection, id_utilisateur: int) -> list[Tentative]:
    rows = con.execute(
        "SELECT t.*, q.titre FROM tentative t JOIN quizz q USING (id_quizz) "
        "WHERE t.id_utilisateur = ? ORDER BY t.date_passage DESC, t.id_tentative DESC",
        (id_utilisateur,),
    ).fetchall()
    return [Tentative(r["id_utilisateur"], r["id_quizz"], r["score"], r["nb_questions"], r["duree_secondes"],
                      r["date_passage"], r["id_tentative"], r["titre"]) for r in rows]


# ---------------------------------------------------------------- gestion admin (US08)
def supprimer_quizz(con: sqlite3.Connection, id_quizz: int) -> None:
    with con:
        con.execute("DELETE FROM quizz WHERE id_quizz = ?", (id_quizz,))


def modifier_quizz(con: sqlite3.Connection, quizz: Quizz) -> None:
    """Remplace titre, description, durée et questions d'un quizz existant (US08).

    Les tentatives passées gardent leur score, mais le détail des choix cochés est perdu,
    car les anciennes questions et leurs choix sont supprimés puis recréés.
    """
    if quizz.id_quizz is None:
        raise ErreurQuizz("Ce quizz n'est pas encore enregistré : utiliser enregistrer_quizz.")
    valider(quizz)
    with con:  # transaction : si une étape échoue, le quizz reste tel qu'avant
        cur = con.execute(
            "UPDATE quizz SET titre = ?, description = ?, duree_limite = ? WHERE id_quizz = ?",
            (quizz.titre.strip(), quizz.description, quizz.duree_limite, quizz.id_quizz),
        )
        if cur.rowcount == 0:
            raise ErreurQuizz(f"Quizz {quizz.id_quizz} introuvable.")
        con.execute("DELETE FROM question WHERE id_quizz = ?", (quizz.id_quizz,))
        _inserer_questions(con, quizz)


# ---------------------------------------------------------------- minuterie (US09)
def temps_restant(quizz: Quizz, secondes_ecoulees: float) -> float | None:
    """Secondes restantes (jamais négatif), ou None si le quizz n'a pas de minuterie."""
    if not quizz.duree_limite:
        return None
    return max(0.0, quizz.duree_limite - secondes_ecoulees)


def temps_ecoule(quizz: Quizz, secondes_ecoulees: float) -> bool:
    restant = temps_restant(quizz, secondes_ecoulees)
    return restant is not None and restant <= 0


# ---------------------------------------------------------------- ordre aléatoire (US13)
def melanger(quizz: Quizz, generateur: random.Random | None = None) -> Quizz:
    """Copie du quizz avec questions et choix dans un ordre aléatoire.

    La correction se fait par identifiants, donc l'ordre d'affichage ne change pas le score.
    `generateur` permet aux tests d'obtenir toujours le même ordre (random.Random(graine)).
    """
    generateur = generateur or random.Random()
    copie = copy.deepcopy(quizz)
    generateur.shuffle(copie.questions)
    for q in copie.questions:
        generateur.shuffle(q.choix)
    return copie


# ---------------------------------------------------------------- bonus (US12)
def classement(con: sqlite3.Connection, id_quizz: int, limite: int = 10) -> list[tuple[str, int]]:
    """Meilleur score de chaque joueur sur ce quizz, du meilleur au moins bon.

    À score égal, le joueur qui l'a obtenu en premier est devant.
    """
    rows = con.execute(
        "SELECT u.login, MAX(t.score) AS meilleur, MIN(t.date_passage) AS premiere_fois "
        "FROM tentative t JOIN utilisateur u USING (id_utilisateur) "
        "WHERE t.id_quizz = ? "
        "GROUP BY u.id_utilisateur "
        "ORDER BY meilleur DESC, premiere_fois, u.login "
        "LIMIT ?",
        (id_quizz, limite),
    ).fetchall()
    return [(r["login"], r["meilleur"]) for r in rows]
