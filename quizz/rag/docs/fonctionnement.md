# Fonctionnement de MyKwizz

## Jouer un quizz
Sur l'accueil, choisis un quizz (tu peux filtrer par thème : Culture générale, Code, Histoire, Mathématiques, Physique-Chimie, SVT, Géographie…). La plupart des quizz ont une minuterie : quand le temps est écoulé, ta partie est corrigée automatiquement. Les touches 1 à 9 cochent les réponses. Une question peut avoir plusieurs bonnes réponses : elle est juste seulement si tu coches exactement toutes les bonnes.

## Score, historique et classement
Après la correction, tu vois ton score et le corrigé. « Mon espace » montre ton historique, ta réussite par thème et te permet de changer ton mot de passe. Le classement d'un quizz garde le meilleur score de chaque joueur ; à égalité, celui qui l'a atteint en premier est devant.

## L'assistant
L'assistant répond à tes questions sur les thèmes des quizz à partir de fiches de cours, et cite les fiches utilisées. Il ne donne pas les réponses d'un quizz en cours : termine d'abord ta partie, puis demande-lui de t'expliquer.

## Comptes et sécurité
Un mot de passe doit contenir au moins 8 caractères, dont une lettre et un chiffre. Il n'est jamais stocké en clair, seulement son empreinte (PBKDF2). Après 3 essais ratés, la connexion est bloquée 30 secondes.
