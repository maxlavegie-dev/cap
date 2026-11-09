'use strict';

// Essai du compte Cap (07/11/2026, accord de Max) : avec le compte Google NEUF dédié à Cap
// (google_compte_relations.js), compter en LECTURE SEULE ce que Max a déposé dans « Relations »
// (dossiers « r_ », MP3, images, PDF, sous-dossiers album ou playlist), puis afficher un PDF DANS Cap
// avec pdf.js (copié en local dans pdfjs/, comme la visionneuse de Zencoder : chaque page dessinée
// sur un canvas). Aucun nom de fichier n'est affiché ni gardé (seulement les noms des dossiers « r_ »).
// Rien n'est créé, modifié ni supprimé : le compte Cap ne permet que des lectures.
// Lot 2 (07/11/2026) : comptage rapide. Cap lit d'un coup la liste de TOUS les fichiers du compte Cap
// (avec leur dossier parent), en quelques demandes, puis reconstruit l'arbre sur le téléphone, au
// lieu d'une demande par dossier. Compte aussi « Documents » (à la racine) : seuls les noms des
// dossiers du premier niveau sont affichés, à l'écran seulement (rien n'est gardé ni envoyé).
const relationsCompte = (() => {
  const drive = 'https://www.googleapis.com/drive/v3/files';
  const DOSSIER = 'application/vnd.google-apps.folder';
  // Garde-fou : profondeur maximale, et chaque dossier n'est compté qu'une fois (pas de boucle).
  const PROFONDEUR_MAX = 20;

  async function lister(compte, q) {
    const tous = [];
    let page = '';
    do {
      const url = new URL(drive);
      url.search = new URLSearchParams({ q, fields: 'nextPageToken,files(id,name,mimeType,parents,size)', pageSize: '1000',
        spaces: 'drive', ...(page ? { pageToken: page } : {}) }).toString();
      const corps = await (await compte.appeler(url.href)).json();
      tous.push(...(corps.files || []));
      page = corps.nextPageToken || '';
    } while (page);
    return tous;
  }

  // Tout le Drive du compte Cap en une fois (quelques pages de 1000), rangé par dossier parent.
  async function lireArbre(compte) {
    const racine = await (await compte.appeler(`${drive}/root?fields=id`)).json();
    const enfantsDe = new Map();
    for (const fichier of await lister(compte, 'trashed=false')) {
      for (const parent of fichier.parents || []) {
        if (!enfantsDe.has(parent)) enfantsDe.set(parent, []);
        enfantsDe.get(parent).push(fichier);
      }
    }
    return { racine: racine && racine.id, enfants: id => enfantsDe.get(id) || [] };
  }
  const dossiersRacine = (arbre, nom) => arbre.enfants(arbre.racine).filter(x => x.name === nom && x.mimeType === DOSSIER);
  const parNom = liste => [...liste].sort((a, b) => String(a.name).localeCompare(String(b.name), 'fr'));

  function sorte(fichier) {
    const nom = String(fichier.name || '').toLowerCase();
    const type = String(fichier.mimeType || '');
    if (type === DOSSIER) return /album|playlist/.test(nom) ? 'albums' : 'sousDossiers';
    if (type === 'audio/mpeg' || type === 'audio/mp3' || nom.endsWith('.mp3')) return 'mp3';
    if (type === 'application/pdf' || nom.endsWith('.pdf')) return 'pdf';
    if (type.startsWith('image/') || /\.(jpe?g|png|gif|webp|heic)$/.test(nom)) return 'images';
    return 'autres';
  }

  function compterDans(arbre, id, niveau, total, pdfs, vus) {
    if (vus.has(id)) return;
    vus.add(id);
    for (const fichier of arbre.enfants(id)) {
      if (fichier.mimeType === DOSSIER && vus.has(fichier.id)) continue;
      const s = sorte(fichier);
      total[s]++;
      if (s === 'pdf') pdfs.push(fichier.id);
      if (fichier.mimeType === DOSSIER && niveau < PROFONDEUR_MAX) compterDans(arbre, fichier.id, niveau + 1, total, pdfs, vus);
    }
  }

  // « Relations » à la racine du Drive du compte Cap, puis chaque dossier « r_ ».
  function compterRelations(arbre) {
    const racines = dossiersRacine(arbre, 'Relations');
    const resultat = { racines: racines.length, lignes: [], autres: 0, pdfs: [] };
    if (racines.length !== 1) return resultat;
    const vus = new Set([racines[0].id]);
    for (const fichier of parNom(arbre.enfants(racines[0].id))) {
      if (fichier.mimeType === DOSSIER && fichier.name.startsWith('r_')) {
        const ligne = { nomDossier: fichier.name, mp3: 0, images: 0, pdf: 0, albums: 0, sousDossiers: 0, autres: 0 };
        compterDans(arbre, fichier.id, 1, ligne, resultat.pdfs, vus);
        resultat.lignes.push(ligne);
      } else resultat.autres++;
    }
    return resultat;
  }

  // « Documents » à la racine : une ligne par dossier du premier niveau (tous ses sous-dossiers compris).
  function compterDocuments(arbre) {
    const racines = dossiersRacine(arbre, 'Documents');
    const resultat = { racines: racines.length, lignes: [], directs: 0, pdfs: [] };
    if (racines.length !== 1) return resultat;
    const vus = new Set([racines[0].id]);
    for (const fichier of parNom(arbre.enfants(racines[0].id))) {
      if (fichier.mimeType === DOSSIER) {
        const t = { mp3: 0, images: 0, pdf: 0, albums: 0, sousDossiers: 0, autres: 0 };
        compterDans(arbre, fichier.id, 1, t, resultat.pdfs, vus);
        resultat.lignes.push({ nomDossier: fichier.name, dossiers: t.albums + t.sousDossiers, pdf: t.pdf, images: t.images, autres: t.mp3 + t.autres });
      } else {
        resultat.directs++;
        if (sorte(fichier) === 'pdf') resultat.pdfs.push(fichier.id);
      }
    }
    return resultat;
  }

  async function compter(compte) {
    const arbre = await lireArbre(compte);
    return { ...compterRelations(arbre), documents: compterDocuments(arbre) };
  }

  function resumer(r) {
    if (r.racines === 0) return 'Aucun dossier « Relations » à la racine du Drive du compte Cap. Rien n’a été modifié.';
    if (r.racines > 1) return `${r.racines} dossiers « Relations » à la racine du Drive du compte Cap : garde-en un seul. Rien n’a été modifié.`;
    const somme = cle => r.lignes.reduce((n, ligne) => n + ligne[cle], 0);
    return [`Compte Cap (lecture seule, rien n’est modifié) : ${r.lignes.length} dossier(s) « r_ ».`,
      ...r.lignes.map(l => `${l.nomDossier} : ${l.mp3} MP3 · ${l.images} image(s) · ${l.pdf} PDF · ${l.albums} album(s)`
        + (l.sousDossiers ? ` · ${l.sousDossiers} autre(s) sous-dossier(s)` : '') + (l.autres ? ` · ${l.autres} autre(s) fichier(s)` : '')),
      ...(r.autres ? [`${r.autres} autre(s) élément(s) dans « Relations » (pas des dossiers « r_ »).`] : []),
      `Total : ${somme('mp3')} MP3, ${somme('images')} image(s), ${somme('pdf')} PDF, ${somme('albums')} album(s).`].join('\n');
  }

  function resumerDocuments(d) {
    if (!d || d.racines === 0) return 'Aucun dossier « Documents » à la racine du Drive du compte Cap.';
    if (d.racines > 1) return `${d.racines} dossiers « Documents » à la racine du Drive du compte Cap : garde-en un seul.`;
    const somme = cle => d.lignes.reduce((n, ligne) => n + ligne[cle], 0);
    return [`« Documents » : ${d.lignes.length} dossier(s) au premier niveau.`,
      ...d.lignes.map(l => `${l.nomDossier} : ${l.dossiers} sous-dossier(s) · ${l.pdf} PDF · ${l.images} image(s) · ${l.autres} autre(s) fichier(s)`),
      ...(d.directs ? [`${d.directs} fichier(s) directement dans « Documents ».`] : []),
      `Total « Documents » : ${d.lignes.length + somme('dossiers')} dossier(s), ${d.pdfs.length} PDF, ${somme('images')} image(s), ${somme('autres')} autre(s) fichier(s).`].join('\n');
  }

  // pdf.js chargé seulement au premier PDF (1,4 Mo), depuis Cap lui-même, jamais d'Internet.
  let chargement = null;
  function chargerPdfjs(doc, fenetre) {
    if (fenetre.pdfjsLib) return Promise.resolve(fenetre.pdfjsLib);
    if (!chargement) {
      chargement = new Promise((ok, refus) => {
        const script = doc.createElement('script');
        script.src = 'pdfjs/pdf.min.js';
        script.onload = () => {
          if (!fenetre.pdfjsLib) { chargement = null; refus(new Error('Le lecteur de PDF n’a pas pu démarrer.')); return; }
          fenetre.pdfjsLib.GlobalWorkerOptions.workerSrc = 'pdfjs/pdf.worker.min.js';
          ok(fenetre.pdfjsLib);
        };
        script.onerror = () => { chargement = null; refus(new Error('Le lecteur de PDF n’a pas pu être chargé.')); };
        doc.head.appendChild(script);
      });
    }
    return chargement;
  }

  async function ouvrirPdf(compte, id, lib) {
    const reponse = await compte.appeler(`${drive}/${encodeURIComponent(id)}?alt=media`);
    return lib.getDocument({ data: new Uint8Array(await reponse.arrayBuffer()) }).promise;
  }

  // Une page dessinée sur le canvas, à la largeur de l'écran (finesse limitée pour la mémoire).
  async function dessinerPage(pdf, numero, canvas, largeurEcran, densite) {
    const page = await pdf.getPage(numero);
    const base = page.getViewport({ scale: 1 });
    const echelle = Math.min(3, Math.max(0.5, (largeurEcran * Math.min(2, densite || 1)) / base.width));
    const vue = page.getViewport({ scale: echelle });
    canvas.width = Math.floor(vue.width);
    canvas.height = Math.floor(vue.height);
    await page.render({ canvasContext: canvas.getContext('2d'), viewport: vue }).promise;
  }

  // 09/11/2026 (décision de Max, bloc c76) : + propositionsOeil (false par défaut) : l'œil ouvre la visionneuse VIDE, sans lire
  // ni proposer les PDF du compte Cap ; Max touche lui-même « Choisir un fichier ». La lecture d'avant est gardée (true).
  function brancher(doc, { compte, pdfjs, visionneuse = null, stockage = (typeof localStorage !== 'undefined' ? localStorage : null), maintenant = () => Date.now(), propositionsOeil = false }) {
    const el = id => doc.getElementById(id);
    const champ = el('adresse-compte-relations');
    const connecter = el('connecter-compte-relations');
    const bouton = el('compter-compte-relations');
    const zone = el('resume-compte-relations');
    const zoneDocuments = el('resume-documents-compte');
    const boutonPdf = el('pdf-compte-relations');
    const lecteur = el('lecteur-pdf-relations');
    const canvas = el('canvas-pdf-relations');
    const etiquette = el('page-pdf-relations');
    const precedente = el('pdf-precedente-relations');
    const suivante = el('pdf-suivante-relations');
    const pdfAvant = el('pdf-avant-relations');
    const pdfApres = el('pdf-apres-relations');
    const fermer = el('pdf-fermer-relations');
    if (![champ, connecter, bouton, zone, zoneDocuments, boutonPdf, lecteur, canvas, etiquette, precedente, suivante, pdfAvant, pdfApres, fermer].every(Boolean)) return;
    // Chaque zone garde son message jusqu'à la prochaine action (rien ne s'efface tout seul).
    const montrer = (z, texte, titre = '') => {
      z.hidden = false;
      z.dataset.titre = titre;
      z.textContent = texte;
    };
    const ecrire = (texte, titre) => {
      montrer(zone, texte, titre);
      try { zone.scrollIntoView({ block: 'start' }); } catch (erreur) {}
    };
    const raison = erreur => String(erreur && erreur.message || 'raison inconnue').slice(0, 220);
    champ.value = compte.adresse();
    if (compte.message()) ecrire(compte.message());
    let pdfs = [];
    let pdf = null;
    let indexPdf = 0;
    let numero = 1;

    // ----- 08/11/2026 (accord de Max) : l'œil de « Autre » ouvre DIRECTEMENT la visionneuse (PDF du compte Cap) -----
    const laVisionneuse = () => (typeof visionneuse === 'function' ? visionneuse() : visionneuse);
    let lectureOeil = 0;
    async function ouvrirOeil(texteRetour = '') {
      const v = laVisionneuse();
      if (!v || typeof v.annoncer !== 'function') return;
      // 09/11/2026 (bloc c76) : plus aucune proposition : la visionneuse s'ouvre vide (aucune lecture du Drive, aucun message).
      // Les PDF du compte Cap ne sont ni touchés ni effacés : ils ne sont simplement plus proposés à l'ouverture.
      if (!propositionsOeil && typeof v.ouvrirVide === 'function') { ++lectureOeil; await v.ouvrirVide(); return; }
      const numeroOeil = ++lectureOeil;
      if (!compte.adresse()) {
        v.annoncer('Identifiant du compte Cap absent : écris-le d’abord dans « Réglages du Drive » (Autre, puis Réglages).');
        return;
      }
      if (!compte.connecte()) {
        v.annoncer(texteRetour || 'Le compte Cap n’est pas connecté (ou la connexion a expiré, au bout d’environ 1 h). '
          + 'Touche « Autoriser la lecture du compte Cap » : tu reviendras ici.', { autorisation: true });
        return;
      }
      v.annoncer('Lecture en cours… (recherche des PDF du compte Cap ; rien n’est modifié)', { enLecture: true });
      try {
        const r = await compter(compte);
        if (numeroOeil !== lectureOeil || !v.ouverte()) return; // fermée pendant la lecture : rien ne se rouvre
        const liste = [...r.pdfs, ...r.documents.pdfs];
        // 09/11/2026 (décision de Max après c72) : aucun document : la visionneuse vide, SANS message. Avant :
        // if (!liste.length) { v.annoncer('Aucun PDF dans le compte Cap pour l’instant. Rien n’a été modifié.'); return; }
        if (!liste.length) { if (typeof v.ouvrirVide === 'function') await v.ouvrirVide(); else v.annoncer('Aucun PDF dans le compte Cap pour l’instant. Rien n’a été modifié.'); return; }
        await v.ouvrir(liste.map(id => ({ id })));
      } catch (erreur) {
        if (numeroOeil !== lectureOeil || !v.ouverte()) return;
        const expire = /expir|pas connecté/i.test(String(erreur && erreur.message || ''));
        v.annoncer(expire
          ? 'La connexion du compte Cap a expiré : touche « Autoriser la lecture du compte Cap », tu reviendras ici.'
          : `PDF non ouverts : ${raison(erreur)}`, { autorisation: expire });
      }
    }
    const oeil = el('ouvrir-oeil');
    if (oeil) oeil.addEventListener('click', () => { void ouvrirOeil(); });

    // Retour de Google pour le compte Cap : « Réglages du Drive » est rouvert, avec le résultat.
    // 08/11/2026 : si « Autoriser » avait été touché DANS la visionneuse, c'est elle qui se rouvre (PDF lus).
    const retourVisionneuse = compte.retourRecent() && stockage && typeof visionneuseCap !== 'undefined'
      && visionneuseCap.retourDemande(stockage, maintenant());
    if (retourVisionneuse) {
      const apresChargementOeil = () => { void ouvrirOeil(compte.connecte() ? '' : compte.message()); };
      if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', apresChargementOeil, { once: true });
      else apresChargementOeil();
    }
    // 08/11/2026 (accord de Max) : « Autoriser » touché dans la fenêtre « Musique » : au retour, Autre puis la musique
    // (le Lecteur, branché par relations_mp3.js) au lieu de « Réglages du Drive ».
    const retourMusique = !retourVisionneuse && compte.retourRecent() && stockage && typeof visionneuseCap !== 'undefined'
      && visionneuseCap.retourDemande(stockage, maintenant(), visionneuseCap.CLE_RETOUR_MUSIQUE);
    if (retourMusique) {
      const apresChargementMusique = () => {
        const autre = el('ouvrir-autre');
        const lecteur = el('ouvrir-lecteur');
        if (autre && el('ecran-autre') && el('ecran-autre').hidden) autre.click();
        if (lecteur) lecteur.click();
      };
      if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', apresChargementMusique, { once: true });
      else apresChargementMusique();
    } else if (!retourVisionneuse && compte.retourRecent()) {
      const apresChargement = () => {
        const ouvrir = el('ouvrir-reglages-drive');
        if (ouvrir && !el('reglages-drive')?.open) ouvrir.click();
        ecrire(compte.message());
        if (!compte.connecte()) return;
        const avant = zone.textContent;
        const siRienDautre = texte => { if (zone.textContent === avant) ecrire(texte); };
        compte.verifier().then(siRienDautre).catch(erreur => siRienDautre(raison(erreur)));
      };
      if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', apresChargement, { once: true });
      else apresChargement();
    }

    connecter.addEventListener('click', () => {
      try {
        if (champ.value.trim()) compte.enregistrerAdresse(champ.value);
        ecrire('Ouverture de la page de Google… Choisis le compte Cap, PAS ton compte personnel. Cap revient tout seul ensuite, et le résultat s’affiche ici.');
        compte.seConnecter();
      } catch (erreur) { ecrire(raison(erreur)); }
    });

    bouton.addEventListener('click', () => attenteLecture.pendant(bouton, async () => {
      boutonPdf.hidden = true;
      zoneDocuments.hidden = true;
      ecrire('Lecture du Drive du compte Cap… (rien n’est modifié)');
      try {
        const r = await compter(compte);
        pdfs = [...r.pdfs, ...r.documents.pdfs];
        ecrire(resumer(r), 'Relations');
        montrer(zoneDocuments, resumerDocuments(r.documents), 'Documents');
        if (pdfs.length) { boutonPdf.textContent = `Afficher les PDF dans Cap (${pdfs.length})`; boutonPdf.hidden = false; }
      } catch (erreur) { ecrire(`${raison(erreur)} Rien n’a été modifié.`); }
    }));

    const montrerPage = async () => {
      const vue = doc.defaultView;
      await dessinerPage(pdf, numero, canvas, Math.min(vue.innerWidth || 400, 900) - 32, vue.devicePixelRatio);
      // Les numéros ne sont affichés qu'une fois la page dessinée.
      etiquette.textContent = `PDF ${indexPdf + 1} sur ${pdfs.length} · Page ${numero} sur ${pdf.numPages}`;
      precedente.disabled = numero <= 1;
      suivante.disabled = numero >= pdf.numPages;
    };

    // Ouvre le PDF n° i (le précédent est libéré de la mémoire).
    const ouvrirIndex = async i => {
      indexPdf = i;
      pdfAvant.disabled = i <= 0;
      pdfApres.disabled = i >= pdfs.length - 1;
      precedente.disabled = true;
      suivante.disabled = true;
      if (pdf) { pdf.destroy(); pdf = null; }
      etiquette.textContent = `Lecture en cours… (PDF ${i + 1} sur ${pdfs.length})`;
      etiquette.classList.add('en-lecture');
      try {
        pdf = await ouvrirPdf(compte, pdfs[i], await pdfjs());
        numero = 1;
        await montrerPage();
      } catch (erreur) { etiquette.textContent = `PDF ${i + 1} illisible : ${raison(erreur)}`; }
      finally { etiquette.classList.remove('en-lecture'); }
    };

    boutonPdf.addEventListener('click', () => {
      if (!pdfs.length) return;
      // 07/11/2026 (étape B, lot 1, accord de Max) : les PDF s'ouvrent dans la visionneuse de Zencoder.
      // L'ancien petit lecteur ci-dessous est DÉSACTIVÉ dans Cap (code gardé, utilisé seulement sans visionneuse).
      const v = typeof visionneuse === 'function' ? visionneuse() : visionneuse;
      if (v) { void v.ouvrir(pdfs.map(id => ({ id }))); return; }
      if (!lecteur.open) lecteur.showModal();
      void ouvrirIndex(0);
    });
    const changer = ecart => {
      if (!pdf || numero + ecart < 1 || numero + ecart > pdf.numPages) return;
      numero += ecart;
      montrerPage().catch(erreur => { etiquette.textContent = `Page illisible : ${raison(erreur)}`; });
    };
    precedente.addEventListener('click', () => changer(-1));
    suivante.addEventListener('click', () => changer(1));
    pdfAvant.addEventListener('click', () => { if (indexPdf > 0) void ouvrirIndex(indexPdf - 1); });
    pdfApres.addEventListener('click', () => { if (indexPdf < pdfs.length - 1) void ouvrirIndex(indexPdf + 1); });
    fermer.addEventListener('click', () => { lecteur.close(); if (pdf) { pdf.destroy(); pdf = null; } });
  }

  return { lireArbre, sorte, compter, resumer, resumerDocuments, chargerPdfjs, ouvrirPdf, dessinerPage, brancher };
})();

if (!(typeof window !== 'undefined' && window.CAP_TESTS)) {
  relationsCompte.brancher(document, { compte: googleCompteRelations, pdfjs: () => relationsCompte.chargerPdfjs(document, window),
    visionneuse: () => (typeof visionneuseCap !== 'undefined' ? visionneuseCap.instance : null) });
}
