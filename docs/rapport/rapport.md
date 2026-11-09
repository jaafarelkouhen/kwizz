# Rapport de projet — Kwizz

**PROJ531 — Gestion de projet informatique · Polytech · 2026**
**Équipe Kwizz & Co :** Jaafar EL KOUHEN (Product Owner), Akram AISSA, Sami LAARFI, Nour El Oula HARRAG
**Dépôt :** https://github.com/jaafarelkouhen/kwizz · **Trello :** https://trello.com/b/uNtICE5l/kwizz-co-kwizz-app

> Brouillon v1 (sprint S5). Les passages entre crochets `[…]` sont à compléter avec les **données
> réelles** du projet : temps réels, dates, difficultés vécues. Ne rien inventer : le prof compare avec
> Trello et GitHub.

## Sommaire
- A. Objectifs du projet
- B. Gestion du projet
- C. Autonomie de l'équipe et gestion des difficultés *(sprint S7)*
- D. Réalisation technique *(Akram et Sami, sprint S7)*
- E. Bilan et perspectives *(sprint S7)*
- Annexes

---

## A. Objectifs du projet

### A.1 Le besoin
Le commanditaire demande une **application Python de quizz** : un quizz est une série de questions
posées à des utilisateurs autorisés, et l'application affiche le score final et les bonnes réponses.
Le cahier des charges impose au minimum :
- la **création de compte**, pour conserver l'historique des scores de chaque utilisateur ;
- la **création de quizz par un administrateur**, directement ou à partir d'un fichier texte.

Il suggère des extensions : minuterie, export JSON, interface graphique.

### A.2 Notre compréhension et notre périmètre
Le cahier des charges est volontairement court. Nous l'avons traduit en **19 user stories** priorisées
avec la méthode MoSCoW ([backlog](../gestion/backlog.md)) :
- **Must** (US01–US07) : comptes, connexion, création et import de quizz, jeu, correction, historique.
- **Should** (US08, US14, US15) : modifier/supprimer un quizz, sécurité des mots de passe.
- **Could** (US09–US13, US16–US18) : minuterie, JSON, interface graphique, classement, ordre
  aléatoire et un **assistant IA**. L'IA est une initiative de l'équipe, au-delà des suggestions du sujet.
- **Contrainte forte** (US19) : l'application doit rester **entièrement utilisable sans IA**.

### A.3 Double objectif
Le projet est évalué à **60 % sur la gestion de projet** et à 40 % sur le développement. Notre objectif
était donc autant de **livrer un produit qui marche** que de **montrer une démarche de gestion de projet
traçable** : Trello, comptes-rendus, Git et les livrables de planification.

---

## B. Gestion du projet

### B.1 Organisation de l'équipe
| Membre | Rôle | Périmètre |
|--------|------|-----------|
| Jaafar EL KOUHEN | Product Owner | relation avec le commanditaire, backlog, Trello, plannings, comptes-rendus, intégration, rapport |
| Akram AISSA | Dev « Données » | MCD/MLD, base SQLite, comptes et sécurité, classement, recommandation |
| Sami LAARFI | Dev « Moteur Quizz » | logique des quizz, import/export, minuterie, services IA |
| Nour El Oula HARRAG | Dev « Interface & Qualité » | console, interface graphique, tests, README, logo |

