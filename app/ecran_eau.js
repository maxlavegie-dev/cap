'use strict';

// Écran d'ouverture « eau » (06/11/2026, étape 1 de l'intégration du travail de Zencoder, accord de Max).
// Repris du dossier d'essai de Zencoder (Cap_eau_essai), copié en lecture seule : l'eau dessinée par
// le code et la vidéo du galet. NON repris : la fausse page d'accueil FICTIF (remplacée par le vrai
// Cap) et la « capture » du doigt par l'eau, qui détournait les touchers destinés aux boutons.
// Règles :
// - l'écran d'eau s'affiche au DÉMARRAGE de Cap seulement (une marque dans sessionStorage, rien de
//   personnel, évite de le remontrer quand la page se recharge pendant la même ouverture) ;
// - un glissement net de bas en haut fait MONTER Cap « de sous le sable » (lot c20, environ 1 s, animé
//   par le code, l'eau bouge encore) ; en mode 'video' il lance d'abord la vidéo du galet (sans son),
//   puis un second glissement fait entrer ; plus de bouton « Entrer dans Cap » (lot c21, choix de Max) ;
// - REPLI : vidéo absente, illisible ou bloquée → l'eau seule reste et le glissement fait entrer ;
//   Cap ne plante jamais ;
// - un seul réglage pour le fond : 'video', 'image' ou 'aucun' (REGLAGES ci-dessous) ;
// - la couche d'eau (creerCouche) ne capte JAMAIS un toucher (pointer-events: none) et peut être
//   posée ou retirée sur un autre écran sans toucher au reste (ambiance d'eau à venir, page par page) ;
// - l'animation s'arrête dès qu'on entre dans Cap (batterie).
const ecranEau = (() => {
  const REGLAGES = Object.freeze({
    fond: 'aucun', // 'video' | 'image' | 'aucun' (lot c20 : 'aucun' ; la vidéo du galet reste disponible)
    dureeSortieMs: 1000, // montée de Cap « de sous le sable »
    video: 'eau/galet_sortie.mp4',
    image: '', // chemin d'une image fixe, si fond = 'image'
    dureeSecoursMs: 7000 // si la vidéo ne finit pas d'elle-même, les boutons apparaissent quand même
  });
  const CLE_VUE = 'cap_eau_vue_v1';
  // Lot c21 : interrupteur « Eau » (préférence gardée sur ce téléphone : 'non' = arrêt).
  const CLE_ACTIVE = 'cap_eau_active_v1';
  // Couleurs de l'eau : tirées du fond de Cap (variable CSS --fond, réglage unique dans style.css) ;
  // à défaut, l'ancienne eau de l'essai de Zencoder.
  const COULEUR_PEU_PROFOND_SECOURS = [201, 227, 221];
  const COULEUR_PROFOND_SECOURS = [156, 182, 184];
  function couleursDuFond(doc) {
    try {
      const valeur = doc.defaultView.getComputedStyle(doc.documentElement).getPropertyValue('--fond').trim();
      const m = /^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(valeur);
      if (!m) return [COULEUR_PEU_PROFOND_SECOURS, COULEUR_PROFOND_SECOURS];
      const clair = [1, 2, 3].map(i => parseInt(m[i], 16));
      const fonce = clair.map((c, i) => Math.round(c * 0.8 + [120, 150, 165][i] * 0.2));
      return [clair, fonce];
    } catch (e) {
      return [COULEUR_PEU_PROFOND_SECOURS, COULEUR_PROFOND_SECOURS];
    }
  }
  // Lot c22 : UNE SEULE eau, la même partout (ouverture et accueil) : même finesse, même vivacité, même
  // force du doigt ; l'opacité est la même aussi (classe .couche-eau de style.css).
  const EAU = Object.freeze({
    cellules: 46000, // finesse (nombre de points calculés)
    amortissement: 0.985, // vivacité : plus proche de 1, les vagues durent plus longtemps
    forcePose: 6, // doigt posé
    forceGlisse: 7, // doigt qui glisse
    rayon: 3, // taille de l'onde du doigt
    delaiOndes: 1800 // ondes qui naissent seules (ms, en moyenne + hasard)
  });
  const AMORTISSEMENT = EAU.amortissement;
  const CELLULES_CIBLE = EAU.cellules;

  // ----- Couleurs des bandes du téléphone (lot c21) -----
  // En haut, l'eau est à son plus clair (= le fond) ; en bas, elle est un peu plus « profonde ». La bande
  // de la barre de navigation prend donc la couleur de l'eau en bas (fond + eau à son opacité), sinon
  // elle paraît blanche à côté. Sans eau : le fond partout.
  function hex(rgb) { return `#${rgb.map(c => Math.max(0, Math.min(255, Math.round(c))).toString(16).padStart(2, '0')).join('')}`; }
  function couleursBandes(doc, eauVisible) {
    const [clair, fonce] = couleursDuFond(doc);
    if (!eauVisible) return { haut: hex(clair), bas: hex(clair) };
    let opacite = 0.55;
    try {
      const toile = doc.getElementById('eau-accueil') || doc.getElementById('toile-eau');
      const lue = Number(doc.defaultView.getComputedStyle(toile).opacity);
      if (lue >= 0 && lue <= 1) opacite = lue;
    } catch (e) { /* valeur par défaut */ }
    return { haut: hex(clair), bas: hex(clair.map((c, i) => c * (1 - opacite) + fonce[i] * opacite)) };
  }
  function informerTelephone(doc, eauVisible) {
    try {
      const pont = doc.defaultView && doc.defaultView.CouleursAndroid;
      if (!pont || typeof pont.changer !== 'function') return;
      const c = couleursBandes(doc, eauVisible);
      pont.changer(c.haut, c.bas);
    } catch (e) { /* hors de l'application Android : rien */ }
  }

  // ----- Couche d'eau réutilisable (simulation de Zencoder) -----
  function creerCouche(toile, options = {}) {
    const fenetre = options.fenetre || (typeof window !== 'undefined' ? window : null);
    const raf = options.raf || (f => fenetre.requestAnimationFrame(f));
    const caf = options.caf || (id => fenetre.cancelAnimationFrame(id));
    const reduit = Boolean(options.animationsReduites
      ?? (fenetre && fenetre.matchMedia && fenetre.matchMedia('(prefers-reduced-motion: reduce)').matches));
    const ctx = toile.getContext('2d', { alpha: false });
    const [COULEUR_PEU_PROFOND, COULEUR_PROFOND] = options.couleurs || couleursDuFond(toile.ownerDocument);
    const basse = toile.ownerDocument.createElement('canvas');
    const ctxBasse = basse.getContext('2d');
    let largeur = 0, hauteur = 0, colonnes = 0, lignes = 0;
    let buf1 = null, buf2 = null, image = null;
    let identifiant = null;
    let prochaineOnde = 0;
    let touchers = 0;
    const cellulesCible = CELLULES_CIBLE; // lot c22 : plus de finesse réduite pour l'accueil

    function dimensionner() {
      largeur = toile.clientWidth || 360;
      hauteur = toile.clientHeight || 640;
      toile.width = largeur;
      toile.height = hauteur;
      const echelle = Math.sqrt((largeur * hauteur) / cellulesCible);
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
      touchers++;
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
      prochaineOnde = temps + (reduit ? 3200 : EAU.delaiOndes) + Math.random() * 1600;
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
    return { demarrer, arreter, perturber, dimensionner, active: () => identifiant !== null, touchers: () => touchers,
      reglages: () => ({ cellules: cellulesCible, amortissement: AMORTISSEMENT, delaiOndes: EAU.delaiOndes,
        opacite: (() => { try { return toile.ownerDocument.defaultView.getComputedStyle(toile).opacity; } catch (e) { return ''; } })() }) };
  }

  // ----- Eau derrière l'accueil (lot c20 ; lot c22 : EXACTEMENT la même eau que l'ouverture) -----
  // Ne capte JAMAIS un toucher : elle écoute les gestes sans les retenir (écouteurs passifs), donc une
  // tuile touchée fonctionne ET l'eau bouge ; elle suit aussi le doigt pendant un défilement (touchmove,
  // passif : le défilement garde son geste). Arrêtée quand Cap passe en arrière-plan (batterie), et
  // pendant l'écran d'ouverture (qui a sa propre eau).
  function eauAccueil(doc, options = {}) {
    const toile = doc.getElementById('eau-accueil');
    if (!toile) return { demarrer() {}, arreter() {}, etat: () => ({ active: false, touchers: 0 }) };
    const couche = creerCouche(toile, options);
    let voulue = false;
    const fenetre = doc.defaultView;
    function ignorer(e) {
      const cible = e.target && e.target.closest ? e.target : null;
      return !cible || cible.closest('#ecran-eau') || cible.closest('dialog[open]');
    }
    function position(e) {
      return [e.clientX / (fenetre.innerWidth || 1), e.clientY / (fenetre.innerHeight || 1)];
    }
    doc.addEventListener('pointerdown', e => {
      if (!couche.active() || ignorer(e)) return;
      couche.perturber(...position(e), EAU.forcePose, EAU.rayon);
    }, { passive: true, capture: true });
    doc.addEventListener('pointermove', e => {
      if (!couche.active() || !e.buttons || ignorer(e)) return;
      couche.perturber(...position(e), EAU.forceGlisse, EAU.rayon);
    }, { passive: true, capture: true });
    // Pendant un défilement, le téléphone garde le geste (plus d'événements « pointer ») : on suit le
    // doigt avec les événements « touch », en écoute passive seulement (jamais de preventDefault).
    doc.addEventListener('touchmove', e => {
      if (!couche.active() || ignorer(e)) return;
      for (const t of e.changedTouches || []) {
        couche.perturber(t.clientX / (fenetre.innerWidth || 1), t.clientY / (fenetre.innerHeight || 1), EAU.forceGlisse, EAU.rayon);
      }
    }, { passive: true, capture: true });
    doc.addEventListener('visibilitychange', () => {
      if (doc.hidden) couche.arreter();
      else if (voulue) couche.demarrer();
    });
    return {
      demarrer() { voulue = true; if (!doc.hidden) couche.demarrer(); },
      arreter() { voulue = false; couche.arreter(); },
      etat: () => ({ active: couche.active(), touchers: couche.touchers(), reglagesEau: couche.reglages() })
    };
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
    const boutonVagues = parSelecteur('#bouton-revenir-vagues');
    const reduit = Boolean(options.animationsReduites
      ?? (doc.defaultView && doc.defaultView.matchMedia && doc.defaultView.matchMedia('(prefers-reduced-motion: reduce)').matches));
    let sortie = null;
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
      // « Revenir aux vagues » n'a de sens qu'avec la vidéo.
      boutonVagues.hidden = reglages.fond !== 'video';
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
    // Repli : la vidéo ne peut pas servir → l'eau seule ; le glissement fait entrer.
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
      if (typeof options.avantAffichage === 'function') options.avantAffichage();
      if (sortie !== null) { annulerMinuterie(sortie); sortie = null; }
      racine.classList.remove('eau-sort');
      doc.documentElement.classList.remove('cap-monte');
      racine.hidden = false;
      doc.documentElement.classList.add('eau-ouverte');
      revenirAuxVagues();
      couche.demarrer();
    }

    // Fin de l'entrée : l'eau d'ouverture disparaît, son animation s'arrête.
    function finEntree() {
      sortie = null;
      couche.arreter();
      racine.hidden = true;
      racine.classList.remove('eau-sort');
      doc.documentElement.classList.remove('eau-ouverte', 'cap-monte');
      const allerEau = doc.getElementById('aller-eau');
      if (allerEau) allerEau.blur();
      if (typeof options.apresEntree === 'function') options.apresEntree();
    }
    // Entrée dans Cap : l'accueil monte « de sous le sable » pendant que l'eau, qui bouge encore,
    // s'efface (environ 1 s) ; aucun toucher n'est retenu par l'eau pendant ce temps.
    function entrerDansCap() {
      if (sortie !== null || racine.hidden) return;
      annulerSecours();
      try { video.pause(); } catch (e) { /* rien */ }
      const duree = reduit ? 0 : Math.max(0, Number(reglages.dureeSortieMs) || 0);
      if (!duree) { finEntree(); return; }
      racine.style.setProperty('--duree-sortie', `${duree}ms`);
      doc.documentElement.style.setProperty('--duree-sortie', `${duree}ms`);
      racine.classList.add('eau-sort');
      doc.documentElement.classList.add('cap-monte');
      sortie = minuterie(finEntree, duree);
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
      couche.perturber(p.x, p.y, EAU.forcePose, EAU.rayon);
      try { surface.setPointerCapture(e.pointerId); } catch (erreur) { /* rien */ }
    });
    surface.addEventListener('pointermove', e => {
      if (!pointeur || e.pointerId !== pointeur.id) return;
      const p = position(e);
      couche.perturber(p.x, p.y, EAU.forceGlisse, EAU.rayon);
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
        // Avec la vidéo : le galet d'abord. Sans vidéo (ou en panne) : Cap monte de sous le sable.
        if (videoUtilisable() && etatVideo === 'avant') demarrerVideo(); else entrerDansCap();
      }
    }
    surface.addEventListener('pointerup', fin);
    surface.addEventListener('pointercancel', e => { if (pointeur && e.pointerId === pointeur.id) pointeur = null; });
    parSelecteur('#bouton-revenir-vagues').addEventListener('click', revenirAuxVagues);

    return {
      afficher, entrerDansCap, revenirAuxVagues, demarrerVideo,
      etat: () => ({ visible: !racine.hidden, video: etatVideo, panne: videoEnPanne, boutons: boutons.classList.contains('visible'),
        animation: couche.active(), entree: sortie !== null, reglagesEau: couche.reglages() })
    };
  }

  // Au démarrage de Cap : montré une seule fois par ouverture ; le petit bouton « Eau » y ramène.
  // Interrupteur « Eau » sur arrêt : aucune eau nulle part (ni ouverture, ni accueil), aucune
  // animation ; Cap démarre directement sur l'accueil, au fond pâle.
  function auDemarrage(doc, options = {}) {
    const racine = doc.getElementById('ecran-eau');
    if (!racine) return null;
    const preferences = options.preferences || null;
    let active = true;
    try { active = !preferences || preferences.getItem(CLE_ACTIVE) !== 'non'; } catch (e) { active = true; }
    const fond = eauAccueil(doc, options);
    const ecran = monter(racine, { ...options, avantAffichage: () => fond.arreter(), apresEntree: () => { if (active) fond.demarrer(); } });
    ecran.fond = fond;
    const interrupteur = doc.getElementById('interrupteur-eau');
    const texteInterrupteur = doc.getElementById('etat-interrupteur-eau');
    function appliquerActive() {
      doc.documentElement.classList.toggle('sans-eau', !active);
      informerTelephone(doc, active);
      if (interrupteur) interrupteur.setAttribute('aria-checked', String(active));
      if (texteInterrupteur) texteInterrupteur.textContent = active ? 'en marche' : 'arrêtée';
    }
    ecran.eauActive = () => active;
    ecran.changerEau = valeur => {
      active = Boolean(valeur);
      try { if (preferences) preferences.setItem(CLE_ACTIVE, active ? 'oui' : 'non'); } catch (e) { /* rien : vaut pour cette ouverture */ }
      appliquerActive();
      if (active) fond.demarrer();
      else { fond.arreter(); if (ecran.etat().visible) ecran.entrerDansCap(); }
    };
    if (interrupteur) interrupteur.addEventListener('click', () => ecran.changerEau(!active));
    appliquerActive();
    const allerEau = doc.getElementById('aller-eau');
    if (allerEau) allerEau.addEventListener('click', () => { if (active) ecran.afficher(); });
    if (!active) return ecran;
    const stockage = options.stockage !== undefined ? options.stockage : (typeof sessionStorage !== 'undefined' ? sessionStorage : null);
    let dejaVue = false;
    try { dejaVue = Boolean(stockage && stockage.getItem(CLE_VUE)); } catch (e) { dejaVue = false; }
    if (!dejaVue) {
      ecran.afficher();
      try { if (stockage) stockage.setItem(CLE_VUE, 'oui'); } catch (e) { /* rien : l'eau reste juste affichée */ }
    } else {
      fond.demarrer();
    }
    return ecran;
  }

  return { REGLAGES, EAU, CLE_VUE, CLE_ACTIVE, creerCouche, eauAccueil, monter, auDemarrage, couleursBandes };
})();

// Démarrage réel dans Cap. La page des tests automatiques (window.CAP_TESTS) crée ses propres écrans
// isolés, pour ne pas faire tourner d'eau pendant tous les autres tests.
if (typeof document !== 'undefined' && document.getElementById('ecran-eau') && !(typeof window !== 'undefined' && window.CAP_TESTS)) {
  let preferences = null;
  try { preferences = window.localStorage; } catch (e) { preferences = null; }
  ecranEau.instance = ecranEau.auDemarrage(document, { preferences });
}
