# Plan des sprints — Kwizz (Kwizz & Co)

> Planning de A à Z, une semaine = un sprint = une séance de TD.
> Les dates sont à caler sur l'emploi du temps réel (hypothèse : une séance par semaine à partir du 12/10/2026).
> Règle SCRUM du sujet : **aucune tâche ne dépasse 2 jours** (ici ≤ 6 h).

**Légende**
- **Resp.** : JK = Jaafar (PO) · AA = Akram (Données) · SL = Sami (Moteur) · NH = Nour (Interface & Qualité)
- **Est.** : temps estimé (à reporter dans Trello, puis noter le temps **réel** dans le compte-rendu)
- **Dép.** : tâche(s) à terminer avant
- **Fini quand** : critère de fin (Definition of Done)

**Tableau Trello :** https://trello.com/b/uNtICE5l/kwizz-co-kwizz-app — une liste par membre + `En cours` → `En revue` → `Terminé`. Les cartes sont préfixées par la séance (`S2 - T14 …` = séance 2, tâche T14).
**Étiquettes :** `Gestion` · `Données` · `Moteur` · `Interface` · `Tests` · `IA` · `Doc` · `Bonus`

**Definition of Done globale :** code commité sur une branche, revu par 1 autre membre, tests passants,
`python main.py` ne plante pas, carte Trello déplacée dans *Terminé* avec le temps réel.

---

## Sprint 0 — Semaine 1 (12/10) · Lancement *(TP1)*

Objectif : l'équipe, les outils et le périmètre sont en place.

| ID | Tâche | Resp. | Est. | Dép. | Fini quand |
|----|-------|-------|------|------|-----------|
| T01 | Créer le dépôt GitHub `jaafarelkouhen/kwizz` + inviter les 3 membres en écriture | JK | 0,5 h | — | les 3 ont accepté l'invitation ✅ |
| T02 | Créer le tableau Trello (colonnes + étiquettes ci-dessus), inviter l'équipe | JK | 1 h | — | les 4 membres sur le tableau |
| T03 | Créer le canal d'équipe (Discord/Teams/Slack) + règles de communication | JK | 0,5 h | — | canal actif, 1er message de chacun |
| T04 | Envoyer le mail au commanditaire avec liens GitHub + Trello | JK | 0,5 h | T01, T02 | mail envoyé (copie dans `docs/gestion/`) |
| T05 | Rédiger la charte d'équipe (rôles, horaires, règles de commit, branches) | JK | 1 h | — | `docs/gestion/charte-equipe.md` commité |
| T06 | Chacun installe Python 3.10+, Git, clone le dépôt, crée le venv | Tous | 1 h | T01 | `python -m pytest` lancé chez chacun |
| T07 | Rédiger le backlog produit (US01 → US19) avec priorités MoSCoW | JK | 2 h | — | `docs/gestion/backlog.md` + cartes Trello |
| T08 | Compte-rendu séance 1 | JK | 0,5 h | — | `docs/comptes-rendus/CR-01.md` commité |

---

## Sprint 1 — Semaine 2 (19/10) · Conception

Objectif : architecture et modèle de données validés, livrables de planification faits.

| ID | Tâche | Resp. | Est. | Dép. | Fini quand |
|----|-------|-------|------|------|-----------|
| T09 | PBS (arborescence des produits/livrables) | JK | 1,5 h | T07 | `docs/gestion/PBS.png` |
| T10 | WBS (découpage en lots de travaux, reprend les IDs de ce plan) | JK | 2 h | T09 | `docs/gestion/WBS.png` |
| T11 | Gantt prévisionnel (GanttProject ou Excel) | JK | 2 h | T10 | `docs/gestion/gantt-previsionnel.png` |
| T12 | PERT + chemin critique | JK | 1,5 h | T10 | `docs/gestion/PERT.png` + chemin critique noté |
| T13 | MCD entité-association (Utilisateur, Quizz, Question, Choix, Tentative, Réponse) | AA | 3 h | — | `docs/conception/MCD.png` validé par l'équipe |
| T14 | MLD / schéma SQL déduit du MCD | AA | 2 h | T13 | `docs/conception/schema.sql` |
| T15 | Diagramme d'architecture (modules + règle « ui n'écrit pas de SQL ») | SL | 1,5 h | — | `docs/conception/architecture.png` |
| T16 | Diagramme de cas d'utilisation (admin / joueur / IA) | NH | 1,5 h | T07 | `docs/conception/cas-utilisation.png` |
| T17 | Maquettes des écrans console + GUI (papier ou Figma) | NH | 2 h | T16 | `docs/conception/maquettes/` |
| T18 | Spécifier le format du fichier d'import texte + JSON | SL | 1 h | — | section dans README validée |
| T19 | Matrice des risques (dont risque IA : coût, panne réseau, clé API) | JK | 1 h | — | `docs/gestion/risques.md` |
| T20 | Glossaire du domaine (quizz, tentative, score, prompt, LLM…) | NH | 1 h | — | `docs/glossaire.md` complété |
| T21 | Compte-rendu séance 2 + mail d'avancement au prof | JK | 1 h | — | CR-02 commité, mail envoyé |

