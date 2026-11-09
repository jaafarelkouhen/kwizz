# Scénario de la démonstration — 15 minutes

**Objectif :** montrer que le cahier des charges est rempli, puis les bonus, et enfin la gestion de
projet (60 % de la note). Chacun présente **sa** partie : c'est aussi une preuve de contribution.

## Préparation (la veille et 15 min avant)
```bash
git clone https://github.com/jaafarelkouhen/kwizz.git demo && cd demo
python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt
python -m pytest                       # tout doit passer
python outils/preparer_demo.py         # 3 quizz, 3 joueurs, des parties déjà jouées
```
- ☐ Fichier `.env` avec la clé API (test d'une génération la veille) **et** plan B prêt (voir plus bas).
- ☐ Le fichier `data/exemples/capitales.json` est prêt pour la démonstration de l'import JSON.
- ☐ Navigateur ouvert sur deux onglets : GitHub (dépôt) et Trello.
- ☐ Police de la console agrandie (Ctrl + molette), écran en mode « dupliquer ».
- ☐ Répétition chronométrée faite (carte T71).

## Déroulé
| Min. | Qui | Ce qu'on montre | Ce qu'on dit (idée clé) |
|------|-----|-----------------|-------------------------|
| 0:00 | Jaafar | logo, équipe, rôles | « Kwizz : application de quizz, 4 rôles, SCRUM en 7 sprints. » |
| 1:00 | Akram | `python main.py` → connexion `admin` / `admin` → changement de mot de passe obligatoire, saisie masquée | sécurité : hachage salé, mot de passe par défaut interdit (US14, US15) |
| 2:30 | Sami | admin › Importer `capitales.json` · Créer un quizz de 1 question avec minuterie · Modifier son titre | les 3 façons de créer un quizz ; formats documentés ; validation commune (US03, US06, US08, US10) |
| 5:00 | Nour | se connecter `alice` / `demo` → 💡 recommandation → jouer « Capitales d'Europe » en ordre aléatoire avec 1 erreur → corrigé ✔/✘ → historique → classement 🥇 | le cœur du sujet : score, bonnes réponses, historique (US04, US05, US07, US12, US13, US18) |
| 7:30 | Nour | `python main.py --gui` : même parcours, minuterie en direct | même logique que la console, zéro SQL dans l'interface (US11) |
| 9:00 | Sami | GUI admin › 🤖 Générer un quizz « les volcans », 5 questions → relecture → enregistrer · en joueur : « Pourquoi ? » sur une erreur | IA optionnelle, relecture obligatoire, format JSON imposé (US16, US17) |
| 11:00 | Akram | `.env` avec `KWIZZ_IA=non` → relancer : les boutons IA ont disparu, tout marche | mode hors-ligne (US19) ; la clé n'est jamais sur GitHub |
| 12:00 | Jaafar | Trello (colonnes, cartes avec estimation) → GitHub (PR relues, tags `v1.0-mvp` et `v2.0-final`) → `docs/gestion/` (Gantt, PERT et chemin critique) | la gestion de projet en 3 preuves : planification, suivi, traçabilité |
| 14:00 | Jaafar | `python -m pytest` → tous verts | qualité : tests à chaque PR ; questions ? |

## Plan B (pas d'Internet ou IA en panne)
- Passer directement à la minute 11:00 : « voici ce qui se passe sans IA ». C'est une fonctionnalité,
  pas un échec.
- Montrer les tests IA (`python -m pytest tests/test_ui_ia.py -v`) : ils prouvent le fonctionnement
  avec une fausse IA.

## Questions probables du jury (et qui répond)
| Question | Qui | Éléments de réponse |
|----------|-----|---------------------|
| Pourquoi SQLite ? | Akram | inclus dans Python, pas de serveur, vraies contraintes ; rapport D.2 |
| Comment sont stockés les mots de passe ? | Akram | PBKDF2 + sel, jamais en clair ; rapport D.3 |
| Que se passe-t-il si l'IA invente une fausse réponse ? | Sami | relecture obligatoire, modifiable, marqué 🤖 ; rapport D.7 |
| Comment avez-vous testé l'interface ? | Nour | saisies simulées, fenêtre cachée, fausse IA ; rapport D.6 |
| Quel a été le chemin critique ? Avez-vous eu du retard ? | Jaafar | PERT : données → moteur → console → IA ; écarts dans les CR |
| Comment avez-vous réparti le travail ? | Jaafar | un module par personne, Trello, commits par auteur |
