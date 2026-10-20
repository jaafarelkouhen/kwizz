# Gantt prévisionnel et planning des sprints — Kwizz

Hypothèse : **une séance par semaine**, et un sprint = la semaine qui suit la séance. Les dates sont à
ajuster à l'emploi du temps réel. Le détail des 74 tâches (Txx) est dans
[plan-sprints.md](plan-sprints.md).

## Planning des sprints

| Sprint | Séance | Objectif (livrable de fin de sprint) | US visées |
|--------|--------|--------------------------------------|-----------|
| S1 | 12/10 | Équipe, outils et périmètre en place | — |
| S2 | 19/10 | Conception validée : MCD/MLD, architecture, PBS/WBS/Gantt/PERT | — |
| S3 | 26/10 | Comptes utilisateurs et création de quizz | US01–03, US14–15 |
| S4 | 02/11 | **MVP** : jouer, corriger, importer, historique → tag `v1.0-mvp` | US04–08 |
| S5 | 09/11 | Bonus : JSON, minuterie, classement, ordre aléatoire, interface graphique | US09–13 |
| S6 | 16/11 | Assistant IA (optionnel, l'appli marche sans) | US16–19 |
| S7 | 23/11 | Stabilisation, rapport, démo → tag `v2.0-final` | — |

## Diagramme de Gantt

```mermaid
gantt
    title Kwizz — Gantt prévisionnel (Kwizz & Co)
    dateFormat YYYY-MM-DD
    axisFormat %d/%m
    todayMarker off

    section Pilotage (Jaafar)
    Lancement : dépôt, Trello, mail      :done, p1, 2026-10-12, 3d
    Charte, backlog, risques              :p2, 2026-10-15, 5d
    PBS, WBS, Gantt, PERT                 :p3, 2026-10-15, 5d
    Comptes-rendus + mails (chaque séance) :p4, 2026-10-19, 36d
    Recette MVP + tag v1.0                :crit, p5, 2026-11-02, 2d
    Rapport (rédaction)                   :p6, 2026-11-05, 22d

    section Conception
    MCD (Akram)                           :crit, c1, 2026-10-13, 6d
    MLD + schéma SQL (Akram)              :crit, c2, after c1, 2d
    Architecture + formats (Sami)         :c3, 2026-10-15, 5d
    Cas d'utilisation, maquettes (Nour)   :c4, 2026-10-15, 5d

    section Données (Akram)
    Modèles + base SQLite                 :crit, d1, 2026-10-19, 4d
    Authentification + getpass + admin    :d2, after d1, 4d
    Historique + classement               :d3, 2026-11-02, 7d

    section Moteur (Sami)
    Créer / modifier / supprimer          :crit, m1, 2026-10-23, 5d
    Jouer, corriger, import texte         :crit, m2, after m1, 5d
    JSON, minuterie, ordre aléatoire      :m3, 2026-11-02, 7d

    section Interface & tests (Nour)
    Console accueil + création            :i1, 2026-10-26, 5d
    Console admin + joueur                :crit, i2, after m2, 4d
    Interface graphique Tkinter           :i3, 2026-11-09, 7d
    Tests (au fil de l'eau)               :i4, 2026-10-26, 21d

    section Assistant IA (S6)
    Étude + config (Jaafar, Akram)        :a1, 2026-11-09, 4d
    Client + générateur + explications    :crit, a2, 2026-11-16, 4d
    Écrans IA + tests mock                :crit, a3, after a2, 3d

    section Clôture (S7)
    Gel + correction des bugs             :crit, f1, 2026-11-23, 2d
    Démo 15 min                           :milestone, crit, f2, 2026-11-23, 0d
```

Les barres `crit` (en rouge) correspondent au **chemin critique** du [PERT](PERT.md).

## Jalons
| Date | Jalon | Preuve |
|------|-------|--------|
| 19/10 | Conception validée | MCD, PBS/WBS/Gantt/PERT dans `docs/` |
| 02/11 | MVP livré | tag `v1.0-mvp` + fiche de recette |
| 16/11 | Fonctions bonus + IA | tableau d'avancement du README |
| 23/11 | Démo + rapport | tag `v2.0-final`, rapport PDF |

## Suivi « prévu vs réel »
À chaque compte-rendu, on note les écarts dans le tableau ci-dessous. En fin de projet, on refait le
Gantt avec les dates **réelles** (annexe du rapport, tâche T68).

| Sprint | Prévu | Réel | Écart | Cause / action |
|--------|-------|------|-------|----------------|
| S2 | conception validée | … | … | … |
| S3 | comptes + création | … | … | … |
| S4 | MVP | … | … | … |
| S5 | bonus | … | … | … |
| S6 | IA | … | … | … |