---

## Sprint 2 — Semaine 3 (26/10) · Socle (MVP partie 1)

Objectif : on peut créer un compte, se connecter, et la base existe.

| ID | Tâche | Resp. | Est. | Dép. | Fini quand |
|----|-------|-------|------|------|-----------|
| T22 | `models.py` : dataclasses Utilisateur, Quizz, Question, Choix, Tentative | AA | 2 h | T13 | importables, typées |
| T23 | `database.py` : connexion SQLite + création du schéma + admin par défaut | AA | 3 h | T14, T22 | `quizz.db` créée au 1er lancement |
| T24 | `auth.py` : inscription, connexion, hachage (hashlib + sel) — US01-02 | AA | 3 h | T23 | mot de passe jamais en clair |
| T25 | Tests `test_auth.py` (inscription doublon, mauvais mdp, admin) | NH | 2 h | T24 | tests verts |
| T26 | `ui/cli.py` : menu d'accueil (s'inscrire / se connecter / quitter) | NH | 3 h | T24 | navigation sans crash |
| T27 | `main.py` : point d'entrée, choix CLI/GUI (`--gui`) | JK | 1,5 h | T26 | `python main.py` lance le menu |
| T28 | `quiz_service.py` : créer un quizz + ajouter questions/choix — US03 | SL | 4 h | T23 | quizz enregistré en base |
| T29 | Mettre en place les branches (`feature/...`) + 1ʳᵉ pull request revue | JK | 1 h | — | règle appliquée par tous |
| T30 | Compte-rendu séance 3 (estimé vs réel) + mail prof | JK | 1 h | — | CR-03 commité |

---

## Sprint 3 — Semaine 4 (02/11) · MVP complet

Objectif : **le cahier des charges minimum est rempli** et démontrable.

| ID | Tâche | Resp. | Est. | Dép. | Fini quand |
|----|-------|-------|------|------|-----------|
| T31 | `quiz_service.py` : lister les quizz, passer un quizz, corriger — US04-05 | SL | 4 h | T28 | score + bonnes réponses renvoyés |
| T32 | Enregistrer les tentatives + historique des scores — US07 | AA | 3 h | T31 | historique par utilisateur en base |
| T33 | `importer.py` : import fichier texte + messages d'erreur clairs — US06 | SL | 4 h | T18, T28 | fichier exemple importé |
| T34 | Écrire 3 quizz d'exemple dans `data/exemples/` | SL | 1 h | T33 | 3 fichiers valides |
| T35 | CLI : menu admin (créer quizz à la main, importer un fichier) | NH | 3 h | T28, T33 | admin crée un quizz depuis la console |
| T36 | CLI : menu joueur (jouer, voir score + corrigé, historique) | NH | 3 h | T31, T32 | parcours joueur complet |
| T37 | Tests `test_quiz_service.py` + `test_importer.py` | NH | 3 h | T31, T33 | tests verts |
| T38 | Recette PO : tester le parcours complet comme le prof (clone propre) | JK | 1,5 h | T35, T36 | fiche de recette `docs/gestion/recette-v1.md` |
| T39 | Tag Git `v1.0-mvp` + mise à jour tableau d'avancement README | JK | 0,5 h | T38 | tag poussé |
| T40 | Rétrospective sprint + Gantt réel vs prévu | JK | 1 h | — | CR-04 avec section rétro |

---

## Sprint 4 — Semaine 5 (09/11) · Fonctionnalités avancées

Objectif : enrichir le produit (bonus du sujet).

| ID | Tâche | Resp. | Est. | Dép. | Fini quand |
|----|-------|-------|------|------|-----------|
| T41 | Modifier / supprimer un quizz — US08 | SL | 3 h | T31 | admin peut éditer/supprimer |
| T42 | Minuterie par quizz (`# DUREE:`) — US09 | SL | 3 h | T31 | quizz coupé à la fin du temps |
| T43 | Export / import JSON — US10 | SL | 3 h | T33 | aller-retour JSON sans perte |
| T44 | Classement (top scores par quizz) — US12 | AA | 2 h | T32 | requête + affichage |
| T45 | Questions et choix en ordre aléatoire — US13 | AA | 1,5 h | T31 | option activable |
| T46 | GUI (Tkinter) : fenêtre connexion + inscription — US11 | NH | 4 h | T24 | connexion via GUI |
| T47 | GUI : liste des quizz + écran de jeu + résultat | NH | 5 h | T46, T31 | partie complète en GUI |
| T48 | Tests minuterie, JSON, classement | NH | 2 h | T42-T44 | tests verts |
| T49 | Démarrer le rapport : plan + parties A (objectifs) et B (gestion) | JK | 3 h | — | `docs/rapport/rapport.md` brouillon |
| T50 | Compte-rendu séance 5 + mail prof | JK | 1 h | — | CR-05 commité |

---

## Sprint 5 — Semaine 6 (16/11) · IA interne « Kwizz AI »

