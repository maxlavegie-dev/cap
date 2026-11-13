'use strict';

// 12/11/2026 (accord de Max, marche M1 du rangement des MMS par personne, plan de Haiku vérifié) : INDEX LOCAL PAR EMPREINTE.
// Sur le téléphone seulement : une table « empreinte du numéro → identifiant de la personne ». L'empreinte est un HMAC-SHA-256
// du numéro NORMALISÉ (numeros.js, M2), avec une CLÉ aléatoire (32 octets) créée une fois et gardée sur le téléphone.
// - Le numéro n'est JAMAIS écrit : ni dans l'index, ni dans un journal, ni à l'écran, ni dans le dépôt.
// - La clé ne se dicte ni ne se voit : aucun affichage, aucune voix, aucune console ; elle ne quitte pas le téléphone.
// - Deux personnes avec le même numéro : « plusieurs » (aucun choix automatique) ; numéro inconnu : null (donc « À trier »).
// - Aucun écran ici (M1) : la première chose visible sera M3, sur décision de Max. Aucune lecture du Drive, rien vers l'IA.
const indexRelations = (() => {
  const CLE_STOCKAGE = 'cap_cle_index_relations_v1';
  const hex = octets => [...new Uint8Array(octets)].map(b => b.toString(16).padStart(2, '0')).join('');
  const depuisHex = texte => new Uint8Array(texte.match(/../g).map(x => parseInt(x, 16)));

  // La clé du téléphone : lue si elle existe, sinon créée une fois (aléatoire) et gardée.
  function cleDuTelephone(stockage, aleatoire = n => crypto.getRandomValues(new Uint8Array(n))) {
    if (!stockage) return null;
    let cle = null;
    try { cle = stockage.getItem(CLE_STOCKAGE); } catch (erreur) { cle = null; }
    if (typeof cle === 'string' && /^[0-9a-f]{64}$/.test(cle)) return cle;
    cle = hex(aleatoire(32));
    try { stockage.setItem(CLE_STOCKAGE, cle); } catch (erreur) { return null; }
    return cle;
  }

  async function empreinteNumero(numero, cle) {
    const n = typeof numeros !== 'undefined' ? numeros.normaliserNumero(numero) : null;
    if (!n || typeof cle !== 'string' || !/^[0-9a-f]{64}$/.test(cle)) return null;
    const k = await crypto.subtle.importKey('raw', depuisHex(cle), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
    return hex(await crypto.subtle.sign('HMAC', k, new TextEncoder().encode(n)));
  }

  // personnes : [{ identifiant, numeros: [...] }], déjà lues, en mémoire. Rend { version, empreintes: { empreinte: [identifiants] } }.
  async function construireIndex(personnes, cle) {
    const empreintes = {};
    for (const p of Array.isArray(personnes) ? personnes : []) {
      if (!p || p.identifiant === undefined || p.identifiant === null) continue;
      const id = String(p.identifiant);
      for (const numero of Array.isArray(p.numeros) ? p.numeros : []) {
        const e = await empreinteNumero(numero, cle);
        if (!e) continue;
        if (!empreintes[e]) empreintes[e] = [];
        if (!empreintes[e].includes(id)) empreintes[e].push(id);
      }
    }
    return { version: 1, empreintes };
  }

  // Rend l'identifiant de la personne, null (inconnu), ou 'plusieurs' (homonymes de numéro : Max choisit).
  async function trouverPersonne(numero, index, cle) {
    const e = await empreinteNumero(numero, cle);
    const liste = e && index && index.empreintes ? index.empreintes[e] : null;
    if (!Array.isArray(liste) || !liste.length) return null;
    return liste.length > 1 ? 'plusieurs' : liste[0];
  }

  return Object.freeze({ CLE_STOCKAGE, cleDuTelephone, empreinteNumero, construireIndex, trouverPersonne });
})();
