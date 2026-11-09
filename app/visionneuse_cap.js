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
      const image = await vue.createImageBitmap(contenu);
      const echelle = Math.min(1, LARGEUR_VIGNETTE / image.width);
      toile.width = Math.max(1, Math.round(image.width * echelle));
      toile.height = Math.max(1, Math.round(image.height * echelle));
      toile.getContext('2d').drawImage(image, 0, 0, toile.width, toile.height);
      if (image.close) image.close();
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
      demande++;
      etat.classList.remove('en-lecture');
      proposerAutorisation(false);
      try { if (pret) pret.fermer(); } catch (erreur) { /* la page est peut-être déjà partie */ }
      pret = null;
      for (const a of adresses) urls.revokeObjectURL(a);
      adresses = [];
      if (typeof visionneuse.vider === 'function') visionneuse.vider();
    }
    fenetre.addEventListener('cancel', nettoyer);
    fenetre.addEventListener('close', () => { if (!fenetre.open) nettoyer(); });
    fermer.addEventListener('click', () => { nettoyer(); if (fenetre.open) fenetre.close(); });

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
          if (estExpiration(erreur)) {
            messageVignettes('La connexion du compte Cap a expiré : touche « Autoriser la lecture du compte Cap », tu reviendras ici.', Boolean(autoriserVignettes));
            return;
          }
          boutons[i].classList.remove('en-chargement');
          boutons[i].classList.add('vignette-illisible'); // la vignette reste touchable : le document s'ouvre quand même en grand
        }
      }
    }
    function ouvrirVignettes(liste) {
      if (fenetre.open) { nettoyer(); fenetre.close(); } // l'éventuel « Lecture en cours… » de l'œil
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
    function ouvrir(liste) {
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
      if (fenetre.open) { fermer.click(); return vignettesOuvertes() ? 'Je ferme le document : voici les vignettes.' : 'Je ferme la visionneuse.'; }
      if (vignettesOuvertes()) { fermerVignettes.click(); return 'Je ferme les documents.'; }
      return 'La visionneuse n’est pas ouverte.';
    }

    // 08/11/2026 (étape 3c) : + documentVoisin, page, fermerParVoix, vignettesOuvertes.
    // 09/11/2026 : + ouvrirVide.
    return { ouvrir, ouvrirEnGrand, ouvrirVide, annoncer, ouverte: () => fenetre.open, MAX_DOCUMENTS, MAX_VIGNETTES, ouverts: () => adresses.length,
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
  return { MAX_DOCUMENTS, MAX_VIGNETTES, CLE_RETOUR, CLE_RETOUR_MUSIQUE, DUREE_RETOUR_MS, chargeur, retoucherVisionneuse, brancher, retourDemande, fabriquerVignette };
})();

if (typeof document !== 'undefined' && !(typeof window !== 'undefined' && window.CAP_TESTS)) {
  const cadre = document.getElementById('cadre-visionneuse');
  // 08/11/2026 (vignettes) : + pdfjs, le même pdf.js que Cap (chargé seulement au premier PDF).
  visionneuseCap.instance = cadre ? visionneuseCap.brancher(document, {
    compte: googleCompteRelations, visionneuse: visionneuseCap.chargeur(cadre),
    pdfjs: () => relationsCompte.chargerPdfjs(document, window)
  }) : null;
}
