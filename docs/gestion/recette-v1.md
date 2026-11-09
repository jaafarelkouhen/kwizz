# Fiche de recette — MVP (v1.0-mvp)

**Testeur :** Jaafar EL KOUHEN (PO) · **Date :** 09/11/2026 · **Commit testé :** `85e1a03` (main après la PR #54)

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
| 1 | — | `python -m pytest` | tous les tests passent | ✅ | 123 tests passent sur le clone propre |
| 2 | US15 | se connecter `admin` / `admin` | changement de mot de passe obligatoire | ✅ | « Vous utilisez le mot de passe administrateur par défaut » |
| 3 | US15 | nouveau mot de passe `abc` | refusé (4 caractères minimum) | ✅ | « au moins 4 caractères », mot de passe redemandé |
| 4 | US14 | taper un mot de passe | rien ne s'affiche à l'écran | ✅ | saisie via `getpass` (vérifié dans le code et par les tests) |
| 5 | US03 | admin › Créer un quizz avec un titre vide | titre redemandé | ✅ | « Ce champ ne peut pas être vide », titre redemandé |
| 6 | US03 | créer un quizz de 2 questions, minuterie 60 s | récapitulatif affiché, puis « enregistré » | ✅ | récapitulatif ✔ 4 / ✔ Paris, puis « Quizz « Test recette » enregistré » |
| 7 | US06 | importer `data/exemples/capitales.txt` | « importé (3 questions) » | ✅ | « Capitales d'Europe » importé (3 questions) |
| 8 | US06 | importer un fichier qui n'existe pas | « Fichier introuvable », pas de plantage | ✅ | « Fichier introuvable. », retour au menu |
| 9 | US08 | modifier le titre d'un quizz | nouveau titre dans la liste | ✅ | « Capitales d'Europe » renommé, visible dans la liste |
| 10 | US01 | se déconnecter › Créer un compte `alice` avec 2 mots de passe différents | refusé | ✅ | « les deux mots de passe ne correspondent pas » |
| 11 | US01 | créer `alice` correctement | compte créé et connecté directement | ✅ | « Compte « alice » créé. Bienvenue ! », menu joueur affiché |
| 12 | US01 | recréer `alice` | « déjà utilisé » | ✅ | « Le login « alice » est déjà utilisé » |
| 13 | US04/05 | jouer « Capitales d'Europe » avec 1 erreur | ✔/✘ par question, bonnes réponses, score 2/3 | ✅ | ✘ Q1 → Rome, ✔ Q2, ✔ Q3, « Score : 2/3 » |
| 14 | US07 | Mon historique | la partie apparaît avec date et score | ✅ | ligne `2026-11-09 16:06:15 … 2/3` |
| 15 | US02 | 3 mauvais mots de passe | « Trop d'essais », retour à l'accueil | ✅ | 2 messages « essai(s) restant(s) », puis « Trop d'essais » |
| 16 | — | taper `abc` dans un menu | « Entrez un nombre entre… », pas de plantage | ✅ | « Entrez un nombre entre 1 et 9. » |
| 17 | — | `Ctrl+C` dans un menu | « Au revoir ! », pas de trace d'erreur | ✅ | « Au revoir ! », aucune trace d'erreur |
| 18 | US08 | supprimer un quizz | il disparaît de la liste | ✅ | le quizz supprimé n'est plus dans la liste |

## Bilan
- Cas OK : **18 / 18**
- Bugs trouvés → **une carte Trello par bug** (liste du responsable du module), avec les étapes pour le
  reproduire :
  - aucun bug bloquant. À noter : la liste des quizz est triée par titre, donc les numéros changent
    après un renommage ; c'est voulu, mais à savoir pendant la démo.
- Décision : ☑ **MVP accepté → tag `v1.0-mvp`** ☐ refusé, corrections d'abord
- Méthode : les cas 2 à 18 ont été joués sur l'application réelle (`main.py`, base neuve) avec une
  suite de saisies scriptée ; seul le masquage visuel du cas 4 n'est pas observable de cette façon.
