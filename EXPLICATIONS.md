# Cap - Explications du code

Ce fichier explique en français simple comment Cap est fabriqué. Il est mis à jour à chaque étape.

## Le dossier du projet
- `PROMPT_CAP.txt` : le cahier des charges de Max.
- `JOURNAL_DE_BORD.md` : où on en est, les décisions prises et les questions en attente.
- `AGENTS.md` : les règles à respecter par les assistants qui programment.
- `icone/` : l'icône de Cap (une vague calme).
- `app/` : l'application elle-même.

## L'application (dossier `app/`)
C'est une page web qui pourra s'installer sur le téléphone comme une vraie application. Chaque fichier a un seul rôle :

| Fichier | Rôle |
|---|---|
| `index.html` | La structure de l'écran : la date seule en haut, la barre de recherche en bas juste au-dessus des boutons + , micro et clavier, l'écran complet (liste, rendez-vous, dernières actions) qui s'ouvre d'un glissement vers le haut, et les petites fenêtres (menu, confirmation, ajout, fiche de rendez-vous). |
| `style.css` | L'apparence : les couleurs de l'icône, la taille des textes et des boutons. |
| `donnees_fictives.js` | Des tâches INVENTÉES pour les essais. Ce fichier sera supprimé d'un coup à la bascule. |
| `etapes_par_defaut.js` | Les réglages des étapes créées automatiquement (ex. pour un titre d'album : réenregistrer les voix, mixer, masteriser). On peut les modifier sans toucher au reste. |
| `stockage.js` | Garde la liste sur le téléphone. Il sera remplacé par Google Sheets en semaine 2. |
| `taches.js` | Les règles de la liste : ajouter, cocher, abandonner, remettre, calculer l'avancement et les jours restants. |
| `reglages_google.js` | Les réglages Google : l'identifiant client (public, ce n'est pas un secret), l'adresse de retour, les noms du tableau et de l'agenda FICTIF. |
| `google_connexion.js` | Le bouton « Se connecter à Google » : demande l'accord de Max à Google et garde l'autorisation environ une heure. |
| `google_sheets.js` | Trouve ou crée le tableau « Cap – FICTIF – Tâches » et y écrit les tâches. Ne supprime jamais une ligne. |
| `google_agenda.js` | Trouve ou crée l'agenda séparé « Cap – FICTIF » et lit les prochains rendez-vous. Ne touche jamais au vrai agenda. |
| `synchronisation.js` | Met d'accord le téléphone et le tableau. Hors connexion, les changements attendent dans une file et partent au retour. |
| `dictee.js` | Écoute ce que Max dit, avec la reconnaissance vocale du navigateur, et transmet le texte entendu. |
| `phrases_clavier.js` | Les réglages des débuts de phrases du clavier. Ils iront dans le Drive en semaine 2. |
| `preferences_clavier.js` | Retient sur le téléphone les phrases les plus utilisées, les dernières demandes et l'interrupteur « Réponse silencieuse ». |
| `comprendre_demande.js` | Comprend, sans intelligence artificielle, une demande de rendez-vous (date, heure, titre, rappels) ou « Reporte ça à demain ». Ne fait rien lui-même : il prépare seulement un brouillon. |
| `demandes.js` | La porte d'entrée unique de toutes les demandes (micro et clavier). C'est là qu'on branchera l'intelligence artificielle. |
| `recherche.js` | La recherche tapée, sans intelligence artificielle : trouve un mot dans les tâches ou les rendez-vous, sans tenir compte des accents ni des majuscules. |
| `journal_actions.js` | Retient sur le téléphone les dernières actions (ajout, coche, abandon) avec leur heure. |
| `fiche_rendezvous.js` | La fiche d'un rendez-vous : détails, boutons « Appeler » et « Écrire », modification avec récapitulatif avant de confirmer. Ne touche que l'agenda « Cap – FICTIF ». |
| `listes_choix.js` | Les listes de catégories (avec leurs couleurs et sous-catégories) et d'étapes par défaut. Retirer n'efface rien : l'élément est marqué avec la date et peut être remis. |
| `synchro_listes.js` | Recopie ces listes dans le tableau (onglets « Catégories » et « Étapes par défaut ») et relit ce qui s'y trouve. |
| `choix_dates.js` | Les dates en trois menus (jour, mois, année), avec les boutons Aujourd'hui, Demain, Ce week-end, Semaine prochaine, et la date dictée. |
| `fenetres_listes.js` | Les fenêtres en gros boutons pour choisir une catégorie, et pour ajouter, retirer ou remettre une catégorie ou des étapes par défaut. |
| `app.js` | L'affichage à l'écran et ce qui se passe quand on touche un bouton. |
| `manifest.webmanifest` | La carte d'identité de l'appli pour le téléphone : nom, couleurs, icônes. Elle permet de l'installer sur l'écran d'accueil. |
| `service-worker.js` | Garde une copie de l'appli sur le téléphone pour qu'elle s'ouvre même sans internet. |
| `installation.js` | Active cette copie hors connexion. |
| `icones/` | L'icône aux différentes tailles demandées par Android. Elles sont fabriquées par `outils/fabriquer_icones.py` à partir de l'icône validée. |
| `test_cap.py` | Des vérifications automatiques des règles, de la dictée, du clavier, de la connexion Google (simulée), de la recherche, de la fiche de rendez-vous, de l'accueil, de la fenêtre d'ajout et de l'installation (202 essais). |

