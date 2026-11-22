"""Un tour de conversation de l'assistant : routeur → récupération → prompt → LLM → garde-fous.

Reprend les étapes de chat_turn / intent_router / prompt_builder / response_guardrails /
conversation_memory de market-risk-rag-chatbot, réduites à ce dont un quizz a besoin.
Aucun print() : le serveur appelle repondre() et renvoie le dict en JSON.
"""
import re

from ..ia import client
from . import retriever

MAX_QUESTION = 500          # caractères acceptés par question
MEMOIRE_TOURS = 3           # échanges précédents donnés au modèle
MAX_REPONSE = 1500          # caractères renvoyés au navigateur

_SALUTATIONS = {"bonjour", "salut", "coucou", "hello", "merci", "bonsoir", "hey", "ok", "cool", "super"}
_APP = {"quizz", "quiz", "score", "classement", "minuterie", "timer", "historique", "partie", "jouer",
        "connexion", "compte", "mykwizz", "assistant", "theme", "point"}

SYSTEME = """Tu es l'assistant pédagogique de MyKwizz, une application de quizz pour étudiants.
Tu as ci-dessous les fiches de cours de MyKwizz (toutes, ou les passages utiles à la question). Règles :
1. Tu réponds en français, en tutoyant, de façon claire et pédagogique : l'idée principale d'abord,
   puis le pourquoi, avec un exemple si ça aide. 8 phrases au maximum, sauf si l'élève demande plus.
2. Si les fiches contiennent la réponse, appuie-toi dessus en priorité et termine par
   (fiche : <titre de la fiche>).
3. Si les fiches ne la contiennent pas mais que c'est une question scolaire ou de culture générale,
   réponds avec tes connaissances, sans inventer, et termine par (réponse hors fiches).
   Si tu n'es pas sûr, dis-le.
4. N'écris aucun lien qui n'est pas dans les fiches ; propose plutôt une ressource de leurs sections
   « Ressources pour aller plus loin ».
5. Tiens compte de la conversation : « et pourquoi ? », « donne un exemple » portent sur le sujet précédent.
6. Si la question n'a rien à voir avec l'école, les sciences, la culture ou MyKwizz, refuse poliment
   en une phrase et propose un des thèmes : Culture générale, Code, Histoire, Mathématiques,
   Physique-Chimie, SVT, Géographie, Gestion de projet."""


def fiches_completes() -> str:
    """Toutes les fiches en un bloc : la base est assez petite pour tenir entière dans le contexte.

    shortcut: tout envoyer marche tant que les fiches restent sous ~100 000 tokens ; au-delà, revenir
    à l'envoi des seuls passages trouvés par retriever.chercher().
    """
    return "\n\n".join(f"<fiche nom=\"{f.name}\">\n{f.read_text(encoding='utf-8')}\n</fiche>"
                       for f in sorted(retriever.DOCS.glob("*.md")))


def passages_choisis(resultats: list) -> str:
    """Seulement les passages trouvés (et les ressources de leurs fiches) : pour Groq, dont l'offre gratuite
    limite une requête à environ 8 000 tokens par minute, trop peu pour envoyer toutes les fiches."""
    blocs = [f"<fiche nom=\"{r.passage.fiche}\">\n# {r.passage.titre}\n## {r.passage.section}\n"
             f"{r.passage.texte}\n</fiche>" for r in resultats]
    liens = list(dict.fromkeys(l for r in resultats for l in retriever.liens_de(r.passage.fiche)))
    if liens:
        blocs.append("Ressources pour aller plus loin :\n" + "\n".join(liens))
    return "\n\n".join(blocs) or "(aucun passage des fiches ne correspond à cette question)"


# ---------------------------------------------------------------- routeur d'intention
def router(question: str, enonces_en_cours: list[str]) -> str:
    """salutation | triche | aide_app | cours.

    shortcut: règles lexicales au lieu du classifieur à embeddings du dépôt d'origine ;
    suffisant pour 4 intentions, à remplacer si on en ajoute beaucoup.
    """
    mots = set(retriever.normaliser(question))
    brut = set(re.findall(r"[a-zà-ÿ]+", question.lower()))
    if brut and brut <= _SALUTATIONS | {"et", "toi", "ca", "va", "beaucoup"}:
        return "salutation"
    for enonce in enonces_en_cours:  # pendant une partie : pas de réponse aux questions du quizz
        e = set(retriever.normaliser(enonce))
        if e and len(mots & e) / len(e) >= 0.6:
            return "triche"
    if mots & _APP and not retriever.chercher(question, k=1, score_min=6.0):
        return "aide_app"
    return "cours"


