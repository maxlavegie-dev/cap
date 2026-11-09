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
SOURCES = ["reglages_google.js", "reglages_ia.js", "limite_ia.js", "cle_ia.js", "scan_image.js", "scan_pdf.js", "scan_documents.js", "scan_file.js", "scan_depot.js", "scan_lecture.js", "scan_nommage.js", "nommage_scan.js", "mots_courts.js", "emetteur.js", "scan_ecran.js"]

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
  function monterDepot({ connecte = true, enLigne = true, reponses, documents = { id: 'docs', nom: 'Documents Personnels' }, depuisDrive = null }) {
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
    const rangements = [];
    const piqueur = {
      dossierDocumentsPersonnels: () => documents,
      retrouverDepuisDrive: async role => { rangements.push('relu:' + role); return depuisDrive; },
      rangerDansDrive: async role => { rangements.push('range:' + role); }
    };
    const depot = new Function('googleConnexion', 'REGLAGES_GOOGLE', 'localStorage', 'navigator', 'googlePicker', sourceDepot + '\nreturn scanDepot;')(
      faux, REGLAGES_GOOGLE, stockageFaux, { onLine: enLigne }, piqueur);
    return { depot, requetes, memoire, rangements };
  }
  const reponsesDrive = (etat = {}) => async r => {
    if (r.methode === 'GET' && r.chemin === '/drive/v3/files' && r.q.includes('folder')) {
      (etat.recherches ||= []).push(r.q);
      return { files: etat.aclasser ? [{ id: 'acl' }] : [] };
    }
    if (r.methode === 'GET' && r.chemin.startsWith('/drive/v3/files/')) return { id: 'x', trashed: false };
    if (r.methode === 'GET' && r.chemin === '/drive/v3/files') return { files: etat.existant ? [{ id: 'deja' }] : [] };
    if (r.methode === 'POST' && r.chemin === '/drive/v3/files') {
      const meta = JSON.parse(r.corps);
      (etat.crees ||= []).push(meta);
      return { id: 'acl' };
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

  await test('dépôt (règle de nommage) : nom déjà pris dans le dossier → « (2) », « (3) » ; description sans le texte lu', async () => {
    const etat = { aclasser: true, envoyes: [] };
    const pris = ['2026-01-12 Attestation - Jean Fictif.pdf', '2026-01-12 Attestation - Jean Fictif (2).pdf'];
    const base = reponsesDrive(etat);
    const m = monterDepot({ reponses: async r => {
      if (r.methode === 'GET' && r.chemin === '/drive/v3/files' && !r.q.includes('folder')) {
        if (r.q.includes('cap_origine')) return { files: [] };
        return { files: pris.some(nom => r.q.includes(`name='${nom}'`)) ? [{ id: 'autre' }] : [] };
      }
      return base(r);
    } });
    const f = scanFile.creer('test_depot_regle_' + Math.random().toString(36).slice(2));
    await f.ajouter({ nom: 'SCAN-regle.pdf', pdf: new Blob([new Uint8Array([37, 80, 68, 70, 9])], { type: 'application/pdf' }), pages: 1,
      nom_valide: '2026-01-12 Attestation - Jean Fictif.pdf', details: ['Date du scan : 2026-01-15', 'Émetteur : non reconnu'] });
    const res = await m.depot.deposerEnAttente(f);
    egal(res.deposes, 1, 'dépôt');
    const corps = await etat.envoyes[0].corps.text();
    attendre(corps.includes('"name":"2026-01-12 Attestation - Jean Fictif (3).pdf"'), `nom libre non pris : ${corps.slice(0, 300)}`);
    attendre(corps.includes('Nom d’origine : SCAN-regle.pdf\\nDate du scan : 2026-01-15\\nÉmetteur : non reconnu'), 'description incomplète');
  });

  await test('dépôt : crée 00_A_CLASSER dans Documents Personnels, envoie les scans, jamais de suppression', async () => {
    egal(REGLAGES_GOOGLE.dossier_a_classer, '00_A_CLASSER', 'nom du dossier');
    egal(REGLAGES_GOOGLE.dossier_documents_personnels, 'Documents Personnels', 'dossier parent');
    attendre(!('dossier_archives' in REGLAGES_GOOGLE), 'ancien dossier racine encore réglé');
    const etat = {};
    const m = monterDepot({ reponses: reponsesDrive(etat) });
    const f = await filePrete(['SCAN-a.pdf', 'SCAN-b.pdf']);
    const res = await m.depot.deposerEnAttente(f);
    egal([res.deposes, res.restants, res.erreur], [2, 0, ''], 'résultat');
    egal(etat.crees.map(c => c.name), ['00_A_CLASSER'], 'un seul dossier créé, rien à la racine');
    egal(etat.crees[0].parents, ['docs'], 'parent de 00_A_CLASSER');
    attendre(etat.recherches.every(q => q.includes("'docs' in parents")), 'recherche hors de Documents Personnels');
    attendre(m.requetes.every(r => r.methode !== 'DELETE' && r.methode !== 'PATCH'), 'suppression ou modification');
    egal(etat.envoyes.length, 2, 'envois');
    const corps = await etat.envoyes[0].corps.text();
    attendre(corps.includes('"name":"SCAN-a.pdf"') && corps.includes('"parents":["acl"]') && corps.includes('%PDF'), 'contenu multipart');
    attendre(JSON.parse(m.memoire.cap_scan_dossiers_v1).a_classer === 'acl', 'identifiants gardés');
    const gardes = await f.lister();
    egal(gardes.map(x => x.etat), ['depose', 'depose'], 'fiches');
  });

  await test('dépôt : Documents Personnels pas encore choisi = aucune requête, scan gardé, Max prévenu', async () => {
    const m = monterDepot({ reponses: reponsesDrive({}), documents: null });
    const f = await filePrete(['SCAN-g.pdf']);
    const res = await m.depot.deposerEnAttente(f);
    egal([res.deposes, res.restants], [0, 1], 'scan gardé sur le téléphone');
    attendre(res.erreur.includes('Documents Personnels') && res.erreur.includes('Réglages du Drive'), 'message pour Max');
    egal(m.requetes.length, 0, 'aucune requête ni création sans dossier choisi');
    attendre((await f.enAttente())[0].pdf.size > 0, 'PDF perdu');
  });

  await test('dépôt : coque sans choix sur l’appareil = dossier relu dans le Drive, scan déposé dedans', async () => {
    const etat = {};
    const m = monterDepot({ reponses: reponsesDrive(etat), documents: null, depuisDrive: { id: 'docs', nom: 'Documents Personnels' } });
    const f = await filePrete(['SCAN-i.pdf']);
    const res = await m.depot.deposerEnAttente(f);
    egal([res.deposes, res.restants, res.erreur], [1, 0, ''], 'déposé grâce au Drive');
    egal(etat.crees[0].parents, ['docs'], '00_A_CLASSER créé dans le dossier relu');
    attendre(m.rangements.includes('relu:documents_personnels'), 'Drive non relu');
  });

  await test('dépôt : ancien dossier FICTIF gardé en mémoire = jamais réutilisé, 00_A_CLASSER créé dans Documents Personnels', async () => {
    const etat = {};
    const m = monterDepot({ reponses: reponsesDrive(etat) });
    m.memoire.cap_scan_dossiers_v1 = JSON.stringify({ archives: 'arch', a_classer: 'ancien-acl' });
    const f = await filePrete(['SCAN-h.pdf']);
    const res = await m.depot.deposerEnAttente(f);
    egal(res.deposes, 1, 'déposé');
    egal(etat.crees[0].parents, ['docs'], 'créé dans Documents Personnels');
    attendre(!(await etat.envoyes[0].corps.text()).includes('ancien-acl'), 'ancien dossier FICTIF réutilisé');
  });

  await test('dépôt : dossiers existants réutilisés, pas de doublon de fichier', async () => {
    const etat = { aclasser: true, existant: true };
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
    const ecran = scanEcran.initialiser({ annoncer: (t, f) => annonces.push(t), file, depot, maintenant, delaiRafale: options.delaiRafale,
      classement: options.classement, journaux: options.journaux || { ajouter: () => ({}) }, scannerAndroid: options.scannerAndroid || null });
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
      // 08/11/2026 (demande de Max) : plus de « Tous les scans sont déposés… » en bas de l'écran de scan ; rien n'y reste.
      attendre(e.id('scanner-etat').hidden && e.id('scanner-etat').textContent === '', 'état après dépôt : ' + e.id('scanner-etat').textContent);
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
    const p = scanNommage.proposer({ type: 'Devis', organisme: 'Me Dupont (FICTIF)', personne: 'Zoe Test', date: '2026-05-14', description: 'Pièce à fournir' });
    egal(p.base, '2026-05-14 - DEVIS - ME DUPONT FICTIF - ZOE TEST - PIECE A FOURNIR', 'exemple du document');
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
    for (const phrase of ['est OBLIGATOIRE', 'nom de plat', 'nom de lieu', 'mot rare', 'plausible ou courant', 'le doute à la devinette']) {
      attendre(scanLecture.consigne.includes(phrase), 'consigne stricte sans : ' + phrase);
    }
    attendre(scanLecture.consigne.length < 4000, 'consigne trop longue : ' + scanLecture.consigne.length);
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

  // ---------- Étape 3 : scanner de Google (coque) et nom tiré du tableur, FAUX documents ----------
  const tableurFictif = [
    { numero: 2, mot_cle: 'carte test Prenom_fictif', modele: '[date] Carte test Prenom_fictif Nom_fictif', chemin: ['01_IDENTITE_ET_ETAT_CIVIL', 'Pieces_identite'] },
    { numero: 3, mot_cle: 'syndic fictif', modele: '[date] Releve syndic fictif Prenom_fictif', chemin: ['02_MAISON', 'Prenom_fictif', 'Factures_energie'] },
    { numero: 4, mot_cle: 'banque fictive', modele: '[date] Releve banque fictive', chemin: ['04_BANQUE_ET_FINANCES'] },
    { numero: 5, mot_cle: 'releve syndic fictif', modele: '[date] Releve syndic fictif Prenom_fictif', chemin: ['02_MAISON'] }
  ];

  await test('nommage : mot-clé du tableur, date du document, modèle gardé tel quel, jamais de date inventée', async () => {
    let p = nommageScan.proposer('SYNDIC FICTIF\nRelevé du 12/03/2026 pour Prénom FICTIF', tableurFictif);
    egal([p.raison, p.mot_cle, p.nom], ['trouve', 'syndic fictif', '2026-03-12 Releve syndic fictif Prenom_fictif'], 'mot-clé et date');
    p = nommageScan.proposer('Relevé SYNDIC Fictif, sans aucune date', tableurFictif);
    egal(p.nom, 'DATE A PRECISER Releve syndic fictif Prenom_fictif', 'date absente');
    egal(nommageScan.dateDuTexte('Fait le 1er mars 2026, payé le 05/04/2026'), '2026-03-01', 'première date, mois en toutes lettres');
    egal(nommageScan.dateDuTexte('Le 31/02/2026 puis 2026-04-07'), '2026-04-07', 'date impossible écartée');
    egal(nommageScan.dateDuTexte('Référence 12345678, aucune date'), '', 'date inventée');
    p = nommageScan.proposer('Courrier FICTIF de la BANQUE FICTIVE et de la syndic fictif', tableurFictif);
    egal([p.raison, p.nom], ['contradictoire', ''], 'deux modèles différents : aucune proposition');
    egal(nommageScan.proposer('Prospectus FICTIF sans mot-clé', tableurFictif).raison, 'aucun', 'aucun mot-clé');
    egal(nommageScan.proposer('Lettre bancaire fictive', tableurFictif).raison, 'aucun', 'mot-clé pris dans un autre mot');
    egal(nommageScan.proposer('   ', tableurFictif).raison, 'sans_texte', 'texte vide');
    egal(nommageScan.verifierNom('2026-03-12 Relevé Syndic.pdf'), { ok: true, base: '2026-03-12 Relevé Syndic', raison: '', change: false }, 'nom gardé tel quel');
    egal(nommageScan.verifierNom('a/b'), { ok: true, base: 'a-b', raison: '', change: true }, 'caractère interdit remplacé');
    attendre(!nommageScan.verifierNom('  ').ok, 'nom vide accepté');
  });

  function pageJpegFictive() {
    const canvas = document.createElement('canvas');
    canvas.width = 120; canvas.height = 170;
    const c = canvas.getContext('2d');
    c.fillStyle = '#fff'; c.fillRect(0, 0, 120, 170); c.fillStyle = '#000'; c.fillRect(10, 10, 80, 8);
    return canvas.toDataURL('image/jpeg', 0.8);
  }
  function monterGoogle(options = {}) {
    const lignes = [];
    const appels = [];
    const journauxFaux = { ajouter: (journal, ligne) => { lignes.push({ journal, ...ligne }); return {}; } };
    const scanneur = { scanner: () => appels.push('scanner'), oublierPages: () => appels.push('oublier') };
    const classementFaux = { lireTableurChoisi: options.tableurEnPanne
      ? async () => { throw new Error('tableur injoignable FICTIF'); } : async () => tableurFictif };
    return { lignes, appels, options: { journaux: journauxFaux, scannerAndroid: scanneur, classement: classementFaux } };
  }

  async function scanGoogle(g, pages) {
    const e = await demarrerEcran(g.options);
    cliquer(e.id('ouvrir-scanner'));
    await pause(200);
    await e.ecran.recevoirScanGoogle({ pages: pages.map(p => ({ url: pageJpegFictive(), lu: true, ...p })) });
    return e;
  }
  async function terminerPuisVoir(e) {
    cliquer(e.id('scanner-terminer'));
    await pause(300);
  }

  await test('écran Google : rien d’enregistré avant « Terminé » et la réponse ; fenêtre en haut ; « Oui » = nom retenu ; journal précis', async () => {
    const g = monterGoogle();
    const e = await demarrerEcran(g.options);
    cliquer(e.id('ouvrir-scanner'));
    await pause(200);
    attendre(!e.id('scanner-google').hidden, 'bouton du scanner de Google caché dans la coque');
    cliquer(e.id('scanner-google'));
    egal(g.appels, ['scanner'], 'scanner de Google non lancé');
    const res = await e.ecran.recevoirScanGoogle({ pages: [
      { url: pageJpegFictive(), texte: 'SYNDIC FICTIF', lu: true },
      { url: pageJpegFictive(), texte: 'Relevé du 12/03/2026', lu: true }
    ] });
    egal(res.pages, 2, 'pages reçues');
    attendre(g.appels.includes('oublier'), 'pages laissées sur le téléphone');
    attendre(e.id('scanner-proposition').hidden, 'fenêtre affichée avant « Terminé »');
    await terminerPuisVoir(e);
    attendre(!e.id('scanner-proposition').hidden, 'fenêtre absente après « Terminé »');
    const fenetre = e.id('scanner');
    attendre(fenetre.querySelector('header').nextElementSibling === e.id('scanner-proposition'), 'fenêtre pas en haut');
    egal((await e.file.lister()).length, 0, 'scan enregistré avant la réponse');
    egal(e.id('scanner-proposition-nom').textContent, '2026-03-12 Releve syndic fictif Prenom_fictif.pdf', 'nom proposé');
    attendre(e.id('scanner-proposition-info').textContent.includes('33 caractères lus'), `caractères : ${e.id('scanner-proposition-info').textContent}`);
    attendre(e.id('scanner-proposition-daccord').hidden && !e.id('scanner-proposition-oui').hidden, 'mauvais boutons avec un nom');
    cliquer(e.id('scanner-proposition-oui'));
    await pause(1500);
    const fiche = (await e.file.lister())[0];
    egal([fiche.pages, fiche.nom_valide], [2, '2026-03-12 Releve syndic fictif Prenom_fictif.pdf'], 'nom retenu après Oui');
    attendre(fiche.nom.startsWith('SCAN-'), 'nom d’origine perdu');
    egal(g.lignes.length, 1, 'ligne au Journal Numérisation');
    const l = g.lignes[0];
    egal([l.journal, l.action, l.resultat], ['numerisation', 'Lecture du texte', 'mot-clé : syndic fictif'], 'ligne du journal');
    attendre(l.details.includes('caractères lus : 33') && l.details.includes('pages lues : 2 sur 2') && l.details.includes('réponse : Oui')
      && l.details.includes(`ancien nom : ${fiche.nom}`), `détails : ${l.details}`);
    attendre(!l.details.includes('Relevé du 12/03/2026') && !l.details.includes('SYNDIC FICTIF'), 'texte lu recopié dans le journal');
  });

  await test('écran Google : « Non », « Modifier », aucun mot-clé (« D’accord » ou nom écrit par Max)', async () => {
    const cas = [
      ['non', 'SYNDIC FICTIF le 12/03/2026', '', 'Non', 'mot-clé : syndic fictif'],
      ['modifier', 'SYNDIC FICTIF le 12/03/2026', '2026-03-12 Syndic corrigee FICTIF.pdf', 'Modifié', 'mot-clé : syndic fictif'],
      ['daccord', 'Prospectus FICTIF', '', 'D’accord', 'aucun mot-clé trouvé'],
      ['ecrire', 'Prospectus FICTIF', 'Prospectus FICTIF ecrit par Max.pdf', 'Écrit par Max', 'aucun mot-clé trouvé']
    ];
    for (const [action, texte, attendu, reponse, resultat] of cas) {
      const g = monterGoogle();
      const e = await scanGoogle(g, [{ texte }]);
      await terminerPuisVoir(e);
      if (action === 'non') cliquer(e.id('scanner-proposition-non'));
      if (action === 'daccord') {
        attendre(e.id('scanner-proposition-oui').hidden && !e.id('scanner-proposition-daccord').hidden && !e.id('scanner-proposition-ecrire').hidden, 'boutons sans mot-clé');
        attendre(e.id('scanner-proposition-info').textContent.includes('aucun mot-clé du tableur trouvé'), 'message sans mot-clé');
        cliquer(e.id('scanner-proposition-daccord'));
      }
      if (action === 'modifier' || action === 'ecrire') {
        cliquer(e.id(action === 'modifier' ? 'scanner-proposition-modifier' : 'scanner-proposition-ecrire'));
        attendre(!e.id('scanner-proposition-modification').hidden && !e.id('scanner-proposition-oui').hidden, 'saisie absente');
        egal((await e.file.lister()).length, 0, `enregistré avant « Oui » (${action})`);
        e.id('scanner-proposition-champ').value = attendu.replace(/\.pdf$/, '');
        cliquer(e.id('scanner-proposition-oui'));
      }
      await pause(1500);
      const fiche = (await e.file.lister())[0];
      egal(fiche.nom_valide, attendu, `nom retenu (${action})`);
      attendre(g.lignes.length === 1 && g.lignes[0].resultat === resultat && g.lignes[0].details.includes(`réponse : ${reponse}`),
        `journal (${action}) : ${JSON.stringify(g.lignes)}`);
    }
  });

  // ---------- 06/11/2026 : recherche par mots-clés courts et par score, FAUX courrier, FAUX noms ----------
  const tableurMaison = [
    { numero: 2, mot_cle: 'compte rendu de suivi Théo Exemplaire', organisme: 'Garage fictif', modele: '[date] Compte rendu suivi Théo Exemplaire', chemin: ['02_MAISON'] },
    { numero: 3, mot_cle: 'compte rendu Théo Exemplaire', organisme: '', modele: '[date] Compte rendu Théo Exemplaire', chemin: ['02_MAISON'] },
    { numero: 4, mot_cle: 'bilan climatiseur Théo Exemplaire', organisme: 'Garage fictif', modele: '[date] Bilan climatiseur Théo Exemplaire', chemin: ['02_MAISON'] },
    { numero: 5, mot_cle: 'compte rendu de suivi Lina Exemplaire', organisme: '', modele: '[date] Compte rendu suivi Lina Exemplaire', chemin: ['02_MAISON'] },
    { numero: 6, mot_cle: 'compte rendu climatisation Lina Exemplaire', organisme: '', modele: '[date] Compte rendu climatisation Lina Exemplaire', chemin: ['02_MAISON'] },
    { numero: 7, mot_cle: 'bilan climatiseur Lina Exemplaire', organisme: '', modele: '[date] Bilan climatiseur Lina Exemplaire', chemin: ['02_MAISON'] },
    { numero: 8, mot_cle: 'photo Théo Exemplaire', organisme: '', modele: '[date] Photo Théo Exemplaire', chemin: ['02_MAISON'] },
    { numero: 10, mot_cle: 'photographie Théo Exemplaire', organisme: '', modele: '[date] Photographie Théo Exemplaire', chemin: ['02_MAISON'] },
    { numero: 11, mot_cle: 'devis charpenterie Théo Exemplaire', organisme: '', modele: '[date] Devis charpenterie Théo Exemplaire', chemin: ['02_MAISON'] },
    { numero: 12, mot_cle: 'certificat Théo Exemplaire', organisme: '', modele: '[date] Certificat Théo Exemplaire', chemin: ['01_IDENTITE'] },
    { numero: 9, mot_cle: 'relevé bancaire Théo Exemplaire', organisme: 'Banque fictive', modele: '[date] Releve bancaire Théo Exemplaire', chemin: ['04_BANQUE'] }
  ];
  const ongletsFictifs = {
    types: [
      ['Expression du tableur (sans la personne)', 'Lignes du tableur d\'origine', 'Nombre de lignes', 'Mots courts proposés (type)', 'Mots trop courants dans cette ligne', 'Suffit seul ?', 'Statut', 'Proposé le', 'Correction de Max'],
      ['compte rendu de suivi', '2, 5', '2', 'compte rendu suivi', 'compte rendu', 'Oui', 'À valider', '2026-11-06', ''],
      ['compte rendu', '3', '1', 'compte rendu', 'compte rendu', 'Non (jamais seul)', 'À valider', '2026-11-06', ''],
      ['bilan climatiseur', '4, 7', '2', 'bilan climatiseur', 'bilan', 'Oui', 'À valider', '2026-11-06', ''],
      ['compte rendu climatisation', '6', '1', 'compte rendu climatisation', 'compte rendu', 'Oui', 'À valider', '2026-11-06', ''],
      ['photo', '8', '1', 'photo', 'photo', 'Non (jamais seul)', 'À valider', '2026-11-06', ''],
      ['photographie', '10', '1', 'photographie', '', 'Oui', 'À valider', '2026-11-06', ''],
      ['devis charpenterie', '11', '1', 'devis charpenterie', '', 'Oui', 'À valider', '2026-11-06', ''],
      ['certificat', '12', '1', 'certificat', '', 'Oui', 'À valider', '2026-11-06', ''],
      ['relevé bancaire', '9', '1', 'relevé', 'relevé', 'Oui', 'Corrigé', '2026-11-06', 'relevé bancaire | extrait bancaire (note FICTIVE)']
    ],
    organismes: [
      ['Organisme du tableur', 'Nombre de lignes', 'Mots courts proposés (séparés par |)', 'Remarque', 'Statut', 'Proposé le', 'Correction de Max'],
      ['Garage fictif', '2', 'garage fictif', '', 'À valider', '2026-11-06', ''],
      ['Banque fictive', '1', 'banque fictive', '', 'Refusé', '2026-11-06', '']
    ],
    personnes: [
      ['Nom écrit dans le tableur', 'Nombre de lignes', 'Prénom cherché dans le texte', 'Remarque', 'Statut', 'Proposé le', 'Correction de Max'],
      ['Théo Exemplaire', '5', 'Théo', '', 'Corrigé', '2026-11-06', 'Théo | Théodore (note FICTIVE : le courrier écrit « Théodore », pas « Théo ».)'],
      ['Lina Exemplaire', '3', 'Lina', '', 'À valider', '2026-11-06', '']
    ],
    courants: [
      ['Mot (sans accents ni majuscules)', 'Nombre d\'expressions où il apparaît', 'Jamais seul ?', 'Statut', 'Proposé le', 'Correction de Max'],
      ['compte', '3', 'Oui', 'À valider', '2026-11-06', ''], ['rendu', '3', 'Oui', 'À valider', '2026-11-06', ''],
      ['bilan', '2', 'Oui', 'À valider', '2026-11-06', ''], ['photo', '1', 'Oui', 'À valider', '2026-11-06', ''],
      ['releve', '1', 'Oui', 'À valider', '2026-11-06', ''], ['bancaire', '1', 'Oui', 'Refusé', '2026-11-06', '']
    ]
  };
  // Faux courrier d'un service technique à un collègue (rien de vrai). La date de naissance vient en premier.
  // 09/11/2026 (décision de Max, avant publication) : avant, un faux courrier médical ; plus aucun contenu de santé, même fictif.
  function courrierFictif(client, { bilan = false } = {}) {
    return ['CENTRE TECHNIQUE FICTIF – Service de CLIMATISATION', `Client : ${client}, né le 03/02/1970`,
      'COMPTE RENDU DE SUIVI EN CLIMATISATION', 'Cher collègue,',
      `J'ai revu ${client} pour une fenêtre qui ferme mal. Châssis normal.`,
      'Photographie du portail sans anomalie.',
      bilan ? 'Un bilan climatiseur complet est prévu dans trois mois.' : 'Pas d’examen supplémentaire.',
      'Bien cordialement, Me FICTIF', 'Fait le 14/10/2026'].join('\n');
  }

  await test('mots courts : la correction de Max prime (avant la parenthèse, formes « | »), « Refusé » ignoré', async () => {
    egal(motsCourts.valeurRetenue('Théo', 'Corrigé', 'Théo | Théodore (note)'), 'Théo | Théodore', 'correction avant la parenthèse');
    egal(motsCourts.valeurRetenue('Théo', 'À valider', ''), 'Théo', 'proposition sans correction');
    egal(motsCourts.valeurRetenue('banque fictive', 'Refusé', ''), '', 'refus sans correction');
    egal(motsCourts.valeurRetenue('x', 'Refusé', 'y'), 'y', 'refus avec correction');
    const mots = motsCourts.analyser(ongletsFictifs);
    egal(mots.personnes.find(p => p.nom === 'theo exemplaire').prenoms, ['theo', 'theodore'], 'deux formes du prénom');
    egal(mots.types.get('releve bancaire').alternatives, [['releve', 'bancaire'], ['extrait', 'bancaire']], 'correction du type');
    egal(mots.types.get('compte rendu').seul, false, 'jamais seul');
    egal(mots.organismes.get('banque fictive'), [], 'organisme refusé');
    attendre(mots.courants.has('compte') && !mots.courants.has('bancaire'), 'mots trop courants (refus compris)');
  });

  await test('mots courts : courrier FICTIF de climatisation, prénom long, prénom court, nom de famille seul', async () => {
    const mots = motsCourts.analyser(ongletsFictifs);
    // 1. Prénom long (correction de Max) : une seule proposition, la date de naissance écartée ;
    //    la « photographie » citée en passant ne l'emporte pas sur le titre (mots côte à côte, en haut).
    let p = motsCourts.proposer(courrierFictif('M. Théodore EXEMPLAIRE'), tableurMaison, mots);
    egal([p.raison, p.nom, p.mot_cle, p.personne_incertaine], ['trouve', '2026-10-14 Compte rendu suivi - Théo Exemplaire',
      'compte rendu suivi + prénom', false], 'prénom long');
    attendre(p.score > 5, `score : ${p.score}`);
    // 2. Prénom court : même résultat.
    p = motsCourts.proposer(courrierFictif('M. Théo EXEMPLAIRE'), tableurMaison, mots);
    egal([p.raison, p.nom], ['trouve', '2026-10-14 Compte rendu suivi - Théo Exemplaire'], 'prénom court');
    // 3. Nom de famille seul : personne incertaine, 3 titres proches proposés.
    p = motsCourts.proposer(courrierFictif('M. EXEMPLAIRE'), tableurMaison, mots);
    egal([p.raison, p.personne_incertaine, p.choix.length], ['choix', true, 3], 'nom de famille seul');
    egal(p.choix.map(c => c.nom).sort(), ['2026-10-14 Compte rendu climatisation - Lina Exemplaire', '2026-10-14 Compte rendu suivi - Lina Exemplaire',
      '2026-10-14 Compte rendu suivi - Théo Exemplaire'], 'titres proposés');
    // 4. Le courrier parle aussi d'un « bilan climatiseur » : deux titres proches, Cap ne choisit pas seul.
    p = motsCourts.proposer(courrierFictif('M. Théodore EXEMPLAIRE', { bilan: true }), tableurMaison, mots);
    egal([p.raison, p.choix.map(c => c.nom)], ['choix', ['2026-10-14 Compte rendu suivi - Théo Exemplaire',
      '2026-10-14 Bilan climatiseur - Théo Exemplaire']], 'deux titres proches');
  });

  await test('mots courts : mots trop courants jamais seuls, autre personne écartée, aucun texte, pluriel', async () => {
    const mots = motsCourts.analyser(ongletsFictifs);
    egal(motsCourts.proposer('Compte rendu de Théodore Exemplaire. Photo du portail.', tableurMaison, mots).raison, 'aucun', 'mots courants seuls');
    egal(motsCourts.proposer('Compte rendu de suivi pour Lina Exemplaire', tableurMaison, mots).nom,
      'DATE-A-PRECISER Compte rendu suivi - Lina Exemplaire', 'la bonne personne, l’autre écartée');
    egal(motsCourts.proposer('   ', tableurMaison, mots).raison, 'sans_texte', 'texte vide');
    egal(motsCourts.proposer('Extraits bancaires de Théo, le 02/01/2026', tableurMaison, mots).nom,
      '2026-01-02 Releve bancaire - Théo Exemplaire', 'forme corrigée et pluriel');
    egal(nommageScan.dateDuTexte('Née le 12/05/1980. Courrier du 03/09/2026'), '2026-09-03', 'date de naissance écartée');
  });

  await test('mots courts : même début (8 lettres ou plus) pour le type, y compris un cas où la règle se trompe', async () => {
    const mots = motsCourts.analyser(ongletsFictifs);
    // Le faux document écrit « charpentes », le tableur « charpenterie » : même début, la ligne est trouvée.
    let p = motsCourts.proposer(['DEVIS FICTIF', 'Travaux de charpentes par un artisan diplômé pour Théo Exemplaire.', 'Fait le 02/03/2026'].join(' '), tableurMaison, mots);
    egal([p.raison, p.nom], ['trouve', '2026-03-02 Devis charpenterie - Théo Exemplaire'], 'même début trouvé');
    // La règle se trompe : « certification » a le même début que « certificat ». Cap propose ce
    // titre (FAUX ici) ; il n'est retenu que si Max dit « Oui ».
    p = motsCourts.proposer('Certification qualité FICTIVE de l’atelier de Théo Exemplaire, le 05/05/2026', tableurMaison, mots);
    egal([p.raison, p.nom], ['trouve', '2026-05-05 Certificat - Théo Exemplaire'], 'erreur connue de la règle');
    // Jamais pour les prénoms : une forme plus longue d'un prénom ne compte pas.
    p = motsCourts.proposer('Compte rendu de suivi pour Théodorine Exemplaire', tableurMaison, mots);
    egal([p.raison, p.personne_incertaine], ['choix', true], 'prénom : pas de même début');
    // Mots trop courts (moins de 8 lettres) : pas de même début.
    egal(motsCourts.proposer('Photocopie FICTIVE pour Théo', tableurMaison, mots).raison, 'aucun', 'mot trop court ou trop différent');
    // Les 3 meilleurs candidats sont rendus, avec leur score.
    p = motsCourts.proposer(courrierFictif('M. EXEMPLAIRE'), tableurMaison, mots);
    attendre(p.meilleurs.length === 3 && p.meilleurs.every(c => c.nom && c.mot_cle && c.score > 0), `meilleurs : ${JSON.stringify(p.meilleurs)}`);
  });

  function monterScore(options = {}) {
    const g = monterGoogle();
    g.options.classement = { lireTableurChoisi: async () => tableurMaison,
      lireMotsCourts: options.motsEnPanne ? async () => { throw new Error('mots injoignables FICTIF'); } : async () => motsCourts.analyser(ongletsFictifs) };
    return g;
  }

  await test('écran Google : titre trouvé par score, journal avec mot-clé, score et réponse, jamais le texte', async () => {
    const g = monterScore();
    const e = await scanGoogle(g, [{ texte: courrierFictif('M. Théodore EXEMPLAIRE') }]);
    await terminerPuisVoir(e);
    egal(e.id('scanner-proposition-nom').textContent, '2026-10-14 Compte rendu suivi - Théo Exemplaire.pdf', 'nom proposé');
    attendre(e.id('scanner-proposition-info').textContent.includes('score'), `score absent : ${e.id('scanner-proposition-info').textContent}`);
    attendre(e.id('scanner-proposition-choix').hidden, 'choix affichés pour une seule proposition');
    cliquer(e.id('scanner-proposition-oui'));
    await pause(1500);
    egal((await e.file.lister())[0].nom_valide, '2026-10-14 Compte rendu suivi - Théo Exemplaire.pdf', 'nom retenu après Oui');
    const l = g.lignes[0];
    attendre(/^mot-clé : compte rendu suivi \+ prénom ; score : \d/.test(l.resultat), `résultat : ${l.resultat}`);
    attendre(l.details.includes('recherche : par score') && l.details.includes('réponse : Oui'), `détails : ${l.details}`);
    attendre(l.details.includes('meilleurs candidats : 2026-10-14 Compte rendu suivi - Théo Exemplaire.pdf (compte rendu suivi + prénom, score '),
      `meilleurs candidats absents : ${l.details}`);
    attendre(!l.details.includes('gêne') && !l.resultat.includes('gêne'), 'texte lu recopié dans le journal');
  });

  await test('écran Google : personne choisie d’abord (grande fenêtre), puis 2 titres proches, rien sans choix puis « Oui » ; mots-clés courts en panne', async () => {
    let g = monterScore();
    let e = await scanGoogle(g, [{ texte: courrierFictif('M. EXEMPLAIRE') }]);
    await terminerPuisVoir(e);
    // Nom de famille seul : les titres proches nomment deux personnes → grande fenêtre d'abord, avant tout nom.
    const fenetre = e.id('scanner-choix-emetteur');
    attendre(fenetre.open && e.id('scanner-choix-emetteur-titre').textContent.startsWith('Qui est concerné'), 'fenêtre de la personne absente');
    attendre(e.id('scanner-proposition').hidden, 'nom proposé avant le choix de la personne');
    const casesPersonne = [...e.id('scanner-choix-emetteur-cases').querySelectorAll('button')];
    egal(casesPersonne.map(b => b.textContent).sort(), ['Aucune de ces personnes', 'Lina Exemplaire', 'Théo Exemplaire'], 'cases des personnes');
    attendre(casesPersonne.every(b => b.scrollWidth <= b.clientWidth + 1), 'case trop large pour une ligne');
    cliquer(casesPersonne.find(b => b.textContent === 'Lina Exemplaire'));
    await pause(300);
    attendre(!fenetre.open, 'fenêtre de la personne restée ouverte');
    const boutons = [...e.id('scanner-proposition-choix').querySelectorAll('button')];
    egal(boutons.length, 2, 'deux titres proposés pour la personne choisie');
    attendre(boutons.every(b => b.textContent.includes('- Lina Exemplaire')), 'titre d’une autre personne proposé');
    attendre(!e.id('scanner-proposition-info').textContent.includes('Personne pas sûre'), 'personne dite incertaine après le choix de Max');
    cliquer(e.id('scanner-proposition-oui'));
    await pause(500);
    egal((await e.file.lister()).length, 0, 'enregistré sans titre choisi');
    attendre(e.id('scanner-proposition-statut').textContent.includes('Touche d’abord'), 'consigne absente');
    cliquer(boutons[1]);
    egal(boutons[1].getAttribute('aria-pressed'), 'true', 'titre touché non marqué');
    cliquer(e.id('scanner-proposition-oui'));
    await pause(1500);
    const attendu = `${boutons[1].textContent}`;
    egal((await e.file.lister())[0].nom_valide, attendu, 'titre choisi retenu');
    const l = g.lignes[0];
    attendre(l.resultat.startsWith('choix entre 2 titres') && l.details.includes('titre touché : n° 2') && /personne : choisie par Max \(n° \d parmi 2\)/.test(l.details),
      `journal : ${l.resultat} | ${l.details}`);
    // Mots-clés courts illisibles : recherche stricte, et le journal le dit.
    g = monterScore({ motsEnPanne: true });
    e = await scanGoogle(g, [{ texte: courrierFictif('M. Théodore EXEMPLAIRE') }]);
    await terminerPuisVoir(e);
    cliquer(e.id('scanner-proposition-daccord'));
    await pause(1500);
    attendre(g.lignes[0].details.includes('recherche : stricte (mots-clés courts non lus : mots injoignables FICTIF)'), `journal : ${g.lignes[0].details}`);
  });


  await test('règle de nommage : ordre, émetteur absent, caractères remplacés, mois seul, numéro (2)', async () => {
    egal(nommageScan.composerNom({ date: '2026-02-03', type: 'Avis d’imposition', emetteur: 'Finances FICTIVES', personne: 'Jean et Jeanne Fictif' }),
      '2026-02-03 Avis d’imposition - Finances FICTIVES - Jean et Jeanne Fictif', 'ordre des éléments');
    egal(nommageScan.composerNom({ date: '2026-05-05', type: 'Facture', personne: 'Jeanne Exemple' }), '2026-05-05 Facture - Jeanne Exemple', 'émetteur absent');
    egal(nommageScan.composerNom({ type: 'Attestation', personne: 'Jean Fictif' }), 'DATE-A-PRECISER Attestation - Jean Fictif', 'sans date');
    egal(nommageScan.nettoyerNom('Relevé 03/2026: « Banque » ? *Fictive*. '), 'Relevé 03-2026 - Banque Fictive', 'caractères remplacés');
    egal(nommageScan.moisDuTexte('Relevé du mois de mars 2026, FICTIF'), '2026-03', 'mois en toutes lettres');
    egal(nommageScan.moisDuTexte('Période 04/2025 FICTIVE'), '2025-04', 'mois en chiffres');
    egal(nommageScan.moisDuTexte('Aucune date FICTIVE'), '', 'pas de mois inventé');
    egal(nommageScan.nomUnique('2026-01-12 Attestation - Jean Fictif', ['2026-01-12 attestation - jean fictif.pdf', '2026-01-12 Attestation - Jean Fictif (2).pdf']),
      '2026-01-12 Attestation - Jean Fictif (3).pdf', 'numéro (3)');
    // Sans date complète dans le texte, le mois seul sert ; le type vient de la colonne « Type de document ».
    const mots = motsCourts.analyser(ongletsFictifs);
    const lignes = [{ numero: 20, mot_cle: 'relevé bancaire Théo Exemplaire', organisme: '', type: 'Relevé de compte', modele: '[date] Releve Théo Exemplaire', chemin: ['04_BANQUE'] }];
    egal(motsCourts.proposer('Relevé bancaire FICTIF de Théo pour mars 2026', lignes, mots).nom, '2026-03 Relevé de compte - Théo Exemplaire', 'mois seul et colonne Type');
    // Ligne sans personne dans le mot-clé : la personne vient du modèle de titre.
    const sansPersonne = [{ numero: 21, mot_cle: 'fiche de paie FICTIVE', organisme: '', type: 'Fiche de paie', modele: '[date] Fiche de paie Lina Exemplaire', chemin: ['03_TRAVAIL'] }];
    const typesPaie = { ...ongletsFictifs, types: [...ongletsFictifs.types, ['fiche de paie fictive', '21', '1', 'fiche paie', '', 'Oui', 'À valider', '2026-11-06', '']] };
    const p = motsCourts.proposer('Fiche de paie FICTIVE de Lina, le 31/01/2026', sansPersonne, motsCourts.analyser(typesPaie));
    egal([p.nom, p.personne_incertaine], ['2026-01-31 Fiche de paie - Lina Exemplaire', false], 'personne du modèle');
    egal(motsCourts.proposer('Fiche de paie FICTIVE de Théo, le 31/01/2026', sansPersonne, motsCourts.analyser(typesPaie)).raison, 'aucun', 'autre personne écartée');
  });

  await test('écran Google : sans date, « Prendre la date du scan » seulement si Max le touche ; caractères remplacés montrés avant Oui ; description', async () => {
    let g = monterScore();
    let e = await scanGoogle(g, [{ texte: 'Compte rendu de suivi FICTIF pour Théo Exemplaire, sans aucune date' }]);
    await terminerPuisVoir(e);
    egal(e.id('scanner-proposition-nom').textContent, 'DATE-A-PRECISER Compte rendu suivi - Théo Exemplaire.pdf', 'nom sans date');
    attendre(!e.id('scanner-proposition-date-scan').hidden, 'bouton de la date du scan absent');
    const jour = /\((\d{2})\/(\d{2})\/(\d{4})\)/.exec(e.id('scanner-proposition-date-scan').textContent).slice(1).reverse().join('-');
    cliquer(e.id('scanner-proposition-date-scan'));
    egal(e.id('scanner-proposition-nom').textContent, `${jour} Compte rendu suivi - Théo Exemplaire.pdf`, 'date du scan prise');
    egal((await e.file.lister()).length, 0, 'enregistré avant le Oui');
    cliquer(e.id('scanner-proposition-oui'));
    await pause(1500);
    const fiche = (await e.file.lister())[0];
    egal(fiche.nom_valide, `${jour} Compte rendu suivi - Théo Exemplaire.pdf`, 'nom retenu');
    attendre(fiche.details.includes('Date du nom : date du scan, choisie par Max') && fiche.details.includes('Émetteur : non reconnu')
      && fiche.details.some(d => d.startsWith('Mot-clé : compte rendu suivi + prénom (score ')), `description : ${JSON.stringify(fiche.details)}`);
    attendre(!fiche.details.join(' ').includes('sans aucune date'), 'texte lu dans la description');
    // Date lisible : pas de bouton.
    g = monterScore();
    e = await scanGoogle(g, [{ texte: courrierFictif('M. Théodore EXEMPLAIRE') }]);
    await terminerPuisVoir(e);
    attendre(e.id('scanner-proposition-date-scan').hidden, 'bouton de la date du scan affiché alors qu’une date est lue');
    // Nom modifié par Max avec des caractères interdits : remplacés, montrés, puis Oui.
    cliquer(e.id('scanner-proposition-modifier'));
    e.id('scanner-proposition-champ').value = '2026-10-14 Suivi: Théo/Exemplaire ?';
    cliquer(e.id('scanner-proposition-oui'));
    await pause(300);
    egal((await e.file.lister()).length, 0, 'enregistré sans montrer le nom corrigé');
    egal(e.id('scanner-proposition-champ').value, '2026-10-14 Suivi - Théo-Exemplaire', 'nom corrigé montré');
    cliquer(e.id('scanner-proposition-oui'));
    await pause(1500);
    egal((await e.file.lister())[0].nom_valide, '2026-10-14 Suivi - Théo-Exemplaire.pdf', 'nom corrigé retenu');
  });
  // ---------- 06/11/2026 : émetteur (Dictionnaire général FICTIF, trois onglets) ----------
  const dicoFictif = {
    'Ancienne liste': [
      ['First Name', 'Middle Name', 'Last Name', 'Name Prefix', 'Nickname', 'Organization Name', 'Organization Title', 'Notes', 'Birthday',
        'E-mail 1 - Value', 'Phone 1 - Value', 'Address 1 - City', 'Address 1 - Postal Code'],
      ['Jean', '', 'Fictif', 'Me', '', '', 'Notaire FICTIF', 'note FICTIVE 06 11 11 11 11', '1970-01-01', 'jean.fictif@exemple.test', '04 00 00 00 01', 'Villefictive', '99000'],
      ['Jeanne', '', 'Fictif', '', '', '', '', '', '', '', '04 00 00 00 02', '', ''],
      ['Banque', '', '', '', '', '', '', '', '', '', '04 00 00 00 03', '', ''],
      ['Théo', '', 'Exemplaire', '', '', '', '', '', '', '', '04 00 00 00 09', '', ''],
      ['', '', '', '', '', 'Cabinet Fictif des Lilas', '', '', '', '', '04 00 00 00 05', '', ''],
      ['Marc', '', 'Dupontel', '', '', '', '', '', '', '', '04 00 00 00 06', '', ''],
      ['Luc', '', 'Dupontel', '', '', '', '', '', '', '', '04 00 00 00 06', '', '']
    ],
    'Tri contacts': [
      ['Nom dans les contacts', 'Organisation / étiquette', 'Téléphone', 'Mail', 'Note d’origine', 'Catégorie', 'Décision', 'Nom propre pour le dictionnaire', 'Rôle / lien avec Max', 'Remarques'],
      ['Me Fictif Jean', '', '04 00 00 00 01', '', 'note FICTIVE', 'Maison FICTIVE', '', 'Jean Fictif', 'Notaire', '']
    ],
    Dictionnaire: [
      ['Prénom', 'Nom', 'Type', 'Rôle', 'Lien avec Max', 'Appellations et surnoms', 'Coordonnées', 'Téléphone', 'Mail', 'Domaine', 'Note pour IA',
        'Date de naissance / anniversaire', 'Adresse postale', 'Deuxième téléphone', 'Deuxième mail', 'Fonction / titre', 'Site web', 'Note'],
      ['Jean', 'Fictif', 'Personne', 'Notaire FICTIF', 'Notaire de Théo', '', '', '04 00 00 00 01', '', 'Maison', 'NE PAS LIRE 04 77 77 77 77',
        '01/01/1970', '1 rue FICTIVE 99000 Villefictive', '', '', 'Maître', '', 'note FICTIVE 04 88 88 88 88'],
      ['Lina', 'Exemplaire', 'Personne', 'Sœur FICTIVE', '', '', '', '04 00 00 00 08', '', 'Famille', '', '', '', '', '', '', '', '']
    ]
  };
  const personnesExclues = { noms: ['Théo Exemplaire', 'Lina Exemplaire'] };

  await test('émetteur : colonnes de notes et dates de naissance jamais lues', async () => {
    egal(emetteur.colonnesALire('Ancienne liste', dicoFictif['Ancienne liste'][0]), [0, 1, 2, 3, 4, 5, 6, 9, 10, 11, 12], 'ancienne liste');
    egal(emetteur.colonnesALire('Tri contacts', dicoFictif['Tri contacts'][0]), [0, 1, 2, 3, 5, 7, 8], 'tri contacts');
    egal(emetteur.colonnesALire('Dictionnaire', dicoFictif.Dictionnaire[0]), [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 12, 13, 14, 15], 'dictionnaire');
    const entrees = emetteur.analyser(dicoFictif);
    // Un numéro écrit seulement dans une colonne de notes ne fait reconnaître personne.
    for (const texte of ['Rappeler le 06 11 11 11 11 FICTIF', 'Tél. 04 77 77 77 77 FICTIF', 'Tél. 04 88 88 88 88 FICTIF']) {
      egal(emetteur.reconnaitre(texte, entrees, personnesExclues).etat, 'aucun', `numéro de note : ${texte}`);
    }
  });

  await test('émetteur : nom exact et seul → certain (Dictionnaire prioritaire) ; souple, homonymes, téléphone partagé ou seul → cases', async () => {
    const entrees = emetteur.analyser(dicoFictif);
    let r = emetteur.reconnaitre('Courrier FICTIF du Me Jean Fictif concernant Théo Exemplaire', entrees, personnesExclues);
    egal([r.etat, r.candidats.length, r.candidats[0].onglet, r.candidats[0].numero, r.candidats[0].complet], ['certain', 1, 'Dictionnaire', 2, 'Jean Fictif'], 'nom exact');
    attendre(Object.keys(r.candidats[0]).every(k => ['onglet', 'numero', 'complet', 'court', 'score', 'exact'].includes(k)), 'indice rendu avec le candidat');
    r = emetteur.reconnaitre('Courrier FICTIF du Me Jean Fictiff', entrees, personnesExclues);
    egal([r.etat, r.candidats[0].complet], ['choix', 'Jean Fictif'], 'graphie souple : jamais de choix automatique');
    r = emetteur.reconnaitre('Avis FICTIF du Maître Fictif', entrees, personnesExclues);
    egal([r.etat, r.candidats.map(c => c.complet).sort()], ['choix', ['Jean Fictif', 'Jeanne Fictif']], 'titre + nom de famille partagé');
    r = emetteur.reconnaitre('Appeler le 04 00 00 00 06 FICTIF', entrees, personnesExclues);
    egal([r.etat, r.candidats.map(c => c.complet).sort()], ['choix', ['Luc Dupontel', 'Marc Dupontel']], 'téléphone partagé');
    r = emetteur.reconnaitre('Contact FICTIF : 04.00.00.00.05', entrees, personnesExclues);
    egal([r.etat, r.candidats.map(c => c.complet)], ['choix', ['Cabinet Fictif des Lilas']], 'un téléphone seul ne décide jamais');
    r = emetteur.reconnaitre('Écrire à jean.fictif@exemple.test FICTIF', entrees, personnesExclues);
    egal([r.etat, r.candidats[0].complet], ['choix', 'Jean Fictif'], 'un mail seul ne décide jamais');
  });

  await test('émetteur : famille et Max jamais reconnus (nom complet, coordonnées), mots génériques et indices faibles seuls → rien', async () => {
    const entrees = emetteur.analyser(dicoFictif);
    for (const texte of ['Courrier FICTIF de Lina Exemplaire', 'Tél. 04 00 00 00 08 FICTIF', 'Théo Exemplaire, tél. 04 00 00 00 09 FICTIF',
      'Votre Banque FICTIVE', 'Villefictive 99000, rue FICTIVE', 'Maître Banque FICTIF']) {
      egal(emetteur.reconnaitre(texte, entrees, personnesExclues).etat, 'aucun', texte);
    }
    // Les indices faibles départagent : même nom de famille, la ville de l'entrée la fait passer devant.
    const r = emetteur.reconnaitre('Avis FICTIF du Maître Fictif, Villefictive', entrees, personnesExclues);
    egal(r.candidats[0].complet, 'Jean Fictif', 'indice faible pour départager');
  });

  await test('émetteur : forme courte pour les cases, allongée si deux formes se ressemblent', async () => {
    egal(emetteur.formeCourte('Jean-Baptiste Fictif-Exemplaire'), 'J. Fictif-Exemplaire', 'personne au nom long');
    egal(emetteur.formeCourte('Centre FICTIF de Sport des Lilas Fleuris'), 'CFSLF', 'organisme long');
    egal(emetteur.formeCourte('Jean Fictif'), 'Jean Fictif', 'nom court gardé');
    const entrees = emetteur.analyser({ Dictionnaire: [['Prénom', 'Nom', 'Type'],
      ['Jean-Baptiste', 'Fictif-Exemplaire', 'Personne'], ['Jean-Bernard', 'Fictif-Exemplaire', 'Personne']] });
    const r = emetteur.reconnaitre('Avis FICTIF du Me Fictif-Exemplaire', entrees, {});
    egal(r.candidats.map(c => c.court).sort(), ['Jean-Baptiste Fictif-Exemplaire', 'Jean-Bernard Fictif-Exemplaire'], 'formes courtes allongées');
  });

  await test('émetteur : appellations lues dans les trois onglets ; appellation exacte → reconnue ; famille jamais', async () => {
    egal(emetteur.colonnesALire('Ancienne liste', ['First Name', 'Notes', 'Appellations et surnoms']), [0, 2], 'ancienne liste : appellations lues, notes jamais');
    egal(emetteur.colonnesALire('Tri contacts', ['Nom dans les contacts', 'Remarques', 'Appellations et surnoms']), [0, 2], 'tri contacts : appellations lues');
    const onglets = {
      'Ancienne liste': [['First Name', 'Last Name', 'Notes', 'Appellations et surnoms'],
        ['P.', 'Fictivo-Exemple', 'note FICTIVE', 'Maître Paul FICTIVO'],
        ['Doc', '', '', 'Doc']],
      'Tri contacts': [['Nom dans les contacts', 'Appellations et surnoms'], ['Cabinet FICTIF', 'Maison FICTIVE des Lilas']],
      Dictionnaire: [['Prénom', 'Nom', 'Type', 'Domaine', 'Appellations et surnoms'], ['Lina', 'Exemplaire', 'Personne', 'Famille', 'Tata Linou']]
    };
    const entrees = emetteur.analyser(onglets);
    // Les colonnes de nom ne correspondent pas au scan, mais l'appellation écrite par Max, oui.
    let r = emetteur.reconnaitre('DEVIS FICTIF\nMaître Paul FICTIVO\nPour Théo Exemplaire', entrees, personnesExclues);
    egal([r.etat, r.candidats[0].onglet, r.candidats[0].numero], ['certain', 'Ancienne liste', 2], 'appellation exacte');
    egal(r.diagnostic.candidats.appellation, 1, 'diagnostic : appellation');
    r = emetteur.reconnaitre('Courrier FICTIF de la Maison FICTIVE des Lilas', entrees, personnesExclues);
    egal([r.etat, r.candidats[0].onglet], ['certain', 'Tri contacts'], 'appellation dans tri contacts');
    // Une appellation d'un seul mot trop court ne compte pas ; une appellation de la famille jamais.
    egal(emetteur.reconnaitre('Doc FICTIF', entrees, personnesExclues).etat, 'aucun', 'appellation trop courte');
    egal(emetteur.reconnaitre('Mot FICTIF de Tata Linou', entrees, personnesExclues).etat, 'aucun', 'appellation de la famille');
  });

  await test('émetteur : fiche « Me Nom » et prénom entre le titre et le nom → cases ; nom coupé par d’autres mots → rien, et le diagnostic le montre', async () => {
    const entrees = emetteur.analyser({ 'Ancienne liste': [['First Name', 'Last Name'], ['Me Fictivoz', '']] });
    let r = emetteur.reconnaitre('Devis FICTIF de Me Fictivoz', entrees, {});
    egal(r.etat, 'certain', 'titre juste avant le nom');
    r = emetteur.reconnaitre('Devis FICTIF du Maître Luc FICTIVOZ', entrees, {});
    egal([r.etat, r.candidats.length, r.diagnostic.candidats.souple], ['choix', 1, 1], 'prénom entre les deux : jamais certain');
    r = emetteur.reconnaitre('Devis FICTIF du Maître Luc Jean Marc FICTIVOZ', entrees, {});
    egal(r.etat, 'aucun', 'trop de mots entre le titre et le nom');
    // Cas du test c16 (FICTIF) : la lecture du texte a glissé une adresse entre le prénom et le nom.
    const fiche = emetteur.analyser({ 'Ancienne liste': [['First Name', 'Last Name', 'Phone 1 - Value'], ['Paul', 'Fictivo', '04 00 00 00 07']] });
    r = emetteur.reconnaitre('Maître Paul\n12 rue FICTIVE 99000 Villefictive\nFICTIVO\nDevis', fiche, {});
    egal(r.etat, 'aucun', 'nom coupé par la lecture');
    egal(r.diagnostic, { lues: { 'Ancienne liste': 1, 'Tri contacts': 0, Dictionnaire: 0 }, titres: 1, telephones: 0,
      candidats: { telephone_mail: 0, exact: 0, appellation: 0, souple: 0 }, famille_ecartee: 0 }, 'diagnostic en nombres');
  });

  await test('dates : formes en plus, confusions de lecture corrigées (dans une date seulement), année sur 2 chiffres jamais acceptée, diagnostic en nombres', async () => {
    const d = t => nommageScan.analyserDates(t);
    egal(d('Fait le 17 / 05 / 2025, FICTIF').date, '2025-05-17', 'espaces autour des séparateurs');
    egal(d('Le 12 sept. 2026 FICTIF').date, '2026-09-12', 'mois abrégé avec point');
    egal(d('Le 3 févr 2026 FICTIF').date, '2026-02-03', 'mois abrégé avec accent');
    egal(d('Le 17mai 2025 FICTIF').date, '2025-05-17', 'jour collé au mois');
    egal(d('Le 1er déc. 2025 FICTIF').date, '2025-12-01', '1er et décembre abrégé');
    let r = d('Devis FICTIF du 17/05/2O25');
    egal([r.date, r.corrigee, r.diagnostic.corrections, r.diagnostic.choisie], ['2025-05-17', true, 1, 'chiffres'], 'lettre O dans l’année');
    r = d('Devis FICTIF du 17 mal 2025');
    egal([r.date, r.corrigee], ['2025-05-17', true], '« mal » lu pour « mai »');
    egal(d('Devis FICTIF du l7/05/2025').date, '2025-05-17', 'lettre l pour 1');
    r = d('Devis FICTIF du 17/05/25');
    egal([r.date, r.diagnostic.non_acceptees, r.diagnostic.choisie], ['', 1, 'aucune'], 'année sur 2 chiffres jamais acceptée');
    r = d('Client FICTIF né le 01/02/1980. Fait le 03/04/2026');
    egal([r.date, r.diagnostic.rejetees.naissance, r.diagnostic.candidates.chiffres], ['2026-04-03', 1, 2], 'naissance écartée et comptée');
    r = d('Le 31/02/2026 FICTIF');
    egal([r.date, r.diagnostic.rejetees.impossible], ['', 1], 'date impossible comptée');
    // Jamais une date inventée : des lettres seules ou un numéro de téléphone ne sont pas des dates.
    egal(d('Code FICTIF ol/il/oooo').date, '', 'lettres seules');
    egal(d('Tél. 04.78.12.34.56 FICTIF').date, '', 'numéro de téléphone');
    egal(d('Mot FICTIF : il mal, mal 2026').date, '', '« mal » sans jour');
    egal(d('Relevé FICTIF de sept. 2026').mois, '', 'mois abrégé sans jour : pas de date complète (le mois seul reste en toutes lettres)');
  });

  await test('écran Google : date corrigée montrée et signalée, diagnostic de la date au journal sans la date', async () => {
    const g = monterScore();
    const e = await scanGoogle(g, [{ texte: courrierFictif('M. Théodore EXEMPLAIRE').replace('Fait le 14/10/2026', 'Fait le 14/1O/2026') }]);
    await terminerPuisVoir(e);
    egal(e.id('scanner-proposition-nom').textContent, '2026-10-14 Compte rendu suivi - Théo Exemplaire.pdf', 'date corrigée dans le nom proposé');
    attendre(e.id('scanner-proposition-info').textContent.includes('correction de lecture'), `correction non signalée : ${e.id('scanner-proposition-info').textContent}`);
    cliquer(e.id('scanner-proposition-oui'));
    await pause(1500);
    const fiche = (await e.file.lister())[0];
    attendre(fiche.details.includes('Date du nom : lue sur le document, avec une correction de lecture'), `description : ${JSON.stringify(fiche.details)}`);
    const diag = g.lignes[0].details.slice(g.lignes[0].details.indexOf('diagnostic date'), g.lignes[0].details.indexOf('choisie : ') + 'choisie : chiffres'.length);
    attendre(diag.startsWith('diagnostic date : candidates 2 (chiffres 2, lettres 0, iso 0) ; rejetées 1 (impossible 0, naissance 1) ; formes non acceptées 0 ; corrections de lecture 1 ; choisie : chiffres'),
      `diagnostic : ${diag}`);
    attendre(!/\d{3,}|\d\/\d/.test(diag), 'une date apparaît dans le diagnostic');
  });

  function monterEmetteur() {
    const g = monterScore();
    g.options.classement.lireDictionnaire = async () => emetteur.analyser(dicoFictif);
    return g;
  }
  function courrierAvecEmetteur(signature) {
    return courrierFictif('M. Théodore EXEMPLAIRE').replace('Me FICTIF', signature);
  }

  await test('écran Google : émetteur certain dans le nom, journal (onglet et numéro seulement) et description', async () => {
    const g = monterEmetteur();
    const avant = Object.keys(localStorage).sort();
    const e = await scanGoogle(g, [{ texte: courrierAvecEmetteur('Me Jean Fictif, tél. 04 00 00 00 01') }]);
    await terminerPuisVoir(e);
    attendre(!e.id('scanner-choix-emetteur').open, 'fenêtre de choix ouverte alors que l’émetteur est certain');
    egal(e.id('scanner-proposition-nom').textContent, '2026-10-14 Compte rendu suivi - Jean Fictif - Théo Exemplaire.pdf', 'émetteur dans le nom');
    cliquer(e.id('scanner-proposition-oui'));
    await pause(1500);
    const fiche = (await e.file.lister())[0];
    attendre(fiche.details.includes('Émetteur : Jean Fictif'), `description : ${JSON.stringify(fiche.details)}`);
    const l = g.lignes[0];
    attendre(l.details.includes('émetteur : Dictionnaire n° 2 (reconnu)'), `journal : ${l.details}`);
    attendre(/diagnostic émetteur : lues 7 \/ 1 \/ 2 \(ancienne liste \/ tri contacts \/ dictionnaire\) ; titres 1 ; téléphones 1 ; candidats tél\.\/mail 3, exact 3, appellation 0, souple 0 ; famille écartée 2/.test(l.details),
      `diagnostic : ${l.details}`);
    attendre(!l.details.includes('04 00 00 00 01') && !fiche.details.join(' ').includes('04 00'), 'indice (téléphone) écrit au journal ou dans la description');
    egal(Object.keys(localStorage).sort(), avant, 'quelque chose du Dictionnaire écrit dans le stockage du téléphone');
  });

  await test('écran Google : hésitation → grande fenêtre de choix AVANT le nom (une ligne par case), puis « Aucun de ceux-là »', async () => {
    let g = monterEmetteur();
    let e = await scanGoogle(g, [{ texte: courrierAvecEmetteur('Maître Fictif') }]);
    cliquer(e.id('scanner-terminer'));
    await pause(300);
    const fenetre = e.id('scanner-choix-emetteur');
    attendre(fenetre.open, 'fenêtre de choix absente');
    attendre(e.id('scanner-proposition').hidden, 'nom proposé avant le choix de l’émetteur');
    const cases = [...e.id('scanner-choix-emetteur-cases').querySelectorAll('button')];
    egal(cases.map(b => b.textContent).sort(), ['Aucun de ceux-là', 'Jean Fictif', 'Jeanne Fictif'], 'cases');
    for (const b of cases) {
      attendre(b.scrollWidth <= b.clientWidth + 1, `texte coupé ou trop large : ${b.textContent}`);
      attendre(b.getBoundingClientRect().height < parseFloat(b.style.fontSize) * 2.2 + 40, `texte sur deux lignes : ${b.textContent}`);
    }
    attendre(!cases.some(b => /\d{2} \d{2}|@|Villefictive/.test(b.textContent)), 'indice affiché dans une case');
    cliquer(cases.find(b => b.textContent === 'Jeanne Fictif'));
    await pause(300);
    attendre(!fenetre.open, 'fenêtre restée ouverte');
    egal(e.id('scanner-proposition-nom').textContent, '2026-10-14 Compte rendu suivi - Jeanne Fictif - Théo Exemplaire.pdf', 'nom après le choix');
    cliquer(e.id('scanner-proposition-oui'));
    await pause(1500);
    attendre(g.lignes[0].details.includes('émetteur : Ancienne liste n° 3 (choisi par Max parmi 2)'), `journal : ${g.lignes[0].details}`);
    // « Aucun de ceux-là » : nom sans émetteur, la description le note.
    g = monterEmetteur();
    e = await scanGoogle(g, [{ texte: courrierAvecEmetteur('Maître Fictif') }]);
    cliquer(e.id('scanner-terminer'));
    await pause(300);
    cliquer([...e.id('scanner-choix-emetteur-cases').querySelectorAll('button')].find(b => b.textContent === 'Aucun de ceux-là'));
    await pause(300);
    egal(e.id('scanner-proposition-nom').textContent, '2026-10-14 Compte rendu suivi - Théo Exemplaire.pdf', 'nom sans émetteur');
    cliquer(e.id('scanner-proposition-oui'));
    await pause(1500);
    attendre((await e.file.lister())[0].details.includes('Émetteur : aucun de ceux-là (choix de Max)'), 'description sans la mention');
    attendre(g.lignes[0].details.includes('émetteur : aucun de ceux-là (choix de Max parmi 2)'), `journal : ${g.lignes[0].details}`);
  });

  await test('écran Google : personne choisie seule → un seul titre ; « Aucune de ces personnes » → aucun nom', async () => {
    let g = monterScore();
    let e = await scanGoogle(g, [{ texte: courrierFictif('M. EXEMPLAIRE') }]);
    await terminerPuisVoir(e);
    cliquer([...e.id('scanner-choix-emetteur-cases').querySelectorAll('button')].find(b => b.textContent === 'Théo Exemplaire'));
    await pause(300);
    egal(e.id('scanner-proposition-nom').textContent, '2026-10-14 Compte rendu suivi - Théo Exemplaire.pdf', 'un seul titre pour la personne choisie');
    attendre(e.id('scanner-proposition-choix').hidden, 'boutons de titres affichés pour un seul titre');
    cliquer(e.id('scanner-proposition-non'));
    await pause(1500);
    g = monterScore();
    e = await scanGoogle(g, [{ texte: courrierFictif('M. EXEMPLAIRE') }]);
    await terminerPuisVoir(e);
    cliquer([...e.id('scanner-choix-emetteur-cases').querySelectorAll('button')].find(b => b.textContent === 'Aucune de ces personnes'));
    await pause(300);
    attendre(!e.id('scanner-proposition-daccord').hidden && e.id('scanner-proposition-oui').hidden, 'nom proposé malgré « Aucune de ces personnes »');
    cliquer(e.id('scanner-proposition-daccord'));
    await pause(1500);
    egal(g.lignes[0].resultat, 'aucune des personnes proposées (choix de Max)', 'journal');
    attendre(g.lignes[0].details.includes('personne : aucune de celles proposées (choix de Max parmi 2)'), `journal : ${g.lignes[0].details}`);
  });

  await test('écran Google : dans le même scan, un membre FICTIF de la famille reconnu comme personne, jamais comme émetteur', async () => {
    const g = monterEmetteur();
    const texte = ['Courrier FICTIF de Lina Exemplaire, tél. 04 00 00 00 08', 'COMPTE RENDU DE SUIVI', 'Pour Lina Exemplaire, revue par le Me Jean Fictif.',
      'Fait le 14/10/2026'].join('\n');
    const e = await scanGoogle(g, [{ texte }]);
    await terminerPuisVoir(e);
    attendre(!e.id('scanner-choix-emetteur').open, 'fenêtre de choix ouverte');
    egal(e.id('scanner-proposition-nom').textContent, '2026-10-14 Compte rendu suivi - Jean Fictif - Lina Exemplaire.pdf', 'famille = personne, émetteur = Me FICTIF');
    // Sans le médecin, la famille seule n'est jamais l'émetteur : nom sans émetteur.
    const g2 = monterEmetteur();
    const e2 = await scanGoogle(g2, [{ texte: texte.replace(', revue par le Me Jean Fictif', '') }]);
    await terminerPuisVoir(e2);
    attendre(!e2.id('scanner-choix-emetteur').open, 'la famille proposée comme émetteur');
    egal(e2.id('scanner-proposition-nom').textContent, '2026-10-14 Compte rendu suivi - Lina Exemplaire.pdf', 'personne reconnue, aucun émetteur');
    cliquer(e2.id('scanner-proposition-oui'));
    await pause(1500);
    attendre(g2.lignes[0].details.includes('émetteur : aucun trouvé'), `journal : ${g2.lignes[0].details}`);
  });

  await test('écran Google : lecture échouée page par page, aucun texte lu, tableur non lu, annulation', async () => {
    let g = monterGoogle();
    let e = await scanGoogle(g, [{ texte: 'SYNDIC FICTIF' }, { lu: false, texte: '' }]);
    attendre(e.id('scanner-message').textContent.includes('Lecture échouée : page 2'), `échec non signalé : ${e.id('scanner-message').textContent}`);
    await terminerPuisVoir(e);
    attendre(e.id('scanner-proposition-info').textContent.includes('lecture échouée : page 2'), 'échec absent de la fenêtre');
    cliquer(e.id('scanner-proposition-non'));
    await pause(1500);
    attendre(g.lignes[0].details.includes('pages lues : 1 sur 2') && g.lignes[0].details.includes('lecture échouée : page 2'), `journal : ${g.lignes[0].details}`);
    g = monterGoogle();
    e = await scanGoogle(g, [{ lu: false, texte: '' }]);
    await terminerPuisVoir(e);
    attendre(e.id('scanner-proposition-info').textContent.includes('Lecture du texte échouée sur toutes les pages'), 'échec total non dit');
    cliquer(e.id('scanner-proposition-daccord'));
    await pause(1500);
    egal(g.lignes[0].resultat, 'lecture échouée', 'journal : lecture échouée');
    g = monterGoogle();
    e = await scanGoogle(g, [{ texte: '   ' }]);
    await terminerPuisVoir(e);
    cliquer(e.id('scanner-proposition-daccord'));
    await pause(1500);
    egal(g.lignes[0].resultat, 'aucun texte lu', 'journal : aucun texte lu');
    g = monterGoogle({ tableurEnPanne: true });
    e = await scanGoogle(g, [{ texte: 'SYNDIC FICTIF' }]);
    await terminerPuisVoir(e);
    attendre(e.id('scanner-proposition-info').textContent.includes('tableur injoignable FICTIF'), 'panne du tableur non dite');
    cliquer(e.id('scanner-proposition-daccord'));
    await pause(1500);
    egal(g.lignes[0].resultat, 'tableur non lu (tableur injoignable FICTIF)', 'journal : tableur non lu');
    g = monterGoogle();
    e = await demarrerEcran(g.options);
    cliquer(e.id('ouvrir-scanner'));
    await pause(200);
    egal((await e.ecran.recevoirScanGoogle({ annule: true })).pages, 0, 'annulation');
    attendre(e.id('scanner-message').textContent.includes('annulé'), 'annulation non dite');
    attendre(e.id('scanner-proposition').hidden, 'proposition après annulation');
  });

  await test('écran Google : diagnostic par page (taille, rotation, blocs, lignes, caractères) dans la fenêtre et le journal, jamais le texte', async () => {
    const g = monterGoogle();
    const e = await scanGoogle(g, [
      { texte: 'SYNDIC FICTIF texte secret FICTIF', largeur: 2480, hauteur: 3508, rotation: 90, rotation_exif: 0, blocs: 3, lignes: 7, caracteres: 36, essais: 4 },
      { lu: false, texte: '' },
      { texte: 'Autre page FICTIVE' }
    ]);
    await terminerPuisVoir(e);
    const diag = e.id('scanner-proposition-diagnostic');
    attendre(!diag.hidden, 'diagnostic caché');
    attendre(diag.textContent.includes('page 1 : 2480×3508 px, rotation 90° (photo 0°), 3 bloc(s), 7 ligne(s), 36 caractère(s), 4 sens essayés'), `diagnostic : ${diag.textContent}`);
    attendre(diag.textContent.includes('page 2 : lecture échouée') && diag.textContent.includes('page 3 : diagnostic absent'), `pages 2 et 3 : ${diag.textContent}`);
    attendre(!diag.textContent.includes('secret'), 'texte lu dans le diagnostic');
    cliquer(e.id('scanner-proposition-non'));
    await pause(1500);
    const details = g.lignes[0].details;
    attendre(details.includes('diagnostic : page 1 : 2480×3508 px, rotation 90°') && details.includes('page 2 : lecture échouée'), `journal : ${details}`);
    attendre(!details.includes('secret') && !details.includes('SYNDIC FICTIF'), 'texte lu dans le journal');
  });

  await test('écran : sans la coque Android, pas de bouton du scanner de Google', async () => {
    const e = await demarrerEcran({ scannerAndroid: null });
    attendre(e.id('scanner-google').hidden, 'bouton visible hors de la coque');
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