Chaque membre est **propriétaire** de modules précis. Ce découpage par couche (données → moteur →
interface) suit l'architecture logicielle. Il réduit les conflits Git et rend la contribution de
chacun visible. Les règles de travail sont fixées dans la [charte d'équipe](../gestion/charte-equipe.md).

### B.2 Ressources
- **Humaines** : 4 personnes, environ 6 séances encadrées, plus du travail personnel entre les séances.
- **Matérielles et logicielles** : PC personnels sous Windows, Python 3.12, bibliothèques standard
  (`sqlite3`, `tkinter`, `hashlib`) ; `pytest` pour les tests ; SDK `anthropic` pour l'IA (optionnelle).
- **Outils de gestion** : GitHub (code, PR, tags), Trello (tâches), canal d'équipe (communication),
  draw.io et Mermaid (diagrammes).

### B.3 Modèle de processus : SCRUM adapté
Nous avons suivi un **SCRUM simplifié** :
- **sprints d'une semaine**, un par séance, avec chacun un objectif livrable
  ([planning des sprints](../gestion/gantt.md)) ;
- un **backlog priorisé** tenu par le PO ;
- des **tâches de 6 h au maximum**, soit moins de 2 jours comme l'impose le sujet ;
- des **rituels courts** : *daily* de 5 min en début de séance, réunion de fin de séance avec un
  compte-rendu, **rétrospective** en fin de sprint ;
- une **Definition of Done** commune : code relu en PR, tests verts, appli fonctionnelle, carte Trello
  terminée avec le temps réel noté.

Pourquoi SCRUM plutôt qu'un cycle en V : le cahier des charges est court et volontairement ouvert. Une
démarche **itérative** nous a permis de livrer un **MVP dès le sprint S4** (tag `v1.0-mvp`), puis
d'ajouter les bonus sans jamais casser ce qui marchait.

### B.4 Planification
Les livrables de planification exigés sont dans `docs/gestion/` :
| Livrable | Contenu | Fichier |
|----------|---------|---------|
| PBS | ce que l'on livre (application, documentation, gestion, fin de projet) | [PBS.md](../gestion/PBS.md) |
| WBS | 7 lots de travail, 74 tâches T01–T74 avec responsable et charge | [WBS.md](../gestion/WBS.md) |
| Gantt + sprints | planning semaine par semaine, jalons | [gantt.md](../gestion/gantt.md) |
| PERT | 23 tâches structurantes, chemin critique calculé | [PERT.md](../gestion/PERT.md) |
| Risques | 11 risques notés probabilité × impact, avec leurs parades | [risques.md](../gestion/risques.md) |

Le **PERT** a guidé nos décisions. Le chemin critique (backlog → MCD → MLD → base → créer/jouer un
quizz → console → écrans IA → bugs → démo) a montré que les données d'Akram bloquaient tout le reste.
Elles ont donc été **poussées et fusionnées en premier**. À l'inverse, l'interface graphique avait
6 h de marge : c'était la première fonction à réduire en cas de retard.

### B.5 Suivi de l'avancement
- **Trello** : une liste par membre plus les colonnes En cours / En revue / Terminé. Chaque carte porte
  son identifiant (`S3 - T29 …`), une estimation, ses dépendances et un critère de fin.
- **Comptes-rendus** de chaque séance (`docs/comptes-rendus/CR-0N.md`) : tâches prévues, temps
  **estimé** et temps **réel**, problèmes rencontrés, décisions, écart au planning.
- **Git** : une branche et une Pull Request relue par tâche, `main` protégée, tags de version.
  L'historique des commits montre qui a fait quoi.
- **Recette** du PO sur un clone propre avant chaque jalon ([fiche de recette](../gestion/recette-v1.md)).
- **Tests automatisés** : [nombre] tests pytest, dont un scénario complet de démo.

**Estimé vs réel** *(à compléter depuis les comptes-rendus)* :

| Sprint | Charge estimée | Charge réelle | Écart | Explication |
|--------|----------------|---------------|-------|-------------|
| S2 | [ ] h | [ ] h | [ ] | [ ] |
| S3 | [ ] h | [ ] h | [ ] | [ ] |
| S4 | [ ] h | [ ] h | [ ] | [ ] |
| S5 | [ ] h | [ ] h | [ ] | [ ] |
| S6 | [ ] h | [ ] h | [ ] | [ ] |

### B.6 Communication
- **Interne** : canal d'équipe avec un fil par module, une réponse sous 24 h, et les blocages signalés
  immédiatement ([message d'ouverture](../gestion/canal-equipe.md)).
- **Avec le commanditaire** : mail d'ouverture avec les liens du dépôt et du Trello, puis un mail de
  point en fin de séance si besoin ([modèle](../gestion/mail-fin-de-seance.md)).

### B.7 Amélioration continue
À chaque fin de sprint, une **rétrospective** « Garder / Arrêter / Essayer » fixe **une** action pour le
sprint suivant, vérifiée à la rétrospective d'après ([rétrospectives](../gestion/retrospectives.md)).
*[Citer ici 2 actions réelles et leur effet, ex. : « S4 : on attendait la fin de séance pour commiter →
décision : commit à chaque étape → S5 : 3× plus de commits, plus aucun conflit »]*

---

## C. Autonomie de l'équipe et gestion des difficultés
*[Sprint S7 — Jaafar. Auto-formation (Tkinter, SQLite, Git, API IA), appels aux enseignants, initiatives
(assistant IA, interface graphique), cohésion, difficultés relationnelles et leur résolution.]*

## D. Réalisation technique
*[D.1 Architecture et D.4 Moteur : Sami · D.5 Interfaces et D.6 Validation : Nour]*

### D.2 Données : du MCD à SQLite *(Akram)*
Le **MCD** ([MCD.md](../conception/MCD.md), [schéma draw.io](../conception/MCD-Kwizz.drawio)) compte
5 entités : UTILISATEUR, QUIZZ, QUESTION, CHOIX et TENTATIVE. Elles sont reliées par 6 associations.
Deux choix de modélisation sont à justifier :
- **un seul type d'utilisateur**, avec un attribut `est_admin`, plutôt que deux entités. Un
  administrateur peut ainsi aussi jouer, et l'authentification reste unique ;
- **RÉPONDRE (TENTATIVE n,n CHOIX)** conserve le détail des réponses cochées, pas seulement le score.
  Les questions à plusieurs bonnes réponses restent donc possibles.

Le passage au **MLD** applique les règles classiques :
- une association 1,1 donne une clé étrangère ;
- une association 0,1 donne une clé étrangère facultative ;
- une association n,n donne une table `reponse` dont la clé primaire est composée des deux clés.

Le schéma SQL ([schema.sql](../conception/schema.sql)) traduit les **cardinalités en contraintes** :
| Règle du MCD | Contrainte SQL |
|--------------|----------------|
| un login identifie un utilisateur | `UNIQUE` |
| une question appartient à un quizz (1,1) | clé étrangère `NOT NULL` + `ON DELETE CASCADE` |
| un quizz survit à la suppression de son créateur (0,1) | `ON DELETE SET NULL` |
| l'origine d'un quizz est manuel, fichier ou ia | `CHECK (source IN …)` |

**Choix de SQLite** : inclus dans Python, sans serveur à installer, et avec de vraies contraintes
d'intégrité (contrairement à un fichier JSON). Une base qui date d'une version précédente est
**migrée automatiquement** au lancement (`database.migrer`, ajout de la colonne `source`), sans perte de
données. 6 tests vérifient que les cardinalités du MCD sont bien respectées par la base.

### D.3 Sécurité des comptes *(Akram)*
- Les mots de passe ne sont **jamais stockés en clair**. On stocke `sel$hash` : un **sel** aléatoire de
  16 octets propre à chaque compte, et un hash **PBKDF2-SHA256 à 100 000 itérations**, volontairement
  lent. MD5 et SHA-1 seuls ont été écartés : ils sont trop rapides à attaquer par force brute.
- La vérification se fait en **temps constant** (`hmac.compare_digest`).
- Le message « login ou mot de passe incorrect » est **identique** dans les deux cas : on ne révèle pas
  quels logins existent. La connexion permet 3 essais.
- La saisie est **masquée** (`getpass`, US14).
- Le compte `admin/admin` créé au premier lancement doit **obligatoirement changer de mot de passe** à
  la première connexion (US15).
- La clé API de l'IA reste dans `.env`, exclu de Git. Un test vérifie que `.env.example` ne contient
  pas de vraie clé.

### D.x L'assistant IA : choix, éthique et limites
**Choix.** Nous avons comparé l'API Claude, un modèle local (Ollama) et l'absence d'IA
([étude](../conception/choix-ia.md)). Nous avons retenu l'**API Claude, en option**. C'est la seule
solution qui garantit une réponse au format JSON de Kwizz, sans installation lourde sur les 4 PC.

**Limites connues et réponses apportées :**

| Limite | Risque | Ce que fait Kwizz |
|--------|--------|-------------------|
| **Hallucinations** : une IA peut affirmer une chose fausse avec assurance | une question avec une mauvaise « bonne réponse » | aucun quizz généré n'est enregistré sans **relecture** : récapitulatif, avertissement « une IA peut se tromper », confirmation. Le quizz reste modifiable (US08) et porte la marque 🤖 (`source = ia`) |
| Réponse au mauvais format | plantage ou quizz incomplet | format **imposé par un schéma JSON**, puis les **mêmes contrôles** qu'un fichier importé : au moins 2 choix, une seule bonne réponse |
| **Dépendance** à un service externe | démo bloquée sans réseau | **mode hors-ligne** (US19) : sans clé ni réseau, les fonctions IA disparaissent et le reste marche. Testé automatiquement |
| **Coût** à l'usage | facture | appels seulement sur clic, 20 questions maximum, modèle réglable (`KWIZZ_MODELE`) |
| **Données envoyées** à un tiers | confidentialité | seuls le thème, le texte collé ou la question ratée sont envoyés : jamais les comptes, mots de passe ou scores. À éviter : coller un texte confidentiel |
| **Sécurité de la clé** | clé publiée sur GitHub | clé dans `.env` (ignoré par Git), `.env.example` sans vraie clé, test automatique qui le vérifie |
| Refus du modèle | aucune réponse | option `fallbacks` (repli automatique) et message clair à l'utilisateur |

**Position de l'équipe.** L'IA **assiste** l'administrateur et le joueur, elle ne décide pas. La
recommandation de quizz fonctionne même **sans IA**, avec des règles simples et explicables. Le contenu
final reste sous la responsabilité de l'humain qui le valide.

**Validation.** Tout le code IA est testé avec une **fausse IA** : aucun appel réseau pendant les tests.
Les tests couvrent les pannes (pas de clé, délai dépassé, refus, JSON invalide) et le parcours complet
dans les écrans. *[Ajouter ici le résultat d'un essai réel avec une clé : qualité des questions sur
2-3 thèmes, temps de réponse, coût constaté sur la console Anthropic.]*

## E. Bilan et perspectives
*[Sprint S7 — Jaafar. Fonctionnalités livrées / non livrées, évaluation critique, difficultés,
pistes : multijoueur, modèle IA local, export PDF des résultats…]*

## Annexes
- Gantt réel vs prévu (T68)
- Comptes-rendus de séance
- Fiche de recette
