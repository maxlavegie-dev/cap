'use strict';

// 13/11/2026 (accord de Max, P3) : INVENTAIRE DES ÉCHANGES DU TÉLÉPHONE, en NOMBRES seulement.
// Reçoit des lignes déjà réduites par mms_lecture.js : { s: 'sms' | 'mms', sens: 'recu' | 'envoye' | 'autre', date (ms),
// sorteCle, cle (empreinte éphémère), code: 'code' | 'doute' | 'normal' } : aucun texte, aucun numéro.
// Rend des nombres et deux dates (le plus ancien, le plus récent) ; texte() en fait des lignes pour l'écran.
// Règles de Max : un code à usage unique est EXCLU (compté seulement) ; « À trier » = sans identité claire (expéditeur en
// lettres, groupe, masqué, numéro sur deux fiches ou illisible) ou doute sur un code. Fonction PURE : pas de page, pas de
// réseau, pas de stockage, aucune sortie.
const inventaireEchanges = (() => {
  const SORTES = ['numero', 'court', 'lettres', 'masque', 'groupe', 'nom', 'a-trier'];
  const A_TRIER = new Set(['lettres', 'groupe', 'masque', 'a-trier']);

  function compter(lignes) {
    const r = {
      total: 0,
      sms: { recu: 0, envoye: 0, autre: 0 }, mms: { recu: 0, envoye: 0, autre: 0 },
      correspondants: Object.fromEntries(SORTES.map(s => [s, 0])),
      codesExclus: 0, doutes: 0, aTrier: 0, plusAncien: null, plusRecent: null
    };
    const vus = Object.fromEntries(SORTES.map(s => [s, new Set()]));
    for (const l of Array.isArray(lignes) ? lignes : []) {
      if (!l || typeof l !== 'object') continue;
      r.total++;
      const s = l.s === 'mms' ? 'mms' : 'sms';
      const sens = ['recu', 'envoye'].includes(l.sens) ? l.sens : 'autre';
      r[s][sens]++;
      const d = Number(l.date);
      if (Number.isFinite(d) && d > 0) {
        if (r.plusAncien === null || d < r.plusAncien) r.plusAncien = d;
        if (r.plusRecent === null || d > r.plusRecent) r.plusRecent = d;
      }
      const sorte = SORTES.includes(l.sorteCle) ? l.sorteCle : 'a-trier';
      if (sorte === 'a-trier') vus[sorte].add(`message-${r.total}`); // chaque message illisible ou sur deux fiches compte
      else vus[sorte].add(String(l.cle));
      if (l.code === 'code') { r.codesExclus++; continue; } // exclu : jamais copié, compté seulement
      if (l.code === 'doute') { r.doutes++; r.aTrier++; continue; }
      if (A_TRIER.has(sorte)) r.aTrier++;
    }
    for (const s of SORTES) r.correspondants[s] = vus[s].size;
    return r;
  }

  const jour = ms => { const d = new Date(ms); return `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()}`; };

  // Lignes pour l'écran : des nombres et deux dates, rien d'autre.
  function texte(r) {
    const c = r.correspondants;
    return [
      `Inventaire : ${r.total} message${r.total > 1 ? 's' : ''} lus sur le téléphone (rien n’est copié ni envoyé).`,
      `SMS : ${r.sms.recu} reçus, ${r.sms.envoye} envoyés, ${r.sms.autre} autres (brouillons, en attente, échecs).`,
      `MMS : ${r.mms.recu} reçus, ${r.mms.envoye} envoyés, ${r.mms.autre} autres.`,
      `Correspondants différents : ${c.numero} numéros, ${c.court} numéros courts, ${c.lettres} expéditeurs en lettres, ${c.masque ? 'des numéros masqués' : 'aucun numéro masqué'}, ${c.groupe} groupes, ${c['a-trier']} messages au numéro illisible ou sur deux fiches.`,
      `Codes à usage unique exclus (jamais copiés) : ${r.codesExclus}. Doutes sur un code : ${r.doutes}.`,
      `Messages qui iraient dans « À trier » : ${r.aTrier}.`,
      r.plusAncien === null ? 'Période : aucun message daté.' : `Période : du ${jour(r.plusAncien)} au ${jour(r.plusRecent)}.`,
      'Noms sans numéro : ils viennent du Dictionnaire, pas des messages (voir la ligne « Dossiers r_ » de « Lire mes derniers MMS »).'
    ].join('\n');
  }

  return Object.freeze({ compter, texte });
})();
