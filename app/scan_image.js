'use strict';

// Traitement d'image du scanner : qualité, bords du document, redressement, verso vide.
// Sans DOM : travaille sur des objets { data (RGBA), width, height }, donc testable seul.
const scanImage = (() => {
  const cote_analyse = 320;
  const cote_nettete = 800;
  const cote_sortie_max = 1800;

  // Seuils de qualité (réglables ici, séparés de la logique).
  const REGLAGES = Object.freeze({
    nettete_min: 60,
    luminance_min: 70,
    aire_document_min: 0.2,
    aire_document_max: 0.97,
    remplissage_quad_min: 0.7,
    remplissage_quad_max: 1.15,
    cadre_occupe_min: 0.12,
    fond_blanc_min: 0.55,
    couleur_max: 0.1,
    encre_page_vide_max: 0.004,
    contraste_page_vide_max: 22
  });

  function creer(largeur, hauteur) {
    return { data: new Uint8ClampedArray(largeur * hauteur * 4), width: largeur, height: hauteur };
  }

  function gris(image) {
    const { data, width, height } = image;
    const sortie = new Float32Array(width * height);
    for (let i = 0, p = 0; i < sortie.length; i++, p += 4) {
      sortie[i] = 0.299 * data[p] + 0.587 * data[p + 1] + 0.114 * data[p + 2];
    }
    return sortie;
  }

  function reduire(image, coteMax) {
    const plusGrand = Math.max(image.width, image.height);
    if (plusGrand <= coteMax) return image;
    const echelle = coteMax / plusGrand;
    const largeur = Math.max(1, Math.round(image.width * echelle));
    const hauteur = Math.max(1, Math.round(image.height * echelle));
    const sortie = creer(largeur, hauteur);
    for (let y = 0; y < hauteur; y++) {
      const y0 = Math.floor(y / echelle);
      const y1 = Math.max(y0 + 1, Math.min(image.height, Math.floor((y + 1) / echelle)));
      for (let x = 0; x < largeur; x++) {
        const x0 = Math.floor(x / echelle);
        const x1 = Math.max(x0 + 1, Math.min(image.width, Math.floor((x + 1) / echelle)));
        let r = 0, v = 0, b = 0, n = 0;
        for (let yy = y0; yy < y1; yy++) {
          for (let xx = x0; xx < x1; xx++) {
            const p = (yy * image.width + xx) * 4;
            r += image.data[p]; v += image.data[p + 1]; b += image.data[p + 2]; n++;
          }
        }
        const q = (y * largeur + x) * 4;
        sortie.data[q] = r / n; sortie.data[q + 1] = v / n; sortie.data[q + 2] = b / n; sortie.data[q + 3] = 255;
      }
    }
    return sortie;
  }

  function seuilOtsu(valeurs) {
    const histo = new Float64Array(256);
    for (let i = 0; i < valeurs.length; i++) histo[Math.max(0, Math.min(255, Math.round(valeurs[i])))]++;
    const total = valeurs.length;
    let somme = 0;
    for (let t = 0; t < 256; t++) somme += t * histo[t];
    let sommeFond = 0, poidsFond = 0, meilleur = 0, seuil = 127;
    for (let t = 0; t < 256; t++) {
      poidsFond += histo[t];
      if (!poidsFond) continue;
      const poidsPremier = total - poidsFond;
      if (!poidsPremier) break;
      sommeFond += t * histo[t];
      const moyFond = sommeFond / poidsFond;
      const moyPremier = (somme - sommeFond) / poidsPremier;
      const variance = poidsFond * poidsPremier * (moyFond - moyPremier) ** 2;
      if (variance > meilleur) { meilleur = variance; seuil = t; }
    }
    return seuil;
  }

  function percentile(valeurs, fraction) {
    const histo = new Uint32Array(256);
    for (let i = 0; i < valeurs.length; i++) histo[Math.max(0, Math.min(255, Math.round(valeurs[i])))]++;
    const cible = fraction * valeurs.length;
    let cumul = 0;
    for (let t = 0; t < 256; t++) {
      cumul += histo[t];
      if (cumul >= cible) return t;
    }
    return 255;
  }

  function netteteGris(g, largeur, hauteur) {
    let somme = 0, sommeCarres = 0, n = 0;
    const x0 = Math.max(1, Math.floor(largeur * 0.15)), x1 = Math.min(largeur - 1, Math.ceil(largeur * 0.85));
    const y0 = Math.max(1, Math.floor(hauteur * 0.15)), y1 = Math.min(hauteur - 1, Math.ceil(hauteur * 0.85));
    for (let y = y0; y < y1; y++) {
      for (let x = x0; x < x1; x++) {
        const i = y * largeur + x;
        const laplacien = 4 * g[i] - g[i - 1] - g[i + 1] - g[i - largeur] - g[i + largeur];
        somme += laplacien; sommeCarres += laplacien * laplacien; n++;
      }
    }
    if (!n) return 0;
    const moyenne = somme / n;
    return sommeCarres / n - moyenne * moyenne;
  }

  function composantePrincipale(masque, largeur, hauteur) {
    const etiquette = new Int32Array(largeur * hauteur);
    const pile = new Int32Array(largeur * hauteur);
    let meilleurId = 0, meilleureTaille = 0, id = 0;
    for (let depart = 0; depart < masque.length; depart++) {
      if (!masque[depart] || etiquette[depart]) continue;
      id++;
      let sommet = 0, taille = 0;
      pile[sommet++] = depart;
      etiquette[depart] = id;
      while (sommet) {
        const i = pile[--sommet];
        taille++;
        const x = i % largeur, y = (i - x) / largeur;
        if (x > 0 && masque[i - 1] && !etiquette[i - 1]) { etiquette[i - 1] = id; pile[sommet++] = i - 1; }
        if (x < largeur - 1 && masque[i + 1] && !etiquette[i + 1]) { etiquette[i + 1] = id; pile[sommet++] = i + 1; }
        if (y > 0 && masque[i - largeur] && !etiquette[i - largeur]) { etiquette[i - largeur] = id; pile[sommet++] = i - largeur; }
        if (y < hauteur - 1 && masque[i + largeur] && !etiquette[i + largeur]) { etiquette[i + largeur] = id; pile[sommet++] = i + largeur; }
      }
      if (taille > meilleureTaille) { meilleureTaille = taille; meilleurId = id; }
    }
    return { etiquette, id: meilleurId, taille: meilleureTaille };
  }

  function aireQuadrilatere(p) {
    let somme = 0;
    for (let i = 0; i < 4; i++) {
      const a = p[i], b = p[(i + 1) % 4];
      somme += a.x * b.y - b.x * a.y;
    }
    return Math.abs(somme) / 2;
  }

  // Érosion ou dilatation 3x3 (le dehors du cadre compte comme « plein » pour l'érosion : un bord de page n'est pas rongé).
  function filtre3(masque, l, h, erosion) {
    const sortie = new Uint8Array(l * h);
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < l; x++) {
        let valeur = erosion ? 1 : 0;
        for (let dy = -1; dy <= 1; dy++) {
          for (let dx = -1; dx <= 1; dx++) {
            const xx = x + dx, yy = y + dy;
            const dehors = xx < 0 || yy < 0 || xx >= l || yy >= h;
            const plein = dehors ? erosion : masque[yy * l + xx] === 1;
            if (erosion && !plein) valeur = 0;
            if (!erosion && plein) valeur = 1;
          }
        }
        sortie[y * l + x] = valeur;
      }
    }
    return sortie;
  }

  // Fermeture (comble les trous du texte) puis ouverture : efface les fines fuites (grain du bois, ombres) qui collent à la page.
  function ouvrirMasque(masque, l, h, tours) {
    let courant = masque;
    for (let t = 0; t < tours; t++) courant = filtre3(courant, l, h, false);
    for (let t = 0; t < tours; t++) courant = filtre3(courant, l, h, true);
    for (let t = 0; t < tours; t++) courant = filtre3(courant, l, h, true);
    for (let t = 0; t < tours; t++) courant = filtre3(courant, l, h, false);
    return courant;
  }

  function mediane(valeurs) {
    const copie = Float32Array.from(valeurs).sort();
    return copie[Math.floor(copie.length / 2)] || 0;
  }

  // Masque « différent du fond » : le fond est la couleur médiane du pourtour de la photo.
  function masqueCouleur(petit, l, h) {
    const rouge = [], vert = [], bleu = [];
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < l; x++) {
        if (x >= 3 && y >= 3 && x < l - 3 && y < h - 3) { x = l - 3 - 1; continue; }
        const p = (y * l + x) * 4;
        rouge.push(petit.data[p]); vert.push(petit.data[p + 1]); bleu.push(petit.data[p + 2]);
      }
    }
    const fr = mediane(rouge), fv = mediane(vert), fb = mediane(bleu);
    const distance = new Float32Array(l * h);
    for (let i = 0, p = 0; i < distance.length; i++, p += 4) {
      distance[i] = Math.hypot(petit.data[p] - fr, petit.data[p + 1] - fv, petit.data[p + 2] - fb) * 255 / 441;
    }
    const seuil = seuilOtsu(distance);
    const masque = new Uint8Array(l * h);
    for (let i = 0; i < masque.length; i++) if (distance[i] > seuil) masque[i] = 1;
    return masque;
  }

  // Plus longue suite de pixels de la page le long d'un côté du cadre, en part de ce côté : si la page dépasse du cadre, elle est longue.
  function partDeCadreOccupee(etiquette, id, l, h) {
    const cotes = [
      [l, i => etiquette[i]], [l, i => etiquette[(h - 1) * l + i]],
      [h, i => etiquette[i * l]], [h, i => etiquette[i * l + l - 1]]
    ];
    let meilleure = 0;
    for (const [longueur, lire] of cotes) {
      let suite = 0, max = 0;
      for (let i = 0; i < longueur; i++) {
        if (lire(i) === id) { suite++; if (suite > max) max = suite; } else suite = 0;
      }
      meilleure = Math.max(meilleure, max / longueur);
    }
    return meilleure;
  }

  // Évalue un masque « page » : retourne le document trouvé avec une pénalité (plus petite = plus sûr), ou null.
  function evaluerMasque(masque, g, image, l, h) {
    let clairs = 0;
    for (let i = 0; i < masque.length; i++) clairs += masque[i];
    const part = clairs / masque.length;
    if (part < REGLAGES.aire_document_min * 0.8 || part > 0.995) return null;
    const ouvert = ouvrirMasque(masque, l, h, 2);
    const { etiquette, id, taille } = composantePrincipale(ouvert, l, h);
    if (!id) return null;
    const aire = taille / (l * h);
    if (aire < REGLAGES.aire_document_min || aire > REGLAGES.aire_document_max) return null;
    let hg = null, bd = null, hd = null, bg = null;
    let scoreHg = Infinity, scoreBd = -Infinity, scoreHd = -Infinity, scoreBg = Infinity;
    let sommeDedans = 0, sommeDehors = 0;
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < l; x++) {
        if (etiquette[y * l + x] !== id) { sommeDehors += g[y * l + x]; continue; }
        sommeDedans += g[y * l + x];
        const somme = x + y, difference = x - y;
        if (somme < scoreHg) { scoreHg = somme; hg = { x, y }; }
        if (somme > scoreBd) { scoreBd = somme; bd = { x, y }; }
        if (difference > scoreHd) { scoreHd = difference; hd = { x, y }; }
        if (difference < scoreBg) { scoreBg = difference; bg = { x, y }; }
      }
    }
    const quad = [hg, hd, bd, bg];
    const aireQuad = aireQuadrilatere(quad);
    if (!aireQuad) return null;
    const remplissage = taille / aireQuad;
    if (remplissage < REGLAGES.remplissage_quad_min || remplissage > REGLAGES.remplissage_quad_max) return null;
    const coupe = partDeCadreOccupee(etiquette, id, l, h) >= REGLAGES.cadre_occupe_min;
    const dehors = l * h - taille;
    const plusSombre = dehors > 0 && sommeDedans / taille < sommeDehors / dehors - 10;
    const penalite = Math.abs(1 - remplissage) + (plusSombre ? 0.15 : 0) + (coupe ? 0.03 : 0);
    const echelleX = image.width / l, echelleY = image.height / h;
    const coins = quad.map(p => ({ x: (p.x + 0.5) * echelleX, y: (p.y + 0.5) * echelleY }));
    return { coins, coupe, aire, penalite };
  }

  // Cherche les quatre coins du document, avec deux méthodes (page plus claire que le fond, page différente de la couleur du fond)
  // et garde la plus cohérente. « coupé » = la page dépasse réellement du cadre sur une partie notable d'un côté.
  // Retourne { coins, coupe, aire } ou null si les bords ne sont pas trouvés.
  function trouverDocument(image) {
    const petit = reduire(image, cote_analyse);
    const { width: l, height: h } = petit;
    const g = gris(petit);
    const seuil = seuilOtsu(g);
    const masqueClair = new Uint8Array(l * h);
    for (let i = 0; i < masqueClair.length; i++) if (g[i] > seuil) masqueClair[i] = 1;
    const candidats = [
      evaluerMasque(masqueClair, g, image, l, h),
      evaluerMasque(masqueCouleur(petit, l, h), g, image, l, h)
    ].filter(Boolean).sort((a, b) => a.penalite - b.penalite);
    return candidats.length ? candidats[0] : null;
  }

  function homographie(c) {
    const [p0, p1, p2, p3] = c;
    const dx1 = p1.x - p2.x, dx2 = p3.x - p2.x, dx3 = p0.x - p1.x + p2.x - p3.x;
    const dy1 = p1.y - p2.y, dy2 = p3.y - p2.y, dy3 = p0.y - p1.y + p2.y - p3.y;
    let g = 0, h = 0;
    if (Math.abs(dx3) > 1e-9 || Math.abs(dy3) > 1e-9) {
      const det = dx1 * dy2 - dy1 * dx2;
      g = (dx3 * dy2 - dy3 * dx2) / det;
      h = (dx1 * dy3 - dy1 * dx3) / det;
    }
    return {
      a: p1.x - p0.x + g * p1.x, b: p3.x - p0.x + h * p3.x, c: p0.x,
      d: p1.y - p0.y + g * p1.y, e: p3.y - p0.y + h * p3.y, f: p0.y, g, h
    };
  }

  function echantillon(image, x, y, sortie, position) {
    const { data, width, height } = image;
    const cx = Math.max(0, Math.min(width - 1, x)), cy = Math.max(0, Math.min(height - 1, y));
    const x0 = Math.floor(cx), y0 = Math.floor(cy);
    const x1 = Math.min(width - 1, x0 + 1), y1 = Math.min(height - 1, y0 + 1);
    const fx = cx - x0, fy = cy - y0;
    for (let k = 0; k < 3; k++) {
      const haut = data[(y0 * width + x0) * 4 + k] * (1 - fx) + data[(y0 * width + x1) * 4 + k] * fx;
      const bas = data[(y1 * width + x0) * 4 + k] * (1 - fx) + data[(y1 * width + x1) * 4 + k] * fx;
      sortie[position + k] = haut * (1 - fy) + bas * fy;
    }
    sortie[position + 3] = 255;
  }

  // Redresse le document : déforme le quadrilatère en rectangle.
  function redresser(image, coins) {
    const [hg, hd, bd, bg] = coins;
    const distance = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
    let largeur = (distance(hg, hd) + distance(bg, bd)) / 2;
    let hauteur = (distance(hg, bg) + distance(hd, bd)) / 2;
    const echelle = Math.min(1, cote_sortie_max / Math.max(largeur, hauteur));
    largeur = Math.max(1, Math.round(largeur * echelle));
    hauteur = Math.max(1, Math.round(hauteur * echelle));
    const m = homographie(coins);
    const sortie = creer(largeur, hauteur);
    for (let y = 0; y < hauteur; y++) {
      const v = (y + 0.5) / hauteur;
      for (let x = 0; x < largeur; x++) {
        const u = (x + 0.5) / largeur;
        const w = m.g * u + m.h * v + 1;
        echantillon(image, (m.a * u + m.b * v + m.c) / w, (m.d * u + m.e * v + m.f) / w, sortie.data, (y * largeur + x) * 4);
      }
    }
    return sortie;
  }

  function valeurHisto(histo, total, fraction) {
    const cible = fraction * total;
    let cumul = 0;
    for (let t = 0; t < histo.length; t++) {
      cumul += histo[t];
      if (cumul >= cible) return t;
    }
    return histo.length - 1;
  }

  // Estime l'éclairage de la page : pour chaque petit bloc et chaque couleur, la valeur du fond (papier), lissée.
  // Retourne une fonction (x, y, sortie) qui écrit dans sortie la couleur du fond en ce point.
  function estimerFond(image) {
    const { width: w, height: h, data } = image;
    const bloc = Math.max(8, Math.round(Math.max(w, h) / 40));
    const gx = Math.ceil(w / bloc), gy = Math.ceil(h / bloc);
    const histos = new Uint16Array(gx * gy * 768);
    const nombres = new Uint32Array(gx * gy);
    for (let y = 0; y < h; y++) {
      const ligne = Math.floor(y / bloc) * gx;
      for (let x = 0; x < w; x++) {
        const b = ligne + Math.floor(x / bloc);
        const base = b * 768, p = (y * w + x) * 4;
        histos[base + data[p]]++; histos[base + 256 + data[p + 1]]++; histos[base + 512 + data[p + 2]]++;
        nombres[b]++;
      }
    }
    let fond = new Float32Array(gx * gy * 3);
    for (let b = 0; b < gx * gy; b++) {
      for (let k = 0; k < 3; k++) {
        fond[b * 3 + k] = valeurHisto(histos.subarray(b * 768 + k * 256, b * 768 + k * 256 + 256), nombres[b], 0.9);
      }
    }
    const globaux = [0, 1, 2].map(k => {
      const valeurs = [];
      for (let b = 0; b < gx * gy; b++) valeurs.push(fond[b * 3 + k]);
      valeurs.sort((a, c) => a - c);
      return valeurs[Math.floor(valeurs.length * 0.9)] || 1;
    });
    for (let b = 0; b < gx * gy; b++) for (let k = 0; k < 3; k++) fond[b * 3 + k] = Math.max(fond[b * 3 + k], globaux[k] * 0.5, 1);
    for (const maximum of [true, false]) {
      const suite = new Float32Array(fond.length);
      for (let by = 0; by < gy; by++) {
        for (let bx = 0; bx < gx; bx++) {
          for (let k = 0; k < 3; k++) {
            let valeur = maximum ? 0 : 0, n = 0;
            for (let dy = -1; dy <= 1; dy++) {
              for (let dx = -1; dx <= 1; dx++) {
                const xx = Math.max(0, Math.min(gx - 1, bx + dx)), yy = Math.max(0, Math.min(gy - 1, by + dy));
                const v = fond[(yy * gx + xx) * 3 + k];
                valeur = maximum ? Math.max(valeur, v) : valeur + v;
                n++;
              }
            }
            suite[(by * gx + bx) * 3 + k] = maximum ? valeur : valeur / n;
          }
        }
      }
      fond = suite;
    }
    const colonnes = new Array(w), lignes = new Array(h);
    const position = (i, taille, grille) => {
      const f = Math.max(0, Math.min(grille - 1, (i + 0.5) / taille * grille - 0.5));
      const i0 = Math.floor(f);
      return [i0, Math.min(grille - 1, i0 + 1), f - i0];
    };
    for (let x = 0; x < w; x++) colonnes[x] = position(x, bloc * gx, gx).map((v, i) => (i === 2 ? v : v));
    for (let y = 0; y < h; y++) lignes[y] = position(y, bloc * gy, gy);
    return (x, y, sortie) => {
      const [x0, x1, fx] = colonnes[x], [y0, y1, fy] = lignes[y];
      for (let k = 0; k < 3; k++) {
        const haut = fond[(y0 * gx + x0) * 3 + k] * (1 - fx) + fond[(y0 * gx + x1) * 3 + k] * fx;
        const bas = fond[(y1 * gx + x0) * 3 + k] * (1 - fx) + fond[(y1 * gx + x1) * 3 + k] * fx;
        sortie[k] = haut * (1 - fy) + bas * fy;
      }
    };
  }

  // Améliore la page automatiquement, sans réglage :
  // - page écrite (papier clair, peu de couleur) : éclairage égalisé, fond blanchi, noir du texte renforcé ;
  // - page en couleur ou photo : traitement doux (éclairage corrigé à moitié, niveaux étirés, couleurs gardées).
  function ameliorer(image) {
    const { width: w, height: h, data } = image;
    const fondEn = estimerFond(image);
    const f = [0, 0, 0];
    const histoNormal = new Uint32Array(256), histoGain = new Uint32Array(256);
    let echantillons = 0, fonds = 0, colores = 0;
    const gains = new Float32Array(w * h);
    let fondMax = 0;
    for (let y = 0; y < h; y += 4) for (let x = 0; x < w; x += 4) {
      fondEn(x, y, f);
      fondMax = Math.max(fondMax, 0.299 * f[0] + 0.587 * f[1] + 0.114 * f[2]);
    }
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const i = y * w + x;
        if (y % 3 || x % 3) continue;
        fondEn(x, y, f);
        const p = i * 4;
        const r = data[p], v = data[p + 1], b = data[p + 2];
        const lumFond = 0.299 * f[0] + 0.587 * f[1] + 0.114 * f[2];
        const n = Math.min(1.2, (0.299 * r / f[0] + 0.587 * v / f[1] + 0.114 * b / f[2]));
        const gain = Math.max(0.8, Math.min(1.6, Math.sqrt(fondMax / lumFond)));
        const lum = (0.299 * r + 0.587 * v + 0.114 * b) * gain;
        histoNormal[Math.min(255, Math.round(n * 255))]++;
        histoGain[Math.min(255, Math.round(lum))]++;
        echantillons++;
        if (n > 0.85) fonds++;
        const maxi = Math.max(r, v, b), mini = Math.min(r, v, b);
        if (maxi > 60 && (maxi - mini) / maxi > 0.35) colores++;
      }
    }
    const partFond = fonds / echantillons, partCouleur = colores / echantillons;
    const texte = partFond >= REGLAGES.fond_blanc_min && partCouleur < REGLAGES.couleur_max;
    const sortie = creer(w, h);
    if (texte) {
      const noir = Math.min(0.45, valeurHisto(histoNormal, echantillons, 0.01) / 255 + 0.12);
      const blanc = 0.88;
      for (let y = 0; y < h; y++) {
        for (let x = 0; x < w; x++) {
          const p = (y * w + x) * 4;
          fondEn(x, y, f);
          for (let k = 0; k < 3; k++) {
            const t = Math.max(0, Math.min(1, (data[p + k] / f[k] - noir) / (blanc - noir)));
            sortie.data[p + k] = 255 * t * t * (3 - 2 * t);
          }
          sortie.data[p + 3] = 255;
        }
      }
      return { page: sortie, mode: 'texte' };
    }
    const bas = valeurHisto(histoGain, echantillons, 0.01) * 0.6;
    const haut = Math.max(bas + 40, valeurHisto(histoGain, echantillons, 0.98));
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const p = (y * w + x) * 4;
        fondEn(x, y, f);
        const lumFond = 0.299 * f[0] + 0.587 * f[1] + 0.114 * f[2];
        const gain = Math.max(0.8, Math.min(1.6, Math.sqrt(fondMax / lumFond)));
        for (let k = 0; k < 3; k++) {
          sortie.data[p + k] = Math.max(0, Math.min(255, (data[p + k] * gain - bas) * 255 / (haut - bas)));
        }
        sortie.data[p + 3] = 255;
      }
    }
    return { page: sortie, mode: 'doux' };
  }

  // Page blanche (verso vide) : presque aucune encre et contraste très faible.
  function analyserVide(image) {
    const petit = reduire(image, cote_analyse);
    const g = gris(petit);
    const { width: l, height: h } = petit;
    const x0 = Math.floor(l * 0.06), x1 = Math.ceil(l * 0.94), y0 = Math.floor(h * 0.06), y1 = Math.ceil(h * 0.94);
    const centre = [];
    for (let y = y0; y < y1; y++) for (let x = x0; x < x1; x++) centre.push(g[y * l + x]);
    const valeurs = Float32Array.from(centre);
    const fond = percentile(valeurs, 0.5);
    let encre = 0;
    for (let i = 0; i < valeurs.length; i++) if (valeurs[i] < fond - 45) encre++;
    const part = valeurs.length ? encre / valeurs.length : 0;
    const contraste = percentile(valeurs, 0.99) - percentile(valeurs, 0.01);
    return { vide: part <= REGLAGES.encre_page_vide_max && contraste <= REGLAGES.contraste_page_vide_max * 2, encre: part, contraste };
  }

  // Qualité d'une page : flou, trop sombre, coupée. Chaque alerte est expliquée à Max en français.
  function analyserQualite(image, document = null) {
    const reduite = reduire(image, cote_nettete);
    const g = gris(reduite);
    const luminance = g.reduce((somme, v) => somme + v, 0) / (g.length || 1);
    const sombre = luminance < REGLAGES.luminance_min;
    const nettete = netteteGris(gris(reduite), reduite.width, reduite.height);
    const vide = analyserVide(image).vide;
    const flou = !vide && nettete < REGLAGES.nettete_min;
    const coupe = Boolean(document && document.coupe);
    const alertes = [];
    if (flou) alertes.push('flou');
    if (sombre) alertes.push('sombre');
    if (coupe) alertes.push('coupe');
    return { flou, sombre, coupe, nettete, luminance, alertes };
  }

  const messages = Object.freeze({
    flou: 'La photo est floue.',
    sombre: 'La photo est trop sombre.',
    coupe: 'Le document semble coupé : un bord touche le cadre.'
  });

  function phrase(alertes) {
    return alertes.map(a => messages[a]).join(' ');
  }

  // Traite une photo complète : bords, redressement, éclaircissement, qualité.
  // Si les bords ne sont pas trouvés (ou si le document est coupé), garde la photo entière sans la déformer.
  function traiter(image) {
    const document = trouverDocument(image);
    let page = image;
    let redressee = false;
    if (document && !document.coupe) {
      page = redresser(image, document.coins);
      redressee = true;
    }
    const qualite = analyserQualite(image, document);
    const amelioree = ameliorer(page);
    page = amelioree.page;
    const vide = analyserVide(page);
    return { page, mode: amelioree.mode, redressee, bords_trouves: Boolean(document), qualite, vide: vide.vide, coins: document ? document.coins : null };
  }

  return { REGLAGES, creer, reduire, gris, trouverDocument, redresser, ameliorer, analyserVide, analyserQualite, phrase, traiter, homographie };
})();
