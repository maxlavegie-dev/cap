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
  // Eau v2 de Zencoder (Cap_eau_essai_v2_2026_11_07/eau.js, lu sans rien y toucher ; reprise le 07/11/2026,
  // accord de Max) : mêmes réglages et mêmes formules, adaptées dans la couche d'eau de Cap :
  // houle de fond lente, tache de lumière qui se déplace, fin trait clair sur le haut des vagues (« liseré
  // de crête »), pour que l'eau SOMBRE bouge visiblement. Utilisée avec les couleurs sombres seulement.
  const EAU_V2 = Object.freeze({
    houle: Object.freeze({ intensite: 0.15, vitesse: 0.00022, frequence: 1.6 }),
    reflet: Object.freeze({ intensite: 0.5, vitesse: 0.00018, taille: 2.2 }),
    lisereCrete: Object.freeze({ intensite: 0.35, couleur: Object.freeze([214, 230, 226]) })
  });
  // 08/11/2026 (accord de Max) : en mode CLAIR sur les écrans sur l'eau, doigt qui glisse plus doux (4, comme la
  // visionneuse et le lecteur de Zencoder) ; mode sombre et écran des tâches : EAU.forceGlisse inchangé.
  const FORCE_GLISSE_CLAIRE = 4;
  function forceGlisse(doc) {
    try {
      return doc.documentElement.classList.contains('theme-cap-clair') && !doc.body.classList.contains('vue-complete')
        ? FORCE_GLISSE_CLAIRE : EAU.forceGlisse;
    } catch (e) { return EAU.forceGlisse; }
  }
  const AMORTISSEMENT = EAU.amortissement;
  const CELLULES_CIBLE = EAU.cellules;
  const TRACE_MAX = 64; // 08/11/2026 : touches d'eau au plus par mouvement du doigt (traînée continue)

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
    // Étape A (07/11/2026) : couleurs changeables (mode clair / sombre des écrans sur l'eau).
    let [COULEUR_PEU_PROFOND, COULEUR_PROFOND] = options.couleurs || couleursDuFond(toile.ownerDocument);
    // Effets de l'eau v2 (null = l'eau d'avant, inchangée).
    let effets = options.effets || null;
    let houleX = null, houleY = null, refletX = null, refletY = null;
    const basse = toile.ownerDocument.createElement('canvas');
    const ctxBasse = basse.getContext('2d');
    let largeur = 0, hauteur = 0, colonnes = 0, lignes = 0;
    let buf1 = null, buf2 = null, image = null;
    let identifiant = null;
    let prochaineOnde = 0;
    let touchers = 0;
    // lot c22 : plus de finesse réduite pour l'accueil ; étape A : une petite eau (alerte) peut en demander moins.
    const cellulesCible = Number(options.cellules) > 0 ? Number(options.cellules) : CELLULES_CIBLE;

    function dimensionner() {
      largeur = toile.clientWidth || 360;
      hauteur = toile.clientHeight || 640;
      toile.width = largeur;
      toile.height = hauteur;
      const echelle = Math.sqrt((largeur * hauteur) / cellulesCible);
      const nouvellesColonnes = Math.max(20, Math.round(largeur / echelle));
      const nouvellesLignes = Math.max(20, Math.round(hauteur / echelle));
      // 08/11/2026 (accord de Max, vagues sans remise à zéro) : même taille = on garde les vagues en cours
      // (reprise après une pause, retour du scan, Cap revenu au premier plan).
      if (buf1 && nouvellesColonnes === colonnes && nouvellesLignes === lignes) return;
      // 09/11/2026 (défaut 1 vu par Max : fenêtres « + » et crayon) : quand la taille change (le clavier du téléphone qui
      // s'ouvre ou se ferme), les vagues en cours sont REPORTÉES sur la nouvelle grille au lieu d'être remises à plat
      // (avant : eau soudain unie). Avant : buf1 = new Float32Array(...) seulement.
      const ancien = buf1 ? { b1: buf1, b2: buf2, c: colonnes, l: lignes } : null;
      colonnes = nouvellesColonnes;
      lignes = nouvellesLignes;
      buf1 = new Float32Array(colonnes * lignes);
      buf2 = new Float32Array(colonnes * lignes);
      if (ancien) {
        for (let y = 0; y < lignes; y++) {
          const ya = Math.min(ancien.l - 1, Math.floor(y * ancien.l / lignes));
          for (let x = 0; x < colonnes; x++) {
            const xa = Math.min(ancien.c - 1, Math.floor(x * ancien.c / colonnes));
            buf1[y * colonnes + x] = ancien.b1[ya * ancien.c + xa];
            buf2[y * colonnes + x] = ancien.b2[ya * ancien.c + xa];
          }
        }
      }
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

    // 08/11/2026 (accord de Max) : traînée continue entre deux positions du doigt (plus de pointillés
    // quand le geste est rapide) : une touche d'eau tous les « rayon » carreaux, 64 au plus par mouvement.
    function tracer(x0, y0, x1, y1, force, rayon) {
      if (!buf1) return;
      const distance = Math.hypot((x1 - x0) * colonnes, (y1 - y0) * lignes);
      const n = Math.min(TRACE_MAX, Math.max(1, Math.ceil(distance / Math.max(1, rayon))));
      for (let k = 1; k <= n; k++) perturber(x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n, force, rayon);
    }

    // 08/11/2026 (accord de Max) : l'état des vagues passe d'une eau à l'autre (eau seule → accueil, et retour) :
    // plus de coupure nette. Tailles différentes : chaque carreau prend le plus proche.
    function exporterEtat() {
      return buf1 ? { colonnes, lignes, buf1: buf1.slice(), buf2: buf2.slice() } : null;
    }
    function importerEtat(etat) {
      if (!etat || !etat.buf1 || !etat.buf2) return false;
      dimensionner();
      if (etat.colonnes === colonnes && etat.lignes === lignes) { buf1.set(etat.buf1); buf2.set(etat.buf2); return true; }
      for (let y = 0; y < lignes; y++) {
        const sy = Math.min(etat.lignes - 1, Math.floor(y * etat.lignes / lignes));
        for (let x = 0; x < colonnes; x++) {
          const s = sy * etat.colonnes + Math.min(etat.colonnes - 1, Math.floor(x * etat.colonnes / colonnes));
          buf1[y * colonnes + x] = etat.buf1[s];
          buf2[y * colonnes + x] = etat.buf2[s];
        }
      }
      return true;
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

    // Eau v2 : houle et tache de lumière se calculent par colonne et par ligne (même résultat que les
    // formules de Zencoder, beaucoup moins de calculs : sinus et exponentielle se séparent en x et en y).
    function preparerEffets(temps) {
      if (!houleX || houleX.length !== colonnes) { houleX = new Float32Array(colonnes); refletX = new Float32Array(colonnes); }
      if (!houleY || houleY.length !== lignes) { houleY = new Float32Array(lignes); refletY = new Float32Array(lignes); }
      const h = effets.houle, r = effets.reflet;
      const phaseH = temps * h.vitesse, phaseR = temps * r.vitesse;
      const cx = 0.5 + Math.sin(phaseR) * 0.35, cy = 0.5 + Math.cos(phaseR * 0.8) * 0.35;
      for (let x = 0; x < colonnes; x++) {
        const f = x / colonnes;
        houleX[x] = Math.sin(f * 2 * Math.PI * h.frequence + phaseH) * 4 * h.intensite;
        const dx = (f - cx) * r.taille;
        refletX[x] = Math.exp(-dx * dx * 3);
      }
      for (let y = 0; y < lignes; y++) {
        const f = y / lignes;
        houleY[y] = Math.sin(f * 2 * Math.PI * h.frequence * 0.7 - phaseH * 1.3) * 4 * h.intensite;
        const dy = (f - cy) * r.taille;
        refletY[y] = Math.exp(-dy * dy * 3) * 10 * r.intensite;
      }
    }

    function dessinerV2(temps) {
      preparerEffets(temps);
      const pixels = image.data;
      const l = effets.lisereCrete;
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
          const c = Math.max(-22, Math.min(22, (gx + gy) * 9)) + houleX[x] + houleY[y] + refletX[x] * refletY[y];
          let r = r0 + c, g = g0 + c, b = b0 + c * 0.9;
          // Liseré de crête : éclaircit seulement le haut des vagues (au-dessus d'un petit seuil).
          const dessus = buf1[i] - 2.2;
          if (l.intensite > 0 && dessus > 0) {
            const q = Math.min(dessus / 3, 1) * l.intensite;
            r += (l.couleur[0] - r) * q; g += (l.couleur[1] - g) * q; b += (l.couleur[2] - b) * q;
          }
          const p = i * 4;
          pixels[p] = Math.max(0, Math.min(255, r));
          pixels[p + 1] = Math.max(0, Math.min(255, g));
          pixels[p + 2] = Math.max(0, Math.min(255, b));
        }
      }
      ctxBasse.putImageData(image, 0, 0);
      ctx.imageSmoothingEnabled = true;
      ctx.drawImage(basse, 0, 0, colonnes, lignes, 0, 0, largeur, hauteur);
    }

    function dessiner(temps) {
      if (effets) { dessinerV2(temps); return; }
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
    // couleurs : [peu profond, profond] (trois nombres chacun) ; sans argument, celles du fond de Cap.
    // effetsV2 : EAU_V2 (eau v2 de Zencoder) ou rien (l'eau d'avant).
    function changerCouleurs(couleurs, effetsV2) {
      [COULEUR_PEU_PROFOND, COULEUR_PROFOND] = couleurs || couleursDuFond(toile.ownerDocument);
      effets = effetsV2 || null;
    }
    return { demarrer, arreter, perturber, tracer, exporterEtat, importerEtat, dimensionner, changerCouleurs, couleurs: () => [COULEUR_PEU_PROFOND, COULEUR_PROFOND],
      effets: () => effets, pixels: () => (image ? image.data : null), avancer: temps => { etape(); dessiner(temps); },
      active: () => identifiant !== null, touchers: () => touchers,
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
      // 08/11/2026 (demande de Max) : l'eau reste jouable derrière les écrans de choix sur l'eau (fenetre-choix) ;
      // ancienne règle : toute fenêtre ouverte était ignorée (cible.closest('dialog[open]')).
      // 09/11/2026 (défaut 1) : + les deux fenêtres de saisie posées sur l'eau (« + » et crayon) : l'eau suit le doigt dessous.
      // Avant : cible.closest('dialog[open]:not(.fenetre-choix)').
      return !cible || cible.closest('#ecran-eau') || cible.closest('dialog[open]:not(.fenetre-choix):not(#clavier):not(#ajout-tache)');
    }
    function position(e) {
      return [e.clientX / (fenetre.innerWidth || 1), e.clientY / (fenetre.innerHeight || 1)];
    }
    // 08/11/2026 : dernière position de chaque doigt, pour la traînée continue.
    const derniers = new Map();
    function glisser(cle, x, y) {
      const avant = derniers.get(cle);
      if (avant) couche.tracer(avant[0], avant[1], x, y, forceGlisse(doc), EAU.rayon);
      else couche.perturber(x, y, forceGlisse(doc), EAU.rayon);
      derniers.set(cle, [x, y]);
    }
    doc.addEventListener('pointerdown', e => {
      if (!couche.active() || ignorer(e)) return;
      couche.perturber(...position(e), EAU.forcePose, EAU.rayon);
      derniers.set(`p${e.pointerId}`, position(e));
    }, { passive: true, capture: true });
    doc.addEventListener('pointermove', e => {
      if (!couche.active() || !e.buttons || ignorer(e)) return;
      glisser(`p${e.pointerId}`, ...position(e));
    }, { passive: true, capture: true });
    for (const type of ['pointerup', 'pointercancel']) doc.addEventListener(type, e => derniers.delete(`p${e.pointerId}`), { passive: true, capture: true });
    for (const type of ['touchend', 'touchcancel']) {
      doc.addEventListener(type, e => { for (const t of e.changedTouches || []) derniers.delete(`t${t.identifier}`); }, { passive: true, capture: true });
    }
    // Pendant un défilement, le téléphone garde le geste (plus d'événements « pointer ») : on suit le
    // doigt avec les événements « touch », en écoute passive seulement (jamais de preventDefault).
    doc.addEventListener('touchmove', e => {
      if (!couche.active() || ignorer(e)) return;
      for (const t of e.changedTouches || []) {
        glisser(`t${t.identifier}`, t.clientX / (fenetre.innerWidth || 1), t.clientY / (fenetre.innerHeight || 1));
      }
    }, { passive: true, capture: true });
    doc.addEventListener('visibilitychange', () => {
      if (doc.hidden) couche.arreter();
      else if (voulue) couche.demarrer();
    });
    return {
      demarrer() { voulue = true; if (!doc.hidden) couche.demarrer(); },
      arreter() { voulue = false; couche.arreter(); },
      changerCouleurs: (couleurs, effetsV2) => couche.changerCouleurs(couleurs, effetsV2),
      couleurs: () => couche.couleurs(),
      effets: () => couche.effets(),
      exporterEtat: () => couche.exporterEtat(),
      importerEtat: etat => couche.importerEtat(etat),
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

    // 08/11/2026 (accord de Max) : descente douce, symétrique de la montée. { descente: true } = retour depuis
    // l'accueil (geste de haut en bas) : la date et les boutons s'enfoncent, flous, en fondu, pendant que l'eau seule
    // revient en fondu (même durée que la montée) ; l'eau de l'accueil s'arrête à la FIN (avantAffichage).
    // Animations réduites, durée 0 ou premier affichage : d'un coup, comme avant.
    let descente = null;
    function finDescente() {
      if (descente !== null) annulerMinuterie(descente);
      descente = null;
      racine.classList.remove('eau-revient');
      doc.documentElement.classList.remove('cap-descend');
    }
    function afficher({ descente: douce = false } = {}) {
      if (descente !== null) return; // déjà en train de descendre
      const duree = douce && !reduit && racine.hidden ? Math.max(0, Number(reglages.dureeSortieMs) || 0) : 0;
      if (!duree && typeof options.avantAffichage === 'function') options.avantAffichage();
      if (sortie !== null) { annulerMinuterie(sortie); sortie = null; }
      racine.classList.remove('eau-sort');
      doc.documentElement.classList.remove('cap-monte');
      if (duree) {
        racine.style.setProperty('--duree-sortie', `${duree}ms`);
        doc.documentElement.style.setProperty('--duree-sortie', `${duree}ms`);
        racine.classList.add('eau-revient');
        doc.documentElement.classList.add('cap-descend');
        descente = minuterie(() => {
          descente = null;
          finDescente();
          if (typeof options.avantAffichage === 'function') options.avantAffichage();
        }, duree);
      }
      racine.hidden = false;
      doc.documentElement.classList.add('eau-ouverte');
      revenirAuxVagues();
      // 08/11/2026 : retour à l'eau seule (bouton « Eau ») : elle reprend les vagues de l'accueil.
      if (typeof options.etatAvantAffichage === 'function') couche.importerEtat(options.etatAvantAffichage());
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
      finDescente(); // 08/11/2026 : geste vers le haut pendant la descente = elle s'arrête, Cap remonte
      annulerSecours();
      try { video.pause(); } catch (e) { /* rien */ }
      // 08/11/2026 (accord de Max) : l'eau de l'accueil reçoit les vagues du geste et démarre DÈS MAINTENANT,
      // sous l'eau seule qui s'efface : les traces continuent puis s'apaisent, sans remise à zéro.
      if (typeof options.avantSortie === 'function') options.avantSortie(couche.exporterEtat());
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
      pointeur = { id: e.pointerId, depart: p, dernier: p, t: maintenant() };
      couche.perturber(p.x, p.y, EAU.forcePose, EAU.rayon);
      try { surface.setPointerCapture(e.pointerId); } catch (erreur) { /* rien */ }
    });
    surface.addEventListener('pointermove', e => {
      if (!pointeur || e.pointerId !== pointeur.id) return;
      const p = position(e);
      couche.tracer(pointeur.dernier.x, pointeur.dernier.y, p.x, p.y, forceGlisse(doc), EAU.rayon); // 08/11/2026 : traînée continue
      pointeur.dernier = p;
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
      afficher, entrerDansCap, revenirAuxVagues, demarrerVideo, changerCouleurs: (couleurs, effetsV2) => couche.changerCouleurs(couleurs, effetsV2),
      etatVagues: () => couche.exporterEtat(), // 08/11/2026 : lecture seule (tests)
      etat: () => ({ visible: !racine.hidden, video: etatVideo, panne: videoEnPanne, boutons: boutons.classList.contains('visible'),
        animation: couche.active(), entree: sortie !== null, descente: descente !== null, reglagesEau: couche.reglages() })
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
    // 08/11/2026 (accord de Max) : les vagues passent d'une eau à l'autre (avantSortie, etatAvantAffichage).
    const ecran = monter(racine, { ...options, avantAffichage: () => fond.arreter(), apresEntree: () => { if (active) fond.demarrer(); },
      avantSortie: etat => { if (active) { fond.importerEtat(etat); fond.demarrer(); } },
      etatAvantAffichage: () => fond.exporterEtat() });
    ecran.fond = fond;
    // Étape A : mode clair / sombre : la même couleur pour l'eau d'ouverture et l'eau de l'accueil.
    const changerCouleursOuverture = ecran.changerCouleurs;
    ecran.changerCouleurs = (couleurs, effetsV2) => { changerCouleursOuverture(couleurs, effetsV2); fond.changerCouleurs(couleurs, effetsV2); };
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
    if (allerEau) allerEau.addEventListener('click', () => { if (active) ecran.afficher({ descente: true }); }); // 08/11/2026 : descente douce
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

  return { REGLAGES, EAU, EAU_V2, FORCE_GLISSE_CLAIRE, forceGlisse, CLE_VUE, CLE_ACTIVE, creerCouche, eauAccueil, monter, auDemarrage, couleursBandes };
})();

// Démarrage réel dans Cap. La page des tests automatiques (window.CAP_TESTS) crée ses propres écrans
// isolés, pour ne pas faire tourner d'eau pendant tous les autres tests.
if (typeof document !== 'undefined' && document.getElementById('ecran-eau') && !(typeof window !== 'undefined' && window.CAP_TESTS)) {
  let preferences = null;
  try { preferences = window.localStorage; } catch (e) { preferences = null; }
  ecranEau.instance = ecranEau.auDemarrage(document, { preferences });
}
