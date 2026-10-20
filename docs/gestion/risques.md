# Matrice des risques — Kwizz

Probabilité (P) et impact (I) notés de 1 à 3. **Criticité = P × I** : à partir de 6, le risque est
prioritaire.

| # | Risque | P | I | Criticité | Prévention | Si ça arrive |
|---|--------|---|---|-----------|------------|--------------|
| R1 | Absence ou indisponibilité d'un membre | 2 | 3 | **6** | chaque module est documenté (README par tâche) ; on prévient avant la séance | le PO redistribue les cartes, c'est noté dans le CR |
| R2 | Conflits Git (plusieurs personnes sur `cli.py`) | 3 | 2 | **6** | une branche par carte, fusion dans l'ordre, on prévient avant de toucher le fichier d'un autre | résolution à deux, puis on relance les tests |
| R3 | Retard d'intégration (un module bloque les autres) | 2 | 3 | **6** | données poussées en premier ; chemin critique suivi (PERT) | le PO repriorise et décale les bonus |
| R4 | `main` cassé en fin de séance | 2 | 3 | **6** | tests avant chaque PR ; recette du PO sur un clone propre | retour au dernier commit stable (`git revert`) |
| R5 | Sous-estimation des tâches | 3 | 2 | **6** | tâches de 6 h max ; on compare estimé et réel à chaque CR | on sort les bonus (Could) du sprint |
| R6 | API IA indisponible ou réseau absent pendant la démo | 2 | 2 | 4 | mode hors-ligne (US19) : l'appli marche sans IA | démo du plan B sans IA |
| R7 | Clé API IA publiée sur GitHub | 1 | 3 | 3 | clé dans `.env`, `.env` dans `.gitignore`, `.env.example` sans vraie clé | révoquer la clé immédiatement et en créer une autre |
| R8 | Coût de l'API IA | 1 | 2 | 2 | petit modèle, réponses courtes, limite de questions générées | désactiver l'IA |
| R9 | Contenu faux généré par l'IA | 2 | 2 | 4 | l'admin relit et valide avant d'enregistrer | modifier ou supprimer le quizz (US08) |
| R10 | Perte de données locales | 1 | 2 | 2 | tout est sur GitHub ; base recréée au lancement | re-cloner le dépôt |
| R11 | Mauvaise communication / tensions | 1 | 3 | 3 | charte d'équipe, daily, canal commun | discussion à deux, puis avec le PO |

À revoir à chaque rétrospective : un risque qui s'est produit est noté dans le compte-rendu avec ce qui
a été fait (rapport, partie C).
