"""Prépare une base de démonstration : python outils/preparer_demo.py

Crée quizz.db avec les quizz d'exemple, trois joueurs (alice, bob, chloe — mot de passe « demo »)
et quelques parties, pour que l'historique, le classement et la recommandation aient du contenu.
Le compte admin garde le mot de passe par défaut (admin / admin), pour montrer qu'il faut le changer
à la première connexion (US15).

Une base existante n'est jamais écrasée sans --ecraser ; elle est alors sauvegardée en quizz.db.bak.
"""
import argparse
import shutil
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from quizz import auth, importer, quiz_service as qs  # noqa: E402
from quizz.database import CHEMIN_PAR_DEFAUT, connexion  # noqa: E402

JOUEURS = ["alice", "bob", "chloe"]
# (joueur, titre du quizz, nombre de bonnes réponses)
PARTIES = [("alice", "Capitales d'Europe", 3), ("bob", "Capitales d'Europe", 1),
           ("chloe", "Capitales d'Europe", 2), ("alice", "Gestion de projet", 6),
           ("bob", "Gestion de projet", 7), ("bob", "Les bases de Python", 2)]


def preparer(chemin: Path) -> dict:
    con = connexion(chemin)
    auth.creer_admin_par_defaut(con)
    admin = con.execute("SELECT id_utilisateur FROM utilisateur WHERE login = 'admin'").fetchone()[0]
    for fichier in sorted((RACINE / "data" / "exemples").glob("*.txt")):
        quizz = importer.lire_quizz(fichier)
        quizz.id_createur = admin
        qs.enregistrer_quizz(con, quizz)
    joueurs = {login: auth.inscrire(con, login, "demo") for login in JOUEURS}
    par_titre = {q.titre: qs.charger_quizz(con, q.id_quizz) for q in qs.lister_quizz(con)}
    for login, titre, justes in PARTIES:
        quizz = par_titre[titre]
        reponses = {q.id_question: {q.bonnes_reponses()[0].id_choix} for q in quizz.questions[:justes]}
        qs.enregistrer_tentative(con, joueurs[login].id_utilisateur, quizz, reponses, duree_secondes=40)
    bilan = {"quizz": len(par_titre), "joueurs": len(joueurs), "parties": len(PARTIES)}
    con.close()
    return bilan


def main(argv=None):
    parser = argparse.ArgumentParser(description="Prépare une base de démonstration Kwizz.")
    parser.add_argument("--ecraser", action="store_true", help="remplacer la base existante (sauvegardée en .bak)")
    parser.add_argument("--base", type=Path, default=CHEMIN_PAR_DEFAUT, help="chemin de la base à créer")
    args = parser.parse_args(argv)
    if args.base.exists():
        if not args.ecraser:
            print(f"{args.base} existe déjà. Relancez avec --ecraser (une sauvegarde .bak sera faite).")
            return 1
        shutil.copy2(args.base, args.base.with_suffix(".db.bak"))
        args.base.unlink()
    bilan = preparer(args.base)
    print(f"Base de démo prête : {bilan['quizz']} quizz, {bilan['joueurs']} joueurs, {bilan['parties']} parties.")
    print("Comptes : admin / admin (changement obligatoire) · alice, bob, chloe / demo")
    return 0


if __name__ == "__main__":
    sys.exit(main())
