"""Point d'entrée : python main.py          (console)
                 python main.py --gui    (interface graphique, bonus)
"""
import sys

from quizz import auth
from quizz.database import connexion


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # accents et symboles sur toutes les consoles Windows
    con = connexion()
    auth.creer_admin_par_defaut(con)
    try:
        if "--gui" in sys.argv:
            from quizz.ui import gui
            gui.lancer(con)
        else:
            from quizz.ui import cli
            cli.lancer(con)
    except (KeyboardInterrupt, EOFError):
        print("\nAu revoir !")
    finally:
        con.close()


if __name__ == "__main__":
    main()
