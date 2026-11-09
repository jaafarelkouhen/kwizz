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
    Lancement — dépôt, Trello, mail      :done, p1, 2026-10-12, 3d
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
    Classement (bonus)                    :d3, 2026-11-02, 7d

    section Moteur (Sami)
    Créer / modifier / supprimer          :crit, m1, 2026-10-23, 4d
    Jouer, corriger, historique, import   :crit, m2, after m1, 4d
    JSON, minuterie, ordre aléatoire      :m3, 2026-11-02, 7d

    section Interface & tests (Nour)
    Console accueil + création            :i1, 2026-10-26, 5d
    Console admin + joueur                :crit, i2, after m2, 2d
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

**Corrections de la v1.1 (02/11)** : l'historique (US07) fait partie du MVP, il est donc passé du lot
d3 (après le MVP) au lot m2. La console admin + joueur (i2) finissait le 05/11, après le début de la
recette MVP (02/11) : m1, m2 et i2 sont resserrés pour que i2 se termine le 01/11.

## Gantt réel (mis à jour le 09/11)

Dates de fusion sur `main` (Pull Requests GitHub, numéros entre parenthèses). Le code d'Akram
(getpass, mot de passe admin, schéma SQL) était prêt le 22/10 mais n'a été fusionné que le 02/11.

```mermaid
gantt
    title Kwizz — Gantt réel au 09/11 (Kwizz & Co)
    dateFormat YYYY-MM-DD
    axisFormat %d/%m
    todayMarker off

    section Pilotage (Jaafar)
    Lancement — dépôt, Trello, mail      :done, r1, 2026-10-12, 3d
    Planning des sprints (PR 1)             :done, r2, 2026-10-19, 1d
    Charte, backlog, risques (PR 11-13)     :done, r3, 2026-10-20, 1d
    PBS, WBS, Gantt, PERT (PR 9, 14, 15)  :done, r4, 2026-10-20, 1d
    Workflow Git, CR S2-S4, recette, rétro (PR 25-28) :done, r5, 2026-11-02, 1d
    Étude IA (PR 29)                        :done, r6, 2026-11-02, 1d
    Recette MVP + tag v1.0                :crit, active, r7, 2026-11-02, 8d
    Rapport A, B, éthique IA (PR 44, 47)    :done, r8, 2026-11-09, 1d

    section Conception
    MCD (PR 3)                              :done, rc1, 2026-10-13, 7d
    Schéma SQL + tests (PR 20)              :done, rc2, 2026-10-20, 3d
    Cas d'utilisation, maquettes (PR 10, 16) :done, rc3, 2026-10-20, 1d
    Architecture + formats (PR 23, 24)      :done, rc4, 2026-10-15, 18d

    section Données (Akram)
    Modèles, base, auth (PR 4)              :done, rd1, 2026-10-19, 1d
    getpass + mot de passe admin (PR 20, 21) :done, rd2, 2026-10-20, 13d
    Classement + recommandation (PR 33, 34) :done, rd3, 2026-11-02, 1d
    Config IA + colonne source (PR 37, 38)  :done, rd4, 2026-11-02, 1d
    Rapport D données (PR 50)               :done, rd5, 2026-11-09, 1d

    section Moteur (Sami)
    Créer, jouer, corriger, historique, import (PR 5, 6) :done, rm1, 2026-10-19, 2d
    Modifier un quizz US08 (PR 22)        :crit, done, rm2, 2026-10-23, 10d
    JSON, minuterie, aléatoire (PR 31, 32)  :done, rm3, 2026-11-02, 1d
    Client, générateur, explications IA (PR 39-41) :done, rm4, 2026-11-02, 1d
    Bug BOM + rapport D moteur (PR 46, 51)  :done, rm5, 2026-11-09, 1d

    section Interface & tests (Nour)
    Console + tests (PR 7)                  :done, ri1, 2026-10-20, 1d
    Menu accueil + création (PR 18, 19)    :done, ri2, 2026-10-20, 1d
    Écran modifier + parcours + GUI (PR 30, 35, 36) :done, ri3, 2026-11-02, 1d
    Écrans IA + tests IA (PR 42, 43)        :done, ri4, 2026-11-09, 1d
    README, bug fenêtre figée, rapport D (PR 45, 49, 52) :done, ri5, 2026-11-09, 1d
```

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
| S1 | équipe, outils, périmètre | dépôt, Trello, mail aux profs faits ; CR-01 non rédigé | CR manquant | rédiger CR-01 à partir du Trello |
| S2 | conception validée | MCD le 19/10 ; PBS, WBS, Gantt, PERT, charte, backlog, risques, cas d'utilisation, maquettes le 20/10 ; diagramme d'architecture absent | +1 j ; architecture en retard | PR ouvertes en fin de séance, fusionnées le lendemain ; Sami pousse l'architecture en S4 |
| S3 | comptes + création | modèles, base, auth, création, jeu, correction, import, historique, console : tout fusionné les 19-20/10 | **en avance d'environ 1 semaine** | le squelette commun a permis de livrer le MVP partie 2 en avance |
| S4 | MVP | US08 fusionné le 02/11 en fin de séance (PR 22, 30), avec getpass et mot de passe admin (code prêt le 22/10) ; dans la même séance : tous les bonus (PR 31-36) et le moteur IA (PR 37-41) ; pas de tag `v1.0-mvp` | MVP livré **à la date du jalon**, mais sans recette ni tag ; bonus et moteur IA **en avance d'1 à 2 semaines** | fusionner les PR le jour même (22 PR le 02/11) ; recette et tag reportés |
| S5 | bonus | bonus déjà livrés en S4 ; le 09/11 : écrans IA + tests IA (PR 42, 43), README (PR 45), 3 bugs corrigés (PR 46, 48, 49), rapport A, B, éthique IA et partie D (PR 44, 47, 50-52) ; 121 tests verts | **en avance d'1 semaine** (IA prévue en S6) ; recette MVP et tag `v1.0-mvp` toujours pas faits | faire la recette sur un clone propre et poser le tag `v1.0-mvp` ; S6 consacrée au rapport (C, E) et à la démo |
| S6 | IA | … | … | … |
