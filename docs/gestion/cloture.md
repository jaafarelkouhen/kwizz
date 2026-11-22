# Clôture du projet — sprint S7

## 1. Gel des fonctionnalités (début de séance)
Message à poster sur le canal :

> 🧊 **Gel des fonctionnalités** à partir de maintenant : plus aucune nouvelle US. Uniquement des
> corrections de bugs (branches `fix/…`), le rapport et la démo. Tout bug connu = une carte Trello
> « 🐞 » dans la liste du responsable du module, avec les étapes pour le reproduire.

## 2. Checklist de la version finale `v2.0-final`
- ☐ Toutes les PR fusionnées dans l'ordre fixé par le PO, aucune PR ouverte
- ☐ `python -m pytest` : tous les tests passent sur `main`
- ☐ Clone dans un dossier vide → installation → `python main.py` et `python main.py --gui` fonctionnent
- ☐ `python outils/preparer_demo.py` fonctionne
- ☐ README à jour (tableau d'avancement, captures d'écran)
- ☐ Aucun secret dans le dépôt : `git log -p | findstr /i "sk-ant"` ne renvoie rien
- ☐ Tag :
```bash
git checkout main && git pull
git tag -a v2.0-final -m "Version finale : 19 US, IA optionnelle, interface graphique"
git push origin v2.0-final
```
- ☐ Sur GitHub : *Releases › Draft a new release* avec le tag, en joignant `rapport.pdf`

## 3. Mail de clôture au commanditaire

**Objet :** [PROJ531] Kwizz & Co — version finale et rapport

Bonjour Madame, bonjour Monsieur,

L'équipe Kwizz & Co vous transmet la version finale de son projet :
- version finale (tag `v2.0-final`) : https://github.com/jaafarelkouhen/kwizz/releases/tag/v2.0-final
- rapport : `docs/rapport/rapport.pdf` (également joint à ce mail)
- suivi du projet : https://trello.com/b/uNtICE5l/kwizz-co-kwizz-app

En résumé : les 19 user stories sont livrées (cahier des charges minimum, extensions suggérées,
classement, sécurité renforcée et un assistant IA optionnel), avec 123 tests automatiques.
Pour lancer l'application : `pip install -r requirements.txt` puis `python main.py` (ou `--gui`).

En bonus, nous avons réalisé la version web que vous aviez demandée, **MyKwizz**, avec une v2.1
« données fiables » : historique et corrigés jamais effacés, tableau de bord pour l'administrateur,
sécurité renforcée, et un assistant de révision qui répond à partir de fiches de cours (rapport, partie E.3).

Merci pour votre suivi tout au long du projet.

Cordialement,
Jaafar EL KOUHEN — Product Owner, Kwizz & Co
