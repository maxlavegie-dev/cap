# Journal de bord - Projet Cap

Ce fichier dit à tout moment où en est le projet. Il est mis à jour après chaque étape.

---

## Où on en est

**Étape actuelle :** Lot 3 (fenêtre « Ajouter une tâche ») publié le 29/10/2026, à essayer sur le téléphone.

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
- 28/10/2026 : connexion Google publiée et essayée par Max : tableau créé, faux rendez-vous affichés, ajouts et coches arrivés. Des tâches n'arrivaient pas après l'expiration de l'autorisation (environ 1 h).
- 28/10/2026 : corrigé et publié : alerte visible quand Google coupe l'accès, bouton « Redonner l'accès à Google », reconnexion silencieuse, envoi automatique des tâches en attente. Max a vu l'alerte sur son téléphone et a pu redonner l'accès : PRIORITÉ N° 1 REMPLIE.
- 28/10/2026 : publiés : accueil épuré, recherche tapée (tâches et rendez-vous), dernières actions avec l'heure, indicateur d'envois en attente et « Synchroniser maintenant », fiche de rendez-vous (affichage, modification, « Appeler », « Écrire »). Max est content ; ses remarques viendront plus tard.
- 29/10/2026 : vérifications automatiques réparées : deux essais étaient faux depuis l'arrivée de la fiche de rendez-vous (le fichier était chargé deux fois dans les essais, et un essai attendait l'ancien comportement).
- 29/10/2026 : LOT 1 construit (sauvegarde `sauvegarde-avant-lot1-accueil-20261029`) : l'heure disparaît de l'accueil ; la date reste en haut, centrée, un peu plus grosse ; une seule longue barre de recherche en bas, juste au-dessus des boutons, avec à gauche un petit menu qui affiche toujours le choix en cours (« Tâches ▾ ») ; les résultats arrivent pendant la frappe et s'affichent au-dessus de la barre, dans l'espace libre. Barre du haut du téléphone : Cap installée est en mode « standalone », qui garde la barre du téléphone (heure, réseau, batterie) visible ; la date est placée en dessous. 183 vérifications automatiques réussies.
- 29/10/2026 : Lot 1 publié par Max et validé sur son téléphone, sauf le rendez-vous dicté avec rappel.
- 29/10/2026 : DÉFAUT trouvé et corrigé : un rendez-vous dicté répondait « ajouté » mais n'allait dans aucun agenda. Cause : sans cerveau, Cap transformait toute demande en tâche « À trier » (le « Atrier » vu par Max était le message « Ajoutée dans À trier »). Correction : un nouveau fichier (`comprendre_demande.js`) reconnaît, sans IA, une demande de rendez-vous (date, heure, titre, rappels) et ouvre une fiche « Nouveau rendez-vous » préremplie ; Max vérifie, puis confirme, et le rendez-vous est créé dans l'agenda « Cap – FICTIF » seulement, avec le rappel en notification Google Agenda. Sans connexion, Cap le dit honnêtement et le note en tâche. Aucune nouvelle autorisation Google.
- 29/10/2026 : LOT 2 construit (sauvegarde `sauvegarde-avant-lot2-20261029`) : les tâches cochées sortent de la liste et vont dans une ligne repliée « Terminées (N) » tout en bas ; un appui l'ouvre, décocher remet la tâche dans sa catégorie. Glisser une tâche vers la droite la coche, vers la gauche la reporte à demain, avec « Annuler » pendant 8 secondes. « Reporter à demain » aussi dans le menu « … », et à la voix (« Reporte ça à demain ») pour la dernière tâche ouverte. 193 vérifications automatiques réussies. Publié le 29/10/2026 avec l'accord de Max.
- 29/10/2026 : Lot 2 validé par Max.
- 29/10/2026 : LOT 3 construit (sauvegarde `sauvegarde-avant-lot3-20261029`), fenêtre « Ajouter une tâche » :
  - **Dates** : « Échéance » et « Avant le » se choisissent avec trois menus (jour, mois, année, l'année en cours en premier). Au-dessus, quatre boutons : Aujourd'hui, Demain, Ce week-end, Semaine prochaine. Un bouton « Dire la date » permet de dicter (« vendredi »), et un bouton « Effacer » vide la date. La date reste vide tant que Max ne la choisit pas ; une date impossible (31 février) est refusée.
  - **Catégorie** : plus de clavier. Un appui ouvre de gros boutons de couleur : « À trier » toujours en premier, puis les plus utilisées. Un appui sur une catégorie ouvre ses sous-catégories, en boutons aussi. « Ajouter » et « Modifier » marchent aux deux niveaux. Chaque catégorie a sa couleur, visible dans la liste (trait coloré devant le titre).
  - **Étapes par défaut** : le menu gagne « Ajouter… » et « Modifier la liste… » (cases à cocher, bouton « Retirer (N) »).
  - **Rien n'est effacé** : ce qui est retiré reste dans le tableau, marqué avec la date, avec « Annuler » pendant 8 secondes et un bouton « Remettre ».
  - **Tableau** : nouvel onglet « Catégories » (nom, sous-catégorie de, couleur, retirée le), et l'onglet « Étapes par défaut » est maintenant relu par Cap. Aucune nouvelle autorisation Google.
  - 202 vérifications automatiques réussies. Publié le 29/10/2026 avec l'accord de Max.
- 29/10/2026 : Max valide les boutons rapides de dates. Corrections avant le Lot 4 (sauvegarde `sauvegarde-avant-lot4-20261029`) :
  - **Date en toutes lettres** : sous les trois menus, une ligne « lundi 2 novembre 2026 » se met à jour toute seule (boutons, menus ou voix) ; vide si la date est vide.
  - **« Dire la date »** : écoute rendue plus solide. Cap affiche « Je t'écoute », montre ce qu'il entend pendant que Max parle, garde ce texte si le téléphone n'envoie pas de résultat final, relance l'écoute une fois s'il n'a rien entendu, et explique clairement si le micro est bloqué ou s'il manque internet. La cause exacte du défaut n'a pas pu être vue sans le téléphone : à vérifier par Max avec « vendredi », « demain » et « le 15 novembre ».
  - **Petites fenêtres** : on les ferme en touchant à côté, ce qui ramène à la fenêtre d'avant ; les boutons Fermer/Retour/Annuler qui servaient seulement à sortir ont disparu. Fenêtre vide : elle se ferme tout de suite. Texte déjà écrit : question « Garder » (le texte revient à la prochaine ouverture), « Jeter » (avec « Annuler » pendant 8 secondes) ou « Continuer ». Le geste retour du téléphone marche comme avant. La fenêtre « Abandonner cette tâche ? » garde son bouton Annuler (c'est une réponse), et la fiche de rendez-vous garde son bouton Retour (c'est une fiche complète, pas une petite fenêtre).
  - 205 vérifications automatiques réussies. Publié le 29/10/2026 avec l'accord de Max.
- 29/10/2026 : Lot 4 construit (sauvegarde `sauvegarde-avant-lot4-tuiles-20261029`) :
  - **Tuiles** : l'écran complet montre des tuiles carrées avec compteur. D'abord les tuiles fixes (Dernières actions, Prochains rendez-vous, Aujourd'hui, Trier), puis À trier, puis les catégories de Max, et enfin Tout, + Ajouter et Modifier. « ‹ Tuiles » permet de revenir. Les catégories sont les mêmes que dans « Ajouter une tâche ».
  - **Micro sur chaque tuile de catégorie** : la tâche dictée va directement dans cette catégorie.
  - **Ordre au doigt** : appui long (une demi-seconde) puis glissement. L'ordre est gardé dans la colonne « Ordre » de l'onglet Catégories. À trier reste en tête et les tuiles fixes ne bougent pas.
  - **Mode Trier** : une tâche à trier à la fois. Max touche une catégorie ou la dit à la voix, ou appuie sur « Passer ». « Annuler » reste affiché 8 secondes. Rien n'est effacé.
  - **Aide** : bouton en haut à droite de l'écran complet (décidé par Max). Il ouvre 8 gestes expliqués, chacun avec une petite démonstration animée. On le ferme en touchant à côté.
  - **Journal de toutes les actions** : il est écrit dans un nouvel onglet « Journal » (heure à la seconde, ce que Max a dit ou touché, ce que Cap a compris, ce que Cap a fait). Les mots de passe et les longs numéros sont masqués. Rien n'est jamais effacé. Hors connexion, les lignes attendent et partent ensuite.
  - **Sauvegarde du tableau** : bouton « Sauvegarder maintenant ». La copie datée va dans le dossier Drive des sauvegardes. Ensuite, une copie automatique chaque semaine, mais seulement après la première. Aucune copie n'est supprimée sans l'accord de Max. Pas de nouvelle autorisation Google : le droit déjà donné sur les fichiers créés par Cap suffit.
  - 215 vérifications automatiques réussies. Publié le 29/10/2026 avec l'accord de Max.
- 29/10/2026 : Max valide tout le Lot 4 sur son téléphone. Lot 5, demande 1 (toutes les façons de dire une date) :
  - **Nouveau moteur de dates** (`comprendre_dates.js`) : dans N jours, semaines, mois ou ans (même jour de la semaine pour les semaines) ; « vendredi dans deux semaines » ; « lundi en huit », « mardi en quinze » ; « la semaine prochaine, mercredi » ; « le premier lundi du mois prochain », « le dernier vendredi de novembre » ; fin du mois, du mois prochain, de l'année ; après-demain ; dates en chiffres ou en lettres.
  - **Pas de devinette** : si deux dates sont possibles (« jeudi » dit un jeudi, « vendredi prochain » dit un jeudi, « dans 8 jours », « fin de semaine »), Cap pose une question avec deux gros boutons. Si Max ferme la question, rien n'est inventé.
  - **Partout** : bouton « Dire la date », dictée principale (la tâche reçoit son échéance, l'intitulé reste mot pour mot), micro des tuiles, et rendez-vous dictés.
  - 218 vérifications automatiques réussies. Pas encore publié : à tester par Max.

### En cours
- Lot 5, demande 1 (dates) : construite, à tester par Max. Ensuite, demande 2 (dictée dans une catégorie à sous-catégories, avec « À classer »), puis demande 3 (« + Ajouter » et « Modifier » dans les écrans de choix de catégorie), une à la fois.
- Plus tard : mode conversation continue (pas commencé).

### À faire (semaine 1)
- Jours 1 et 2 : dessiner l'icône et l'écran d'accueil. FAIT.
- Jours 3 et 4 : la liste de tâches (ajouter, cocher, supprimer). FAIT, validé par Max.
- Jours 5 et 6 : la dictée à la voix pour ajouter une tâche toute seule. FAIT, essayée avec le vrai micro.
- Jour 7 : essai sur le téléphone de Max. FAIT (installation, liste, dictée, mode avion). Premier bilan FAIT.

---

## Décisions prises
- 29/10/2026 : à la demande de Max (Lot 2), les tâches cochées ne restent plus dans leur catégorie : elles vont dans la ligne repliée « Terminées (N) ». Rien n'est effacé : la tâche garde sa date et sa catégorie, et décocher la remet à sa place. Cela remplace le choix du 28/10 (« les tâches cochées restent dans leur catégorie »).
- 29/10/2026 : un rendez-vous dicté n'est jamais ajouté directement : Cap ouvre une fiche préremplie que Max vérifie et confirme. Déplacer un rendez-vous à la voix n'est pas encore géré (Cap le dit et propose « Modifier »).
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
- 29/10/2026 : LOT 2, liste de tâches : d'abord régler le rendez-vous dicté avec rappel (rien n'arrivait dans l'agenda, « Atrier » affiché, droit aux notifications à vérifier) ; tâches cochées regroupées dans une ligne repliée « Terminées (N) » en bas ; glisser à droite pour cocher, à gauche pour reporter à demain, aussi à la voix, avec « Annuler ».
- 29/10/2026 : LOT 1, écran d'accueil : plus d'heure dans Cap (la barre du téléphone la montre déjà, comme dans Google Agenda) ; date seule en haut, centrée, un peu plus grosse ; une seule barre de recherche en bas, au-dessus du micro et des trois boutons, facile à atteindre d'une main, avec le petit menu des sources intégré à gauche et toujours visible ; résultats pendant la frappe, affichés au-dessus de la barre. Également : gestion des premiums annoncée à chaque séance (15 % gardés en réserve ; la publication est faite par Max lui-même).
- 28/10/2026 : COMPLÉMENT 4 (texte complet : `PROMPT_COMPLEMENT_4.txt`) : mode conversation continue (appui long d'environ 2 s sur le micro, vibration et son doux grave à l'entrée et à la sortie, micro allumé bien visible, sortie par un appui ou seule après 3 minutes de silence, test batterie) ; conversation en arrière-plan pendant l'usage d'autres applis ; alerte quand Google refuse ou expire (priorité n° 1) ; nouvelle règle de travail ; compte rendu à chaque étape ; sauvegarde avant les grosses modifications.
- 28/10/2026 : après l'essai Google (texte complet : `PROMPT_COMPLEMENT_ACCUEIL_RDV.txt`) : écran d'accueil épuré (jour, heure, barre de recherche, boutons du bas ; un glissement vers le haut montre l'écran complet) ; texte un peu plus gros sauf l'heure ; recherche tapée sans IA (tâches et rendez-vous, autres sources grisées) ; dernières actions avec l'heure ; fiche de rendez-vous cliquable et modifiable (adresse, téléphone « Appeler », mail « Écrire », « Itinéraire », notes, rappel affiché ET vraie notification) ; indicateur des envois en attente et bouton « Synchroniser maintenant » ; animations douces gardées pour la toute fin.
- 28/10/2026 : CLAVIER DE PHRASES (texte complet : `PROMPT_COMPLEMENT_CLAVIER.txt`). Pour utiliser Cap sans parler : des débuts de phrases tout prêts (« Retrouve-moi... ») à compléter, une saisie libre, un interrupteur « réponse silencieuse », un historique des demandes à relancer, de gros boutons. Les phrases sont rangées dans le Drive de Max, modifiables sans code, et les plus utilisées remontent toutes seules. Plan validé par Max et construit le 28/10/2026. Reste pour plus tard : phrases dans le Drive (semaine 2), placement définitif, phrases pour les personnes fréquentes, et les deux idées à tester (mode « je ne peux pas parler », phrases selon le moment de la journée).
