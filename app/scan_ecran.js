'use strict';

// Écran du scanner : caméra, pages, boutons « Page suivante » et « Terminé », mode rafale, dépôt.
// Les règles sont dans scan_documents.js, l'image dans scan_image.js, le PDF dans scan_pdf.js.
const scanEcran = (() => {
  const cote_photo_max = 2400;
  const qualite_jpeg = 0.85;
  const hauteur_miniature = 56;

  function initialiser(options = {}) {
    const parId = id => document.getElementById(id);
    const fenetre = parId('scanner');
    if (!fenetre) return null;
    const annoncer = options.annoncer || (() => {});
    const file = options.file || scanFile.creer();
    const depot = options.depot || scanDepot;
    // Étape 3 (05/11/2026) : scanner de Google et texte lu sur le téléphone, dans la coque seulement.
    const sourceClassement = options.classement || (typeof classement !== 'undefined' ? classement : null);
    const journauxChantier = options.journaux || (typeof journaux !== 'undefined' ? journaux : null);
    const scannerAndroid = options.scannerAndroid || (typeof window !== 'undefined' ? window.ScannerAndroid : null);
    const maintenant = options.maintenant || (() => new Date());
    const session = scanDocuments.creerSession();
    const rafale = scanDocuments.creerRafale(options.delaiRafale);

    const video = parId('scanner-video');
    const travail = parId('scanner-travail');
    const apercu = parId('scanner-apercu');
    const revue = parId('scanner-revue');
    const message = parId('scanner-message');
    const compteur = parId('scanner-compteur');
    const liste = parId('scanner-pages');
    const etat = parId('scanner-etat');
    const interrupteur = parId('scanner-rafale');
    const boutonCapturer = parId('scanner-capturer');
    const camera = parId('scanner-camera');

    const boutonLire = parId('scanner-lire');
    const zoneAccord = parId('scanner-accord');
    const texteAccord = parId('scanner-accord-texte');
    const zoneTexte = parId('scanner-texte-zone');
    const texteLu = parId('scanner-texte');
    const zoneNom = parId('scanner-nom-zone');
    const champNom = parId('scanner-nom');
    const nomManque = parId('scanner-nom-manque');
    const nomErreur = parId('scanner-nom-erreur');
    const nomStatut = parId('scanner-nom-statut');
    let pagesProposees = null;
    let texteDocument = '';
    let nomPropose = '';
    let nomValide = '';
    let lectureEnCours = false;

    const boutonGoogle = parId('scanner-google');
    const zoneProposition = parId('scanner-proposition');
    const propositionInfo = parId('scanner-proposition-info');
    const propositionNom = parId('scanner-proposition-nom');
    const propositionModification = parId('scanner-proposition-modification');
    const propositionChamp = parId('scanner-proposition-champ');
    const propositionErreur = parId('scanner-proposition-erreur');
    const propositionStatut = parId('scanner-proposition-statut');
    const propositionDiagnostic = parId('scanner-proposition-diagnostic');
    const boutonsAvecNom = ['scanner-proposition-oui', 'scanner-proposition-modifier', 'scanner-proposition-non'].map(parId);
    const boutonsSansNom = ['scanner-proposition-daccord', 'scanner-proposition-ecrire'].map(parId);
    // Texte lu sur le téléphone (jamais envoyé), nombres de caractères et de pages, proposition, réponse.
    let lectureGoogle = null;
    let nomGoogle = '';

    const indicateur = parId('scans-en-attente');
    let minuteurIndicateur = null;
    let dernierNombre = 0;
    let flux = null;
    let enAttente = null;
    let minuteur = null;
    let occupe = false;

    function dire(texte) {
      message.textContent = texte;
      message.hidden = !texte;
    }

    function afficherCompteur() {
      const n = session.nombre();
      const courante = n + 1;
      compteur.textContent = n === 0 ? 'Page 1' : `Page ${courante} (${n} déjà prise${n > 1 ? 's' : ''})`;
    }

    function montrerCamera() {
      pagesProposees = null;
      zoneAccord.hidden = true;
      revue.hidden = true;
      camera.hidden = false;
      boutonCapturer.hidden = false;
      afficherCompteur();
    }

    function montrerRevue() {
      revue.hidden = false;
      camera.hidden = true;
      boutonCapturer.hidden = true;
    }

    async function demarrerCamera() {
      if (flux) return;
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        dire('La caméra n’est pas disponible ici. Utilise le bouton « appareil photo du téléphone ».');
        return;
      }
      try {
        flux = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: 'environment' }, width: { ideal: 1920 }, height: { ideal: 1080 } }, audio: false
        });
        const piste = flux.getVideoTracks()[0];
        try { await piste.applyConstraints({ advanced: [{ focusMode: 'continuous' }] }); } catch (erreur) {}
        video.srcObject = flux;
        await video.play().catch(() => {});
      } catch (erreur) {
        flux = null;
        dire('Je n’ai pas accès à la caméra. Autorise-la dans Chrome, ou utilise le bouton « appareil photo du téléphone ».');
      }
    }

    function arreterCamera() {
      if (flux) flux.getTracks().forEach(piste => piste.stop());
      flux = null;
      video.srcObject = null;
    }

    function versCanvas(image, canvas) {
      canvas.width = image.width;
      canvas.height = image.height;
      canvas.getContext('2d').putImageData(new ImageData(new Uint8ClampedArray(image.data), image.width, image.height), 0, 0);
    }

    function enJpeg(canvas) {
      return new Promise((resolve, reject) => {
        canvas.toBlob(blob => {
          if (!blob) { reject(new Error('Impossible de fabriquer l’image de la page.')); return; }
          blob.arrayBuffer().then(buffer => resolve(new Uint8Array(buffer)), reject);
        }, 'image/jpeg', qualite_jpeg);
      });
    }

    function miniature(canvas) {
      const petite = document.createElement('canvas');
      petite.height = hauteur_miniature;
      petite.width = Math.max(1, Math.round(canvas.width * hauteur_miniature / canvas.height));
      petite.getContext('2d').drawImage(canvas, 0, 0, petite.width, petite.height);
      petite.className = 'miniature';
      petite.setAttribute('role', 'img');
      return petite;
    }

    let enRevue = null;

    function afficherPages() {
      const pages = session.pages();
      liste.replaceChildren(...pages.map((page, i) => {
        const ligne = document.createElement('li');
        ligne.dataset.page = String(page.id);
        const numero = document.createElement('span');
        numero.className = 'numero';
        numero.textContent = `Page ${i + 1}`;
        const boutons = [
          ['reprendre', 'Reprendre', () => reprendrePage(page.id)],
          ['monter', 'Monter', () => { session.deplacer(page.id, -1); afficherPages(); }],
          ['descendre', 'Descendre', () => { session.deplacer(page.id, 1); afficherPages(); }],
          ['supprimer', 'Supprimer', () => { session.supprimer(page.id); afficherPages(); }]
        ].map(([classe, texte, action]) => {
          const bouton = document.createElement('button');
          bouton.type = 'button';
          bouton.className = classe;
          bouton.textContent = texte;
          bouton.setAttribute('aria-label', `${texte} la page ${i + 1}`);
          bouton.addEventListener('click', action);
          return bouton;
        });
        ligne.append(page.miniature.cloneNode(true), numero, ...boutons);
        const copie = ligne.querySelector('canvas');
        if (copie) copie.getContext('2d').drawImage(page.miniature, 0, 0);
        return ligne;
      }));
      afficherCompteur();
    }

    let pageARefaire = null;

    function reprendrePage(id) {
      pageARefaire = id;
      dire('Reprends la photo de cette page : elle prendra la place de l’ancienne.');
      montrerCamera();
    }

    async function recevoirImage(image) {
      if (occupe) return null;
      occupe = true;
      try {
        rafale.toucher();
        const resultat = scanImage.traiter(image);
        const canvas = document.createElement('canvas');
        versCanvas(resultat.page, canvas);
        const jpeg = await enJpeg(canvas);
        const page = {
          jpeg, largeur: canvas.width, hauteur: canvas.height, vide: resultat.vide,
          alertes: resultat.qualite.alertes, miniature: miniature(canvas)
        };
        if (page.vide && session.nombre() > 0 && pageARefaire === null) {
          session.ajouter(page);
          dire('Page blanche ignorée (verso vide).');
          montrerCamera();
          return { ignoree: true };
        }
        enRevue = { page, canvas, bords: resultat.bords_trouves, redressee: resultat.redressee };
        versCanvas(resultat.page, apercu);
        const phrases = [];
        const alerte = scanImage.phrase(page.alertes);
        if (alerte) phrases.push(`${alerte} Tu peux reprendre la photo.`);
        if (!resultat.bords_trouves) phrases.push('Je n’ai pas trouvé les bords du document : je garde la photo entière.');
        dire(phrases.join(' '));
        montrerRevue();
        return { ignoree: false, alertes: page.alertes, bords: resultat.bords_trouves };
      } finally {
        occupe = false;
      }
    }

    function validerPage() {
      if (!enRevue) return;
      const { page } = enRevue;
      enRevue = null;
      if (pageARefaire !== null) {
        const id = pageARefaire;
        pageARefaire = null;
        session.remplacer(id, page);
      } else {
        session.ajouter({ ...page, vide: false });
      }
      afficherPages();
    }

    async function capturerDepuisCamera() {
      if (!flux || !video.videoWidth) { dire('La caméra n’est pas prête.'); return; }
      // Photo fixe pleine résolution (exposition de la vraie photo) si le téléphone la permet ; sinon image de la vidéo.
      if (typeof ImageCapture === 'function') {
        try {
          const piste = flux.getVideoTracks()[0];
          const blob = await new ImageCapture(piste).takePhoto();
          if (blob && blob.size > 0) { await capturerDepuisFichier(blob); return; }
        } catch (erreur) {
          // Repli : on garde l’image de la vidéo.
        }
      }
      const echelle = Math.min(1, cote_photo_max / Math.max(video.videoWidth, video.videoHeight));
      travail.width = Math.round(video.videoWidth * echelle);
      travail.height = Math.round(video.videoHeight * echelle);
      const contexte = travail.getContext('2d', { willReadFrequently: true });
      contexte.drawImage(video, 0, 0, travail.width, travail.height);
      await recevoirImage(contexte.getImageData(0, 0, travail.width, travail.height));
    }

    async function capturerDepuisFichier(fichier) {
      const bitmap = await createImageBitmap(fichier);
      const echelle = Math.min(1, cote_photo_max / Math.max(bitmap.width, bitmap.height));
      travail.width = Math.round(bitmap.width * echelle);
      travail.height = Math.round(bitmap.height * echelle);
      const contexte = travail.getContext('2d', { willReadFrequently: true });
      contexte.drawImage(bitmap, 0, 0, travail.width, travail.height);
      if (bitmap.close) bitmap.close();
      await recevoirImage(contexte.getImageData(0, 0, travail.width, travail.height));
    }

    function raisonHorsLigne() {
      if (typeof navigator !== 'undefined' && navigator.onLine === false) return 'reseau';
      if (typeof depot.pret === 'function' && !depot.pret()) return 'google';
      return '';
    }

    function afficherIndicateur(nombre) {
      if (!indicateur) return;
      clearTimeout(minuteurIndicateur);
      if (nombre > 0) {
        indicateur.textContent = scanDocuments.messageEnAttente(nombre, raisonHorsLigne());
        indicateur.hidden = false;
      } else if (dernierNombre > 0) {
        indicateur.textContent = 'Tous les scans sont déposés dans 00_A_CLASSER.';
        indicateur.hidden = false;
        minuteurIndicateur = setTimeout(() => { indicateur.hidden = true; }, 10000);
      } else {
        indicateur.hidden = true;
      }
      dernierNombre = nombre;
    }

    async function afficherEtat() {
      try {
        const attente = await file.enAttente();
        etat.textContent = attente.length
          ? scanDocuments.messageEnAttente(attente.length, raisonHorsLigne())
          : 'Tous les scans sont déposés dans 00_A_CLASSER.';
        afficherIndicateur(attente.length);
      } catch (erreur) {
        etat.textContent = erreur.message;
      }
    }

    function lancerDepot() {
      const execution = (async () => {
        try {
          const resultat = await depot.deposerEnAttente(file, () => rafale.noter(false, true));
          if (resultat.deposes && !rafale.active()) {
            annoncer(`${resultat.deposes} scan${resultat.deposes > 1 ? 's' : ''} déposé${resultat.deposes > 1 ? 's' : ''} dans 00_A_CLASSER.`, true);
          }
          return resultat;
        } catch (erreur) {
          return { deposes: 0, restants: -1, erreur: erreur.message };
        } finally {
          await afficherEtat();
        }
      })();
      enAttente = execution;
      return execution;
    }

    function effacerLecture() {
      pagesProposees = null;
      texteDocument = '';
      nomPropose = '';
      nomValide = '';
      zoneAccord.hidden = true;
      zoneTexte.hidden = true;
      texteLu.textContent = '';
      zoneNom.hidden = true;
      champNom.value = '';
      nomManque.textContent = '';
      nomStatut.textContent = '';
      nomErreur.hidden = true;
      nomErreur.textContent = '';
      lectureGoogle = null;
      nomGoogle = '';
      zoneProposition.hidden = true;
      propositionModification.hidden = true;
      propositionErreur.hidden = true;
      propositionStatut.textContent = '';
    }

    // ----- Étape 3 : scanner de Google (coque) et nom proposé à partir du texte lu -----

    // Page déjà redressée et nettoyée par Google : pas de second traitement, seulement la taille.
    async function pageDepuisBlob(blob) {
      const bitmap = await createImageBitmap(blob);
      const echelle = Math.min(1, cote_photo_max / Math.max(bitmap.width, bitmap.height));
      const canvas = document.createElement('canvas');
      canvas.width = Math.max(1, Math.round(bitmap.width * echelle));
      canvas.height = Math.max(1, Math.round(bitmap.height * echelle));
      canvas.getContext('2d').drawImage(bitmap, 0, 0, canvas.width, canvas.height);
      if (bitmap.close) bitmap.close();
      const jpeg = await enJpeg(canvas);
      return { page: { jpeg, largeur: canvas.width, hauteur: canvas.height, vide: false, alertes: [], miniature: miniature(canvas) }, canvas };
    }

    function lancerScannerGoogle() {
      if (!scannerAndroid) return;
      arreterCamera();
      boutonGoogle.disabled = true;
      window.__scannerAndroidResultat = resultat => { void recevoirScanGoogle(resultat); };
      dire('L’écran de scan de Google s’ouvre…');
      try {
        scannerAndroid.scanner();
      } catch (erreur) {
        boutonGoogle.disabled = false;
        dire('Le scanner de Google n’a pas pu s’ouvrir.');
      }
    }

    // Pages reçues du scanner de Google. Le texte a déjà été lu SUR LE TÉLÉPHONE par la coque (les
    // images y sont effacées aussitôt) ; la recherche dans le tableur et la fenêtre attendent « Terminé ».
    async function recevoirScanGoogle(resultat) {
      boutonGoogle.disabled = false;
      if (!resultat || resultat.annule) {
        dire('Scan annulé : rien n’a été gardé.');
        montrerCamera();
        void demarrerCamera();
        return { pages: 0 };
      }
      if (resultat.erreur) { dire(String(resultat.erreur)); return { pages: 0, erreur: String(resultat.erreur) }; }
      const pages = Array.isArray(resultat.pages) ? resultat.pages : [];
      const textes = [];
      const echecs = [];
      const diagnostics = [];
      let prises = 0;
      validerPage();
      pageARefaire = null;
      const dejaDansLeDocument = session.nombre();
      try {
        for (const [i, morceau] of pages.entries()) {
          const reponse = await fetch(morceau.url, { cache: 'no-store' });
          if (!reponse.ok) throw new Error('Une page du scanner n’a pas pu être récupérée.');
          const { page, canvas } = await pageDepuisBlob(await reponse.blob());
          if (i < pages.length - 1) {
            session.ajouter(page);
          } else {
            enRevue = { page, canvas, bords: true, redressee: true };
            apercu.width = canvas.width;
            apercu.height = canvas.height;
            apercu.getContext('2d').drawImage(canvas, 0, 0);
          }
          prises++;
          diagnostics.push(diagnosticPage(morceau, dejaDansLeDocument + i + 1));
          if (morceau.lu === false) echecs.push(dejaDansLeDocument + i + 1);
          else textes.push(String(morceau.texte || '').trim());
        }
      } catch (erreur) {
        afficherPages();
        dire(`${erreur.message} Les pages déjà prises sont gardées.`);
        return { pages: prises, erreur: erreur.message };
      } finally {
        try { if (scannerAndroid && scannerAndroid.oublierPages) scannerAndroid.oublierPages(); } catch (erreur) {}
      }
      afficherPages();
      if (enRevue) montrerRevue();
      const avant = lectureGoogle || { texte: '', caracteres: 0, pages_lues: 0, pages_total: 0, echecs: [], diagnostics: [] };
      lectureGoogle = {
        texte: [avant.texte, ...textes].filter(Boolean).join('\n'),
        caracteres: avant.caracteres + textes.reduce((total, texte) => total + texte.length, 0),
        pages_lues: avant.pages_lues + textes.length,
        pages_total: avant.pages_total + prises,
        echecs: [...avant.echecs, ...echecs],
        diagnostics: [...avant.diagnostics, ...diagnostics],
        mot_cle: '', nom_propose: '', raison: '', erreur_tableur: '', reponse: '', repondu: false
      };
      dire(`${prises} page${prises > 1 ? 's' : ''} reçue${prises > 1 ? 's' : ''} du scanner de Google. `
        + `Texte lu sur ${lectureGoogle.pages_lues} page${lectureGoogle.pages_lues > 1 ? 's' : ''} sur ${lectureGoogle.pages_total}.`
        + (echecs.length ? ` Lecture échouée : page${echecs.length > 1 ? 's' : ''} ${echecs.join(', ')}.` : '')
        + ' Appuie sur « Terminé » quand le document est complet.');
      return { pages: prises, echecs: echecs.length };
    }

    const nombreFrancais = new Intl.NumberFormat('fr-FR');

    // Diagnostic d'une page (06/11/2026), donné par la coque : JAMAIS le texte, seulement des nombres.
    function entier(valeur) {
      const nombre = Number(valeur);
      return Number.isFinite(nombre) ? Math.round(nombre) : null;
    }
    function diagnosticPage(morceau, numero) {
      if (morceau.lu === false) return `page ${numero} : lecture échouée`;
      const largeur = entier(morceau.largeur);
      const hauteur = entier(morceau.hauteur);
      if (largeur === null || hauteur === null) return `page ${numero} : diagnostic absent`;
      const essais = entier(morceau.essais) || 1;
      return `page ${numero} : ${largeur}×${hauteur} px, rotation ${entier(morceau.rotation) || 0}°`
        + ` (photo ${entier(morceau.rotation_exif) || 0}°), ${entier(morceau.blocs) || 0} bloc(s),`
        + ` ${entier(morceau.lignes) || 0} ligne(s), ${entier(morceau.caracteres) || 0} caractère(s)`
        + (essais > 1 ? `, ${essais} sens essayés` : '');
    }

    // À « Terminé » : recherche dans le tableur, puis fenêtre EN HAUT, toujours (même sans mot-clé).
    async function preparerProposition() {
      const lecture = lectureGoogle;
      nomGoogle = '';
      lecture.reponse = '';
      propositionModification.hidden = true;
      propositionErreur.hidden = true;
      propositionStatut.textContent = '';
      let p = { nom: '', mot_cle: '', raison: 'echec', date: '' };
      if (lecture.pages_lues) {
        try {
          if (!sourceClassement) throw new Error('tableur non disponible ici');
          p = nommageScan.proposer(lecture.texte, await sourceClassement.lireTableurChoisi());
        } catch (erreur) {
          p = { nom: '', mot_cle: '', raison: 'tableur', date: '' };
          lecture.erreur_tableur = String(erreur.message || 'raison inconnue').slice(0, 160);
        }
      }
      lecture.mot_cle = p.mot_cle;
      lecture.nom_propose = p.nom;
      lecture.raison = p.raison;
      const avecNom = Boolean(p.nom);
      boutonsAvecNom.forEach(bouton => { bouton.hidden = !avecNom; });
      boutonsSansNom.forEach(bouton => { bouton.hidden = avecNom; });
      propositionNom.textContent = avecNom ? `${p.nom}.pdf` : '';
      const lus = `${nombreFrancais.format(lecture.caracteres)} caractère${lecture.caracteres > 1 ? 's' : ''} lu${lecture.caracteres > 1 ? 's' : ''}`
        + ` (texte lu sur ${lecture.pages_lues} page${lecture.pages_lues > 1 ? 's' : ''} sur ${lecture.pages_total})`
        + (lecture.echecs.length ? `, lecture échouée : page${lecture.echecs.length > 1 ? 's' : ''} ${lecture.echecs.join(', ')}` : '');
      const garde = 'le scan gardera son nom SCAN-… dans 00_A_CLASSER.';
      propositionInfo.textContent = ({
        trouve: `${lus}, mot-clé du tableur repéré : « ${p.mot_cle} ».${p.date ? '' : ' Aucune date lisible : « DATE A PRECISER ».'} Rien n’est renommé tant que tu n’as pas dit Oui.`,
        aucun: `${lus}, aucun mot-clé du tableur trouvé : ${garde}`,
        contradictoire: `${lus}, plusieurs mots-clés du tableur qui ne vont pas ensemble : je ne choisis pas, ${garde}`,
        sans_texte: `${lus} : aucun texte lu, ${garde}`,
        echec: `Lecture du texte échouée sur toutes les pages (${lecture.pages_total}) : ${garde}`,
        tableur: `${lus}, mais je n’ai pas pu lire le tableur de classement (${lecture.erreur_tableur}) : ${garde}`
      })[p.raison];
      propositionDiagnostic.textContent = lecture.diagnostics.length ? ['Diagnostic :', ...lecture.diagnostics].join('\n') : '';
      propositionDiagnostic.hidden = !lecture.diagnostics.length;
      zoneProposition.hidden = false;
      if (zoneProposition.scrollIntoView) zoneProposition.scrollIntoView({ block: 'start' });
    }

    function nomPourOui() {
      if (!propositionModification.hidden) return { texte: propositionChamp.value, reponse: lectureGoogle.nom_propose ? 'Modifié' : 'Écrit par Max' };
      return lectureGoogle.nom_propose ? { texte: lectureGoogle.nom_propose, reponse: 'Oui' } : null;
    }

    // Un nom (proposé, modifié ou écrit par Max) n'est retenu qu'après « Oui » ; le scan est alors enregistré.
    async function repondreOui() {
      if (!lectureGoogle || lectureGoogle.repondu) return;
      const choix = nomPourOui();
      if (!choix) return;
      const verdict = nommageScan.verifierNom(choix.texte);
      if (!verdict.ok) {
        propositionErreur.textContent = verdict.raison;
        propositionErreur.hidden = false;
        return;
      }
      propositionErreur.hidden = true;
      nomGoogle = verdict.base;
      lectureGoogle.reponse = choix.reponse;
      await finaliserApresReponse(`Nom retenu : ${verdict.base}.pdf.`);
    }

    function ouvrirSaisie(valeur, consigne) {
      propositionChamp.value = valeur;
      propositionModification.hidden = false;
      propositionErreur.hidden = true;
      boutonsAvecNom[0].hidden = false;
      propositionStatut.textContent = consigne;
      propositionChamp.focus();
    }

    function repondreModifier() {
      if (!lectureGoogle || lectureGoogle.repondu || !lectureGoogle.nom_propose) return;
      ouvrirSaisie(nomGoogle || lectureGoogle.nom_propose, 'Change le nom, puis touche « Oui ».');
    }

    function repondreEcrire() {
      if (!lectureGoogle || lectureGoogle.repondu) return;
      ouvrirSaisie('', 'Écris le nom, puis touche « Oui ». Rien n’est enregistré avant.');
    }

    async function repondreSansNom(reponse) {
      if (!lectureGoogle || lectureGoogle.repondu) return;
      nomGoogle = '';
      lectureGoogle.reponse = reponse;
      propositionModification.hidden = true;
      propositionErreur.hidden = true;
      await finaliserApresReponse('Le scan garde son nom SCAN-… dans 00_A_CLASSER.');
    }

    async function finaliserApresReponse(texte) {
      lectureGoogle.repondu = true;
      propositionStatut.textContent = texte;
      const fiche = await terminerDocument();
      if (fiche) await apresTermine();
    }

    function resultatJournal(lecture) {
      switch (lecture.raison) {
        case 'trouve': return `mot-clé : ${lecture.mot_cle}`;
        case 'contradictoire': return `mots-clés contradictoires : ${lecture.mot_cle}`;
        case 'aucun': return 'aucun mot-clé trouvé';
        case 'sans_texte': return 'aucun texte lu';
        case 'echec': return 'lecture échouée';
        case 'tableur': return `tableur non lu (${lecture.erreur_tableur})`;
        default: return 'recherche non faite (document fermé sans « Terminé »)';
      }
    }

    // Journal Numérisation : une ligne par lecture, à l'enregistrement du scan. Le nombre de
    // caractères lus, jamais le texte lu lui-même.
    function noterLectureGoogle(fiche) {
      if (!lectureGoogle || !journauxChantier) return;
      const l = lectureGoogle;
      try {
        journauxChantier.ajouter('numerisation', {
          action: 'Lecture du texte', resultat: resultatJournal(l),
          details: [`caractères lus : ${l.caracteres}`, `pages lues : ${l.pages_lues} sur ${l.pages_total}`,
            ...(l.echecs.length ? [`lecture échouée : page${l.echecs.length > 1 ? 's' : ''} ${l.echecs.join(', ')}`] : []),
            ...(l.diagnostics.length ? [`diagnostic : ${l.diagnostics.join(' | ')}`] : []),
            `nom proposé : ${l.nom_propose ? `${l.nom_propose}.pdf` : 'aucun'}`,
            `ancien nom : ${fiche.nom}`, `nom retenu : ${fiche.nom_valide || fiche.nom}`,
            `réponse : ${l.reponse || 'sans réponse'}`].join(' ; ')
        });
      } catch (erreur) {
        annoncer(`La ligne du Journal Numérisation n’a pas pu être gardée : ${erreur.message}`, false);
      }
    }

    function nomsDejaPris(fiches) {
      return fiches.flatMap(f => [f.nom, f.nom_valide].filter(Boolean));
    }

    // Cap propose un nom à partir de ce que l'IA a lu. Rien n'est retenu tant que Max n'a pas cliqué.
    async function proposerNom(identification) {
      const proposition = scanNommage.proposer(identification, nomsDejaPris(await file.lister()));
      nomPropose = proposition.nom;
      nomValide = '';
      champNom.value = proposition.base;
      nomErreur.hidden = true;
      nomStatut.textContent = 'Rien n’est renommé tant que tu n’as pas validé.';
      nomManque.textContent = !identification
        ? 'Je n’ai pas pu lire l’identité du document : complète le nom toi-même, ou garde le nom provisoire.'
        : proposition.manques.length
          ? `Je ne suis pas sûr : il me manque ${proposition.manques.join(', ')}. Complète le nom, ou garde le nom provisoire.`
          : 'Relis ce nom : l’IA peut se tromper.';
      zoneNom.hidden = false;
    }

    function validerNomPropose() {
      const verdict = scanNommage.verifier(champNom.value);
      if (!verdict.ok) {
        nomValide = '';
        nomErreur.textContent = verdict.raison;
        nomErreur.hidden = false;
        return;
      }
      nomErreur.hidden = true;
      nomValide = verdict.base;
      champNom.value = verdict.base;
      const confirmation = `Nom enregistré : ${verdict.base}.pdf. Il sera utilisé quand tu appuieras sur « Terminé » ; le nom d’origine est gardé.`;
      nomStatut.textContent = confirmation;
      dire(confirmation);
    }

    function garderNomProvisoire() {
      nomValide = '';
      nomErreur.hidden = true;
      const confirmation = 'Nom provisoire enregistré : le scan gardera son nom SCAN-… fixé à « Terminé ». La proposition reste gardée avec le scan.';
      nomStatut.textContent = confirmation;
      dire(confirmation);
    }

    // Pages que la lecture enverrait : celles déjà gardées, plus celle en aperçu (qui remplace l'ancienne si on reprend une page).
    function pagesALire() {
      const gardees = session.pages().map(page => ({ id: page.id, jpeg: page.jpeg }));
      if (!enRevue) return gardees;
      const neuve = { id: pageARefaire, jpeg: enRevue.page.jpeg };
      if (pageARefaire === null) return [...gardees, neuve];
      return gardees.map(page => (page.id === pageARefaire ? neuve : page));
    }

    // Étape 1 : Cap annonce ce qui partirait, et attend le « oui » de Max. Rien n'est envoyé ici.
    function demanderLecture() {
      if (lectureEnCours) return;
      zoneAccord.hidden = true;
      const pages = pagesALire();
      const raison = scanLecture.verifier(pages.length);
      if (raison) { dire(raison); return; }
      pagesProposees = pages;
      texteAccord.textContent = scanLecture.phraseAccord(pages.length);
      zoneAccord.hidden = false;
    }

    function refuserLecture() {
      pagesProposees = null;
      zoneAccord.hidden = true;
      dire('D’accord : rien n’a été envoyé.');
    }

    // Étape 2 : seulement après le « oui ». Les mêmes pages que celles annoncées, jamais d'autres.
    async function accepterLecture() {
      const pages = pagesProposees;
      pagesProposees = null;
      zoneAccord.hidden = true;
      if (!pages || lectureEnCours) return null;
      lectureEnCours = true;
      boutonLire.disabled = true;
      dire('Lecture du texte en cours…');
      try {
        const resultat = await scanLecture.lire(pages, { accord: true });
        texteDocument = resultat.texte;
        texteLu.textContent = resultat.texte;
        zoneTexte.hidden = false;
        await proposerNom(resultat.identification);
        dire('Texte lu. Relis-le : l’IA peut se tromper, les mots incertains sont marqués [?] ou [illisible].');
        return resultat;
      } catch (erreur) {
        dire(erreur.message);
        return null;
      } finally {
        lectureEnCours = false;
        boutonLire.disabled = false;
      }
    }

    async function terminerDocument() {
      validerPage();
      if (!session.nombre()) { dire('Aucune page prise.'); return null; }
      const nombre = session.nombre();
      const pages = session.pages();
      let fiche;
      try {
        const pdf = scanPdf.assembler(pages.map(p => ({ jpeg: p.jpeg, largeur: p.largeur, hauteur: p.hauteur })));
        const existants = nomsDejaPris(await file.lister());
        const base = nomValide ? scanNommage.verifier(nomValide) : null;
        // Nom tiré du tableur : seulement après le « Oui » de Max ; sinon, comme avant.
        const nomRetenu = nomGoogle ? scanNommage.uniqueAvecExtension(nomGoogle, existants)
          : base && base.ok ? scanNommage.uniqueAvecExtension(base.base, existants) : '';
        fiche = {
          nom: scanDocuments.nomFichier(maintenant(), existants),
          pdf: new Blob([pdf], { type: 'application/pdf' }),
          pages: nombre,
          texte: texteDocument || (lectureGoogle ? lectureGoogle.texte : ''),
          nom_propose: nomPropose || (lectureGoogle && lectureGoogle.nom_propose ? `${lectureGoogle.nom_propose}.pdf` : ''),
          nom_valide: nomRetenu
        };
        await file.ajouter(fiche);
        noterLectureGoogle(fiche);
      } catch (erreur) {
        dire(`Le scan n’a pas pu être enregistré : ${erreur.message} Tes pages sont toujours là.`);
        afficherPages();
        return null;
      }
      const ignorees = session.ignorees();
      session.vider();
      pageARefaire = null;
      effacerLecture();
      afficherPages();
      rafale.noter(true, false);
      const horsLigne = raisonHorsLigne();
      await afficherEtat();
      const retenu = fiche.nom_valide ? ` Nom retenu : ${fiche.nom_valide}.` : '';
      const texte = scanDocuments.messageEnregistre(nombre, horsLigne) + retenu + (ignorees ? ` ${ignorees} page${ignorees > 1 ? 's' : ''} blanche${ignorees > 1 ? 's' : ''} ignorée${ignorees > 1 ? 's' : ''}.` : '');
      annoncer(texte, !horsLigne);
      dire(texte);
      void lancerDepot();
      return fiche;
    }

    async function finRafale() {
      if (!rafale.active()) return null;
      const compte = rafale.compte();
      rafale.arreter();
      interrupteur.checked = false;
      if (enAttente) await enAttente;
      if (compte.scannes) annoncer(rafale.compteRendu());
      return rafale.compteRendu();
    }

    async function apresTermine() {
      if (rafale.active()) {
        montrerCamera();
        await demarrerCamera();
      } else {
        await fermer();
      }
    }

    async function fermer() {
      if (enRevue || session.nombre()) await terminerDocument();
      if (rafale.active()) await finRafale();
      clearInterval(minuteur);
      minuteur = null;
      arreterCamera();
      if (fenetre.open) fenetre.close();
    }

    function verifierInactivite() {
      if (rafale.expiree()) {
        void finRafale().then(() => dire('Mode rafale arrêté : trop longtemps sans scan.'));
      }
    }

    async function ouvrir() {
      session.vider();
      enRevue = null;
      pageARefaire = null;
      effacerLecture();
      dire('');
      afficherPages();
      montrerCamera();
      if (!fenetre.open) fenetre.showModal();
      await afficherEtat();
      clearInterval(minuteur);
      minuteur = setInterval(verifierInactivite, 15000);
      await demarrerCamera();
    }

    parId('ouvrir-scanner').addEventListener('click', () => { void ouvrir(); });
    // Le scanner de Google n'existe que dans la coque Android (pont ScannerAndroid).
    boutonGoogle.hidden = !scannerAndroid;
    boutonGoogle.addEventListener('click', lancerScannerGoogle);
    parId('scanner-proposition-oui').addEventListener('click', () => { void repondreOui(); });
    parId('scanner-proposition-modifier').addEventListener('click', repondreModifier);
    parId('scanner-proposition-non').addEventListener('click', () => { void repondreSansNom('Non'); });
    parId('scanner-proposition-daccord').addEventListener('click', () => { void repondreSansNom('D’accord'); });
    parId('scanner-proposition-ecrire').addEventListener('click', repondreEcrire);
    boutonCapturer.addEventListener('click', () => { void capturerDepuisCamera().catch(e => dire(e.message)); });
    parId('scanner-fichier').addEventListener('change', event => {
      const fichier = event.target.files && event.target.files[0];
      event.target.value = '';
      if (fichier) void capturerDepuisFichier(fichier).catch(e => dire(e.message));
    });
    parId('scanner-page-suivante').addEventListener('click', () => {
      validerPage();
      dire('');
      montrerCamera();
      void demarrerCamera();
    });
    parId('scanner-terminer').addEventListener('click', async () => {
      // Pages du scanner de Google : d'abord la recherche dans le tableur et la fenêtre ; le scan
      // n'est enregistré qu'après la réponse de Max (voir finaliserApresReponse).
      if (lectureGoogle && !lectureGoogle.repondu) {
        if (zoneProposition.hidden) await preparerProposition();
        else if (zoneProposition.scrollIntoView) zoneProposition.scrollIntoView({ block: 'start' });
        return;
      }
      const fiche = await terminerDocument();
      if (fiche) await apresTermine();
    });
    parId('scanner-reprendre').addEventListener('click', () => {
      enRevue = null;
      dire('Reprends la photo.');
      montrerCamera();
      void demarrerCamera();
    });
    boutonLire.addEventListener('click', demanderLecture);
    parId('scanner-accord-oui').addEventListener('click', () => { void accepterLecture(); });
    parId('scanner-accord-non').addEventListener('click', refuserLecture);
    champNom.addEventListener('input', () => {
      nomValide = '';
      nomErreur.hidden = true;
      nomStatut.textContent = 'Nom modifié : appuie sur « Valider ce nom » pour le retenir.';
    });
    parId('scanner-nom-valider').addEventListener('click', validerNomPropose);
    parId('scanner-nom-provisoire').addEventListener('click', garderNomProvisoire);
    interrupteur.addEventListener('change', () => {
      if (interrupteur.checked) rafale.demarrer();
      else void finRafale();
    });
    parId('scanner-fermer').addEventListener('click', () => { void fermer(); });
    fenetre.addEventListener('cancel', event => { event.preventDefault(); void fermer(); });
    fenetre.addEventListener('close', () => { arreterCamera(); });

    window.addEventListener('online', () => { void lancerDepot(); });
    window.addEventListener('offline', () => { void afficherEtat(); });
    window.addEventListener('cap-google-etat', () => { void lancerDepot(); });
    void lancerDepot();

    return {
      ouvrir, fermer, recevoirImage, terminerDocument, validerPage, lancerDepot, finRafale, afficherEtat,
      session, rafale, reprendrePage, demanderLecture, accepterLecture, refuserLecture, recevoirScanGoogle
    };
  }

  return { initialiser };
})();
