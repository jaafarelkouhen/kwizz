"""Interface console : menus, saisies et affichages. Aucun SQL ici, on passe par les services."""
import getpass
import time

from .. import auth, importer, quiz_service as qs
from ..models import Choix, Question, Quizz, Utilisateur


# ---------------------------------------------------------------- utilitaires de saisie
def demander(message: str) -> str:
    return input(message).strip()


def demander_mot_de_passe(message: str) -> str:
    """Saisie masquée : les caractères tapés ne s'affichent pas (US14)."""
    return getpass.getpass(message)


def demander_entier(message: str, mini: int, maxi: int) -> int:
    while True:
        val = demander(message)
        if val.isdigit() and mini <= int(val) <= maxi:
            return int(val)
        print(f"  Entrez un nombre entre {mini} et {maxi}.")


def demander_non_vide(message: str) -> str:
    while True:
        val = demander(message)
        if val:
            return val
        print("  Ce champ ne peut pas être vide.")


def demander_duree(message: str) -> int | None:
    """Renvoie un nombre de secondes > 0, ou None si l'utilisateur appuie juste sur Entrée."""
    while True:
        val = demander(message)
        if not val:
            return None
        if val.isdigit() and int(val) > 0:
            return int(val)
        print("  Entrez un nombre de secondes positif, ou appuyez sur Entrée.")


def menu(titre: str, options: list[str]) -> int:
    print(f"\n=== {titre} ===")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    return demander_entier("Votre choix : ", 1, len(options))


def pause():
    input("\n(Entrée pour continuer)")


# ---------------------------------------------------------------- comptes (US01, US02)
BANNIERE = r"""
  _  __        _
 | |/ /_    __(_)________
 | ' /\ \/\/ / |_  /_  /
 | . \ \_/\_/| |/ / / /
 |_|\_\      |_/___/___|   par Kwizz & Co
"""
ESSAIS_CONNEXION = 3


def ecran_inscription(con) -> Utilisateur | None:
    """Crée un compte puis connecte directement le nouvel utilisateur."""
    print("\n--- Créer un compte ---")
    print("  (login : 3 caractères minimum · mot de passe : 4 caractères minimum)")
    login = demander("Login : ")
    mdp = demander_mot_de_passe("Mot de passe : ")
    if demander_mot_de_passe("Confirmez le mot de passe : ") != mdp:
        print("Erreur : les deux mots de passe ne correspondent pas.")
        return None
    try:
        auth.inscrire(con, login, mdp)
        print(f"Compte « {login} » créé. Bienvenue !")
        return auth.connecter(con, login, mdp)
    except auth.ErreurAuth as e:
        print(f"Erreur : {e}")
        return None


def ecran_connexion(con) -> Utilisateur | None:
    """Laisse ESSAIS_CONNEXION tentatives, puis revient à l'accueil."""
    print("\n--- Connexion ---")
    for essai in range(1, ESSAIS_CONNEXION + 1):
        login = demander("Login : ")
        mdp = demander_mot_de_passe("Mot de passe : ")
        try:
            user = auth.connecter(con, login, mdp)
            print(f"Bonjour {user.login} !")
            return user
        except auth.ErreurAuth as e:
            restants = ESSAIS_CONNEXION - essai
            print(f"Erreur : {e}" + (f" ({restants} essai(s) restant(s))" if restants else ""))
    print("Trop d'essais, retour à l'accueil.")
    return None


# ---------------------------------------------------------------- joueur
def choisir_quizz(con) -> Quizz | None:
    liste = qs.lister_quizz(con)
    if not liste:
        print("Aucun quizz disponible pour l'instant.")
        return None
    print("\nQuizz disponibles :")
    for i, q in enumerate(liste, 1):
        timer = f" (⏱ {q.duree_limite}s)" if q.duree_limite else ""
        print(f"  {i}. {q.titre}{timer} — {q.description}")
    n = demander_entier("Numéro du quizz (0 = retour) : ", 0, len(liste))
    return None if n == 0 else qs.charger_quizz(con, liste[n - 1].id_quizz)


def ecran_jouer(con, user: Utilisateur):
    quizz = choisir_quizz(con)
    if quizz is None:
        return
    print(f"\n### {quizz.titre} — {len(quizz.questions)} question(s) ###")
    # TODO (US13) : random.shuffle(quizz.questions) si option activée
    # TODO (US09) : arrêter le quizz si quizz.duree_limite est dépassée
    reponses: dict[int, set[int]] = {}
    debut = time.monotonic()
    for num, q in enumerate(quizz.questions, 1):
        print(f"\nQ{num}. {q.enonce}")
        for i, c in enumerate(q.choix, 1):
            print(f"   {i}) {c.texte}")
        n = demander_entier("Votre réponse : ", 1, len(q.choix))
        reponses[q.id_question] = {q.choix[n - 1].id_choix}
    duree = int(time.monotonic() - debut)

    t = qs.enregistrer_tentative(con, user.id_utilisateur, quizz, reponses, duree)
    afficher_correction(quizz, reponses)
    print(f"\n>>> Score : {t.score}/{t.nb_questions} en {duree}s <<<")
    pause()