# ---------------------------------------------------------------- garde-fous
def garde_fous(reponse: str, contexte: str) -> str:
    """Retire les liens inventés, coupe une réponse trop longue."""
    autorises = set(re.findall(r"https?://[^\s)\]]+", contexte))
    reponse = re.sub(r"https?://[^\s)\]]+",
                     lambda m: m.group(0) if m.group(0).rstrip(".,;") in autorises else "[lien retiré]", reponse)
    if len(reponse) > MAX_REPONSE:
        reponse = reponse[:MAX_REPONSE].rsplit(" ", 1)[0] + "…"
    return reponse.strip()


def _extrait(texte: str, question: str, phrases: int = 2) -> str:
    """Les phrases du passage qui partagent le plus de mots avec la question, dans leur ordre."""
    morceaux = re.split(r"(?<=[.!?])\s+", texte.strip())
    q = set(retriever.normaliser(question))
    rang = sorted(range(len(morceaux)), key=lambda i: -len(q & set(retriever.normaliser(morceaux[i]))))
    return " ".join(morceaux[i] for i in sorted(rang[:phrases]))


def _sources(resultats: list[retriever.Resultat]) -> list[dict]:
    vues, sources = set(), []
    for r in resultats:
        if r.passage.fiche not in vues:
            vues.add(r.passage.fiche)
            sources.append({"fiche": r.passage.titre, "section": r.passage.section,
                            "liens": retriever.liens_de(r.passage.fiche)})
    return sources


# ---------------------------------------------------------------- un tour complet
def repondre(question: str, historique: list[dict], enonces_en_cours: list[str] | None = None) -> dict:
    """Renvoie {"reponse", "sources", "intention", "mode"} ; mode = ia | fiches | regle."""
    question = " ".join(question.split())[:MAX_QUESTION]
    if not question:
        return {"reponse": "Pose-moi une question sur un des thèmes des quizz.", "sources": [],
                "intention": "vide", "mode": "regle"}
    intention = router(question, enonces_en_cours or [])
    if intention == "salutation":
        return {"reponse": "Bonjour ! Pose-moi une question de Culture générale, Code, Histoire, Mathématiques, "
                           "Physique-Chimie, SVT, Géographie ou Gestion de projet, ou demande-moi comment marche MyKwizz.",
                "sources": [], "intention": intention, "mode": "regle"}
    if intention == "triche":
        return {"reponse": "Cette question ressemble à celle de ta partie en cours : termine d'abord le quizz, "
                           "puis reviens me demander l'explication.",
                "sources": [], "intention": intention, "mode": "regle"}

    fiche = "fonctionnement.md" if intention == "aide_app" else None
    resultats = retriever.chercher(question, k=3, fiche=fiche)
    if not resultats and historique:  # question de suite (« et pourquoi ? ») : on cherche avec le contexte
        resultats = retriever.chercher(historique[-1]["question"] + " " + question, k=3)
    resultats = [r for r in resultats if r.score >= resultats[0].score / 2]  # pas de passage hors sujet

    if client.ia_disponible():
        fiches = passages_choisis(resultats) if client.fournisseur() == "groq" else fiches_completes()
        # le bloc des fiches ne change pas d'une question à l'autre : mis en cache (~10 fois moins cher)
        systeme = [{"type": "text", "text": SYSTEME},
                   {"type": "text", "text": fiches, "cache_control": {"type": "ephemeral"}}]
        messages = [m for tour in historique[-MEMOIRE_TOURS:] for m in
                    ({"role": "user", "content": tour["question"]}, {"role": "assistant", "content": tour["reponse"]})]
        messages.append({"role": "user", "content": question})
        try:
            texte = client.demander_conversation(systeme, messages)
            cite_une_fiche = "(fiche" in texte.lower()  # ni refus, ni « réponse hors fiches »
            return {"reponse": garde_fous(texte, fiches), "sources": _sources(resultats) if cite_une_fiche else [],
                    "intention": intention, "mode": "ia"}
        except client.ErreurIA:
            pass  # on retombe sur les fiches : l'élève a quand même une réponse

    if not resultats:
        return {"reponse": "Je n'ai rien trouvé à ce sujet dans les fiches. Essaie avec d'autres mots, "
                           "ou choisis un thème : Culture générale, Code, Histoire, Mathématiques, "
                           "Physique-Chimie, SVT.", "sources": [], "intention": intention, "mode": "fiches"}
    meilleur = resultats[0].passage
    texte = _extrait(" ".join(r.passage.texte for r in resultats), question, phrases=3)
    return {"reponse": f"D'après la fiche « {meilleur.titre} » ({meilleur.section}) : {texte}",
            "sources": _sources(resultats), "intention": intention, "mode": "fiches"}