## L'écran d'accueil (Lot 1, 29/10/2026)
- En haut : seulement la date du jour, centrée. Pas d'heure : la barre du haut du téléphone (heure, Wi-Fi, réseau, batterie) reste visible, car Cap installée s'ouvre en mode « standalone » (comme une appli, mais sans cacher cette barre).
- En bas, juste au-dessus des trois boutons : une seule barre de recherche, facile à atteindre d'une main. À gauche dans la barre, un petit menu montre toujours où l'on cherche (« Tâches ▾ », « Rendez-vous ▾ » ; Gmail, Drive, archives et mémoire perso arriveront plus tard).
- Les résultats arrivent pendant la frappe, sans appuyer sur Entrée, et s'affichent au-dessus de la barre, dans l'espace libre entre la date et la barre.
- Un glissement vers le haut ouvre l'écran complet (liste, rendez-vous, dernières actions, état de la synchronisation).

## La fenêtre « Ajouter une tâche » (Lot 3, 29/10/2026)
- Dates : trois menus (jour, mois, année) et quatre boutons rapides. « Ce week-end » donne le samedi qui vient (ou aujourd'hui le week-end) ; « Semaine prochaine » donne le lundi suivant. La date reste vide tant qu'on ne la choisit pas.
- Catégorie : de gros boutons de couleur, « À trier » en premier puis les plus utilisées ; un appui ouvre les sous-catégories.
- Ce qui est retiré (catégorie ou étapes par défaut) reste dans le tableau avec la date ; « Annuler » pendant 8 secondes, puis « Remettre » à tout moment.

## La connexion à Google (semaine 2)
- Cap n'a accès qu'aux fichiers qu'il a créés lui-même, et seulement à son agenda « Cap – FICTIF ». Il ne voit ni le reste du Drive ni le vrai agenda.
- Google affiche « application non vérifiée » : c'est normal, elle est en mode test et Max est le seul utilisateur autorisé.
- L'autorisation dure environ une heure. Ensuite, un bouton « Se reconnecter » apparaît. Aucun secret n'est rangé dans l'appli.
- Qui gagne en cas de différence : le tableau, sauf si le téléphone a un changement pas encore envoyé (le téléphone gagne alors). Rien n'est jamais retiré.
- Si une ligne du tableau est mal remplie (par exemple une date tapée à la main que Google transforme), Cap la laisse telle quelle et le signale.

## Les règles programmées pour la liste
- **Zéro perte** : il n'existe aucun moyen d'effacer une tâche. « Abandonner » la retire de la vue normale, avec la date, mais elle reste gardée et on peut la remettre.
- On ne peut pas modifier l'intitulé d'une tâche existante.
- Cocher enregistre la date de réalisation, et une tâche cochée reste à sa place.
- Si la liste enregistrée devient illisible, Cap en garde une copie de sécurité au lieu de l'écraser.

## La dictée
- On touche le gros micro, on parle, et la tâche est ajoutée tout de suite dans la catégorie « À trier », mot pour mot, sans aucune reformulation.
- Pendant 8 secondes, un bouton « Annuler » permet d'abandonner la tâche (elle reste gardée dans les abandonnées).
- Si la sauvegarde échoue, le texte dicté reste affiché pour pouvoir le recopier.
- Cap doit être installé depuis **Chrome** : certains navigateurs (par exemple Qwant) n'ont pas de reconnaissance vocale, et le micro affiche alors « La dictée n'est pas disponible ».
- À savoir : selon le téléphone, la reconnaissance vocale passe par internet (le son est alors traité par Google) ou se fait directement sur le téléphone. Sur le téléphone de Max, elle marche aussi en mode avion.

## Le clavier de phrases (ajout de Max du 28/10/2026)
Pour utiliser Cap sans parler (détail dans `PROMPT_COMPLEMENT_CLAVIER.txt`).
- Le bouton clavier, à droite du micro, ouvre un panneau qui monte du bas de l'écran.
- On touche un début de phrase (« Retrouve-moi... »), on écrit la fin, puis « Envoyer ». On peut aussi écrire n'importe quoi dans le champ, sans phrase.
- « Les plus utilisées » remontent toutes seules ; « Dernières demandes » permet de relancer une demande telle quelle.
- L'interrupteur « Réponse silencieuse » est allumé par défaut. Pour l'instant Cap ne parle jamais : il servira quand Cap saura répondre à voix haute.
- Le micro et le clavier passent par la même porte d'entrée (`demandes.js`). Tant que l'intelligence artificielle n'est pas branchée, tout ce qui est écrit va dans « À trier », mot pour mot. « Ajoute à ma to-do... » ne garde que la fin de la phrase. « Continue. » et « Annule. » attendront l'intelligence artificielle. Exception : une demande de rendez-vous ouvre une fiche « Nouveau rendez-vous » préremplie, que Max vérifie avant l'ajout dans l'agenda « Cap – FICTIF » ; « Reporte ça à demain » reporte la dernière tâche ouverte.
- Les tâches cochées vont dans la ligne repliée « Terminées (N) », en bas de la liste. Glisser une tâche à droite la coche, à gauche la reporte à demain. Rien n'est jamais effacé, et « Annuler » reste affiché 8 secondes.
- Un bouton ne fait que remplir une phrase : il ne peut jamais envoyer un mail.

## Ce que contient une tâche
Identifiant, intitulé, catégorie, sous-catégorie, fait ou pas fait, date d'entrée, échéance, date de réalisation, priorité, tâche parente, note, « avant le », « abandonnée le », origine, fictif.

## Où se trouve Cap en ligne
- L'appli : https://maxlavegie-dev.github.io/cap/app/ (à ouvrir avec Chrome sur le téléphone pour l'installer).
- Le code est public sur https://github.com/maxlavegie-dev/cap. Il ne contient aucune donnée personnelle : la liste de Max reste dans son téléphone.
- `PROMPT_CAP.txt` n'est jamais publié (il est exclu par le fichier `.gitignore`).
- Pour publier une nouvelle version, on envoie les changements sur GitHub, et l'adresse se met à jour toute seule en une à deux minutes.

## Comment voir l'application sur l'ordinateur
Double-cliquer sur `app/index.html`.

## Comment lancer les vérifications automatiques
Dans un terminal ouvert dans le dossier du projet, taper `python app\test_cap.py`. Il faut que Microsoft Edge soit installé.
