"""Interface graphique Tkinter (US11).

Elle appelle EXACTEMENT les mêmes services que la console (auth, quiz_service, importer) :
aucun SQL ici. Chaque écran est un tk.Frame ; l'application remplace l'écran affiché.
La création et la modification de quizz restent dans la console (python main.py).
"""
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from .. import auth, importer, quiz_service as qs
from ..ia import client as client_ia, explications, generateur, recommandation
from ..models import Quizz, Tentative

LOGO = Path(__file__).resolve().parent / "logo.png"
POLICE = ("Segoe UI", 11)
POLICE_TITRE = ("Segoe UI", 15, "bold")
POLICE_QUESTION = ("Segoe UI", 13)
ROUGE, VERT, GRIS = "#c0392b", "#1e8449", "#666666"


def executer_en_fond(widget: tk.Misc, travail, quand_fini):
    """Lance travail() dans un thread pour ne pas figer la fenêtre pendant un appel à l'IA.

    Tkinter ne doit être touché que depuis le thread principal : le thread se contente de
    calculer, et on vérifie toutes les 100 ms (after) s'il a fini avant d'appeler
    quand_fini(resultat, erreur) dans le thread principal.
    """
    boite = {}

    def fond():
        try:
            boite["resultat"] = travail()
        except client_ia.ErreurIA as e:
            boite["erreur"] = e
        except Exception as e:  # imprévu : on l'affiche plutôt que de laisser l'écran bloqué
            boite["erreur"] = client_ia.ErreurIA(f"Erreur inattendue : {e}")

    fil = threading.Thread(target=fond, daemon=True)
    fil.start()

    def verifier():
        try:
            if not widget.winfo_exists():
                return  # fenêtre fermée entre-temps : on abandonne le résultat
        except tk.TclError:
            return
        if fil.is_alive():
            widget.after(100, verifier)
        else:
            quand_fini(boite.get("resultat"), boite.get("erreur"))

    widget.after(100, verifier)


class Application(tk.Tk):
    def __init__(self, con):
        super().__init__()
        self.con = con
        self.user = None
        self.title("Kwizz")
        self.geometry("680x560")
        self.minsize(560, 460)
        self.option_add("*Font", POLICE)
        self.logo = None
        if LOGO.exists():
            try:
                self.logo = tk.PhotoImage(file=LOGO)  # chargé une seule fois, réutilisé par les écrans
            except tk.TclError:
                pass  # pas de logo plutôt qu'un plantage
        self.ecran = None
        self.afficher(EcranConnexion)

    def afficher(self, classe, *args):
        """Remplace l'écran courant par un nouvel écran de la classe donnée."""
        if self.ecran is not None:
            self.ecran.destroy()
        self.ecran = classe(self, *args)
        self.ecran.pack(fill="both", expand=True, padx=20, pady=14)
        return self.ecran


class Ecran(tk.Frame):
    def __init__(self, app: Application):
        super().__init__(app)
        self.app, self.con = app, app.con
        self.message = tk.Label(self, text="", fg=ROUGE, wraplength=600, justify="left")

    def erreur(self, texte: str):
        self.message.config(text=texte, fg=ROUGE)

    def info(self, texte: str):
        self.message.config(text=texte, fg=VERT)


