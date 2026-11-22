# Évaluation par les pairs — mode d'emploi

Le sujet : l'équipe reçoit une note de travail × 4, que nous **répartissons entre nous** selon
l'implication de chacun. Pour que ce soit juste et défendable, on s'appuie sur des **faits**.

## 1. Données objectives (à remplir par le PO avant la discussion)
| Membre | Cartes Trello terminées | Heures réelles (CR) | Commits | PR relues | Présence (séances) |
|--------|-------------------------|---------------------|---------|-----------|--------------------|
| Jaafar | | | | | / 7 |
| Akram | | | | | / 7 |
| Sami | | | | | / 7 |
| Nour | | | | | / 7 |

Commandes utiles :
```bash
git shortlog -sn --no-merges          # commits par auteur
gh pr list --state merged --limit 100 --json author,reviews
```

## 2. Discussion (15 min, sans jugement personnel)
1. Chacun propose **en privé** une répartition (ex. Jaafar 20, Akram 20, Sami 19, Nour 21 si la note
   est 20).
2. On compare : si les propositions sont proches, on prend la moyenne.
3. Si un écart dépasse 2 points, on en discute **à partir du tableau du § 1**.

## 3. Règles
- Le total doit faire exactement note × 4.
- La charge de gestion (PO) compte autant que le code : le projet est noté à 60 % sur la gestion.
- Aucune pression : chacun peut aussi transmettre sa proposition directement à l'enseignant.
