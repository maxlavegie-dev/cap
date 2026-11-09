'use strict';

// 09/11/2026 (décision de Max, bloc c74) : dans TOUTE fenêtre de choix (deux cases ou plus), Max peut répondre par l'ORDRE
// des propositions affichées : « numéro 1 », « numéro un », « le premier », « la première », « le deuxième », « la
// seconde », « le 3e », « le troisième »… C'est le CODE qui reconnaît (aucune IA), et seulement une phrase faite d'un
// rang et de petits mots (« c'est le deuxième », « je prends la troisième ») : « la première page » n'est PAS un rang.
// Sans DOM : rang(phrase) rend 1, 2, 3… ou null.
const numeroChoix = (() => {
  const plier = texte => String(texte || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/œ/g, 'oe')
    .replace(/[^a-z0-9]+/g, ' ').trim();
  const CARDINAUX = { un: 1, une: 1, deux: 2, trois: 3, quatre: 4, cinq: 5, six: 6, sept: 7, huit: 8, neuf: 9, dix: 10,
    onze: 11, douze: 12, treize: 13, quatorze: 14, quinze: 15, seize: 16, 'dix sept': 17, 'dix huit': 18, 'dix neuf': 19, vingt: 20 };
  const ORDINAUX = { premier: 1, premiere: 1, second: 2, seconde: 2, deuxieme: 2, troisieme: 3, quatrieme: 4, cinquieme: 5,
    sixieme: 6, septieme: 7, huitieme: 8, neuvieme: 9, dixieme: 10, onzieme: 11, douzieme: 12, treizieme: 13,
    quatorzieme: 14, quinzieme: 15, seizieme: 16, 'dix septieme': 17, 'dix huitieme': 18, 'dix neuvieme': 19, vingtieme: 20 };
  // Ce que la reconnaissance d'Android écrit souvent pour un numéro dit SEUL (repris du défaut 3, 09/11/2026).
  const SONS_SEULS = { de: 2, deu: 2, eux: 2, d: 2, hein: 1, in: 1, toit: 3, quatres: 4, sinq: 5, sank: 5 };
  // Petits mots autour du rang (« c'est le numéro deux », « je prends la troisième », « celle-ci la première »).
  const PETITS = new Set(['le', 'la', 'l', 'les', 'numero', 'num', 'no', 'n', 'nr', 'choix', 'case', 'ligne', 'proposition', 'c', 'est', 'ce',
    'sera', 'prends', 'prend', 'je', 'veux', 'voudrais', 'plutot', 'celui', 'celle', 'ci', 'alors', 'euh', 'bon', 'donc',
    'merci', 's', 'il', 'te', 'plait']);
  // « 1er », « 1re », « 1ere », « 2e », « 2eme », « 2nd », « 2nde », « 3eme » : le chiffre.
  const CHIFFRE = /^(\d{1,2})(er|re|ere|e|eme|em|nd|nde)?$/;

  function rang(phrase) {
    const mots = plier(phrase).split(' ').filter(Boolean);
    if (!mots.length || mots.length > 8) return null;
    if (mots.length === 1 && SONS_SEULS[mots[0]]) return SONS_SEULS[mots[0]];
    const utiles = mots.filter(m => !PETITS.has(m));
    if (!utiles.length || utiles.length > 2) return null;
    // « d'eux » (deux sons pour un seul numéro) : le même numéro répété compte une fois.
    const sons = utiles.map(m => SONS_SEULS[m] || CARDINAUX[m] || ORDINAUX[m] || null);
    if (sons.every(Boolean) && sons.every(v => v === sons[0])) return sons[0];
    const reste = utiles.join(' ');
    if (ORDINAUX[reste]) return ORDINAUX[reste];
    if (CARDINAUX[reste]) return CARDINAUX[reste];
    const chiffre = utiles.length === 1 ? reste.match(CHIFFRE) : null;
    if (chiffre) { const n = Number(chiffre[1]); return n >= 1 ? n : null; }
    return null;
  }

  return { rang, plier };
})();
