"""Point d'accès UNIQUE à l'API Claude (US19 : tout est optionnel).

Les autres modules IA n'appellent jamais le SDK directement : ils passent par demander_texte()
ou demander_json(). Les tests remplacent ces fonctions par une fausse IA, donc ils
n'utilisent ni le réseau ni la clé. Comme les autres services, ce module ne fait aucun print().
"""
import json

try:
    import anthropic
except ImportError:  # SDK non installé : l'IA est simplement indisponible
    anthropic = None

from ..config import config_ia

DELAI_MAX = 60  # secondes avant d'abandonner un appel
# Repli automatique si le modèle refuse une demande (option « fallbacks » de l'API).
# Seuls certains modèles le proposent ; pour les autres, on n'envoie pas l'option.
BETA_REPLI = "server-side-fallback-2026-07-01"
MODELES_AVEC_REPLI = {"claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5", "claude-fable-5-1"}


class ErreurIA(Exception):
    """L'IA n'a pas pu répondre. Le message est lisible par l'utilisateur."""


def ia_disponible() -> bool:
    return anthropic is not None and config_ia().activee


_client = None


def _obtenir_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(timeout=DELAI_MAX, max_retries=1)
    return _client


def _appeler(systeme: str, prompt: str, max_tokens: int, effort: str, format_sortie: dict | None = None) -> str:
    if not ia_disponible():
        raise ErreurIA("L'assistant IA n'est pas configuré (voir le fichier .env.example).")
    modele = config_ia().modele
    output_config = {"effort": effort}
    if format_sortie:
        output_config["format"] = format_sortie
    options = {"betas": [BETA_REPLI], "fallbacks": "default"} if modele in MODELES_AVEC_REPLI else {}
    try:
        reponse = _obtenir_client().beta.messages.create(
            model=modele,
            max_tokens=max_tokens,
            system=systeme,
            messages=[{"role": "user", "content": prompt}],
            output_config=output_config,
            **options,
        )
    # du plus précis au plus général : chaque cas a un message utile pour l'utilisateur
    except anthropic.AuthenticationError:
        raise ErreurIA("Clé API refusée : vérifiez ANTHROPIC_API_KEY dans le fichier .env.") from None
    except anthropic.PermissionDeniedError:
        raise ErreurIA("Cette clé API n'a pas accès à ce modèle (KWIZZ_MODELE).") from None
    except anthropic.RateLimitError:
        raise ErreurIA("Trop de demandes envoyées à l'IA : réessayez dans une minute.") from None
    except anthropic.APITimeoutError:
        raise ErreurIA("L'IA met trop de temps à répondre : réessayez.") from None
    except anthropic.APIConnectionError:
        raise ErreurIA("Impossible de joindre l'IA : vérifiez la connexion Internet.") from None
    except anthropic.APIStatusError as e:
        raise ErreurIA(f"Le service IA a renvoyé une erreur ({e.status_code}) : réessayez plus tard.") from None

    if reponse.stop_reason == "refusal":
        raise ErreurIA("L'IA a refusé cette demande. Reformulez le thème ou le texte.")
    if reponse.stop_reason == "max_tokens":
        raise ErreurIA("La réponse de l'IA était trop longue : demandez moins de questions.")
    texte = "".join(b.text for b in reponse.content if b.type == "text").strip()
    if not texte:
        raise ErreurIA("L'IA n'a rien répondu : réessayez.")
    return texte


def demander_texte(systeme: str, prompt: str, max_tokens: int = 4000, effort: str = "low") -> str:
    """Réponse libre en texte (ex. une explication)."""
    return _appeler(systeme, prompt, max_tokens, effort)


def demander_json(systeme: str, prompt: str, schema: dict, max_tokens: int = 16000,
                  effort: str = "medium") -> dict:
    """Réponse JSON conforme au schéma imposé (structured outputs)."""
    texte = _appeler(systeme, prompt, max_tokens, effort, {"type": "json_schema", "schema": schema})
    try:
        return json.loads(texte)
    except json.JSONDecodeError:
        raise ErreurIA("La réponse de l'IA est illisible (JSON invalide) : réessayez.") from None
