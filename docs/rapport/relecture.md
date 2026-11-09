# Grille de relecture du rapport (critère F)

**Relectrice :** Nour El Oula HARRAG · **Date :** …/…/2026

Le critère F du sujet porte sur la hiérarchisation, l'enchaînement logique, l'orthographe, la clarté et
la concision. Coche chaque ligne ; une ligne non cochée devient une remarque pour son auteur.

## 1. Contenu exigé par le sujet
- ☐ A. Objectifs : compréhension du sujet et des objectifs
- ☐ B. Gestion : organisation, ressources, planification, processus, amélioration continue, suivi, outils
- ☐ C. Autonomie : auto-formation, appels aux enseignants, initiatives, cohésion, difficultés
- ☐ D. Réalisation technique : architecture, conception, modularité, choix justifiés, validation
- ☐ E. Bilan : résultats, critique, difficultés, perspectives, documentation
- ☐ Les livrables sont référencés : Gantt/PERT, PBS, WBS, sprints, MCD, dépôt GitHub, comptes-rendus

## 2. Vérité des faits (le prof compare avec Trello et GitHub)
- ☐ Plus aucun `[…]` ni `…` à compléter
- ☐ Les temps réels viennent des cartes Trello et des comptes-rendus
- ☐ Les nombres sont à jour : nombre de tests (`python -m pytest`), nombre de commits, de PR
- ☐ Les difficultés décrites ont vraiment eu lieu, et sont datées

## 3. Forme
- ☐ Sommaire et titres numérotés (A, B, B.1…) cohérents
- ☐ Chaque figure ou tableau est cité dans le texte (« voir figure 2 »)
- ☐ Les diagrammes Mermaid sont exportés en image (mermaid.live › PNG) pour la version PDF
- ☐ Orthographe : relecture avec un correcteur (LanguageTool, Antidote ou Word)
- ☐ Termes cohérents avec le [glossaire](../glossaire.md) (« quizz », « tentative »…)
- ☐ Ni phrase de plus de 3 lignes, ni paragraphe de plus de 8 lignes
- ☐ Ni « je » ni « on » familier : « nous » ou formulation neutre

## 4. Export PDF
1. Ouvrir `rapport.md` dans VS Code avec l'extension « Markdown PDF » (ou coller le texte dans Word ou
   Google Docs).
2. Remplacer chaque bloc Mermaid par son image PNG.
3. Ajouter une page de garde : titre, équipe, logo, date, PROJ531.
4. Enregistrer sous `docs/rapport/rapport.pdf`, puis commiter.