# ---------------------------------------------------------------- connexion / inscription
class EcranConnexion(Ecran):
    def __init__(self, app):
        super().__init__(app)
        if app.logo is not None:
            tk.Label(self, image=app.logo).pack(pady=(0, 6))
        tk.Label(self, text="Bienvenue dans Kwizz !", font=POLICE_TITRE).pack(pady=(0, 12))

        formulaire = tk.Frame(self)
        formulaire.pack()
        tk.Label(formulaire, text="Login").grid(row=0, column=0, sticky="e", padx=6, pady=4)
        tk.Label(formulaire, text="Mot de passe").grid(row=1, column=0, sticky="e", padx=6, pady=4)
        self.login = tk.Entry(formulaire, width=26)
        self.mdp = tk.Entry(formulaire, width=26, show="•")
        self.login.grid(row=0, column=1, pady=4)
        self.mdp.grid(row=1, column=1, pady=4)
        self.login.focus_set()
        self.mdp.bind("<Return>", lambda _e: self.connecter())

        boutons = tk.Frame(self)
        boutons.pack(pady=12)
        tk.Button(boutons, text="Se connecter", width=14, command=self.connecter).pack(side="left", padx=4)
        tk.Button(boutons, text="Créer un compte", width=14, command=self.inscrire).pack(side="left", padx=4)
        tk.Label(self, text="login : 3 caractères min. · mot de passe : 4 caractères min.", fg=GRIS).pack()
        self.message.pack(pady=8)

    def connecter(self):
        try:
            user = auth.connecter(self.con, self.login.get(), self.mdp.get())
        except auth.ErreurAuth as e:
            self.erreur(str(e))
            return
        if auth.utilise_mot_de_passe_par_defaut(self.con, user) and not self.changer_mot_de_passe(user):
            self.erreur("Vous devez choisir un nouveau mot de passe administrateur pour continuer.")
            return
        self.app.user = user
        self.app.afficher(EcranListe)

    def changer_mot_de_passe(self, user) -> bool:
        """US15 : renvoie False si l'admin annule."""
        while True:
            nouveau = simpledialog.askstring("Mot de passe par défaut",
                                             "Choisissez un nouveau mot de passe administrateur :",
                                             show="•", parent=self)
            if nouveau is None:
                return False
            if simpledialog.askstring("Confirmation", "Confirmez le mot de passe :", show="•", parent=self) != nouveau:
                messagebox.showerror("Kwizz", "Les deux mots de passe ne correspondent pas.", parent=self)
                continue
            try:
                auth.changer_mot_de_passe(self.con, user.id_utilisateur, nouveau)
                return True
            except auth.ErreurAuth as e:
                messagebox.showerror("Kwizz", str(e), parent=self)

    def inscrire(self):
        login, mdp = self.login.get().strip(), self.mdp.get()
        confirmation = simpledialog.askstring("Créer un compte", "Confirmez le mot de passe :", show="•", parent=self)
        if confirmation is None:
            return
        if confirmation != mdp:
            self.erreur("Les deux mots de passe ne correspondent pas.")
            return
        try:
            auth.inscrire(self.con, login, mdp)
        except auth.ErreurAuth as e:
            self.erreur(str(e))
            return
        self.app.user = auth.connecter(self.con, login, mdp)
        self.app.afficher(EcranListe)


