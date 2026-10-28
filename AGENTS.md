# Repository Guidelines

Projet **Cap** : application Android personnelle (PWA recommandée) pour Max. Le cahier des charges complet est `PROMPT_CAP.txt` : le relire, avec le fichier d'explications et le journal de bord, au début de chaque session. État actuel : semaine 1 construite (écran d'accueil, liste de tâches, dictée, installation PWA) et en ligne ; voir `JOURNAL_DE_BORD.md`.

## Communication avec Max
- Max n'est pas développeur et dicte à la voix. Lui parler en français, en le tutoyant, simplement, sans jargon. Une seule question à la fois, réponses courtes, toujours la vérité.
- Ne jamais lui demander d'écrire du code.
- Règle de travail (Complément 4, 28/10/2026) : tant que tout reste fictif, avancer seul (coder, tester) sans demander. S'ARRÊTER et demander l'accord explicite de Max avant : toute nouvelle autorisation Google ou tout élargissement ; tout accès à ses vraies données (vrai Gmail, vrai agenda, vrai Drive) ; tout envoi de mail ; toute publication (push).
- À chaque étape terminée : compte rendu court (ce qui a été fait, ce que Max doit tester). Avant chaque grosse modification : sauvegarde de l'état actuel (tag git local `sauvegarde-...`).
- Accueillir ses ajouts en cours de route : les reformuler, puis les noter dans le journal de bord et le fichier d'explications.

## Délégation (économie de quota, environ 1300 unités LLM par jour)
- Le modèle principal s'occupe du plan, de l'architecture, de la sécurité, des bugs difficiles et de la vérification finale.
- Les subagents moins chers (par exemple `gpt-6-1-sol`, `claude-haiku-5-5`) font les tâches de routine : écrans simples, code répétitif, tests simples, conversions.
- Toujours relire, exécuter et tester le travail d'un subagent : il n'a jamais le dernier mot.

## Architecture (décidée)
- L'IA est interchangeable (Claude, ChatGPT ou Gemini) : passer par une couche d'accès unique.
- La to-do est stockée dans un Google Sheets du Drive de Max. L'agenda passe par Google Agenda : pas d'agenda maison.
- Le dictionnaire des personnes, le journal de classement et les sauvegardes vont aussi dans le Drive de Max.
- Mode hors connexion : la to-do et l'agenda restent lisibles (lecture seule), et les ajouts sont mis en file d'attente puis synchronisés sans perte.

## Verrous techniques obligatoires (à coder, pas seulement à écrire en consigne)
- **Mails** : jamais d'envoi sans un « oui » explicite de Max.
- **Mémoire personnelle** : Cap peut la consulter, mais rien n'en sort, même si Max le demande. Le module qui prépare les brouillons n'y a pas accès.
- **Zéro perte** : aucune tâche n'est supprimée ni reformulée. Une tâche cochée reste en place avec sa date. En cas de doute, ne rien fermer.
- **Honnêteté** : ne jamais inventer une date, un montant, un nom ou un document. Dire « je ne suis pas sûr ».

## Code et tests
- `app/` contient du HTML/CSS/JS pur : pas de framework, pas de build, pas de ressource externe. Scripts classiques chargés dans cet ordre : `donnees_fictives.js`, `etapes_par_defaut.js`, `stockage.js` (localStorage, à remplacer par Google Sheets), `taches.js` (règles métier, sans DOM ; signale chaque modification à `synchronisation`), `reglages_google.js` (ID client public, noms FICTIF ; jamais de secret client), `google_connexion.js` (OAuth implicite par redirection, jeton ~1 h), `google_sheets.js`, `google_agenda.js` (agenda secondaire uniquement, jamais `primary`), `synchronisation.js` (file d'attente hors ligne, fusion ; aucun appel de suppression ou d'effacement côté Google), `dictee.js` (reconnaissance vocale du navigateur, sans DOM), `phrases_clavier.js` (réglages du clavier de phrases), `preferences_clavier.js` (usage, historique, réponse silencieuse), `demandes.js` (porte d'entrée unique micro + clavier, où brancher l'IA), `app.js` (affichage).
- PWA : `manifest.webmanifest`, `service-worker.js` (réseau d'abord, cache en secours ; ajouter chaque nouveau fichier à `FICHIERS_PRECACHE`), `installation.js`. Icônes régénérées par `python outils\fabriquer_icones.py`.
- Tests : `python app\test_cap.py`. Il lance Microsoft Edge sans fenêtre ; Node n'est pas installé.
- Construire le DOM avec `textContent`, jamais `innerHTML` avec des données.
- Déploiement : dépôt public `maxlavegie-dev/cap`, GitHub Pages servi depuis la racine de `main`. L'appli est en ligne sur https://maxlavegie-dev.github.io/cap/app/, et chaque `git push` sur `main` la met à jour. Le dépôt est public : `PROMPT_CAP.txt` et tout secret doivent rester dans `.gitignore`.
- Commits : messages courts en français. Les commits locaux servent de sauvegarde et sont permis sur le fictif ; ne jamais faire de push sans l'accord de Max : lui présenter d'abord ce qui sera publié, puis lui dire clairement quand il doit essayer sur son téléphone.
- Le shell cmd gère mal les guillemets : passer les messages de commit par un fichier (`git commit -F`).

## Style de code
- Scripts simples, un seul but chacun. Commentaires en français.
- Réglages (clés API, listes d'expéditeurs, budgets, noms de feuilles) séparés du code. Aucune clé ni donnée personnelle en dur, et rien de tout cela dans un dépôt.
- Accès Google avec les droits minimaux nécessaires.
- Tenir à jour, en français, un fichier d'explications et un journal de bord : ce qui est fait, en cours, à faire, les décisions et les questions en attente.

## Données
- Utiliser UNIQUEMENT des données fictives, inventées et marquées « FICTIF » (ou placées dans des fichiers de test séparés), pour pouvoir les vider d'un coup. Ne jamais demander les vraies données de Max.
- Ne jamais toucher à l'ancien système de Max (document « À faire », briefing par mail) avant la bascule, que Max décide lui-même.
- Ne rien construire pour la commercialisation, ni la partie banque (en attente de confirmation de la banque).
