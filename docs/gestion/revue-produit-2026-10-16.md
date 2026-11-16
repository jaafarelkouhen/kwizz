# Revue produit : version web MyKwizz (16/10/2026)

**Animée par :** Jaafar EL KOUHEN (PO)  **Participants :** …  **Durée :** … min

## Contexte
Le client a demandé une version jouable dans le navigateur (le 15/10). MyKwizz réutilise le même paquet
`quizz/` (mêmes règles, même base SQLite) ; seule l'interface change (`serveur.py` + `web/`).

## Méthode
Lecture du code, puis une partie complète jouée sur ordinateur et sur téléphone (375 px), avec les
comptes de démonstration.

## Constats et corrections immédiates
| Constat | Gravité | Correction |
|---|---|---|
| La fenêtre de confirmation s'affichait collée en haut à gauche | visible en démo | corrigée (CSS) |
| Les touches 1 à 9 ne marchaient pas sur la 1re question | accessibilité | corrigée (focus) |
| À égalité au classement, le joueur qui avait joué en premier passait devant, au lieu de celui qui avait atteint le score en premier | règle métier fausse | corrigée + vérifiée |
| « 1er au classement » affiché après un 1/3, sans explication | compréhension | phrase précisée |

## Risques relevés (non corrigés, mis au backlog v2.1)
- Modifier ou supprimer un quizz efface le détail des parties des joueurs → **US21**.
- « Pourquoi ? » peut révéler la bonne réponse d'une question jamais jouée → **US23**.
- Les sessions sont perdues au redémarrage du serveur → **US24**.

## Décisions du PO
1. MyKwizz reste un **bonus** : il ne remplace pas l'application Python notée.
2. Les 10 améliorations deviennent **US20 à US29** (`backlog-v2.1.md`), à traiter après le MVP.
3. Maquettes v2.0 et v2.1 tenues à jour dans Figma (lien dans le README de MyKwizz).
4. Démo : 1 minute de MyKwizz à la fin des 15 minutes, si le temps le permet.

## Suite
- Créer les cartes US20 à US29 dans Trello (Jaafar).
- Valider les priorités avec l'équipe à la prochaine réunion de fin de séance.
