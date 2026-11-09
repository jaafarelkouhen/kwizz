"""Tests du script de préparation de la démo."""
import sys
from pathlib import Path

from quizz import auth, quiz_service as qs
from quizz.database import connexion

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "outils"))
import preparer_demo  # noqa: E402


def test_base_de_demo_complete(tmp_path):
    base = tmp_path / "demo.db"
    assert preparer_demo.main(["--base", str(base)]) == 0

    con = connexion(base)
    assert len(qs.lister_quizz(con)) == 3
    admin = auth.connecter(con, "admin", "admin")
    assert auth.utilise_mot_de_passe_par_defaut(con, admin)          # pour montrer US15
    capitales = next(q for q in qs.lister_quizz(con) if q.titre == "Capitales d'Europe")
    assert qs.classement(con, capitales.id_quizz)[0] == ("alice", 3)
    con.close()


def test_ne_jamais_ecraser_sans_le_demander(tmp_path):
    base = tmp_path / "demo.db"
    base.write_bytes(b"donnees importantes")
    assert preparer_demo.main(["--base", str(base)]) == 1
    assert base.read_bytes() == b"donnees importantes"

    assert preparer_demo.main(["--base", str(base), "--ecraser"]) == 0
    assert base.with_suffix(".db.bak").read_bytes() == b"donnees importantes"
