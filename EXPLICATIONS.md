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
| `index.html` | La structure de l'écran : date et heure en haut, liste au milieu, boutons + et micro en bas, petites fenêtres (menu, confirmation, ajout). |
| `style.css` | L'apparence : les couleurs de l'icône, la taille des textes et des boutons. |
| `donnees_fictives.js` | Des tâches INVENTÉES pour les essais. Ce fichier sera supprimé d'un coup à la bascule. |
| `etapes_par_defaut.js` | Les réglages des étapes créées automatiquement (ex. pour un titre d'album : réenregistrer les voix, mixer, masteriser). On peut les modifier sans toucher au reste. |
| `stockage.js` | Garde la liste sur le téléphone. Il sera remplacé par Google Sheets en semaine 2. |
| `taches.js` | Les règles de la liste : ajouter, cocher, abandonner, remettre, calculer l'avancement et les jours restants. |
| `dictee.js` | Écoute ce que Max dit, avec la reconnaissance vocale du navigateur, et transmet le texte entendu. |
| `app.js` | L'affichage à l'écran et ce qui se passe quand on touche un bouton. |
| `manifest.webmanifest` | La carte d'identité de l'appli pour le téléphone : nom, couleurs, icônes. Elle permet de l'installer sur l'écran d'accueil. |
| `service-worker.js` | Garde une copie de l'appli sur le téléphone pour qu'elle s'ouvre même sans internet. |
| `installation.js` | Active cette copie hors connexion. |
| `icones/` | L'icône aux différentes tailles demandées par Android. Elles sont fabriquées par `outils/fabriquer_icones.py` à partir de l'icône validée. |
| `test_cap.py` | Des vérifications automatiques des règles, de la dictée et de l'installation (46 essais). |

## Les règles programmées pour la liste
- **Zéro perte** : il n'existe aucun moyen d'effacer une tâche. « Abandonner » la retire de la vue normale, avec la date, mais elle reste gardée et on peut la remettre.
- On ne peut pas modifier l'intitulé d'une tâche existante.
- Cocher enregistre la date de réalisation, et une tâche cochée reste à sa place.
- Si la liste enregistrée devient illisible, Cap en garde une copie de sécurité au lieu de l'écraser.

## La dictée
- On touche le gros micro, on parle, et la tâche est ajoutée tout de suite dans la catégorie « À trier », mot pour mot, sans aucune reformulation.
- Pendant 8 secondes, un bouton « Annuler » permet d'abandonner la tâche (elle reste gardée dans les abandonnées).
- Si la sauvegarde échoue, le texte dicté reste affiché pour pouvoir le recopier.
- À savoir : la reconnaissance vocale du navigateur passe par internet, et le son est traité par Google ou Microsoft selon le navigateur.

## Ce que contient une tâche
Identifiant, intitulé, catégorie, sous-catégorie, fait ou pas fait, date d'entrée, échéance, date de réalisation, priorité, tâche parente, note, « avant le », « abandonnée le », origine, fictif.

## Comment voir l'application sur l'ordinateur
Double-cliquer sur `app/index.html`.

## Comment lancer les vérifications automatiques
Dans un terminal ouvert dans le dossier du projet, taper `python app\test_cap.py`. Il faut que Microsoft Edge soit installé.
