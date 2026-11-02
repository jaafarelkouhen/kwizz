# Étude : quelle IA pour l'assistant de Kwizz ?

**Rédigé par :** Jaafar EL KOUHEN (PO) · **Validé par l'équipe le :** …/…/2026

## 1. Besoin
L'assistant IA doit :
1. **générer un quizz** à partir d'un thème ou d'un texte collé (US16, admin) ;
2. **expliquer une mauvaise réponse** après la correction (US17, joueur) ;
3. aider à la **recommandation** du prochain quizz (US18), qui marche aussi sans IA.

Contraintes : l'IA est un **bonus**. L'application doit rester utilisable **sans IA**, sans clé et sans
réseau (US19). Le code IA doit être testable sans appeler l'API, et la clé ne doit jamais être publiée.

## 2. Solutions comparées

| Critère | A. API Claude (SDK `anthropic`) | B. Modèle local (Ollama) | C. Pas d'IA, règles fixes |
|---------|-------------------------------|--------------------------|---------------------------|
| Qualité des questions générées | ✅ très bonne, en français | ⚠ correcte avec un gros modèle, faible avec un petit | ❌ impossible de générer |
| Format JSON garanti | ✅ *structured outputs* (schéma JSON imposé) | ⚠ à vérifier et souvent à corriger | — |
| Installation | ✅ `pip install anthropic` + une clé | ❌ plusieurs Go à télécharger, machine puissante | ✅ rien |
| Marche hors ligne | ❌ non → mode hors-ligne obligatoire | ✅ oui | ✅ oui |
| Coût | ⚠ payant à l'usage (voir § 4) | ✅ gratuit | ✅ gratuit |
| Confidentialité | ⚠ le thème ou le texte part chez Anthropic | ✅ tout reste sur le PC | ✅ |
| Charge pour l'équipe | ✅ faible | ❌ forte (installation sur 4 PC, démo) | ✅ |

## 3. Décision
**Solution A (API Claude), optionnelle, avec un mode hors-ligne propre**, parce que :
- c'est la seule qui garantit un JSON au format attendu : on réutilise directement l'import JSON
  (US10) et ses vérifications ;
- elle ne demande aucune installation lourde, ce qui compte pour les 4 PC et la machine de démo ;
- sans clé ou sans réseau, Kwizz fonctionne exactement comme avant : les boutons IA sont simplement
  masqués. Le risque R6 de la [matrice des risques](../gestion/risques.md) est donc couvert.

La solution B reste une **perspective** pour le rapport (partie E) : un modèle local supprimerait le
coût et l'envoi de données.

## 4. Modèle et coût
- Modèle par défaut : **`claude-opus-5-5`**, le modèle recommandé par Anthropic au moment du projet.
  Il est **modifiable sans toucher au code** grâce à la variable `KWIZZ_MODELE` du fichier `.env`.
  Par exemple, `claude-haiku-5-5` est beaucoup moins cher pour des quizz simples : c'est à l'équipe de
  choisir après avoir testé la qualité.
- Ordre de grandeur (tarifs Anthropic, octobre 2026) : `claude-opus-5-5` coûte 4 $ par million de
  jetons en entrée et 20 $ en sortie. Un quizz de 10 questions représente quelques milliers de jetons,
  soit **quelques centimes**. Une explication d'erreur coûte encore moins.
- Pour limiter les dépenses : 20 questions maximum par génération, réponses courtes pour les
  explications, et l'IA n'est appelée que si l'utilisateur clique.
- **Refus du modèle** : on active l'option `fallbacks` du SDK. Si le modèle refuse une demande pour une
  raison de sécurité, l'API la repasse automatiquement sur un autre modèle. Si tout est refusé, Kwizz
  affiche un message clair.

## 5. Mise en œuvre (qui fait quoi)
| Module | Rôle | Resp. |
|--------|------|-------|
| `.env` / `.env.example` | clé `ANTHROPIC_API_KEY`, `KWIZZ_IA`, `KWIZZ_MODELE` | Akram |
| `quizz/ia/client.py` | un seul point d'accès à l'API : erreurs, délai maximal, mode hors-ligne | Sami |
| `quizz/ia/generateur.py` | thème ou texte → quizz validé (source = `ia`) | Sami |
| `quizz/ia/explications.py` | question + mauvaise réponse → explication courte | Sami |
| `quizz/ia/recommandation.py` | règles simples (sans IA) | Akram |
| écrans console + graphique, tests avec une fausse IA | Nour |

## 6. Règles de sécurité retenues
- La clé n'est **jamais** dans le code ni sur GitHub : `.env` est dans `.gitignore`, et seul
  `.env.example` (sans vraie clé) est versionné.
- Un quizz généré n'est **jamais enregistré sans relecture** par l'admin.
- Les tests n'appellent **jamais** la vraie API : ils remplacent le client par une fausse IA.