# ---------------------------------------------------------------- liste des quizz
class EcranListe(Ecran):
    def __init__(self, app):
        super().__init__(app)
        user = app.user
        haut = tk.Frame(self)
        haut.pack(fill="x")
        role = "admin" if user.est_admin else "joueur"
        tk.Label(haut, text=f"Connecté : {user.login} ({role})", font=POLICE_TITRE).pack(side="left")
        tk.Button(haut, text="Se déconnecter", command=self.deconnecter).pack(side="right")

        self.recommandation = tk.Label(self, text="", fg=GRIS, anchor="w")
        self.recommandation.pack(fill="x", pady=(8, 0))

        tk.Label(self, text="Quizz disponibles", anchor="w").pack(fill="x", pady=(8, 2))
        cadre = tk.Frame(self)
        cadre.pack(fill="both", expand=True)
        self.liste = tk.Listbox(cadre, height=10, activestyle="none")
        barre = tk.Scrollbar(cadre, command=self.liste.yview)
        self.liste.config(yscrollcommand=barre.set)
        self.liste.pack(side="left", fill="both", expand=True)
        barre.pack(side="right", fill="y")
        self.liste.bind("<Double-Button-1>", lambda _e: self.jouer())

        self.aleatoire = tk.BooleanVar(value=False)
        tk.Checkbutton(self, text="Questions dans un ordre aléatoire", variable=self.aleatoire).pack(anchor="w")

        joueur = tk.Frame(self)
        joueur.pack(pady=(8, 0))
        tk.Button(joueur, text="▶ Jouer", width=12, command=self.jouer).pack(side="left", padx=3)
        tk.Button(joueur, text="Mon historique", width=14, command=self.historique).pack(side="left", padx=3)
        tk.Button(joueur, text="Classement", width=12, command=self.classement).pack(side="left", padx=3)
        if user.est_admin:
            admin = tk.Frame(self)
            admin.pack(pady=(6, 0))
            tk.Button(admin, text="Importer…", width=12, command=self.importer).pack(side="left", padx=3)
            tk.Button(admin, text="Exporter en JSON…", width=16, command=self.exporter).pack(side="left", padx=3)
            tk.Button(admin, text="Supprimer", width=12, command=self.supprimer).pack(side="left", padx=3)
            if client_ia.ia_disponible():  # US19 : bouton absent sans clé
                tk.Button(self, text="🤖 Générer un quizz avec l'IA…",
                          command=lambda: FenetreGenerationIA(self)).pack(pady=(6, 0))
        self.message.pack(pady=6)
        self.rafraichir()

    def rafraichir(self):
        self.quizz = qs.lister_quizz(self.con)
        self.liste.delete(0, "end")
        for q in self.quizz:
            minuterie = f"   ⏱ {q.duree_limite} s" if q.duree_limite else ""
            minuterie += "   🤖" if q.source == "ia" else ""
            description = f" — {q.description}" if q.description else ""
            self.liste.insert("end", f"{q.titre}{minuterie}{description}")
        if not self.quizz:
            self.info("Aucun quizz pour l'instant." + (" Importez-en un !" if self.app.user.est_admin else ""))
        r = recommandation.recommander(self.con, self.app.user.id_utilisateur)
        self.recommandation.config(text=f"💡 Recommandé : « {r.quizz.titre} » ({r.raison})" if r else "")

    def selection(self) -> Quizz | None:
        choix = self.liste.curselection()
        if not choix:
            self.erreur("Sélectionnez d'abord un quizz dans la liste.")
            return None
        return self.quizz[choix[0]]

    def jouer(self):
        q = self.selection()
        if q:
            quizz = qs.charger_quizz(self.con, q.id_quizz)
            self.app.afficher(EcranJeu, qs.melanger(quizz) if self.aleatoire.get() else quizz)

    def historique(self):
        self.app.afficher(EcranHistorique)

    def classement(self):
        q = self.selection()
        if q:
            self.app.afficher(EcranClassement, qs.charger_quizz(self.con, q.id_quizz))

    def importer(self):
        chemin = filedialog.askopenfilename(parent=self, title="Importer un quizz",
                                            filetypes=[("Quizz Kwizz", "*.txt *.json"), ("Tous les fichiers", "*.*")])
        if not chemin:
            return
        try:
            quizz = importer.lire_quizz(chemin)
            quizz.id_createur = self.app.user.id_utilisateur
            qs.enregistrer_quizz(self.con, quizz)
        except (importer.ErreurFormat, qs.ErreurQuizz, OSError) as e:
            self.erreur(f"Import impossible : {e}")
            return
        self.rafraichir()
        self.info(f"Quizz « {quizz.titre} » importé ({len(quizz.questions)} questions).")

    def exporter(self):
        q = self.selection()
        if not q:
            return
        chemin = filedialog.asksaveasfilename(parent=self, defaultextension=".json",
                                              initialfile=f"{q.titre}.json".replace(" ", "_"),
                                              filetypes=[("JSON", "*.json")])
        if chemin:
            importer.exporter_json(qs.charger_quizz(self.con, q.id_quizz), chemin)
            self.info(f"Quizz exporté dans {chemin}")

    def supprimer(self):
        q = self.selection()
        if q and messagebox.askyesno("Kwizz", f"Supprimer « {q.titre} » et tous ses scores ?", parent=self):
            qs.supprimer_quizz(self.con, q.id_quizz)
            self.rafraichir()
            self.info("Quizz supprimé.")

    def deconnecter(self):
        self.app.user = None
        self.app.afficher(EcranConnexion)


