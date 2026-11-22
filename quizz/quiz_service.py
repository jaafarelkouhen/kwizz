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
            "INSERT INTO quizz (titre, description, duree_limite, id_createur, source, theme, statut) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (quizz.titre.strip(), quizz.description, quizz.duree_limite, quizz.id_createur, quizz.source,
             quizz.theme.strip() or "Divers", quizz.statut),
        )
        quizz.id_quizz = cur.lastrowid
        _inserer_questions(con, quizz)
    return quizz.id_quizz


def _inserer_questions(con: sqlite3.Connection, quizz: Quizz) -> None:
    """Insère les questions et leurs choix (à appeler à l'intérieur d'une transaction)."""
    for ordre, q in enumerate(quizz.questions):
        cur = con.execute(
            "INSERT INTO question (enonce, ordre, id_quizz, explication) VALUES (?, ?, ?, ?)",
            (q.enonce, ordre, quizz.id_quizz, q.explication.strip() or None),
        )
        q.id_question, q.ordre = cur.lastrowid, ordre
        for c in q.choix:
            cur = con.execute(
                "INSERT INTO choix (texte, est_correct, id_question) VALUES (?, ?, ?)",
                (c.texte, int(c.est_correct), q.id_question),
            )
            c.id_choix = cur.lastrowid


# ---------------------------------------------------------------- lecture (US04)
def _quizz_depuis_ligne(r: sqlite3.Row) -> Quizz:
    return Quizz(r["titre"], r["description"] or "", r["duree_limite"], [], r["id_quizz"], r["id_createur"],
                 r["source"], r["theme"], r["statut"], r["teste_le"], r["valide_le"], bool(r["archive"]))


def lister_quizz(con: sqlite3.Connection, publies_seulement: bool = False,
                 inclure_archives: bool = False) -> list[Quizz]:
    """`publies_seulement` : la liste des joueurs (les brouillons ne sont visibles que des admins).
    Les quizz archivés (supprimés après avoir été joués) n'apparaissent nulle part, sauf `inclure_archives`."""
    conditions = ([] if inclure_archives else ["archive = 0"]) + (["statut = 'publie'"] if publies_seulement else [])
    rows = con.execute("SELECT * FROM quizz " + (f"WHERE {' AND '.join(conditions)} " if conditions else "")
                       + "ORDER BY titre").fetchall()
    return [_quizz_depuis_ligne(r)
            for r in rows]


def charger_quizz(con: sqlite3.Connection, id_quizz: int) -> Quizz:
    r = con.execute("SELECT * FROM quizz WHERE id_quizz = ?", (id_quizz,)).fetchone()
    if r is None:
        raise ErreurQuizz(f"Quizz {id_quizz} introuvable.")
    quizz = _quizz_depuis_ligne(r)
    rows = con.execute("SELECT * FROM question WHERE id_quizz = ? AND active = 1 ORDER BY ordre", (id_quizz,))
    quizz.questions = [_question_depuis_ligne(con, rq) for rq in rows.fetchall()]
    return quizz


def _question_depuis_ligne(con: sqlite3.Connection, rq: sqlite3.Row) -> Question:
    choix = [Choix(rc["texte"], bool(rc["est_correct"]), rc["id_choix"])
             for rc in con.execute("SELECT * FROM choix WHERE id_question = ? ORDER BY id_choix", (rq["id_question"],))]
    return Question(rq["enonce"], choix, rq["ordre"], rq["id_question"], rq["explication"] or "")


def charger_question(con: sqlite3.Connection, id_question: int) -> tuple[Question, int]:
    """Une question et l'id de son quizz, même désactivée (corrigé d'une ancienne partie)."""
    rq = con.execute("SELECT * FROM question WHERE id_question = ?", (id_question,)).fetchone()
    if rq is None:
        raise ErreurQuizz("Question introuvable.")
    return _question_depuis_ligne(con, rq), rq["id_quizz"]


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
        con.executemany(
            "INSERT INTO resultat_question (id_tentative, id_question, juste) VALUES (?, ?, ?)",
            [(id_tentative, q.id_question, int(est_juste(q, reponses.get(q.id_question, set()))))
             for q in quizz.questions],
        )
    return Tentative(id_utilisateur, quizz.id_quizz, score, len(quizz.questions), duree_secondes,
                     id_tentative=id_tentative, titre_quizz=quizz.titre)


def detail_correction(questions: list[Question], reponses: dict[int, set[int]]) -> list[dict]:
    """Le corrigé affiché au joueur : pour chaque question, juste ou faux et chaque choix coché ou non."""
    return [{"id": q.id_question, "enonce": q.enonce, "explication": q.explication,
             "juste": est_juste(q, reponses.get(q.id_question, set())),
             "choix": [{"id": c.id_choix, "texte": c.texte, "correct": c.est_correct,
                        "coche": c.id_choix in reponses.get(q.id_question, set())} for c in q.choix]}
            for q in questions]


