"""Récupération des passages utiles dans les fiches Markdown de quizz/rag/docs/.

Adapté de fast_markdown_retriever.py (market-risk-rag-chatbot) : découpage par titre « ## »,
mots normalisés (sans accents, sans mots vides), score = recouvrement pondéré par la rareté du mot.
shortcut: pas d'embeddings (sentence-transformers + Chroma = ~1 Go) ; passer à des embeddings si
les fiches dépassent quelques centaines de sections ou si les synonymes posent problème.
"""
import math
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

DOCS = Path(__file__).resolve().parent / "docs"
SECTION_RESSOURCES = "Ressources pour aller plus loin"
_MOT = re.compile(r"[a-z0-9]+")
_URL = re.compile(r"https?://\S+")
_VIDES = set("""au aux avec ce ces cette dans de des du elle en est et il ils la le les leur lui mais
ou par pas pour qu que qui sa se ses son sont sur ta te tes ton tu un une vos votre nous vous je moi
quel quelle quels quelles quoi comment pourquoi est-ce cest explique expliquer moi peux peut dire
donne donner sais savoir veux voudrais bien aussi tres plus fait faire etre avoir the and""".split())


def normaliser(texte: str) -> list[str]:
    texte = unicodedata.normalize("NFKD", texte.lower())
    texte = "".join(c for c in texte if not unicodedata.combining(c))
    mots = []
    for m in _MOT.findall(texte):
        if len(m) > 4 and not m.isdigit():  # racine grossière : chromosomes = chromosome, humaine = humain
            m = re.sub(r"(es|s|x|e)$", "", m)
        if (len(m) > 1 or m.isdigit()) and m not in _VIDES:
            mots.append(m)
    return mots


@dataclass(frozen=True)
class Passage:
    fiche: str      # nom du fichier, ex. « svt.md »
    titre: str      # titre de la fiche (« SVT (Sciences de la vie et de la Terre) »)
    section: str
    texte: str


@dataclass(frozen=True)
class Resultat:
    score: float
    passage: Passage


@lru_cache(maxsize=1)
def charger() -> tuple[tuple[Passage, ...], dict[str, list[str]]]:
    """(passages, liens « Ressources » de chaque fiche)."""
    passages, liens = [], {}
    for chemin in sorted(DOCS.glob("*.md")):
        titre, section, tampon = chemin.stem, chemin.stem, []

        def vider():
            texte = "\n".join(tampon).strip()
            if texte and section != SECTION_RESSOURCES:
                passages.append(Passage(chemin.name, titre, section, texte))
            tampon.clear()

        for ligne in chemin.read_text(encoding="utf-8").splitlines():
            if ligne.startswith("# "):
                titre = ligne[2:].strip()
            elif ligne.startswith("## "):
                vider()
                section = ligne[3:].strip()
            elif section == SECTION_RESSOURCES:
                liens.setdefault(chemin.name, []).extend(_URL.findall(ligne))
                tampon.append(ligne)
            else:
                tampon.append(ligne)
        vider()
    return tuple(passages), liens


@lru_cache(maxsize=1)
def _index():
    passages, _ = charger()
    mots = [set(normaliser(f"{p.titre} {p.section} {p.texte}")) for p in passages]
    df: dict[str, int] = {}
    for m in mots:
        for mot in m:
            df[mot] = df.get(mot, 0) + 1
    n = len(passages)
    idf = {mot: math.log(1 + n / d) for mot, d in df.items()}
    return passages, mots, idf


def chercher(question: str, k: int = 3, score_min: float = 2.0, fiche: str | None = None) -> list[Resultat]:
    passages, mots, idf = _index()
    q = set(normaliser(question))
    if not q:
        return []
    resultats = []
    for p, m in zip(passages, mots):
        if fiche and p.fiche != fiche:
            continue
        communs = q & m
        score = sum(idf[x] for x in communs)
        score += 0.5 * sum(idf[x] for x in communs & set(normaliser(p.section)))  # bonus titre
        if score >= score_min:
            resultats.append(Resultat(round(score, 2), p))
    resultats.sort(key=lambda r: r.score, reverse=True)
    return resultats[:k]


def liens_de(fiche: str) -> list[str]:
    return charger()[1].get(fiche, [])