def afficher_correction(quizz: Quizz, reponses: dict[int, set[int]]):
    print("\n--- Correction ---")
    for num, q in enumerate(quizz.questions, 1):
        ok = qs.est_juste(q, reponses.get(q.id_question, set()))
        bonnes = ", ".join(c.texte for c in q.bonnes_reponses())
        print(f"{'✔' if ok else '✘'} Q{num}. {q.enonce}  →  {bonnes}")


def ecran_historique(con, user: Utilisateur):
    tentatives = qs.historique(con, user.id_utilisateur)
    if not tentatives:
        print("Vous n'avez encore passé aucun quizz.")
    for t in tentatives:
        print(f"  {t.date_passage}  {t.titre_quizz:<30} {t.score}/{t.nb_questions}")
    pause()


# ---------------------------------------------------------------- admin
def afficher_recapitulatif(quizz: Quizz):
    print(f"\n--- Récapitulatif : {quizz.titre} ---")
    if quizz.description:
        print(f"  {quizz.description}")
    print(f"  Minuterie : {f'{quizz.duree_limite} s' if quizz.duree_limite else 'aucune'}")
    for num, q in enumerate(quizz.questions, 1):
        print(f"  Q{num}. {q.enonce}")
        for c in q.choix:
            print(f"      {'✔' if c.est_correct else ' '} {c.texte}")


def ecran_creer_quizz(con, user: Utilisateur):
    print("\n--- Créer un quizz ---")
    quizz = Quizz(demander_non_vide("Titre : "), demander("Description (facultative) : "),
                  demander_duree("Durée limite en secondes (Entrée = pas de minuterie) : "),
                  id_createur=user.id_utilisateur)
    nb_q = demander_entier("Nombre de questions : ", 1, 100)
    for i in range(1, nb_q + 1):
        q = Question(demander_non_vide(f"\nÉnoncé de la question {i} : "))
        nb_c = demander_entier("Nombre de choix : ", 2, 10)
        for j in range(1, nb_c + 1):
            q.choix.append(Choix(demander_non_vide(f"  Choix {j} : ")))
        bonne = demander_entier("Numéro de la bonne réponse : ", 1, nb_c)
        q.choix[bonne - 1].est_correct = True
        quizz.questions.append(q)
    afficher_recapitulatif(quizz)
    if demander("Enregistrer ce quizz ? (o/n) ").lower() != "o":
        print("Création annulée, rien n'a été enregistré.")
        return
    try:
        qs.enregistrer_quizz(con, quizz)
        print(f"Quizz « {quizz.titre} » enregistré.")
    except qs.ErreurQuizz as e:
        print(f"Erreur : {e}")


def ecran_importer(con, user: Utilisateur):
    chemin = demander("Chemin du fichier texte : ").strip('"')
    try:
        quizz = importer.lire_quizz_texte(chemin)
        quizz.id_createur = user.id_utilisateur
        qs.enregistrer_quizz(con, quizz)
        print(f"Quizz « {quizz.titre} » importé ({len(quizz.questions)} questions).")
    except FileNotFoundError:
        print("Fichier introuvable.")
    except (importer.ErreurFormat, qs.ErreurQuizz) as e:
        print(f"Erreur : {e}")


def ecran_supprimer(con, user: Utilisateur):
    quizz = choisir_quizz(con)
    if quizz and demander(f"Supprimer « {quizz.titre} » ? (o/n) ").lower() == "o":
        qs.supprimer_quizz(con, quizz.id_quizz)
        print("Quizz supprimé.")


# ---------------------------------------------------------------- boucles principales
def session(con, user: Utilisateur):
    actions = [("Passer un quizz", ecran_jouer), ("Mon historique", ecran_historique)]
    if user.est_admin:
        actions += [("Créer un quizz", ecran_creer_quizz),
                    ("Importer un quizz (fichier texte)", ecran_importer),
                    ("Supprimer un quizz", ecran_supprimer)]
    while True:
        role = "admin" if user.est_admin else "joueur"
        n = menu(f"Connecté : {user.login} ({role})", [a[0] for a in actions] + ["Se déconnecter"])
        if n == len(actions) + 1:
            return
        actions[n - 1][1](con, user)


def lancer(con):
    print(BANNIERE)
    print("Bienvenue dans Kwizz !")
    while True:
        n = menu("Accueil", ["Se connecter", "Créer un compte", "Quitter"])
        if n in (1, 2):
            user = ecran_connexion(con) if n == 1 else ecran_inscription(con)
            if user:
                session(con, user)
        else:
            print("À bientôt !")
            return