Objectif : ajouter un assistant IA **optionnel** (l'appli marche sans clé ni réseau).

Fonctions IA retenues :
1. **Générer un quizz** à partir d'un thème ou d'un texte collé (admin) — US16
2. **Expliquer une mauvaise réponse** après correction (joueur) — US17
3. **Recommander** le prochain quizz selon l'historique (joueur) — US18
4. **Mode hors-ligne** : sans clé API, l'IA est désactivée proprement — US19

| ID | Tâche | Resp. | Est. | Dép. | Fini quand |
|----|-------|-------|------|------|-----------|
| T51 | Étude de solutions IA (API Claude vs modèle local Ollama) + choix justifié | JK | 2 h | — | `docs/conception/choix-ia.md` (coût, confidentialité, perf) |
| T52 | Config : clé API dans `.env` (jamais commitée), `python-dotenv` | AA | 1 h | T51 | `.env.example` + `.gitignore` à jour |
| T53 | `quizz/ai/client.py` : appel du modèle, timeout, gestion d'erreur, mode off | SL | 3 h | T52 | renvoie `None` proprement sans clé |
| T54 | `quizz/ai/generator.py` : prompt « génère N questions en JSON » + validation | SL | 4 h | T53, T43 | quizz IA réutilise l'import JSON |
| T55 | Marquer en base les quizz générés par IA (colonne `source`) | AA | 1,5 h | T54 | champ visible côté admin |
| T56 | `quizz/ai/explainer.py` : explication d'une réponse fausse | SL | 2 h | T53 | texte court en français |
| T57 | `quizz/ai/recommender.py` : recommandation (règles simples + IA si dispo) | AA | 2,5 h | T32 | marche même sans IA |
| T58 | CLI + GUI : bouton « Générer avec l'IA » (admin) avec relecture avant enregistrement | NH | 3 h | T54 | admin valide/édite avant sauvegarde |
| T59 | CLI + GUI : « Pourquoi ? » après correction + recommandation | NH | 3 h | T56, T57 | affichage sans crash hors-ligne |
| T60 | Tests IA avec **faux client** (mock) : JSON invalide, timeout, pas de clé | NH | 3 h | T53-T57 | tests verts sans réseau |
| T61 | Section rapport : éthique / limites de l'IA (hallucinations, relecture humaine, coût) | JK | 1,5 h | T51 | section rédigée |
| T62 | Compte-rendu séance 6 + mail prof | JK | 1 h | — | CR-06 commité |

---

## Sprint 6 — Semaine 7 (23/11) · Stabilisation, rapport, démo *(dernière séance)*

Objectif : version finale sans bug, rapport rendu, démo de 15 min prête.

| ID | Tâche | Resp. | Est. | Dép. | Fini quand |
|----|-------|-------|------|------|-----------|
| T63 | Gel des fonctionnalités (feature freeze) + liste des bugs dans Trello | JK | 0,5 h | — | plus aucune nouvelle US |
| T64 | Correction des bugs restants (chacun sur son module) | Tous | 3 h | T63 | 0 bug bloquant |
| T65 | README final (install, usage, IA, captures, format fichiers) | NH | 2 h | — | un inconnu installe seul |
| T66 | Rapport : partie D (réalisation technique, MCD, architecture) | AA + SL | 3 h | — | section rédigée |
| T67 | Rapport : parties C (autonomie, difficultés) et E (bilan, perspectives) | JK | 3 h | — | sections rédigées |
| T68 | Gantt réel final + comparaison prévu/réel + temps estimés vs réels | JK | 1,5 h | — | annexe du rapport |
| T69 | Relecture complète du rapport (orthographe, partie F) | NH | 1,5 h | T66, T67 | rapport en PDF |
| T70 | Scénario de démo 15 min (qui parle, quoi montrer, données prêtes) | JK | 1,5 h | — | `docs/gestion/scenario-demo.md` |
| T71 | Répétition de la démo chronométrée | Tous | 1 h | T70 | < 15 min, plan B hors-ligne testé |
| T72 | Tag `v2.0-final` + clone propre testé | JK | 0,5 h | T64 | tag poussé |
| T73 | Évaluation par les pairs (répartition des points) | Tous | 0,5 h | — | fiche rendue |
| T74 | Compte-rendu final + mail de clôture au commanditaire | JK | 1 h | — | CR-07 commité, mail envoyé |

---

## Tâches PO récurrentes (chaque séance)

- Début : daily de 5 min (fait hier / fait aujourd'hui / blocages)
- Pendant : déplacer les cartes, débloquer, vérifier que chacun commit régulièrement
- Fin : réunion de 10 min → compte-rendu (estimé vs réel) → commit → mail au prof si besoin
- Vérifier qu'une version **sans bug** est sur `main` à la fin de chaque séance

## Chemin critique (à confirmer avec le PERT)

T13 MCD → T14 schéma → T23 base → T28 créer quizz → T31 jouer/corriger → T36 CLI joueur → T38 recette → T64 bugs → T71 démo
