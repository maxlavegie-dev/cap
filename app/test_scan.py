# Tests du scanner (lot 3.1) : tout est mécanique et fictif. Lance : python app\test_scan.py
import html
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

APP = pathlib.Path(__file__).resolve().parent
EDGE = pathlib.Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
SOURCES = ["reglages_google.js", "reglages_ia.js", "limite_ia.js", "cle_ia.js", "scan_image.js", "scan_pdf.js", "scan_documents.js", "scan_file.js", "scan_depot.js", "scan_lecture.js", "scan_nommage.js", "scan_ecran.js"]

TESTS_JS = r"""
(async () => {
  const resultats = [];
  const attendre = (condition, message) => { if (!condition) throw new Error(message); };
  const egal = (reel, attendu, message) => {
    const r = JSON.stringify(reel), a = JSON.stringify(attendu);
    if (r !== a) throw new Error(`${message} : attendu ${a}, reçu ${r}`);
  };
  async function test(nom, fonction) {
    try { await fonction(); resultats.push({ nom, ok: true }); }
    catch (erreur) { resultats.push({ nom, ok: false, erreur: String(erreur && erreur.stack ? erreur.stack : erreur) }); }
    window.progres = resultats.map(r => (r.ok ? 'ok ' : 'ECHEC ') + r.nom);
  }

  // ---------- Images synthétiques (fictives) ----------
  function dansQuad(q, x, y) {
    let signe = 0;
    for (let i = 0; i < 4; i++) {
      const a = q[i], b = q[(i + 1) % 4];
      const c = (b[0] - a[0]) * (y - a[1]) - (b[1] - a[1]) * (x - a[0]);
      if (c !== 0) { if (signe && Math.sign(c) !== signe) return false; signe = Math.sign(c); }
    }
    return true;
  }
  function rapetisser(q, f) {
    const cx = q.reduce((s, p) => s + p[0], 0) / 4, cy = q.reduce((s, p) => s + p[1], 0) / 4;
    return q.map(p => [cx + (p[0] - cx) * f, cy + (p[1] - cy) * f]);
  }
  function scene(opts = {}) {
    const l = opts.l || 640, h = opts.h || 480;
    const quad = opts.quad || [[110, 60], [520, 80], [500, 420], [130, 400]];
    const image = scanImage.creer(l, h);
    const texte = rapetisser(quad, 0.85);
    const papier = opts.papier === undefined ? 235 : opts.papier;
    const fond = opts.fond === undefined ? 50 : opts.fond;
    for (let y = 0; y < h; y++) for (let x = 0; x < l; x++) {
      let v = fond;
      if (dansQuad(quad, x, y)) {
        v = papier;
        if (!opts.vide && y % 6 < 2 && x % 16 < 10 && dansQuad(texte, x, y)) v = 40;
      }
      const p = (y * l + x) * 4;
      image.data[p] = image.data[p + 1] = image.data[p + 2] = v; image.data[p + 3] = 255;
    }
    return image;
  }
  function flouter(image, rayon) {
    const { width: l, height: h } = image;
    let source = image;
    for (let passe = 0; passe < 2; passe++) {
      const sortie = scanImage.creer(l, h);
      for (let y = 0; y < h; y++) for (let x = 0; x < l; x++) {
        let s = 0, n = 0;
        for (let d = -rayon; d <= rayon; d++) {
          const xx = passe === 0 ? x + d : x, yy = passe === 0 ? y : y + d;
          if (xx < 0 || yy < 0 || xx >= l || yy >= h) continue;
          s += source.data[(yy * l + xx) * 4]; n++;
        }
        const p = (y * l + x) * 4;
        sortie.data[p] = sortie.data[p + 1] = sortie.data[p + 2] = s / n; sortie.data[p + 3] = 255;
      }
      source = sortie;
    }
    return source;
  }
  function assombrir(image, f) {
    const s = scanImage.creer(image.width, image.height);
    for (let p = 0; p < s.data.length; p += 4) { s.data[p] = s.data[p + 1] = s.data[p + 2] = image.data[p] * f; s.data[p + 3] = 255; }
    return s;
  }
  async function jpegFictif(l, h, teinte) {
    const c = document.createElement('canvas'); c.width = l; c.height = h;
    const g = c.getContext('2d'); g.fillStyle = teinte || '#888'; g.fillRect(0, 0, l, h);
    g.fillStyle = '#000'; g.fillRect(2, 2, l / 3, h / 3);
    const blob = await new Promise(r => c.toBlob(r, 'image/jpeg', 0.8));
    return new Uint8Array(await blob.arrayBuffer());
  }
  const pause = ms => new Promise(r => setTimeout(r, ms));

  // ---------- Image ----------
  await test('bords : les 4 coins du papier sont trouvés (± 8 px)', () => {
    const d = scanImage.trouverDocument(scene());
    attendre(d, 'document non trouvé');
    const attendus = [[110, 60], [520, 80], [500, 420], [130, 400]];
    d.coins.forEach((c, i) => attendre(Math.hypot(c.x - attendus[i][0], c.y - attendus[i][1]) < 8, `coin ${i} : ${c.x},${c.y}`));
    attendre(!d.coupe, 'faussement coupé');
  });

  await test('redressement : sortie rectangulaire, coins blancs, texte présent', () => {
    const r = scanImage.traiter(scene());
    attendre(r.bords_trouves && r.redressee, 'pas redressée');
    const { width: l, height: h, data } = r.page;
    attendre(l / h > 1.05 && l / h < 1.4, `proportions ${l}x${h}`);
    for (const [x, y] of [[3, 3], [l - 4, 3], [3, h - 4], [l - 4, h - 4]]) attendre(data[(y * l + x) * 4] > 200, `coin sombre en ${x},${y}`);
    let sombres = 0;
    for (let p = 0; p < data.length; p += 4) if (data[p] < 100) sombres++;
    attendre(sombres > l * h * 0.02, 'le texte a disparu');
  });

  await test('bords introuvables : la photo entière est gardée sans déformation', () => {
    const uniforme = scanImage.creer(300, 200);
    for (let p = 0; p < uniforme.data.length; p += 4) { uniforme.data[p] = uniforme.data[p + 1] = uniforme.data[p + 2] = 120; uniforme.data[p + 3] = 255; }
    const r = scanImage.traiter(uniforme);
    attendre(!r.bords_trouves && !r.redressee, 'bords inventés');
    egal([r.page.width, r.page.height], [300, 200], 'dimensions');
  });

  await test('coupé : un document qui touche le cadre est signalé et gardé entier', () => {
    const image = scene({ quad: [[-40, 60], [520, 80], [500, 420], [-30, 400]] });
    const r = scanImage.traiter(image);
    attendre(r.qualite.coupe && r.qualite.alertes.includes('coupe'), 'coupé non détecté');
    attendre(!r.redressee, 'redressé alors que coupé');
    egal([r.page.width, r.page.height], [640, 480], 'dimensions');
    attendre(scanImage.phrase(r.qualite.alertes).includes('coupé'), 'phrase');
  });

  // Scène en couleur : fond « bois » avec grain, papier, ombre douce, éclairage inégal, encre (tout fictif).
  function sceneCouleur(opts = {}) {
    const l = 640, h = 480;
    const quad = opts.quad || [[110, 60], [520, 80], [500, 420], [130, 400]];
    const texte = rapetisser(quad, 0.85);
    const image = scanImage.creer(l, h);
    let graine = 12345;
    const hasard = () => { graine = (graine * 1103515245 + 12345) & 0x7fffffff; return graine / 0x7fffffff; };
    const papier = opts.papier || [232, 230, 222];
    const base = opts.base || [170, 120, 75];
    for (let y = 0; y < h; y++) for (let x = 0; x < l; x++) {
      const p = (y * l + x) * 4;
      let c;
      if (dansQuad(quad, x, y)) {
        const lumiere = opts.degrade ? 1 - opts.degrade * (x / l) : 1;
        c = papier.map(v => v * lumiere);
        if (opts.encre !== false && y % 6 < 2 && x % 16 < 10 && dansQuad(texte, x, y)) c = [35, 35, 45];
        if (opts.couleur && dansQuad(texte, x, y) && ((x >> 4) + (y >> 4)) % 2) c = opts.couleur;
      } else {
        const grain = ((x >> 1) % 7 === 0 ? 40 : 0) + (hasard() - 0.5) * 70;
        c = base.map(v => Math.max(0, Math.min(255, v + grain)));
      }
      image.data[p] = c[0]; image.data[p + 1] = c[1]; image.data[p + 2] = c[2]; image.data[p + 3] = 255;
    }
    return image;
  }
  const attendusBois = [[110, 60], [520, 80], [500, 420], [130, 400]];

  await test('bois : papier sur une table en bois, coins trouvés et pas de fausse alerte « coupé »', () => {
    const d = scanImage.trouverDocument(sceneCouleur());
    attendre(d, 'document non trouvé sur le bois');
    d.coins.forEach((c, i) => attendre(Math.hypot(c.x - attendusBois[i][0], c.y - attendusBois[i][1]) < 14, `coin ${i} : ${c.x},${c.y}`));
    attendre(!d.coupe, 'faussement coupé sur le bois');
  });

  await test('bois : une page vraiment coupée reste signalée', () => {
    const d = scanImage.trouverDocument(sceneCouleur({ quad: [[-40, 60], [520, 80], [500, 420], [-30, 400]] }));
    attendre(d && d.coupe, 'coupure non détectée sur le bois');
  });

  await test('lisibilité : éclairage inégal, le fond devient blanc et uniforme, l’encre reste noire', () => {
    const r = scanImage.traiter(sceneCouleur({ degrade: 0.55 }));
    attendre(r.mode === 'texte', `mode ${r.mode}`);
    const { width: l, height: h, data } = r.page;
    const medianes = [];
    for (const [qx, qy] of [[0, 0], [1, 0], [0, 1], [1, 1]]) {
      const v = [];
      for (let y = Math.floor(h * (0.05 + qy * 0.5)); y < h * (0.45 + qy * 0.5); y += 2) for (let x = Math.floor(l * (0.05 + qx * 0.5)); x < l * (0.45 + qx * 0.5); x += 2) v.push(data[(y * l + x) * 4 + 1]);
      v.sort((a, b) => a - b);
      medianes.push(v[Math.floor(v.length / 2)]);
    }
    attendre(Math.max(...medianes) - Math.min(...medianes) < 25, `fond inégal : ${medianes}`);
    attendre(Math.min(...medianes) > 235, `fond pas assez blanc : ${medianes}`);
    let noirs = 0;
    for (let p = 0; p < data.length; p += 4) if (data[p] < 60) noirs++;
    attendre(noirs > l * h * 0.02, 'l’encre a disparu');
  });

  await test('lisibilité : une page sombre (papier gris) devient claire', () => {
    const r = scanImage.traiter(sceneCouleur({ papier: [120, 118, 112], base: [60, 40, 25] }));
    attendre(r.bords_trouves, 'bords non trouvés');
    const { width: l, height: h, data } = r.page;
    const v = [];
    for (let y = 2; y < h; y += 3) for (let x = 2; x < l; x += 3) v.push(data[(y * l + x) * 4]);
    v.sort((a, b) => a - b);
    attendre(v[Math.floor(v.length * 0.7)] > 235, `fond ${v[Math.floor(v.length * 0.7)]}`);
  });

  await test('lisibilité : page très colorée = traitement doux, couleurs gardées', () => {
    const r = scanImage.traiter(sceneCouleur({ couleur: [200, 40, 40], encre: false }));
    attendre(r.mode === 'doux', `mode ${r.mode}`);
    let rouges = 0;
    const { data } = r.page;
    for (let p = 0; p < data.length; p += 4) if (data[p] > 150 && data[p + 1] < 90 && data[p + 2] < 90) rouges++;
    attendre(rouges > 2000, `rouge perdu : ${rouges}`);
  });

  await test('netteté : page nette sans alerte, page floue avec alerte', () => {
    const nette = scanImage.analyserQualite(scene());
    const floue = scanImage.analyserQualite(flouter(scene(), 6));
    attendre(!nette.flou, `nette jugée floue (${nette.nettete})`);
    attendre(floue.flou, `floue non détectée (nette ${nette.nettete}, floue ${floue.nettete})`);
    attendre(nette.nettete > floue.nettete * 3, `écart trop faible ${nette.nettete} / ${floue.nettete}`);
  });

  await test('sombre : une photo assombrie est signalée, pas la normale', () => {
    attendre(!scanImage.analyserQualite(scene()).sombre, 'normale jugée sombre');
    const q = scanImage.analyserQualite(assombrir(scene(), 0.3));
    attendre(q.sombre && q.alertes.includes('sombre'), 'sombre non détecté');
  });

  await test('verso vide : papier blanc = vide, page de texte = non vide', () => {
    attendre(scanImage.traiter(scene({ vide: true })).vide, 'blanc non reconnu');
    attendre(!scanImage.traiter(scene()).vide, 'texte pris pour du vide');
  });

  // ---------- PDF ----------
  await test('PDF : en-tête, nombre de pages, table xref exacte, fin de fichier', async () => {
    const pages = [];
    for (let i = 0; i < 3; i++) pages.push({ jpeg: await jpegFictif(200, 300 + i * 10), largeur: 200, hauteur: 300 + i * 10 });
    const pdf = scanPdf.assembler(pages);
    const texte = new TextDecoder('latin1').decode(pdf);
    attendre(texte.startsWith('%PDF-1.4'), 'en-tête');
    attendre(texte.includes('/Count 3'), 'nombre de pages');
    attendre((texte.match(/\/Type \/Page /g) || []).length === 3, 'objets page');
    attendre(texte.trimEnd().endsWith('%%EOF'), 'fin');
    const debut = Number(texte.match(/startxref\n(\d+)/)[1]);
    attendre(texte.slice(debut, debut + 4) === 'xref', 'startxref ne pointe pas sur xref');
    const lignes = texte.slice(debut).split('\n').slice(2);
    for (let n = 1; n < 12; n++) {
      const pos = Number(lignes[n].slice(0, 10));
      attendre(texte.slice(pos, pos + String(n).length + 6) === `${n} 0 obj`, `objet ${n} mal placé`);
    }
    for (let i = 0; i < 3; i++) {
      const longueur = Number(texte.match(new RegExp(`${4 + i * 3} 0 obj[\\s\\S]*?/Length (\\d+)`))[1]);
      attendre(longueur === pages[i].jpeg.length, 'longueur image');
    }
  });

  await test('PDF : refuse une page qui n’est pas un JPEG et une liste vide', () => {
    let m1 = '', m2 = '';
    try { scanPdf.assembler([{ jpeg: new Uint8Array([1, 2, 3, 4]), largeur: 10, hauteur: 10 }]); } catch (e) { m1 = e.message; }
    try { scanPdf.assembler([]); } catch (e) { m2 = e.message; }
    attendre(m1.includes('JPEG') && m2.includes('Aucune page'), `${m1} / ${m2}`);
  });

  // ---------- Règles ----------
  const jpegMini = () => new Uint8Array([0xFF, 0xD8, 0xFF, 0xD9]);
  await test('session : ajout, ordre, déplacement, suppression, remplacement', () => {
    const s = scanDocuments.creerSession();
    const a = s.ajouter({ jpeg: jpegMini() }).id, b = s.ajouter({ jpeg: jpegMini() }).id, c = s.ajouter({ jpeg: jpegMini() }).id;
    egal(s.ordre(), [a, b, c], 'ordre initial');
    s.deplacer(c, -1); egal(s.ordre(), [a, c, b], 'monter');
    s.deplacer(a, 1); egal(s.ordre(), [c, a, b], 'descendre');
    egal(s.deplacer(c, -1), false, 'déjà en premier');
    s.supprimer(a); egal(s.ordre(), [c, b], 'suppression');
    s.remplacer(b, { jpeg: jpegMini(), largeur: 7 });
    egal(s.ordre(), [c, b], 'remplacement garde la place');
    egal(s.pages()[1].largeur, 7, 'contenu remplacé');
    let erreur = '';
    try { s.supprimer(999); } catch (e) { erreur = e.message; }
    attendre(erreur.includes('n’existe plus'), 'page inconnue');
    s.vider(); egal(s.nombre(), 0, 'vidée');
  });

  await test('session : verso vide ignoré, mais jamais la première page', () => {
    const s = scanDocuments.creerSession();
    attendre(s.ajouter({ jpeg: jpegMini(), vide: true }).ajoutee, 'première page blanche refusée');
    const r = s.ajouter({ jpeg: jpegMini(), vide: true });
    attendre(!r.ajoutee && r.raison === 'vide', 'verso vide gardé');
    egal([s.nombre(), s.ignorees()], [1, 1], 'compteurs');
    let erreur = '';
    try { s.ajouter({ jpeg: [1, 2] }); } catch (e) { erreur = e.message; }
    attendre(erreur.includes('invalide'), 'page invalide acceptée');
  });

  await test('nom de fichier : daté, sans accent, suffixe en cas de collision', () => {
    const d = new Date(2026, 10, 2, 9, 5, 7);
    egal(scanDocuments.nomFichier(d), 'SCAN-2026-11-02-09h05m07.pdf', 'nom');
    egal(scanDocuments.nomFichier(d, ['SCAN-2026-11-02-09h05m07.pdf']), 'SCAN-2026-11-02-09h05m07-2.pdf', 'collision');
    egal(scanDocuments.nomFichier(d, ['scan-2026-11-02-09h05m07.PDF', 'SCAN-2026-11-02-09h05m07-2.pdf']), 'SCAN-2026-11-02-09h05m07-3.pdf', 'collisions multiples');
  });

  await test('messages : 1 page et plusieurs pages', () => {
    egal(scanDocuments.messageEnregistre(1), '1 page enregistrée, en cours de classement.', 'une');
    egal(scanDocuments.messageEnregistre(4), '4 pages enregistrées, en cours de classement.', 'plusieurs');
  });

  await test('rafale : compte rendu, expiration après inactivité, arrêt', () => {
    const r = scanDocuments.creerRafale(1000);
    attendre(!r.expiree(5000), 'expirée sans démarrage');
    r.demarrer(0);
    r.noter(true, false); r.noter(true, true); r.noter(true, true);
    r.noter(false, true);
    egal(r.compteRendu(), '3 scannés, 3 déposés, 0 en attente.', 'compte rendu');
    const r2 = scanDocuments.creerRafale(1000); r2.demarrer(0);
    for (let i = 0; i < 20; i++) r2.noter(true, i < 17);
    egal(r2.compteRendu(), '20 scannés, 17 déposés, 3 en attente.', 'exemple du document');
    r2.toucher(900);
    attendre(!r2.expiree(1500), 'expirée trop tôt après toucher');
    attendre(r2.expiree(1900), 'pas expirée');
    r2.arreter(); attendre(!r2.active() && !r2.expiree(99999), 'arrêt');
  });

  // ---------- File hors connexion (IndexedDB) ----------
  const nomBase = 'test_scans_' + Date.now();
  await test('file : un scan est gardé, survit à la réouverture, et ne perd rien', async () => {
    const f = scanFile.creer(nomBase);
    const pdf = new Blob([new Uint8Array([37, 80, 68, 70, 1, 2, 3])], { type: 'application/pdf' });
    const id = await f.ajouter({ nom: 'SCAN-test.pdf', pdf, pages: 2 });
    await f.fermer();
    const g = scanFile.creer(nomBase);
    const attente = await g.enAttente();
    egal(attente.map(x => x.nom), ['SCAN-test.pdf'], 'après réouverture');
    egal(attente[0].pdf.size, 7, 'contenu gardé');
    await g.marquerErreur(id, 'réseau coupé');
    attendre((await g.enAttente())[0].pdf.size === 7 && (await g.enAttente())[0].erreur === 'réseau coupé', 'une erreur ne doit pas libérer le PDF');
    await g.marquerDepose(id, 'drive-1');
    egal((await g.enAttente()).length, 0, 'plus en attente');
    const tout = await g.lister();
    egal([tout.length, tout[0].etat, tout[0].drive_id, tout[0].pdf], [1, 'depose', 'drive-1', null], 'fiche gardée');
    let erreur = '';
    try { await g.ajouter({ nom: 'x.pdf', pdf: new Blob([]), pages: 1 }); } catch (e) { erreur = e.message; }
    attendre(erreur.includes('vide'), 'scan vide accepté');
    await g.fermer();
  });

  // ---------- Dépôt (réseau simulé) ----------
  const sourceDepot = await (await fetch('/src/scan_depot.js')).text();
  function monterDepot({ connecte = true, enLigne = true, reponses }) {
    const requetes = [];
    const memoire = {};
    const faux = {
      connecte: () => connecte,
      appeler: async (url, options = {}) => {
        const u = new URL(url);
        const r = { methode: options.method || 'GET', chemin: decodeURIComponent(u.pathname), q: u.searchParams.get('q') || '', corps: options.body, url };
        requetes.push(r);
        const donnees = await reponses(r);
        if (donnees instanceof Error) throw donnees;
        return { json: async () => donnees };
      }
    };
    const stockageFaux = { getItem: c => (c in memoire ? memoire[c] : null), setItem: (c, v) => { memoire[c] = String(v); } };
    const depot = new Function('googleConnexion', 'REGLAGES_GOOGLE', 'localStorage', 'navigator', sourceDepot + '\nreturn scanDepot;')(
      faux, REGLAGES_GOOGLE, stockageFaux, { onLine: enLigne });
    return { depot, requetes, memoire };
  }
  const reponsesDrive = (etat = {}) => async r => {
    if (r.methode === 'GET' && r.chemin === '/drive/v3/files' && r.q.includes('folder')) {
      if (r.q.includes('ARCHIVES_PERSONNELLES')) return { files: etat.archives ? [{ id: 'arch' }] : [] };
      return { files: etat.aclasser ? [{ id: 'acl' }] : [] };
    }
    if (r.methode === 'GET' && r.chemin.startsWith('/drive/v3/files/')) return { id: 'x', trashed: false };
    if (r.methode === 'GET' && r.chemin === '/drive/v3/files') return { files: etat.existant ? [{ id: 'deja' }] : [] };
    if (r.methode === 'POST' && r.chemin === '/drive/v3/files') {
      const meta = JSON.parse(r.corps);
      (etat.crees ||= []).push(meta);
      return { id: meta.name === REGLAGES_GOOGLE.dossier_archives ? 'arch' : 'acl' };
    }
    if (r.methode === 'POST' && r.chemin === '/upload/drive/v3/files') {
      if (etat.echecEnvoi) return new Error('Réseau coupé.');
      (etat.envoyes ||= []).push(r);
      return { id: 'fichier-' + etat.envoyes.length };
    }
    return new Error('Requête inattendue : ' + r.methode + ' ' + r.chemin);
  };
  async function filePrete(noms) {
    const f = scanFile.creer('test_depot_' + Math.random().toString(36).slice(2));
    for (const nom of noms) await f.ajouter({ nom, pdf: new Blob([new Uint8Array([37, 80, 68, 70, 9])], { type: 'application/pdf' }), pages: 1 });
    return f;
  }

  await test('dépôt : crée les faux dossiers, envoie les scans, jamais de suppression', async () => {
    attendre(REGLAGES_GOOGLE.dossier_archives.includes('FICTIF'), 'le dossier racine doit être marqué FICTIF');
    egal(REGLAGES_GOOGLE.dossier_a_classer, '00_A_CLASSER', 'nom du dossier');
    const etat = {};
    const m = monterDepot({ reponses: reponsesDrive(etat) });
    const f = await filePrete(['SCAN-a.pdf', 'SCAN-b.pdf']);
    const res = await m.depot.deposerEnAttente(f);
    egal([res.deposes, res.restants, res.erreur], [2, 0, ''], 'résultat');
    egal(etat.crees.map(c => c.name), [REGLAGES_GOOGLE.dossier_archives, '00_A_CLASSER'], 'dossiers créés');
    egal(etat.crees[1].parents, ['arch'], 'parent de 00_A_CLASSER');
    attendre(m.requetes.every(r => r.methode !== 'DELETE' && r.methode !== 'PATCH'), 'suppression ou modification');
    egal(etat.envoyes.length, 2, 'envois');
    const corps = await etat.envoyes[0].corps.text();
    attendre(corps.includes('"name":"SCAN-a.pdf"') && corps.includes('"parents":["acl"]') && corps.includes('%PDF'), 'contenu multipart');
    attendre(JSON.parse(m.memoire.cap_scan_dossiers_v1).a_classer === 'acl', 'identifiants gardés');
    const gardes = await f.lister();
    egal(gardes.map(x => x.etat), ['depose', 'depose'], 'fiches');
  });

  await test('dépôt : dossiers existants réutilisés, pas de doublon de fichier', async () => {
    const etat = { archives: true, aclasser: true, existant: true };
    const m = monterDepot({ reponses: reponsesDrive(etat) });
    const f = await filePrete(['SCAN-c.pdf']);
    const res = await m.depot.deposerEnAttente(f);
    egal(res.deposes, 1, 'marqué déposé');
    attendre(!etat.crees && !etat.envoyes, 'dossier recréé ou fichier renvoyé en double');
    egal((await f.lister())[0].drive_id, 'deja', 'identifiant du fichier existant');
  });

  await test('dépôt : échec réseau = rien perdu, arrêt au premier échec, reprise ensuite', async () => {
    const etat = { echecEnvoi: true };
    const m = monterDepot({ reponses: reponsesDrive(etat) });
    const f = await filePrete(['SCAN-d.pdf', 'SCAN-e.pdf']);
    const res = await m.depot.deposerEnAttente(f);
    egal([res.deposes, res.restants], [0, 2], 'après échec');
    attendre(res.erreur.includes('Réseau'), 'erreur non transmise');
    const attente = await f.enAttente();
    attendre(attente.length === 2 && attente.every(x => x.pdf && x.pdf.size > 0), 'PDF perdu');
    attendre(m.requetes.filter(r => r.chemin === '/upload/drive/v3/files').length === 1, 'doit s’arrêter au premier échec');
    etat.echecEnvoi = false;
    const res2 = await m.depot.deposerEnAttente(f);
    egal([res2.deposes, res2.restants], [2, 0], 'reprise');
  });

  await test('dépôt : hors connexion ou déconnecté de Google, aucune requête', async () => {
    for (const options of [{ enLigne: false }, { connecte: false }]) {
      const m = monterDepot({ ...options, reponses: reponsesDrive({}) });
      const f = await filePrete(['SCAN-f.pdf']);
      const res = await m.depot.deposerEnAttente(f);
      egal([res.deposes, res.restants], [0, 1], 'garde sur le téléphone');
      egal(m.requetes.length, 0, 'requêtes envoyées sans réseau');
    }
  });

  // ---------- Écran ----------
  async function demarrerEcran(options = {}) {
    let ouvertures = 0;
    const flux = () => document.createElement('canvas').captureStream();
    Object.defineProperty(navigator, 'mediaDevices', { configurable: true, value: { getUserMedia: async () => { ouvertures++; return flux(); } } });
    const annonces = [];
    const base = 'test_ecran_' + Math.random().toString(36).slice(2);
    const file = scanFile.creer(base);
    const depose = [];
    const depot = options.depot || { deposerEnAttente: async (f, apres) => { for (const x of await f.enAttente()) { await f.marquerDepose(x.id, 'fictif'); depose.push(x.nom); if (apres) apres(x); } return { deposes: depose.length, restants: 0, erreur: '' }; } };
    const maintenant = (() => { let t = 0; return () => new Date(2026, 10, 2, 10, 0, t++); })();
    const ecran = scanEcran.initialiser({ annoncer: (t, f) => annonces.push(t), file, depot, maintenant, delaiRafale: options.delaiRafale });
    const id = i => document.getElementById(i);
    return { ecran, annonces, file, depose, id, ouvertures: () => ouvertures };
  }
  const cliquer = el => el.dispatchEvent(new MouseEvent('click', { bubbles: true }));

  await test('écran : le bouton Scanner ouvre la fenêtre et la caméra', async () => {
    const e = await demarrerEcran();
    attendre(e.id('ouvrir-scanner'), 'bouton Scanner absent');
    cliquer(e.id('ouvrir-scanner'));
    await pause(200);
    attendre(e.id('scanner').open, 'fenêtre fermée');
    egal(e.ouvertures(), 1, 'caméra ouverte');
    egal(e.id('scanner-compteur').textContent, 'Page 1', 'compteur');
    attendre(!e.id('scanner-capturer').hidden && e.id('scanner-revue').hidden, 'état initial');
    cliquer(e.id('scanner-fermer'));
    await pause(100);
  });

  await test('écran : deux pages, un verso vide ignoré, Terminé = un seul PDF', async () => {
    const e = await demarrerEcran();
    cliquer(e.id('ouvrir-scanner'));
    await pause(200);
    const r1 = await e.ecran.recevoirImage(scene());
    egal(r1.ignoree, false, 'page 1');
    attendre(!e.id('scanner-revue').hidden, 'aperçu non affiché');
    cliquer(e.id('scanner-page-suivante'));
    egal(e.id('scanner-compteur').textContent, 'Page 2 (1 déjà prise)', 'compteur après page 1');
    egal(e.id('scanner-pages').children.length, 1, 'liste');
    const r2 = await e.ecran.recevoirImage(scene({ vide: true }));
    egal(r2.ignoree, true, 'verso vide');
    attendre(e.id('scanner-message').textContent.includes('blanche'), 'message verso vide');
    egal(e.id('scanner-pages').children.length, 1, 'verso vide ajouté');
    await e.ecran.recevoirImage(scene({ quad: [[90, 50], [540, 60], [530, 430], [100, 420]] }));
    cliquer(e.id('scanner-terminer'));
    await pause(1500);
    const tout = await e.file.lister();
    egal(tout.length, 1, 'un seul document');
    egal(tout[0].pages, 2, 'pages');
    egal(tout[0].nom, 'SCAN-2026-11-02-10h00m00.pdf', 'nom');
    egal(e.depose, ['SCAN-2026-11-02-10h00m00.pdf'], 'déposé');
    attendre(e.annonces.some(t => t.startsWith('2 pages enregistrées, en cours de classement.')), 'annonce : ' + e.annonces.join('|'));
    attendre(e.annonces.some(t => t.includes('1 page blanche ignorée')), 'verso non mentionné');
    attendre(!e.id('scanner').open, 'fenêtre restée ouverte hors rafale');
    egal(e.id('scanner-compteur').textContent, 'Page 1', 'compteur remis à zéro');
  });

  await test('écran : alerte flou et reprise de la photo à la même place', async () => {
    const e = await demarrerEcran();
    cliquer(e.id('ouvrir-scanner'));
    await pause(200);
    const r = await e.ecran.recevoirImage(flouter(scene(), 6));
    attendre(r.alertes.includes('flou'), 'flou non signalé');
    attendre(e.id('scanner-message').textContent.includes('floue') && e.id('scanner-message').textContent.includes('reprendre'), 'message flou');
    cliquer(e.id('scanner-reprendre'));
    await pause(50);
    attendre(e.id('scanner-revue').hidden && !e.id('scanner-camera').hidden, 'retour caméra');
    await e.ecran.recevoirImage(scene());
    cliquer(e.id('scanner-page-suivante'));
    egal(e.id('scanner-pages').children.length, 1, 'une seule page gardée');
    const ancienne = e.id('scanner-pages').children[0].dataset.page;
    cliquer(e.id('scanner-pages').querySelector('button.reprendre'));
    attendre(e.id('scanner-message').textContent.includes('prendra la place'), 'message reprise');
    await e.ecran.recevoirImage(scene());
    cliquer(e.id('scanner-page-suivante'));
    egal(e.id('scanner-pages').children.length, 1, 'page dupliquée au lieu de remplacée');
    egal(e.id('scanner-pages').children[0].dataset.page, ancienne, 'la page a changé de place');
    await e.ecran.recevoirImage(scene({ quad: [[90, 50], [540, 60], [530, 430], [100, 420]] }));
    cliquer(e.id('scanner-page-suivante'));
    egal(e.id('scanner-pages').children.length, 2, 'deuxième page');
    cliquer(e.id('scanner-fermer'));
    await pause(1500);
  });

  await test('écran : monter, descendre, supprimer une page', async () => {
    const e = await demarrerEcran();
    cliquer(e.id('ouvrir-scanner'));
    await pause(200);
    for (const q of [[[110, 60], [520, 80], [500, 420], [130, 400]], [[90, 50], [540, 60], [530, 430], [100, 420]], [[120, 70], [510, 70], [510, 410], [120, 410]]]) {
      await e.ecran.recevoirImage(scene({ quad: q }));
      cliquer(e.id('scanner-page-suivante'));
    }
    const ids = () => [...e.id('scanner-pages').children].map(li => li.dataset.page);
    const avant = ids();
    egal(avant.length, 3, 'trois pages');
    cliquer(e.id('scanner-pages').children[2].querySelector('button.monter'));
    egal(ids(), [avant[0], avant[2], avant[1]], 'monter');
    cliquer(e.id('scanner-pages').children[0].querySelector('button.descendre'));
    egal(ids(), [avant[2], avant[0], avant[1]], 'descendre');
    cliquer(e.id('scanner-pages').children[1].querySelector('button.supprimer'));
    egal(ids(), [avant[2], avant[1]], 'supprimer');
    egal(e.id('scanner-compteur').textContent, 'Page 3 (2 déjà prises)', 'compteur');
    cliquer(e.id('scanner-terminer'));
    await pause(1500);
    egal((await e.file.lister())[0].pages, 2, 'pages dans le PDF');
  });

  await test('écran : Fermer enregistre les pages en cours (zéro perte)', async () => {
    const e = await demarrerEcran();
    cliquer(e.id('ouvrir-scanner'));
    await pause(200);
    await e.ecran.recevoirImage(scene());
    cliquer(e.id('scanner-fermer'));
    await pause(1500);
    egal((await e.file.lister()).length, 1, 'page perdue à la fermeture');
    attendre(!e.id('scanner').open, 'fenêtre ouverte');
  });

  await test('écran : hors connexion, le scan reste sur le téléphone et part au retour du réseau', async () => {
    let enLigne = false;
    Object.defineProperty(navigator, 'onLine', { configurable: true, get: () => enLigne });
    try {
      const depot = {
        pret: () => enLigne,
        deposerEnAttente: async f => { const a = await f.enAttente(); if (!enLigne) return { deposes: 0, restants: a.length, erreur: '' }; for (const x of a) await f.marquerDepose(x.id, 'ok'); return { deposes: a.length, restants: 0, erreur: '' }; }
      };
      const e = await demarrerEcran({ depot });
      const indicateur = e.id('scans-en-attente');
      await pause(300);
      attendre(indicateur && indicateur.hidden, 'indicateur visible sans scan en attente : ' + indicateur.textContent);
      cliquer(e.id('ouvrir-scanner'));
      await pause(200);
      await e.ecran.recevoirImage(scene());
      cliquer(e.id('scanner-terminer'));
      await pause(1500);
      const attente = await e.file.enAttente();
      egal(attente.length, 1, 'en attente');
      attendre(attente[0].pdf.size > 500, 'PDF absent');
      const horsLigne = 'Pas de réseau : le scan est gardé sur le téléphone et partira tout seul au retour du réseau.';
      attendre(e.annonces.some(t => t.includes(horsLigne)), 'message hors connexion : ' + e.annonces.join('|'));
      attendre(e.id('scanner-message').textContent.includes(horsLigne), 'message dans la fenêtre : ' + e.id('scanner-message').textContent);
      attendre(e.id('scanner-etat').textContent.includes('1 scan en attente d’envoi : gardé sur le téléphone, il partira au retour du réseau'), 'état : ' + e.id('scanner-etat').textContent);
      attendre(!indicateur.hidden && indicateur.textContent.includes('1 scan en attente') && indicateur.textContent.includes('retour du réseau'), 'indicateur : ' + indicateur.textContent);
      await e.ecran.recevoirImage(scene());
      cliquer(e.id('scanner-terminer'));
      await pause(1500);
      egal((await e.file.enAttente()).length, 2, 'deux scans en attente');
      attendre(indicateur.textContent.includes('2 scans en attente') && indicateur.textContent.includes('gardés') && indicateur.textContent.includes('ils partiront'), 'indicateur pluriel : ' + indicateur.textContent);
      enLigne = true;
      window.dispatchEvent(new Event('online'));
      await pause(600);
      egal((await e.file.enAttente()).length, 0, 'déposé au retour du réseau');
      attendre(!indicateur.hidden && indicateur.textContent.includes('Tous les scans sont déposés'), 'indicateur après dépôt : ' + indicateur.textContent);
      attendre(e.id('scanner-etat').textContent.includes('Tous les scans sont déposés'), 'état après dépôt');
    } finally {
      delete navigator.onLine;
    }
  });

  await test('écran : réseau présent mais Cap non connecté à Google, le scan attend la connexion', async () => {
    let connecte = false;
    const depot = { pret: () => connecte, deposerEnAttente: async f => { const a = await f.enAttente(); if (!connecte) return { deposes: 0, restants: a.length, erreur: '' }; for (const x of a) await f.marquerDepose(x.id, 'ok'); return { deposes: a.length, restants: 0, erreur: '' }; } };
    const e = await demarrerEcran({ depot });
    cliquer(e.id('ouvrir-scanner'));
    await pause(200);
    await e.ecran.recevoirImage(scene());
    cliquer(e.id('scanner-terminer'));
    await pause(1500);
    attendre(e.annonces.some(t => t.includes('Cap n’est pas connecté à Google : le scan est gardé sur le téléphone et partira après la connexion.')), 'message : ' + e.annonces.join('|'));
    attendre(e.id('scans-en-attente').textContent.includes('connexion à Google'), 'indicateur : ' + e.id('scans-en-attente').textContent);
    egal((await e.file.enAttente()).length, 1, 'scan perdu');
  });

  await test('écran : au démarrage, des scans restés en attente sont signalés', async () => {
    const base = 'test_demarrage_' + Math.random().toString(36).slice(2);
    const file = scanFile.creer(base);
    await file.ajouter({ nom: 'SCAN-2026-11-02-09h00m00.pdf', pdf: new Blob([new Uint8Array(600)], { type: 'application/pdf' }), pages: 1 });
    const depot = { pret: () => false, deposerEnAttente: async f => ({ deposes: 0, restants: (await f.enAttente()).length, erreur: '' }) };
    scanEcran.initialiser({ annoncer: () => {}, file, depot });
    await pause(400);
    const indicateur = document.getElementById('scans-en-attente');
    attendre(!indicateur.hidden && indicateur.textContent.includes('1 scan en attente'), 'indicateur : ' + indicateur.textContent);
  });

  await test('écran : mode rafale, la caméra se rouvre, compte rendu à la fin', async () => {
    const e = await demarrerEcran({ delaiRafale: 60000 });
    cliquer(e.id('ouvrir-scanner'));
    await pause(200);
    const interrupteur = e.id('scanner-rafale');
    interrupteur.checked = true;
    interrupteur.dispatchEvent(new Event('change', { bubbles: true }));
    for (let i = 0; i < 3; i++) {
      await e.ecran.recevoirImage(scene());
      cliquer(e.id('scanner-terminer'));
      await pause(1500);
      attendre(e.id('scanner').open, `fenêtre fermée après le document ${i + 1} en rafale`);
      attendre(!e.id('scanner-camera').hidden && e.id('scanner-revue').hidden, 'caméra non rouverte');
    }
    egal((await e.file.lister()).length, 3, 'trois documents');
    egal(new Set((await e.file.lister()).map(x => x.nom)).size, 3, 'noms identiques');
    attendre(e.ouvertures() >= 2, 'caméra pas rouverte');
    cliquer(e.id('scanner-fermer'));
    await pause(800);
    attendre(e.annonces.includes('3 scannés, 3 déposés, 0 en attente.'), 'compte rendu : ' + e.annonces.join('|'));
    attendre(!e.id('scanner').open, 'fenêtre ouverte');
  });

  // ---------- Lecture du texte par l'IA (lot 3.2) : l'appel est toujours simulé, images fictives ----------
  window.dateDuJour = () => new Date().toISOString().slice(0, 10);
  const nettoyerIA = () => { for (const k of ['cap_cle_ia_v1', 'cap_depense_ia_v1', 'cap_echanges_ia_v1', 'cap_reglages_ia_v1']) localStorage.removeItem(k); };
  async function avecFauxClaude(reponse, action) {
    const vrai = window.fetch;
    const appels = [];
    window.fetch = async (adresse, options) => {
      appels.push({ adresse, options, corps: JSON.parse(options.body) });
      return reponse();
    };
    try { await action(appels); } finally { window.fetch = vrai; nettoyerIA(); }
  }
  const reponseTexte = (texte, extra = {}) => () => ({ ok: true, status: 200, json: async () => ({ content: [{ type: 'text', text: texte }], usage: { input_tokens: 1700, output_tokens: 400 }, ...extra }) });
  const cleFictive = () => localStorage.setItem('cap_cle_ia_v1', 'sk-ant-' + 'x'.repeat(40));

  await test('lecture : sans « oui » explicite, rien n’est envoyé', async () => {
    nettoyerIA(); cleFictive();
    await avecFauxClaude(reponseTexte('texte'), async appels => {
      const page = { jpeg: new Uint8Array([1, 2, 3]) };
      for (const accord of [undefined, false, 'oui', 1]) {
        let erreur = '';
        try { await scanLecture.lire([page], { accord }); } catch (e) { erreur = e.message; }
        attendre(erreur.includes('Pas de « oui »'), 'lecture sans accord strict : ' + erreur);
      }
      egal(appels.length, 0, 'requêtes envoyées sans accord');
    });
  });

  await test('lecture : pas de clé, trop de pages ou plafond atteint, aucune lecture', async () => {
    nettoyerIA();
    attendre(scanLecture.verifier(1).includes('clé'), 'sans clé : ' + scanLecture.verifier(1));
    cleFictive();
    egal(scanLecture.verifier(1), '', 'avec clé');
    attendre(scanLecture.verifier(6).includes('5 pages'), 'trop de pages');
    attendre(scanLecture.verifier(0) !== '', 'zéro page');
    limiteIA.ajouterDepense(5e6, 0);
    attendre(scanLecture.verifier(1).includes('plafond'), 'plafond : ' + scanLecture.verifier(1));
    nettoyerIA();
  });

  await test('lecture : requête neutre, images seules, sans fiche ni clé dans le corps', async () => {
    nettoyerIA(); cleFictive();
    await avecFauxClaude(reponseTexte('Facture FICTIF 12 [?]'), async appels => {
      const r = await scanLecture.lire([{ jpeg: new Uint8Array([255, 216, 255, 217]) }, { jpeg: new Uint8Array([255, 216, 255, 217]) }], { accord: true });
      egal(appels.length, 1, 'une seule requête pour deux pages');
      const { corps, options } = appels[0];
      egal(corps.messages[0].content.filter(b => b.type === 'image').length, 2, 'images');
      egal(corps.messages[0].content[0].source.media_type, 'image/jpeg', 'type');
      attendre(corps.messages[0].content[0].source.data === btoa(String.fromCharCode(255, 216, 255, 217)), 'base64');
      attendre(options.headers['x-api-key'].startsWith('sk-ant-'), 'clé dans l’en-tête');
      attendre(!options.body.includes('sk-ant-'), 'clé dans le corps');
      attendre(!('tools' in corps), 'outils donnés à la lecture');
      attendre(corps.system.includes('invente jamais') && corps.system.includes('[illisible]'), 'consigne d’honnêteté');
      egal(r.texte, 'Facture FICTIF 12 [?]', 'texte');
      egal(r.pages, 2, 'pages');
      attendre(r.euros > 0 && limiteIA.depenseDuMois() > 0, 'dépense non comptée');
    });
  });

  await test('lecture : erreur de clé ou réseau coupé, message clair, rien d’inventé', async () => {
    nettoyerIA(); cleFictive();
    await avecFauxClaude(() => ({ ok: false, status: 401, json: async () => ({}) }), async () => {
      let erreur = '';
      try { await scanLecture.lire([{ jpeg: new Uint8Array([1]) }], { accord: true }); } catch (e) { erreur = e.message; }
      attendre(erreur.includes('expiré'), 'erreur 401 : ' + erreur);
    });
    cleFictive();
    await avecFauxClaude(() => { throw new TypeError('réseau'); }, async () => {
      let erreur = '';
      try { await scanLecture.lire([{ jpeg: new Uint8Array([1]) }], { accord: true }); } catch (e) { erreur = e.message; }
      attendre(erreur.includes('gardé sur le téléphone'), 'réseau coupé : ' + erreur);
    });
    cleFictive();
    await avecFauxClaude(reponseTexte('Début du texte', { stop_reason: 'max_tokens' }), async () => {
      const r = await scanLecture.lire([{ jpeg: new Uint8Array([1]) }], { accord: true });
      attendre(r.texte.includes('je ne suis pas sûr de la fin'), 'texte coupé non signalé');
    });
  });

  await test('écran : la lecture demande l’accord à chaque fois, « non » n’envoie rien', async () => {
    nettoyerIA(); cleFictive();
    await avecFauxClaude(reponseTexte('Courrier FICTIF'), async appels => {
      const e = await demarrerEcran();
      cliquer(e.id('ouvrir-scanner'));
      await pause(200);
      await e.ecran.recevoirImage(scene());
      cliquer(e.id('scanner-lire'));
      attendre(!e.id('scanner-accord').hidden, 'accord non demandé');
      const demande = e.id('scanner-accord-texte').textContent;
      attendre(demande.includes('1 page') && demande.includes('Anthropic') && demande.includes('sur 4,00 €'), 'phrase d’accord : ' + demande);
      egal(appels.length, 0, 'envoi avant le oui');
      cliquer(e.id('scanner-accord-non'));
      attendre(e.id('scanner-accord').hidden, 'accord resté ouvert');
      attendre(e.id('scanner-message').textContent.includes('rien n’a été envoyé'), 'message refus : ' + e.id('scanner-message').textContent);
      egal(appels.length, 0, 'envoi après non');
      cliquer(e.id('scanner-lire'));
      cliquer(e.id('scanner-accord-oui'));
      await pause(300);
      egal(appels.length, 1, 'une lecture');
      attendre(!e.id('scanner-texte-zone').hidden && e.id('scanner-texte').textContent === 'Courrier FICTIF', 'texte affiché');
      attendre(e.id('scanner-message').textContent.includes('peut se tromper'), 'avertissement');
      cliquer(e.id('scanner-lire'));
      attendre(!e.id('scanner-accord').hidden, 'accord non redemandé pour la deuxième lecture');
      egal(appels.length, 1, 'envoi sans nouveau oui');
      cliquer(e.id('scanner-accord-non'));
      cliquer(e.id('scanner-terminer'));
      await pause(1500);
      const fiche = (await e.file.lister())[0];
      egal(fiche.texte, 'Courrier FICTIF', 'texte gardé avec le scan');
      attendre(fiche.pdf === null || fiche.pdf.size > 500, 'scan abîmé');
      attendre(e.id('scanner-texte-zone').hidden && e.id('scanner-texte').textContent === '', 'texte pas effacé pour le document suivant');
    });
  });

  await test('écran : lecture impossible (pas de clé, erreur), le scan et les pages restent intacts', async () => {
    nettoyerIA();
    await avecFauxClaude(reponseTexte('inutile'), async appels => {
      const e = await demarrerEcran();
      cliquer(e.id('ouvrir-scanner'));
      await pause(200);
      await e.ecran.recevoirImage(scene());
      cliquer(e.id('scanner-lire'));
      attendre(e.id('scanner-accord').hidden, 'accord proposé sans clé');
      attendre(e.id('scanner-message').textContent.includes('clé'), 'message sans clé : ' + e.id('scanner-message').textContent);
      cleFictive();
    });
    nettoyerIA(); cleFictive();
    await avecFauxClaude(() => ({ ok: false, status: 500, json: async () => ({}) }), async appels => {
      const e = await demarrerEcran();
      cliquer(e.id('ouvrir-scanner'));
      await pause(200);
      await e.ecran.recevoirImage(scene());
      cliquer(e.id('scanner-lire'));
      cliquer(e.id('scanner-accord-oui'));
      await pause(300);
      attendre(e.id('scanner-message').textContent.includes('ne répond pas'), 'message erreur : ' + e.id('scanner-message').textContent);
      attendre(e.id('scanner-texte-zone').hidden, 'texte affiché malgré l’erreur');
      attendre(!e.id('scanner-lire').disabled, 'bouton resté bloqué');
      cliquer(e.id('scanner-terminer'));
      await pause(1500);
      const fiche = (await e.file.lister())[0];
      egal(fiche.texte, '', 'texte inventé');
      egal((await e.file.lister()).length, 1, 'scan perdu');
    });
  });

  // ---------- Lot 3.3 : nommage (noms fictifs seulement) ----------
  await test('nommage : accents, majuscules, séparateurs, morceaux manquants', () => {
    const p = scanNommage.proposer({ type: 'Ordonnance', organisme: 'Dr Dupont (FICTIF)', personne: 'Zoe Test', date: '2026-05-14', description: 'Antibiotique à prendre' });
    egal(p.base, '2026-05-14 - ORDONNANCE - DR DUPONT FICTIF - ZOE TEST - ANTIBIOTIQUE A PRENDRE', 'exemple du document');
    egal(p.nom, p.base + '.pdf', 'extension');
    egal([p.dateValide, p.manques], [true, []], 'rien ne manque');
    const q = scanNommage.proposer({ type: 'Fiche de paie', organisme: 'Société Œuvre-Test', personne: '', date: '2026-09', description: '' });
    egal(q.base, '2026-09 - FICHE DE PAIE - SOCIETE OEUVRE TEST', 'mois seul, morceaux vides omis, sans accent');
    attendre(/^[A-Z0-9 -]+$/.test(q.base), 'caractères spéciaux : ' + q.base);
  });

  await test('nommage : date absente ou invalide = « DATE A PRECISER », jamais inventée', () => {
    for (const date of ['', 'inconnu', '2026-13-01', '2026-02-30', '14/05/2026', '1850-01-01']) {
      const p = scanNommage.proposer({ type: 'Facture', organisme: 'Banque FICTIF', date });
      attendre(p.base.startsWith('DATE A PRECISER - FACTURE'), 'date « ' + date + ' » : ' + p.base);
      egal(p.dateValide, false, 'dateValide pour ' + date);
      attendre(p.manques.some(m => m.includes('date')), 'manque non signalé pour ' + date);
      egal(scanNommage.verifier(p.base).ok, false, 'validation sans date pour ' + date);
    }
    const sans = scanNommage.proposer(null);
    egal(sans.base, 'DATE A PRECISER - DOCUMENT', 'identification absente');
    egal(sans.manques.length, 3, 'manques');
    egal(scanNommage.proposer({ type: 'X', date: '2024-02-29' }).dateValide, true, 'année bissextile');
    egal(scanNommage.proposer({ type: 'X', date: '2026-02-29' }).dateValide, false, 'pas bissextile');
  });

  await test('nommage : longueurs limitées et noms uniques', () => {
    const long = 'MOT '.repeat(100);
    const p = scanNommage.proposer({ type: long, organisme: long, personne: long, date: '2026-01-01', description: long });
    attendre(p.base.length <= 150, 'trop long : ' + p.base.length);
    attendre(p.base.startsWith('2026-01-01 - MOT'), 'début : ' + p.base);
    const base = '2026-05-14 - FACTURE - EDF FICTIF';
    const a = scanNommage.uniqueAvecExtension(base, []);
    const b = scanNommage.uniqueAvecExtension(base, [a]);
    const c = scanNommage.uniqueAvecExtension(base, [a, b.toUpperCase()]);
    egal([a, b, c], [base + '.pdf', base + '-2.pdf', base + '-3.pdf'], 'suffixes');
  });

  await test('nommage : vérification du nom tapé par Max', () => {
    egal(scanNommage.verifier('2026-05-14 - facture - Électricité FICTIF.pdf').base, '2026-05-14 - FACTURE - ELECTRICITE FICTIF', 'nettoyage');
    egal(scanNommage.verifier('2026-05 - magazine - métropole édition lyon').ok, true, 'mois seul');
    egal(scanNommage.verifier('facture sans date').ok, false, 'sans date');
    egal(scanNommage.verifier('2026-05-14').ok, false, 'date seule');
    egal(scanNommage.verifier('').ok, false, 'vide');
  });

  await test('lecture : le bloc d’identification est séparé du texte, absent ou coupé = null', async () => {
    const bloc = '\n=== IDENTIFICATION ===\nTYPE: Magazine\nORGANISME: Métropole FICTIF\nPERSONNE: inconnu\nDATE: 2026-10\nDESCRIPTION: Numéro 65 édition Lyon';
    const r = scanLecture.separer('Texte du magazine FICTIF' + bloc, false);
    egal(r.transcription, 'Texte du magazine FICTIF', 'transcription sans le bloc');
    egal(r.identification, { type: 'Magazine', organisme: 'Métropole FICTIF', personne: '', date: '2026-10', description: 'Numéro 65 édition Lyon' }, 'identification');
    egal(scanLecture.separer('Texte seul', false).identification, null, 'bloc absent');
    egal(scanLecture.separer('Texte' + bloc, true).identification, null, 'réponse coupée');
    egal(scanLecture.separer('Texte\n=== IDENTIFICATION ===\nTYPE: Facture', false).identification, null, 'bloc incomplet');
    attendre(scanLecture.consigne.includes('inconnu') && scanLecture.consigne.includes('N’invente jamais un type'), 'consigne d’honnêteté');
    nettoyerIA(); cleFictive();
    await avecFauxClaude(reponseTexte('Courrier FICTIF' + bloc), async () => {
      const lu = await scanLecture.lire([{ jpeg: new Uint8Array([1, 2]) }], { accord: true });
      egal([lu.texte, lu.identification.date], ['Courrier FICTIF', '2026-10'], 'lire');
    });
  });

  await test('dépôt : nom validé utilisé, nom d’origine gardé dans Drive, reprise sans doublon', async () => {
    const etat = {};
    const m = monterDepot({ reponses: reponsesDrive(etat) });
    const f = scanFile.creer('test_depot_nom_' + Math.random().toString(36).slice(2));
    const pdf = () => new Blob([new Uint8Array([37, 80, 68, 70, 9])], { type: 'application/pdf' });
    await f.ajouter({ nom: 'SCAN-origine.pdf', pdf: pdf(), pages: 1, nom_propose: '2026-10 - MAGAZINE FICTIF.pdf', nom_valide: '2026-10 - MAGAZINE FICTIF.pdf' });
    await f.ajouter({ nom: 'SCAN-provisoire.pdf', pdf: pdf(), pages: 1, nom_propose: '2026-10 - AUTRE FICTIF.pdf' });
    const res = await m.depot.deposerEnAttente(f);
    egal([res.deposes, res.restants], [2, 0], 'résultat');
    const corps0 = await etat.envoyes[0].corps.text();
    attendre(corps0.includes('"name":"2026-10 - MAGAZINE FICTIF.pdf"'), 'nom validé non utilisé');
    attendre(corps0.includes('"cap_origine":"SCAN-origine.pdf"') && corps0.includes('Nom d’origine : SCAN-origine.pdf'), 'nom d’origine perdu');
    const corps1 = await etat.envoyes[1].corps.text();
    attendre(corps1.includes('"name":"SCAN-provisoire.pdf"') && !corps1.includes('cap_origine'), 'nom provisoire non gardé quand rien n’est validé');
    const requeteReprise = m.requetes.find(r => r.q.includes('cap_origine'));
    attendre(requeteReprise && requeteReprise.q.includes('SCAN-origine.pdf'), 'reprise non basée sur le nom d’origine');
    const fiches = await f.lister();
    egal(fiches.map(x => x.nom), ['SCAN-origine.pdf', 'SCAN-provisoire.pdf'], 'nom d’origine jamais modifié');
    egal(fiches[1].nom_propose, '2026-10 - AUTRE FICTIF.pdf', 'proposition gardée pour le lot 3.4');
    const etat2 = { archives: true, aclasser: true, existant: true };
    const m2 = monterDepot({ reponses: reponsesDrive(etat2) });
    const g = scanFile.creer('test_depot_nom2_' + Math.random().toString(36).slice(2));
    await g.ajouter({ nom: 'SCAN-x.pdf', pdf: pdf(), pages: 1, nom_valide: '2026-01 - TEST FICTIF.pdf' });
    egal((await m2.depot.deposerEnAttente(g)).deposes, 1, 'reprise');
    attendre(!etat2.envoyes, 'fichier renvoyé en double');
  });

  const lireIdentification = async (e, appels) => {
    cliquer(e.id('scanner-lire'));
    cliquer(e.id('scanner-accord-oui'));
    await pause(400);
  };
  const blocMagazine = '\n=== IDENTIFICATION ===\nTYPE: Magazine\nORGANISME: Métropole FICTIF\nPERSONNE: inconnu\nDATE: 2026-10\nDESCRIPTION: Numéro 65 édition Lyon';
  const saisir = (e, valeur) => { const champ = e.id('scanner-nom'); champ.value = valeur; champ.dispatchEvent(new Event('input')); };

  await test('écran : le nom est proposé, rien n’est renommé sans « Valider », puis le nom validé est gardé', async () => {
    nettoyerIA(); cleFictive();
    await avecFauxClaude(reponseTexte('Magazine FICTIF' + blocMagazine), async appels => {
      const e = await demarrerEcran();
      cliquer(e.id('ouvrir-scanner'));
      await pause(200);
      await e.ecran.recevoirImage(scene());
      attendre(e.id('scanner-nom-zone').hidden, 'nom proposé avant la lecture');
      await lireIdentification(e, appels);
      attendre(!e.id('scanner-nom-zone').hidden, 'zone du nom absente');
      egal(e.id('scanner-nom').value, '2026-10 - MAGAZINE - METROPOLE FICTIF - NUMERO 65 EDITION LYON', 'nom proposé');
      attendre(!e.id('scanner-texte').textContent.includes('IDENTIFICATION'), 'bloc d’identification affiché à Max');
      attendre(e.id('scanner-nom-statut').textContent.includes('Rien n’est renommé'), 'statut');
      saisir(e, '2026-10 - magazine - métropole fictif - numéro 65');
      cliquer(e.id('scanner-nom-valider'));
      attendre(e.id('scanner-nom-statut').textContent.includes('Nom enregistré : 2026-10 - MAGAZINE - METROPOLE FICTIF - NUMERO 65.pdf'), 'validation : ' + e.id('scanner-nom-statut').textContent);
      attendre(e.id('scanner-message').textContent.includes('Nom enregistré : 2026-10 - MAGAZINE - METROPOLE FICTIF - NUMERO 65.pdf') && !e.id('scanner-message').hidden, 'confirmation non visible tout de suite : ' + e.id('scanner-message').textContent);
      cliquer(e.id('scanner-terminer'));
      await pause(1500);
      const fiche = (await e.file.lister())[0];
      egal(fiche.nom_valide, '2026-10 - MAGAZINE - METROPOLE FICTIF - NUMERO 65.pdf', 'nom validé gardé');
      attendre(fiche.nom.startsWith('SCAN-'), 'nom d’origine perdu : ' + fiche.nom);
      egal(fiche.nom_propose, '2026-10 - MAGAZINE - METROPOLE FICTIF - NUMERO 65 EDITION LYON.pdf', 'proposition gardée');
      attendre(e.id('scanner-nom-zone').hidden && e.id('scanner-nom').value === '', 'nom pas effacé pour le document suivant');
    });
  });

  await test('écran : « Garder le nom provisoire », ou nom sans date, rien n’est renommé', async () => {
    nettoyerIA(); cleFictive();
    await avecFauxClaude(reponseTexte('Courrier FICTIF' + blocMagazine), async appels => {
      const e = await demarrerEcran();
      cliquer(e.id('ouvrir-scanner'));
      await pause(200);
      await e.ecran.recevoirImage(scene());
      await lireIdentification(e, appels);
      saisir(e, 'facture sans date');
      cliquer(e.id('scanner-nom-valider'));
      attendre(!e.id('scanner-nom-erreur').hidden && e.id('scanner-nom-erreur').textContent.includes('date'), 'validation sans date acceptée');
      cliquer(e.id('scanner-nom-provisoire'));
      attendre(e.id('scanner-nom-statut').textContent.includes('Nom provisoire enregistré'), 'statut provisoire');
      attendre(e.id('scanner-message').textContent.includes('Nom provisoire enregistré') && !e.id('scanner-message').hidden, 'confirmation du nom provisoire non visible : ' + e.id('scanner-message').textContent);
      cliquer(e.id('scanner-terminer'));
      await pause(1500);
      const fiche = (await e.file.lister())[0];
      egal(fiche.nom_valide, '', 'nom validé sans clic');
      attendre(fiche.nom.startsWith('SCAN-') && fiche.nom_propose.startsWith('2026-10'), 'nom provisoire ou proposition perdus');
    });
  });

  await test('écran : sans date lue, la validation reste bloquée', async () => {
    nettoyerIA(); cleFictive();
    const sansDate = '\n=== IDENTIFICATION ===\nTYPE: Facture\nORGANISME: Banque FICTIF\nPERSONNE: inconnu\nDATE: inconnu\nDESCRIPTION: inconnu';
    await avecFauxClaude(reponseTexte('Facture FICTIF' + sansDate), async appels => {
      const e = await demarrerEcran();
      cliquer(e.id('ouvrir-scanner'));
      await pause(200);
      await e.ecran.recevoirImage(scene());
      await lireIdentification(e, appels);
      egal(e.id('scanner-nom').value, 'DATE A PRECISER - FACTURE - BANQUE FICTIF', 'nom proposé');
      attendre(e.id('scanner-nom-manque').textContent.includes('la date'), 'manque non dit : ' + e.id('scanner-nom-manque').textContent);
      cliquer(e.id('scanner-nom-valider'));
      attendre(!e.id('scanner-nom-erreur').hidden, 'validation sans date');
      cliquer(e.id('scanner-terminer'));
      await pause(1500);
      egal((await e.file.lister())[0].nom_valide, '', 'nom validé sans date');
    });
  });

  const erreursPage = window.erreursPage || [];
  document.getElementById('resultat-tests').textContent = JSON.stringify({
    erreurs_page: erreursPage, reussis: resultats.filter(r => r.ok).length, total: resultats.length, tests: resultats
  });
  fetch('/fini').catch(() => {});
})();
"""