# ---------------------------------------------------------------- jeu (US04, US09)
class EcranJeu(Ecran):
    def __init__(self, app, quizz: Quizz):
        super().__init__(app)
        self.quizz, self.index = quizz, 0
        self.reponses: dict[int, set[int]] = {}
        self.debut = time.monotonic()
        self.minuteur = None

        haut = tk.Frame(self)
        haut.pack(fill="x")
        tk.Label(haut, text=quizz.titre, font=POLICE_TITRE).pack(side="left")
        self.chrono = tk.Label(haut, text="", font=POLICE_TITRE)
        self.chrono.pack(side="right")
        self.progression = tk.Label(self, text="", fg=GRIS, anchor="w")
        self.progression.pack(fill="x", pady=(6, 0))
        self.enonce = tk.Label(self, text="", font=POLICE_QUESTION, wraplength=600, justify="left", anchor="w")
        self.enonce.pack(fill="x", pady=12)
        self.choix_var = tk.IntVar(value=-1)
        self.cadre_choix = tk.Frame(self)
        self.cadre_choix.pack(fill="x")
        self.bouton = tk.Button(self, text="Valider", width=14, command=self.valider)
        self.bouton.pack(pady=14)
        self.message.pack()
        self.afficher_question()
        self.tic()

    def afficher_question(self):
        q = self.quizz.questions[self.index]
        self.progression.config(text=f"Question {self.index + 1} / {len(self.quizz.questions)}")
        self.enonce.config(text=q.enonce)
        for widget in self.cadre_choix.winfo_children():
            widget.destroy()
        self.choix_var.set(-1)
        for i, c in enumerate(q.choix):
            tk.Radiobutton(self.cadre_choix, text=c.texte, variable=self.choix_var, value=i,
                           anchor="w", wraplength=580, justify="left").pack(fill="x", pady=2)
        dernier = self.index == len(self.quizz.questions) - 1
        self.bouton.config(text="Terminer" if dernier else "Valider")
        self.message.config(text="")

    def ecoule(self) -> float:
        return time.monotonic() - self.debut

    def tic(self):
        """Mise à jour du chrono toutes les 250 ms ; fin automatique quand le temps est écoulé."""
        restant = qs.temps_restant(self.quizz, self.ecoule())
        if restant is None:
            return
        self.chrono.config(text=f"⏱ {int(restant)} s", fg=ROUGE if restant <= 10 else "black")
        if restant <= 0:
            self.terminer(temps_ecoule=True)
        else:
            self.minuteur = self.after(250, self.tic)

    def valider(self):
        if qs.temps_ecoule(self.quizz, self.ecoule()):
            self.terminer(temps_ecoule=True)
            return
        n = self.choix_var.get()
        if n < 0:
            self.erreur("Choisissez une réponse.")
            return
        q = self.quizz.questions[self.index]
        self.reponses[q.id_question] = {q.choix[n].id_choix}
        self.index += 1
        if self.index < len(self.quizz.questions):
            self.afficher_question()
        else:
            self.terminer()

    def terminer(self, temps_ecoule: bool = False):
        if self.minuteur is not None:
            self.after_cancel(self.minuteur)
            self.minuteur = None
        duree = int(self.ecoule())
        if self.quizz.duree_limite:
            duree = min(duree, self.quizz.duree_limite)
        t = qs.enregistrer_tentative(self.con, self.app.user.id_utilisateur, self.quizz, self.reponses, duree)
        self.app.afficher(EcranResultat, self.quizz, self.reponses, t, temps_ecoule)

    def destroy(self):
        if self.minuteur is not None:
            self.after_cancel(self.minuteur)
            self.minuteur = None
        super().destroy()


# ---------------------------------------------------------------- résultat (US05)
class CadreDefilant(tk.Frame):
    """Cadre avec barre de défilement verticale (pour les longs corrigés)."""

    def __init__(self, parent):
        super().__init__(parent)
        canvas = tk.Canvas(self, highlightthickness=0)
        barre = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.interieur = tk.Frame(canvas)
        self.interieur.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.interieur, anchor="nw")
        canvas.configure(yscrollcommand=barre.set)
        canvas.pack(side="left", fill="both", expand=True)
        barre.pack(side="right", fill="y")
        # molette de la souris, seulement quand le pointeur est au-dessus du corrigé
        defiler = lambda e: canvas.yview_scroll(-1 if e.delta > 0 else 1, "units")
        canvas.bind("<Enter>", lambda _e: canvas.bind_all("<MouseWheel>", defiler))
        canvas.bind("<Leave>", lambda _e: canvas.unbind_all("<MouseWheel>"))


