# Fiche de recette — MVP (v1.0-mvp)

**Testeur :** Jaafar EL KOUHEN (PO) · **Date :** …/…/2026 · **Commit testé :** `…`

La recette vérifie, **comme le ferait le prof**, que le produit respecte les critères d'acceptation du
[backlog](backlog.md). Elle complète les tests automatiques : on teste ici l'application réelle, à la main.

## Préparation (dans un dossier vide)
```bash
git clone https://github.com/jaafarelkouhen/kwizz.git recette && cd recette
python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt
python -m pytest          # attendu : tous les tests passent
python main.py
```

## Cas de test
| # | US | Action | Résultat attendu | OK / KO | Remarque |
|---|----|--------|------------------|---------|----------|
| 1 | — | `python -m pytest` | tous les tests passent | ☐ | |
| 2 | US15 | se connecter `admin` / `admin` | changement de mot de passe obligatoire | ☐ | |
| 3 | US15 | nouveau mot de passe `abc` | refusé (4 caractères minimum) | ☐ | |
| 4 | US14 | taper un mot de passe | rien ne s'affiche à l'écran | ☐ | |
| 5 | US03 | admin › Créer un quizz avec un titre vide | titre redemandé | ☐ | |
| 6 | US03 | créer un quizz de 2 questions, minuterie 60 s | récapitulatif affiché, puis « enregistré » | ☐ | |
| 7 | US06 | importer `data/exemples/capitales.txt` | « importé (3 questions) » | ☐ | |
| 8 | US06 | importer un fichier qui n'existe pas | « Fichier introuvable », pas de plantage | ☐ | |
| 9 | US08 | modifier le titre d'un quizz | nouveau titre dans la liste | ☐ | |
| 10 | US01 | se déconnecter › Créer un compte `alice` avec 2 mots de passe différents | refusé | ☐ | |
| 11 | US01 | créer `alice` correctement | compte créé et connecté directement | ☐ | |
| 12 | US01 | recréer `alice` | « déjà utilisé » | ☐ | |
| 13 | US04/05 | jouer « Capitales d'Europe » avec 1 erreur | ✔/✘ par question, bonnes réponses, score 2/3 | ☐ | |
| 14 | US07 | Mon historique | la partie apparaît avec date et score | ☐ | |
| 15 | US02 | 3 mauvais mots de passe | « Trop d'essais », retour à l'accueil | ☐ | |
| 16 | — | taper `abc` dans un menu | « Entrez un nombre entre… », pas de plantage | ☐ | |
| 17 | — | `Ctrl+C` dans un menu | « Au revoir ! », pas de trace d'erreur | ☐ | |
| 18 | US08 | supprimer un quizz | il disparaît de la liste | ☐ | |

## Bilan
- Cas OK : … / 18
- Bugs trouvés → **une carte Trello par bug** (liste du responsable du module), avec les étapes pour le
  reproduire :
  - …
- Décision : ☐ MVP accepté → tag `v1.0-mvp` ☐ refusé, corrections d'abord
