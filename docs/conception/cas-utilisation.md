# Cas d'utilisation — Kwizz

```mermaid
flowchart LR
    V(["🧑 Visiteur"])
    J(["🎮 Joueur"])
    A(["🛠️ Administrateur"])
    IA(["🤖 Service IA<br/>(optionnel)"])

    subgraph K["Système Kwizz"]
        UC1(["Créer un compte — US01"])
        UC2(["Se connecter — US02"])
        UC4(["Passer un quizz — US04"])
        UC5(["Voir score + corrigé — US05"])
        UC7(["Consulter l'historique — US07"])
        UC12(["Voir le classement — US12"])
        UC17(["Demander une explication — US17"])
        UC18(["Recevoir une recommandation — US18"])
        UC3(["Créer un quizz — US03"])
        UC6(["Importer texte / JSON — US06, US10"])
        UC8(["Modifier / supprimer — US08"])
        UC10(["Exporter en JSON — US10"])
        UC16(["Générer un quizz avec l'IA — US16"])
        UC15(["Changer le mot de passe admin — US15"])
    end

    V --> UC1
    J --> UC2 & UC4 & UC7 & UC12 & UC18
    UC4 -. inclut .-> UC5
    UC5 -. étend .-> UC17
    A --> UC2 & UC3 & UC6 & UC8 & UC10 & UC16 & UC15
    UC16 --- IA
    UC17 --- IA
```

**Lecture :**
- **Joueur** et **Administrateur** sont tous deux des utilisateurs connectés. L'administrateur peut
  aussi jouer : c'est le même compte, avec `est_admin = vrai`.
- `inclut` : passer un quizz **affiche toujours** le score et le corrigé.
- `étend` : l'explication IA est **facultative**. Elle n'existe que si l'IA est disponible.

## Description textuelle d'un cas : « Passer un quizz » (US04)
| | |
|--|--|
| **Acteur** | Joueur connecté |
| **Pré-condition** | au moins un quizz existe |
| **Scénario nominal** | 1. le joueur choisit un quizz dans la liste · 2. il choisit l'ordre (normal ou aléatoire) · 3. pour chaque question, il choisit une réponse · 4. le système corrige, enregistre la tentative et affiche le score et le corrigé |
| **Variante minuterie** | si le temps est écoulé, le quizz s'arrête et les questions sans réponse comptent comme fausses |
| **Variante IA** | le joueur demande « Pourquoi ? » sur ses erreurs (US17) |
| **Post-condition** | la tentative apparaît dans l'historique et le classement |
