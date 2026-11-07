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
      url.search = new URLSearchParams({ q, fields: 'nextPageToken,files(id,name,mimeType,parents)', pageSize: '1000',
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

  function brancher(doc, { compte, pdfjs }) {
    const el = id => doc.getElementById(id);
    const champ = el('adresse-compte-relations');
    const connecter = el('connecter-compte-relations');
    const bouton = el('compter-compte-relations');
    const zone = el('resume-compte-relations');
    const boutonPdf = el('pdf-compte-relations');
    const lecteur = el('lecteur-pdf-relations');
    const canvas = el('canvas-pdf-relations');
    const etiquette = el('page-pdf-relations');
    const precedente = el('pdf-precedente-relations');
    const suivante = el('pdf-suivante-relations');
    const fermer = el('pdf-fermer-relations');
    if (!champ || !connecter || !bouton || !zone || !boutonPdf || !lecteur || !canvas || !etiquette || !precedente || !suivante || !fermer) return;
    const ecrire = texte => { zone.hidden = false; zone.textContent = texte; try { zone.scrollIntoView({ block: 'center' }); } catch (erreur) {} };
    const raison = erreur => String(erreur && erreur.message || 'raison inconnue').slice(0, 220);
    champ.value = compte.adresse();
    if (compte.message()) ecrire(compte.message());
    let pdfs = [];
    let pdf = null;
    let numero = 1;

    connecter.addEventListener('click', () => {
      try {
        if (champ.value.trim()) compte.enregistrerAdresse(champ.value);
        ecrire('Ouverture de la page de Google… Choisis le compte Cap, PAS ton compte personnel. Cap revient tout seul ensuite.');
        compte.seConnecter();
      } catch (erreur) { ecrire(raison(erreur)); }
    });

    bouton.addEventListener('click', () => attenteLecture.pendant(bouton, async () => {
      boutonPdf.hidden = true;
      ecrire('Lecture du Drive du compte Cap… (rien n’est modifié)');
      try {
        const r = await compter(compte);
        pdfs = [...r.pdfs, ...r.documents.pdfs];
        ecrire(`${resumer(r)}\n\n${resumerDocuments(r.documents)}`);
        if (pdfs.length) { boutonPdf.textContent = `Afficher un PDF dans Cap (1 sur ${pdfs.length})`; boutonPdf.hidden = false; }
      } catch (erreur) { ecrire(`${raison(erreur)} Rien n’a été modifié.`); }
    }));

    const montrerPage = async () => {
      const vue = doc.defaultView;
      await dessinerPage(pdf, numero, canvas, Math.min(vue.innerWidth || 400, 900) - 32, vue.devicePixelRatio);
      // Le numéro n'est affiché qu'une fois la page dessinée.
      etiquette.textContent = `Page ${numero} sur ${pdf.numPages}`;
      precedente.disabled = numero <= 1;
      suivante.disabled = numero >= pdf.numPages;
    };

    boutonPdf.addEventListener('click', async () => {
      if (!pdfs.length) return;
      etiquette.textContent = 'Lecture en cours… (ouverture du PDF)';
      etiquette.classList.add('en-lecture');
      if (!lecteur.open) lecteur.showModal();
      try {
        pdf = await ouvrirPdf(compte, pdfs[0], await pdfjs());
        numero = 1;
        await montrerPage();
      } catch (erreur) { etiquette.textContent = `PDF illisible : ${raison(erreur)}`; }
      finally { etiquette.classList.remove('en-lecture'); }
    });
    const changer = ecart => {
      if (!pdf || numero + ecart < 1 || numero + ecart > pdf.numPages) return;
      numero += ecart;
      montrerPage().catch(erreur => { etiquette.textContent = `Page illisible : ${raison(erreur)}`; });
    };
    precedente.addEventListener('click', () => changer(-1));
    suivante.addEventListener('click', () => changer(1));
    fermer.addEventListener('click', () => { lecteur.close(); if (pdf) { pdf.destroy(); pdf = null; } });
  }

  return { compter, resumer, resumerDocuments, chargerPdfjs, ouvrirPdf, dessinerPage, brancher };
})();

if (!(typeof window !== 'undefined' && window.CAP_TESTS)) {
  relationsCompte.brancher(document, { compte: googleCompteRelations, pdfjs: () => relationsCompte.chargerPdfjs(document, window) });
}