class EcranResultat(Ecran):
    def __init__(self, app, quizz: Quizz, reponses: dict[int, set[int]], tentative: Tentative,
                 temps_ecoule: bool = False):
        super().__init__(app)
        self.quizz, self.reponses = quizz, reponses
        titre = f"Résultat : {tentative.score} / {tentative.nb_questions}"
        if tentative.duree_secondes is not None:
            titre += f"  en {tentative.duree_secondes} s"
        tk.Label(self, text=titre, font=POLICE_TITRE).pack(anchor="w")
        if temps_ecoule:
            tk.Label(self, text="⏰ Temps écoulé : les questions sans réponse comptent comme fausses.",
                     fg=ROUGE).pack(anchor="w")
        self.corrige = CadreDefilant(self)
        self.corrige.pack(fill="both", expand=True, pady=10)
        for num, q in enumerate(quizz.questions, 1):
            self.ligne_corrige(num, q)
        tk.Button(self, text="Retour à la liste", width=16,
                  command=lambda: app.afficher(EcranListe)).pack(pady=(0, 4))
        self.message.pack()

    def ligne_corrige(self, num, q):
        ok = qs.est_juste(q, self.reponses.get(q.id_question, set()))
        ligne = tk.Frame(self.corrige.interieur)
        ligne.pack(fill="x", pady=3)
        tk.Label(ligne, text="✔" if ok else "✘", fg=VERT if ok else ROUGE,
                 font=POLICE_TITRE, width=2).pack(side="left", anchor="n")
        bonnes = ", ".join(c.texte for c in q.bonnes_reponses())
        texte = f"Q{num}. {q.enonce}\n→ {bonnes}"
        tk.Label(ligne, text=texte, justify="left", anchor="w", wraplength=440).pack(side="left", fill="x")
        if not ok and client_ia.ia_disponible():
            tk.Button(ligne, text="Pourquoi ?", command=lambda: self.expliquer(q)).pack(side="right", anchor="n")
        return ligne, ok

    def expliquer(self, q):
        """US17 : explication de l'IA dans une boîte de dialogue (appel en arrière-plan)."""
        self.info("⏳ L'IA prépare l'explication…")
        self.en_cours = True

        def fini(texte, erreur):
            self.en_cours = False
            if erreur:
                self.erreur(str(erreur))
                return
            self.message.config(text="")
            messagebox.showinfo("Pourquoi ?", f"{q.enonce}\n\n{texte}", parent=self)

        executer_en_fond(self, lambda: explications.expliquer(q, self.reponses.get(q.id_question, set())), fini)


# ---------------------------------------------------------------- historique (US07) et classement (US12)
class EcranTableau(Ecran):
    def __init__(self, app, titre: str, colonnes: list[tuple[str, int]], lignes: list[tuple], vide: str):
        super().__init__(app)
        tk.Label(self, text=titre, font=POLICE_TITRE).pack(anchor="w", pady=(0, 8))
        self.tableau = ttk.Treeview(self, columns=[c for c, _ in colonnes], show="headings", height=12)
        for nom, largeur in colonnes:
            self.tableau.heading(nom, text=nom)
            self.tableau.column(nom, width=largeur, anchor="w")
        for ligne in lignes:
            self.tableau.insert("", "end", values=ligne)
        self.tableau.pack(fill="both", expand=True)
        if not lignes:
            self.info(vide)
        self.message.pack(pady=4)
        tk.Button(self, text="Retour", width=12, command=lambda: app.afficher(EcranListe)).pack(pady=6)


class EcranHistorique(EcranTableau):
    def __init__(self, app):
        lignes = [(t.date_passage, t.titre_quizz, f"{t.score} / {t.nb_questions}")
                  for t in qs.historique(app.con, app.user.id_utilisateur)]
        super().__init__(app, "Mon historique", [("Date", 170), ("Quizz", 300), ("Score", 90)],
                         lignes, "Vous n'avez encore passé aucun quizz.")


class EcranClassement(EcranTableau):
    def __init__(self, app, quizz: Quizz):
        medailles = {1: "🥇", 2: "🥈", 3: "🥉"}
        lignes = [(medailles.get(rang, rang), login, f"{score} / {len(quizz.questions)}")
                  for rang, (login, score) in enumerate(qs.classement(app.con, quizz.id_quizz), 1)]
        super().__init__(app, f"🏆 Classement — {quizz.titre}", [("Rang", 70), ("Joueur", 300), ("Meilleur score", 140)],
                         lignes, "Personne n'a encore joué à ce quizz.")


