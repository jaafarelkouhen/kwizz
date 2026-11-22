"""MyKwizz : la version web de Kwizz.

    python serveur.py              lance le serveur et ouvre le navigateur sur http://127.0.0.1:8000
    python serveur.py --port 8080  autre port
    python serveur.py --demo       ajoute des joueurs de démo (alice, bob, chloe / demo) et quelques parties

Toute la logique reste en Python, dans le paquet quizz/ (le même que Kwizz) : ce fichier ne fait que
traduire des requêtes HTTP en appels à auth, quiz_service, importer et ia, puis renvoyer du JSON.
Le navigateur (dossier web/) n'affiche que ce que le serveur lui donne : il ne connaît jamais les
bonnes réponses avant d'avoir envoyé les siennes.
Aucune dépendance en plus de Kwizz : http.server fait partie de Python.
"""
import argparse
import hashlib
import json
import secrets
import sys
import tempfile
import threading
import time
import webbrowser
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from quizz import auth, importer, journal, parties, quiz_service as qs
from quizz.database import CHEMIN_PAR_DEFAUT, connexion
from quizz.ia import client as ia_client
from quizz.ia import explications, generateur, recommandation
from quizz.models import Quizz
from quizz.rag import assistant, conversation

RACINE = Path(__file__).resolve().parent
WEB = RACINE / "web"
TYPES = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
         ".js": "text/javascript; charset=utf-8", ".png": "image/png", ".svg": "image/svg+xml",
         ".woff2": "font/woff2", ".ico": "image/x-icon", ".json": "application/json"}
ESSAIS_MAX, BLOCAGE_SECONDES = 3, 30   # US02 : 3 essais, puis une courte pause
TAILLE_MAX_CORPS = 2_000_000           # 2 Mo : largement assez pour un quizz importé

CHEMIN_BASE = CHEMIN_PAR_DEFAUT
DUREE_SESSION = 7 * 24 * 3600          # secondes : un joueur reste connecté une semaine
# Rien de propre à un joueur ne reste en mémoire : sessions, échecs de connexion, partie en cours et fil
# de l'assistant sont en base. Un redémarrage du serveur ne perd rien et ne mélange rien entre comptes.


def empreinte(jeton: str) -> str:
    """On ne stocke que l'empreinte du jeton : une fuite de la base ne permet pas d'ouvrir les sessions."""
    return hashlib.sha256(jeton.encode()).hexdigest()


class ErreurHTTP(Exception):
    def __init__(self, statut: int, message: str):
        super().__init__(message)
        self.statut, self.message = statut, message


# ---------------------------------------------------------------- conversions objets → JSON
def quizz_resume(con, q: Quizz, id_utilisateur: int | None) -> dict:
    nb = con.execute("SELECT COUNT(*) FROM question WHERE id_quizz = ? AND active = 1", (q.id_quizz,)).fetchone()[0]
    meilleur = None
    if id_utilisateur is not None:
        r = con.execute("SELECT MAX(score) AS s, COUNT(*) AS n FROM tentative WHERE id_quizz = ? AND id_utilisateur = ?",
                        (q.id_quizz, id_utilisateur)).fetchone()
        if r["n"]:
            meilleur = r["s"]
    return {"id": q.id_quizz, "titre": q.titre, "description": q.description, "duree": q.duree_limite,
            "source": q.source, "theme": q.theme, "nb_questions": nb, "mon_meilleur": meilleur,
            "statut": q.statut, "teste_le": q.teste_le, "valide_le": q.valide_le, "archive": q.archive}


def quizz_pour_joueur(q: Quizz) -> dict:
    """Sans les bonnes réponses : le navigateur ne doit pas pouvoir tricher."""
    return {"id": q.id_quizz, "titre": q.titre, "description": q.description, "duree": q.duree_limite,
            "theme": q.theme,
            "questions": [{"id": x.id_question, "enonce": x.enonce, "multiple": len(x.bonnes_reponses()) > 1,
                           "choix": [{"id": c.id_choix, "texte": c.texte} for c in x.choix]}
                          for x in q.questions]}


def quizz_complet(q: Quizz) -> dict:
    """Pour l'éditeur admin (et l'aperçu d'un import ou d'une génération IA)."""
    return {"id": q.id_quizz, "titre": q.titre, "description": q.description, "duree": q.duree_limite,
            "source": q.source, "theme": q.theme,
            "questions": [{"enonce": x.enonce, "explication": x.explication,
                           "choix": [{"texte": c.texte, "correct": c.est_correct} for c in x.choix]}
                          for x in q.questions]}


def quizz_depuis_editeur(d: dict) -> Quizz:
    duree = d.get("duree")
    if duree in ("", 0, "0"):
        duree = None
    if duree is not None:
        try:
            duree = int(duree)
        except (TypeError, ValueError):
            raise ErreurHTTP(400, "La durée doit être un nombre de secondes.")
        if duree <= 0:
            raise ErreurHTTP(400, "La durée doit être positive (ou vide pour aucune minuterie).")
    try:
        q = importer.quizz_depuis_dict({"format": importer.FORMAT_JSON, "version": importer.VERSION_JSON,
                                        "titre": d.get("titre", ""), "description": d.get("description", ""),
                                        "duree_limite": duree, "theme": str(d.get("theme") or "Divers")[:40],
                                        "questions": d.get("questions", [])})
    except importer.ErreurFormat as e:
        raise ErreurHTTP(400, str(e))
    for i, question in enumerate(q.questions, 1):
        if not question.enonce:
            raise ErreurHTTP(400, f"Question {i} : l'énoncé est vide.")
        if any(not c.texte for c in question.choix):
            raise ErreurHTTP(400, f"Question {i} : un choix est vide.")
    source = d.get("source")
    q.source = source if source in ("manuel", "fichier", "ia") else "manuel"
    try:
        qs.valider(q)
    except qs.ErreurQuizz as e:
        raise ErreurHTTP(400, str(e))
    return q


