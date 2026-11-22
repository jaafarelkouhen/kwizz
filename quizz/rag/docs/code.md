# Code et informatique

## Python : types et opérateurs
En Python 3, `3 / 2` vaut `1.5` (un float) : la division `/` renvoie toujours un flottant. `3 // 2` vaut `1` (division entière) et `3 % 2` vaut `1` (reste). Les types de base sont int, float, str, bool, list, tuple, dict et set. Une liste est modifiable (mutable), un tuple ne l'est pas. `len(x)` donne la taille d'une séquence.

## Python : fonctions et boucles
On définit une fonction avec `def nom(parametres):` et on renvoie une valeur avec `return`. Une fonction sans `return` renvoie `None`. `for x in liste:` parcourt une séquence ; `range(5)` produit 0, 1, 2, 3, 4. Une fonction récursive s'appelle elle-même et doit avoir un cas de base pour s'arrêter.

## Complexité des algorithmes
La notation O décrit la croissance du temps de calcul quand la taille n des données augmente. Parcourir un tableau : O(n). Recherche dichotomique dans un tableau trié : O(log n), car on coupe l'intervalle en deux à chaque étape. Tri fusion et tri par tas : O(n log n). Tri à bulles, tri par insertion et tri par sélection : O(n²) dans le pire des cas. Accès à un élément d'un tableau par son indice : O(1).

## Structures de données
Une pile (stack) suit le principe LIFO : dernier entré, premier sorti (comme une pile d'assiettes). Une file (queue) suit le principe FIFO : premier entré, premier sorti. Listes chaînées, piles et files sont des structures linéaires. Les arbres et les graphes ne sont pas linéaires. Une table de hachage (dict en Python) donne un accès moyen en O(1) par clé.

## Binaire
Un bit vaut 0 ou 1. Sur n bits on code 2^n valeurs : 8 bits (un octet) donnent 256 valeurs, de 0 à 255. Pour convertir 1010 en décimal : 1×8 + 0×4 + 1×2 + 0×1 = 10.

## Web : HTML, CSS, HTTP
HTML (HyperText Markup Language) décrit la structure d'une page, CSS sa présentation (la propriété `color` change la couleur du texte, `background-color` celle du fond), JavaScript son comportement. HTTP est le protocole d'échange : 200 = succès, 301 = redirection permanente, 404 = ressource introuvable, 500 = erreur du serveur, 401 = non authentifié, 403 = interdit.

## SQL
SELECT lit des lignes, INSERT en ajoute, UPDATE les modifie, DELETE les supprime. WHERE filtre les lignes avant un regroupement, GROUP BY regroupe, HAVING filtre les groupes après regroupement, ORDER BY trie. Une clé primaire identifie une ligne de façon unique ; une clé étrangère référence une autre table.

## Sécurité des applications
Pour se protéger des injections SQL, il faut utiliser des requêtes paramétrées (marqueurs `?`), jamais en concaténant les saisies de l'utilisateur dans la requête. Un mot de passe ne doit jamais être stocké en clair : on stocke un hash lent et salé (PBKDF2, bcrypt, scrypt ou Argon2), pour qu'une fuite de la base ne révèle pas les mots de passe. Le sel est aléatoire et propre à chaque compte, il empêche les tables précalculées. L'OWASP recommande 600 000 itérations pour PBKDF2-HMAC-SHA256.

## Variables et types
Une variable est un nom qui désigne une valeur rangée en mémoire : `age = 18` crée la variable age et lui donne la valeur 18. En Python, on n'écrit pas le type : il est déduit de la valeur (int pour 18, str pour "bonjour", bool pour True). On peut changer la valeur d'une variable à tout moment (`age = age + 1`). Un bon nom de variable dit ce qu'elle contient.

## Conditions et boucles en détail
`if condition:` exécute un bloc seulement si la condition est vraie ; `elif` et `else` traitent les autres cas. Une boucle `for` répète un bloc pour chaque élément d'une séquence : `for i in range(3): print(i)` affiche 0, 1, 2. Une boucle `while condition:` répète tant que la condition reste vraie ; il faut que quelque chose change dans la boucle, sinon elle ne s'arrête jamais (boucle infinie). En Python, c'est l'indentation (les espaces en début de ligne) qui délimite les blocs.

## Programmation orientée objet
Une classe est un modèle (par exemple Voiture) ; un objet est un exemplaire créé à partir de ce modèle. Les attributs sont les données de l'objet (couleur, vitesse), les méthodes sont ses fonctions (accélérer). L'héritage permet à une classe de reprendre et compléter une autre classe.

## Ressources pour aller plus loin
- Tutoriel officiel Python (en français) : https://docs.python.org/fr/3/tutorial/
- MDN Web Docs (HTML, CSS, JavaScript, HTTP) : https://developer.mozilla.org/fr/
- SQLBolt, exercices SQL interactifs : https://sqlbolt.com
- OWASP, stockage des mots de passe : https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
- France-IOI, algorithmique progressive : https://www.france-ioi.org
