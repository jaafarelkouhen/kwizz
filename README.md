<p align="center">
  <img src="quizz/ui/logo.png" alt="Logo Kwizz & Co" width="180">
</p>

# Kwizz — PROJ531 Gestion de projet informatique

**Kwizz** est une application Python de quizz, en console et en interface graphique :
- un **administrateur** crée des quizz (à la main, depuis un fichier texte ou JSON, ou avec l'IA) ;
- les **joueurs inscrits** y répondent, avec une minuterie et un ordre aléatoire possibles ;
- chacun voit son **score**, les **bonnes réponses**, son **historique** et le **classement** de chaque
  quizz.

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
python main.py --gui    # interface graphique (Tkinter)
python -m pytest        # lancer les tests automatiques
```

**Premier lancement :** un compte administrateur `admin` / `admin` est créé. À la première connexion,
Kwizz **oblige à choisir un nouveau mot de passe**. Les données sont stockées dans `quizz.db` (SQLite),
créée automatiquement et ignorée par Git.

| Je suis… | Je peux… |
|----------|----------|
| visiteur | créer un compte (mot de passe saisi deux fois, masqué à l'écran) |
| joueur | passer un quizz (ordre aléatoire possible), voir le corrigé, mon historique, le classement, la recommandation 💡 |
| admin | tout ce que fait un joueur, plus : créer, importer (`.txt` / `.json`), exporter en JSON, modifier, supprimer un quizz, générer un quizz avec l'IA 🤖 |

La création et la modification de quizz « à la main » se font dans la **console**. L'interface
graphique propose le jeu, l'import, l'export, la suppression et la génération par IA.

## Assistant IA (optionnel)

Sans configuration, Kwizz fonctionne normalement : les fonctions IA sont **simplement masquées**.
Pour les activer :

```bash
copy .env.example .env        # Linux/Mac : cp .env.example .env
```
puis, dans `.env`, renseignez `ANTHROPIC_API_KEY=` avec votre clé API Claude. **Ne commitez jamais
`.env`** : il est déjà dans `.gitignore`.

Fonctions activées :
- **générer un quizz** à partir d'un thème ou d'un texte collé (admin), avec relecture obligatoire
  avant l'enregistrement ;
- **« Pourquoi ? »** : une explication de chaque mauvaise réponse après la correction.

La recommandation du prochain quizz marche **même sans IA** (règles simples). Options du fichier
`.env` : `KWIZZ_IA=non` désactive l'IA, et `KWIZZ_MODELE=` change le modèle (par défaut
`claude-opus-5-5`). Détails et justification : [docs/conception/choix-ia.md](docs/conception/choix-ia.md).

## Formats d'import

```text
# TITRE: Capitales d'Europe
# DESCRIPTION: Teste tes connaissances en géographie
# DUREE: 60
Q: Quelle est la capitale de l'Italie ?
- Milan
+ Rome
- Naples
```

- `# TITRE:`, `# DESCRIPTION:` et `# DUREE:` (en secondes) sont optionnels ; toute autre ligne `#` est
  un commentaire.
- `Q:` commence une question ; `+` = bonne réponse, `-` = mauvaise réponse (au moins 2 choix et au
  moins 1 bonne réponse).
- Le format **JSON** (export et import) est décrit dans
  [docs/conception/formats.md](docs/conception/formats.md).
- Exemples dans [`data/exemples/`](data/exemples/) : capitales, gestion de projet, bases de Python,
  et un exemple JSON.

## Structure du dépôt

```
main.py                   point d'entrée (console ou --gui)
quizz/
  models.py               objets métier (Utilisateur, Quizz, Question, Choix, Tentative)
  database.py             connexion SQLite, schéma, migration automatique
  auth.py                 comptes, hachage des mots de passe, mot de passe admin
  quiz_service.py         créer, modifier, jouer, corriger, historique, classement, minuterie, ordre aléatoire
  importer.py             import texte / JSON, export JSON
  config.py               lecture de .env (IA)
  ia/                     assistant IA optionnel : client, générateur, explications, recommandation
  ui/cli.py               interface console
  ui/gui.py               interface graphique Tkinter
tests/                    tests pytest (dont un scénario complet de démo)
data/exemples/            quizz d'exemple
docs/                     gestion de projet, conception, comptes-rendus, rapport
```

Règles d'architecture : `ui/` n'écrit jamais de SQL ; `auth`, `quiz_service`, `importer` et `ia/` ne
font jamais de `print()` ni d'`input()` ([architecture](docs/conception/architecture.md)).

## Avancement

| US | Fonctionnalité | État |
|----|----------------|------|
| US01-02 | Création de compte, connexion (3 essais) | ✅ |
| US03 | Création de quizz (admin) | ✅ |
| US04-05 | Passer un quizz, score + corrigé | ✅ |
| US06 | Import fichier texte | ✅ |
| US07 | Historique des scores | ✅ |
| US08 | Modifier / supprimer un quizz | ✅ |
| US09 | Minuterie | ✅ |
| US10 | Export / import JSON | ✅ |
| US11 | Interface graphique | ✅ |
| US12 | Classement | ✅ |
| US13 | Questions en ordre aléatoire | ✅ |
| US14 | Mot de passe masqué à la saisie | ✅ |
| US15 | Changement obligatoire du mot de passe admin | ✅ |
| US16 | IA : générer un quizz | ✅ |
| US17 | IA : expliquer une mauvaise réponse | ✅ |
| US18 | Recommandation du prochain quizz | ✅ |
| US19 | Fonctionnement sans IA | ✅ |

## Équipe

| Membre | Rôle | Responsabilités |
|--------|------|-----------------|
| Jaafar EL KOUHEN | Product Owner | relation avec le commanditaire, Trello, comptes-rendus, plannings, intégration (`main.py`), rapport |
| Akram AISSA | Dev « Données » | MCD, base de données, comptes et sécurité, classement, recommandation |
| Sami LAARFI | Dev « Moteur Quizz » | création, jeu, correction, import/export, minuterie, services IA |
| Nour El Oula HARRAG | Dev « Interface & Qualité » | console, interface graphique, tests, README, logo |

- Tableau Trello : https://trello.com/b/uNtICE5l/kwizz-co-kwizz-app
- Gestion de projet : [`docs/gestion/`](docs/gestion/) (backlog, PBS, WBS, Gantt, PERT, risques, charte)
- Comptes-rendus de séance : [`docs/comptes-rendus/`](docs/comptes-rendus/)
