# Backlog v2.1 : des données fiables (bonus, après le MVP)

Source : revue produit du 16/10/2026 (`revue-produit-2026-10-16.md`). Ces stories complètent US01 à
US19 de `backlog.md`. Elles ne démarrent qu'une fois le MVP fusionné et recetté.

| ID | En tant que | Je veux | Afin de | Priorité | Responsable |
|----|-------------|---------|---------|----------|-------------|
| US20 | équipe | que la base ait un numéro de version et des index | faire évoluer le schéma sans casser les bases existantes | **Must** | Akram |
| US21 | joueur | que modifier ou supprimer un quizz n'efface pas mes parties | garder tout mon historique | **Must** | Akram + Sami |
| US22 | équipe | enregistrer le résultat de chaque question | permettre l'historique détaillé et les statistiques | **Must** | Sami |
| US23 | administrateur | que « Pourquoi ? » ne marche que sur une question déjà jouée | empêcher d'obtenir les réponses sans jouer | **Must** | Sami |
| US24 | joueur | rester connecté si le serveur redémarre | ne pas perdre ma partie | Should | Akram |
| US25 | administrateur | que l'explication IA d'une erreur soit gardée | payer et attendre une seule fois | Should | Sami |
| US26 | joueur | revoir le corrigé d'une ancienne partie | réviser mes erreurs passées | Should | Nour |
| US27 | administrateur | voir les questions les plus ratées | repérer une question mal posée | Could | Nour |
| US28 | utilisateur | me connecter sans souci de majuscules (`Alice` = `alice`) | ne pas créer de doublons | Could | Akram |
| US29 | joueur | être tutoyé partout | une interface cohérente | Could | Nour |

## Critères d'acceptation des « Must »
- **US20** : une base créée par la v2.0 s'ouvre sans perte ; un test de migration le prouve.
- **US21** : après modification ou suppression d'un quizz, l'historique et le corrigé des parties
  passées sont identiques ; « supprimer » devient « archiver » (avec « restaurer »).
- **US22** : une ligne par question à chaque correction, et `juste` vaut ce que renvoie `est_juste`.
- **US23** : refus (403) pour une question d'un quizz jamais corrigé par ce joueur ; test automatique.

## Stories ajoutées après la revue (US30 à US39)

Source : cartes Trello à étiquette violette. US30 à US38 forment la « V2 » de MyKwizz (comptes,
contenus, assistant) ; US39 complète la v2.1.

| ID | En tant que | Je veux | Afin de | Priorité | Responsable |
|----|-------------|---------|---------|----------|-------------|
| US30 | utilisateur | un mot de passe solide, et que l'ancien soit demandé pour le changer | que mon compte ne soit pas facile à prendre | **Must** | Akram |
| US31 | administrateur | créer, renommer, passer admin, réinitialiser ou supprimer un compte | gérer les utilisateurs sans toucher à la base | **Must** | Akram |
| US32 | administrateur | voir les actions des utilisateurs et l'historique de chacun | suivre l'activité et repérer un problème | Should | Akram |
| US33 | administrateur | tester un quizz sans que le score compte, puis le valider | ne publier que des quizz vérifiés | **Must** | Sami |
| US34 | joueur | des quizz rangés par matière | réviser le sujet qui m'intéresse | Should | Jaafar |
| US35 | joueur | poser des questions de cours à un assistant | comprendre mes erreurs | Should | Sami |
| US36 | PO | une fiche claire par matière avec des ressources fiables | que l'assistant puisse expliquer chaque question | Should | Jaafar |
| US37 | administrateur | un tableau de bord sur les parties | voir ce qui marche | Should | Nour |
| US38 | joueur | voir mes statistiques et changer mon mot de passe | suivre ma progression | Should | Nour |
| US39 | administrateur | écrire moi-même l'explication d'une question | que le joueur comprenne son erreur même sans IA | Should | Jaafar |

### Critères d'acceptation des « Must »
- **US30** : 8 caractères minimum avec une lettre et un chiffre ; l'ancien mot de passe est exigé ; le
  mot de passe n'apparaît jamais en clair (ni en base, ni dans le journal).
- **US31** : le dernier admin ne peut être ni supprimé ni rétrogradé ; un admin ne peut pas se
  supprimer ; une réinitialisation de mot de passe déconnecte le compte partout.
- **US33** : un quizz créé, importé ou modifié est un brouillon invisible des joueurs ; la validation
  est refusée tant qu'il n'a pas été testé depuis sa dernière modification ; un test n'entre dans
  aucun score.

## Definition of Done
Identique à `backlog.md` : PR relue et fusionnée, tests verts, `python main.py` fonctionne, carte
Trello dans ✅ Terminé avec le temps réel.
