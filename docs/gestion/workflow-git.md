# Workflow Git de l'équipe

## 1. Protéger `main` sur GitHub (une seule fois, par le PO)
*Settings › Branches › Add branch ruleset* (ou *Add rule*) sur `main` :
- ☑ **Require a pull request before merging**, avec 1 approbation ;
- ☑ **Block force pushes** ;
- ☐ ne pas cocher « Require status checks » (pas d'intégration continue dans ce projet).

Plus personne ne peut alors pousser directement sur `main` : tout passe par une Pull Request relue.

## 2. Le cycle d'une carte Trello (pour chaque membre)
```bash
git checkout main
git pull                                  # 1. partir de la dernière version
git checkout -b feature/nom-court         # 2. une branche par carte
# ... coder, puis tester :
python -m pytest
git add fichier1.py fichier2.py           # 3. ajouter SEULEMENT ses fichiers
git commit -m "feat: ce que fait ce commit"
git push -u origin feature/nom-court      # 4. publier la branche
```
5. Sur GitHub : **Compare & pull request**. On donne un titre clair et on met le lien de la carte Trello
   dans la description.
6. On prévient sur le canal : « PR à relire ». Un autre membre relit (*Files changed*), puis
   **Approve** ou **Request changes**.
7. Le PO fusionne (**Merge**), puis **Delete branch**. La carte passe dans ✅ Terminé.

## 3. Mettre sa branche à jour quand `main` a bougé
```bash
git checkout main && git pull
git checkout feature/nom-court
git merge main                # en cas de conflit : ouvrir le fichier, garder le bon code, puis :
git add fichier_en_conflit.py
git commit
python -m pytest              # toujours retester après un merge
```

## 4. Annuler une erreur
| Situation | Commande |
|-----------|----------|
| Modification locale ratée, pas encore commitée | `git restore fichier.py` |
| Dernier commit pas encore poussé | `git reset --soft HEAD~1` (on garde les changements) |
| Commit déjà fusionné dans `main` qui casse tout | `git revert <id-du-commit>`, dans une PR |

## 5. Tags de version
```bash
git checkout main && git pull
git tag -a v1.0-mvp -m "MVP : comptes, création, jeu, correction, import, historique"
git push origin v1.0-mvp
```
Le tag apparaît dans *Releases* sur GitHub : c'est la version que le prof peut cloner et tester.
