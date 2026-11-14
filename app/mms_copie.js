'use strict';

// 14/11/2026 (accord de Max, P6) : COPIE d'UN message (ses pièces jointes : images, vidéos) d'UNE personne connue, dans le Drive
// du COMPTE CAP, dans le dossier de cette personne (« MMS des relations », créé au P5).
// - Le message est COPIÉ, jamais déplacé : la coque ne fait que LIRE (autorisation SMS en lecture seule) ; rien n'est effacé, ni
//   sur le téléphone, ni dans le Drive (aucune suppression, aucun remplacement, aucune corbeille).
// - Max choisit la personne et le message sur le téléphone ; la fenêtre « Oui, copier » montre la sorte de pièce, la taille,
//   reçu ou envoyé, et le dossier d'arrivée ; rien ne part avant (preparer ne fait que LIRE ; copier écrit).
// - Seulement : un MMS reçu ou envoyé, d'une personne connue (une seule fiche), ni code à usage unique ni doute, avec au moins
//   une image ou vidéo ; 10 pièces au plus ; 5 Mo au plus par pièce.
// - Écritures permises ici : créer « Reçus » ou « Envoyés » (dossier VIDE, marqué, daté) DANS le dossier de la personne, puis
//   envoyer chaque pièce par la porte unique du compte Cap (envoyerFichier, P4), qui relit le dossier cible.
// - Anti-doublon : chaque copie porte sa marque (empreinte de « message:pièce », jamais un numéro ni un contenu), relue juste
//   avant chaque envoi, corbeille comprise : une pièce déjà copiée (même jetée par Max) n'est jamais recopiée.
// - Nom du fichier (décision de Max) : la date du message + un numéro d'ordre (« 2026-11-13 n°1.jpg ») ; jamais le contenu.
// - Une copie à la fois (verrou) ; la PREMIÈRE erreur arrête tout. Jamais plus de pièces que celles montrées.
// Ce module ne lit pas le téléphone lui-même : la lecture d'une pièce lui est donnée (lire), par l'écran.
const mmsCopie = (() => {
  const DRIVE = 'https://www.googleapis.com/drive/v3/files';
  const DOSSIER = 'application/vnd.google-apps.folder';
  const MARQUES = Object.freeze({ dossier: 'cap_mms_dossier', sous: 'cap_mms_sous', copie: 'cap_mms_copie', date: 'cap_mms_cree_le' });
  const SOUS = Object.freeze({ recu: 'Reçus', envoye: 'Envoyés' });
  const EXTENSIONS = Object.freeze({ 'image/jpeg': 'jpg', 'image/png': 'png', 'image/gif': 'gif', 'image/webp': 'webp', 'image/heic': 'heic', 'image/heif': 'heif',
    'video/mp4': 'mp4', 'video/3gpp': '3gp', 'video/webm': 'webm', 'video/quicktime': 'mov' });
  const PIECES_MAX = 10;
  const TAILLE_MAX = 5 * 1024 * 1024;
  const ID_SUR = /^\d{1,18}$/;
  const MARQUE_SURE = /^[a-z0-9_:-]{1,100}$/;
  const deux = n => String(n).padStart(2, '0');
  const jour = d => `${d.getFullYear()}-${deux(d.getMonth() + 1)}-${deux(d.getDate())}`;
  let enCours = false;

  // Les personnes connues et leurs messages COPIABLES (lignes de l'inventaire : stable, avecPersonne, etiquettes, pieces).
  // Rend [{ cle, nom, messages: [{ mid, date, sens, pieces: [{ id, ct, marque }], autres, code }] }] (messages du plus récent au plus ancien).
  function personnes(lignes) {
    const parCle = new Map();
    for (const l of Array.isArray(lignes) ? lignes : []) {
      if (!l || typeof l.personne !== 'string' || l.s !== 'mms' || !SOUS[l.sens] || l.code !== 'normal' || !ID_SUR.test(String(l.mid || ''))) continue;
      const pieces = (Array.isArray(l.pieces) ? l.pieces : []).filter(x => x && ID_SUR.test(String(x.id)) && EXTENSIONS[x.ct] && MARQUE_SURE.test(String(x.marque)));
      if (!pieces.length) continue;
      const e = parCle.get(l.personne) || { cle: l.personne, nom: '', messages: [] };
      if (!e.nom && l.etiquette) e.nom = String(l.etiquette);
      e.messages.push({ mid: String(l.mid), date: Number(l.date) || 0, sens: l.sens, pieces: pieces.slice(0, PIECES_MAX).map(x => ({ id: String(x.id), ct: x.ct, marque: String(x.marque) })), autres: Math.max(0, Number(l.autres) || 0), code: l.code });
      parCle.set(l.personne, e);
    }
    return [...parCle.values()]
      .map(e => ({ ...e, nom: e.nom || mmsDossiers.nomDossier('personne', e.cle), messages: e.messages.sort((a, b) => b.date - a.date) }))
      .sort((a, b) => a.nom.localeCompare(b.nom, 'fr'));
  }

  const sorteDe = ct => (String(ct).startsWith('video/') ? 'vidéo' : 'image');
  function sortes(pieces) {
    const n = { image: 0, 'vidéo': 0 };
    for (const p of pieces) n[sorteDe(p.ct)]++;
    return Object.entries(n).filter(([, k]) => k).map(([s, k]) => `${k} ${s}${k > 1 ? 's' : ''}`).join(', ');
  }
  const taille = o => (o >= 1024 * 1024 ? `${(o / 1024 / 1024).toFixed(1).replace('.', ',')} Mo` : `${Math.max(1, Math.round(o / 1024))} Ko`);
  const quand = t => { const d = new Date(t); return `${deux(d.getDate())}/${deux(d.getMonth() + 1)}/${d.getFullYear()} ${deux(d.getHours())}:${deux(d.getMinutes())}`; };
  // Une ligne pour le bouton d'un message : date, reçu ou envoyé, sortes de pièces (aucun contenu).
  const texteMessage = m => `${quand(m.date)} · ${m.sens === 'recu' ? 'reçu' : 'envoyé'} · ${sortes(m.pieces)}${m.autres ? ` (+ ${m.autres} pièce${m.autres > 1 ? 's' : ''} non copiable${m.autres > 1 ? 's' : ''})` : ''}`;
  const nomFichier = (date, numero, ct) => `${jour(new Date(date))} n°${numero}.${EXTENSIONS[ct]}`;

  // LECTURE SEULE : les fichiers portant une marque (corbeille comprise ; tous les types si mimeType est vide).
  async function parMarque(compte, cle, valeur, mimeType = DOSSIER) {
    if (!MARQUE_SURE.test(String(valeur))) throw new Error('Marque illisible : arrêt, rien n’est copié.');
    const q = `appProperties has { key='${cle}' and value='${valeur}' }${mimeType ? ` and mimeType='${mimeType}'` : ''}`;
    const params = new URLSearchParams({ q, fields: 'files(id,name,trashed,parents)', pageSize: '10', spaces: 'drive' });
    const corps = await (await compte.appeler(`${DRIVE}?${params}`)).json();
    return Array.isArray(corps.files) ? corps.files : [];
  }

  // Le dossier de la personne : UN seul, marqué par Cap, pas à la corbeille, DANS « MMS des relations ».
  async function dossierPersonne(compte, cle) {
    const etat = await mmsDossiers.lireEtat(compte);
    if (!etat.racineId) throw new Error('« MMS des relations » est introuvable : rien n’est copié.');
    const vivants = (await parMarque(compte, MARQUES.dossier, cle)).filter(f => f && f.trashed !== true);
    if (vivants.length !== 1 || !Array.isArray(vivants[0].parents) || vivants[0].parents[0] !== etat.racineId) throw new Error('Le dossier de cette personne est introuvable (ou en double) dans « MMS des relations » : rien n’est copié.');
    return { id: vivants[0].id, nom: String(vivants[0].name || '') };
  }

  // « Reçus » ou « Envoyés » de cette personne : { id } s'il existe, { id: null } sinon ; à la corbeille : arrêt.
  // 14/11/2026 (P7) : nom : aussi « Dialogue » (sens « dialogue »), même règle.
  async function sousDossier(compte, cle, sens, parent, nom = SOUS[sens]) {
    const tous = await parMarque(compte, MARQUES.sous, `${cle}:${sens}`);
    if (tous.length && tous.every(f => f && f.trashed === true)) throw new Error(`« ${nom} » de cette personne est à la corbeille : rien n’est copié (Cap ne le recrée pas).`);
    const vivants = tous.filter(f => f && f.trashed !== true);
    if (vivants.length > 1) throw new Error(`« ${nom} » existe en double pour cette personne : rien n’est copié. Préviens Claude Code.`);
    if (vivants.length && (!Array.isArray(vivants[0].parents) || vivants[0].parents[0] !== parent)) throw new Error(`« ${nom} » n’est plus dans le dossier de la personne : rien n’est copié.`);
    return { id: vivants.length ? vivants[0].id : null };
  }

  function garde(personne, message) {
    const refus = raison => { throw new Error(`Copie refusée : ${raison}. Rien n’est copié.`); };
    if (!personne || typeof personne.cle !== 'string' || !/^personne:[0-9a-f]{16,}$/.test(personne.cle)) refus('ce n’est pas une personne connue');
    if (!message || !ID_SUR.test(String(message.mid))) refus('message illisible');
    if (message.code !== 'normal') refus('code à usage unique ou doute');
    if (!SOUS[message.sens]) refus('ni reçu ni envoyé');
    if (!Array.isArray(message.pieces) || !message.pieces.length) refus('aucune pièce copiable');
    if (message.pieces.length > PIECES_MAX) refus(`plus de ${PIECES_MAX} pièces`);
    for (const p of message.pieces) if (!p || !ID_SUR.test(String(p.id)) || !EXTENSIONS[p.ct] || !MARQUE_SURE.test(String(p.marque))) refus('pièce illisible');
  }

  // LECTURE SEULEMENT (Drive et téléphone) : ce que « Oui, copier » ferait. lire(mid, idPiece) → { ct, taille, octets } | { trop }.
  // Rend { personne, message, dossier: { id, nom }, sous: { nom, id }, pieces: [{ id, ct, marque, taille, octets }], deja, tropGrosses }.
  async function preparer(compte, personne, message, lire) {
    garde(personne, message);
    const dossier = await dossierPersonne(compte, personne.cle);
    const sous = await sousDossier(compte, personne.cle, message.sens, dossier.id);
    const pieces = [];
    let deja = 0;
    let tropGrosses = 0;
    for (const p of message.pieces) {
      if ((await parMarque(compte, MARQUES.copie, p.marque, '')).length) { deja++; continue; }
      const lu = await lire(message.mid, p.id);
      if (lu && lu.trop === true) { tropGrosses++; continue; }
      if (!lu || lu.ct !== p.ct || !(lu.octets instanceof Uint8Array) || lu.octets.length < 1 || lu.octets.length > TAILLE_MAX) throw new Error('Le téléphone n’a pas rendu la pièce attendue : rien n’est copié.');
      pieces.push({ id: p.id, ct: p.ct, marque: p.marque, taille: lu.octets.length, octets: lu.octets });
    }
    return { personne: { cle: personne.cle }, message: { mid: message.mid, date: message.date, sens: message.sens, code: message.code }, dossier, sous: { nom: SOUS[message.sens], id: sous.id }, pieces, deja, tropGrosses };
  }

  // Le texte de la fenêtre « Oui, copier » : sorte, taille, reçu ou envoyé, dossier d'arrivée (aucun contenu, aucun numéro).
  function texte(prop) {
    const total = prop.pieces.reduce((s, p) => s + p.taille, 0);
    const lignes = [
      `Copier ce message (${prop.message.sens === 'recu' ? 'reçu' : 'envoyé'} le ${quand(prop.message.date)}) :`,
      `${sortes(prop.pieces)} (${prop.pieces.map(p => p.ct.split('/')[1]).join(', ')}), ${taille(total)} en tout.`,
      `Vers « ${prop.sous.nom} »${prop.sous.id ? '' : ' (créé, vide, marqué et daté)'}, dans le dossier « ${prop.dossier.nom} » de « MMS des relations » (Drive du compte Cap).`,
      `Nom du fichier : la date du message et un numéro d’ordre (« ${nomFichier(prop.message.date, 1, prop.pieces[0].ct)} »).`
    ];
    if (prop.deja) lignes.push(`Déjà copiée${prop.deja > 1 ? 's' : ''} (pas recopiée${prop.deja > 1 ? 's' : ''}) : ${prop.deja}.`);
    if (prop.tropGrosses) lignes.push(`Plus de 5 Mo (pas copiée${prop.tropGrosses > 1 ? 's' : ''}) : ${prop.tropGrosses}.`);
    lignes.push('Le message reste sur ton téléphone. Rien n’est effacé, ni déplacé.');
    return lignes.join('\n');
  }

  // ÉCRITURE, après « Oui, copier » seulement. montre = { pieces } : le nombre de pièces montrées (la limite).
  // Rend { copiees, deja, sousCree, erreur, nom (sous-dossier), noms (fichiers) }.
  async function copier(compte, prop, montre, { maintenant = () => new Date() } = {}) {
    if (enCours) throw new Error('Une copie est déjà en cours : attends qu’elle finisse.');
    enCours = true;
    const rapport = { copiees: 0, deja: 0, sousCree: false, erreur: null, nom: prop && prop.sous ? prop.sous.nom : '', noms: [] };
    try {
      if (!prop || !Array.isArray(prop.pieces) || !montre || !Number.isInteger(montre.pieces)) throw new Error('Copie refusée : rien n’a été montré à Max. Rien n’est copié.');
      garde(prop.personne, { ...prop.message, pieces: prop.pieces });
      if (prop.pieces.length > montre.pieces) throw new Error('Copie refusée : plus de pièces que celles montrées. Rien n’est copié.');
      for (const p of prop.pieces) if (!(p.octets instanceof Uint8Array) || p.octets.length < 1 || p.octets.length > TAILLE_MAX || p.octets.length !== p.taille) throw new Error('Copie refusée : pièce abîmée. Rien n’est copié.');
      const cle = prop.personne.cle;
      const sens = prop.message.sens;
      const date = jour(maintenant());
      // Relu : le dossier de la personne doit être celui montré.
      const dossier = await dossierPersonne(compte, cle);
      if (dossier.id !== prop.dossier.id) throw new Error('Le dossier de la personne a changé depuis la question : rien n’est copié.');
      let sousId = (await sousDossier(compte, cle, sens, dossier.id)).id;
      // Numéro d'ordre : après ceux déjà présents pour cette date (lecture seule, corbeille comprise).
      const prefixe = `${jour(new Date(prop.message.date))} n°`;
      let numero = 0;
      if (sousId) {
        const params = new URLSearchParams({ q: `'${sousId}' in parents`, fields: 'files(id,name)', pageSize: '1000', spaces: 'drive' });
        const corps = await (await compte.appeler(`${DRIVE}?${params}`)).json();
        for (const f of Array.isArray(corps.files) ? corps.files : []) {
          const n = String(f && f.name || '').startsWith(prefixe) ? parseInt(String(f.name).slice(prefixe.length), 10) : 0;
          if (n > numero) numero = n;
        }
      }
      let envois = 0;
      for (const p of prop.pieces) {
        if ((await parMarque(compte, MARQUES.copie, p.marque, '')).length) { rapport.deja++; continue; } // relu juste avant
        if (envois + 1 > montre.pieces) throw new Error('Plus de pièces que celles montrées : arrêt.');
        if (!sousId) {
          const r = await (await compte.appelerEcriture(`${DRIVE}?fields=id`, { method: 'POST', body: JSON.stringify({ name: SOUS[sens], mimeType: DOSSIER, parents: [dossier.id], appProperties: { [MARQUES.sous]: `${cle}:${sens}`, [MARQUES.date]: date } }) })).json();
          if (!r || !r.id) throw new Error('Google n’a pas rendu le dossier créé.');
          sousId = r.id;
          rapport.sousCree = true;
        }
        const nom = nomFichier(prop.message.date, ++numero, p.ct);
        await compte.envoyerFichier(sousId, { nom, mimeType: p.ct, appProperties: { [MARQUES.copie]: p.marque, [MARQUES.date]: date } }, new Blob([p.octets], { type: p.ct }));
        envois++;
        rapport.copiees++;
        rapport.noms.push(nom);
      }
    } catch (erreur) {
      rapport.erreur = String(erreur && erreur.message || 'raison inconnue').slice(0, 200); // arrêt NET
    } finally {
      enCours = false;
      for (const p of prop && Array.isArray(prop.pieces) ? prop.pieces : []) if (p && p.octets instanceof Uint8Array) p.octets.fill(0); // rien ne reste en mémoire
    }
    return rapport;
  }

  // 14/11/2026 (P7) : + dossierPersonne, sousDossier, parMarque (LECTURE SEULE), pour le document « Dialogue ».
  return Object.freeze({ MARQUES, SOUS, PIECES_MAX, personnes, texteMessage, nomFichier, preparer, texte, copier, enCours: () => enCours, dossierPersonne, sousDossier, parMarque });
})();