def construire_page():
    style = (APP / "style.css").read_text(encoding="utf-8")
    index = (APP / "index.html").read_text(encoding="utf-8")
    corps = re.search(r"<body>(.*?)</body>", index, re.S).group(1)
    corps = re.sub(r"<script\b[^>]*>.*?</script>", "", corps, flags=re.S)
    scripts = "\n".join(f'<script src="/src/{nom}"></script>' for nom in SOURCES)
    return f"""<!doctype html>
<html lang="fr">
<head><meta charset="utf-8"><title>Tests scanner</title><style>{style}</style></head>
<body>
<pre id="resultat-tests"></pre>
<img src="/attente.gif" alt="" width="1" height="1">
<script>
window.erreursPage = [];
window.addEventListener('error', e => window.erreursPage.push(String(e.message)));
window.addEventListener('unhandledrejection', e => window.erreursPage.push(String(e.reason)));
</script>
{corps}
{scripts}
<script>{TESTS_JS}</script>
<script>setTimeout(() => {{ const p = document.getElementById('resultat-tests'); if (!p.textContent) p.textContent = JSON.stringify({{ erreurs_page: window.erreursPage.concat(['Les tests ne se sont pas terminés.'], window.progres || []), reussis: 0, total: 0, tests: [] }}); fetch('/fini'); }}, 100000);</script>
</body>
</html>
"""


