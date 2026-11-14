'use strict';

// 14/11/2026 (accord de Max, P7a et P7b) : les TEXTES des messages d'UNE personne connue, pour un document « Dialogue » (.txt)
// dans le Drive du COMPTE CAP, sous-dossier « Dialogue » du dossier de cette personne (« MMS des relations », P5).
// P7a, P7b : LIRE et PRÉPARER (rien écrit). 14/11/2026 (accord de Max, P7c) : copier, SEULEMENT après « Oui, copier » : crée
// « Dialogue » (dossier VIDE, marqué, daté) DANS le dossier de la personne si besoin, puis UN fichier .txt NOUVEAU par la porte
// unique du compte Cap (envoyerFichier : création seulement) ; relit juste avant (rien de copié depuis la question) ; relit le
// fichier APRÈS (nom, dossier, marques, contenu identique à ce qui était préparé). Rien n'est effacé, ni remplacé, ni déplacé.
// Décisions de Max (14/11/2026) :
// - fichier .txt (la porte d'envoi ne change pas) ; un fichier NOUVEAU à chaque copie (« Dialogue n°1.txt », « n°2 »…) :
//   jamais d'ajout ni de remplacement ;
// - sous-dossier « Dialogue » dans le dossier de la personne, à côté de « Reçus » et « Envoyés » ;
// - premier essai : une seule personne, ses 10 plus anciens messages ;
// - brouillons exclus ; leur nombre affiché avec ceux des codes à usage unique et des doutes ;
// - la fenêtre dit aussi « dernier message vu » (pour repérer les messages invisibles pour Cap : « chat », WhatsApp…).
// Document : du plus ancien au plus récent ; une ligne par message : « JJ/MM/AAAA HH:MM · reçu · texte » (heure de Paris ;
// l'heure qui revient deux fois fin octobre : « (heure d'été) » ou « (heure d'hiver) ») ; AUCUN nom ni numéro dans le texte
// (le nom de la personne est celui du dossier). Pièce jointe : renvoi vers le fichier copié au P6, ou « pas encore copiée ».
// Même date : SMS avant MMS, puis l'ordre du téléphone. Un lot ne coupe jamais un groupe de messages de même date.
// Anti-doublon : chaque fichier « Dialogue » porte ses marques invisibles : la personne (sa clé), son numéro, la date du
// dernier message copié (fin), le NOMBRE de messages copiés jusque-là (cumulé) et l'EMPREINTE de leur ensemble (cumulée).
// Relancé : seuls les messages APRÈS la fin sont nouveaux ; si les messages jusqu'à la fin ne correspondent plus (nombre ou
// empreinte : message ancien arrivé après coup, message effacé du téléphone…), ARRÊT, rien n'est copié. Fichiers à la
// corbeille compris (comme au P6).
// La fenêtre ne montre que des NOMBRES (messages, période, taille, dossier, exclus, dernier message vu), jamais un texte.
// 14/11/2026 (décision de Max, P7d) : TOUS les messages restants de la personne, avec UN SEUL « Oui, copier » ; en plusieurs
// fichiers enchaînés si besoin (4 Mo au plus chacun : « Dialogue n°3 », « n°4 »…) ; la fenêtre annonce tout avant (messages,
// fichiers, taille) ; chaque fichier : relu juste avant, envoyé, relu après ; au premier fichier pas identique ou à la première
// panne : ARRÊT NET (ce qui est fait reste, rien n'est effacé). Marque en plus sur chaque fichier : l'empreinte de son contenu ;
// à la relance, le DERNIER fichier est relu et doit être intact (sinon arrêt). Reprise sans doublon (marques cumulées).
const mmsDialogue = (() => {
  const DRIVE = 'https://www.googleapis.com/drive/v3/files';
  // 14/11/2026 (P7d) : + « contenu » : l'empreinte du contenu du fichier (relue à la relance : le dernier fichier doit être intact).
  const MARQUES = Object.freeze({ dialogue: 'cap_dialogue', numero: 'cap_dialogue_num', fin: 'cap_dialogue_fin', nombre: 'cap_dialogue_n', somme: 'cap_dialogue_somme', contenu: 'cap_dialogue_contenu', date: 'cap_mms_cree_le' });
  const SOUS = 'Dialogue';
  const SENS_SOUS = 'dialogue'; // marque du sous-dossier : « clé:dialogue » (comme « clé:recu » au P6)
  // 14/11/2026 (décision de Max, P7d) : TOUS les messages restants d'une personne, un seul « Oui, copier » ; plusieurs fichiers
  // enchaînés si besoin, 4 Mo au plus chacun (la porte d'envoi en permet 5 : marge).
  const TAILLE_FICHIER = 4 * 1024 * 1024;
  const FICHIERS_MAX = 200; // garde-fou : 800 Mo de textes ne viendront pas d'un téléphone
  const RESERVE_ENTETE = 1024; // les trois lignes du début d'un fichier
  const CLE_PERSONNE = /^personne:[0-9a-f]{16,}$/;
  const EMPREINTE = /^[0-9a-f]{64}$/;
  const NOMBRE = /^\d{1,15}$/;

  // ----- P7a : l'heure de Paris -----
  const formatParis = new Intl.DateTimeFormat('fr-FR', { timeZone: 'Europe/Paris', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23' });
  function parties(t) {
    const o = {};
    for (const p of formatParis.formatToParts(new Date(t))) o[p.type] = p.value;
    return o;
  }
  // Décalage de Paris (en minutes) à l'instant t.
  function decalage(t) {
    const o = parties(t);
    return Math.round((Date.UTC(+o.year, +o.month - 1, +o.day, +o.hour, +o.minute, +o.second) - Math.floor(t / 1000) * 1000) / 60000);
  }
  // « JJ/MM/AAAA HH:MM », + « (heure d'été) » ou « (heure d'hiver) » pour l'heure qui revient deux fois.
  function heure(t) {
    const o = parties(t);
    const base = `${o.day}/${o.month}/${o.year} ${o.hour}:${o.minute}`;
    for (const u of [t - 3600000, t + 3600000]) {
      const x = parties(u);
      if (x.year === o.year && x.month === o.month && x.day === o.day && x.hour === o.hour && decalage(u) !== decalage(t)) {
        return `${base} (${decalage(t) > decalage(u) ? 'heure d’été' : 'heure d’hiver'})`;
      }
    }
    return base;
  }

  // ----- P7a : la mise en ordre -----
  // Du plus ancien au plus récent ; même date : SMS avant MMS, puis l'ordre du téléphone (ordre reçu).
  function enOrdre(messages) {
    return messages.map((m, i) => ({ m, i }))
      .sort((a, b) => (a.m.date - b.m.date) || ((a.m.s === 'mms') - (b.m.s === 'mms')) || (a.i - b.i))
      .map(x => x.m);
  }

  // Les messages d'UNE personne : copiables (reçus ou envoyés, ni code ni doute ni brouillon), exclus (en nombres) et la
  // date du dernier message vu (tous ses messages, même exclus).
  function trier(lignes, cle) {
    const copiables = [];
    const exclus = { codes: 0, doutes: 0, brouillons: 0, nonEnvoyes: 0 };
    let dernier = 0;
    for (const l of Array.isArray(lignes) ? lignes : []) {
      if (!l || l.personne !== cle) continue;
      const date = Number(l.date) || 0;
      if (date > dernier) dernier = date;
      if (typeof l.texte !== 'string' || !EMPREINTE.test(String(l.marqueTexte))) throw new Error('Textes absents de la lecture : rien n’est copié.');
      if (l.brouillon === true) { exclus.brouillons++; continue; }
      if (l.sens !== 'recu' && l.sens !== 'envoye') { exclus.nonEnvoyes++; continue; }
      if (l.code === 'code') { exclus.codes++; continue; }
      if (l.code !== 'normal') { exclus.doutes++; continue; }
      if (!date) { exclus.doutes++; continue; }
      copiables.push(l);
    }
    return { copiables: enOrdre(copiables), exclus, dernier };
  }

  // Les personnes connues qui ont au moins un message copiable : [{ cle, nom, total }] (nom : écran du téléphone seulement).
  function personnes(lignes) {
    const parCle = new Map();
    for (const l of Array.isArray(lignes) ? lignes : []) {
      if (!l || typeof l.personne !== 'string' || !CLE_PERSONNE.test(l.personne)) continue;
      const e = parCle.get(l.personne) || { cle: l.personne, nom: '', total: 0 };
      if (!e.nom && l.etiquette) e.nom = String(l.etiquette);
      if (typeof l.texte === 'string' && l.brouillon !== true && (l.sens === 'recu' || l.sens === 'envoye') && l.code === 'normal' && Number(l.date) > 0) e.total++;
      parCle.set(l.personne, e);
    }
    return [...parCle.values()].filter(e => e.total > 0)
      .map(e => ({ ...e, nom: e.nom || mmsDossiers.nomDossier('personne', e.cle) }))
      .sort((a, b) => a.nom.localeCompare(b.nom, 'fr'));
  }

  // ----- P7a : les lignes du document -----
  // Le texte, propre : fins de ligne unifiées, caractères de commande et d'inversion du sens de lecture remplacés.
  const propre = texte => String(texte ?? '').replace(/\r\n?/g, '\n').replace(/[\u0000-\u0008\u000B-\u001F\u007F\u2028\u2029\u202A-\u202E\u2066-\u2069]/g, ' ').trim();
  const sorteDe = ct => (String(ct).startsWith('video/') ? 'vidéo' : 'image');
  // Une ligne (et ses suites, en retrait) : « JJ/MM/AAAA HH:MM · reçu · texte » + renvois des pièces jointes.
  // copies : Map(marque de la pièce → { sous, nom }) : les pièces copiées au P6.
  function ligne(m, copies = new Map()) {
    const morceaux = [];
    const t = propre(m.texte);
    if (t) morceaux.push(...t.split('\n'));
    for (const p of Array.isArray(m.pieces) ? m.pieces : []) {
      const c = copies.get(p.marque);
      morceaux.push(c ? `[${sorteDe(p.ct)}, copiée : ${c.sous} / ${c.nom}]` : `[${sorteDe(p.ct)}, pas encore copiée]`);
    }
    const autres = Math.max(0, Number(m.autres) || 0);
    if (autres) morceaux.push(`[${autres} autre${autres > 1 ? 's' : ''} pièce${autres > 1 ? 's' : ''} (son, fiche…), pas copiable${autres > 1 ? 's' : ''}]`);
    if (!morceaux.length) morceaux.push('(sans texte)');
    return `${heure(m.date)} · ${m.sens === 'recu' ? 'reçu' : 'envoyé'} · ${morceaux[0]}${morceaux.slice(1).map(x => `\n    ${x}`).join('')}`;
  }
  const pl = (n, un, plusieurs = `${un}s`) => `${n} ${n > 1 ? plusieurs : un}`;
  // Le document entier (aucun nom, aucun numéro).
  function documentTexte(numero, lot, copies, quand) {
    const recus = lot.filter(m => m.sens === 'recu').length;
    return [
      `Dialogue n°${numero} : copie faite par Cap le ${heure(quand)} (heure de Paris).`,
      `${pl(lot.length, 'message')}, du ${heure(lot[0].date)} au ${heure(lot[lot.length - 1].date)} : ${pl(recus, 'reçu')}, ${pl(lot.length - recus, 'envoyé')}.`,
      'Le nom de la personne n’est pas écrit ici : c’est le nom du dossier. Codes à usage unique, doutes et brouillons : pas copiés.',
      '',
      ...lot.map(m => ligne(m, copies)),
      ''
    ].join('\n');
  }

  // ----- P7a : les marques -----
  // Empreinte d'un ENSEMBLE de messages (leurs marques, dans un ordre fixe) : jamais un texte ni un numéro.
  const sha256 = async texte => [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(texte)))].map(b => b.toString(16).padStart(2, '0')).join('');
  async function somme(messages) {
    return sha256(messages.map(m => String(m.marqueTexte)).sort().join('\n'));
  }
  // 14/11/2026 (P7d) : l'empreinte du CONTENU d'un fichier (marque « contenu ») : jamais un texte.
  const empreinteContenu = contenu => sha256(contenu);
  // Le lot : les « limite » premiers, sans couper un groupe de même date.
  function lot(reste, limite) {
    const l = reste.slice(0, limite);
    while (l.length && reste.length > l.length && reste[l.length].date === l[l.length - 1].date) l.push(reste[l.length]);
    return l;
  }
  // L'état des copies déjà faites (fichiers marqués, corbeille comprise) : { numero (dernier), fin, nombre, somme } ou null.
  function etatCopies(fichiers) {
    const lus = [];
    for (const f of fichiers) {
      const a = f && f.appProperties ? f.appProperties : {};
      if (![a[MARQUES.numero], a[MARQUES.fin], a[MARQUES.nombre]].every(x => NOMBRE.test(String(x))) || !EMPREINTE.test(String(a[MARQUES.somme]))) throw new Error('Un fichier « Dialogue » a des marques illisibles : rien n’est copié. Préviens Claude Code.');
      if (a[MARQUES.contenu] !== undefined && !EMPREINTE.test(String(a[MARQUES.contenu]))) throw new Error('Un fichier « Dialogue » a des marques illisibles : rien n’est copié. Préviens Claude Code.');
      // P7d : + id et empreinte du contenu (absente sur les fichiers faits avant P7d : n°1 et n°2 de Max)
      lus.push({ numero: +a[MARQUES.numero], fin: +a[MARQUES.fin], nombre: +a[MARQUES.nombre], somme: String(a[MARQUES.somme]), id: String(f.id || ''), contenu: a[MARQUES.contenu] === undefined ? '' : String(a[MARQUES.contenu]) });
    }
    if (!lus.length) return null;
    lus.sort((a, b) => a.numero - b.numero);
    for (let i = 1; i < lus.length; i++) {
      if (lus[i].numero === lus[i - 1].numero) throw new Error(`« Dialogue n°${lus[i].numero} » existe en double : rien n’est copié. Préviens Claude Code.`);
      if (lus[i].fin < lus[i - 1].fin || lus[i].nombre <= lus[i - 1].nombre) throw new Error('Les fichiers « Dialogue » ne se suivent pas : rien n’est copié. Préviens Claude Code.');
    }
    return lus[lus.length - 1];
  }

  // ----- P7b : LECTURE SEULE (Drive) -----
  async function lister(compte, q) {
    const params = new URLSearchParams({ q, fields: 'files(id,name,trashed,parents,appProperties)', pageSize: '1000', spaces: 'drive' });
    const corps = await (await compte.appeler(`${DRIVE}?${params}`)).json();
    return Array.isArray(corps.files) ? corps.files : [];
  }
  // Les pièces déjà copiées (P6) de cette personne : Map(marque → { sous, nom }) (« Reçus » et « Envoyés », corbeille comprise).
  async function piecesCopiees(compte, cle) {
    const copies = new Map();
    for (const sens of ['recu', 'envoye']) {
      for (const d of await mmsCopie.parMarque(compte, mmsCopie.MARQUES.sous, `${cle}:${sens}`)) {
        if (!d || !/^[A-Za-z0-9_-]{10,200}$/.test(String(d.id))) continue;
        for (const f of await lister(compte, `'${d.id}' in parents`)) {
          const marque = f && f.appProperties ? f.appProperties[mmsCopie.MARQUES.copie] : '';
          if (marque && !copies.has(marque)) copies.set(marque, { sous: mmsCopie.SOUS[sens], nom: String(f.name || '') });
        }
      }
    }
    return copies;
  }

  // ----- 14/11/2026 (P7d) : le découpage de TOUT le reste en fichiers de tailleMax octets au plus, sans couper un groupe de même
  // date (ordre du temps gardé). Rend [[messages du fichier 1], [fichier 2]…].
  function decouper(reste, copies, tailleMax) {
    const enc = new TextEncoder();
    const groupes = [];
    for (const m of reste) {
      const g = groupes[groupes.length - 1];
      if (g && g[0].date === m.date) g.push(m); else groupes.push([m]);
    }
    const lots = [];
    let courant = [];
    let octets = 0;
    for (const g of groupes) {
      const t = g.reduce((s, m) => s + enc.encode(ligne(m, copies)).length + 1, 0);
      if (courant.length && octets + t + RESERVE_ENTETE > tailleMax) { lots.push(courant); courant = []; octets = 0; }
      courant.push(...g);
      octets += t;
    }
    if (courant.length) lots.push(courant);
    return lots;
  }
  // 14/11/2026 (P7d) : le DERNIER fichier déjà copié doit être intact (son contenu = son empreinte « contenu »), sinon ARRÊT.
  // Les fichiers faits avant P7d (sans cette marque) sont acceptés tels quels. Lecture seule.
  async function verifierDernier(compte, etat) {
    if (!etat || !etat.contenu) return;
    let contenu = null;
    try {
      if (!/^[A-Za-z0-9_-]{10,200}$/.test(etat.id)) throw new Error('identifiant');
      contenu = await (await compte.appeler(`${DRIVE}/${encodeURIComponent(etat.id)}?alt=media`)).text();
    } catch (erreur) {
      throw new Error(`Cap n’a pas pu relire « Dialogue n°${etat.numero}.txt » : rien n’est copié. Réessaie plus tard ; si ça recommence, préviens Claude Code.`);
    }
    if (await empreinteContenu(String(contenu)) !== etat.contenu) throw new Error(`« Dialogue n°${etat.numero}.txt » n’est pas intact dans le Drive : rien n’est copié. Ne relance pas ; préviens Claude Code.`);
  }

  // Ce que « Oui, copier » ferait (P7c, P7d). LECTURE SEULEMENT. Rend la proposition :
  // { personne, dossier, sous: { nom, id }, avant: { numero, nombre }, fichiers: [{ numero, nom, contenu, taille, messages, recus,
  //   du, au, marques: { fin, nombre, somme, contenu } }], taille, nombres } ; ou { rien: true, nombres } si tout est déjà copié.
  async function preparer(compte, personne, lignes, { tailleMax = TAILLE_FICHIER, maintenant = () => new Date() } = {}) {
    if (!personne || typeof personne.cle !== 'string' || !CLE_PERSONNE.test(personne.cle)) throw new Error('Copie refusée : ce n’est pas une personne connue. Rien n’est copié.');
    if (!Number.isInteger(tailleMax) || tailleMax < RESERVE_ENTETE + 256 || tailleMax > TAILLE_FICHIER) throw new Error('Copie refusée : taille de fichier non permise. Rien n’est copié.');
    const cle = personne.cle;
    const { copiables, exclus, dernier } = trier(lignes, cle);
    const dossier = await mmsCopie.dossierPersonne(compte, cle);
    const sous = await mmsCopie.sousDossier(compte, cle, SENS_SOUS, dossier.id, SOUS);
    const etat = etatCopies(await lister(compte, `appProperties has { key='${MARQUES.dialogue}' and value='${cle}' }`));
    let deja = [];
    let reste = copiables;
    if (etat) {
      deja = copiables.filter(m => m.date <= etat.fin);
      if (deja.length !== etat.nombre || await somme(deja) !== etat.somme) {
        throw new Error(`Les messages déjà copiés ne correspondent plus (${deja.length} sur le téléphone jusqu’au dernier copié, ${etat.nombre} dans la copie) : rien n’est copié. Préviens Claude Code.`);
      }
      reste = copiables.filter(m => m.date > etat.fin);
    }
    const nombres = { messages: reste.length, recus: reste.filter(m => m.sens === 'recu').length, deja: deja.length, restent: 0, exclus, dernier, piecesCopiees: 0, piecesPasCopiees: 0, fichiers: 0 };
    if (!reste.length) return { rien: true, nombres, dossier, sous: { nom: SOUS, id: sous.id } };
    await verifierDernier(compte, etat); // P7d : le dernier fichier copié est intact (sinon arrêt)
    const copies = await piecesCopiees(compte, cle);
    for (const m of reste) for (const p of Array.isArray(m.pieces) ? m.pieces : []) { if (copies.has(p.marque)) nombres.piecesCopiees++; else nombres.piecesPasCopiees++; }
    nombres.du = reste[0].date;
    nombres.au = reste[reste.length - 1].date;
    const lots = decouper(reste, copies, tailleMax);
    if (lots.length > FICHIERS_MAX) throw new Error('Copie refusée : trop de fichiers. Rien n’est copié. Préviens Claude Code.');
    const quand = maintenant().getTime();
    const fichiers = [];
    let cumul = deja.slice();
    for (let i = 0; i < lots.length; i++) {
      const l = lots[i];
      const numero = (etat ? etat.numero : 0) + 1 + i;
      const contenu = documentTexte(numero, l, copies, quand);
      const taille = new TextEncoder().encode(contenu).length;
      if (taille > tailleMax) throw new Error(`Copie refusée : des messages de même date font plus de ${Math.round(tailleMax / 1024 / 1024) || 1} Mo. Rien n’est copié. Préviens Claude Code.`);
      cumul = cumul.concat(l);
      fichiers.push({
        numero, nom: `Dialogue n°${numero}.txt`, contenu, taille, messages: l.length, recus: l.filter(m => m.sens === 'recu').length, du: l[0].date, au: l[l.length - 1].date,
        marques: { fin: l[l.length - 1].date, nombre: cumul.length, somme: await somme(cumul), contenu: await empreinteContenu(contenu) }
      });
    }
    nombres.fichiers = fichiers.length;
    return {
      personne: { cle }, dossier, sous: { nom: SOUS, id: sous.id },
      avant: { numero: etat ? etat.numero : 0, nombre: deja.length }, // relu juste avant la copie
      fichiers, taille: fichiers.reduce((s, f) => s + f.taille, 0), nombres
    };
  }

  const taille = o => (o >= 1024 * 1024 ? `${(o / 1024 / 1024).toFixed(1).replace('.', ',')} Mo` : `${Math.max(1, Math.round(o / 1024))} Ko`);
  const vu = n => `Dernier message vu par Cap avec cette personne : ${n.dernier ? heure(n.dernier) : 'aucun'}. S’il y en a de plus récents dans ta messagerie, Cap ne les voit pas (« chat », WhatsApp…).`;
  const exclusTexte = e => `Non copiés : ${pl(e.codes, 'code à usage unique', 'codes à usage unique')}, ${pl(e.doutes, 'doute')}, ${pl(e.brouillons, 'brouillon')}, ${pl(e.nonEnvoyes, 'non envoyé', 'non envoyés')}.`;
  // La fenêtre « Oui, copier » : des NOMBRES seulement (jamais un texte de message).
  function texte(prop) {
    const n = prop.nombres;
    if (prop.rien) return [`Tout est déjà copié : ${pl(n.deja, 'message')} dans « ${prop.sous.nom} ». Rien de nouveau.`, exclusTexte(n.exclus), vu(n)].join('\n');
    const f = prop.fichiers;
    const lignes = [
      `Copier les textes de ${pl(n.messages, 'message')} (${pl(n.recus, 'reçu')}, ${pl(n.messages - n.recus, 'envoyé')}), du ${heure(n.du)} au ${heure(n.au)} : tous les messages pas encore copiés.`,
      f.length === 1 ? `En 1 fichier : « ${f[0].nom} ». Taille : ${taille(prop.taille)}.`
        : `En ${f.length} fichiers (4 Mo au plus chacun) : de « ${f[0].nom} » à « ${f[f.length - 1].nom} ». Taille totale : ${taille(prop.taille)}.`,
      `Vers « ${prop.sous.nom} »${prop.sous.id ? '' : ' (créé, vide, marqué et daté)'}, dans le dossier « ${prop.dossier.nom} » de « MMS des relations » (Drive du compte Cap).`,
      `${f.length === 1 ? 'Un fichier NOUVEAU' : 'Des fichiers NOUVEAUX'} : aucun fichier existant n’est modifié.`,
      `Déjà copiés : ${n.deja}. Ensuite, seuls les messages nouveaux seront copiés.`,
      exclusTexte(n.exclus)
    ];
    if (n.piecesCopiees + n.piecesPasCopiees) lignes.push(`Pièces jointes : ${n.piecesCopiees} déjà copiée${n.piecesCopiees > 1 ? 's' : ''} (renvoi vers le fichier), ${n.piecesPasCopiees} pas encore copiée${n.piecesPasCopiees > 1 ? 's' : ''}.`);
    lignes.push(vu(n),
      f.length === 1 ? 'Après la copie, Cap relit le fichier dans le Drive et te dit s’il est identique.'
        : 'Après chaque fichier, Cap le relit dans le Drive. Au premier fichier différent ou à la première panne, il s’arrête net : ce qui est fait reste, rien n’est effacé.',
      'Les messages restent sur ton téléphone. Rien n’est effacé, ni déplacé, ni remplacé.');
    return lignes.join('\n');
  }

  // ----- P7c, P7d : ÉCRITURE, après « Oui, copier » seulement. montre = { messages, fichiers } : ce qui a été montré à Max.
  // Rend { copie, faits: [{ nom, messages, relu }], messages, nom (le dernier créé), sousCree, relu ('identique' si tous le sont,
  // sinon celui du fichier qui a arrêté : 'différent' | 'impossible'), pasFaits: { fichiers, messages }, erreur }.
  let enCours = false;
  const NOM_SUR = /^Dialogue n°\d{1,6}\.txt$/;
  async function copier(compte, prop, montre, { maintenant = () => new Date() } = {}) {
    if (enCours) throw new Error('Une copie est déjà en cours : attends qu’elle finisse.');
    enCours = true;
    const rapport = { copie: false, faits: [], messages: 0, nom: '', sousCree: false, relu: '', pasFaits: { fichiers: 0, messages: 0 }, erreur: null };
    try {
      const refus = raison => { throw new Error(`Copie refusée : ${raison}. Rien n’est copié.`); };
      if (!prop || prop.rien || !montre || !Number.isInteger(montre.messages) || !Number.isInteger(montre.fichiers) || !prop.nombres || !Array.isArray(prop.fichiers) || !prop.fichiers.length) refus('rien n’a été montré à Max');
      if (!prop.personne || !CLE_PERSONNE.test(String(prop.personne.cle))) refus('ce n’est pas une personne connue');
      const fs = prop.fichiers;
      if (fs.length > FICHIERS_MAX || montre.fichiers !== fs.length || montre.messages !== prop.nombres.messages || fs.reduce((s, f) => s + (Number(f && f.messages) || 0), 0) !== prop.nombres.messages) refus('pas exactement ce qui a été montré');
      if (!prop.avant || !Number.isInteger(prop.avant.numero) || !Number.isInteger(prop.avant.nombre)) refus('marques illisibles');
      let nombre = prop.avant.nombre;
      let fin = 0;
      for (let i = 0; i < fs.length; i++) {
        const f = fs[i];
        if (!f || f.numero !== prop.avant.numero + 1 + i || !NOM_SUR.test(String(f.nom)) || f.nom !== `Dialogue n°${f.numero}.txt`) refus('nom de fichier illisible');
        if (typeof f.contenu !== 'string' || !f.contenu || new TextEncoder().encode(f.contenu).length !== f.taille || f.taille > TAILLE_FICHIER) refus('fichier abîmé');
        const mq = f.marques || {};
        nombre += f.messages;
        if (!Number.isInteger(f.messages) || f.messages < 1 || !Number.isInteger(mq.fin) || mq.fin <= fin || mq.nombre !== nombre || !EMPREINTE.test(String(mq.somme)) || !EMPREINTE.test(String(mq.contenu))) refus('marques illisibles');
        if (await empreinteContenu(f.contenu) !== mq.contenu) refus('fichier abîmé');
        fin = mq.fin;
      }
      const cle = prop.personne.cle;
      const date = (() => { const d = maintenant(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`; })();
      // Relu juste avant : le même dossier ; rien de copié depuis la question ; le dernier fichier intact.
      const dossier = await mmsCopie.dossierPersonne(compte, cle);
      if (dossier.id !== prop.dossier.id) throw new Error('Le dossier de la personne a changé depuis la question : rien n’est copié.');
      let sousId = (await mmsCopie.sousDossier(compte, cle, SENS_SOUS, dossier.id, SOUS)).id;
      const etat = etatCopies(await lister(compte, `appProperties has { key='${MARQUES.dialogue}' and value='${cle}' }`));
      if ((etat ? etat.numero : 0) !== prop.avant.numero || (etat ? etat.nombre : 0) !== prop.avant.nombre) throw new Error('Une copie a été faite depuis la question : rien n’est copié. Relance pour voir ce qui reste.');
      await verifierDernier(compte, etat);
      if (!sousId) {
        const r = await (await compte.appelerEcriture(`${DRIVE}?fields=id`, { method: 'POST', body: JSON.stringify({ name: SOUS, mimeType: 'application/vnd.google-apps.folder', parents: [dossier.id], appProperties: { [mmsCopie.MARQUES.sous]: `${cle}:${SENS_SOUS}`, [MARQUES.date]: date } }) })).json();
        if (!r || !r.id) throw new Error('Google n’a pas rendu le dossier créé.');
        sousId = r.id;
        rapport.sousCree = true;
      }
      rapport.pasFaits = { fichiers: fs.length, messages: prop.nombres.messages };
      for (let i = 0; i < fs.length; i++) {
        const f = fs[i];
        if (i > 0) { // relu juste avant CHAQUE fichier : le précédent est bien le dernier
          const e = etatCopies(await lister(compte, `appProperties has { key='${MARQUES.dialogue}' and value='${cle}' }`));
          if (!e || e.numero !== fs[i - 1].numero || e.nombre !== fs[i - 1].marques.nombre) throw new Error('Une autre copie a été faite pendant celle-ci : arrêt. Relance pour voir ce qui reste.');
        }
        const marques = { [MARQUES.dialogue]: cle, [MARQUES.numero]: String(f.numero), [MARQUES.fin]: String(f.marques.fin), [MARQUES.nombre]: String(f.marques.nombre), [MARQUES.somme]: String(f.marques.somme), [MARQUES.contenu]: String(f.marques.contenu), [MARQUES.date]: date };
        const reponse = await compte.envoyerFichier(sousId, { nom: f.nom, mimeType: 'text/plain', appProperties: marques }, new Blob([f.contenu], { type: 'text/plain' }));
        rapport.copie = true;
        const fait = { nom: f.nom, messages: f.messages, relu: '' };
        rapport.faits.push(fait);
        rapport.nom = f.nom;
        rapport.messages += f.messages;
        rapport.pasFaits = { fichiers: fs.length - i - 1, messages: prop.nombres.messages - rapport.messages };
        // Relecture (lecture seule) : le fichier créé, ses marques, son dossier, son contenu.
        try {
          const id = String((await reponse.json()).id || '');
          if (!/^[A-Za-z0-9_-]{10,200}$/.test(id)) throw new Error('identifiant');
          const meta = await (await compte.appeler(`${DRIVE}/${encodeURIComponent(id)}?fields=id,name,parents,appProperties,trashed`)).json();
          const contenu = await (await compte.appeler(`${DRIVE}/${encodeURIComponent(id)}?alt=media`)).text();
          const memes = meta && meta.name === f.nom && Array.isArray(meta.parents) && meta.parents[0] === sousId && meta.trashed !== true
            && Object.entries(marques).every(([k, v]) => meta.appProperties && meta.appProperties[k] === v) && contenu === f.contenu;
          fait.relu = memes ? 'identique' : 'différent';
        } catch (erreur) { fait.relu = 'impossible'; }
        rapport.relu = fait.relu;
        if (fait.relu !== 'identique') break; // arrêt NET au premier fichier pas identique
      }
    } catch (erreur) {
      rapport.erreur = String(erreur && erreur.message || 'raison inconnue').slice(0, 200); // arrêt NET
    } finally {
      enCours = false;
      if (prop && typeof prop === 'object' && Array.isArray(prop.fichiers)) for (const f of prop.fichiers) if (f && typeof f === 'object') f.contenu = ''; // les textes ne restent pas dans la proposition
    }
    return rapport;
  }

  return Object.freeze({ MARQUES, SOUS, TAILLE_FICHIER, heure, enOrdre, trier, personnes, ligne, documentTexte, somme, lot, decouper, etatCopies, preparer, texte, copier, enCours: () => enCours }); // 14/11/2026 (P7d) : + TAILLE_FICHIER, decouper (LIMITE_PREMIER retiré)
})();