# ---------------------------------------------------------------- serveur
class Gestionnaire(BaseHTTPRequestHandler):
    server_version = "MyKwizz/1.0"

    # -- utilitaires
    def log_message(self, fmt, *args):  # journal plus discret que celui par défaut
        if not self.path.startswith("/api/"):
            return
        sys.stderr.write(f"  {self.command} {self.path.split('?')[0]} {args[1] if len(args) > 1 else ''}\n")

    def _session(self, con) -> tuple[str | None, dict | None]:
        """Login, rôle et changement de mot de passe sont relus en base à chaque requête : un compte
        renommé, rétrogradé ou supprimé par l'admin l'est aussitôt dans toutes ses sessions."""
        cookie = SimpleCookie(self.headers.get("Cookie", ""))
        jeton = cookie["kwizz"].value if "kwizz" in cookie else None
        if not jeton:
            return None, None
        e = empreinte(jeton)
        row = con.execute("SELECT s.doit_changer, u.id_utilisateur, u.login, u.est_admin FROM session s "
                          "JOIN utilisateur u USING (id_utilisateur) "
                          "WHERE s.empreinte_jeton = ? AND s.expire_le > datetime('now')", (e,)).fetchone()
        if row is None:
            return jeton, None
        return jeton, {"empreinte": e, "id": row["id_utilisateur"], "login": row["login"],
                       "admin": bool(row["est_admin"]), "doit_changer": bool(row["doit_changer"])}

    def _envoyer(self, statut: int, corps: bytes, type_: str, entetes: dict | None = None):
        self.send_response(statut)
        self.send_header("Content-Type", type_)
        self.send_header("Content-Length", str(len(corps)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "same-origin")
        for k, v in (entetes or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(corps)

    def _json(self, donnees, statut: int = 200, entetes: dict | None = None):
        self._envoyer(statut, json.dumps(donnees, ensure_ascii=False).encode(), "application/json; charset=utf-8",
                      entetes)

    def _corps(self) -> dict:
        taille = int(self.headers.get("Content-Length") or 0)
        if taille > TAILLE_MAX_CORPS:
            raise ErreurHTTP(413, "Fichier trop volumineux (2 Mo maximum).")
        if not taille:
            return {}
        try:
            return json.loads(self.rfile.read(taille).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise ErreurHTTP(400, "Requête illisible.")

    # -- verbes HTTP
    def do_GET(self):
        self._traiter("GET")

    def do_POST(self):
        self._traiter("POST")

    def do_PUT(self):
        self._traiter("PUT")

    def do_DELETE(self):
        self._traiter("DELETE")

    def _traiter(self, verbe: str):
        url = urlparse(self.path)
        if not url.path.startswith("/api/"):
            if verbe != "GET":
                return self._json({"erreur": "Méthode non autorisée."}, 405)
            return self._fichier(url.path)
        con = connexion(CHEMIN_BASE)
        try:
            self._api(verbe, url.path[5:].strip("/").split("/"), parse_qs(url.query), con)
        except ErreurHTTP as e:
            self._json({"erreur": e.message}, e.statut)
        except (auth.ErreurAuth, qs.ErreurQuizz, importer.ErreurFormat, ia_client.ErreurIA) as e:
            self._json({"erreur": str(e)}, 400)
        except Exception as e:  # ne jamais laisser le navigateur sans réponse
            sys.stderr.write(f"  ERREUR {e!r}\n")
            self._json({"erreur": "Erreur interne du serveur."}, 500)
        finally:
            con.close()

    def _fichier(self, chemin: str):
        if chemin in ("", "/"):
            chemin = "/index.html"
        cible = (WEB / chemin.lstrip("/")).resolve()
        if WEB.resolve() not in cible.parents or not cible.is_file():
            cible = WEB / "index.html"  # application d'une seule page : le JS gère la route
        self._envoyer(200, cible.read_bytes(), TYPES.get(cible.suffix, "application/octet-stream"))

    # -- API
    def _api(self, verbe, morceaux, query, con):
        jeton, s = self._session(con)
        route = "/".join(m for m in morceaux if not m.isdigit())
        ids = [int(m) for m in morceaux if m.isdigit()]

        def exiger_joueur():
            if s is None:
                raise ErreurHTTP(401, "Connecte-toi d'abord.")
            if s.get("doit_changer"):
                raise ErreurHTTP(403, "Choisis d'abord un nouveau mot de passe.")
            return s

        def exiger_admin():
            exiger_joueur()
            if not s["admin"]:
                raise ErreurHTTP(403, "Réservé à l'administrateur.")
            return s

        # ------------------------------------------------ comptes (US01, US02, US15)
        if (verbe, route) == ("GET", "etat"):
            return self._json({"utilisateur": None if s is None else
                               {"login": s["login"], "admin": s["admin"], "doit_changer": s.get("doit_changer", False)},
                               "ia": ia_client.ia_disponible()})

        if (verbe, route) == ("POST", "inscription"):
            d = self._corps()
            if d.get("mdp") != d.get("mdp2"):
                raise ErreurHTTP(400, "Les deux mots de passe ne sont pas identiques.")
            u = auth.inscrire(con, str(d.get("login", "")), str(d.get("mdp", "")))
            journal.noter(con, u.id_utilisateur, u.login, "inscription")
            return self._ouvrir_session(con, u, False)

        if (verbe, route) == ("POST", "connexion"):
            d = self._corps()
            login = str(d.get("login", "")).strip()
            maintenant = time.time()
            with con:
                con.execute("DELETE FROM echec_connexion WHERE instant < ?", (maintenant - BLOCAGE_SECONDES,))
            recents = [r[0] for r in con.execute(
                "SELECT instant FROM echec_connexion WHERE login = ? ORDER BY instant", (login,))]
            if len(recents) >= ESSAIS_MAX:
                attente = int(BLOCAGE_SECONDES - (maintenant - recents[0])) + 1
                raise ErreurHTTP(429, f"Trois essais ratés : réessaie dans {attente} s.")
            try:
                u = auth.connecter(con, login, str(d.get("mdp", "")))
            except auth.ErreurAuth:
                with con:
                    con.execute("INSERT INTO echec_connexion (login, instant) VALUES (?, ?)", (login, maintenant))
                restants = ESSAIS_MAX - len(recents) - 1
                row = con.execute("SELECT id_utilisateur, login FROM utilisateur WHERE login = ? COLLATE NOCASE",
                                  (login,)).fetchone()
                if row:  # seulement pour un compte existant : on ne remplit pas le journal de logins inventés
                    journal.noter(con, row["id_utilisateur"], row["login"], "connexion_echouee",
                                  f"adresse {self.client_address[0]}")
                msg = "Login ou mot de passe incorrect."
                msg += f" Encore {restants} essai{'s' if restants > 1 else ''}." if restants > 0 else \
                    f" Réessaie dans {BLOCAGE_SECONDES} s."
                raise ErreurHTTP(401, msg)
            with con:
                con.execute("DELETE FROM echec_connexion WHERE login = ?", (login,))
            journal.noter(con, u.id_utilisateur, u.login, "connexion")
            return self._ouvrir_session(con, u, auth.utilise_mot_de_passe_par_defaut(con, u))

        if (verbe, route) == ("POST", "deconnexion"):
            if s is not None:
                journal.noter(con, s["id"], s["login"], "deconnexion")
            if jeton:
                with con:
                    con.execute("DELETE FROM session WHERE empreinte_jeton = ?", (empreinte(jeton),))
            return self._json({"ok": True}, entetes={"Set-Cookie": "kwizz=; Path=/; Max-Age=0; HttpOnly; SameSite=Strict"})

        if (verbe, route) == ("POST", "mot-de-passe"):
            if s is None:
                raise ErreurHTTP(401, "Connecte-toi d'abord.")
            d = self._corps()
            if d.get("nouveau") != d.get("confirmation"):
                raise ErreurHTTP(400, "Les deux mots de passe ne sont pas identiques.")
            auth.changer_mot_de_passe(con, s["id"], str(d.get("nouveau", "")),
                                      None if s.get("doit_changer") else str(d.get("ancien", "")))
            with con:
                con.execute("UPDATE session SET doit_changer = 0 WHERE id_utilisateur = ?", (s["id"],))
            journal.noter(con, s["id"], s["login"], "mot_de_passe")
            return self._json({"ok": True})

        # ------------------------------------------------ joueur (US04, US05, US07, US09, US12, US13, US17, US18)
        if (verbe, route) == ("GET", "quizz"):
            exiger_joueur()
            archives = s["admin"] and query.get("archives") == ["1"]  # la liste admin montre aussi l'archive
            return self._json([quizz_resume(con, q, s["id"])
                               for q in qs.lister_quizz(con, not s["admin"], inclure_archives=archives)])

        if (verbe, route) == ("GET", "quizz/jouer"):
            exiger_joueur()
            quizz = charger_visible(con, ids[0], s)
            test = query.get("test") == ["1"]
            if test and not s["admin"]:
                raise ErreurHTTP(403, "Réservé à l'administrateur.")
            if query.get("aleatoire") == ["1"]:
                quizz = qs.melanger(quizz)
            partie = parties.commencer(con, s["id"], quizz, test)
            return self._json({"partie": partie, "test": test, **quizz_pour_joueur(quizz)})

        if (verbe, route) == ("POST", "quizz/sauver"):
            exiger_joueur()
            d = self._corps()
            try:
                reponses = {int(q): {int(c) for c in choisis} for q, choisis in (d.get("reponses") or {}).items()}
            except (TypeError, ValueError, AttributeError):
                raise ErreurHTTP(400, "Réponses mal formées.")
            if not parties.sauver_reponses(con, s["id"], str(d.get("partie")), reponses):
                raise ErreurHTTP(409, "Cette partie n'existe plus : relance le quizz.")
            return self._json({"ok": True})

        # ------------------------------------------------ révision ciblée (v2.2, W4)
        if (verbe, route) == ("GET", "revision"):
            exiger_joueur()
            serie = Quizz("Réviser mes erreurs", "Les questions que tu as ratées la dernière fois.",
                          questions=qs.questions_a_revoir(con, s["id"]))
            return self._json({**quizz_pour_joueur(serie), "revision": True, "partie": None})

        if (verbe, route) == ("POST", "revision/corriger"):
            exiger_joueur()
            d = self._corps()
            try:
                ids = list(dict.fromkeys(int(i) for i in d.get("questions") or []))[:50]
                reponses = {int(q): {int(c) for c in choisis} for q, choisis in (d.get("reponses") or {}).items()}
            except (TypeError, ValueError, AttributeError):
                raise ErreurHTTP(400, "Réponses mal formées.")
            # seulement des questions déjà corrigées pour ce joueur : sinon on lui donnerait les bonnes réponses
            if not ids or set(ids) - qs.deja_jouees(con, s["id"], set(ids)):
                raise ErreurHTTP(403, "On ne révise que des questions déjà jouées.")
            questions = [qs.charger_question(con, i)[0] for i in ids]
            reponses = {q: c for q, c in reponses.items() if q in set(ids)}
            score = sum(qs.est_juste(q, reponses.get(q.id_question, set())) for q in questions)
            journal.noter(con, s["id"], s["login"], "revision", f"{score}/{len(questions)}")
            return self._json({"revision": True, "titre": "Réviser mes erreurs", "id_quizz": None, "score": score,
                               "total": len(questions), "duree": None, "detail": qs.detail_correction(questions, reponses)})

        if (verbe, route) == ("GET", "partie/en-cours"):
            exiger_joueur()
            p = parties.en_cours(con, s["id"])
            if p is None:
                return self._json(None)
            try:
                quizz = parties.remettre_dans_l_ordre(charger_visible(con, p["id_quizz"], s), p["ordre"])
            except (ErreurHTTP, qs.ErreurQuizz, KeyError):  # quizz retiré, archivé ou modifié depuis
                parties.terminer(con, s["id"], p["partie"])
                return self._json(None)
            restant = None if not quizz.duree_limite else max(0, round(quizz.duree_limite - (time.time() - p["debut"])))
            return self._json({"partie": p["partie"], "test": p["test"], "restant": restant,
                               "reponses": {q: sorted(c) for q, c in p["reponses"].items()},
                               **quizz_pour_joueur(quizz)})

        if (verbe, route) == ("POST", "quizz/corriger"):
            exiger_joueur()
            d = self._corps()
            partie = parties.terminer(con, s["id"], str(d.get("partie")))
            if partie is None or partie["id_quizz"] != ids[0]:
                raise ErreurHTTP(409, "Cette partie n'existe plus : relance le quizz.")
            quizz = qs.charger_quizz(con, ids[0])
            ecoule = time.time() - partie["debut"]
            depasse = qs.temps_ecoule(quizz, ecoule - 2)  # 2 s de tolérance pour le réseau
            valides = {q.id_question: {c.id_choix for c in q.choix} for q in quizz.questions}
            reponses: dict[int, set[int]] = {}
            for cle, choisis in (d.get("reponses") or {}).items():
                try:
                    id_q = int(cle)
                    ensemble = {int(c) for c in choisis} & valides.get(id_q, set())
                except (TypeError, ValueError):
                    raise ErreurHTTP(400, "Réponses mal formées.")
                if ensemble:
                    reponses[id_q] = ensemble
            duree = round(min(ecoule, quizz.duree_limite) if quizz.duree_limite else ecoule)
            if partie.get("test"):  # test de l'admin : corrigé complet, mais rien dans les scores
                score = qs.corriger(quizz, reponses)
                qs.noter_test(con, quizz.id_quizz)
                journal.noter(con, s["id"], s["login"], "partie_test", f"{quizz.titre} : {score}/{len(quizz.questions)}")
            else:
                score = qs.enregistrer_tentative(con, s["id"], quizz, reponses, duree).score
                journal.noter(con, s["id"], s["login"], "partie",
                              f"{quizz.titre} : {score}/{len(quizz.questions)} en {duree} s")
            detail = qs.detail_correction(quizz.questions, reponses)
            rang, meilleur = (None, None) if partie.get("test") else next(
                ((i, sc) for i, (login, sc) in enumerate(qs.classement(con, quizz.id_quizz, 1000), 1)
                 if login == s["login"]), (None, None))
            return self._json({"score": score, "total": len(quizz.questions), "duree": duree, "temps_ecoule": depasse,
                               "titre": quizz.titre, "id_quizz": quizz.id_quizz, "rang": rang, "meilleur": meilleur,
                               "detail": detail, "test": bool(partie.get("test")), "statut": quizz.statut})

        if (verbe, route) == ("POST", "expliquer"):
            exiger_joueur()
            try:
                id_question = int(self._corps().get("id_question", 0))
            except (TypeError, ValueError):
                raise ErreurHTTP(400, "Question invalide.")
            # seulement une question d'une partie que ce joueur a terminée (V4) : sinon l'explication souffle la réponse
            if con.execute("SELECT 1 FROM resultat_question r JOIN tentative t USING (id_tentative) "
                           "WHERE r.id_question = ? AND t.id_utilisateur = ?", (id_question, s["id"])).fetchone() is None:
                raise ErreurHTTP(403, "Joue d'abord ce quizz pour voir l'explication.")
            question, _ = qs.charger_question(con, id_question)
            deja_gardee = bool(question.explication)
            texte = explications.expliquer(con, question)
            journal.noter(con, s["id"], s["login"], "explication", question.enonce[:120])
            return self._json({"texte": texte, "gardee": deja_gardee})

        if (verbe, route) == ("GET", "historique"):
            exiger_joueur()
            archives = {r[0] for r in con.execute("SELECT id_quizz FROM quizz WHERE archive = 1")}
            avec_corrige = {r[0] for r in con.execute(
                "SELECT DISTINCT r.id_tentative FROM resultat_question r JOIN tentative t USING (id_tentative) "
                "WHERE t.id_utilisateur = ?", (s["id"],))}
            return self._json([{"id": t.id_tentative, "titre": t.titre_quizz, "id_quizz": t.id_quizz, "score": t.score,
                                "total": t.nb_questions, "duree": t.duree_secondes, "date": t.date_passage,
                                "archive": t.id_quizz in archives, "revoir": t.id_tentative in avec_corrige}
                               for t in qs.historique(con, s["id"])])

        if (verbe, route) == ("GET", "partie/corrige"):
            exiger_joueur()
            c = qs.corrige_tentative(con, ids[0])
            # même réponse pour une partie d'un autre joueur que pour une partie inexistante
            if c is None or (c["id_utilisateur"] != s["id"] and not s["admin"]):
                raise ErreurHTTP(404, "Le corrigé de cette partie n'est pas disponible.")
            return self._json(c)

        if (verbe, route) == ("GET", "quizz/classement"):
            exiger_joueur()
            quizz = charger_visible(con, ids[0], s)
            return self._json({"titre": quizz.titre, "total": len(quizz.questions),
                               "lignes": [{"login": l, "score": sc, "moi": l == s["login"]}
                                          for l, sc in qs.classement(con, ids[0])]})

        if (verbe, route) == ("GET", "recommandation"):
            exiger_joueur()
            r = recommandation.recommander(con, s["id"])
            return self._json(None if r is None else {"quizz": quizz_resume(con, r.quizz, s["id"]), "raison": r.raison})

        # ------------------------------------------------ administration (US03, US06, US08, US10, US16)
        if (verbe, route) == ("GET", "admin/quizz"):
            exiger_admin()
            return self._json(quizz_complet(qs.charger_quizz(con, ids[0])))

        if (verbe, route) == ("POST", "admin/quizz"):
            a = exiger_admin()
            q = quizz_depuis_editeur(self._corps())
            q.id_createur = a["id"]
            q.statut = "brouillon"  # invisible des joueurs tant qu'il n'est pas testé puis validé
            id_q = qs.enregistrer_quizz(con, q)
            journal.noter(con, a["id"], a["login"], "quizz_cree", q.titre)
            return self._json({"id": id_q}, 201)

        if (verbe, route) == ("PUT", "admin/quizz"):
            a = exiger_admin()
            q = quizz_depuis_editeur(self._corps())
            q.id_quizz = ids[0]
            qs.modifier_quizz(con, q, repasser_en_brouillon=True)  # à retester et revalider
            journal.noter(con, a["id"], a["login"], "quizz_modifie", q.titre)
            return self._json({"id": q.id_quizz})

        if (verbe, route) == ("POST", "admin/quizz/valider"):
            a = exiger_admin()
            qs.valider_publication(con, ids[0])
            journal.noter(con, a["id"], a["login"], "quizz_valide", qs.charger_quizz(con, ids[0]).titre)
            return self._json({"ok": True})

        if (verbe, route) == ("POST", "admin/quizz/restaurer"):
            a = exiger_admin()
            qs.restaurer_quizz(con, ids[0])
            journal.noter(con, a["id"], a["login"], "quizz_restaure", qs.charger_quizz(con, ids[0]).titre)
            return self._json({"ok": True})

        if (verbe, route) == ("GET", "admin/questions"):
            exiger_admin()
            try:
                id_quizz = int(query.get("quizz", ["0"])[0] or 0) or None
            except ValueError:
                raise ErreurHTTP(400, "Quizz invalide.")
            return self._json(qs.stats_questions(con, id_quizz))

        if (verbe, route) == ("POST", "admin/quizz/depublier"):
            a = exiger_admin()
            qs.depublier(con, ids[0])
            journal.noter(con, a["id"], a["login"], "quizz_depublie", qs.charger_quizz(con, ids[0]).titre)
            return self._json({"ok": True})

        if (verbe, route) == ("DELETE", "admin/quizz"):
            a = exiger_admin()
            titre = qs.charger_quizz(con, ids[0]).titre  # erreur lisible si déjà supprimé
            gardees = qs.supprimer_quizz(con, ids[0])
            journal.noter(con, a["id"], a["login"], "quizz_supprime",
                          f"{titre} (archivé : {gardees} partie(s) gardée(s))" if gardees else titre)
            return self._json({"ok": True, "archive": bool(gardees), "parties_gardees": gardees})

        if (verbe, route) == ("GET", "admin/quizz/export"):
            exiger_admin()
            q = qs.charger_quizz(con, ids[0])
            nom = "".join(ch if ch.isalnum() else "_" for ch in q.titre).strip("_").lower() or "quizz"
            corps = json.dumps(importer.quizz_vers_dict(q), ensure_ascii=False, indent=2).encode()
            return self._envoyer(200, corps, "application/json; charset=utf-8",
                                 {"Content-Disposition": f'attachment; filename="{nom}.json"'})

        if (verbe, route) == ("POST", "admin/import"):
            exiger_admin()
            d = self._corps()
            nom = Path(str(d.get("nom", "quizz.txt"))).name
            suffixe = ".json" if nom.lower().endswith(".json") else ".txt"
            with tempfile.TemporaryDirectory() as dossier:
                chemin = Path(dossier) / (Path(nom).stem + suffixe)  # le titre par défaut vient du nom du fichier
                chemin.write_text(str(d.get("contenu", "")), encoding="utf-8")
                q = importer.lire_quizz(chemin)
            return self._json(quizz_complet(q))

        if (verbe, route) == ("POST", "admin/generer"):
            exiger_admin()
            d = self._corps()
            try:
                nb = int(d.get("nb", 5))
            except (TypeError, ValueError):
                raise ErreurHTTP(400, "Nombre de questions invalide.")
            q = generateur.generer_quizz(str(d.get("sujet", "")), nb, bool(d.get("depuis_texte")))
            return self._json(quizz_complet(q))

        # ------------------------------------------------ assistant RAG (V2)
        if (verbe, route) == ("POST", "assistant"):
            exiger_joueur()
            question = str(self._corps().get("question", ""))
            historique = conversation.lire(con, s["id"], 10)   # seulement le fil de CE compte
            p = parties.en_cours(con, s["id"])  # pendant une partie, l'assistant ne souffle pas ses questions
            enonces = [] if p is None else [x.enonce for x in qs.charger_quizz(con, p["id_quizz"]).questions]
            r = assistant.repondre(question, historique, enonces)
            journal.noter(con, s["id"], s["login"], "assistant", question[:200])
            if question.strip():
                conversation.ajouter(con, s["id"], " ".join(question.split())[:500], r)
            return self._json(r)

        if (verbe, route) == ("GET", "assistant"):
            exiger_joueur()
            return self._json(conversation.lire(con, s["id"]))

        if (verbe, route) == ("DELETE", "assistant"):
            exiger_joueur()
            conversation.effacer(con, s["id"])
            return self._json({"ok": True})

        # ------------------------------------------------ espace joueur (V2)
        if (verbe, route) == ("GET", "moi"):
            exiger_joueur()
            return self._json(tableau_joueur(con, s["id"]))

        # ------------------------------------------------ administration des comptes (V2)
        if (verbe, route) == ("GET", "admin/stats"):
            exiger_admin()
            return self._json(tableau_admin(con))

        if (verbe, route) == ("GET", "admin/utilisateurs"):
            exiger_admin()
            return self._json(auth.lister_utilisateurs(con))

        if (verbe, route) == ("POST", "admin/utilisateurs"):
            exiger_admin()
            d = self._corps()
            u = auth.inscrire(con, str(d.get("login", "")), str(d.get("mdp", "")), bool(d.get("admin")))
            journal.noter(con, s["id"], s["login"], "compte_cree", f"{u.login}{' (admin)' if u.est_admin else ''}")
            return self._json({"id": u.id_utilisateur}, 201)

        if (verbe, route) == ("GET", "admin/utilisateurs/historique"):
            exiger_admin()
            row = con.execute("SELECT * FROM utilisateur WHERE id_utilisateur = ? AND supprime = 0",
                              (ids[0],)).fetchone()
            if row is None:
                raise ErreurHTTP(404, "Utilisateur introuvable.")
            return self._json({
                "login": row["login"], "admin": bool(row["est_admin"]), "depuis": row["date_creation"],
                "tableau": tableau_joueur(con, ids[0]),
                "parties": [{"titre": t.titre_quizz, "score": t.score, "total": t.nb_questions,
                             "duree": t.duree_secondes, "date": t.date_passage} for t in qs.historique(con, ids[0])],
                "actions": journal.lister(con, id_utilisateur=ids[0])})

        if (verbe, route) == ("GET", "admin/journal"):
            exiger_admin()
            try:
                qui = int(query["utilisateur"][0]) if query.get("utilisateur", [""])[0] else None
            except ValueError:
                raise ErreurHTTP(400, "Utilisateur invalide.")
            action = query.get("action", [""])[0] or None
            return self._json({"libelles": journal.LIBELLES,
                               "lignes": journal.lister(con, qui, action, int(query.get("limite", ["500"])[0] or 500))})

        if (verbe, route) == ("PUT", "admin/utilisateurs"):
            a = exiger_admin()
            d = self._corps()
            if ids[0] == a["id"] and not d.get("admin"):
                raise ErreurHTTP(400, "Tu ne peux pas retirer tes propres droits d'administrateur.")
            auth.modifier_utilisateur(con, ids[0], str(d.get("login", "")), bool(d.get("admin")))
            if d.get("mdp"):
                auth.changer_mot_de_passe(con, ids[0], str(d["mdp"]))
            journal.noter(con, a["id"], a["login"], "compte_modifie",
                          f"{str(d.get('login', '')).strip()}{' (admin)' if d.get('admin') else ''}"
                          f"{', mot de passe réinitialisé' if d.get('mdp') else ''}")
            if d.get("mdp"):  # mot de passe réinitialisé : ce compte est déconnecté partout
                with con:
                    con.execute("DELETE FROM session WHERE id_utilisateur = ?", (ids[0],))
            return self._json({"ok": True})

        if (verbe, route) == ("DELETE", "admin/utilisateurs"):
            a = exiger_admin()
            if ids[0] == a["id"]:
                raise ErreurHTTP(400, "Tu ne peux pas supprimer ton propre compte.")
            cible = con.execute("SELECT login FROM utilisateur WHERE id_utilisateur = ?", (ids[0],)).fetchone()
            anonymise = auth.supprimer_utilisateur(con, ids[0])
            journal.noter(con, a["id"], a["login"], "compte_supprime",
                          (cible["login"] if cible else "") + (" (anonymisé, parties gardées)" if anonymise else ""))
            return self._json({"ok": True, "anonymise": anonymise})

        raise ErreurHTTP(404, "Cette adresse n'existe pas.")

    def _ouvrir_session(self, con, u, doit_changer: bool):
        jeton = secrets.token_urlsafe(32)
        with con:
            con.execute("DELETE FROM session WHERE expire_le <= datetime('now')")  # ménage des sessions périmées
            con.execute("INSERT INTO session (empreinte_jeton, id_utilisateur, doit_changer, expire_le) "
                        "VALUES (?, ?, ?, datetime('now', ?))",
                        (empreinte(jeton), u.id_utilisateur, int(doit_changer), f"+{DUREE_SESSION} seconds"))
        return self._json({"login": u.login, "admin": u.est_admin, "doit_changer": doit_changer},
                          entetes={"Set-Cookie": f"kwizz={jeton}; Path=/; Max-Age={DUREE_SESSION}; "
                                                 "HttpOnly; SameSite=Strict"})


def charger_visible(con, id_quizz: int, s: dict) -> Quizz:
    """Un brouillon n'existe pas pour un joueur (même message qu'un quizz supprimé)."""
    quizz = qs.charger_quizz(con, id_quizz)
    if quizz.statut != "publie" and not s["admin"]:
        raise ErreurHTTP(404, "Ce quizz n'existe pas ou n'est pas encore publié.")
    return quizz


# ---------------------------------------------------------------- tableaux de bord (V2)
def _reussite(score, total) -> int:
    return round(100 * score / total) if total else 0


def tableau_joueur(con, id_utilisateur: int) -> dict:
    u = con.execute("SELECT login, date_creation FROM utilisateur WHERE id_utilisateur = ?",
                    (id_utilisateur,)).fetchone()
    g = con.execute("SELECT COUNT(*) AS n, COALESCE(SUM(score), 0) AS s, COALESCE(SUM(nb_questions), 0) AS t, "
                    "COALESCE(SUM(duree_secondes), 0) AS d FROM tentative WHERE id_utilisateur = ?",
                    (id_utilisateur,)).fetchone()
    themes = con.execute(
        "SELECT q.theme, COUNT(*) AS n, SUM(t.score) AS s, SUM(t.nb_questions) AS tot FROM tentative t "
        "JOIN quizz q USING (id_quizz) WHERE t.id_utilisateur = ? GROUP BY q.theme ORDER BY q.theme",
        (id_utilisateur,)).fetchall()
    joues = con.execute("SELECT COUNT(DISTINCT id_quizz) FROM tentative WHERE id_utilisateur = ?",
                        (id_utilisateur,)).fetchone()[0]
    return {"login": u["login"], "depuis": u["date_creation"], "parties": g["n"], "reussite": _reussite(g["s"], g["t"]),
            "temps_total": g["d"], "quizz_joues": joues,
            "quizz_total": con.execute("SELECT COUNT(*) FROM quizz WHERE archive = 0").fetchone()[0],
            "themes": [{"theme": r["theme"], "parties": r["n"], "reussite": _reussite(r["s"], r["tot"])}
                       for r in themes]}


def tableau_admin(con) -> dict:
    un = lambda sql: con.execute(sql).fetchone()[0]  # noqa: E731
    g = con.execute("SELECT COALESCE(SUM(score), 0) AS s, COALESCE(SUM(nb_questions), 0) AS t FROM tentative").fetchone()
    themes = con.execute(
        "SELECT q.theme, COUNT(DISTINCT q.id_quizz) AS nq, COUNT(t.id_tentative) AS n, "
        "COALESCE(SUM(t.score), 0) AS s, COALESCE(SUM(t.nb_questions), 0) AS tot "
        "FROM quizz q LEFT JOIN tentative t USING (id_quizz) WHERE q.archive = 0 "
        "GROUP BY q.theme ORDER BY q.theme").fetchall()
    jours = {r["jour"]: r["n"] for r in con.execute(
        "SELECT date(date_passage) AS jour, COUNT(*) AS n FROM tentative "
        "WHERE date_passage >= date('now', '-13 days') GROUP BY jour")}
    quatorze = [r[0] for r in con.execute(
        "WITH RECURSIVE j(d) AS (SELECT date('now', '-13 days') UNION ALL SELECT date(d, '+1 day') FROM j "
        "WHERE d < date('now')) SELECT d FROM j")]
    dernieres = con.execute(
        "SELECT t.date_passage, t.score, t.nb_questions, t.duree_secondes, u.login, q.titre FROM tentative t "
        "JOIN utilisateur u USING (id_utilisateur) JOIN quizz q USING (id_quizz) "
        "ORDER BY t.id_tentative DESC LIMIT 10").fetchall()
    return {"utilisateurs": un("SELECT COUNT(*) FROM utilisateur WHERE supprime = 0"),
            "admins": un("SELECT COUNT(*) FROM utilisateur WHERE est_admin = 1"),
            "quizz": un("SELECT COUNT(*) FROM quizz WHERE archive = 0"), "parties": un("SELECT COUNT(*) FROM tentative"),
            "brouillons": un("SELECT COUNT(*) FROM quizz WHERE statut = 'brouillon' AND archive = 0"),
            "actifs_7j": un("SELECT COUNT(DISTINCT id_utilisateur) FROM tentative "
                            "WHERE date_passage >= date('now', '-6 days')"),
            "reussite": _reussite(g["s"], g["t"]),
            "par_jour": [{"jour": j, "parties": jours.get(j, 0)} for j in quatorze],
            "par_quizz": stats_par_quizz(con),
            "dernieres": [{"date": r["date_passage"], "login": r["login"], "titre": r["titre"], "score": r["score"],
                           "total": r["nb_questions"], "duree": r["duree_secondes"]} for r in dernieres],
            "themes": [{"theme": r["theme"], "quizz": r["nq"], "parties": r["n"], "reussite": _reussite(r["s"], r["tot"])}
                       for r in themes]}


def stats_par_quizz(con) -> list[dict]:
    """Parties, joueurs, réussite et question la plus ratée de chaque quizz (questions actuelles seulement)."""
    pires = {}
    for r in con.execute(
            "SELECT q.id_quizz, q.enonce, COUNT(*) AS n, SUM(1 - r.juste) AS ratees FROM resultat_question r "
            "JOIN question q USING (id_question) WHERE q.active = 1 GROUP BY q.id_question "
            "HAVING ratees > 0 ORDER BY 1.0 * ratees / n DESC, n DESC"):
        pires.setdefault(r["id_quizz"], {"enonce": r["enonce"], "taux": round(100 * r["ratees"] / r["n"])})
    lignes = []
    for q in qs.lister_quizz(con):
        r = con.execute("SELECT COUNT(*) AS n, COUNT(DISTINCT id_utilisateur) AS j, COALESCE(SUM(score), 0) AS s, "
                        "COALESCE(SUM(nb_questions), 0) AS t FROM tentative WHERE id_quizz = ?", (q.id_quizz,)).fetchone()
        lignes.append({"id": q.id_quizz, "titre": q.titre, "theme": q.theme, "statut": q.statut,
                       "parties": r["n"], "joueurs": r["j"], "reussite": _reussite(r["s"], r["t"]),
                       "pire": pires.get(q.id_quizz)})
    return sorted(lignes, key=lambda l: -l["parties"])


# ---------------------------------------------------------------- premier lancement
def preparer_base(demo: bool) -> None:
    con = connexion(CHEMIN_BASE)
    try:
        auth.creer_admin_par_defaut(con)
        admin = con.execute("SELECT id_utilisateur FROM utilisateur WHERE est_admin = 1").fetchone()[0]
        presents = {q.titre for q in qs.lister_quizz(con, inclure_archives=True)}
        for fichier in sorted((RACINE / "data" / "exemples").glob("*.txt")):
            q = importer.lire_quizz(fichier)
            if q.titre in presents:
                # base v2.0 : on complète seulement le thème des quizz d'exemple encore « Divers »
                con.execute("UPDATE quizz SET theme = ? WHERE titre = ? AND theme = 'Divers'", (q.theme, q.titre))
                con.commit()
                continue
            q.id_createur = admin
            qs.enregistrer_quizz(con, q)
        if demo and con.execute("SELECT 1 FROM utilisateur WHERE login = 'alice'").fetchone() is None:
            joueurs = {l: auth.creer_compte_demo(con, l, "demo") for l in ("alice", "bob", "chloe")}
            par_titre = {q.titre: qs.charger_quizz(con, q.id_quizz) for q in qs.lister_quizz(con)}
            for login, titre, justes in [("alice", "Capitales d'Europe", 3), ("bob", "Capitales d'Europe", 1),
                                         ("chloe", "Capitales d'Europe", 2), ("alice", "Gestion de projet", 6),
                                         ("bob", "Gestion de projet", 7), ("bob", "Les bases de Python", 2)]:
                q = par_titre.get(titre)
                if q:
                    rep = {x.id_question: {x.bonnes_reponses()[0].id_choix} for x in q.questions[:justes]}
                    qs.enregistrer_tentative(con, joueurs[login].id_utilisateur, q, rep, 40)
    finally:
        con.close()


def main(argv=None):
    global CHEMIN_BASE
    p = argparse.ArgumentParser(description="MyKwizz : Kwizz dans le navigateur.")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--base", type=Path, default=CHEMIN_PAR_DEFAUT, help="fichier SQLite (défaut : quizz.db)")
    p.add_argument("--demo", action="store_true", help="ajouter des joueurs et des parties de démonstration")
    p.add_argument("--sans-navigateur", action="store_true", help="ne pas ouvrir le navigateur")
    args = p.parse_args(argv)
    if sys.stdout is not None:
        sys.stdout.reconfigure(encoding="utf-8")
    CHEMIN_BASE = args.base
    preparer_base(args.demo)
    serveur = ThreadingHTTPServer(("127.0.0.1", args.port), Gestionnaire)
    adresse = f"http://127.0.0.1:{args.port}/"
    print(f"MyKwizz tourne sur {adresse}  (Ctrl+C pour arrêter)")
    print("Premier lancement : admin / admin, puis choix d'un nouveau mot de passe.")
    if not args.sans_navigateur:
        threading.Timer(0.6, webbrowser.open, (adresse,)).start()
    try:
        serveur.serve_forever()
    except KeyboardInterrupt:
        print("\nAu revoir !")
    finally:
        serveur.server_close()


if __name__ == "__main__":
    main()