FINI = threading.Event()


class Gestionnaire(BaseHTTPRequestHandler):
    def do_GET(self):
        chemin = self.path.split("?", 1)[0]
        if chemin == "/tests.html":
            corps = construire_page().encode("utf-8")
            type_contenu = "text/html; charset=utf-8"
        elif chemin == "/attente.gif":
            FINI.wait(150)
            corps = b"GIF89a\x01\x00\x01\x00\x00\x00\x00;"
            type_contenu = "image/gif"
        elif chemin == "/fini":
            FINI.set()
            corps = b"ok"
            type_contenu = "text/plain"
        elif chemin.startswith("/src/") and chemin[5:] in SOURCES:
            corps = (APP / chemin[5:]).read_bytes()
            type_contenu = "text/javascript; charset=utf-8"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", type_contenu)
        self.send_header("Content-Length", str(len(corps)))
        self.end_headers()
        self.wfile.write(corps)

    def log_message(self, format, *args):
        pass


def executer(port):
    url = f"http://127.0.0.1:{port}/tests.html"
    with tempfile.TemporaryDirectory(dir=APP, ignore_cleanup_errors=True) as profil:
        commande = [
            str(EDGE), "--headless", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
            "--disable-background-networking", f"--user-data-dir={profil}", "--dump-dom",
            url,
        ]
        try:
            resultat = subprocess.run(commande, capture_output=True, timeout=180)
        except subprocess.TimeoutExpired:
            return None
        return resultat.stdout.decode("utf-8", errors="replace")


