'use strict';

// Écran d'ouverture « eau » (06/11/2026, étape 1 de l'intégration du travail de Zencoder, accord de Max).
// Repris du dossier d'essai de Zencoder (Cap_eau_essai), copié en lecture seule : l'eau dessinée par
// le code et la vidéo du galet. NON repris : la fausse page d'accueil FICTIF (remplacée par le vrai
// Cap) et la « capture » du doigt par l'eau, qui détournait les touchers destinés aux boutons.
// Règles :
// - l'écran d'eau s'affiche au DÉMARRAGE de Cap seulement (une marque dans sessionStorage, rien de
//   personnel, évite de le remontrer quand la page se recharge pendant la même ouverture) ;
// - un glissement net de bas en haut lance la vidéo du galet (sans son), puis « Entrer dans Cap » ;
// - REPLI : vidéo absente, illisible ou bloquée → l'eau seule reste et « Entrer dans Cap » apparaît
//   tout de suite ; Cap ne plante jamais ;
// - un seul réglage pour le fond : 'video', 'image' ou 'aucun' (REGLAGES ci-dessous) ;
// - la couche d'eau (creerCouche) ne capte JAMAIS un toucher (pointer-events: none) et peut être
//   posée ou retirée sur un autre écran sans toucher au reste (ambiance d'eau à venir, page par page) ;
// - l'animation s'arrête dès qu'on entre dans Cap (batterie).
const ecranEau = (() => {
  const REGLAGES = Object.freeze({
    fond: 'video', // 'video' | 'image' | 'aucun'
    video: 'eau/galet_sortie.mp4',
    image: '', // chemin d'une image fixe, si fond = 'image'
    dureeSecoursMs: 7000 // si la vidéo ne finit pas d'elle-même, les boutons apparaissent quand même
  });
  const CLE_VUE = 'cap_eau_vue_v1';
  const COULEUR_PEU_PROFOND = [201, 227, 221];
  const COULEUR_PROFOND = [156, 182, 184];
  const AMORTISSEMENT = 0.985;
  const CELLULES_CIBLE = 46000;

  // ----- Couche d'eau réutilisable (simulation de Zencoder) -----
  function creerCouche(toile, options = {}) {
    const fenetre = options.fenetre || (typeof window !== 'undefined' ? window : null);
    const raf = options.raf || (f => fenetre.requestAnimationFrame(f));
    const caf = options.caf || (id => fenetre.cancelAnimationFrame(id));
    const reduit = Boolean(options.animationsReduites
      ?? (fenetre && fenetre.matchMedia && fenetre.matchMedia('(prefers-reduced-motion: reduce)').matches));
    const ctx = toile.getContext('2d', { alpha: false });
    const basse = toile.ownerDocument.createElement('canvas');
    const ctxBasse = basse.getContext('2d');
    let largeur = 0, hauteur = 0, colonnes = 0, lignes = 0;
    let buf1 = null, buf2 = null, image = null;
    let identifiant = null;
    let prochaineOnde = 0;

    function dimensionner() {
      largeur = toile.clientWidth || 360;
      hauteur = toile.clientHeight || 640;
      toile.width = largeur;
      toile.height = hauteur;
      const echelle = Math.sqrt((largeur * hauteur) / CELLULES_CIBLE);
      colonnes = Math.max(20, Math.round(largeur / echelle));
      lignes = Math.max(20, Math.round(hauteur / echelle));
      buf1 = new Float32Array(colonnes * lignes);
      buf2 = new Float32Array(colonnes * lignes);
      basse.width = colonnes;
      basse.height = lignes;
      image = ctxBasse.createImageData(colonnes, lignes);
      for (let i = 0; i < colonnes * lignes; i++) image.data[i * 4 + 3] = 255;
    }

    function perturber(fracX, fracY, force, rayon) {
      if (!buf1) return;
      const bx = Math.round(fracX * colonnes);
      const by = Math.round(fracY * lignes);
      for (let dy = -rayon; dy <= rayon; dy++) {
        for (let dx = -rayon; dx <= rayon; dx++) {
          const x = bx + dx, y = by + dy;
          if (x < 1 || x >= colonnes - 1 || y < 1 || y >= lignes - 1) continue;
          const distance = Math.sqrt(dx * dx + dy * dy);
          if (distance > rayon) continue;
          buf1[y * colonnes + x] += force * (1 - distance / (rayon + 1));
        }
      }
    }

    function ondesAmbiantes(temps) {
      if (temps < prochaineOnde) return;
      prochaineOnde = temps + (reduit ? 3200 : 1800) + Math.random() * 1600;
      perturber(Math.random(), Math.random(), (reduit ? 0.5 : 1) + Math.random(), 1 + Math.round(Math.random() * 2));
    }

    function etape() {
      for (let y = 1; y < lignes - 1; y++) {
        const base = y * colonnes;
        for (let x = 1; x < colonnes - 1; x++) {
          const i = base + x;
          buf2[i] = ((buf1[i - 1] + buf1[i + 1] + buf1[i - colonnes] + buf1[i + colonnes]) / 2 - buf2[i]) * AMORTISSEMENT;
        }
      }
      const t = buf1; buf1 = buf2; buf2 = t;
    }

    function dessiner(temps) {
      const pixels = image.data;
      const reflet = ((Math.sin(temps * 0.00018) * 0.5 + 0.5) - 0.5) * 5;
      for (let y = 0; y < lignes; y++) {
        const t = y / lignes;
        const r0 = COULEUR_PEU_PROFOND[0] + (COULEUR_PROFOND[0] - COULEUR_PEU_PROFOND[0]) * t;
        const g0 = COULEUR_PEU_PROFOND[1] + (COULEUR_PROFOND[1] - COULEUR_PEU_PROFOND[1]) * t;
        const b0 = COULEUR_PEU_PROFOND[2] + (COULEUR_PROFOND[2] - COULEUR_PEU_PROFOND[2]) * t;
        const base = y * colonnes;
        for (let x = 0; x < colonnes; x++) {
          const i = base + x;
          let gx = 0, gy = 0;
          if (x > 0 && x < colonnes - 1) gx = buf1[i + 1] - buf1[i - 1];
          if (y > 0 && y < lignes - 1) gy = buf1[i + colonnes] - buf1[i - colonnes];
          const c = Math.max(-22, Math.min(22, (gx + gy) * 9));
          const p = i * 4;
          pixels[p] = Math.max(0, Math.min(255, r0 + c + reflet));
          pixels[p + 1] = Math.max(0, Math.min(255, g0 + c + reflet));
          pixels[p + 2] = Math.max(0, Math.min(255, b0 + c * 0.9 + reflet));
        }
      }
      ctxBasse.putImageData(image, 0, 0);
      ctx.imageSmoothingEnabled = true;
      ctx.drawImage(basse, 0, 0, colonnes, lignes, 0, 0, largeur, hauteur);
    }

    function boucle(temps) {
      if (identifiant === null) return;
      ondesAmbiantes(temps);
      etape();
      dessiner(temps);
      identifiant = raf(boucle);
    }

    function demarrer() {
      if (identifiant !== null) return;
      dimensionner();
      identifiant = raf(boucle);
    }
    function arreter() {
      if (identifiant !== null) caf(identifiant);
      identifiant = null;
    }
    if (fenetre && fenetre.addEventListener) fenetre.addEventListener('resize', () => { if (identifiant !== null) dimensionner(); });
    return { demarrer, arreter, perturber, dimensionner, active: () => identifiant !== null };
  }

  // ----- L'écran d'ouverture -----
  // racine : l'élément #ecran-eau (hors de .ecran, pour que ses gestes n'ouvrent jamais les tuiles).
  function monter(racine, options = {}) {
    const doc = racine.ownerDocument;
    const reglages = { ...REGLAGES, ...(options.reglages || {}) };
    const parSelecteur = s => racine.querySelector(s);
    const video = parSelecteur('#video-galet');
    const image = parSelecteur('#image-galet');
    const surface = parSelecteur('#surface-eau');
    const boutons = parSelecteur('#boutons-eau');
    const consigne = parSelecteur('#consigne-eau');
    const couche = creerCouche(parSelecteur('#toile-eau'), options);
    const minuterie = options.setTimeout || ((f, d) => setTimeout(f, d));
    const annulerMinuterie = options.clearTimeout || (id => clearTimeout(id));
    const maintenant = options.maintenant || (() => performance.now());
    let etatVideo = 'avant'; // 'avant' | 'lecture' | 'fin'
    let videoEnPanne = false;
    let secours = null;

    function videoUtilisable() {
      return reglages.fond === 'video' && Boolean(reglages.video) && !videoEnPanne;
    }
    function boutonsVisibles(visibles) {
      boutons.classList.toggle('visible', visibles);
      consigne.hidden = visibles || !videoUtilisable();
    }
    function annulerSecours() {
      if (secours !== null) annulerMinuterie(secours);
      secours = null;
    }
    function terminerVideo() {
      annulerSecours();
      etatVideo = 'fin';
      boutonsVisibles(true);
    }
    // Repli : la vidéo ne peut pas servir → l'eau seule, et « Entrer dans Cap » tout de suite.
    function panneVideo() {
      videoEnPanne = true;
      video.hidden = true;
      annulerSecours();
      if (!racine.hidden) boutonsVisibles(true);
    }

    // Fond : un seul réglage.
    if (reglages.fond === 'video' && reglages.video) {
      video.muted = true;
      video.volume = 0;
      video.addEventListener('loadeddata', () => { if (etatVideo === 'avant') { try { video.currentTime = 0; } catch (e) { /* rien */ } video.pause(); } });
      video.addEventListener('ended', terminerVideo);
      video.addEventListener('error', panneVideo);
      video.src = reglages.video;
      video.hidden = false;
    } else {
      video.hidden = true;
    }
    if (reglages.fond === 'image' && reglages.image) {
      image.addEventListener('error', () => { image.hidden = true; });
      image.src = reglages.image;
      image.hidden = false;
    } else {
      image.hidden = true;
    }

    function demarrerVideo() {
      if (etatVideo !== 'avant') return;
      if (!videoUtilisable()) { boutonsVisibles(true); return; }
      etatVideo = 'lecture';
      consigne.hidden = true;
      try { video.currentTime = 0; } catch (e) { /* rien */ }
      let lecture = null;
      try { lecture = video.play(); } catch (e) { panneVideo(); return; }
      if (lecture && typeof lecture.catch === 'function') lecture.catch(() => panneVideo());
      secours = minuterie(() => { if (etatVideo === 'lecture') terminerVideo(); }, reglages.dureeSecoursMs);
    }

    function revenirAuxVagues() {
      annulerSecours();
      try { video.pause(); video.currentTime = 0; } catch (e) { /* rien */ }
      etatVideo = 'avant';
      boutonsVisibles(!videoUtilisable());
    }

    function afficher() {
      racine.hidden = false;
      doc.documentElement.classList.add('eau-ouverte');
      revenirAuxVagues();
      couche.demarrer();
    }

    function entrerDansCap() {
      annulerSecours();
      try { video.pause(); } catch (e) { /* rien */ }
      couche.arreter();
      racine.hidden = true;
      doc.documentElement.classList.remove('eau-ouverte');
      const allerEau = doc.getElementById('aller-eau');
      if (allerEau) allerEau.blur();
    }

    // Gestes : sur la SURFACE seulement (les boutons sont à côté, jamais dedans).
    let pointeur = null;
    function position(e) {
      const r = racine.getBoundingClientRect();
      return { x: (e.clientX - r.left) / (r.width || 1), y: (e.clientY - r.top) / (r.height || 1), largeur: r.width || 1, hauteur: r.height || 1 };
    }
    surface.addEventListener('pointerdown', e => {
      if (pointeur) return;
      const p = position(e);
      pointeur = { id: e.pointerId, depart: p, t: maintenant() };
      couche.perturber(p.x, p.y, 6, 3);
      try { surface.setPointerCapture(e.pointerId); } catch (erreur) { /* rien */ }
    });
    surface.addEventListener('pointermove', e => {
      if (!pointeur || e.pointerId !== pointeur.id) return;
      const p = position(e);
      couche.perturber(p.x, p.y, 7, 3);
    });
    function fin(e) {
      if (!pointeur || e.pointerId !== pointeur.id) return;
      const debut = pointeur;
      pointeur = null;
      const p = position(e);
      const versLeHaut = debut.depart.y - p.y;
      // Glissement net de bas en haut (mêmes seuils que l'essai de Zencoder).
      if (debut.depart.y > 0.72 && p.y < 0.22 && versLeHaut > 0.45
        && Math.abs(p.x - debut.depart.x) * debut.depart.largeur < 0.4 * debut.depart.hauteur && maintenant() - debut.t < 2500) {
        demarrerVideo();
      }
    }
    surface.addEventListener('pointerup', fin);
    surface.addEventListener('pointercancel', e => { if (pointeur && e.pointerId === pointeur.id) pointeur = null; });
    parSelecteur('#bouton-entrer-cap').addEventListener('click', entrerDansCap);
    parSelecteur('#bouton-revenir-vagues').addEventListener('click', revenirAuxVagues);

    return {
      afficher, entrerDansCap, revenirAuxVagues, demarrerVideo,
      etat: () => ({ visible: !racine.hidden, video: etatVideo, panne: videoEnPanne, boutons: boutons.classList.contains('visible'), animation: couche.active() })
    };
  }

  // Au démarrage de Cap : montré une seule fois par ouverture ; le petit bouton « Eau » y ramène.
  function auDemarrage(doc, options = {}) {
    const racine = doc.getElementById('ecran-eau');
    if (!racine) return null;
    const ecran = monter(racine, options);
    const allerEau = doc.getElementById('aller-eau');
    if (allerEau) allerEau.addEventListener('click', () => ecran.afficher());
    const stockage = options.stockage !== undefined ? options.stockage : (typeof sessionStorage !== 'undefined' ? sessionStorage : null);
    let dejaVue = false;
    try { dejaVue = Boolean(stockage && stockage.getItem(CLE_VUE)); } catch (e) { dejaVue = false; }
    if (!dejaVue) {
      ecran.afficher();
      try { if (stockage) stockage.setItem(CLE_VUE, 'oui'); } catch (e) { /* rien : l'eau reste juste affichée */ }
    }
    return ecran;
  }

  return { REGLAGES, CLE_VUE, creerCouche, monter, auDemarrage };
})();

// Démarrage réel dans Cap (les tests créent leurs propres écrans isolés).
if (typeof document !== 'undefined' && document.getElementById('ecran-eau')) {
  ecranEau.instance = ecranEau.auDemarrage(document);
}
