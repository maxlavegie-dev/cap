# Journal de bord - Projet Cap

Ce fichier dit à tout moment où en est le projet. Il est mis à jour après chaque étape.

---

## Où on en est

**Étape actuelle :** préparation de la semaine 1 (rien n'est encore programmé).

### Fait
- 27/10/2026 : cahier des charges de Max rangé dans le projet (`PROMPT_CAP.txt`).
- 27/10/2026 : fiche des règles pour les assistants créée (`AGENTS.md`).
- 27/10/2026 : journal de bord créé (ce fichier).
- 27/10/2026 : premier essai d'icône « vague calme » (`icone/icone_cap_essai1.png`).
- 27/10/2026 : première maquette de l'écran d'ouverture (dossier `app/`), avec 9 tâches fictives. Écrite par un subagent, relue et vérifiée. Cocher ne sauvegarde rien pour l'instant, et le micro affiche seulement « La dictée arrivera bientôt ».
- 27/10/2026 : Max valide la maquette de l'écran d'ouverture.
- 28/10/2026 : liste de tâches fabriquée (jours 3 et 4) : ajouter (bouton +), cocher, abandonner/remettre, étapes par défaut, ajout d'une étape sur un seul titre, avancement, jours restants, sauvegarde sur le téléphone. Écrite par un subagent, relue par le modèle principal : 16 vérifications automatiques réussies et capture d'écran contrôlée.
- 28/10/2026 : fichier d'explications créé (`EXPLICATIONS.md`).
- 28/10/2026 : Max valide la liste de tâches pour l'instant.
- 28/10/2026 : dictée à la voix fabriquée (jours 5 et 6). La tâche dictée est ajoutée tout de suite, mot pour mot, dans une catégorie « À trier », avec un bouton « Annuler » (8 secondes) qui l'abandonne (zéro perte). Le classement automatique viendra avec l'intelligence artificielle. Écrite par un subagent, relue par le modèle principal : 36 vérifications automatiques réussies (avec un micro simulé).
- 28/10/2026 : Max a un compte GitHub.
- 28/10/2026 : Cap est rendu installable sur Android : carte d'identité (manifest), icônes aux bonnes tailles, copie hors connexion (lecture de la dernière version). 46 vérifications automatiques réussies. Pas encore essayé sur un vrai téléphone.
- 28/10/2026 : Max accepte que le code soit public sur GitHub. Le cahier des charges (`PROMPT_CAP.txt`) est exclu de la publication car il contient des informations personnelles.
- 28/10/2026 : Cap est en ligne : https://maxlavegie-dev.github.io/cap/app/ (dépôt https://github.com/maxlavegie-dev/cap, compte GitHub `maxlavegie-dev`).
- 28/10/2026 : Max a installé Cap sur son téléphone Android : l'installation fonctionne. L'ajout avec le bouton + fonctionne.
- 28/10/2026 : PROBLÈME : sur le téléphone, le micro affiche « La dictée n'est pas disponible dans ce navigateur ». Le navigateur utilisé ne fournit pas la reconnaissance vocale (piste : pas Chrome). Cause trouvée : Cap avait été installé depuis le navigateur Qwant, qui n'a pas de reconnaissance vocale. Solution : réinstaller Cap depuis Chrome. À savoir : chaque navigateur garde sa propre liste, la liste de la version Qwant ne passe pas dans Chrome (ce sera réglé en semaine 2 avec Google Sheets).
- 28/10/2026 : Cap réinstallé depuis Chrome : la dictée avec le vrai micro fonctionne sur le téléphone de Max.
- 28/10/2026 : essai en mode avion réussi : Cap s'ouvre, la liste est consultable, et la dictée marche même sans internet (le téléphone de Max reconnaît la voix sur place).
- 28/10/2026 : premier bilan de la semaine 1 : Max est satisfait, rien ne le gêne ni ne lui manque pour l'instant. Semaine 1 terminée.
- 28/10/2026 : Max valide le plan d'intégration du clavier de phrases, à construire avant la connexion à Google.
- 28/10/2026 : clavier de phrases construit (bouton clavier à droite du micro, panneau qui monte du bas) : 11 débuts de phrases en 4 catégories, saisie libre, « Les plus utilisées », « Dernières demandes » à relancer, interrupteur « Réponse silencieuse » (allumé par défaut ; Cap ne parle pas encore). Micro et clavier passent par la même porte d'entrée. Sans cerveau, tout va dans « À trier » mot pour mot ; « Ajoute à ma to-do... » ne garde que la fin de la phrase ; « Continue. » et « Annule. » attendront le cerveau. Écrit par un subagent, relu par le modèle principal : 67 vérifications automatiques réussies. Pas encore publié ni essayé sur le téléphone.
- 28/10/2026 : clavier de phrases publié, essayé sur le téléphone et validé par Max.
- 28/10/2026 : Max a créé dans Google Cloud le « Projet Cap » : Sheets, Drive et Agenda activés, écran de consentement en mode test (non publié), Max seul utilisateur testeur, client OAuth web créé. Le fichier JSON du client est gardé par Max hors du projet. Le code secret du client n'est PAS utilisé par Cap (appli sans serveur) : il ne doit jamais aller dans le projet ni dans une conversation. Origine à autoriser : https://maxlavegie-dev.github.io ; adresse de redirection : https://maxlavegie-dev.github.io/cap/app/
- 28/10/2026 : Max a donné l'identifiant client (public, ce n'est pas un secret). Il est rangé dans `app/reglages_google.js`, avec les noms du fichier et de l'agenda FICTIF. Ce fichier n'est pas encore utilisé par l'appli.
- 28/10/2026 : connexion Google construite (pas encore publiée ni essayée avec le vrai compte). Un bouton « Se connecter à Google » est placé en haut de la liste (le haut de l'écran reste date et heure). Cap crée le tableau « Cap – FICTIF – Tâches » (onglets Tâches, Étapes par défaut, Phrases du clavier) et l'agenda séparé « Cap – FICTIF » avec 4 faux rendez-vous. La liste suit le tableau ; hors connexion, les changements attendent et partent au retour. Aucune ligne n'est jamais effacée ; une ligne du tableau illisible est laissée intacte et signalée. Les prochains rendez-vous s'affichent au-dessus de la liste. Pour l'instant, les onglets Étapes par défaut et Phrases du clavier sont seulement écrits : l'appli ne les relit pas encore. Écrit par un subagent, relu par le modèle principal : 86 vérifications automatiques réussies (Google simulé).

### En cours
- Semaine 2, étape 1 : autorisation Google de Cap. FAIT.
- Semaine 2, étape 2 : connexion Google construite, publiée et essayée par Max le 28/10/2026 : « synchronisé », faux rendez-vous affichés, tableau créé, ajouts et coches arrivés en 2 à 3 minutes. PROBLÈME : plusieurs tâches (dont « sushis », dictée avec internet, et « Terminator », dictée en mode avion) ne sont jamais arrivées dans le tableau. Piste principale : l'autorisation Google expire au bout d'environ une heure ; ensuite Cap garde les tâches en attente sans le dire assez clairement. Plan de correction présenté à Max, en attente de son accord.

### À faire (semaine 1)
- Jours 1 et 2 : dessiner l'icône et l'écran d'accueil. FAIT.
- Jours 3 et 4 : la liste de tâches (ajouter, cocher, supprimer). FAIT, validé par Max.
- Jours 5 et 6 : la dictée à la voix pour ajouter une tâche toute seule. FAIT, essayée avec le vrai micro.
- Jour 7 : essai sur le téléphone de Max. FAIT (installation, liste, dictée, mode avion). Premier bilan FAIT.

---

## Décisions prises
- 28/10/2026 : plan de la semaine 2 validé par Max : liste dans un Google Sheets « Cap – FICTIF – Tâches » (accès limité aux seuls fichiers créés par Cap), agenda séparé « Cap – FICTIF » (Cap ne lit pas le vrai agenda), copie sur le téléphone et file d'attente hors connexion, aucune ligne jamais effacée. Briefing (besoin de la clé API) et Gmail repoussés à l'étape suivante.
- 28/10/2026 : NOUVELLE RÈGLE DE TRAVAIL (Complément 4, remplace la précédente) : tant que tout est fictif, l'assistant avance seul et fait un compte rendu court à chaque étape (fait + à tester). Il s'arrête et demande l'accord de Max avant : toute autorisation Google nouvelle ou élargie, tout accès aux vraies données, tout envoi de mail, toute publication. Sauvegarde avant chaque grosse modification.
- 28/10/2026 : plan « accueil, recherche, rendez-vous » validé par Max, avec deux choix : rappel par Google Agenda (uniquement sur l'agenda FICTIF tant que Max n'a pas donné son accord) ; zone « Dernières actions » en haut au lieu de déplacer les tâches (les tâches cochées restent dans leur catégorie).
- 28/10/2026 : PRIORITÉ N° 1 (Complément 4) : ne plus jamais rester silencieux quand Google refuse ou que la connexion expire : alerte visible, fenêtre Google en un geste, envoi automatique des tâches en attente une fois l'autorisation revenue.
- 28/10/2026 : ancienne règle (remplacée) : présenter le plan et attendre l'accord avant d'agir.
- 27/10/2026 : Max valide le plan de la semaine 1 tel qu'il est écrit dans le cahier des charges.
- 27/10/2026 : Max accepte la tenue de ce journal de bord.
- 27/10/2026 : la semaine 1 n'utilise pas encore de clé d'intelligence artificielle. La dictée passe d'abord par la reconnaissance vocale gratuite du téléphone.
- 27/10/2026 : Max choisit l'idée d'une vague calme à l'horizon pour l'icône.
- 27/10/2026 : Max valide l'icône `icone/icone_cap_essai1.png` (ciel pêche, mer turquoise et bleue).
- 27/10/2026 : écran d'ouverture de la semaine 1 validé par Max : en haut, seulement la date du jour et l'heure (PAS le mot « Cap ») ; au milieu, la liste de tâches avec cases à cocher ; en bas, un gros bouton micro. Couleurs de l'icône.
- 27/10/2026 : organisation de la liste de tâches validée par Max :
  1. une seule grande liste, une ligne par tâche (règle « zéro perte ») ;
  2. chaque ligne a sa catégorie et sa sous-catégorie, et une étape peut indiquer la tâche dont elle fait partie (« tâche parente ») ;
  3. une fiche à part contient les « étapes par défaut » (ex. pour un titre d'album : réenregistrer les voix, mixer, masteriser). Cap les crée tout seul quand on ajoute un titre, et on peut ensuite en ajouter ou en retirer sur un seul titre ;
  4. Cap calcule lui-même l'avancement (ex. « 2 étapes sur 4 », « Album A : 60 % »), sans formule à écrire ;
  5. une simple idée reste une simple ligne, sans étape.
  En semaine 1, la liste est gardée sur le téléphone. En semaine 2, elle passe sur Google Sheets avec la même organisation.
- 27/10/2026 : « supprimer » ne veut jamais dire effacer. La tâche est marquée « abandonnée » avec la date, après confirmation de Max. Elle sort de la vue de tous les jours mais reste gardée, et on peut la retrouver ou la remettre à tout moment.
- 27/10/2026 : colonnes facultatives de la version 1 : « Avant le », « Abandonnée le », « Origine », « Fictif ». Les jours restants sont calculés par Cap, sans colonne. Plus tard : lien, personne, montant, récurrence, dépendance.

---

## Questions en attente
- Clé API créée chez le fournisseur, avec un plafond de dépense mensuel (pas nécessaire avant la semaine 2).

---

## Ajouts de Max en cours de route
- 28/10/2026 : COMPLÉMENT 4 (texte complet : `PROMPT_COMPLEMENT_4.txt`) : mode conversation continue (appui long d'environ 2 s sur le micro, vibration et son doux grave à l'entrée et à la sortie, micro allumé bien visible, sortie par un appui ou seule après 3 minutes de silence, test batterie) ; conversation en arrière-plan pendant l'usage d'autres applis ; alerte quand Google refuse ou expire (priorité n° 1) ; nouvelle règle de travail ; compte rendu à chaque étape ; sauvegarde avant les grosses modifications.
- 28/10/2026 : après l'essai Google (texte complet : `PROMPT_COMPLEMENT_ACCUEIL_RDV.txt`) : écran d'accueil épuré (jour, heure, barre de recherche, boutons du bas ; un glissement vers le haut montre l'écran complet) ; texte un peu plus gros sauf l'heure ; recherche tapée sans IA (tâches et rendez-vous, autres sources grisées) ; dernières actions avec l'heure ; fiche de rendez-vous cliquable et modifiable (adresse, téléphone « Appeler », mail « Écrire », « Itinéraire », notes, rappel affiché ET vraie notification) ; indicateur des envois en attente et bouton « Synchroniser maintenant » ; animations douces gardées pour la toute fin.
- 28/10/2026 : CLAVIER DE PHRASES (texte complet : `PROMPT_COMPLEMENT_CLAVIER.txt`). Pour utiliser Cap sans parler : des débuts de phrases tout prêts (« Retrouve-moi... ») à compléter, une saisie libre, un interrupteur « réponse silencieuse », un historique des demandes à relancer, de gros boutons. Les phrases sont rangées dans le Drive de Max, modifiables sans code, et les plus utilisées remontent toutes seules. Plan validé par Max et construit le 28/10/2026. Reste pour plus tard : phrases dans le Drive (semaine 2), placement définitif, phrases pour les personnes fréquentes, et les deux idées à tester (mode « je ne peux pas parler », phrases selon le moment de la journée).
