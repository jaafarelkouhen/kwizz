# Charte d'équipe — Kwizz & Co

Validée par : ☐ Jaafar ☐ Akram ☐ Sami ☐ Nour, le …/…/2026

## 1. Rôles
| Membre | Rôle | Modules / livrables |
|--------|------|---------------------|
| Jaafar EL KOUHEN | Product Owner | relation avec le commanditaire, Trello, comptes-rendus, plannings, intégration (`main.py`), rapport |
| Akram AISSA | Dev « Données » | MCD/MLD, `models.py`, `database.py`, `auth.py`, recommandation |
| Sami LAARFI | Dev « Moteur Quizz » | `quiz_service.py`, `importer.py`, services IA (`quizz/ia/`) |
| Nour El Oula HARRAG | Dev « Interface & Qualité » | `ui/` (console + graphique), `tests/`, README |

Chacun est **propriétaire** de ses fichiers : pour modifier le fichier d'un autre, on le prévient d'abord
sur le canal.

## 2. Communication
- Canal d'équipe : … (Discord / Teams / WhatsApp). Un fil par module + un fil « général ».
- On répond aux messages **sous 24 h** pendant la semaine.
- Un blocage se signale **tout de suite**, sans attendre la séance suivante.
- Toute décision importante est notée dans le compte-rendu de séance.

## 3. Organisation des séances (rituels SCRUM simplifiés)
| Moment | Durée | Contenu |
|--------|-------|---------|
| Début de séance | 5 min | *daily* : ce que j'ai fait, ce que je fais, ce qui me bloque |
| Pendant | — | travail sur les cartes du sprint ; les cartes avancent dans Trello |
| Fin de séance | 10 min | réunion : avancement, difficultés ; le PO rédige le compte-rendu |
| Fin de sprint | 10 min | rétrospective : garder / arrêter / essayer |

## 4. Trello
- Une carte = une tâche de 6 h maximum, avec un responsable, une estimation et un critère de fin.
- On déplace sa carte : liste perso → 🔨 En cours → 👀 En revue → ✅ Terminé.
- On note le **temps réel** passé dans le commentaire de la carte quand elle est terminée.

## 5. Git et GitHub
- **Personne ne pousse directement sur `main`.** Une branche par carte :
  `feature/…` (code), `docs/…` (documentation), `fix/…` (correction).
- Messages de commit : `feat:` nouvelle fonctionnalité · `fix:` correction · `docs:` documentation ·
  `test:` tests · `refactor:` réorganisation sans changer le comportement.
- On commite **dès qu'une petite étape marche**, pas une seule fois en fin de séance.
- Chaque Pull Request est **relue par un autre membre** avant la fusion. Le PO fusionne.
- Avant d'ouvrir une PR : `python -m pytest` doit passer.
- À la fin de chaque séance, `main` doit fonctionner (`python main.py` sans erreur).
- On ne commite jamais : `quizz.db`, `.venv/`, `__pycache__/`, `.env` (clé API).

## 6. Qualité du code
- `ui/` n'écrit jamais de SQL ; `auth`, `quiz_service`, `importer` et `ia/` ne font jamais de
  `print()` ni d'`input()`.
- Toute nouvelle fonction de service a au moins un test.
- Les noms de variables et les messages sont en français, comme dans le reste du code.

## 7. Absences et conflits
- Une absence se prévient **avant** la séance, sur le canal et au PO. Le travail prévu est réparti ou
  décalé, et c'est noté dans le compte-rendu.
- Un désaccord technique se règle en 10 min maximum ; sinon le PO tranche ou on demande l'avis de
  l'enseignant.
- Un problème relationnel se règle d'abord en discutant à deux, puis avec le PO.

## 8. Évaluation par les pairs
On répartira les points selon l'implication réelle, en s'appuyant sur des faits : cartes Trello
terminées, commits, présence. D'où l'importance de tenir Trello et Git à jour.
