"""Interface graphique Tkinter (bonus, US11).

TODO (équipe) : reproduire les écrans de cli.py (connexion, liste des quizz, jeu,
correction, historique) en appelant les MÊMES fonctions de auth / quiz_service.
"""
import tkinter as tk


def lancer(con):
    fenetre = tk.Tk()
    fenetre.title("Kwizz")
    fenetre.geometry("480x320")
    tk.Label(fenetre, text="Interface graphique à venir (US11)", font=("Segoe UI", 14)).pack(expand=True)
    fenetre.mainloop()
