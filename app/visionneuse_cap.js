'use strict';

// Visionneuse de Zencoder branchée dans Cap (étape B, lot 1 : les PDF ; 07/11/2026, accord de Max).
// La page de Zencoder (copie dans visionneuse/, avec ses changements datés) s'ouvre en plein écran dans un
// cadre, comme le lecteur de musique. Cap lit chaque PDF dans le Drive du compte Cap (lecture seule), en fait
// une adresse locale temporaire et la donne à la visionneuse (window.Visualiseur.montrerFichier, prévue par
// Zencoder). Au plus 4 documents à la fois (mémoire du téléphone). À la fermeture : documents fermés, adresses
// libérées, cadre vidé (l'animation s'arrête ; elle se rejoue à la prochaine ouverture).
// Aucun nom de fichier n'est montré ni gardé : la visionneuse reçoit « PDF 1.pdf », « PDF 2.pdf »…
const visionneuseCap = (() => {
  const drive = 'https://www.googleapis.com/drive/v3/files';
  const MAX_DOCUMENTS = 4;
  // 08/11/2026 (accord de Max) : VIGNETTES. Plusieurs documents = des vignettes légères (au plus 40 par écran, puis
  // « Suivants ») ; seul le document touché s'ouvre en grand dans la visionneuse. Une vignette pèse environ 1 Mo au lieu
  // de 18 Mo (page de PDF) ou 48 Mo (photo) : 40 vignettes tiennent dans la mémoire du téléphone (étude du 08/11/2026).
  const MAX_VIGNETTES = 40;
  const LARGEUR_VIGNETTE = 360;
  // 08/11/2026 (accord de Max) : « Autoriser » touché DANS la visionneuse : au retour de Google, Cap rouvre directement
  // la visionneuse (relations_compte.js lit et efface cette marque ; valable 10 minutes, jamais d'identifiant dedans).
  const CLE_RETOUR = 'cap_retour_visionneuse_v1';
  const DUREE_RETOUR_MS = 10 * 60 * 1000;
  // 08/11/2026 (accord de Max) : même marque pour « Autoriser » touché dans la fenêtre « Musique » (Lecteur de Autre) :
  // au retour de Google, relations_compte.js rouvre directement la musique.
  const CLE_RETOUR_MUSIQUE = 'cap_retour_musique_v1';
  const estExpiration = erreur => /expir|pas connecté/i.test(String(erreur && erreur.message || ''));

  // 08/11/2026 (décision de Max) : l'étiquette de maquette « FICTIF — essai visualiseur » de Zencoder est cachée
  // (affichage seulement : aucun code ne s'en sert). Retouche posée par Cap dans la page chargée ; le fichier de
  // Zencoder n'est pas modifié (son texte reste dans la page).
  function retoucherVisionneuse(docVisionneuse) {
    if (!docVisionneuse || !docVisionneuse.head || docVisionneuse.getElementById('retouches-cap')) return;
    const style = docVisionneuse.createElement('style');
    style.id = 'retouches-cap';
    // 09/11/2026 (accord de Max) : le « Fermer » de la page (tout en haut à droite) passe JUSTE SOUS le petit micro de
    // tous les écrans (12 px + 52 px + 12 px), même bord droit. Page de Zencoder non modifiée. Avant : seulement l'étiquette.
    // 09/11/2026 (décision de Max après c72) : visionneuse VIDE : aucun texte (« aucun fichier charge » caché ; il reste
    // dans la page, rien n'est effacé) ; « Choisir un fichier » en HAUT À GAUCHE (le petit livre et le petit micro sont en
    // haut à droite) ; tout le reste : l'eau. Avant : seulement les deux premières règles.
    style.textContent = '#visualiseur .etiquette-fictif { display: none; }'
      + ' #bouton-fermer { top: 76px !important; right: 12px !important; }'
      + ' #titre-fichier { display: none !important; }'
      // 11/11/2026 (accord de Max, c114) : mosaïque d'un chantier (miniatures en grille, la zone défile s'il y en a
      // beaucoup ; cachée sous le document agrandi) ; en mode chantier, « Choisir un fichier » laisse la place au nom.
      + ' #zone-image.en-mosaique { overflow-y: auto; overscroll-behavior: contain; }'
      + ' #zone-image.agrandi-sur-mosaique { overflow: hidden; }' // c119 : la mosaïque reste visible, seul son défilement s'arrête
      // 11/11/2026 (c121) : miniature saisie par un appui long : elle se soulève (ombre, un peu plus grande, contour vif).
      + ' #zone-image .carte-miniature.miniature-saisie { transform: scale(1.06); box-shadow: 0 8px 22px rgba(0, 0, 0, 0.45); border-color: #ffffff; opacity: 0.95; }'
      + ' #zone-image .carte-miniature { position: absolute; box-sizing: border-box; border: 2px solid rgba(255, 255, 255, 0.7);'
      + ' border-radius: 10px; overflow: hidden; background: rgba(255, 255, 255, 0.18); cursor: pointer; }'
      + ' #zone-image .carte-miniature img { display: block; width: 100%; height: 100%; object-fit: contain; pointer-events: none; }'
      + ' #zone-image .carte-miniature.miniature-en-chargement { opacity: 0.45; }'
      // 11/11/2026 (c117) : case sans miniature : le texte qui dit pourquoi, lisible (avant : case pâle et vide).
      + ' #zone-image .carte-miniature .texte-miniature { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;'
      + ' padding: 6px; text-align: center; font: 600 13px/1.25 sans-serif; color: #102020; background: rgba(255, 255, 255, 0.82); overflow-wrap: anywhere; }'
      + ' body.mode-chantier-cap #bouton-choisir { display: none !important; }'
      // 11/11/2026 (c118, marche 1) : les documents et la mosaïque commencent SOUS la barre de Cap (64 px) ; « Fermer »,
      // « Ajouter un fichier » et « Choisir un fichier » de la page sont dans le menu du bouton blanc (Cap).
      + ' #zone-image { top: var(--haut-cap, 64px) !important; }' // c124 : 64 px de barre, plus le petit journal s'il est là
      + ' #bouton-fermer, #bouton-ajouter, #bouton-choisir { display: none !important; }'
      + ' #bouton-choisir { position: fixed !important; top: 12px !important; left: 12px !important; margin: 0 !important;'
      + ' min-height: 52px; font-size: 1.05rem !important; z-index: 5; }';
    docVisionneuse.head.appendChild(style);
  }

  // Page de Zencoder dans le cadre : rechargée à chaque ouverture, vidée à la fermeture.
  function chargeur(cadre) {
    let promesse = null;
    const charger = () => {
      if (!promesse) {
        promesse = new Promise((ok, refus) => {
          const surChargement = () => {
            let adresse = '';
            try { adresse = String(cadre.contentWindow.location.href); } catch (erreur) { /* pas encore lisible */ }
            if (!/visionneuse\/index\.html/.test(adresse)) return; // page blanche de la fermeture précédente
            cadre.removeEventListener('load', surChargement);
            const v = cadre.contentWindow.Visualiseur;
            if (v && typeof v.montrerFichier === 'function' && typeof v.fermer === 'function') {
              try { retoucherVisionneuse(cadre.contentWindow.document); } catch (erreur) { /* affichage seulement */ }
              ok(v);
            }
            else { promesse = null; refus(new Error('La visionneuse n’a pas pu démarrer.')); }
          };
          cadre.addEventListener('load', surChargement);
          cadre.src = 'visionneuse/index.html';
        });
      }
      return promesse;
    };
    charger.vider = () => { promesse = null; cadre.src = 'about:blank'; };
    return charger;
  }

  // 08/11/2026 (vignettes) : une vignette JPEG d'au plus 360 pixels de large ; l'original est relâché aussitôt.
  async function fabriquerVignette(doc, sorte, contenu, pdfjs) {
    const vue = doc.defaultView;
    const toile = doc.createElement('canvas');
    if (sorte === 'image') {
      // 11/11/2026 (accord de Max, c117) : une photo de téléphone (12 Mpx et plus) n'est plus décodée en entier (48 Mo et plus
      // pour une seule miniature) : elle est décodée DIRECTEMENT à la largeur de la miniature (le navigateur ne garde que la
      // petite image), dans le bon sens (orientation de l'appareil photo). Si ce décodage échoue, secours : l'image comme
      // pour l'affichage en grand (même décodeur), puis réduite. Avant : createImageBitmap(contenu) en taille réelle.
      let image = null;
      let liberer = () => {};
      try {
        image = await vue.createImageBitmap(contenu, { resizeWidth: LARGEUR_VIGNETTE, resizeQuality: 'medium', imageOrientation: 'from-image' });
        liberer = () => { if (image.close) image.close(); };
      } catch (erreur) {
        const adresse = vue.URL.createObjectURL(contenu);
        const img = new vue.Image();
        img.src = adresse;
        try { await img.decode(); } catch (e) { vue.URL.revokeObjectURL(adresse); throw new Error('image illisible pour une miniature'); }
        image = img;
        liberer = () => { vue.URL.revokeObjectURL(adresse); img.src = ''; };
      }
      try {
        const largeur = image.naturalWidth || image.width;
        const hauteur = image.naturalHeight || image.height;
        const echelle = Math.min(1, LARGEUR_VIGNETTE / largeur);
        toile.width = Math.max(1, Math.round(largeur * echelle));
        toile.height = Math.max(1, Math.round(hauteur * echelle));
        toile.getContext('2d').drawImage(image, 0, 0, toile.width, toile.height);
      } finally { liberer(); }
    } else {
      if (!pdfjs) throw new Error('lecteur de PDF absent');
      const lib = await pdfjs();
      const pdf = await lib.getDocument({ data: new Uint8Array(await contenu.arrayBuffer()) }).promise;
      try {
        const page = await pdf.getPage(1);
        const base = page.getViewport({ scale: 1 });
        const vue2 = page.getViewport({ scale: Math.min(2, LARGEUR_VIGNETTE / base.width) });
        toile.width = Math.max(1, Math.round(vue2.width));
        toile.height = Math.max(1, Math.round(vue2.height));
        await page.render({ canvasContext: toile.getContext('2d'), viewport: vue2 }).promise;
      } finally { pdf.destroy(); }
    }
    const petit = await new Promise((ok, refus) => toile.toBlob(b => (b ? ok(b) : refus(new Error('vignette impossible'))), 'image/jpeg', 0.8));
    toile.width = 0;
    toile.height = 0;
    return petit;
  }

  // 08/11/2026 (vignettes) : + « pdfjs » (pour la première page des PDF) et « vignette » (remplaçable dans les tests).
  function brancher(doc, { compte, visionneuse, urls = URL, stockage = (typeof localStorage !== 'undefined' ? localStorage : null), maintenant = () => Date.now(),
    pdfjs = null, vignette = (sorte, contenu) => fabriquerVignette(doc, sorte, contenu, pdfjs),
    // 11/11/2026 (c133) : la Liste des chantiers (chantiers.js : copie du téléphone, puis relecture, lecture seule) et leurs
    // dossiers (chantiers_dossiers.js, compte Cap, lecture seule) ; cherchés au moment du toucher (chargés après ce fichier).
    sourceChantiers = () => (typeof chantiers !== 'undefined' ? chantiers : null),
    dossiersChantiers = () => (typeof chantiersDossiers !== 'undefined' ? chantiersDossiers : null),
    // 11/11/2026 (c141) : le téléphone a-t-il du réseau ? (remplaçable dans les tests)
    enLigne = () => (typeof navigator === 'undefined' || navigator.onLine !== false),
    dureeMenuMs = 4000, // c118 : le menu du bouton blanc se referme seul après 4 s sans toucher
    // 11/11/2026 (c117) : temps maximal pour UNE miniature (lecture + fabrication) ; remplaçable dans les tests.
    delaiMiniatureMs = 25000,
    minuteur = (f, ms) => setTimeout(f, ms), annulerMinuteur = id => clearTimeout(id), // c117 : remplaçables dans les tests
    // 08/11/2026 (étape 3c) : la page de Zencoder chargée (pour ses boutons de page) ; remplaçable dans les tests.
    pageZencoder = () => { try { const c = doc.getElementById('cadre-visionneuse'); return c && c.contentDocument; } catch (erreur) { return null; } } }) {
    const el = id => doc.getElementById(id);
    const fenetre = el('visionneuse-cap');
    const etat = el('etat-visionneuse');
    const fermer = el('fermer-visionneuse');
    const autoriser = el('autoriser-visionneuse'); // 08/11/2026 (facultatif)
    if (!fenetre || !etat || !fermer) return null;
    const raison = erreur => String(erreur && erreur.message || 'raison inconnue').slice(0, 220);
    const message = texte => { etat.hidden = false; etat.textContent = texte; };
    let adresses = [];
    let pret = null;
    let demande = 0;
    let nettoye = true;
    const proposerAutorisation = oui => { if (autoriser) autoriser.hidden = !oui; };
    // 11/11/2026 (accord de Max, c141, ligne 120 ; même idée que c139 et c140) : une lecture du Drive ratée SANS RÉSEAU dit la
    // vraie cause, « Pas de réseau », sans bouton « Autoriser… » (il ouvrirait la page d'erreur de Chrome). Avant : « La
    // connexion du compte Cap a expiré : touche « Autoriser… » » quand le jeton était périmé.
    const PAS_DE_RESEAU_DOC = 'Pas de réseau : les documents du compte Cap se lisent par Internet. Reconnecte le téléphone, puis réessaie. Rien n’a été modifié.';

    // 08/11/2026 : message dans la visionneuse ouverte (jamais un écran vide) ; « Autoriser… » si demandé.
    function annoncer(texte, { autorisation = false, enLecture = false } = {}) {
      demande++;
      if (!fenetre.open) fenetre.showModal();
      nettoye = false;
      message(texte);
      etat.classList.toggle('en-lecture', enLecture);
      proposerAutorisation(autorisation);
    }
    if (autoriser) {
      autoriser.addEventListener('click', () => {
        try {
          if (stockage) stockage.setItem(CLE_RETOUR, String(maintenant()));
          compte.seConnecter();
        } catch (erreur) {
          try { if (stockage) stockage.removeItem(CLE_RETOUR); } catch (e) { /* rien */ }
          message(raison(erreur));
        }
      });
    }

    // 09/11/2026 (décision de Max après c72) : la visionneuse SANS document : la page s'ouvre, sans aucun message (l'eau et
    // « Choisir un fichier » en haut à gauche) ; rien ne se passe tant que Max ne touche pas « Choisir un fichier ».
    async function ouvrirVide() {
      const numero = ++demande;
      if (!fenetre.open) fenetre.showModal();
      nettoye = false;
      proposerAutorisation(false);
      etat.textContent = '';
      etat.hidden = true;
      etat.classList.remove('en-lecture');
      try {
        const v = await visionneuse();
        if (numero !== demande || !fenetre.open) return;
        pret = v;
        brancherFermerHaut();
      } catch (erreur) {
        if (numero === demande) message(`La visionneuse n’a pas pu s’ouvrir : ${raison(erreur)}`);
      }
    }

    // liste : [{ id }] (identifiants Drive des PDF) ; seuls les 4 premiers sont ouverts.
    // 08/11/2026 (vignettes) : renommée « ouvrirEnGrand » (avant : « ouvrir ») ; sert pour un document touché ou un seul.
    async function ouvrirEnGrand(liste) {
      const numero = ++demande;
      if (!fenetre.open) fenetre.showModal();
      nettoye = false;
      proposerAutorisation(false);
      const choisis = (liste || []).slice(0, MAX_DOCUMENTS);
      const enTrop = Math.max(0, (liste || []).length - MAX_DOCUMENTS);
      // 08/11/2026 (étape 3a) : PDF ou images. Avant : `Lecture en cours… (${choisis.length} PDF)`.
      message(`Lecture en cours… (${choisis.length} document${choisis.length > 1 ? 's' : ''})`);
      etat.classList.add('en-lecture');
      try {
        const v = await visionneuse();
        if (numero !== demande || !fenetre.open) return;
        pret = v;
        brancherFermerHaut(); // 09/11/2026
        for (let i = 0; i < choisis.length; i++) {
          const reponse = await compte.appeler(`${drive}/${encodeURIComponent(choisis[i].id)}?alt=media`);
          const contenu = await reponse.blob();
          if (numero !== demande || !fenetre.open) return;
          const adresse = urls.createObjectURL(contenu);
          adresses.push(adresse);
          // 08/11/2026 (étape 3a) : une image (sorte « image ») porte un titre d'image ; avant : toujours `PDF ${i + 1}.pdf`.
          v.montrerFichier(adresse, choisis[i].sorte === 'image' ? `Image ${i + 1}.jpg` : `PDF ${i + 1}.pdf`);
        }
        if (enTrop) message(`${MAX_DOCUMENTS} documents au plus à la fois : ${enTrop} autre(s) pas ouvert(s).`);
        else { etat.textContent = ''; etat.hidden = true; }
      } catch (erreur) {
        if (numero !== demande) return;
        if (!enLigne()) { message(PAS_DE_RESEAU_DOC); proposerAutorisation(false); return; } // c141
        // 08/11/2026 : expiration = bouton « Autoriser » ici même (retour direct dans la visionneuse).
        const expire = estExpiration(erreur);
        message(expire
          ? (autoriser
            ? 'La connexion du compte Cap a expiré : touche « Autoriser la lecture du compte Cap », tu reviendras ici.'
            : 'La connexion du compte Cap a expiré : autorise-la à nouveau dans « Réglages du Drive », puis rouvre le PDF.')
          : `PDF non ouvert : ${raison(erreur)}`);
        proposerAutorisation(expire);
      } finally {
        if (numero === demande) etat.classList.remove('en-lecture');
      }
    }

    // 09/11/2026 (décision de Max) : le gros « Fermer la visionneuse » du bas est caché. Le « Fermer » de la page de
    // Zencoder (en haut à droite, au-dessus du petit micro) ne vidait que ses documents ; il ferme maintenant AUSSI la
    // visionneuse de Cap (même chemin que l'ancien bouton du bas : mémoire libérée, retour aux vignettes s'il y en a).
    // Page de Zencoder non modifiée : l'écoute est posée depuis Cap, une fois par chargement de la page.
    function brancherFermerHaut() {
      let page = null;
      try { page = pageZencoder(); } catch (erreur) { page = null; }
      const haut = page && page.getElementById ? page.getElementById('bouton-fermer') : null;
      if (!haut || haut.dataset.fermeCap === 'oui') return;
      haut.dataset.fermeCap = 'oui';
      haut.addEventListener('click', () => { if (fenetre.open) fermer.click(); });
    }

    // Fermeture (bouton, ou retour du téléphone) : une seule fois par ouverture.
    function nettoyer() {
      if (nettoye) return;
      nettoye = true;
      try { montrerJournal(null, { replacer: false }); journalChantier = null; } catch (e) { /* rien */ } // c124 : la page se vide, rien à replacer
      try { fermerQuestionNote(); if (messageChantier) messageChantier.hidden = true; } catch (e) { /* rien */ } // c125 : la question reste dans la fiche
      try { const c = el('confirmer-depart-visionneuse'); if (c) c.hidden = true; } catch (e) { /* rien */ } // c123
      montrerTitreChantier(''); // c114
      demande++;
      etat.classList.remove('en-lecture');
      proposerAutorisation(false);
      try { if (pret) pret.fermer(); } catch (erreur) { /* la page est peut-être déjà partie */ }
      pret = null;
      for (const a of adresses) urls.revokeObjectURL(a);
      adresses = [];
      if (typeof visionneuse.vider === 'function') visionneuse.vider();
    }
    // 11/11/2026 (c133) : « Fermer » (bouton, voix, retour du téléphone) passe d'abord par la mosaïque des chantiers quand
    // elle est ouverte ou qu'un chantier a été ouvert depuis elle (retourVersChantiers, plus bas). Avant :
    // fenetre.addEventListener('cancel', nettoyer); et fermer : () => { nettoyer(); if (fenetre.open) fenetre.close(); }
    fenetre.addEventListener('cancel', e => { if (retourVersChantiers()) { e.preventDefault(); return; } nettoyer(); });
    fenetre.addEventListener('close', () => { if (!fenetre.open) { oublierGrilleChantiers(); nettoyer(); } });
    fermer.addEventListener('click', () => { if (retourVersChantiers()) return; nettoyer(); if (fenetre.open) fenetre.close(); });

    // ----- 11/11/2026 (accord de Max, c118, marche 1) : le BOUTON ROND BLANC et son menu en ligne (brancherMenu, plus bas).
    brancherMenu(doc, { dureeMenuMs });
    const menuFermer = el('menu-fermer-visionneuse');
    if (menuFermer) menuFermer.addEventListener('click', () => fermer.click());
    // « Ajouter un fichier » : choisi sur le téléphone par Cap (pas par la page), puis montré dans la visionneuse, comme le
    // bouton de la page le faisait. Rien n'est envoyé ni gardé ; mémoire relâchée à la fermeture.
    const fichierLocal = el('fichier-visionneuse');
    const menuAjouter = el('menu-ajouter-visionneuse');
    if (menuAjouter && fichierLocal) {
      menuAjouter.addEventListener('click', () => fichierLocal.click());
      // 11/11/2026 (accord de Max, c137, ligne 111) : un message en bas (6 s) dit ce qui s'est passé : fichier(s) ajouté(s), ou
      // rien choisi. Il ne touche pas à une question en cours (note dictée). Avant : aucun message.
      const direAjout = texte => {
        if (!messageChantier || !fenetre.open) return;
        clearTimeout(minuteurMessage);
        messageChantier.textContent = texte;
        messageChantier.hidden = false;
        minuteurMessage = setTimeout(() => { messageChantier.hidden = true; }, 6000);
      };
      const RIEN_CHOISI = 'Aucun fichier choisi : rien n’a été ajouté.';
      fichierLocal.addEventListener('cancel', () => direAjout(RIEN_CHOISI)); // choix fermé sans rien prendre
      fichierLocal.addEventListener('change', async () => {
        const fichiers = [...(fichierLocal.files || [])];
        fichierLocal.value = '';
        if (!fichiers.length) { direAjout(RIEN_CHOISI); return; }
        let v;
        try { v = pret || await visionneuse(); } catch (erreur) { message(`La visionneuse n’a pas pu s’ouvrir : ${raison(erreur)}`); return; }
        if (!fenetre.open) return;
        pret = v;
        nettoye = false;
        brancherFermerHaut();
        v.montrerPlusieurs(fichiers.map(f => { const adresse = urls.createObjectURL(f); adresses.push(adresse); return { adresse, titre: f.name }; }));
        direAjout(fichiers.length === 1 ? `Fichier ajouté : « ${fichiers[0].name} ».` : `${fichiers.length} fichiers ajoutés.`); // c137
      });
    }
    // 11/11/2026 (accord de Max, c123) : « ↺ » ne remet plus rien tout de suite : il DEMANDE « Tout remettre comme au départ ? ».
    // Seul « Oui » remet tout (grille, ordre, plans, documents) ; « Non », un double toucher hors des boutons, ou la
    // fermeture de la visionneuse : RIEN ne change. Avant (c118) : remise immédiate.
    const menuDepart = el('menu-depart-visionneuse');
    const confirmerDepart = el('confirmer-depart-visionneuse');
    const ouiDepart = el('oui-depart-visionneuse');
    const nonDepart = el('non-depart-visionneuse');
    const fermerDemande = () => { if (confirmerDepart) confirmerDepart.hidden = true; };
    if (menuDepart && confirmerDepart && ouiDepart && nonDepart) {
      menuDepart.addEventListener('click', () => { confirmerDepart.hidden = false; try { nonDepart.focus({ preventScroll: true }); } catch (e) { /* rien */ } });
      ouiDepart.addEventListener('click', () => {
        fermerDemande();
        try { if (pret && typeof pret.remettreCommeAuDepart === 'function') pret.remettreCommeAuDepart(); } catch (e) { /* rien */ }
      });
      nonDepart.addEventListener('click', fermerDemande);
      // Double toucher hors des boutons = « Non » (même règle que les autres fenêtres de confirmation de Cap).
      let dernierAppuiDepart = null;
      confirmerDepart.addEventListener('pointerup', e => {
        if (e.target && e.target.closest && e.target.closest('button')) { dernierAppuiDepart = null; return; }
        const t = Date.now();
        if (dernierAppuiDepart && t - dernierAppuiDepart.t < 350 && Math.hypot(e.clientX - dernierAppuiDepart.x, e.clientY - dernierAppuiDepart.y) < 40) {
          dernierAppuiDepart = null;
          nonDepart.click();
          return;
        }
        dernierAppuiDepart = { t, x: e.clientX, y: e.clientY };
      });
      fenetre.addEventListener('close', fermerDemande); // visionneuse fermée : rien n'est remis à zéro
    }

    // ----- 08/11/2026 (accord de Max) : VIGNETTES (écran de choix sur l'eau, à la règle dès sa création) -----
    // Plusieurs documents : grille de vignettes (au plus 40 par écran ; « Suivants » s'il y en a plus), chargées une à
    // une (les premières d'abord) ; toucher une vignette ouvre CE document en grand dans la visionneuse, par-dessus ;
    // « Fermer la visionneuse » ramène aux vignettes. Fermer les vignettes libère toute leur mémoire.
    // Aucun nom de fichier n'est montré. Connexion expirée : message et « Autoriser la lecture du compte Cap ».
    const fenetreVignettes = el('vignettes-cap');
    const grille = el('grille-vignettes');
    const suivants = el('suivants-vignettes');
    const fermerVignettes = el('fermer-vignettes');
    const etatVignettes = el('etat-vignettes');
    const autoriserVignettes = el('autoriser-vignettes');
    const transition = typeof choixSurEau !== 'undefined' ? choixSurEau : null;
    const vignettesPossibles = Boolean(fenetreVignettes && grille && suivants && fermerVignettes);
    let listeVignettes = [];
    let indexEnGrand = -1; // 08/11/2026 (étape 3c) : document des vignettes ouvert en grand (-1 : aucun ou hors liste)
    let debutVignettes = 0;
    let adressesVignettes = [];
    let lotVignettes = 0;
    const libererVignettes = () => { lotVignettes++; for (const a of adressesVignettes) urls.revokeObjectURL(a); adressesVignettes = []; };
    const viderVignettes = () => { libererVignettes(); if (grille) grille.replaceChildren(); }; // à la fermeture : plus rien de l'écran d'avant
    function messageVignettes(texte, autorisation = false) {
      if (etatVignettes) { etatVignettes.hidden = !texte; etatVignettes.textContent = texte || ''; }
      if (autoriserVignettes) autoriserVignettes.hidden = !autorisation;
    }
    async function remplirVignettes() {
      libererVignettes();
      const lot = lotVignettes;
      const montres = listeVignettes.slice(debutVignettes, debutVignettes + MAX_VIGNETTES);
      messageVignettes('');
      const boutons = montres.map((d, i) => {
        const b = doc.createElement('button');
        b.type = 'button';
        b.className = 'vignette en-chargement';
        b.setAttribute('aria-label', `Document ${debutVignettes + i + 1}`);
        const position = debutVignettes + i; // 08/11/2026 (étape 3c) : place du document dans la liste (suivant / précédent)
        b.addEventListener('click', () => { indexEnGrand = position; void ouvrirEnGrand([d]); });
        return b;
      });
      grille.replaceChildren(...boutons);
      suivants.hidden = listeVignettes.length <= debutVignettes + MAX_VIGNETTES;
      for (let i = 0; i < montres.length; i++) {
        if (lot !== lotVignettes || !fenetreVignettes.open) return;
        try {
          const reponse = await compte.appeler(`${drive}/${encodeURIComponent(montres[i].id)}?alt=media`);
          const contenu = await reponse.blob();
          if (lot !== lotVignettes) return;
          const petit = await vignette(montres[i].sorte === 'image' ? 'image' : 'pdf', contenu);
          if (lot !== lotVignettes) return;
          const adresse = urls.createObjectURL(petit);
          adressesVignettes.push(adresse);
          const img = doc.createElement('img');
          img.alt = '';
          img.src = adresse;
          boutons[i].replaceChildren(img);
          boutons[i].classList.remove('en-chargement');
        } catch (erreur) {
          if (lot !== lotVignettes) return;
          if (!enLigne()) { messageVignettes(PAS_DE_RESEAU_DOC, false); return; } // c141
          if (estExpiration(erreur)) {
            messageVignettes('La connexion du compte Cap a expiré : touche « Autoriser la lecture du compte Cap », tu reviendras ici.', Boolean(autoriserVignettes));
            return;
          }
          boutons[i].classList.remove('en-chargement');
          boutons[i].classList.add('vignette-illisible'); // la vignette reste touchable : le document s'ouvre quand même en grand
        }
      }
    }
    // 11/11/2026 (c111) : « titre » = nom du chantier ouvert, en haut à gauche ; vide = aucun titre (comme avant).
    const titreVignettes = el('titre-vignettes');
    function ouvrirVignettes(liste, titre = '') {
      if (fenetre.open) { nettoyer(); fenetre.close(); } // l'éventuel « Lecture en cours… » de l'œil
      if (titreVignettes) { titreVignettes.textContent = String(titre || ''); titreVignettes.hidden = !titre; }
      listeVignettes = liste;
      debutVignettes = 0;
      if (transition) transition.ouvrir(fenetreVignettes); else if (!fenetreVignettes.open) fenetreVignettes.showModal();
      return remplirVignettes();
    }
    if (vignettesPossibles) {
      suivants.addEventListener('click', () => { debutVignettes += MAX_VIGNETTES; if (debutVignettes >= listeVignettes.length) debutVignettes = 0; void remplirVignettes(); });
      fermerVignettes.addEventListener('click', () => {
        libererVignettes();
        if (transition) transition.fermer(fenetreVignettes); else fenetreVignettes.close();
        // La grille est vidée après le fondu de fermeture (sans compter sur l'événement « close », pas toujours reçu).
        setTimeout(() => { if (!fenetreVignettes.open) viderVignettes(); }, (transition ? transition.REGLAGES.sortieMs : 0) + 60);
      });
      fenetreVignettes.addEventListener('close', () => { if (!fenetreVignettes.open) viderVignettes(); });
      if (autoriserVignettes) autoriserVignettes.addEventListener('click', () => {
        try { if (stockage) stockage.setItem(CLE_RETOUR, String(maintenant())); compte.seConnecter(); } catch (erreur) { messageVignettes(raison(erreur)); }
      });
    }
    // 08/11/2026 (vignettes) : plusieurs documents = vignettes ; un seul = en grand directement. Avant : toujours en grand (4 au plus).
    // ----- 11/11/2026 (accord de Max, c114) : « Ouvrir le chantier » ouvre DIRECTEMENT la vraie visionneuse, avec les
    // documents du chantier déjà dedans, en MOSAÏQUE (miniatures faites sur le téléphone, environ 1 Mo chacune, 60 au
    // plus). Un toucher sur une miniature : Cap lit CE document entier (lecture seule, compte Cap) et la visionneuse
    // l'ouvre comme n'importe quel document (même zoom, même déplacement, mêmes pages) ; un toucher simple le remet à
    // sa place et sa mémoire est relâchée : UN SEUL document entier à la fois. Nom du chantier en haut à gauche.
    // Rien n'est gardé ni envoyé (jamais à l'IA). Avant (c111 à c113) : un écran de miniatures à part.
    const MAX_CHANTIER = 60;
    const titreChantier = el('titre-visionneuse');
    function montrerTitreChantier(titre) {
      if (titreChantier) { titreChantier.textContent = String(titre || ''); titreChantier.hidden = !titre; }
      try { const p = pageZencoder(); if (p && p.body) p.body.classList.toggle('mode-chantier-cap', Boolean(titre)); } catch (e) { /* rien */ }
    }
    // ----- 11/11/2026 (accord de Max, c124) : le PETIT JOURNAL du chantier ouvert, sous la barre : ses 5 dernières lignes, lues
    // par la fiche du chantier (même lecture que « Journal », lecture seule) ; la mosaïque de la page commence dessous.
    const journalVision = el('journal-visionneuse');
    let journalChantier = null; // () => Promise<lignes> (donné par l'écran Chantiers)
    function ajusterHaut() {
      try {
        const p = pageZencoder();
        if (!p || !p.documentElement) return;
        const h = journalVision && !journalVision.hidden ? Math.ceil(journalVision.getBoundingClientRect().height) + 8 : 0;
        p.documentElement.style.setProperty('--haut-cap', `${64 + h}px`);
        if (p.defaultView) p.defaultView.dispatchEvent(new p.defaultView.Event('resize')); // la mosaïque se replace dessous
      } catch (e) { /* rien */ }
    }
    function montrerJournal(contenu, { replacer = true } = {}) {
      if (!journalVision) return;
      if (contenu === null) { journalVision.hidden = true; journalVision.replaceChildren(); if (replacer) ajusterHaut(); return; }
      const lignes = Array.isArray(contenu) ? contenu : [contenu];
      journalVision.replaceChildren(...lignes.map(t => { const p = doc.createElement('p'); p.textContent = t; return p; }));
      journalVision.hidden = false;
      ajusterHaut();
      // 11/11/2026 (décision de Max, c129) : la dernière ligne (la plus récente) en bas, et le petit journal se place sur
      // elle après chaque lecture : elle est toujours visible, même avec des notes longues. Avant : placé en haut.
      journalVision.scrollTop = journalVision.scrollHeight;
    }
    async function rafraichirJournal(numero = demande) {
      if (typeof journalChantier !== 'function') { montrerJournal(null); return []; }
      let lignes;
      try { lignes = await journalChantier(); } catch (erreur) { if (numero === demande && fenetre.open) montrerJournal(`Journal : ${raison(erreur)}`); return []; }
      if (numero !== demande || !fenetre.open) return [];
      montrerJournal(lignes && lignes.length ? lignes : 'Le journal est vide.');
      return lignes || [];
    }
    // ----- 11/11/2026 (accord de Max, c125) : la fiche du chantier parle DANS la visionneuse ouverte par-dessus : la question
    // d'une note dictée (avec « Oui, ajouter » / « Non », qui touchent les boutons de la fiche : même chemin, rien de plus) et
    // ses messages (en bas, 6 s). La visionneuse n'écrit rien elle-même.
    const questionNote = el('question-note-visionneuse');
    const texteNote = el('texte-note-visionneuse');
    const ouiNote = el('oui-note-visionneuse');
    const nonNote = el('non-note-visionneuse');
    const messageChantier = el('message-chantier-visionneuse');
    let actionsNote = null;
    let minuteurMessage = null;
    function fermerQuestionNote() { if (questionNote) questionNote.hidden = true; actionsNote = null; }
    function direChantier(etape, texte, actions = {}) {
      if (!fenetre.open || !questionNote || !messageChantier) return false;
      if (etape === 'question') {
        texteNote.textContent = texte;
        ouiNote.textContent = actions.libelleOui || 'Oui, ajouter';
        actionsNote = actions;
        questionNote.hidden = false;
        messageChantier.hidden = true;
        try { questionNote.scrollTop = 0; nonNote.focus({ preventScroll: true }); } catch (e) { /* rien */ }
        return true;
      }
      fermerQuestionNote();
      clearTimeout(minuteurMessage);
      messageChantier.textContent = texte || '';
      messageChantier.hidden = !texte;
      if (texte) minuteurMessage = setTimeout(() => { messageChantier.hidden = true; }, 6000);
      return true;
    }
    if (questionNote && ouiNote && nonNote) {
      ouiNote.addEventListener('click', () => { const a = actionsNote; fermerQuestionNote(); if (a && a.oui) a.oui(); });
      nonNote.addEventListener('click', () => { const a = actionsNote; fermerQuestionNote(); if (a && a.non) a.non(); });
      let dernierAppuiNote = null; // double toucher hors des boutons = « Non »
      questionNote.addEventListener('pointerup', e => {
        if (e.target && e.target.closest && e.target.closest('button')) { dernierAppuiNote = null; return; }
        const t = Date.now();
        if (dernierAppuiNote && t - dernierAppuiNote.t < 350 && Math.hypot(e.clientX - dernierAppuiNote.x, e.clientY - dernierAppuiNote.y) < 40) { dernierAppuiNote = null; nonNote.click(); return; }
        dernierAppuiNote = { t, x: e.clientX, y: e.clientY };
      });
    }
    async function ouvrirChantier(liste, titre) {
      if (vignettesPossibles && fenetreVignettes.open) { libererVignettes(); fenetreVignettes.close(); }
      const numero = ++demande;
      if (!fenetre.open) fenetre.showModal();
      nettoye = false;
      proposerAutorisation(false);
      etat.textContent = '';
      etat.hidden = true;
      etat.classList.remove('en-lecture');
      montrerTitreChantier(titre);
      let v;
      try { v = await visionneuse(); } catch (erreur) { if (numero === demande) message(`La visionneuse n’a pas pu s’ouvrir : ${raison(erreur)}`); return; }
      if (numero !== demande || !fenetre.open) return;
      pret = v;
      brancherFermerHaut();
      montrerTitreChantier(titre); // la page vient d'être chargée : « Choisir un fichier » laisse la place au nom
      void rafraichirJournal(numero); // c124 : le petit journal sous la barre
      if (typeof v.montrerMosaique !== 'function') { message('Cette visionneuse ne sait pas encore montrer un chantier.'); return; }
      const montres = liste.slice(0, MAX_CHANTIER);
      if (liste.length > MAX_CHANTIER) message(`Les ${MAX_CHANTIER} premiers documents sont montrés (mémoire du téléphone) : le chantier en a ${liste.length}.`);
      miniaturesFaites = new Set(); // c117
      v.montrerMosaique(montres.length, index => { void agrandirChantier(v, montres[index], index, numero); });
      for (let i = 0; i < montres.length; i++) {
        if (numero !== demande || !fenetre.open) return;
        try {
          // c117 : un temps maximal par miniature : une lecture ou un décodage qui ne finit pas n'arrête plus toute la file.
          const petit = await avecDelai((async () => {
            const contenu = await (await compte.appeler(`${drive}/${encodeURIComponent(montres[i].id)}?alt=media`)).blob();
            return vignette(montres[i].sorte === 'image' ? 'image' : 'pdf', contenu);
          })(), delaiMiniatureMs);
          if (numero !== demande) return;
          poserMiniature(v, i, petit);
        } catch (erreur) {
          if (numero !== demande) return;
          if (!enLigne()) { message(PAS_DE_RESEAU_DOC); proposerAutorisation(false); return; } // c141
          if (estExpiration(erreur)) { message('La connexion du compte Cap a expiré : touche « Autoriser la lecture du compte Cap », tu reviendras ici.', true); proposerAutorisation(true); return; }
          direMiniatureImpossible(v, i, erreur);
        }
      }
    }
    // ----- 11/11/2026 (accord de Max, c117) : plus jamais de case vide sans explication.
    let miniaturesFaites = new Set();
    const avecDelai = (promesse, ms) => new Promise((ok, refus) => {
      const id = minuteur(() => refus(new Error('trop longue à préparer')), ms);
      promesse.then(r => { annulerMinuteur(id); ok(r); }, e => { annulerMinuteur(id); refus(e); });
    });
    function poserMiniature(v, i, petit) {
      const adresse = urls.createObjectURL(petit);
      adresses.push(adresse); // relâchée à la fermeture
      v.remplirMiniature(i, adresse);
      miniaturesFaites.add(i);
    }
    function direMiniatureImpossible(v, i, erreur) {
      const pourquoi = /trop longue/i.test(raison(erreur)) ? 'trop longue à préparer'
        : (/illisible|decod|décod|InvalidState|EncodingError|source image/i.test(raison(erreur)) ? 'image illisible pour une miniature' : raison(erreur));
      // Jamais le nom réel du fichier : son numéro dans le chantier.
      v.miniatureIllisible(i, `Miniature impossible pour le document ${i + 1} : ${pourquoi}. Touche pour l’ouvrir.`);
    }
    async function agrandirChantier(v, d, index, numero) {
      try {
        const contenu = await (await compte.appeler(`${drive}/${encodeURIComponent(d.id)}?alt=media`)).blob();
        if (numero !== demande || !fenetre.open) return;
        const adresse = urls.createObjectURL(contenu);
        // La mémoire du document entier est relâchée dès qu'il est remis à sa place (ou à la fermeture).
        v.agrandirDepuisMosaique(adresse, d.sorte === 'image' ? `Image ${index + 1}.jpg` : `PDF ${index + 1}.pdf`, () => {
          urls.revokeObjectURL(adresse);
          // c117 : la case n'avait pas sa miniature : nouvel essai avec le document déjà lu (aucune lecture de plus).
          if (!miniaturesFaites.has(index) && numero === demande && fenetre.open) {
            avecDelai(Promise.resolve(vignette(d.sorte === 'image' ? 'image' : 'pdf', contenu)), delaiMiniatureMs)
              .then(petit => { if (numero === demande && fenetre.open) poserMiniature(v, index, petit); })
              .catch(erreur => { if (numero === demande && fenetre.open) direMiniatureImpossible(v, index, erreur); });
          }
        }, index); // c120 : la page cache la case de CETTE miniature pendant l'agrandi
      } catch (erreur) {
        if (numero !== demande) return;
        if (!enLigne()) { message(PAS_DE_RESEAU_DOC); proposerAutorisation(false); return; } // c141
        if (estExpiration(erreur)) { message('La connexion du compte Cap a expiré : touche « Autoriser la lecture du compte Cap », tu reviendras ici.', true); proposerAutorisation(true); return; }
        message(`Document non ouvert : ${raison(erreur)}`);
      }
    }
    function ouvrir(liste, { titre = '' , lireJournal = null } = {}) {
      if (titre && (liste || []).length) { journalChantier = lireJournal; return ouvrirChantier(liste, titre); } // c114 ; c124 : + journal
      if (vignettesPossibles && (liste || []).length > 1) return ouvrirVignettes(liste);
      indexEnGrand = -1; // 08/11/2026 (étape 3c) : un document seul, hors d'une liste de vignettes
      return ouvrirEnGrand(liste);
    }

    // ----- 08/11/2026 (accord de Max, étape 3c) : la visionneuse COMMANDÉE À LA VOIX -----
    // Chaque fonction rend la phrase que Cap dit. Les pages passent par les boutons ‹ › de la page de Zencoder (non
    // modifiée), comme le doigt. Rien n'est envoyé à l'IA.
    const vignettesOuvertes = () => vignettesPossibles && fenetreVignettes.open;
    // Document suivant (+1) ou précédent (-1). Grille seule affichée (rien en grand) : les 40 vignettes suivantes ou
    // précédentes (règle proposée à Max) ; s'il n'y en a pas, Cap dit de toucher une vignette.
    function documentVoisin(sens) {
      if (!fenetre.open) {
        // 09/11/2026 (défaut 4 vu par Max) : visionneuse fermée : si un document d'une liste a été ouvert, Cap ouvre le
        // suivant (ou le précédent) de cette liste dans la visionneuse ; sinon il le DIT clairement.
        // Avant : if (!vignettesOuvertes()) return 'La visionneuse n’est pas ouverte.';
        if (!vignettesOuvertes()) {
          const mot = sens > 0 ? 'suivant' : 'précédent';
          if (indexEnGrand < 0 || !listeVignettes.length) return `Il n’y a pas de document ${mot} : aucun document n’a été ouvert.`;
          const j = indexEnGrand + sens;
          if (j < 0 || j >= listeVignettes.length) return `Il n’y a pas de document ${mot}.`;
          indexEnGrand = j;
          void ouvrirEnGrand([listeVignettes[j]]);
          return sens > 0 ? 'J’ouvre le document suivant.' : 'J’ouvre le document précédent.';
        }
        const debut = debutVignettes + sens * MAX_VIGNETTES;
        if (debut < 0 || debut >= listeVignettes.length) return 'Touche une vignette pour l’ouvrir.';
        debutVignettes = debut;
        void remplirVignettes();
        return sens > 0 ? 'Vignettes suivantes.' : 'Vignettes précédentes.';
      }
      if (indexEnGrand < 0 || !listeVignettes.length) return 'Il n’y a pas d’autre document.';
      const j = indexEnGrand + sens;
      if (j < 0) return 'C’est le premier document.';
      if (j >= listeVignettes.length) return 'C’est le dernier document.';
      // Le document en grand est remplacé par le suivant (mémoire de l'ancien libérée).
      try { if (pret) pret.fermer(); } catch (erreur) { /* rien */ }
      for (const a of adresses) urls.revokeObjectURL(a);
      adresses = [];
      indexEnGrand = j;
      void ouvrirEnGrand([listeVignettes[j]]);
      return sens > 0 ? 'Document suivant.' : 'Document précédent.';
    }
    // Pages du PDF ouvert : { delta } (+1 / -1), { numero }, { premiere: true } ou { derniere: true }.
    function page(demande) {
      if (!fenetre.open) return 'Aucun PDF n’est ouvert.';
      const d = pageZencoder();
      const carte = d ? [...d.querySelectorAll('.carte-document')].find(c => c.querySelector('.etiquette-page-pdf')) : null;
      if (!carte) return 'Aucun PDF n’est ouvert.';
      const m = /page (\d+) sur (\d+)/.exec(carte.querySelector('.etiquette-page-pdf').textContent || '');
      if (!m) return 'Le PDF se charge encore.';
      const actuelle = Number(m[1]);
      const total = Number(m[2]);
      let cible = actuelle;
      if (demande.premiere) cible = 1;
      else if (demande.derniere) cible = total;
      else if (Number.isFinite(demande.numero)) cible = demande.numero;
      else cible = actuelle + (demande.delta || 0);
      if (cible < 1 || cible > total) return Number.isFinite(demande.numero) ? `Ce PDF n’a que ${total} page${total > 1 ? 's' : ''}.` : (cible < 1 ? 'C’est déjà la première page.' : 'C’est déjà la dernière page.');
      if (cible === actuelle) return `C’est déjà la page ${cible}.`;
      const bouton = carte.querySelector(cible > actuelle ? '.bouton-page-suivante' : '.bouton-page-precedente');
      if (!bouton) return 'Je ne trouve pas les boutons de page.';
      for (let i = 0; i < Math.abs(cible - actuelle); i++) bouton.click();
      return `Page ${cible}.`;
    }
    // Fermer à la voix : le document en grand d'abord (retour aux vignettes s'il y en a), puis les vignettes.
    function fermerParVoix() {
      // c133 : la mosaïque des chantiers d'abord.
      if (fenetre.open && grilleOuverte()) { fermer.click(); return 'Je ferme la liste des chantiers.'; }
      if (fenetre.open && chantierDepuisGrille) { fermer.click(); return 'Je reviens aux chantiers.'; }
      if (fenetre.open) { fermer.click(); return vignettesOuvertes() ? 'Je ferme le document : voici les vignettes.' : 'Je ferme la visionneuse.'; }
      if (vignettesOuvertes()) { fermerVignettes.click(); return 'Je ferme les documents.'; }
      return 'La visionneuse n’est pas ouverte.';
    }

    // ----- 11/11/2026 (accord de Max, c133) : « Ouvrir un chantier » dans le menu du bouton blanc, sous « Ajouter un
    // fichier ». Un toucher : une MOSAÏQUE de carrés par-dessus la visionneuse, un par chantier (nom seulement), dans l'ordre
    // de l'écran Chantiers (voyant puis nom), 3 colonnes (2 sur un écran étroit) ; elle défile. Un toucher sur un carré : les
    // documents de CE chantier s'ouvrent DIRECTEMENT en mosaïque, comme « Ouvrir le chantier » de la fiche (même lecture,
    // même petit journal), sans fiche entre les deux. « Fermer » : chantier ouvert → retour à la mosaïque des chantiers ;
    // mosaïque des chantiers → la visionneuse d'origine. LECTURE SEULE : rien n'est écrit ni envoyé, jamais à l'IA.
    // Le bouton, la mosaïque et leur allure sont posés ici (aucun autre fichier touché).
    const SORTES_CHANTIER = Object.freeze({ pdf: 'pdf', images: 'image' });
    const STYLE_GRILLE = `
dialog#visionneuse-cap #grille-chantiers-visionneuse { position: absolute; top: 64px; left: 0; right: 0; bottom: 0; z-index: 6; display: flex;
  flex-direction: column; gap: 8px; padding: 8px 12px max(12px, env(safe-area-inset-bottom)); box-sizing: border-box;
  background: rgba(8, 26, 24, 0.96); }
dialog#visionneuse-cap #grille-chantiers-visionneuse[hidden] { display: none; }
dialog#visionneuse-cap #haut-grille-chantiers { display: flex; justify-content: flex-end; flex: none; }
dialog#visionneuse-cap #fermer-grille-chantiers { min-height: 44px; padding: 0 18px; border: 0; border-radius: 22px; background: rgba(255, 255, 255, 0.92);
  color: #16201d; font: 600 16px/1 sans-serif; touch-action: manipulation; }
dialog#visionneuse-cap #message-grille-chantiers { flex: none; margin: 0; padding: 8px 12px; border-radius: 10px; background: rgba(255, 255, 255, 0.88);
  color: #16201d; font: 15px/1.35 sans-serif; overflow-wrap: anywhere; }
dialog#visionneuse-cap #message-grille-chantiers[hidden] { display: none; }
dialog#visionneuse-cap #liste-grille-chantiers { flex: 1 1 auto; min-height: 0; overflow-y: auto; overflow-x: hidden; overscroll-behavior: contain;
  touch-action: pan-y; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); grid-auto-rows: min-content; gap: 10px; align-content: start; }
@media (max-width: 340px) { dialog#visionneuse-cap #liste-grille-chantiers { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
dialog#visionneuse-cap .case-chantier-grille { aspect-ratio: 1 / 1; min-width: 0; margin: 0; padding: 8px; box-sizing: border-box; border: 0;
  border-radius: 12px; background: rgba(255, 255, 255, 0.92); color: #16201d; font: 600 16px/1.25 sans-serif; text-align: center;
  display: flex; align-items: center; justify-content: center; overflow-wrap: anywhere; hyphens: auto; touch-action: manipulation; }
`;
    let grilleChantiers = null;
    let listeGrille = null;
    let messageGrille = null;
    let chantierDepuisGrille = false; // un chantier ouvert depuis la mosaïque : « Fermer » y revient
    let lectureGrille = 0;
    const grilleOuverte = () => Boolean(grilleChantiers && !grilleChantiers.hidden);
    function noeudGrille(balise, id, texte) {
      const n = doc.createElement(balise);
      if (id) n.id = id;
      if (texte !== undefined) n.textContent = texte;
      return n;
    }
    function fabriquerGrille() {
      if (grilleChantiers) return;
      if (!el('style-grille-chantiers')) {
        const s = noeudGrille('style', 'style-grille-chantiers', STYLE_GRILLE);
        (doc.head || doc.documentElement).append(s);
      }
      grilleChantiers = noeudGrille('div', 'grille-chantiers-visionneuse');
      grilleChantiers.hidden = true;
      grilleChantiers.setAttribute('role', 'region');
      grilleChantiers.setAttribute('aria-label', 'Chantiers');
      const haut = noeudGrille('div', 'haut-grille-chantiers');
      const fermerGrille = noeudGrille('button', 'fermer-grille-chantiers', 'Fermer');
      fermerGrille.type = 'button';
      fermerGrille.addEventListener('click', () => fermer.click()); // même chemin que tous les « Fermer »
      haut.append(fermerGrille);
      messageGrille = noeudGrille('p', 'message-grille-chantiers');
      messageGrille.setAttribute('role', 'status');
      messageGrille.hidden = true;
      listeGrille = noeudGrille('div', 'liste-grille-chantiers');
      grilleChantiers.append(haut, messageGrille, listeGrille);
      // Le menu du bouton blanc (z-index 7) reste devant la mosaïque (z-index 6).
      fenetre.append(grilleChantiers);
    }
    function direGrille(texte) {
      if (!messageGrille) return;
      messageGrille.textContent = texte || '';
      messageGrille.hidden = !texte;
    }
    function trierChantiers(copie) {
      const s = sourceChantiers();
      const liste = s && copie && Array.isArray(copie.chantiers) ? copie.chantiers : [];
      const evalue = s && typeof s.evaluer === 'function' ? s.evaluer(liste, maintenant()) : { chantiers: liste };
      return s && typeof s.trier === 'function' ? s.trier(evalue.chantiers) : evalue.chantiers;
    }
    function dessinerGrille(tries) {
      listeGrille.replaceChildren(...tries.map(c => {
        const b = noeudGrille('button', '', String(c.nom || 'sans nom'));
        b.type = 'button';
        b.className = 'case-chantier-grille';
        b.addEventListener('click', () => { void ouvrirChantierGrille(c); });
        return b;
      }));
      listeGrille.scrollTop = 0;
    }
    function montrerGrille() {
      fabriquerGrille();
      const numero = ++lectureGrille;
      const s = sourceChantiers();
      try { const c = el('confirmer-depart-visionneuse'); if (c) c.hidden = true; } catch (e) { /* rien */ }
      grilleChantiers.hidden = false;
      if (!s) { dessinerGrille([]); direGrille('La Liste des chantiers n’est pas disponible ici.'); return Promise.resolve(0); }
      let avant = null;
      try { avant = typeof s.copie === 'function' ? s.copie() : null; } catch (e) { avant = null; }
      dessinerGrille(trierChantiers(avant));
      direGrille(avant ? '' : 'Lecture de la Liste des chantiers… (rien n’est modifié)');
      if (typeof s.lire !== 'function') return Promise.resolve(listeGrille.children.length);
      // Relue comme à l'ouverture de l'écran Chantiers (même lecture, lecture seule) ; la copie reste affichée en attendant.
      return Promise.resolve().then(() => s.lire()).then(copie => {
        if (numero !== lectureGrille || !grilleOuverte()) return 0;
        const tries = trierChantiers(copie);
        dessinerGrille(tries);
        direGrille(tries.length ? '' : 'Aucun chantier dans la Liste.');
        return tries.length;
      }, erreur => {
        if (numero !== lectureGrille || !grilleOuverte()) return 0;
        direGrille(avant ? `${raison(erreur)} Voici la dernière copie.` : raison(erreur));
        return listeGrille.children.length;
      });
    }
    function cacherGrille() { if (grilleChantiers) grilleChantiers.hidden = true; lectureGrille++; direGrille(''); }
    function oublierGrilleChantiers() { cacherGrille(); chantierDepuisGrille = false; }
    async function ouvrirChantierGrille(c) {
      const d = dossiersChantiers();
      const numero = ++lectureGrille;
      if (!d || typeof d.listerDocuments !== 'function') { direGrille('Les dossiers des chantiers ne sont pas disponibles ici : rien n’a été ouvert.'); return ''; }
      direGrille(`Lecture des documents de « ${String(c.nom || '')} »… (rien n’est modifié)`);
      let r;
      try { r = await d.listerDocuments(compte, c, 100000); } catch (erreur) {
        if (numero !== lectureGrille || !grilleOuverte()) return '';
        if (!enLigne()) { direGrille(PAS_DE_RESEAU_DOC); return ''; } // c141
        if (estExpiration(erreur)) { direGrille('La connexion du compte Cap a expiré : ferme cette liste et touche « Autoriser la lecture du compte Cap ».'); proposerAutorisation(true); return ''; }
        direGrille(`« ${String(c.nom || '')} » : ${raison(erreur)} Rien n’a été ouvert.`);
        return '';
      }
      if (numero !== lectureGrille || !grilleOuverte() || !fenetre.open) return '';
      const liste = ((r && r.fichiers) || []).filter(f => SORTES_CHANTIER[f.sorte] && f.id).map(f => ({ id: f.id, sorte: SORTES_CHANTIER[f.sorte] }));
      if (!liste.length) { direGrille(`Aucun PDF ni image dans « ${String(c.nom || '')} » : rien n’a été ouvert.`); return ''; }
      cacherGrille();
      chantierDepuisGrille = true;
      void ouvrir(liste, { titre: c.nom, lireJournal: () => d.lireDernieresLignes(compte, c, 5) });
      return String(liste.length);
    }
    // « Fermer » : vrai si le retour a été fait ici (la visionneuse reste ouverte).
    function retourVersChantiers() {
      if (!fenetre.open) return false;
      if (grilleOuverte()) {
        cacherGrille();
        // Revenu d'un chantier : la page avait été vidée ; la visionneuse d'origine se rouvre, vide (comme l'œil).
        if (nettoye) { chantierDepuisGrille = false; void ouvrirVide(); }
        return true;
      }
      if (chantierDepuisGrille) {
        chantierDepuisGrille = false;
        nettoyer(); // documents, miniatures, journal et nom du chantier relâchés, comme à la fermeture
        void montrerGrille();
        return true;
      }
      return false;
    }
    {
      const menuVision = el('menu-visionneuse');
      if (menuVision && !el('menu-chantiers-visionneuse')) {
        const b = noeudGrille('button', 'menu-chantiers-visionneuse', 'Ouvrir un chantier');
        b.type = 'button';
        const ajouter = el('menu-ajouter-visionneuse');
        if (ajouter && ajouter.parentNode === menuVision) ajouter.after(b); else menuVision.append(b);
        b.addEventListener('click', () => { if (fenetre.open) void montrerGrille(); });
      }
    }

    // 08/11/2026 (étape 3c) : + documentVoisin, page, fermerParVoix, vignettesOuvertes.
    // 09/11/2026 : + ouvrirVide.
    // 11/11/2026 (c133) : + montrerChantiers, chantiersOuverts.
    // 12/11/2026 (accord de Max, c162) : le DOSSIER d'une relation (« r_… », compte Cap, LECTURE SEULE) dans la visionneuse :
    // ses photos et ses PDF, et ceux de ses sous-dossiers directs (20 au plus), en mosaïque comme un chantier (60 au plus).
    // Les vidéos restent pour le Lecteur. Rien n'est écrit ni gardé ; aucun droit nouveau (drive.readonly du compte Cap).
    const DRIVE_FICHIERS = 'https://www.googleapis.com/drive/v3/files';
    const DOSSIER_DRIVE = 'application/vnd.google-apps.folder';
    const SORTES_DOSSIER = Object.freeze({ pdf: 'pdf', images: 'image' });
    async function listerDossier(idDossier) {
      const tous = [];
      let pageSuivante = '';
      let tours = 0;
      do {
        const params = { q: `'${String(idDossier).replace(/\\/g, '\\\\').replace(/'/g, "\\'")}' in parents and trashed=false`, fields: 'nextPageToken,files(id,name,mimeType)', pageSize: '1000', spaces: 'drive' };
        if (pageSuivante) params.pageToken = pageSuivante;
        const corps = await (await compte.appeler(`${DRIVE_FICHIERS}?${new URLSearchParams(params)}`)).json();
        tous.push(...(Array.isArray(corps.files) ? corps.files : []));
        pageSuivante = corps.nextPageToken || '';
      } while (pageSuivante && ++tours < 20);
      return tous;
    }
    async function ouvrirDossier(idDossier, titre) {
      const dire = async texte => { await ouvrirVide(); message(texte); return false; };
      if (!idDossier) return dire('Ce dossier est inconnu : touche « Tout synchroniser », puis réessaie.');
      if (!enLigne()) return dire(PAS_DE_RESEAU_DOC);
      let fichiers;
      try {
        const directs = await listerDossier(idDossier);
        fichiers = directs.slice();
        for (const sous of directs.filter(f => f && f.mimeType === DOSSIER_DRIVE).slice(0, 20)) fichiers.push(...await listerDossier(sous.id));
      } catch (erreur) {
        if (!enLigne()) return dire(PAS_DE_RESEAU_DOC);
        if (estExpiration(erreur)) { await dire('La connexion du compte Cap a expiré : touche « Autoriser la lecture du compte Cap », puis rouvre la carte.'); proposerAutorisation(true); return false; }
        return dire(`Dossier non lu : ${raison(erreur)}`);
      }
      const sorte = f => (typeof typesFichiers !== 'undefined' ? typesFichiers.analyser(f).sorte : '');
      const liste = fichiers.filter(f => f && f.id && SORTES_DOSSIER[sorte(f)])
        .sort((a, b) => String(a.name || '').localeCompare(String(b.name || ''), 'fr', { numeric: true, sensitivity: 'base' }))
        .map(f => ({ id: String(f.id), sorte: SORTES_DOSSIER[sorte(f)] }));
      if (!liste.length) return dire('Aucune photo ni PDF dans ce dossier : rien n’a été ouvert.');
      await ouvrir(liste, { titre: String(titre || 'Relation') });
      return true;
    }
    // c133 : une ouverture venue d'ailleurs (fiche, voix, œil) fait oublier la mosaïque des chantiers : son « Fermer » ferme.
    const horsGrille = f => (...a) => { oublierGrilleChantiers(); return f(...a); };
    return { ouvrir: horsGrille(ouvrir), ouvrirDossier: horsGrille(ouvrirDossier), montrerChantiers: montrerGrille, chantiersOuverts: grilleOuverte, rafraichirJournal, direChantier,
      ouvrirEnGrand: horsGrille(ouvrirEnGrand), ouvrirVide: horsGrille(ouvrirVide), annoncer, ouverte: () => fenetre.open, MAX_DOCUMENTS, MAX_VIGNETTES, ouverts: () => adresses.length,
      vignettes: () => (vignettesPossibles && fenetreVignettes.open ? grille.children.length : 0), documentVoisin, page, fermerParVoix, vignettesOuvertes };
  }

  // 08/11/2026 : vrai (et marque effacée) si le retour de Google vient d'un « Autoriser » touché dans la visionneuse
  // (ou, avec cle = CLE_RETOUR_MUSIQUE, dans la fenêtre « Musique »).
  function retourDemande(stockage, maintenant = Date.now(), cle = CLE_RETOUR) {
    let valeur = null;
    try { valeur = stockage.getItem(cle); stockage.removeItem(cle); } catch (erreur) { return false; }
    const quand = Number(valeur);
    return Number.isFinite(quand) && quand > 0 && maintenant - quand >= 0 && maintenant - quand < DUREE_RETOUR_MS;
  }

  // 08/11/2026 (vignettes) : + MAX_VIGNETTES, fabriquerVignette.
  // 11/11/2026 (accord de Max, c118, marche 1) : le bouton rond blanc de la visionneuse ouvre (ou ferme) son menu en ligne ;
  // sans toucher pendant 4 s, ou après un choix, le menu se referme. Branché une seule fois par page (appelé par brancher
  // et par l'accueil, qui range dans ce menu le micro, le livre et la synchronisation).
  function brancherMenu(doc, { dureeMenuMs = 4000 } = {}) {
    const boutonMenu = doc.getElementById('bouton-menu-visionneuse');
    const menu = doc.getElementById('menu-visionneuse');
    const fenetre = doc.getElementById('visionneuse-cap');
    if (!boutonMenu || !menu || !fenetre || boutonMenu.dataset.menuBranche === 'oui') return;
    boutonMenu.dataset.menuBranche = 'oui';
    let minuteur = null;
    function ouvrirMenu(ouvrir) {
      menu.hidden = !ouvrir;
      boutonMenu.setAttribute('aria-expanded', String(ouvrir));
      clearTimeout(minuteur);
      if (ouvrir) minuteur = setTimeout(() => ouvrirMenu(false), dureeMenuMs); // sans toucher : il se referme seul
    }
    boutonMenu.addEventListener('click', () => ouvrirMenu(menu.hidden));
    menu.addEventListener('pointerdown', () => { if (!menu.hidden) ouvrirMenu(true); }, true); // un toucher relance les 4 s
    // Un bouton choisi : la commande se fait, puis le menu se referme.
    menu.addEventListener('click', e => { if (e.target && e.target.closest && e.target.closest('button')) setTimeout(() => ouvrirMenu(false), 0); });
    fenetre.addEventListener('close', () => ouvrirMenu(false));
  }

  return { MAX_DOCUMENTS, MAX_VIGNETTES, CLE_RETOUR, CLE_RETOUR_MUSIQUE, DUREE_RETOUR_MS, chargeur, retoucherVisionneuse, brancher, retourDemande, fabriquerVignette, brancherMenu };
})();

if (typeof document !== 'undefined' && !(typeof window !== 'undefined' && window.CAP_TESTS)) {
  const cadre = document.getElementById('cadre-visionneuse');
  // 08/11/2026 (vignettes) : + pdfjs, le même pdf.js que Cap (chargé seulement au premier PDF).
  visionneuseCap.instance = cadre ? visionneuseCap.brancher(document, {
    compte: googleCompteRelations, visionneuse: visionneuseCap.chargeur(cadre),
    pdfjs: () => relationsCompte.chargerPdfjs(document, window)
  }) : null;
}
