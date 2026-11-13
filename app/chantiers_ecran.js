'use strict';

// 09/11/2026 (accord de Max, CHANTIERS, séance 1 sur 7) : l'écran « Chantiers ». Une fenêtre de choix sur l'eau (règle de
// Max : gros boutons identiques, sans cadre ni titre), un gros bouton numéroté par chantier : nom, voyant, statut. Ordre :
// rouge, orange, vert, puis par nom ; chaque sous-chantier juste sous son parent, en retrait. Les exemples fictifs sont
// masqués (une phrase dit combien). À la voix : « ouvre les chantiers » ; « le premier », « numéro 3 »… touchent la ligne
// (règle des rangs, app.js). Toucher un chantier montre sa fiche courte (famille, type, statut) : l'ouvrir viendra à la
// séance 4. LECTURE SEULE : rien n'est écrit, nulle part. Sans réseau ou sans droit : la dernière copie, avec un message.
const chantiersEcran = (() => {
  function brancher(doc, {
    source = (typeof chantiers !== 'undefined' ? chantiers : null),
    lire = options => source.lire(options),
    commandes = (typeof commandesVocales !== 'undefined' ? commandesVocales : null),
    transition = (typeof choixSurEau !== 'undefined' ? choixSurEau : null),
    // 10/11/2026 (séance 3) : dossiers Drive des chantiers (compte Cap) ; remplaçables dans les tests.
    dossiers = (typeof chantiersDossiers !== 'undefined' ? chantiersDossiers : null),
    compteCap = (typeof googleCompteRelations !== 'undefined' ? googleCompteRelations : null),
    // 10/11/2026 (séance 2) : la date du jour (remplaçable dans les tests) et les règles (regles_voyant.js par défaut).
    maintenant = () => Date.now(),
    regles = undefined,
    // 11/11/2026 (c110) : la visionneuse de Cap (visionneuse_cap.js) ; remplaçable dans les tests.
    visionneuse = () => (typeof visionneuseCap !== 'undefined' ? visionneuseCap.instance : null),
    // 11/11/2026 (c128) : lecture de l'onglet « Prêt » (chantiers.js, compte Cap, lecture seule) ; remplaçable dans les tests.
    lirePret = () => chantiers.lirePret(),
    // 11/11/2026 (c142) : le téléphone a-t-il du réseau ? (remplaçable dans les tests)
    enLigne = () => (typeof navigator === 'undefined' || navigator.onLine !== false),
    // 10/11/2026 (c105) : où garder la dernière liste des chantiers qui ont un dossier (numéros CH-xxx SEULEMENT).
    stockage = (() => { try { return typeof localStorage !== 'undefined' ? localStorage : null; } catch (e) { return null; } })()
  } = {}) {
    const el = id => doc.getElementById(id);
    const fenetre = el('chantiers-cap');
    const liste = el('liste-chantiers');
    // 11/11/2026 (c134) : une CLASSE en plus de l'identifiant : la copie qui part en fondu (sans identifiants) garde
    // l'allure des lignes (style.css : « :is(#liste-chantiers, .liste-chantiers) »).
    if (liste) liste.classList.add('liste-chantiers');
    const etat = el('etat-chantiers');
    const note = el('note-chantiers');
    const recherche = el('recherche-chantiers'); // c131
    const message = el('message-recherche-chantiers'); // c131
    // c134 : même raison que pour la liste (le champ et son message gardent leur allure dans la copie qui part en fondu).
    if (recherche) recherche.classList.add('recherche-chantiers');
    if (message) message.classList.add('message-recherche-chantiers');
    if (recherche) recherche.addEventListener('input', () => dessinerListe(dernieresTries)); // c131 : refiltre tout de suite
    const fiche = el('fiche-chantier');
    const fermer = el('fermer-chantiers');
    const compteurs = el('compteurs-chantiers');
    const zoneDossier = el('dossier-chantier');
    const question = el('question-dossier-chantier');
    const boutonCreer = el('creer-dossier-chantier');
    const boutonOui = el('oui-dossier-chantier');
    const boutonNon = el('non-dossier-chantier');
    let choisi = null; // le chantier dont la fiche est montrée
    let plan = null;   // ce qui serait créé, montré à Max avant son Oui
    // 10/11/2026 (c88) : ce que le Oui confirme : 'creation' (dossier du chantier choisi) ou 'note' (c92).
    // 12/11/2026 (c147, décision de Max) : plus de 'maj' : le bouton « Mettre à niveau » est retiré (« Tout synchroniser »).
    let actionAttendue = 'creation';
    // 10/11/2026 (c89, marche 3) : les chantiers qui ont un dossier (lus dans le Drive du compte Cap, lecture seule) :
    // marque « dossier » dans la liste, et « Ouvrir le dossier dans Drive » dans la fiche (lien ouvert hors de Cap).
    const lienDossier = el('ouvrir-dossier-chantier');
    let dossiersConnus = new Map();
    // ----- 10/11/2026 (accord de Max, c105) : une fiche qui ne trompe pas.
    // - Cap garde sur le téléphone la dernière liste des numéros CH-xxx qui ont un dossier (rien d'autre : ni nom, ni
    //   adresse) ; au démarrage, les boutons du chantier s'affichent d'après elle (le bouton « Drive » attend la relecture,
    //   car l'adresse du dossier n'est pas gardée).
    // - Tant que Cap n'a pas RELU les dossiers dans le Drive du compte Cap (compte pas connecté, lecture pas finie ou
    //   ratée), la fiche d'un chantier absent de cette liste ne propose PAS « Créer le dossier » : elle dit qu'elle ne sait pas.
    const CLE_DOSSIERS = 'cap_chantiers_avec_dossier';
    const MESSAGE_INCONNU = 'Je ne sais pas encore si ce chantier a un dossier : touche « Tout synchroniser ».';
    let dossiersRelus = false;
    function lireCopieDossiers() {
      try {
        const liste = JSON.parse((stockage && stockage.getItem(CLE_DOSSIERS)) || '[]');
        return new Map((Array.isArray(liste) ? liste : []).filter(id => /^CH-\d{1,6}$/.test(String(id))).map(id => [String(id), { id: '', nom: '' }]));
      } catch (erreur) { return new Map(); }
    }
    function garderCopieDossiers() {
      try { if (stockage) stockage.setItem(CLE_DOSSIERS, JSON.stringify([...dossiersConnus.keys()].filter(id => /^CH-\d{1,6}$/.test(id)))); } catch (erreur) { /* copie pas gardée : rien de grave */ }
      try { if (dossiers && typeof dossiers.garderIds === 'function') dossiers.garderIds(stockage, dossiersConnus); } catch (erreur) { /* c152 : rien de grave */ }
    }
    dossiersConnus = lireCopieDossiers();
    // 10/11/2026 (c92) : « Ajouter une note au journal », seulement pour un chantier qui a un dossier.
    const zoneNote = el('zone-note-chantier');
    const champNote = el('note-chantier');
    const boutonNote = el('ajouter-note-chantier');
    let ligneEnAttente = '';
    // 10/11/2026 (c93) : « Lire le journal » (lecture seule), seulement pour un chantier qui a un dossier.
    const boutonLire = el('lire-journal-chantier');
    // 10/11/2026 (c96) : « Voir les documents » (lecture seule).
    const boutonDocuments = el('voir-documents-chantier');
    const zoneDocuments = el('resultat-chantier'); // c97 : la même zone (avant : el('documents-chantier'))
    let lecturesDocuments = 0;
    // 10/11/2026 (c97) : une seule zone de résultat pour le journal et les documents ; la grille des 4 actions ; « Note ».
    // Avant : el('lignes-journal-chantier') et el('documents-chantier'), deux zones.
    const lignesJournal = el('resultat-chantier');
    const actionsChantier = el('actions-chantier');
    const boutonOuvrirNote = el('ouvrir-note-chantier');
    let lecturesJournal = 0;
    function montrerLienDossier() {
      const avecDossier = Boolean(choisi && dossiers && dossiersConnus.get(choisi.id));
      // c97 : le champ de note reste fermé jusqu'à « Note » (avant : ouvert dès qu'il y avait un dossier) ; la grille des actions.
      if (zoneNote) zoneNote.hidden = true;
      if (actionsChantier) actionsChantier.hidden = !avecDossier;
      if (boutonLire) boutonLire.hidden = !avecDossier; // c93
      if (lignesJournal) { lignesJournal.hidden = true; lignesJournal.replaceChildren(); } // c93 : rien d'affiché d'un autre chantier
      if (boutonDocuments) boutonDocuments.hidden = !avecDossier; // c96
      if (zoneDocuments) { zoneDocuments.hidden = true; zoneDocuments.replaceChildren(); } // c96
      if (boutonCreer && avecDossier) boutonCreer.hidden = true; // c92
      if (!lienDossier) return;
      const d = choisi && dossiers && dossiersConnus.get(choisi.id);
      lienDossier.hidden = !(d && d.id); // c105 : sans adresse (copie du téléphone), pas de lien tant que ce n'est pas relu
      if (d && d.id) lienDossier.href = dossiers.adresseDossier(d.id); else lienDossier.removeAttribute('href');
    }
    function poserMarques() {
      for (const b of liste.querySelectorAll('.ligne-chantier')) {
        const deja = b.querySelector('.marque-dossier');
        const a = dossiersConnus.has(b.dataset.id);
        if (a && !deja) b.append(noeud('span', 'marque-dossier', 'dossier'));
        if (!a && deja) deja.remove();
      }
      montrerLienDossier();
    }
    async function lireDossiersExistants() {
      if (!dossiers || typeof dossiers.dossiersExistants !== 'function' || !compteCap || (typeof compteCap.connecte === 'function' && !compteCap.connecte())) return;
      try { dossiersConnus = await dossiers.dossiersExistants(compteCap); } catch (erreur) { return; } // pas de marque, rien d'autre
      dossiersRelus = true; // c105
      garderCopieDossiers(); // c105
      poserMarques();
      // c105 : la fiche disait « je ne sais pas encore » : elle se met à jour (jamais pendant une question ou un travail).
      if (choisi && !enConfirmation && question && question.textContent === MESSAGE_INCONNU) montrerDossier('depart');
    }
    if (!fenetre || !liste || !etat || !fermer || !source) return null;
    const noeud = (balise, classe, texte) => { const n = doc.createElement(balise); if (classe) n.className = classe; if (texte !== undefined) n.textContent = texte; return n; };
    const dire = texte => { etat.hidden = !texte; etat.textContent = texte || ''; };
    const NOMS_VOYANT = { rouge: 'rouge', orange: 'orange', vert: 'vert' };
    let lecture = 0;

    // 10/11/2026 (séance 2) : le voyant montré. Si la couleur calculée et la couleur écrite dans la Liste diffèrent : les
    // deux (« calculé rouge · écrit vert ») ; sinon une seule. Pas de couleur calculée (archivé, en veille sans alerte) : la
    // couleur écrite, comme avant.
    function texteVoyant(c) {
      const ecrit = NOMS_VOYANT[c.voyantEcrit !== undefined ? c.voyantEcrit : c.voyant] || '';
      const calcule = NOMS_VOYANT[c.voyantCalcule] || '';
      if (calcule && calcule !== ecrit) return `calculé ${calcule} · ${ecrit ? `écrit ${ecrit}` : 'rien d’écrit'}`;
      return calcule || ecrit || 'sans voyant';
    }
    // 10/11/2026 (c94) : le prompt du chantier (lecture seule), dans une zone qui défile si le texte est long.
    const zonePrompt = el('prompt-chantier');
    const compteurPrompts = el('compteur-prompts');
    function montrerPrompt(c) {
      if (!zonePrompt) return;
      zonePrompt.hidden = !c;
      zonePrompt.replaceChildren();
      if (!c) return;
      if (c.prompt) zonePrompt.append(noeud('span', 'prompt-titre', 'Prompt : '), noeud('span', 'prompt-texte', c.prompt));
      else zonePrompt.append(noeud('span', 'prompt-titre', 'Pas encore de prompt.'));
      zonePrompt.scrollTop = 0;
    }
    // 11/11/2026 (décision de Max, c130) : la fiche d'un chantier est un ÉCRAN À PART dans la fenêtre : la liste, les
    // compteurs et leurs boutons disparaissent (rien ne reste derrière, aucune couche qui défile pour rien), avec la
    // transition « rien puis sable » (l'écran d'avant part en fondu, l'eau un instant, le nouveau monte). « Fermer » ramène
    // à la liste, puis ferme. Avant (10/11) : la fiche était collée en haut de la liste, qui défilait dessous.
    function changerEcran(miseAJour) {
      let r;
      const faire = () => { r = miseAJour(); };
      // 11/11/2026 (c134, défaut vu par Max : la liste SAUTAIT en haut au toucher) : la copie de l'écran d'avant qui part en
      // fondu (choix_sur_eau.js) repartait du HAUT de la liste (compteurs, « Mettre à niveau ») ; elle est maintenant défilée
      // d'autant que l'était la fenêtre : tout reste à sa place pendant le fondu. Avant : seulement transition.changer(…).
      const defile = fenetre.scrollTop;
      if (transition && typeof transition.changer === 'function' && fenetre.open) {
        transition.changer(fenetre, faire);
        const fantome = [...fenetre.children].find(x => x.classList.contains('choix-fantome'));
        if (fantome && defile > 0) fantome.scrollTop = defile;
      } else faire();
      return r;
    }
    function montrerFiche(c) {
      if (!fiche) return '';
      return changerEcran(() => montrerFicheSurPlace(c));
    }
    function revenirALaListe() {
      changerEcran(() => {
        fenetre.classList.remove('fiche-ouverte');
        if (fiche) { fiche.hidden = true; fiche.textContent = ''; }
        montrerPrompt(null);
        effacerTemoin();
        choisi = null; plan = null; actionAttendue = 'creation';
        if (zoneNote) zoneNote.hidden = true;
        if (lignesJournal) { lignesJournal.hidden = true; lignesJournal.replaceChildren(); }
        { const bt = el('taches-chantier'); if (bt) bt.hidden = true; }
        montrerDossier('depart');
        montrerLienDossier();
      });
    }
    function montrerFicheSurPlace(c) {
      fenetre.classList.add('fiche-ouverte'); // c130
      montrerPrompt(c); // c94
      // 10/11/2026 (c94) : la fiche (et son prompt) remonte en haut de l'écran si elle n'y est pas déjà (liste pas défilée) :
      // sinon le bas du prompt sortait de l'écran.
      const haut = el('haut-chantier');
      try { if (haut && haut.getBoundingClientRect().top > 1) haut.scrollIntoView({ block: 'start' }); } catch (e) { /* rien */ }
      const morceaux = [c.famille && `famille ${c.famille}`, c.type, c.statut, `voyant ${texteVoyant(c)}`].filter(Boolean).join(' · ');
      const texte = `« ${c.nom} » : ${morceaux || 'pas d’autre information'}. L’ouverture d’un chantier viendra à la séance 4.`;
      fiche.hidden = false;
      fiche.textContent = texte;
      if (choisi !== c) effacerTemoin(); // c107 : le témoin ne vaut que pour la fiche où il a été vu
      choisi = c;
      actionAttendue = 'creation'; // 10/11/2026 (c88)
      const bt = el('taches-chantier'); if (bt) bt.hidden = false; // c128 : « Tâches » pour tout chantier choisi
      montrerDossier('depart');
      montrerLienDossier(); // 10/11/2026 (c89)
      return texte;
    }

    // ----- 10/11/2026 (accord de Max, séance 3) : le dossier Drive du chantier choisi, dans le Drive du compte Cap.
    // Toucher « Créer le dossier de ce chantier » LIT d'abord ce qui existe, puis MONTRE ce qui sera créé et attend « Oui,
    // créer ». Rien n'est créé sans ce Oui ; « Non » ne fait rien. Rien n'est jamais effacé, renommé, déplacé ni partagé.
    function montrerDossier(etape, texte = '') {
      if (!zoneDossier || !boutonCreer || !boutonOui || !boutonNon || !question) return;
      // 11/11/2026 (accord de Max, c125) : la visionneuse du chantier est ouverte par-dessus : la question et les messages s'y
      // affichent aussi ; ses « Oui, ajouter » / « Non » touchent les boutons de CETTE fiche (même chemin, rien de plus).
      try {
        const v = visionneuse();
        if (v && typeof v.ouverte === 'function' && v.ouverte() && typeof v.direChantier === 'function') {
          v.direChantier(etape, texte, { libelleOui: boutonOui.textContent, oui: () => boutonOui.click(), non: () => boutonNon.click() });
        }
      } catch (e) { /* rien */ }
      zoneDossier.hidden = !dossiers || !choisi;
      // 10/11/2026 (c92) : « Créer le dossier » caché quand le chantier a déjà son dossier (le bloc du haut restait trop haut ;
      // ce qui manquerait se complète par « Tout synchroniser », c147). Avant : boutonCreer.hidden = etape !== 'depart';
      boutonCreer.hidden = etape !== 'depart' || Boolean(choisi && dossiersConnus.has(choisi.id));
      // c105 : pas relu : pas de « Créer le dossier » pour un chantier absent de la liste ; la fiche dit qu'elle ne sait pas.
      if (etape === 'depart' && !dossiersRelus && choisi && !dossiersConnus.has(choisi.id)) {
        boutonCreer.hidden = true;
        if (!texte) texte = MESSAGE_INCONNU;
      }
      boutonOui.hidden = etape !== 'question';
      boutonNon.hidden = etape !== 'question';
      question.hidden = !texte;
      question.textContent = texte;
      boutonCreer.disabled = boutonOui.disabled = etape === 'travail';
      // 10/11/2026 (c86) : mode confirmation pendant la question (et pendant la création qui suit le Oui).
      fenetre.classList.toggle('mode-confirmation', etape === 'question' || (etape === 'travail' && enConfirmation));
      if (etape === 'question') { enConfirmation = true; try { fenetre.scrollTop = 0; } catch (e) { /* rien */ } }
      else if (etape !== 'travail') enConfirmation = false;
    }
    let enConfirmation = false;
    // 10/11/2026 (c86, demande de Max) : (c) un double toucher sur la fenêtre (hors boutons) pendant la question = « Non ».
    // Deux appuis à moins de 350 ms et à moins de 40 px l'un de l'autre ; un appui sur un bouton ne compte jamais.
    let dernierAppui = null;
    fenetre.addEventListener('pointerup', e => {
      if (!fenetre.classList.contains('mode-confirmation') || boutonOui.hidden) { dernierAppui = null; return; }
      if (e.target && e.target.closest && e.target.closest('button')) { dernierAppui = null; return; }
      const maintenantMs = Date.now();
      if (dernierAppui && maintenantMs - dernierAppui.t < 350 && Math.hypot(e.clientX - dernierAppui.x, e.clientY - dernierAppui.y) < 40) {
        dernierAppui = null;
        boutonNon.click();
        return;
      }
      dernierAppui = { t: maintenantMs, x: e.clientX, y: e.clientY };
    });
    const raisonDe = erreur => (erreur && erreur.message ? erreur.message : 'raison inconnue');
    // 11/11/2026 (accord de Max, c142, ligne 120 ; même idée que c139 à c141) : SANS RÉSEAU, chaque action qui passe par le
    // Drive du compte Cap dit la vraie cause, « Pas de réseau », au lieu de « compte Cap pas connecté : touche « Autoriser… » »
    // (le bouton ouvrirait la page d'erreur de Chrome). Rien n'est tenté, rien n'est changé.
    const pasDeReseau = fin => `Pas de réseau : cela passe par le Drive du compte Cap, sur Internet. Reconnecte le téléphone, puis réessaie. ${fin}`;
    async function demanderCreation() {
      const c = choisi;
      if (!c || !dossiers) return '';
      if (!dossiersRelus && !dossiersConnus.has(c.id)) { montrerDossier('depart', MESSAGE_INCONNU); return MESSAGE_INCONNU; } // c105
      if (!enLigne()) { const t = pasDeReseau('Rien n’a été créé.'); montrerDossier('depart', t); return t; } // c142
      if (!compteCap || (typeof compteCap.connecte === 'function' && !compteCap.connecte())) {
        const t = 'Le compte Cap n’est pas connecté (ou la connexion a expiré) : touche « Autoriser la lecture du compte Cap », puis reviens ici. Rien n’a été créé.';
        montrerDossier('depart', t);
        return t;
      }
      montrerDossier('travail', 'Je regarde ce qui existe déjà dans le Drive du compte Cap… (rien n’est créé)');
      try {
        plan = await dossiers.preparer(compteCap, c);
      } catch (erreur) {
        const t = `${raisonDe(erreur)} Rien n’a été créé.`;
        montrerDossier('depart', t);
        return t;
      }
      if (choisi !== c) return '';
      if (!plan.aCreer.length) { const t = `« ${c.nom} » a déjà son dossier et son journal : rien à créer.`; montrerDossier('fini', t); return t; }
      // 10/11/2026 (c102) : plus de limite du nombre de dossiers ; toujours un seul chantier, après la liste et le Oui de Max.
      const t = `Je vais créer, dans le Drive du compte Cap : ${plan.aCreer.join(', puis ')}. Rien d’autre, et rien dans la Liste. Je crée ?`;
      montrerDossier('question', t);
      return t;
    }
    async function confirmerCreation() {
      const c = choisi;
      if (!c || !plan || !dossiers) return '';
      montrerDossier('travail', 'Création en cours… (rien n’est effacé)');
      try {
        const r = await dossiers.creer(compteCap, c);
        plan = null;
        let t = r.dejaLa ? `« ${c.nom} » avait déjà son dossier : rien créé.` : `C’est fait, dans le Drive du compte Cap : ${r.cree.map(n => `« ${n} »`).join(', ')}.`;
        // 10/11/2026 (c88) : la ligne datée n'a pas pu être écrite : le dire (dossier et journal restent).
        if (r.ligneErreur) t += ` Mais la ligne datée du journal n’a pas pu être écrite : ${r.ligneErreur}`;
        montrerDossier('fini', t);
        void lireDossiersExistants(); // 10/11/2026 (c89)
        return t;
      } catch (erreur) {
        plan = null;
        const t = `${raisonDe(erreur)} Rien n’a été effacé ; tu peux réessayer : ce qui existe déjà ne sera pas recréé.`;
        montrerDossier('depart', t);
        return t;
      }
    }
    if (boutonCreer) boutonCreer.addEventListener('click', () => { void demanderCreation(); });
    // 12/11/2026 (c147, décision de Max, ligne 92) : la mise à niveau à l'écran (demanderMiseANiveau, confirmerMiseANiveau,
    // bouton « Mettre à niveau les dossiers déjà créés ») est RETIRÉE : « Tout synchroniser » (synchro_tout.js) appelle la
    // même préparation (chantiersDossiers.planMiseANiveau) et la même écriture, avec un seul Oui.
    // ----- 10/11/2026 (c92) : la note de Max. Cap MONTRE la ligne exacte (date et texte) et attend « Oui, ajouter ».
    function demanderNote() {
      const c = choisi;
      if (!c || !dossiers || !dossiersConnus.get(c.id)) return '';
      let ligne;
      try { ligne = dossiers.texteNote(champNote ? champNote.value : '', maintenant()); } catch (erreur) { const t = raisonDe(erreur); montrerDossier('depart', t); return t; }
      if (!enLigne()) { const t = pasDeReseau('Rien n’a été ajouté ; ta note est toujours dans le champ.'); montrerDossier('depart', t); return t; } // c142
      if (!compteCap || (typeof compteCap.connecte === 'function' && !compteCap.connecte())) {
        const t = 'Le compte Cap n’est pas connecté (ou la connexion a expiré) : touche « Autoriser la lecture du compte Cap », puis reviens ici. Rien n’a été ajouté.';
        montrerDossier('depart', t);
        return t;
      }
      actionAttendue = 'note';
      ligneEnAttente = ligne;
      plan = { note: true };
      if (boutonOui) boutonOui.textContent = 'Oui, ajouter';
      const t = `Je vais ajouter, à la fin du journal de « ${c.nom} » : « ${ligne} ». Rien d’autre n’est modifié ni effacé. J’ajoute ?`;
      montrerDossier('question', t);
      return t;
    }
    async function confirmerNote() {
      const c = choisi;
      const ligne = ligneEnAttente;
      if (!c || !ligne) return '';
      montrerDossier('travail', 'Ajout en cours… (rien n’est effacé)');
      try {
        await dossiers.ajouterNote(compteCap, c, ligne);
        if (champNote) champNote.value = '';
        if (zoneNote) zoneNote.hidden = true; // c97
        { const bt = el('taches-chantier'); if (bt && choisi) bt.hidden = false; } // c128
        const t = 'C’est fait : ta note est à la fin du journal du chantier.';
        montrerDossier('depart', t);
        try { const v = visionneuse(); if (v && v.ouverte && v.ouverte() && v.rafraichirJournal) void v.rafraichirJournal(); } catch (e) { /* rien */ } // c125 : le petit journal se met à jour
        return t;
      } catch (erreur) {
        const t = `${raisonDe(erreur)}${/rien n’a été ajouté/i.test(raisonDe(erreur)) ? '' : ' Rien n’a été effacé ; ta note est toujours dans le champ.'}`;
        montrerDossier('depart', t);
        ouvrirNote(true); // c97 : le texte reste visible
        return t;
      } finally { ligneEnAttente = ''; plan = null; actionAttendue = 'creation'; if (boutonOui) boutonOui.textContent = 'Oui, créer'; }
    }
    if (boutonNote) boutonNote.addEventListener('click', () => { demanderNote(); });
    // 10/11/2026 (c97) : « Note » ouvre (ou referme) le champ ; la zone de résultat se ferme.
    function ouvrirNote(ouvrir = true) {
      if (!zoneNote) return;
      zoneNote.hidden = !ouvrir;
      { const bt = el('taches-chantier'); if (bt && choisi) bt.hidden = ouvrir; } // c128 : une chose à la fois (place du champ sur un petit écran)
      if (ouvrir && lignesJournal) { lignesJournal.hidden = true; lignesJournal.replaceChildren(); }
      if (ouvrir && champNote) { try { champNote.focus({ preventScroll: true }); } catch (e) { /* rien */ } }
    }
    if (boutonOuvrirNote) boutonOuvrirNote.addEventListener('click', () => ouvrirNote(zoneNote ? zoneNote.hidden : true));
    // ----- 10/11/2026 (accord de Max, c95) : DICTER une note : « ajoute au journal, (note) », seulement quand la fiche d'un
    // chantier qui a un dossier est ouverte (et qu'aucune question n'est posée). Le texte va dans le champ, puis la même
    // question qu'au clavier (ligne datée exacte, « Oui, ajouter » / « Non ») : rien n'est écrit sans le Oui ; « Non » garde
    // le texte dans le champ, modifiable au clavier. Sinon : null, la phrase suit son chemin habituel (rien de perdu).
    const PHRASE_NOTE = /^\s*ajoute(?:r|z)?\s+(?:au|dans\s+le)\s+journal\b\s*(?:,|:|\.|virgule|deux\s+points)?\s*(.*)$/i;
    // 10/11/2026 (accord de Max, c104, correctif A) : DICTÉE EN DEUX TEMPS. « ajoute au journal » dit SEUL : Cap répond
    // « Je t'écoute : dis ta note. » et attend ; la phrase SUIVANTE (dans les 30 secondes, même fiche ouverte, aucune
    // question posée) va dans le champ, puis la même question (« Oui, ajouter » / « Non »). « annuler » arrête l'attente.
    // Attente dépassée, fiche changée ou écran fermé : l'attente tombe et la phrase suit son chemin habituel (rien de perdu).
    const ATTENTE_NOTE_MS = 30000;
    const PHRASE_ANNULER = /^\s*annul(?:e|er|ez)\s*[.!]?\s*$/i;
    let attenteNote = null; // { chantier: CH-xxx, jusqua: ms }
    function ficheNotePrete() {
      const c = choisi;
      return Boolean(fenetre.open && !fenetre.classList.contains('mode-confirmation') && c && dossiers && dossiersConnus.get(c.id) && champNote);
    }
    // 10/11/2026 (c105) : quand l'attente tombe d'elle-même (30 secondes passées), la fiche le DIT (avant : elle gardait
    // « Je t'écoute : dis ta note. »). Changement de fiche ou écran fermé : rien à dire (la fiche n'est plus là).
    const MESSAGE_FIN_ATTENTE = 'J’ai attendu 30 secondes : je n’attends plus ta note. Redis « ajoute au journal ». Rien n’a été ajouté.';
    let minuteurAttente = null;
    function noteEnAttente() {
      if (!attenteNote) return false;
      const memeFiche = ficheNotePrete() && choisi.id === attenteNote.chantier;
      if (maintenant() > attenteNote.jusqua || !memeFiche) {
        attenteNote = null;
        clearTimeout(minuteurAttente);
        if (memeFiche) montrerDossier('depart', MESSAGE_FIN_ATTENTE);
        return false;
      }
      return true;
    }
    function mettreDansLeChamp(texte) {
      attenteNote = null;
      clearTimeout(minuteurAttente); // c105
      champNote.value = texte;
      const t = demanderNote();
      return { message: t, echec: actionAttendue !== 'note' };
    }
    function noteParLaVoix(phrase) {
      const brut = String(phrase || '').trim();
      const x = PHRASE_NOTE.exec(brut);
      // Deuxième temps : la phrase attendue.
      if (noteEnAttente()) {
        if (PHRASE_ANNULER.test(brut)) { attenteNote = null; clearTimeout(minuteurAttente); const t = 'D’accord, je n’attends plus ta note. Rien n’a été ajouté.'; montrerDossier('depart', t); return { message: t, echec: false }; }
        const texte = x ? x[1].trim() : brut;
        if (texte) return mettreDansLeChamp(texte);
        if (!x) return null;
      }
      if (!x || !ficheNotePrete()) return null;
      const texte = x[1].trim();
      if (!texte) {
        attenteNote = { chantier: choisi.id, jusqua: maintenant() + ATTENTE_NOTE_MS };
        clearTimeout(minuteurAttente); // c105 : vérifie juste après les 30 secondes
        minuteurAttente = setTimeout(() => { noteEnAttente(); }, ATTENTE_NOTE_MS + 500);
        ouvrirNote(true);
        const t = 'Je t’écoute : dis ta note.';
        montrerDossier('depart', t);
        return { message: t, echec: false };
      }
      return mettreDansLeChamp(texte);
    }
    // ----- 11/11/2026 (accord de Max, c107) : TÉMOIN DU MICRO. Fiche d'un chantier ouverte : chaque dictée laisse une trace
    // visible de ce que Cap a REÇU d'Android (« Entendu à 08:12:03 : « … » ») ou « Rien entendu » (Android n'a rien rendu).
    // Sert à départager « Android n'a pas reconnu » de « Cap a reçu et perdu ». Rien n'est gardé ni envoyé : affichage seul.
    const temoin = el('temoin-micro-chantier');
    function temoinMicro(texte) {
      if (!temoin || !fenetre.open || !choisi) return '';
      const heure = new Date(maintenant()).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      const brut = String(texte || '').trim();
      const t = brut ? `Entendu à ${heure} : « ${brut} »` : `Rien entendu (${heure})`;
      temoin.textContent = t;
      temoin.hidden = false;
      // 11/11/2026 (accord de Max, c108) : une note est attendue et Android n'a RIEN rendu : la fiche le dit (avant : elle
      // restait sur « Je t'écoute : dis ta note. », ce qui trompait). L'attente continue (même délai) : la phrase suivante
      // va toujours dans le champ.
      if (!brut && noteEnAttente()) montrerDossier('depart', MESSAGE_RIEN_ENTENDU);
      return t;
    }
    const MESSAGE_RIEN_ENTENDU = 'Je n’ai rien entendu : retouche le micro et redis ta note.';
    function effacerTemoin() { if (temoin) { temoin.hidden = true; temoin.textContent = ''; } }
    chantiersEcran.temoinMicro = temoinMicro;
    chantiersEcran.noteParLaVoix = noteParLaVoix;
    chantiersEcran.choisirRang = choisirRang; // c132 : lu par app.js (« numéro N » = liste complète)
    chantiersEcran.nombreChantiers = () => dernieresTries.length;
    chantiersEcran.noteEnAttente = noteEnAttente; // c104 : lu par app.js (« annuler » passe ici avant les fenêtres)
    // ----- 10/11/2026 (c93) : les dernières lignes du journal, affichées dans la fiche (lecture seule).
    async function lireJournal() {
      const c = choisi;
      if (!c || !dossiers || !dossiersConnus.get(c.id) || !lignesJournal) return [];
      const numero = ++lecturesJournal;
      if (zoneNote) zoneNote.hidden = true; // c97 : une chose à la fois
      if (!enLigne()) { lignesJournal.hidden = false; lignesJournal.replaceChildren(noeud('p', 'journal-message', pasDeReseau('Le journal n’a pas été lu.'))); return []; } // c142
      if (!compteCap || (typeof compteCap.connecte === 'function' && !compteCap.connecte())) {
        lignesJournal.hidden = false;
        lignesJournal.replaceChildren(noeud('p', 'journal-message', 'Le compte Cap n’est pas connecté (ou la connexion a expiré) : touche « Autoriser la lecture du compte Cap ».'));
        return [];
      }
      lignesJournal.hidden = false;
      lignesJournal.replaceChildren(noeud('p', 'journal-message', 'Lecture du journal… (rien n’est modifié)'));
      let lignes;
      try { lignes = await dossiers.lireDernieresLignes(compteCap, c, 5); } catch (erreur) {
        if (numero === lecturesJournal) lignesJournal.replaceChildren(noeud('p', 'journal-message', raisonDe(erreur)));
        return [];
      }
      if (numero !== lecturesJournal || choisi !== c) return [];
      lignesJournal.replaceChildren(...(lignes.length ? [noeud('p', 'journal-titre', `Dernières lignes du journal (${lignes.length}) :`), ...lignes.map(l => noeud('p', 'journal-ligne', l))]
        : [noeud('p', 'journal-message', 'Le journal est vide.')]));
      try { lignesJournal.scrollIntoView({ block: 'nearest' }); } catch (e) { /* rien */ }
      return lignes;
    }
    if (boutonLire) boutonLire.addEventListener('click', () => { void lireJournal(); });
    // ----- 10/11/2026 (c96) : les documents du chantier (sous-dossier « Documents »), noms seulement, lecture seule.
    const MOSAIQUE_MAX = 40; // c109 : comme les vignettes de la visionneuse (mémoire du téléphone)
    const ETIQUETTES_SORTE = Object.freeze({ pdf: 'PDF', images: 'Image', musique: 'Musique', video: 'Vidéo', dossier: 'Dossier', autres: 'Autre' });
    // c110 : sortes que la visionneuse sait montrer (« images » de types_fichiers.js = « image » pour la visionneuse).
    const SORTES_VISIONNEUSE = Object.freeze({ pdf: 'pdf', images: 'image' });
    function ouvrirDocument(f) {
      const v = visionneuse();
      if (!v || typeof v.ouvrir !== 'function') {
        if (zoneDocuments) { const p = noeud('p', 'documents-message', 'La visionneuse n’est pas disponible ici : rien n’a été ouvert.'); zoneDocuments.prepend(p); }
        return false;
      }
      void v.ouvrir([{ id: f.id, sorte: SORTES_VISIONNEUSE[f.sorte] }]);
      return true;
    }
    chantiersEcran.ouvrirDocument = ouvrirDocument;
    // c111 : tous les PDF et images du chantier (relus à l'instant dans le Drive du compte Cap, lecture seule), en vignettes.
    async function ouvrirChantier(c) {
      const v = visionneuse();
      const dire = texte => { if (zoneDocuments) zoneDocuments.prepend(noeud('p', 'documents-message', texte)); return texte; };
      if (!v || typeof v.ouvrir !== 'function') return dire('La visionneuse n’est pas disponible ici : rien n’a été ouvert.');
      let r;
      try { r = await dossiers.listerDocuments(compteCap, c, 100000); } catch (erreur) { return dire(raisonDe(erreur)); }
      if (choisi !== c) return '';
      const liste = (r.fichiers || []).filter(f => SORTES_VISIONNEUSE[f.sorte] && f.id).map(f => ({ id: f.id, sorte: SORTES_VISIONNEUSE[f.sorte] }));
      if (!liste.length) return dire('Aucun PDF ni image dans ce chantier : rien n’a été ouvert.');
      // c124 : la visionneuse montre aussi le petit journal (5 dernières lignes, lecture seule, même lecture que « Journal »).
      void v.ouvrir(liste, { titre: c.nom, lireJournal: () => dossiers.lireDernieresLignes(compteCap, c, 5) });
      return `${liste.length}`;
    }
    chantiersEcran.ouvrirChantier = ouvrirChantier;
    async function voirDocuments() {
      const c = choisi;
      if (!c || !dossiers || !dossiersConnus.get(c.id) || !zoneDocuments) return null;
      const numero = ++lecturesDocuments;
      if (zoneNote) zoneNote.hidden = true; // c97 : une chose à la fois
      const message = texte => zoneDocuments.replaceChildren(noeud('p', 'documents-message', texte));
      zoneDocuments.hidden = false;
      if (!enLigne()) { message(pasDeReseau('Rien n’a été lu.')); return null; } // c142
      if (!compteCap || (typeof compteCap.connecte === 'function' && !compteCap.connecte())) { message('Le compte Cap n’est pas connecté (ou la connexion a expiré) : touche « Autoriser la lecture du compte Cap ».'); return null; }
      message('Lecture des documents… (rien n’est ouvert ni modifié)');
      let r;
      try { r = await dossiers.listerDocuments(compteCap, c, MOSAIQUE_MAX); } catch (erreur) { if (numero === lecturesDocuments) message(raisonDe(erreur)); return null; }
      if (numero !== lecturesDocuments || choisi !== c) return null;
      if (!r.total) { message('Aucun document pour l’instant.'); return r; }
      // 11/11/2026 (accord de Max, c109, séance 4, marche 1) : MOSAÏQUE : une case par fichier (40 au plus), avec son
      // type en gros (PDF, Image, Musique, Vidéo, Dossier, Autre) et son nom entier dessous. Avant (c96) : 10 noms en liste.
      // Rien n'est ouvert : les cases ne sont pas des boutons (l'ouverture viendra à la marche suivante, sur le Oui de Max).
      const liste = Array.isArray(r.fichiers) ? r.fichiers : r.noms.map(nom => ({ nom, sorte: 'autres' }));
      const reste = r.total - liste.length;
      // 11/11/2026 (accord de Max, c110, séance 4, marche 2) : une case PDF ou Image est un BOUTON : un toucher ouvre CE
      // fichier dans la visionneuse (lecture seule par le compte Cap, contenu en mémoire seulement, rien gardé ni envoyé ;
      // jamais à l'IA). « Fermer » ramène à la fiche. Les autres cases restent de simples cases.
      const caseDe = f => {
        const ouvrable = Boolean(SORTES_VISIONNEUSE[f.sorte] && f.id);
        const d = doc.createElement(ouvrable ? 'button' : 'div');
        if (ouvrable) {
          d.type = 'button';
          d.setAttribute('aria-label', `Ouvrir ${f.nom}`);
          d.addEventListener('click', () => { ouvrirDocument(f); });
        }
        d.className = `document-case document-${ETIQUETTES_SORTE[f.sorte] ? f.sorte : 'autres'}${ouvrable ? ' document-ouvrable' : ''}`;
        d.append(noeud('span', 'document-sorte', ETIQUETTES_SORTE[f.sorte] || ETIQUETTES_SORTE.autres), noeud('span', 'documents-nom', f.nom));
        return d;
      };
      const grille = doc.createElement('div');
      grille.className = 'documents-mosaique';
      grille.append(...liste.map(caseDe));
      // 11/11/2026 (accord de Max, c111, séance 4, marche 3) : « Ouvrir le chantier » : TOUS les PDF et images du
      // sous-dossier « Documents » en petites images dans la visionneuse (40 par écran, « Suivants », un toucher = en
      // grand), le nom du chantier en haut à gauche. Montré s'il peut y en avoir (case ouvrable visible ou fichiers en plus).
      const ouvrirTout = [];
      if (liste.some(f => SORTES_VISIONNEUSE[f.sorte] && f.id) || reste > 0) {
        const b = noeud('button', 'choix-grand-affichage documents-ouvrir-chantier', 'Ouvrir le chantier');
        b.type = 'button';
        b.addEventListener('click', () => { void ouvrirChantier(c); });
        ouvrirTout.push(b);
      }
      zoneDocuments.replaceChildren(noeud('p', 'documents-titre', `Documents du chantier : ${r.total} fichier${r.total > 1 ? 's' : ''}.`),
        ...ouvrirTout, grille, ...(reste > 0 ? [noeud('p', 'documents-reste', `et ${reste} autre${reste > 1 ? 's' : ''}.`)] : []));
      zoneDocuments.scrollTop = 0;
      try { zoneDocuments.scrollIntoView({ block: 'nearest' }); } catch (e) { /* rien */ }
      return r;
    }
    if (boutonDocuments) boutonDocuments.addEventListener('click', () => { void voirDocuments(); });
    // ----- 11/11/2026 (accord de Max, c128, séance 6b) : les TÂCHES du chantier dans l'onglet « Prêt » de « À faire »,
    // relues à chaque toucher (lecture seule, rien gardé), montrées dans la zone de résultat : en cours (tâche, priorité,
    // échéance) et le nombre de terminées. Cap ne coche rien et n'écrit rien dans « À faire ».
    const boutonTaches = el('taches-chantier');
    let lecturesTaches = 0;
    async function voirTaches() {
      const c = choisi;
      if (!c || !boutonTaches || !lignesJournal) return null;
      const numero = ++lecturesTaches;
      if (zoneNote) zoneNote.hidden = true; // une chose à la fois
      const message = texte => lignesJournal.replaceChildren(noeud('p', 'journal-message', texte));
      lignesJournal.hidden = false;
      message('Lecture de l’onglet « Prêt »… (rien n’est modifié)');
      let r;
      try { r = await lirePret(); } catch (erreur) { if (numero === lecturesTaches && choisi === c) message(raisonDe(erreur)); return null; }
      if (numero !== lecturesTaches || choisi !== c) return null;
      const e = r && r.parChantier && r.parChantier.get(c.id);
      if (!e || (!e.enCours.length && !e.terminees)) { message('Aucune tâche de ce chantier dans l’onglet « Prêt ».'); return e || null; }
      const pluriel = (n, mot) => `${n} ${mot}${n > 1 ? 's' : ''}`;
      lignesJournal.replaceChildren(
        noeud('p', 'taches-titre', `Tâches dans « Prêt » : ${pluriel(e.enCours.length, 'en cours')}, ${pluriel(e.terminees, 'terminée')}.`.replace('en courss', 'en cours')),
        ...e.enCours.map(t => noeud('p', 'tache-ligne', [t.tache, t.priorite && `priorité ${t.priorite}`, t.echeance && `échéance ${t.echeance}`].filter(Boolean).join(' — '))));
      lignesJournal.scrollTop = 0;
      try { lignesJournal.scrollIntoView({ block: 'nearest' }); } catch (err) { /* rien */ }
      return e;
    }
    if (boutonTaches) boutonTaches.addEventListener('click', () => { void voirTaches(); });
    if (boutonOui) boutonOui.addEventListener('click', () => { void (actionAttendue === 'note' ? confirmerNote() : confirmerCreation()); }); // c92 : + note
    if (boutonNon) boutonNon.addEventListener('click', () => {
      const etaitNote = actionAttendue === 'note';
      plan = null;
      if (etaitNote) { ligneEnAttente = ''; actionAttendue = 'creation'; if (boutonOui) boutonOui.textContent = 'Oui, créer'; ouvrirNote(true); } // c97 : le champ réapparaît, texte gardé
      montrerDossier('depart', etaitNote ? 'Rien n’a été ajouté.' : 'Rien n’a été créé.');
    });
    function montrerCompteurs(n) {
      if (!compteurs) return;
      const pluriel = (nombre, mot, invariable = false) => `${nombre} ${mot}${nombre > 1 && !invariable ? 's' : ''}`;
      const texte = n ? `Calculé : ${pluriel(n.rouge, 'rouge')} · ${n.orange} orange · ${pluriel(n.vert, 'vert')} · ${n.sansCouleur} sans couleur calculée (en veille ou archivé).`
        + (n.illisibles ? ` ${n.illisibles} chantier${n.illisibles > 1 ? 's' : ''} avec une date illisible.` : '') : '';
      compteurs.hidden = !texte;
      compteurs.textContent = texte;
    }
    function compterPrompts(liste) {
      if (!compteurPrompts) return;
      const n = (liste || []).filter(c => c.prompt).length;
      compteurPrompts.hidden = !(liste && liste.length);
      compteurPrompts.textContent = n === 1 ? '1 chantier a un prompt.' : `${n} chantiers ont un prompt.`;
    }
    // 11/11/2026 (accord de Max, c131) : la liste affichée = les chantiers dont le nom contient la recherche (sans
    // majuscules ni accents, n'importe où dans le nom). Champ vide = tous. Rien n'est relu : tout est sur le téléphone.
    let dernieresTries = [];
    const plat = x => String(x || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/\s+/g, ' ').trim();
    function dessinerListe(tries) {
      const req = plat(recherche ? recherche.value : '');
      const visibles = req ? tries.filter(c => plat(c.nom).includes(req)) : tries;
      if (message) message.hidden = !(req && visibles.length === 0);
      liste.replaceChildren(...visibles.map((c, i) => {
        const b = noeud('button', `ligne-morceau ligne-choix-voix ligne-chantier niveau-${c.niveau}`);
        b.type = 'button';
        const voyant = texteVoyant(c);
        b.dataset.voyant = NOMS_VOYANT[c.voyantTri !== undefined ? c.voyantTri : c.voyant] || 'aucun';
        b.append(noeud('span', 'numero-morceau', String(i + 1)), noeud('span', 'nom-morceau', c.nom),
          noeud('span', 'etat-chantier', `${voyant}${c.statut ? ` · ${c.statut}` : ''}`));
        b.setAttribute('aria-label', `${c.niveau ? 'Sous-chantier ' : ''}${c.nom}, voyant ${voyant}${c.statut ? `, ${c.statut}` : ''}`);
        b.addEventListener('click', () => montrerFiche(c));
        b.dataset.id = c.id || ''; // 10/11/2026 (c89) : pour la marque « dossier »
        return b;
      }));
      poserMarques();
    }
    function afficher(copie) {
      compterPrompts(copie ? copie.chantiers : []); // c94
      // 10/11/2026 (séance 2) : voyant calculé (règles de regles_voyant.js), puis tri sur la plus grave des deux couleurs.
      const evalue = source.evaluer ? source.evaluer(copie ? copie.chantiers : [], maintenant(), regles) : { chantiers: copie ? copie.chantiers : [], compteurs: null };
      montrerCompteurs(copie && copie.chantiers.length ? evalue.compteurs : null);
      const tries = source.trier(evalue.chantiers);
      dernieresTries = tries; // c131 : pour refiltrer sans relire quoi que ce soit
      dessinerListe(tries);
      if (note) {
        const n = copie ? copie.exemples || 0 : 0;
        note.hidden = n === 0;
        note.textContent = n ? `${n} exemple${n > 1 ? 's' : ''} fictif${n > 1 ? 's' : ''} masqué${n > 1 ? 's' : ''}.` : '';
      }
      poserMarques(); // 10/11/2026 (c89)
      void lireDossiersExistants();
      return tries.length;
    }

    // Ouvre l'écran tout de suite avec la copie du téléphone, puis relit la Liste (sans bloquer).
    function ouvrir() {
      const numero = ++lecture;
      const avant = source.copie();
      if (fiche) { fiche.hidden = true; fiche.textContent = ''; }
      montrerPrompt(null); // c94
      choisi = null; plan = null; montrerDossier('depart'); // 10/11/2026 (séance 3)
      { const bt = el('taches-chantier'); if (bt) bt.hidden = true; } // c128
      fenetre.classList.remove('fiche-ouverte'); // c130 : toujours la liste à l'ouverture
      effacerTemoin(); // c107
      afficher(avant);
      dire(avant ? '' : 'Lecture de la Liste des chantiers… (rien n’est modifié)');
      if (transition) transition.ouvrir(fenetre); else if (!fenetre.open) fenetre.showModal();
      // 12/11/2026 (accord de Max, c171) : la fenêtre donne la main au champ « Chercher un chantier » : le clavier s'ouvrait à
      // l'entrée. Le clavier ne s'ouvre plus qu'au toucher de la bulle.
      if (recherche && doc.activeElement === recherche) recherche.blur();
      return Promise.resolve().then(() => lire()).then(copie => {
        if (numero !== lecture) return '';
        const n = afficher(copie);
        const manque = copie.manquantes && copie.manquantes.length ? ` Colonnes introuvables : ${copie.manquantes.join(', ')}.` : '';
        dire(n ? (manque ? manque.trim() : '') : `Aucun chantier dans la Liste.${manque}`);
        return n ? `${n} chantier${n > 1 ? 's' : ''}.${manque}` : `Aucun chantier dans la Liste.${manque}`;
      }, erreur => {
        if (numero !== lecture) return '';
        const raison = erreur && erreur.message ? erreur.message : 'Lecture impossible.';
        const garde = source.copie();
        dire(garde ? `${raison} Voici la dernière copie (${new Date(garde.lu_le).toLocaleString('fr-FR')}).` : raison);
        return raison;
      });
    }
    function fermerEcran() { if (!fenetre.open) return; fenetre.classList.remove('fiche-ouverte'); if (transition) transition.fermer(fenetre); else fenetre.close(); }
    // c130 : « Fermer » sur une fiche ramène à la liste ; sur la liste, ferme la fenêtre.
    fermer.addEventListener('click', () => { if (fenetre.classList.contains('fiche-ouverte')) revenirALaListe(); else fermerEcran(); });

    // Voix : « ouvre les chantiers » (formulations ajoutées par Cap, commandes_vocales.js, code NAV-CH).
    if (commandes && typeof commandes.brancherAction === 'function') {
      commandes.brancherAction('NAV-CH', () => ({ message: 'J’ouvre les chantiers.', suite: ouvrir() }));
    }
    // 10/11/2026 (choix de Max) : l'icône « Chantiers » de l'écran Chercher (accueil_cap.js) ouvre le même écran.
    const parIcone = () => { ouvrir(); };
    doc.addEventListener('cap-ouvrir-chantiers', parIcone);
    // c132 : « numéro N » = le N-ième chantier de la liste COMPLÈTE, même si le filtre le cache.
    function choisirRang(n) {
      const c = dernieresTries[n - 1];
      if (!c) return false;
      montrerFiche(c);
      return true;
    }
    // 12/11/2026 (c152, C1) : depuis la carte d'un chantier (carte_cap.js) : l'écran des chantiers s'ouvre sur SA fiche, puis
    // fait l'action touchée sur la carte, exactement comme les boutons de la fiche (« journal », « documents », « taches »).
    async function ouvrirFicheDe(code, action) {
      void ouvrir();
      const c = dernieresTries.find(x => x.id === code);
      if (!c) return false;
      montrerFiche(c);
      if (action === 'journal') await lireJournal();
      else if (action === 'documents') await voirDocuments();
      else if (action === 'taches') await voirTaches();
      return true;
    }
    chantiersEcran.ouvrirFiche = ouvrirFicheDe; // c152 : lu par carte_cap.js
    return { ouvrirFicheDe, choisirRang, nombreChantiers: () => dernieresTries.length, ouvrir, fermer: fermerEcran, afficher, ouverte: () => fenetre.open, noteEnAttente, temoinMicro, voirTaches, dossiersRelus: () => dossiersRelus, demanderCreation, confirmerCreation, lireJournal, noteParLaVoix, voirDocuments,
      debrancher: () => { doc.removeEventListener('cap-ouvrir-chantiers', parIcone); if (chantiersEcran.noteParLaVoix === noteParLaVoix) chantiersEcran.noteParLaVoix = null; if (chantiersEcran.noteEnAttente === noteEnAttente) chantiersEcran.noteEnAttente = null; if (chantiersEcran.temoinMicro === temoinMicro) chantiersEcran.temoinMicro = null; clearTimeout(minuteurAttente); } };
  }
  return { brancher };
})();

if (typeof document !== 'undefined' && !(typeof window !== 'undefined' && window.CAP_TESTS)) {
  chantiersEcran.instance = chantiersEcran.brancher(document);
}
