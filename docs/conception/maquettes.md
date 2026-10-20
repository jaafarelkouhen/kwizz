# Maquettes des écrans — Kwizz

Maquettes « fil de fer » : elles fixent **ce qu'on affiche et où**, avant de coder.

## Console

```text
=== Accueil ===                       === Connecté : alice (joueur) ===
  1. Se connecter                       💡 Recommandé : « Capitales d'Europe » (jamais joué)
  2. Créer un compte                    1. Passer un quizz
  3. Quitter                            2. Mon historique
Votre choix : _                         3. Classement d'un quizz
                                        4. Se déconnecter
```

```text
### Capitales d'Europe — 3 question(s) — ⏱ 60 s ###     --- Correction ---
                                                         ✔ Q1. Capitale de l'Italie ?  →  Rome
Q1. Quelle est la capitale de l'Italie ?  (52 s)         ✘ Q2. Capitale du Portugal ?  →  Lisbonne
   1) Milan                                              ✔ Q3. Capitale de la Pologne ? →  Varsovie
   2) Rome
   3) Naples                                             >>> Score : 2/3 en 41s <<<
Votre réponse : _                                        Expliquer mes erreurs avec l'IA ? (o/n)
```

```text
=== Connecté : admin (admin) ===
  1. Passer un quizz            6. Modifier un quizz
  2. Mon historique             7. Supprimer un quizz
  3. Classement d'un quizz      8. Exporter un quizz en JSON
  4. Créer un quizz             9. Générer un quizz avec l'IA   ← affiché seulement si IA disponible
  5. Importer (texte ou JSON)  10. Se déconnecter
```

## Interface graphique (Tkinter)

```text
┌──────────── Kwizz ────────────┐   ┌──────────────── Kwizz — alice ────────────────┐
│          [ logo ]             │   │ 💡 Recommandé : Capitales d'Europe             │
│  Login        [__________]    │   │ ┌───────────────────────────────────────────┐ │
│  Mot de passe [**********]    │   │ │ Capitales d'Europe   ⏱ 60 s               │ │
│                               │   │ │ Gestion de projet    ⏱ 120 s              │ │
│ [Se connecter] [Créer compte] │   │ │ Les bases de Python                       │ │
│  message d'erreur en rouge    │   │ └───────────────────────────────────────────┘ │
└───────────────────────────────┘   │ ☐ Ordre aléatoire                             │
                                    │ [Jouer] [Historique] [Classement] [Quitter]   │
                                    └───────────────────────────────────────────────┘
┌──────────── Q2 / 3 ─────── ⏱ 37 s ┐   ┌──────────── Résultat : 2 / 3 ─────────────┐
│ Quelle est la capitale du         │   │ ✔ Q1  Rome                                 │
│ Portugal ?                        │   │ ✘ Q2  bonne réponse : Lisbonne  [Pourquoi ?]│
│  ( ) Lisbonne                     │   │ ✔ Q3  Varsovie                             │
│  ( ) Porto                        │   │                                            │
│  ( ) Madrid                       │   │                 [Retour à la liste]        │
│                       [Valider]   │   └────────────────────────────────────────────┘
└───────────────────────────────────┘
```

**Principes retenus :**
- une action principale par écran ;
- les erreurs s'affichent en rouge dans la fenêtre, jamais en plantage ;
- les fonctions IA ne sont visibles que si l'IA est disponible.