# ---------------------------------------------------------------- génération IA (US16)
class FenetreGenerationIA(tk.Toplevel):
    """Fenêtre de génération : thème ou texte → aperçu → l'admin enregistre ou abandonne."""

    def __init__(self, liste: EcranListe):
        super().__init__(liste)
        self.liste, self.con, self.quizz = liste, liste.con, None
        self.title("Générer un quizz avec l'IA")
        self.geometry("620x560")
        self.transient(liste.app)

        self.depuis_texte = tk.BooleanVar(value=False)
        haut = tk.Frame(self)
        haut.pack(fill="x", padx=14, pady=(12, 4))
        tk.Radiobutton(haut, text="Thème", variable=self.depuis_texte, value=False).pack(side="left")
        tk.Radiobutton(haut, text="Texte collé", variable=self.depuis_texte, value=True).pack(side="left")
        tk.Label(haut, text="Questions :").pack(side="left", padx=(20, 4))
        self.nb = tk.Spinbox(haut, from_=1, to=generateur.NB_QUESTIONS_MAX, width=4)
        self.nb.delete(0, "end")
        self.nb.insert(0, "5")
        self.nb.pack(side="left")

        tk.Label(self, text="Thème (ex. « les volcans ») ou texte à transformer en quizz :", anchor="w").pack(
            fill="x", padx=14)
        self.sujet = tk.Text(self, height=5, wrap="word")
        self.sujet.pack(fill="x", padx=14)
        self.bouton_generer = tk.Button(self, text="Générer", width=14, command=self.generer)
        self.bouton_generer.pack(pady=8)

        tk.Label(self, text="Aperçu (à vérifier : une IA peut se tromper)", anchor="w").pack(fill="x", padx=14)
        self.apercu = tk.Text(self, height=12, wrap="word", state="disabled", bg="#fafafa")
        self.apercu.pack(fill="both", expand=True, padx=14)
        self.message = tk.Label(self, text="", fg=ROUGE, wraplength=580)
        self.message.pack(pady=4)
        bas = tk.Frame(self)
        bas.pack(pady=(0, 10))
        self.bouton_enregistrer = tk.Button(bas, text="Enregistrer", width=14, state="disabled",
                                            command=self.enregistrer)
        self.bouton_enregistrer.pack(side="left", padx=4)
        tk.Button(bas, text="Fermer", width=14, command=self.destroy).pack(side="left", padx=4)

    def generer(self):
        try:
            nb = int(self.nb.get())
        except ValueError:
            self.message.config(text="Nombre de questions invalide.", fg=ROUGE)
            return
        sujet, depuis_texte = self.sujet.get("1.0", "end"), self.depuis_texte.get()
        self.message.config(text="⏳ L'IA prépare le quizz… (la fenêtre reste utilisable)", fg=GRIS)
        self.bouton_generer.config(state="disabled")
        self.en_cours = True

        def fini(quizz, erreur):
            self.en_cours = False
            self.bouton_generer.config(state="normal")
            self.quizz = quizz
            if erreur:
                self.message.config(text=str(erreur), fg=ROUGE)
            else:
                self.message.config(text="Relisez l'aperçu, puis enregistrez ou relancez une génération.", fg=VERT)
            self.afficher_apercu()

        executer_en_fond(self, lambda: generateur.generer_quizz(sujet, nb, depuis_texte), fini)

    def afficher_apercu(self):
        self.apercu.config(state="normal")
        self.apercu.delete("1.0", "end")
        if self.quizz:
            lignes = [self.quizz.titre, self.quizz.description, ""]
            for num, q in enumerate(self.quizz.questions, 1):
                lignes.append(f"Q{num}. {q.enonce}")
                lignes += [f"   {'✔' if c.est_correct else '·'} {c.texte}" for c in q.choix]
            self.apercu.insert("1.0", "\n".join(lignes))
        self.apercu.config(state="disabled")
        self.bouton_enregistrer.config(state="normal" if self.quizz else "disabled")

    def enregistrer(self):
        self.quizz.id_createur = self.liste.app.user.id_utilisateur
        qs.enregistrer_quizz(self.con, self.quizz)
        self.liste.rafraichir()
        self.liste.info(f"Quizz « {self.quizz.titre} » généré par l'IA et enregistré.")
        self.destroy()


def lancer(con):
    try:  # Windows : texte net sur les écrans à haute résolution au lieu d'une image floue
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass  # autre système, ou ancienne version de Windows
    Application(con).mainloop()