def corrige_tentative(con: sqlite3.Connection, id_tentative: int) -> dict | None:
    """Corrigé d'une partie passée, avec les questions telles qu'elles étaient (même modifiées depuis).

    None si la partie n'a pas de résultats enregistrés (partie d'avant la v2.1 sans réponse cochée).
    """
    t = con.execute("SELECT t.*, q.titre, q.archive FROM tentative t JOIN quizz q USING (id_quizz) "
                    "WHERE id_tentative = ?",
                    (id_tentative,)).fetchone()
    lignes = con.execute("SELECT q.* FROM resultat_question r JOIN question q USING (id_question) "
                         "WHERE r.id_tentative = ? ORDER BY q.ordre, q.id_question", (id_tentative,)).fetchall()
    if t is None or not lignes:
        return None
    reponses: dict[int, set[int]] = {}
    for r in con.execute("SELECT c.id_question, r.id_choix FROM reponse r JOIN choix c USING (id_choix) "
                         "WHERE r.id_tentative = ?", (id_tentative,)):
        reponses.setdefault(r[0], set()).add(r[1])
    return {"id_utilisateur": t["id_utilisateur"], "id_quizz": t["id_quizz"], "titre": t["titre"],
            "score": t["score"], "total": t["nb_questions"], "duree": t["duree_secondes"], "date": t["date_passage"],
            "archive": bool(t["archive"]),
            "detail": detail_correction([_question_depuis_ligne(con, q) for q in lignes], reponses)}


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
def supprimer_quizz(con: sqlite3.Connection, id_quizz: int) -> int:
    """Supprime un quizz jamais joué ; archive un quizz déjà joué pour garder l'historique des joueurs.

    Renvoie le nombre de parties gardées (0 = vraiment supprimé).
    """
    parties = con.execute("SELECT COUNT(*) FROM tentative WHERE id_quizz = ?", (id_quizz,)).fetchone()[0]
    with con:
        if parties:
            con.execute("UPDATE quizz SET archive = 1, statut = 'brouillon', valide_le = NULL WHERE id_quizz = ?",
                        (id_quizz,))
        else:
            con.execute("DELETE FROM quizz WHERE id_quizz = ?", (id_quizz,))
    return parties


def modifier_quizz(con: sqlite3.Connection, quizz: Quizz, repasser_en_brouillon: bool = False) -> None:
    """Remplace titre, description, durée et questions d'un quizz existant (US08).

    Si le quizz a déjà été joué, ses anciennes questions sont désactivées (pas effacées) : le corrigé
    des parties passées reste lisible. Sinon, elles sont effacées.
    `repasser_en_brouillon` : la version web exige un nouveau test et une nouvelle validation après une
    modification ; l'application de bureau, qui n'a pas ce cycle, garde le quizz publié.
    """
    if quizz.id_quizz is None:
        raise ErreurQuizz("Ce quizz n'est pas encore enregistré : utiliser enregistrer_quizz.")
    valider(quizz)
    with con:  # transaction : si une étape échoue, le quizz reste tel qu'avant
        cur = con.execute(
            "UPDATE quizz SET titre = ?, description = ?, duree_limite = ?, theme = ?"
            + (", statut = 'brouillon', teste_le = NULL, valide_le = NULL" if repasser_en_brouillon else "")
            + " WHERE id_quizz = ?",
            (quizz.titre.strip(), quizz.description, quizz.duree_limite, quizz.theme.strip() or "Divers",
             quizz.id_quizz),
        )
        if cur.rowcount == 0:
            raise ErreurQuizz(f"Quizz {quizz.id_quizz} introuvable.")
        if con.execute("SELECT 1 FROM tentative WHERE id_quizz = ?", (quizz.id_quizz,)).fetchone():
            con.execute("UPDATE question SET active = 0 WHERE id_quizz = ?", (quizz.id_quizz,))
        else:
            con.execute("DELETE FROM question WHERE id_quizz = ?", (quizz.id_quizz,))
        _inserer_questions(con, quizz)


def restaurer_quizz(con: sqlite3.Connection, id_quizz: int) -> None:
    """Sort un quizz de l'archive (US21). Il revient en brouillon : l'admin le revalide pour le republier."""
    with con:
        cur = con.execute("UPDATE quizz SET archive = 0 WHERE id_quizz = ? AND archive = 1", (id_quizz,))
    if cur.rowcount == 0:
        raise ErreurQuizz("Ce quizz n'est pas archivé.")


