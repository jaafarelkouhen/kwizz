# Backlog produit — Kwizz

Priorités **MoSCoW** :
- **M**ust : obligatoire d'après le cahier des charges ;
- **S**hould : important ;
- **C**ould : bonus si le temps le permet ;
- **W**on't : pas dans cette version.

| US | En tant que… | je veux… | afin de… | Priorité | Sprint |
|----|--------------|----------|----------|----------|--------|
| US01 | visiteur | créer un compte | conserver l'historique de mes scores | **Must** | S3 |
| US02 | utilisateur | me connecter | retrouver mon compte et mes scores | **Must** | S3 |
| US03 | administrateur | créer un quizz à la main | proposer de nouvelles questions | **Must** | S3 |
| US04 | joueur | choisir et passer un quizz | tester mes connaissances | **Must** | S4 |
| US05 | joueur | voir mon score et les bonnes réponses | comprendre mes erreurs | **Must** | S4 |
| US06 | administrateur | importer un quizz depuis un fichier texte | créer vite un long quizz | **Must** | S4 |
| US07 | joueur | consulter l'historique de mes scores | suivre ma progression | **Must** | S4 |
| US08 | administrateur | modifier ou supprimer un quizz | corriger une erreur | Should | S4 |
| US09 | administrateur | fixer une durée limite à un quizz | ajouter du défi | Could | S5 |
| US10 | administrateur | exporter / importer un quizz en JSON | partager des quizz | Could | S5 |
| US11 | joueur | utiliser une interface graphique | jouer plus confortablement | Could | S5 |
| US12 | joueur | voir le classement d'un quizz | me comparer aux autres | Could | S5 |
| US13 | joueur | avoir les questions dans un ordre aléatoire | ne pas apprendre l'ordre par cœur | Could | S5 |
| US14 | utilisateur | que mon mot de passe soit masqué à la saisie | qu'on ne le lise pas par-dessus mon épaule | Should | S3 |
| US15 | administrateur | être obligé de changer le mot de passe par défaut | sécuriser le compte admin | Should | S3 |
| US16 | administrateur | générer un quizz avec l'IA à partir d'un thème ou d'un texte | gagner du temps | Could | S6 |
| US17 | joueur | qu'on m'explique pourquoi ma réponse est fausse | apprendre de mes erreurs | Could | S6 |
| US18 | joueur | qu'on me recommande un quizz | savoir quoi travailler | Could | S6 |
| US19 | utilisateur | que l'appli marche sans clé IA ni réseau | ne jamais être bloqué | **Must** si IA | S6 |
| — | joueur | jouer en ligne à plusieurs en même temps | — | Won't | — |

## Critères d'acceptation des US obligatoires
- **US01** : un login de 3 caractères minimum, unique ; un mot de passe de 4 caractères minimum,
  stocké haché ; la confirmation du mot de passe est demandée.
- **US02** : un message identique si le login ou le mot de passe est faux ; 3 essais.
- **US03** : au moins 1 question, au moins 2 choix, au moins 1 bonne réponse ; récapitulatif avant
  l'enregistrement.
- **US04/05** : la correction affiche ✔/✘ par question avec la bonne réponse ; le score est enregistré.
- **US06** : format `Q:` / `+` / `-` ; une erreur indique le numéro de ligne.
- **US07** : les tentatives triées de la plus récente à la plus ancienne, avec date, quizz et score.

## Definition of Done (commune à toutes les US)
Le code est relu dans une PR et fusionné dans `main`, les tests passent, `python main.py` fonctionne,
et la carte Trello est dans ✅ Terminé avec le temps réel noté.
