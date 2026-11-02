# Formats d'import / export des quizz

## 1. Format texte (`.txt`) — import (US06)

```text
# TITRE: Capitales d'Europe
# DESCRIPTION: Teste tes connaissances en géographie
# DUREE: 60
# Toute autre ligne qui commence par # est un commentaire

Q: Quelle est la capitale de l'Italie ?
- Milan
+ Rome
- Naples
```

| Ligne | Signification | Obligatoire |
|-------|---------------|-------------|
| `# TITRE: …` | titre du quizz (sinon : nom du fichier) | non |
| `# DESCRIPTION: …` | description | non |
| `# DUREE: n` | minuterie en secondes (entier) | non |
| `Q: …` | début d'une nouvelle question | oui |
| `+ …` | choix **correct** de la dernière question | ≥ 1 par question |
| `- …` | choix **faux** de la dernière question | — |
| ligne vide | ignorée | — |

Encodage **UTF-8**. Une question a au moins 2 choix et au moins 1 bonne réponse.

**Erreurs détectées (avec numéro de ligne) :**
- `# DUREE:` n'est pas un nombre ;
- un choix `+`/`-` apparaît avant toute question `Q:` ;
- une ligne n'est pas reconnue (ex. `* choix`) ;
- puis, à l'enregistrement : pas de question, moins de 2 choix, ou aucune bonne réponse.

## 2. Format JSON (`.json`) — export et import (US10)

```json
{
  "format": "kwizz-quizz",
  "version": 1,
  "titre": "Capitales d'Europe",
  "description": "Teste tes connaissances en géographie",
  "duree_limite": 60,
  "questions": [
    {
      "enonce": "Quelle est la capitale de l'Italie ?",
      "choix": [
        {"texte": "Milan", "correct": false},
        {"texte": "Rome", "correct": true},
        {"texte": "Naples", "correct": false}
      ]
    }
  ]
}
```

| Clé | Type | Obligatoire |
|-----|------|-------------|
| `format` | `"kwizz-quizz"` : permet de reconnaître nos fichiers | oui |
| `version` | entier (`1`) : permettra de faire évoluer le format | oui |
| `titre` | texte non vide | oui |
| `description` | texte | non (`""`) |
| `duree_limite` | entier > 0 ou `null` | non (`null`) |
| `questions` | liste d'objets `{enonce, choix}` | oui |
| `choix` | liste d'objets `{texte, correct}` | oui |

Les identifiants de la base (`id_quizz`…) ne sont **pas** exportés : un fichier JSON peut ainsi être
importé dans n'importe quelle installation de Kwizz.

**Ce même format JSON est demandé à l'IA** quand elle génère un quizz (US16). La réponse de l'IA passe
donc par le même code de lecture et les mêmes vérifications qu'un fichier importé.