def stats_questions(con: sqlite3.Connection, id_quizz: int | None = None) -> list[dict]:
    """Chaque question actuelle déjà jouée, de la moins réussie à la mieux réussie (US27)."""
    filtre, params = ("AND q.id_quizz = ? ", (id_quizz,)) if id_quizz else ("", ())
    rows = con.execute(
        "SELECT q.id_question, q.enonce, q.id_quizz, z.titre, COUNT(*) AS n, SUM(r.juste) AS justes "
        "FROM resultat_question r JOIN question q USING (id_question) JOIN quizz z ON z.id_quizz = q.id_quizz "
        "WHERE q.active = 1 AND z.archive = 0 " + filtre +
        "GROUP BY q.id_question ORDER BY 1.0 * justes / n, n DESC, q.id_question", params).fetchall()
    return [{"id": r["id_question"], "enonce": r["enonce"], "id_quizz": r["id_quizz"], "titre": r["titre"],
             "reponses": r["n"], "reussite": round(100 * r["justes"] / r["n"])} for r in rows]


def questions_a_revoir(con: sqlite3.Connection, id_utilisateur: int, limite: int = 10) -> list[Question]:
    """Révision ciblée (v2.2, W4) : les questions que le joueur a ratées la DERNIÈRE fois qu'il y a répondu
    dans une vraie partie, tous quizz confondus, les plus récentes d'abord. Seulement des questions
    actuelles de quizz publiés (rien d'archivé, de modifié depuis, ni de brouillon)."""
    rows = con.execute(
        "SELECT id_question FROM ("
        "  SELECT r.id_question, r.juste, t.id_tentative, ROW_NUMBER() OVER ("
        "    PARTITION BY r.id_question ORDER BY t.id_tentative DESC) AS rang "
        "  FROM resultat_question r JOIN tentative t USING (id_tentative) "
        "  JOIN question q USING (id_question) JOIN quizz z ON z.id_quizz = q.id_quizz "
        "  WHERE t.id_utilisateur = ? AND q.active = 1 AND z.archive = 0 AND z.statut = 'publie'"
        ") WHERE rang = 1 AND juste = 0 ORDER BY id_tentative DESC, id_question LIMIT ?",
        (id_utilisateur, limite)).fetchall()
    return [charger_question(con, r["id_question"])[0] for r in rows]


def deja_jouees(con: sqlite3.Connection, id_utilisateur: int, ids_questions: set[int]) -> set[int]:
    """Parmi ces questions, celles que le joueur a déjà vues corrigées dans une vraie partie."""
    if not ids_questions:
        return set()
    marques = ",".join("?" * len(ids_questions))
    return {r[0] for r in con.execute(
        f"SELECT DISTINCT r.id_question FROM resultat_question r JOIN tentative t USING (id_tentative) "
        f"WHERE t.id_utilisateur = ? AND r.id_question IN ({marques})", (id_utilisateur, *ids_questions))}


# ---------------------------------------------------------------- validation par l'admin (V2)
def noter_test(con: sqlite3.Connection, id_quizz: int) -> None:
    with con:
        con.execute("UPDATE quizz SET teste_le = CURRENT_TIMESTAMP WHERE id_quizz = ?", (id_quizz,))


def valider_publication(con: sqlite3.Connection, id_quizz: int) -> None:
    """Publie un brouillon. Il doit avoir été testé depuis sa dernière modification."""
    quizz = charger_quizz(con, id_quizz)
    valider(quizz)
    if not quizz.teste_le:
        raise ErreurQuizz("Teste d'abord ce quizz (bouton « Tester ») avant de le valider.")
    with con:
        con.execute("UPDATE quizz SET statut = 'publie', valide_le = CURRENT_TIMESTAMP WHERE id_quizz = ?",
                    (id_quizz,))


def depublier(con: sqlite3.Connection, id_quizz: int) -> None:
    charger_quizz(con, id_quizz)
    with con:
        con.execute("UPDATE quizz SET statut = 'brouillon', valide_le = NULL WHERE id_quizz = ?", (id_quizz,))


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
    # « En premier » = la première tentative qui atteint ce meilleur score, pas la première partie jouée.
    rows = con.execute(
        "SELECT u.login, b.meilleur, MIN(t.id_tentative) AS atteint "
        "FROM (SELECT id_utilisateur, MAX(score) AS meilleur FROM tentative WHERE id_quizz = ? "
        "      GROUP BY id_utilisateur) b "
        "JOIN tentative t ON t.id_utilisateur = b.id_utilisateur AND t.id_quizz = ? AND t.score = b.meilleur "
        "JOIN utilisateur u ON u.id_utilisateur = b.id_utilisateur AND u.supprime = 0 "
        "GROUP BY b.id_utilisateur "
        "ORDER BY b.meilleur DESC, atteint, u.login "
        "LIMIT ?",
        (id_quizz, id_quizz, limite),
    ).fetchall()
    return [(r["login"], r["meilleur"]) for r in rows]
