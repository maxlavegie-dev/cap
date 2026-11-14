'use strict';

// 13/11/2026 (accord de Max, P5 = M3e, TEMPS 1 seulement) : LA LISTE, EN NOMBRES, des dossiers par expéditeur qui seraient créés
// dans le Drive du compte Cap, dans « MMS des relations » (rangement PARALLÈLE : l'ancien rangement « r_ » n'est jamais touché).
// - RIEN N'EST CRÉÉ ICI : ce module ne fait que des calculs (planifier, verifierPlan, texte) et UNE lecture du Drive
//   (lireEtat : ce qui existe déjà ; lecture seule, jamais d'écriture). La création viendra au temps 2, sur le Oui de Max.
// - Un dossier par PERSONNE connue (une seule fiche pour son numéro : plusieurs numéros = un seul dossier), par numéro
//   inconnu, par numéro court, par expéditeur en lettres, par groupe. Numéro masqué, illisible ou sur deux fiches : « À trier ».
//   Un expéditeur qui n'a envoyé QUE des codes à usage unique : pas de dossier (compté seulement ; à décider par Max).
// - Les noms ne contiennent JAMAIS de numéro : un code en lettres tiré de l'empreinte (« Numéro inconnu KXBT-QRMD »).
//   verifierPlan refuse tout nom avec trois chiffres ou plus, même séparés.
// - Anti-doublon : un dossier = une clé (empreinte, jamais le numéro) ; une clé déjà présente dans le Drive (marque
//   « cap_mms_dossier ») n'est jamais planifiée deux fois ; verifierPlan refuse un plan avec deux fois la même clé ou le même
//   nom, un dossier hors de « MMS des relations », ou plus de dossiers que la liste montrée à Max.
// - « Reçus », « Envoyés » et « Dialogue » ne sont PAS créés par P5 : seulement comptés (« plus tard, si la copie en a besoin »).
// Les lignes viennent de l'inventaire de P3 (lecture des MMS, option avecPersonne) : AUCUN texte, AUCUN numéro.
const mmsDossiers = (() => {
  const NOM_RACINE = 'MMS des relations';
  const NOM_A_TRIER = 'À trier';
  const DOSSIER = 'application/vnd.google-apps.folder';
  const DRIVE = 'https://www.googleapis.com/drive/v3/files';
  const MARQUES = Object.freeze({ racine: 'cap_mms_racine', dossier: 'cap_mms_dossier' });
  const PARENT = 'racine'; // tous les dossiers vont DANS « MMS des relations », jamais ailleurs
  const SORTES = Object.freeze(['personne', 'numero', 'court', 'lettres', 'groupe']);
  const LIBELLES = Object.freeze({ personne: 'Personne', numero: 'Numéro inconnu', court: 'Numéro court', lettres: 'Expéditeur en lettres', groupe: 'Groupe' });
  const CONSONNES = 'BCDFGHJKLMNPQRSTVWXZ';

  // Trois chiffres ou plus, même séparés par des espaces, points, tirets, parenthèses, barres ou « + » : un numéro possible.
  const contientNumero = nom => /\d(?:[\s.\-()/+_]*\d){2,}/.test(String(nom));

  // Code en LETTRES tiré d'une empreinte hexadécimale : 8 consonnes, « KXBT-QRMD ». Jamais un chiffre.
  function codeLettres(empreinte) {
    const hex = String(empreinte || '').replace(/^[a-z-]+:/, '').replace(/[^0-9a-f]/g, '');
    if (hex.length < 16) throw new Error('Nom de dossier impossible : empreinte trop courte.');
    let t = '';
    for (let i = 0; i < 8; i++) t += CONSONNES[parseInt(hex.slice(i * 2, i * 2 + 2), 16) % CONSONNES.length];
    return `${t.slice(0, 4)}-${t.slice(4)}`;
  }
  const nomDossier = (sorte, cle) => `${LIBELLES[sorte]} ${codeLettres(cle)}`;
  // 13/11/2026 (P5, temps 2) : le nom AFFICHABLE d'une personne connue ou d'un expéditeur en lettres (étiquette de l'inventaire),
  // nettoyé ; vide s'il contient un numéro (trois chiffres ou plus) : le dossier prend alors le nom à code en lettres.
  function nomPropre(etiquette) {
    const n = String(etiquette || '').replace(/[\x5c/:*?"<>|\u0000-\u001f]/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 100);
    return !n || contientNumero(n) ? '' : n;
  }

  // lignes : [{ s, sens, date, sorteCle, cle, code, personne? }] ; existants : clés déjà marquées dans le Drive.
  // Rend le plan : { racine: { existe }, dossiers: [{ cle, sorte, nom, parent }], aTrier, parSorte, existants, seulementCodes, plusTard, total }.
  function planifier(lignes, { racineExiste = false, aTrierExiste = false, existants = [] } = {}) {
    const deja = new Set((Array.isArray(existants) ? existants : []).map(String));
    const parCle = new Map();
    let messagesATrier = 0;
    const doutes = new Set(); // 13/11/2026 (temps 2) : expéditeurs qui ont envoyé un message douteux
    for (const l of Array.isArray(lignes) ? lignes : []) {
      if (!l || typeof l !== 'object') continue;
      const sorte = l.personne ? 'personne' : (SORTES.includes(l.sorteCle) && l.sorteCle !== 'personne' ? l.sorteCle : null);
      const cle = l.personne ? String(l.personne) : String(l.cle || '');
      const cleSure = /[0-9a-f]{16,}$/.test(cle); // « groupe-inconnu », « masque », « a-trier » : pas d'empreinte → « À trier »
      if (!cleSure) { if (l.code !== 'code') messagesATrier++; continue; }
      if (l.code === 'code') { // exclu : jamais copié ; compté pour savoir si l'expéditeur n'a envoyé QUE des codes
        if (sorte && cle) { const e = parCle.get(cle) || { sorte, codes: 0, utiles: 0, recus: 0, envoyes: 0, textes: 0 }; e.codes++; parCle.set(cle, e); }
        continue;
      }
      if (!sorte || !cle || l.code === 'doute') { messagesATrier++; if (l.code === 'doute' && sorte && cle) doutes.add(cle); continue; }
      const e = parCle.get(cle) || { sorte, codes: 0, utiles: 0, recus: 0, envoyes: 0, textes: 0 };
      e.utiles++;
      if (!e.etiquette && l.etiquette && (e.sorte === 'personne' || e.sorte === 'lettres')) e.etiquette = String(l.etiquette);
      if (l.s === 'mms' && l.sens === 'recu') e.recus++;
      if (l.s === 'mms' && l.sens === 'envoye') e.envoyes++;
      if (l.s === 'sms') e.textes++;
      parCle.set(cle, e);
    }
    const parSorte = Object.fromEntries(SORTES.map(s => [s, 0]));
    const dossiers = [];
    const noms = new Set();
    let existantsVus = 0;
    let seulementCodes = 0;
    const plusTard = { recus: 0, envoyes: 0, dialogue: 0 };
    for (const [cle, e] of parCle) {
      if (!e.utiles) { seulementCodes++; continue; }
      if (e.recus) plusTard.recus++;
      if (e.envoyes) plusTard.envoyes++;
      if (e.textes) plusTard.dialogue++;
      if (deja.has(cle)) { existantsVus++; continue; }
      const base = nomPropre(e.etiquette) || nomDossier(e.sorte, cle); // 13/11/2026 (temps 2) : avant, toujours nomDossier
      let nom = base;
      for (let i = 2; noms.has(nom); i++) nom = `${base} ${'ABCDEFGHJKLMNPQRSTUVWXYZ'[(i - 2) % 24]}`;
      noms.add(nom);
      parSorte[e.sorte]++;
      dossiers.push({ cle, sorte: e.sorte, nom, parent: PARENT });
    }
    const aTrier = { messages: messagesATrier, creer: messagesATrier > 0 && !aTrierExiste };
    const total = dossiers.length + (racineExiste ? 0 : 1) + (aTrier.creer ? 1 : 0);
    const seulementDoutes = [...doutes].filter(k => !parCle.has(k)).length; // 13/11/2026 (temps 2) : que des messages douteux
    return { racine: { existe: Boolean(racineExiste) }, dossiers, aTrier, parSorte, existants: existantsVus, marquesDansDrive: deja.size, seulementCodes, seulementDoutes, plusTard, total };
  }

  // Garde du temps 2 (appelée avant toute création) : rend true, ou lève une erreur SANS aucun nom ni clé dans le message.
  // montre : le plan montré à Max dans la fenêtre « Oui, créer » (son total est la limite).
  function verifierPlan(plan, montre) {
    const refus = raison => { throw new Error(`Plan refusé : ${raison}. Rien n’est créé.`); };
    if (!plan || !Array.isArray(plan.dossiers)) refus('plan illisible');
    if (!montre || !Number.isInteger(montre.total)) refus('aucune liste montrée à Max');
    if (plan.total > montre.total || plan.dossiers.length > montre.dossiers.length) refus('plus de dossiers que la liste montrée');
    const cles = new Set();
    const noms = new Set();
    for (const d of plan.dossiers) {
      if (!d || d.parent !== PARENT) refus('un dossier serait créé hors de « MMS des relations »');
      if (!d.cle || cles.has(d.cle)) refus('un dossier serait créé en double');
      if (!d.nom || !String(d.nom).trim() || noms.has(d.nom)) refus('deux dossiers auraient le même nom');
      if (contientNumero(d.nom)) refus('un nom de dossier contiendrait un numéro');
      if (!SORTES.includes(d.sorte)) refus('sorte de dossier inconnue');
      cles.add(d.cle);
      noms.add(d.nom);
    }
    return true;
  }

  // Lignes pour l'écran : des NOMBRES seulement (aucun nom de dossier, aucune clé).
  function texte(plan) {
    const p = plan.parSorte;
    const t = plan.plusTard;
    const n = plan.dossiers.length;
    return [
      `Liste des dossiers par expéditeur (rien n’est créé sans « Oui, créer » ; aucun message n’est copié).`,
      `Dans le Drive du compte Cap, dans « ${NOM_RACINE} » (${plan.racine.existe ? 'existe déjà' : 'serait créé, marqué et daté'}) :`,
      `${n} dossier${n > 1 ? 's' : ''} à créer : ${p.personne} personnes connues, ${p.numero} numéros inconnus, ${p.court} numéros courts, ${p.lettres} expéditeurs en lettres, ${p.groupe} groupes.`,
      `« ${NOM_A_TRIER} » : ${plan.aTrier.messages} messages (numéro masqué, illisible, sur deux fiches, ou doute sur un code) ; dossier ${plan.aTrier.messages ? (plan.aTrier.creer ? 'à créer' : 'existe déjà') : 'inutile'}.`,
      `Dossiers déjà marqués par Cap dans « ${NOM_RACINE} » : ${plan.marquesDansDrive} ; reconnus dans cette liste (jamais recréés) : ${plan.existants}.`,
      `Expéditeurs qui n’ont envoyé QUE des codes à usage unique : ${plan.seulementCodes} (pas de dossier, décision de Max).`,
      `Expéditeurs avec seulement des doutes : ${plan.seulementDoutes || 0} (pas de dossier ; leurs messages vont dans « ${NOM_A_TRIER} »).`,
      `Plus tard, si la copie en a besoin : « Reçus » pour ${t.recus}, « Envoyés » pour ${t.envoyes}, « Dialogue » pour ${t.dialogue}.`,
      `Total des créations au temps 2 : ${plan.total} au plus. L’ancien rangement « r_ » n’est pas touché.`
    ].join('\n');
  }

  // LECTURE SEULE du Drive du compte Cap : « MMS des relations » existe-t-il (marqué) ? un dossier du même nom NON marqué ?
  // quelles clés sont déjà marquées dedans ? Jamais d'écriture (seulement compte.appeler, la lecture).
  async function lireEtat(compte, { pagesMax = 20 } = {}) {
    const lister = async q => {
      const tout = [];
      let jeton = '';
      for (let i = 0; i < pagesMax; i++) {
        const params = new URLSearchParams({ q, fields: 'nextPageToken,files(id,name,appProperties)', pageSize: '1000', spaces: 'drive' });
        if (jeton) params.set('pageToken', jeton);
        const corps = await (await compte.appeler(`${DRIVE}?${params}`)).json();
        if (Array.isArray(corps.files)) tout.push(...corps.files);
        jeton = corps.nextPageToken || '';
        if (!jeton) return tout;
      }
      throw new Error('Trop de dossiers à lire : arrêté, rien n’a été créé.');
    };
    const racines = await lister(`appProperties has { key='${MARQUES.racine}' and value='1' } and mimeType='${DOSSIER}' and trashed=false`);
    if (racines.length > 1) throw new Error(`Le compte Cap a ${racines.length} dossiers « ${NOM_RACINE} » marqués : rien ne sera créé. Préviens Claude Code.`);
    const aLaRacine = await lister(`'root' in parents and mimeType='${DOSSIER}' and trashed=false`);
    const homonymes = aLaRacine.filter(f => f && f.name === NOM_RACINE && !(f.appProperties && f.appProperties[MARQUES.racine])).length;
    const racine = racines[0] || null;
    let existants = [];
    let aTrierExiste = false;
    let nonMarques = 0;
    if (racine) {
      const enfants = await lister(`'${racine.id}' in parents and mimeType='${DOSSIER}' and trashed=false`);
      for (const f of enfants) {
        const v = f && f.appProperties ? f.appProperties[MARQUES.dossier] : undefined;
        if (v === 'a_trier') aTrierExiste = true;
        else if (typeof v === 'string' && v) existants.push(v);
        else nonMarques++;
      }
    }
    return { racineExiste: Boolean(racine), racineId: racine ? racine.id : null, homonymes, existants, aTrierExiste, nonMarques }; // 13/11/2026 : + racineId
  }

  return Object.freeze({ NOM_RACINE, NOM_A_TRIER, MARQUES, SORTES, contientNumero, codeLettres, nomDossier, planifier, verifierPlan, texte, lireEtat });
})();
