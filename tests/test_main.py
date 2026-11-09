"""Tests du point d'entrée main.py."""
import sqlite3
import sys

import main


def test_lancement_sans_console(monkeypatch):
    """pythonw (double-clic) n'a pas de console : sys.stdout vaut None et main() ne doit pas planter."""
    lancee = []
    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(sys, "argv", ["main.py", "--gui"])
    monkeypatch.setattr(main, "connexion", lambda: sqlite3.connect(":memory:"))
    monkeypatch.setattr(main.auth, "creer_admin_par_defaut", lambda con: None)
    import quizz.ui.gui as gui
    monkeypatch.setattr(gui, "lancer", lambda con: lancee.append(con))

    main.main()

    assert len(lancee) == 1
