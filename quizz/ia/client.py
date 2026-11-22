"""Point d'accès UNIQUE à l'IA (US19 : tout est optionnel) : Claude, ou Groq (gratuit) à défaut.

Claude est utilisé si sa clé est là ; sinon Groq si GROQ_API_KEY est remplie ; sinon pas d'IA.
Groq parle le format d'OpenAI : un simple appel HTTP avec urllib suffit, sans dépendance en plus.

Les autres modules IA n'appellent jamais le SDK directement : ils passent par demander_texte()
ou demander_json(). Les tests remplacent ces fonctions par une fausse IA, donc ils
n'utilisent ni le réseau ni la clé. Comme les autres services, ce module ne fait aucun print().
"""
import json
import urllib.error
import urllib.request

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


URL_GROQ = "https://api.groq.com/openai/v1/chat/completions"


def fournisseur() -> str | None:
    """« claude », « groq » ou None (pas d'IA)."""
    cfg = config_ia()
    if anthropic is not None and cfg.activee:
        return "claude"
    return "groq" if cfg.groq_cle else None


def ia_disponible() -> bool:
    return fournisseur() is not None


_client = None


def _obtenir_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(timeout=DELAI_MAX, max_retries=1)
    return _client


def _appeler(systeme: str | list, prompt: str, max_tokens: int, effort: str, format_sortie: dict | None = None,
             messages: list[dict] | None = None) -> str:
    qui = fournisseur()
    if qui is None:
        raise ErreurIA("L'assistant IA n'est pas configuré (voir le fichier .env.example).")
    if qui == "groq":
        return _appeler_groq(systeme, messages or [{"role": "user", "content": prompt}], max_tokens, format_sortie)
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
            messages=messages or [{"role": "user", "content": prompt}],
            output_config=output_config,
            **options,
        )
    # du plus précis au plus général : chaque cas a un message utile pour l'utilisateur
    except anthropic.AuthenticationError:
        raise ErreurIA("Clé API refusée : vérifie ANTHROPIC_API_KEY dans le fichier .env.") from None
    except anthropic.PermissionDeniedError:
        raise ErreurIA("Cette clé API n'a pas accès à ce modèle (KWIZZ_MODELE).") from None
    except anthropic.RateLimitError:
        raise ErreurIA("Trop de demandes envoyées à l'IA : réessaie dans une minute.") from None
    except anthropic.APITimeoutError:
        raise ErreurIA("L'IA met trop de temps à répondre : réessaie.") from None
    except anthropic.APIConnectionError:
        raise ErreurIA("Impossible de joindre l'IA : vérifie la connexion Internet.") from None
    except anthropic.APIStatusError as e:
        raise ErreurIA(f"Le service IA a renvoyé une erreur ({e.status_code}) : réessaie plus tard.") from None

    if reponse.stop_reason == "refusal":
        raise ErreurIA("L'IA a refusé cette demande. Reformule le thème ou le texte.")
    if reponse.stop_reason == "max_tokens":
        raise ErreurIA("La réponse de l'IA était trop longue : demande moins de questions.")
    texte = "".join(b.text for b in reponse.content if b.type == "text").strip()
    if not texte:
        raise ErreurIA("L'IA n'a rien répondu : réessaie.")
    return texte


def _appeler_groq(systeme: str | list, messages: list[dict], max_tokens: int, format_sortie: dict | None) -> str:
    cfg = config_ia()
    # les blocs « système » de Claude (avec cache_control) deviennent un seul texte
    texte_systeme = systeme if isinstance(systeme, str) else "\n\n".join(b["text"] for b in systeme)
    corps = {"model": cfg.groq_modele, "max_tokens": min(max_tokens, 8000), "messages": []}
    if format_sortie:  # Groq ne vérifie pas le schéma : on le donne au modèle, et l'appelant valide le JSON
        texte_systeme += ("\n\nRéponds uniquement par un objet JSON valide qui respecte ce schéma JSON :\n"
                          + json.dumps(format_sortie["schema"], ensure_ascii=False))
        corps["response_format"] = {"type": "json_object"}
    corps["messages"] = [{"role": "system", "content": texte_systeme}, *messages]
    requete = urllib.request.Request(URL_GROQ, data=json.dumps(corps).encode(), method="POST", headers={
        "Authorization": f"Bearer {cfg.groq_cle}", "Content-Type": "application/json", "User-Agent": "MyKwizz/2.2"})
    try:
        with urllib.request.urlopen(requete, timeout=DELAI_MAX) as r:
            donnees = json.load(r)
    except urllib.error.HTTPError as e:
        messages_erreur = {401: "Clé Groq refusée : vérifie GROQ_API_KEY dans le fichier .env.",
                           404: "Modèle Groq inconnu : vérifie KWIZZ_GROQ_MODELE.",
                           429: "Quota gratuit de Groq atteint : réessaie dans une minute."}
        raise ErreurIA(messages_erreur.get(e.code, f"Le service Groq a renvoyé une erreur ({e.code}) : "
                                                    "réessaie plus tard.")) from None
    except TimeoutError:
        raise ErreurIA("L'IA met trop de temps à répondre : réessaie.") from None
    except urllib.error.URLError:
        raise ErreurIA("Impossible de joindre l'IA : vérifie la connexion Internet.") from None
    except json.JSONDecodeError:
        raise ErreurIA("Réponse illisible du service Groq : réessaie.") from None
    try:
        choix = donnees["choices"][0]
        texte = (choix["message"].get("content") or "").strip()
    except (KeyError, IndexError, TypeError, AttributeError):
        raise ErreurIA("Réponse inattendue du service Groq : réessaie.") from None
    if choix.get("finish_reason") == "length":
        raise ErreurIA("La réponse de l'IA était trop longue : demande moins de questions.")
    if not texte:
        raise ErreurIA("L'IA n'a rien répondu : réessaie.")
    return texte


def demander_texte(systeme: str, prompt: str, max_tokens: int = 4000, effort: str = "low") -> str:
    """Réponse libre en texte (ex. une explication)."""
    return _appeler(systeme, prompt, max_tokens, effort)


def demander_conversation(systeme: list[dict], messages: list[dict], max_tokens: int = 2000,
                          effort: str = "low") -> str:
    """Conversation à plusieurs tours ; `systeme` en blocs pour pouvoir mettre une partie en cache."""
    return _appeler(systeme, "", max_tokens, effort, messages=messages)


def demander_json(systeme: str, prompt: str, schema: dict, max_tokens: int = 16000,
                  effort: str = "medium") -> dict:
    """Réponse JSON conforme au schéma imposé (structured outputs)."""
    texte = _appeler(systeme, prompt, max_tokens, effort, {"type": "json_schema", "schema": schema})
    try:
        return json.loads(texte)
    except json.JSONDecodeError:
        raise ErreurIA("La réponse de l'IA est illisible (JSON invalide) : réessaie.") from None
