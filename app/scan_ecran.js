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

    async function afficherEtat() {
      try {
        const attente = await file.enAttente();
        etat.textContent = attente.length
          ? `${attente.length} scan${attente.length > 1 ? 's' : ''} gardé${attente.length > 1 ? 's' : ''} sur le téléphone, pas encore déposé${attente.length > 1 ? 's' : ''} dans Google Drive.`
          : 'Tous les scans sont déposés dans 00_A_CLASSER.';
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

    async function terminerDocument() {
      validerPage();
      if (!session.nombre()) { dire('Aucune page prise.'); return null; }
      const nombre = session.nombre();
      const pages = session.pages();
      let fiche;
      try {
        const pdf = scanPdf.assembler(pages.map(p => ({ jpeg: p.jpeg, largeur: p.largeur, hauteur: p.hauteur })));
        const existants = (await file.lister()).map(f => f.nom);
        fiche = { nom: scanDocuments.nomFichier(maintenant(), existants), pdf: new Blob([pdf], { type: 'application/pdf' }), pages: nombre };
        await file.ajouter(fiche);
      } catch (erreur) {
        dire(`Le scan n’a pas pu être enregistré : ${erreur.message} Tes pages sont toujours là.`);
        afficherPages();
        return null;
      }
      const ignorees = session.ignorees();
      session.vider();
      pageARefaire = null;
      afficherPages();
      rafale.noter(true, false);
      const texte = scanDocuments.messageEnregistre(nombre) + (ignorees ? ` ${ignorees} page${ignorees > 1 ? 's' : ''} blanche${ignorees > 1 ? 's' : ''} ignorée${ignorees > 1 ? 's' : ''}.` : '');
      annoncer(texte, true);
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
    interrupteur.addEventListener('change', () => {
      if (interrupteur.checked) rafale.demarrer();
      else void finRafale();
    });
    parId('scanner-fermer').addEventListener('click', () => { void fermer(); });
    fenetre.addEventListener('cancel', event => { event.preventDefault(); void fermer(); });
    fenetre.addEventListener('close', () => { arreterCamera(); });

    window.addEventListener('online', () => { void lancerDepot(); });
    window.addEventListener('cap-google-etat', () => { void lancerDepot(); });
    void lancerDepot();

    return {
      ouvrir, fermer, recevoirImage, terminerDocument, validerPage, lancerDepot, finRafale, afficherEtat,
      session, rafale, reprendrePage
    };
  }

  return { initialiser };
})();
