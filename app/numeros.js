'use strict';

// 12/11/2026 (accord de Max, marche M2 du rangement des MMS par personne, plan de Haiku vérifié) : NORMALISATION DES NUMÉROS.
// Un même numéro écrit de plusieurs façons (06…, 07…, +33…, 0033…, avec espaces, points, tirets, parenthèses, « +33 (0)6… »)
// donne UNE seule forme : « +33612345678 » (numéros français) ou « +<indicatif><numéro> » (autres pays, 8 à 15 chiffres).
// Numéro non reconnu (masqué, « insert-address-token », vide, lettres, trop court) : null, sans erreur.
// Fonction PURE : pas de page, pas de réseau, pas de stockage, rien n'est gardé ni écrit (ni journal, ni console).
const numeros = (() => {
  const SEPARATEURS = /[\s.\-()\u00a0\u202f]/g;
  function normaliserNumero(texte) {
    if (typeof texte !== 'string') return null;
    const brut = texte.trim();
    if (!brut) return null;
    if (/[^\d\s.\-()+\u00a0\u202f]/.test(brut)) return null; // lettres ou autres signes : pas un numéro
    let s = brut.replace(SEPARATEURS, '');
    if (/^00\d+$/.test(s)) s = `+${s.slice(2)}`;
    else if (/^0\d{9}$/.test(s)) s = `+33${s.slice(1)}`;
    else if (!/^\+\d+$/.test(s)) return null;
    if (/^\+330\d{9}$/.test(s)) s = `+33${s.slice(4)}`; // « +33 (0)6 … »
    if (!/^\+[1-9]\d{7,14}$/.test(s)) return null;
    if (s.startsWith('+33') && !/^\+33[1-9]\d{8}$/.test(s)) return null; // un numéro français a 9 chiffres après +33
    return s;
  }
  return Object.freeze({ normaliserNumero });
})();
