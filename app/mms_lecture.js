'use strict';

// 12/11/2026 (accord écrit de Max, marche M3a) : LECTURE des MMS reçus, par la coque Android (pont MmsAndroid).
// - Seulement dans l'application Cap du téléphone (la coque) ; ailleurs : « pas disponible ».
// - L'autorisation SMS d'Android est demandée seulement quand Max touche le bouton (demander), jamais au démarrage.
// - La coque rend, pour les 20 derniers MMS reçus : identifiant, date, image / vidéo / texte (oui ou non), nombre de
//   destinataires, et le numéro de l'expéditeur. Ce numéro est changé AUSSITÔT en empreinte (index_relations.js, M1) puis
//   oublié : il ne sort jamais d'ici (ni rendu, ni gardé, ni affiché, ni écrit dans un journal, ni envoyé à l'IA).
// - Rien n'est copié, rien n'est envoyé : aucune lecture du Drive, aucun réseau ici. Sans DOM.
const mmsLecture = (() => {
  const pont = fenetre => (fenetre && fenetre.MmsAndroid) || null;

  function disponible(fenetre = window) { return !!pont(fenetre); }

  function autorise(fenetre = window) {
    try { return !!(pont(fenetre) && pont(fenetre).autorise() === true); } catch (erreur) { return false; }
  }

  // Ouvre la question d'Android ; rend true (accepté) ou false (refusé, pas de coque, pas de réponse dans le délai).
  function demander(fenetre = window, delai = 120000) {
    const p = pont(fenetre);
    if (!p) return Promise.resolve(false);
    if (autorise(fenetre)) return Promise.resolve(true);
    return new Promise(resolu => {
      let fini = false;
      const finir = valeur => {
        if (fini) return;
        fini = true;
        clearTimeout(minuteur);
        if (fenetre.__mmsAutorisation === recevoir) fenetre.__mmsAutorisation = null;
        resolu(valeur === true && autorise(fenetre));
      };
      const recevoir = accordee => finir(accordee);
      const minuteur = setTimeout(() => finir(false), delai);
      fenetre.__mmsAutorisation = recevoir;
      try { p.demander(); } catch (erreur) { finir(false); }
    });
  }

  // cle : la clé du téléphone (indexRelations.cleDuTelephone). Rend [{ id, date, image, video, texte, groupe, nombreDestinataires, empreinte }] :
  // AUCUN numéro dedans (empreinte = null si le numéro est masqué, absent ou illisible).
  async function lireRecents(cle, fenetre = window) {
    const p = pont(fenetre);
    if (!p || !autorise(fenetre)) return [];
    let brut = [];
    try { brut = JSON.parse(p.recents()); } catch (erreur) { brut = []; }
    const rendus = [];
    for (const m of Array.isArray(brut) ? brut.slice(0, 20) : []) {
      if (!m || typeof m !== 'object') continue;
      let empreinte = null;
      try { empreinte = await indexRelations.empreinteNumero(m.expediteur, cle); } catch (erreur) { empreinte = null; }
      rendus.push({
        id: String(m.id ?? ''), date: Number(m.date) || 0,
        image: m.image === true, video: m.video === true, texte: m.texte === true,
        groupe: Number(m.destinataires) > 1, nombreDestinataires: Math.max(0, Math.floor(Number(m.destinataires) || 0)), empreinte // c176 : + le nombre (pour l'explication)
      });
    }
    return rendus;
  }

  // ----- 13/11/2026 (accord de Max, P3) : INVENTAIRE de tous les SMS et MMS (reçus, envoyés, autres), pour des NOMBRES. -----
  // La coque calcule à part (inventaireLancer, inventaireEtat, inventaireLire). Ici, chaque message est AUSSITÔT réduit à :
  // sorte, sens, date, sorte du code à usage unique (P1, codes_usage_unique.js) et clé de son correspondant (P2,
  // cles_expediteurs.js) ; son texte et ses numéros sont oubliés. Les clés viennent d'une empreinte ÉPHÉMÈRE (clé au hasard,
  // en mémoire pour cet inventaire seulement, jamais gardée). « Numéro sur deux fiches » : par l'index des relations (cle,
  // index préparés par le module de rangement des MMS). Rien n'est rendu d'autre : AUCUN texte, AUCUN numéro.
  // 13/11/2026 (P5, temps 1) : avecPersonne : + « personne » sur une ligne d'un numéro qui a UNE seule fiche (empreinte
  // ÉPHÉMÈRE de l'identifiant : jamais le nom) ; sert à compter UN dossier par personne, même avec plusieurs numéros.
  // 13/11/2026 (P5, temps 2) : stable : l'empreinte n'est plus tirée au hasard mais DÉRIVÉE de la clé du téléphone (jamais
  // gardée ni montrée ; le numéro n'en sort pas) : la même personne a la même clé d'un jour à l'autre, ce qui évite les doublons
  // dans le Drive. etiquettes : + « etiquette » = le nom affichable, SEULEMENT pour une personne connue (son dossier « r_ »)
  // et pour un expéditeur en lettres (son nom en lettres) ; JAMAIS pour un numéro. En mémoire seulement.
  // 14/11/2026 (accord de Max, P6) : pieces (seulement avec stable) : sur une ligne de MMS, + « mid » (identifiant du message
  // sur le téléphone, des chiffres), « pieces » = [{ id, ct, marque }] (images et vidéos copiables ; marque = empreinte DÉRIVÉE
  // de « copie:message:pièce », la même d'un jour à l'autre : anti-doublon dans le Drive) et « autres » (pièces non copiables,
  // comptées). Aucun contenu : la pièce elle-même n'est lue que par lirePiece, pour UN message choisi par Max.
  // 14/11/2026 (accord de Max, P7) : textes (seulement avec stable, avecPersonne ET pieces) : sur une ligne d'une PERSONNE CONNUE
  // seulement (une seule fiche), + « texte » (le texte du message, pour le fichier « Dialogue », en mémoire seulement) et
  // « marqueTexte » (empreinte DÉRIVÉE du message : la même d'un jour à l'autre ; jamais un numéro ; anti-doublon) ;
  // + « brouillon » (true) pour un brouillon (la coque dit « brouillon » ; la ligne garde le sens « autre »). Les numéros,
  // les lignes des inconnus, des groupes et des expéditeurs en lettres : JAMAIS de texte.
  const TYPES_PIECES = /^(?:image\/(?:jpeg|png|gif|webp|heic|heif)|video\/(?:mp4|3gpp|webm|quicktime))$/;
  const ID_SUR = /^\d{1,18}$/;
  async function lireInventaire(cle, index, fenetre = window, { pause = ms => new Promise(r => setTimeout(r, ms)), delaiMax = 600000, avecPersonne = false, stable = false, etiquettes = false, pieces = false, textes = false } = {}) {
    if (stable && (typeof cle !== 'string' || !/^[0-9a-f]{64}$/.test(cle))) throw new Error('Clé du téléphone absente : rien n’est lu ni créé.');
    if (pieces && !stable) throw new Error('Pièces sans clé stable : rien n’est lu.'); // 14/11/2026 (P6) : la marque doit rester la même
    if (textes && !(stable && avecPersonne && pieces)) throw new Error('Textes sans clé stable, sans personne ou sans pièces : rien n’est lu.'); // 14/11/2026 (P7) : la marque doit rester la même
    const p = pont(fenetre);
    if (!p || !autorise(fenetre) || typeof p.inventaireLancer !== 'function') throw new Error('Inventaire impossible : l’application Cap du téléphone ne le permet pas encore.');
    if (p.inventaireLancer() !== true) throw new Error('Inventaire impossible : autorisation SMS absente.');
    const debut = Date.now();
    let etat = '';
    for (;;) {
      try { etat = String(p.inventaireEtat()); } catch (erreur) { etat = 'erreur'; }
      if (etat !== 'en-cours') break;
      if (Date.now() - debut > delaiMax) throw new Error('Inventaire trop long : arrêté, rien n’a été gardé.');
      await pause(300);
    }
    if (etat !== 'pret') throw new Error('Inventaire impossible : le téléphone n’a pas pu lire les messages.');
    let brut = [];
    try { brut = JSON.parse(p.inventaireLire() || '[]'); } catch (erreur) { brut = []; }
    let octets;
    if (stable) { // dérivée : HMAC(clé du téléphone, « cap-mms-dossiers-v1 ») ; jamais la clé elle-même
      const base = await crypto.subtle.importKey('raw', new Uint8Array(cle.match(/../g).map(x => parseInt(x, 16))), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
      octets = new Uint8Array(await crypto.subtle.sign('HMAC', base, new TextEncoder().encode('cap-mms-dossiers-v1')));
    } else octets = crypto.getRandomValues(new Uint8Array(32));
    const k = await crypto.subtle.importKey('raw', octets, { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
    octets.fill(0);
    const empreinte = async texte => [...new Uint8Array(await crypto.subtle.sign('HMAC', k, new TextEncoder().encode(texte)))].map(b => b.toString(16).padStart(2, '0')).join('');
    const table = index && index.empreintes ? index.empreintes : {};
    const personnesPour = async numero => {
      let e = null;
      try { e = await indexRelations.empreinteNumero(numero, cle); } catch (erreur) { e = null; }
      return e && Array.isArray(table[e]) ? table[e] : [];
    };
    const options = { empreinte, personnesPour };
    const lignes = [];
    const personneParCle = new Map(); // P5 : en mémoire, pour cet inventaire seulement
    const etiquetteParCle = new Map(); // P5 temps 2 : en mémoire seulement
    for (const m of Array.isArray(brut) ? brut : []) {
      if (!m || typeof m !== 'object') continue;
      const code = codesUsageUnique.analyser(typeof m.texte === 'string' ? m.texte : '').sorte;
      const adresses = Array.isArray(m.adresses) ? m.adresses.filter(a => typeof a === 'string') : [];
      let r;
      try {
        r = m.groupe === true && adresses.length > 1
          ? await clesExpediteurs.cleGroupe(adresses.map(a => ({ adresse: a })), options)
          : m.groupe === true ? { sorte: 'groupe', cle: 'groupe-inconnu' } : await clesExpediteurs.cle({ adresse: adresses[0] }, options);
      } catch (erreur) { r = { sorte: 'a-trier', cle: 'a-trier' }; }
      const ligne = { s: m.s === 'mms' ? 'mms' : 'sms', sens: ['recu', 'envoye'].includes(m.sens) ? m.sens : 'autre', date: Number(m.date) || 0, sorteCle: r.sorte, cle: r.cle, code };
      if (avecPersonne && r.sorte === 'numero') {
        if (!personneParCle.has(r.cle)) {
          let p = [];
          try { p = [...new Set((await personnesPour(adresses[0])) || [])]; } catch (erreur) { p = []; }
          personneParCle.set(r.cle, p.length === 1 ? `personne:${await empreinte(`personne:${p[0]}`)}` : null);
          if (etiquettes && p.length === 1) etiquetteParCle.set(r.cle, String(p[0]).replace(/^r_/, ''));
        }
        if (personneParCle.get(r.cle)) ligne.personne = personneParCle.get(r.cle);
        if (etiquetteParCle.get(r.cle)) ligne.etiquette = etiquetteParCle.get(r.cle);
      }
      if (etiquettes && r.sorte === 'lettres' && typeof adresses[0] === 'string') ligne.etiquette = clesExpediteurs.uniforme(adresses[0]);
      if (pieces && ligne.s === 'mms' && ID_SUR.test(String(m.id ?? ''))) { // 14/11/2026 (P6)
        ligne.mid = String(m.id);
        ligne.pieces = [];
        for (const x of Array.isArray(m.pieces) ? m.pieces.slice(0, 20) : []) {
          if (!x || !ID_SUR.test(String(x.id ?? '')) || typeof x.ct !== 'string' || !TYPES_PIECES.test(x.ct)) continue;
          ligne.pieces.push({ id: String(x.id), ct: x.ct, marque: await empreinte(`copie:${ligne.mid}:${x.id}`) });
        }
        ligne.autres = Math.max(0, Math.floor(Number(m.autres) || 0));
      }
      if (textes && ligne.personne) { // 14/11/2026 (P7) : personne connue SEULEMENT
        ligne.texte = typeof m.texte === 'string' ? couper(m.texte, 20000) : ''; // 14/11/2026 : jamais un émoticône coupé en deux
        ligne.marqueTexte = await empreinte(`dialogue:${ligne.s}:${String(m.sens)}:${ligne.date}:${ligne.mid || ''}:${ligne.texte}`);
        if (m.sens === 'brouillon') ligne.brouillon = true;
      }
      lignes.push(ligne);
    }
    brut = null;
    return lignes;
  }

  // ----- 14/11/2026 (accord de Max, P6) : LIRE UNE pièce d'UN message choisi par Max (lecture seule, par la coque), pour
  // la montrer en nombres (sorte, taille) puis la copier après « Oui, copier ». Rend { ct, taille, octets } ou { ct, trop: true }
  // (plus de 5 Mo : pas de contenu). Le message reste sur le téléphone : la coque ne fait que lire.
  async function lirePiece(mid, idPiece, fenetre = window) {
    const p = pont(fenetre);
    if (!p || !autorise(fenetre) || typeof p.pieceLire !== 'function') throw new Error('Lecture de la pièce impossible : l’application Cap du téléphone ne le permet pas encore.');
    if (!ID_SUR.test(String(mid)) || !ID_SUR.test(String(idPiece))) throw new Error('Pièce illisible : rien n’est copié.');
    let r = {};
    try { r = JSON.parse(p.pieceLire(String(mid), String(idPiece)) || '{}') || {}; } catch (erreur) { r = {}; }
    if (r.trop === true && TYPES_PIECES.test(String(r.ct))) return { ct: r.ct, taille: 0, trop: true };
    if (r.erreur || typeof r.donnees !== 'string' || !TYPES_PIECES.test(String(r.ct))) throw new Error('Le téléphone n’a pas pu lire la pièce : rien n’est copié.');
    let binaire = '';
    try { binaire = atob(r.donnees); } catch (erreur) { binaire = ''; }
    const octets = new Uint8Array(binaire.length);
    for (let i = 0; i < binaire.length; i++) octets[i] = binaire.charCodeAt(i);
    if (!octets.length || (Number(r.taille) || 0) !== octets.length) throw new Error('Pièce incomplète : rien n’est copié.');
    return { ct: r.ct, taille: octets.length, octets };
  }

  // 14/11/2026 (demande de Max : garder TOUS les émoticônes) : coupe un texte trop long SANS couper un émoticône en deux :
  // à la fin du dernier caractère entier (émoticône composé, drapeau, teinte, caractères joints compris) ; jamais une
  // moitié de caractère. Un texte assez court est rendu tel quel.
  function couper(texte, max) {
    if (texte.length <= max) return texte;
    let fin = max;
    if (typeof Intl === 'object' && typeof Intl.Segmenter === 'function') {
      fin = 0;
      for (const s of new Intl.Segmenter('fr', { granularity: 'grapheme' }).segment(texte)) {
        if (s.index + s.segment.length > max) break;
        fin = s.index + s.segment.length;
      }
    }
    const c = texte.charCodeAt(fin - 1);
    if (fin > 0 && c >= 0xD800 && c <= 0xDBFF) fin--; // jamais la première moitié d'un caractère seule
    return texte.slice(0, fin);
  }

  return Object.freeze({ disponible, autorise, demander, lireRecents, lireInventaire, lirePiece, couper }); // 14/11/2026 (P6) : + lirePiece ; + couper (émoticônes)
})();
