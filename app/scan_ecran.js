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
    const boutonsProposition = ['scanner-proposition-oui', 'scanner-proposition-modifier', 'scanner-proposition-non'].map(parId);
    // { texte, mot_cle, nom_propose, raison, reponse } : texte lu sur le téléphone, jamais envoyé.
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
      let illisibles = 0;
      let prises = 0;
      validerPage();
      pageARefaire = null;
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
          if (morceau.lu === false) illisibles++;
          if (morceau.texte) textes.push(String(morceau.texte));
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
      lectureGoogle = { texte: [lectureGoogle && lectureGoogle.texte, ...textes].filter(Boolean).join('\n'),
        mot_cle: '', nom_propose: '', raison: '', reponse: '' };
      dire(`${prises} page${prises > 1 ? 's' : ''} reçue${prises > 1 ? 's' : ''} du scanner de Google.`
        + (illisibles ? ` ${illisibles} sans texte lisible.` : ''));
      await preparerProposition();
      return { pages: prises, proposition: lectureGoogle.nom_propose };
    }

    async function preparerProposition() {
      nomGoogle = '';
      lectureGoogle.reponse = '';
      propositionModification.hidden = true;
      propositionErreur.hidden = true;
      propositionStatut.textContent = '';
      let lignes = null;
      let probleme = '';
      try {
        if (!sourceClassement) throw new Error('le tableur n’est pas disponible ici');
        lignes = await sourceClassement.lireTableurChoisi();
      } catch (erreur) {
        probleme = `Je n’ai pas pu lire le tableur de classement (${erreur.message}). Le scan gardera son nom SCAN-… dans 00_A_CLASSER.`;
      }
      const p = lignes ? nommageScan.proposer(lectureGoogle.texte, lignes) : { nom: '', mot_cle: '', raison: 'tableur', date: '' };
      lectureGoogle.mot_cle = p.mot_cle;
      lectureGoogle.nom_propose = p.nom;
      lectureGoogle.raison = p.raison;
      const avecNom = Boolean(p.nom);
      boutonsProposition.forEach(bouton => { bouton.hidden = !avecNom; });
      propositionNom.textContent = avecNom ? `${p.nom}.pdf` : '';
      propositionInfo.textContent = probleme || ({
        trouve: `Mot-clé repéré : « ${p.mot_cle} ».${p.date ? '' : ' Aucune date lisible : « DATE A PRECISER ».'} Rien n’est renommé tant que tu n’as pas dit Oui.`,
        aucun: 'Aucun mot-clé du tableur dans le texte lu : le scan gardera son nom SCAN-… dans 00_A_CLASSER.',
        contradictoire: 'Plusieurs mots-clés qui ne vont pas ensemble : je ne choisis pas. Le scan gardera son nom SCAN-… dans 00_A_CLASSER.',
        sans_texte: 'Je n’ai pas pu lire de texte sur ces pages : le scan gardera son nom SCAN-… dans 00_A_CLASSER.'
      })[p.raison];
      zoneProposition.hidden = false;
    }

    function repondreOui() {
      if (!lectureGoogle || !lectureGoogle.nom_propose) return;
      const modifie = !propositionModification.hidden;
      const verdict = nommageScan.verifierNom(modifie ? propositionChamp.value : lectureGoogle.nom_propose);
      if (!verdict.ok) {
        propositionErreur.textContent = verdict.raison;
        propositionErreur.hidden = false;
        return;
      }
      propositionErreur.hidden = true;
      nomGoogle = verdict.base;
      lectureGoogle.reponse = modifie ? 'Modifié' : 'Oui';
      propositionModification.hidden = true;
      propositionNom.textContent = `${verdict.base}.pdf`;
      const texte = `Nom retenu : ${verdict.base}.pdf. Il sera utilisé quand tu appuieras sur « Terminé ».`;
      propositionStatut.textContent = texte;
      dire(texte);
    }

    function repondreModifier() {
      if (!lectureGoogle || !lectureGoogle.nom_propose) return;
      propositionChamp.value = nomGoogle || lectureGoogle.nom_propose;
      propositionModification.hidden = false;
      propositionErreur.hidden = true;
      propositionStatut.textContent = 'Change le nom, puis touche « Oui ».';
      propositionChamp.focus();
    }

    function repondreNon() {
      if (!lectureGoogle) return;
      nomGoogle = '';
      lectureGoogle.reponse = 'Non';
      propositionModification.hidden = true;
      propositionErreur.hidden = true;
      const texte = 'D’accord : le scan gardera son nom SCAN-… dans 00_A_CLASSER.';
      propositionStatut.textContent = texte;
      dire(texte);
    }

    // Journal Numérisation : une ligne par lecture (jamais le texte lu), écrite à « Terminé ».
    function noterLectureGoogle(fiche) {
      if (!lectureGoogle || !journauxChantier) return;
      const resultat = lectureGoogle.raison === 'trouve' ? lectureGoogle.mot_cle
        : lectureGoogle.raison === 'contradictoire' ? `mots-clés contradictoires : ${lectureGoogle.mot_cle}` : 'aucun';
      try {
        journauxChantier.ajouter('numerisation', {
          action: 'Lecture du texte', resultat,
          details: [`nom proposé : ${lectureGoogle.nom_propose ? `${lectureGoogle.nom_propose}.pdf` : 'aucun'}`,
            `ancien nom : ${fiche.nom}`, `nom retenu : ${fiche.nom_valide || fiche.nom}`,
            `réponse : ${lectureGoogle.reponse || 'sans réponse'}`].join(' ; ')
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
    parId('scanner-proposition-oui').addEventListener('click', repondreOui);
    parId('scanner-proposition-modifier').addEventListener('click', repondreModifier);
    parId('scanner-proposition-non').addEventListener('click', repondreNon);
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
