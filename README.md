<p align="center">
  <img src="docs/assets/logo-kwizz.webp" alt="Logo Kwizz & Co" width="260">
</p>

# Kwizz — PROJ531 Gestion de projet informatique

**Kwizz** est une application Python de quizz : un **administrateur** crée des quizz (à la main ou depuis un
fichier texte), les **utilisateurs inscrits** y répondent, voient leur **score**, les
**bonnes réponses** et l'**historique** de leurs scores.

## Installation

Python 3.10 ou plus récent.

```bash
git clone https://github.com/jaafarelkouhen/kwizz.git
cd kwizz
python -m venv .venv
.venv\Scripts\activate        # Linux/Mac : source .venv/bin/activate
pip install -r requirements.txt
```

## Utilisation

```bash
python main.py          # interface console
python main.py --gui    # interface graphique (en cours)
python -m pytest        # lancer les tests
```

Au premier lancement, un compte administrateur est créé : **login `admin` / mot de passe `admin`**.
Les données sont stockées dans `quizz.db` (SQLite, créée automatiquement, ignorée par Git).

## Format du fichier texte d'import

```text
# TITRE: Capitales d'Europe
# DESCRIPTION: Teste tes connaissances en géographie
# DUREE: 60
Q: Quelle est la capitale de l'Italie ?
- Milan
+ Rome
- Naples
```

- `# TITRE:`, `# DESCRIPTION:`, `# DUREE:` (en secondes) sont optionnels ; toute autre ligne `#` est un commentaire.
- `Q:` commence une question ; `+` = bonne réponse, `-` = mauvaise réponse (au moins 2 choix, au moins 1 bonne).
- Exemples dans [`data/exemples/`](data/exemples/).

## Structure du dépôt

```
main.py                 point d'entrée
quizz/
  models.py             objets métier (Utilisateur, Quizz, Question, Choix, Tentative)
  database.py           connexion SQLite + schéma
  auth.py               inscription, connexion, hachage des mots de passe
  quiz_service.py       créer, lister, corriger, historique
  importer.py           import fichier texte (+ JSON à venir)
  ui/cli.py             interface console
  ui/gui.py             interface graphique (bonus)
tests/                  tests pytest
data/exemples/          quizz d'exemple
docs/                   comptes-rendus, gestion de projet, conception, rapport
```

Règle d'architecture : `ui/` n'écrit jamais de SQL ; `quiz_service`, `auth` et `importer` ne font jamais de `print()`/`input()`.

## Avancement

| US | Fonctionnalité | État |
|----|----------------|------|
| US01-02 | Création de compte, connexion | ⬜ |
| US03 | Création de quizz (admin) | ⬜ |
| US04-05 | Passer un quizz, score + corrigé | ⬜ |
| US06 | Import fichier texte | ⬜ |
| US07 | Historique des scores | ⬜ |
| US08 | Modifier / supprimer un quizz | ⬜ |
| US09 | Minuterie | ⬜ |
| US10 | Export / import JSON | ⬜ |
| US11 | Interface graphique | ⬜ |
| US12 | Classement | ⬜ |
| US13 | Questions en ordre aléatoire | ⬜ |

## Équipe

| Membre | Rôle | Responsabilités |
|--------|------|-----------------|
| Jaafar EL KOUHEN | Product Owner | Lien avec le commanditaire, Trello, comptes-rendus, plannings, intégration (`main.py`) |
| Akram AISSA | Dev « Données » | MCD, base de données, comptes utilisateurs (`database.py`, `auth.py`, `models.py`) |
| Sami LAARFI | Dev « Moteur Quizz » | Création, jeu, correction, import/export (`quiz_service.py`, `importer.py`) |
| Nour El Oula HARRAG | Dev « Interface & Qualité » | Console, interface graphique, tests, README (`ui/`, `tests/`) |

- Tableau Trello : <lien>
- Comptes-rendus de séance : [`docs/comptes-rendus/`](docs/comptes-rendus/)
