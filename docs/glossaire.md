# Glossaire

## Domaine de l'application
| Terme | Définition |
|-------|------------|
| Quizz | Série de questions à choix proposée aux utilisateurs inscrits. |
| Question | Énoncé accompagné d'au moins deux choix, dont au moins un correct. |
| Choix | Réponse possible à une question, marquée correcte ou non. |
| Tentative | Passage d'un quizz par un utilisateur à une date donnée, avec un score. |
| Score | Nombre de questions justes sur le nombre total de questions d'une tentative. |
| Corrigé | Liste des questions avec ✔/✘ et la bonne réponse, affichée après une tentative. |
| Historique | Liste des tentatives d'un utilisateur, de la plus récente à la plus ancienne. |
| Classement | Meilleur score de chaque joueur sur un quizz, du meilleur au moins bon. |
| Minuterie | Durée limite (en secondes) d'un quizz ; au-delà, les questions restantes sont fausses. |
| Administrateur | Utilisateur autorisé à créer, importer, modifier, exporter et supprimer des quizz. |
| Import / export | Lecture d'un quizz depuis un fichier (texte ou JSON) / écriture d'un quizz dans un fichier JSON. |
| Source d'un quizz | Origine du quizz : `manuel`, `fichier` ou `ia`. |

## Technique
| Terme | Définition |
|-------|------------|
| MCD / MLD | Modèle conceptuel / logique de données (méthode Merise) : entités et associations / tables et clés. |
| Cardinalité | Nombre minimum et maximum de participations d'une entité à une association (ex. 1,n). |
| Clé étrangère | Colonne qui référence la clé primaire d'une autre table. |
| Cascade | Suppression automatique des lignes qui dépendent d'une ligne supprimée. |
| Hachage + sel | Transformation à sens unique du mot de passe, avec une valeur aléatoire propre à chaque compte. |
| Transaction | Groupe d'opérations sur la base : tout est appliqué, ou rien. |
| Test unitaire | Petit programme qui vérifie automatiquement une fonction (ici avec pytest). |
| Mock | Faux objet utilisé dans un test à la place d'un vrai service (ex. une fausse IA). |

## Intelligence artificielle
| Terme | Définition |
|-------|------------|
| LLM | *Large Language Model* : modèle d'IA qui génère du texte (ici Claude, via une API). |
| API | Interface qui permet à un programme d'appeler un service distant. |
| Clé API | Identifiant secret qui autorise l'accès à l'API ; stocké dans `.env`, jamais sur GitHub. |
| Prompt | Instruction envoyée au modèle d'IA. |
| Hallucination | Réponse fausse donnée avec assurance par une IA : d'où la relecture par l'admin. |
| Mode hors-ligne | Fonctionnement de Kwizz sans IA, quand il n'y a pas de clé ou pas de réseau. |

## Gestion de projet
| Terme | Définition |
|-------|------------|
| Product Owner (PO) | Membre qui gère le projet, priorise le backlog et sert d'interface avec le commanditaire. |
| Commanditaire | Client du projet ; ici l'enseignant. |
| Backlog | Liste priorisée des user stories à réaliser. |
| User story (US) | Besoin exprimé du point de vue d'un utilisateur : « En tant que…, je veux…, afin de… ». |
| MoSCoW | Priorisation : Must, Should, Could, Won't. |
| Sprint | Période de travail courte (ici une semaine) avec un objectif livrable. |
| Daily | Point rapide en début de séance : fait, à faire, blocages. |
| Rétrospective | Réunion de fin de sprint sur la façon de travailler : garder, arrêter, essayer. |
| Definition of Done | Critères communs qu'une tâche doit remplir pour être « terminée ». |
| PBS / WBS | Découpage des produits à livrer / du travail à réaliser. |
| Gantt | Diagramme des tâches sous forme de barres sur un axe du temps. |
| PERT / chemin critique | Réseau des dépendances entre tâches / suite de tâches sans marge. |
| Pull Request (PR) | Demande de fusion d'une branche Git, relue par un autre membre. |
| Recette | Vérification par le PO que le produit répond aux critères d'acceptation. |
