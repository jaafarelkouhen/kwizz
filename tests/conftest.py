import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from quizz.database import connexion  # noqa: E402


@pytest.fixture
def con():
    """Base SQLite en mémoire, neuve pour chaque test."""
    c = connexion(":memory:")
    yield c
    c.close()


@pytest.fixture(autouse=True)
def ia_desactivee_par_defaut(monkeypatch):
    """Les tests ne lisent jamais le vrai .env et n'appellent jamais la vraie IA.

    Un test qui a besoin de l'IA l'active lui-même (variables d'environnement + fausse IA).
    """
    from quizz import config
    monkeypatch.setattr(config, "charger_env", lambda *a, **k: None)
    monkeypatch.setenv("KWIZZ_IA", "non")


@pytest.fixture(scope="session")
def fenetre():
    """UNE seule fenêtre Tk pour toute la session de tests (fenêtre cachée).

    Sous Windows, recréer Tk() plusieurs fois dans le même processus échoue parfois
    (« Can't find a usable tk.tcl ») : on la crée donc une fois et on la réutilise.
    """
    import tkinter as tk
    from quizz.ui import gui
    try:
        application = gui.Application(None)
    except tk.TclError as e:
        pytest.skip(f"pas d'affichage graphique disponible ({e})")
    application.withdraw()
    yield application
    application.destroy()
