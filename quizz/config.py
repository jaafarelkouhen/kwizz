"""Configuration lue dans l'environnement ou dans le fichier .env (jamais versionné sur GitHub).

Variables :
    ANTHROPIC_API_KEY  clé de l'API Claude (secrète)
    KWIZZ_IA           auto (défaut : IA active si une clé est présente) · oui (forcer) · non (désactiver)
    KWIZZ_MODELE       modèle Claude à utiliser (défaut : MODELE_PAR_DEFAUT)
"""
import os
from dataclasses import dataclass
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
MODELE_PAR_DEFAUT = "claude-opus-5-5"


@dataclass(frozen=True)
class ConfigIA:
    activee: bool
    cle_presente: bool
    modele: str


def charger_env(chemin: Path = RACINE / ".env") -> None:
    """Charge .env s'il existe. Une variable déjà définie dans le système n'est pas écrasée."""
    try:
        from dotenv import load_dotenv
    except ImportError:  # python-dotenv absent : on se contente des variables du système
        return
    load_dotenv(chemin, override=False)


def config_ia() -> ConfigIA:
    charger_env()
    reglage = os.environ.get("KWIZZ_IA", "auto").strip().lower()
    cle = bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())
    # « oui » sert quand l'accès passe par un profil (ant auth login) plutôt que par une clé
    activee = reglage != "non" and (cle or reglage == "oui")
    modele = os.environ.get("KWIZZ_MODELE", "").strip() or MODELE_PAR_DEFAUT
    return ConfigIA(activee, cle, modele)
