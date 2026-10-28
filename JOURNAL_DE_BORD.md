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

### En cours
- Préparation de la semaine 2 : connexion à Google (Sheets, Agenda, Gmail) et briefing du matin.

### À faire (semaine 1)
- Jours 1 et 2 : dessiner l'icône et l'écran d'accueil. FAIT.
- Jours 3 et 4 : la liste de tâches (ajouter, cocher, supprimer). FAIT, validé par Max.
- Jours 5 et 6 : la dictée à la voix pour ajouter une tâche toute seule. FAIT, essayée avec le vrai micro.
- Jour 7 : essai sur le téléphone de Max. FAIT (installation, liste, dictée, mode avion). Premier bilan FAIT.

---

## Décisions prises
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
(aucun pour l'instant)
