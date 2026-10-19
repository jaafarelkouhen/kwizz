"""Objets métier de l'application (correspondent aux entités du MCD)."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Utilisateur:
    id_utilisateur: Optional[int]
    login: str
    est_admin: bool = False
    date_creation: Optional[str] = None


@dataclass
class Choix:
    texte: str
    est_correct: bool = False
    id_choix: Optional[int] = None


@dataclass
class Question:
    enonce: str
    choix: list[Choix] = field(default_factory=list)
    ordre: int = 0
    id_question: Optional[int] = None

    def bonnes_reponses(self) -> list[Choix]:
        return [c for c in self.choix if c.est_correct]


@dataclass
class Quizz:
    titre: str
    description: str = ""
    duree_limite: Optional[int] = None  # en secondes, None = pas de minuterie
    questions: list[Question] = field(default_factory=list)
    id_quizz: Optional[int] = None
    id_createur: Optional[int] = None


@dataclass
class Tentative:
    id_utilisateur: int
    id_quizz: int
    score: int
    nb_questions: int
    duree_secondes: Optional[int] = None
    date_passage: Optional[str] = None
    id_tentative: Optional[int] = None
    titre_quizz: str = ""  # rempli pour l'affichage de l'historique
