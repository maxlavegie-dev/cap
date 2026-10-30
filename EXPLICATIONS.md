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
| `comprendre_dates.js` | Trouve la date dans une phrase (« dans deux semaines », « vendredi dans deux semaines », « lundi en huit », « premier lundi du mois prochain », « fin du mois »…). S'il hésite entre deux dates, il ne devine pas : il renvoie les deux choix, et Cap pose la question à Max avec deux boutons. |
| `comprendre_demande.js` | Comprend, sans intelligence artificielle, une demande de rendez-vous (date, heure, titre, rappels) ou « Reporte ça à demain ». Ne fait rien lui-même : il prépare seulement un brouillon. |
| `sous_categories.js` | Trouve la sous-catégorie d'une tâche dictée dans une catégorie : celle nommée dans la phrase, sinon celle dont les tâches ressemblent clairement à la phrase (un seul gagnant), sinon « À classer ». Jamais de choix au hasard. |
| `annulation.js` | Un seul « Annuler » pour toute l'appli : retient la dernière action pendant 8 secondes, l'annule une seule fois, et reconnaît « Annule », « Annule ça », « Cap, annule la dernière action ». |
| `vibration.js` | Une vibration très courte (30 ms) quand une action est enregistrée, si le téléphone le permet. |
| `voix.js` | Cap répond à voix haute (voix du téléphone, en français), sauf si « Réponse silencieuse » est allumée. |
| `indices_rangement.js` | Les indices évidents pour ranger (scène, séquence, dialogue → Scénarios ; chapitre, personnage, titre du roman → Roman). Modifiable sans toucher au reste. |
| `reglages_ia.js` | Les réglages de l'IA : modèle (Claude Haiku), limite par défaut (60), prix, nom du fichier de consignes. Aucune clé. |
| `cle_ia.js` | Garde la clé d'IA tapée par Max, sur le téléphone seulement ; n'en montre que les 4 derniers caractères. |
| `consignes_cap.txt` | La fiche de consignes **de secours**, neutre, sans aucun prénom : utilisée seulement si Max n'a pas collé sa propre fiche dans Cap. La vraie fiche de Max n'est jamais publiée : il la colle une fois dans « Réglages du cerveau », elle reste sur le téléphone. Une fiche dont la première ligne contient « BROUILLON » n'est jamais envoyée. |
| `cerveau_claude.js` | Le fournisseur Claude Haiku : utilisé seulement avec une clé et une fiche de consignes lue à l'ouverture (celle du téléphone d'abord, sinon celle de secours). Ajoute la date et l'heure de Paris à chaque échange. Une action à la fois, intitulé mot pour mot. Un numéro de téléphone que Max n'a jamais dit est remplacé par « Je ne sais pas ». Clé refusée : Cap dit qu'elle a sans doute expiré. |
| `journal_ia.js` | L'historique des échanges avec l'IA (ce que Max a dit, ce que l'IA a répondu ou proposé), effaçable d'un geste. Jamais la clé. |
| `limite_ia.js` | Compte les échanges avec une IA payante : limite par jour (60 par défaut) et plafond de dépense du mois en euros (4 € par défaut), tous deux réglables par Max. Prévient avant, s'arrête net au plafond. |
| `actions_cap.js` | La frontière entre le cerveau et Cap : la liste des actions permises, et la vérification de chacune. Le cerveau ne touche jamais aux tâches lui-même. |
| `cerveau.js` | Le cerveau : comprend la demande et rend une décision (une action, ou une seule question courte). Le modèle d'IA est interchangeable. |
| `cerveau_prepare.js` | Les réponses préparées, gratuites et sans clé : range une tâche seulement si la catégorie est nommée, sinon dans À trier ; pose une question s'il hésite. |
| `demandes.js` | La porte d'entrée unique de toutes les demandes (micro et clavier) : elle passe la demande au cerveau, puis exécute sa décision. |
| `recherche.js` | La recherche tapée, sans intelligence artificielle : trouve un mot dans les tâches ou les rendez-vous, sans tenir compte des accents ni des majuscules. |
| `journal_actions.js` | Retient les dernières actions (ajout, coche, abandon) et tient le journal complet (heure à la seconde, ce que Max a dit ou touché, ce que Cap a compris, ce qu'il a fait), envoyé dans l'onglet « Journal ». Masque les mots de passe et les longs numéros ; n'efface jamais rien. |
| `tuiles.js` | Dessine les tuiles de l'écran complet, leur micro, et le déplacement par appui long puis glissement. |
| `mode_trier.js` | Le mode Trier : une tâche « À trier » à la fois, rangée d'un toucher ou à la voix, avec Annuler pendant 8 secondes. |
| `sauvegarde_drive.js` | Copie datée du tableau dans un dossier du Drive : à la demande, puis chaque semaine. Ne supprime aucune copie. |
| `fiche_rendezvous.js` | La fiche d'un rendez-vous : détails, boutons « Appeler » et « Écrire », modification avec récapitulatif avant de confirmer. Ne touche que l'agenda « Cap – FICTIF ». |
| `listes_choix.js` | Les listes de catégories (avec leurs couleurs et sous-catégories) et d'étapes par défaut. Retirer n'efface rien : l'élément est marqué avec la date et peut être remis. |
| `synchro_listes.js` | Recopie ces listes dans le tableau (onglets « Catégories » et « Étapes par défaut ») et relit ce qui s'y trouve. |
| `choix_dates.js` | Les dates en trois menus (jour, mois, année), avec les boutons Aujourd'hui, Demain, Ce week-end, Semaine prochaine, et la date dictée. |
| `fermeture_fenetres.js` | Fermer une petite fenêtre en touchant à côté ; si Max a déjà écrit, question « Garder », « Jeter » (avec Annuler 8 secondes) ou « Continuer ». |
| `fenetres_listes.js` | Les fenêtres en gros boutons pour choisir une catégorie, et pour ajouter, retirer ou remettre une catégorie ou des étapes par défaut. |
| `app.js` | L'affichage à l'écran et ce qui se passe quand on touche un bouton. |
| `manifest.webmanifest` | La carte d'identité de l'appli pour le téléphone : nom, couleurs, icônes. Elle permet de l'installer sur l'écran d'accueil. |
| `service-worker.js` | Garde une copie de l'appli sur le téléphone pour qu'elle s'ouvre même sans internet. |
| `installation.js` | Active cette copie hors connexion. |
| `icones/` | L'icône aux différentes tailles demandées par Android. Elles sont fabriquées par `outils/fabriquer_icones.py` à partir de l'icône validée. |
| `test_cap.py` | Des vérifications automatiques des règles, de la dictée, du clavier, de la connexion Google (simulée), de la recherche, de la fiche de rendez-vous, de l'accueil, de la fenêtre d'ajout, des tuiles, du mode Trier, du journal, de la sauvegarde, de l'annulation, du cerveau et de l'installation (234 essais, dont des vérifications plus complètes du cerveau). |

## L'écran d'accueil (Lot 1, 29/10/2026)
- En haut : seulement la date du jour, centrée. Pas d'heure : la barre du haut du téléphone (heure, Wi-Fi, réseau, batterie) reste visible, car Cap installée s'ouvre en mode « standalone » (comme une appli, mais sans cacher cette barre).
- En bas, juste au-dessus des trois boutons : une seule barre de recherche, facile à atteindre d'une main. À gauche dans la barre, un petit menu montre toujours où l'on cherche (« Tâches ▾ », « Rendez-vous ▾ » ; Gmail, Drive, archives et mémoire perso arriveront plus tard).
- Les résultats arrivent pendant la frappe, sans appuyer sur Entrée, et s'affichent au-dessus de la barre, dans l'espace libre entre la date et la barre.
- Un glissement vers le haut ouvre l'écran complet (liste, rendez-vous, dernières actions, état de la synchronisation).

## La fenêtre « Ajouter une tâche » (Lot 3, 29/10/2026)
- Dates : trois menus (jour, mois, année) et quatre boutons rapides. « Ce week-end » donne le samedi qui vient (ou aujourd'hui le week-end) ; « Semaine prochaine » donne le lundi suivant. La date reste vide tant qu'on ne la choisit pas. Sous les menus, la date s'écrit en toutes lettres avec le jour (« lundi 2 novembre 2026 »).
- « Dire la date » : Cap montre ce qu'il entend, relance l'écoute une fois s'il n'a rien entendu, et dit clairement si le micro est bloqué.
- Petites fenêtres : on les ferme en touchant à côté. Si Max a déjà écrit, Cap demande « Garder », « Jeter » ou « Continuer ».
- Catégorie : de gros boutons de couleur, « À trier » en premier puis les plus utilisées ; un appui ouvre les sous-catégories.
- Ce qui est retiré (catégorie ou étapes par défaut) reste dans le tableau avec la date ; « Annuler » pendant 8 secondes, puis « Remettre » à tout moment.

## L'écran complet en tuiles (Lot 4, 29/10/2026)
- Les tuiles fixes (Dernières actions, Prochains rendez-vous, Aujourd'hui, Trier) viennent toujours en premier et ne peuvent être ni retirées ni déplacées. Ensuite : À trier, les catégories de Max, puis Tout, + Ajouter et Modifier. Chaque tuile affiche son compteur.
- Les catégories des tuiles et celles de « Ajouter une tâche » sont la même liste.
- Appui long puis glissement pour changer l'ordre ; cet ordre passe avant le classement par usage et est gardé dans la colonne « Ordre » de l'onglet Catégories.
- Le bouton Aide est en haut à droite de l'écran complet.
- « Sauvegarder maintenant » fait la première copie ; ensuite Cap en fait une chaque semaine. Au-delà de 5 copies, Cap prévient mais ne supprime rien.

## Dates, sous-catégories et Annuler (Lot 5, 30/10/2026)
- Les dates dites naturellement sont comprises partout ; si deux dates sont possibles, Cap pose la question avec deux boutons.
- Une tâche dictée dans une catégorie à sous-catégories va dans la sous-catégorie nommée ou évidente, sinon dans « À classer » (affiché en premier).
- Dans l'écran Trier, « + Ajouter » crée une catégorie et y range la tâche ; « Modifier » retire une catégorie sans rien effacer.
- Toute action garde un bouton « Annuler » 8 secondes ; dire ou écrire « Annule » fait la même chose. Une vibration courte confirme chaque action.

## Le cerveau de Cap (Lot 6, première version, 30/10/2026)
- Deux pièces séparées : le cerveau comprend et décide ; `actions_cap.js` exécute et vérifie. On peut changer de modèle d'IA ou ajouter des actions sans refaire le reste.
- Sans clé, Cap utilise des réponses préparées, gratuites. Il range seulement ce qui est nommé (« Ajoute dans Écriture : … », « … dans Quotidien Courses », « idée de scénario… ») ; sinon la tâche va dans À trier. S'il hésite entre deux catégories, il pose une seule question.
- Si « Réponse silencieuse » est éteinte, Cap dit en une phrase ce qu'il a fait. Le bouton « Annuler » reste proposé.
- Claude Haiku est prêt : Max tape sa clé une fois dans « Réglages du cerveau », elle reste sur le téléphone, jamais dans le code. La limite par jour se règle au même endroit (60 par défaut) ; la dépense du mois y est affichée. Les consignes (`consignes_cap.txt`, environ 0,04 centime par échange) ne partent qu'une fois validées par Max.
- **Règle de publication** : le projet est public. On n'y met jamais de vraie donnée, de prénom de proche, de clé, ni le contenu de la fiche de Max ou de la future fiche de ses mots propres : tout cela est tapé dans Cap et reste sur le téléphone. Le fichier `mots_prives.txt` (jamais publié) liste les mots interdits, et un test refuse toute publication qui en contiendrait un. Au moindre doute, on demande à Max avant de publier.
- Une fois la clé branchée, ce que Max dit à Cap part chez Anthropic (l'entreprise de Claude), avec les noms des catégories fictives.
- Les « Dernières actions » sont cliquables : une ligne ouvre la liste sur la tâche. Les tâches sans sous-catégorie s'affichent sous l'intitulé « À classer ».

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
- Le micro et le clavier passent par la même porte d'entrée (`demandes.js`). Tant que l'intelligence artificielle n'est pas branchée, tout ce qui est écrit va dans « À trier », mot pour mot. « Ajoute à ma to-do... » ne garde que la fin de la phrase. « Continue. » attendra l'intelligence artificielle ; « Annule. » annule la dernière action (Lot 5). Exception : une demande de rendez-vous ouvre une fiche « Nouveau rendez-vous » préremplie, que Max vérifie avant l'ajout dans l'agenda « Cap – FICTIF » ; « Reporte ça à demain » reporte la dernière tâche ouverte.
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