def main():
    if not EDGE.exists():
        print(f"Edge introuvable : {EDGE}")
        return 2
    serveur = ThreadingHTTPServer(("127.0.0.1", 0), Gestionnaire)
    threading.Thread(target=serveur.serve_forever, daemon=True).start()
    try:
        sortie = executer(serveur.server_address[1])
    finally:
        serveur.shutdown()
        serveur.server_close()
    if sortie is None:
        print("Délai dépassé lors de l’exécution d’Edge.")
        return 1
    trouve = re.search(r'<pre id="resultat-tests">(.*?)</pre>', sortie, re.S)
    if not trouve or not trouve.group(1).strip():
        print("Résultat des tests introuvable dans le DOM.")
        return 1
    rapport = json.loads(html.unescape(trouve.group(1)))
    for erreur in rapport["erreurs_page"]:
        print(f"ERREUR PAGE : {erreur}")
    for test in rapport["tests"]:
        print(("OK   " if test["ok"] else "ECHEC") + " " + test["nom"])
        if not test["ok"]:
            print("      " + test["erreur"].splitlines()[0])
    print(f"{rapport['reussis']}/{rapport['total']} tests réussis")
    return 1 if rapport["erreurs_page"] or rapport["reussis"] != rapport["total"] else 0


if __name__ == "__main__":
    sys.exit(main())
