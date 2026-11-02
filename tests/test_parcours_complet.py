"""Test de bout en bout : on rejoue toute une démo dans la console, du premier lancement au classement.

Si ce test passe, le scénario de la démo fonctionne. Il protège contre les régressions
quand on modifie un écran.
"""
from pathlib import Path

from quizz import auth, quiz_service as qs
from quizz.ui import cli

EXEMPLE = Path(__file__).resolve().parent.parent / "data" / "exemples" / "capitales.txt"


def test_demo_complete(con, monkeypatch, capsys):
    auth.creer_admin_par_defaut(con)
    saisies = [
        # --- l'admin se connecte, change son mot de passe et importe un quizz
        "1", "admin", "admin", "Secret42", "Secret42",
        "5", str(EXEMPLE),                        # Importer (texte ou JSON)
        "9",                                      # Se déconnecter (menu admin : 8 actions + 1)
        # --- un joueur crée son compte et joue
        "2", "alice", "mdp1", "mdp1",
        "1", "1", "n",                            # Passer un quizz → n°1 → ordre normal
        "2", "1", "3",                            # Rome ✔, Lisbonne ✔, Varsovie ✔
        "",                                       # pause après le score
        "2", "",                                  # Mon historique
        "3", "1", "",                             # Classement du quizz n°1
        "4",                                      # Se déconnecter
        "3",                                      # Quitter
    ]
    reponses = iter(saisies)
    lire = lambda _message="": next(reponses)
    monkeypatch.setattr("builtins.input", lire)
    monkeypatch.setattr(cli.getpass, "getpass", lire)

    cli.lancer(con)

    sortie = capsys.readouterr().out
    assert "importé (3 questions)" in sortie
    assert "Score : 3/3" in sortie
    assert "alice" in sortie and "🥇" in sortie
    assert "À bientôt" in sortie
    alice = auth.connecter(con, "alice", "mdp1")
    assert [t.score for t in qs.historique(con, alice.id_utilisateur)] == [3]
