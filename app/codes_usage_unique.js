'use strict';

// 13/11/2026 (accord de Max, marche P1 de la copie des échanges du téléphone) : DÉTECTEUR DE CODES À USAGE UNIQUE.
// Règle de Max : les codes de confirmation ou de sécurité reçus par message ne sont JAMAIS copiés ni gardés, seulement
// comptés ; en cas de doute, le message va dans « À trier, en attente » et n'est pas copié sans le Oui de Max.
// analyser(texte) rend { sorte, raison } :
//   - 'code'   : exclu (jamais copié) ;
//   - 'doute'  : « À trier, en attente » (pas copié sans le Oui de Max) ;
//   - 'normal' : peut être copié.
// Le code lui-même n'est JAMAIS rendu, ni gardé, ni écrit (ni journal, ni sortie de débogage). Fonction PURE : pas de page, pas de
// réseau, pas de stockage. Règles (prudentes : mieux vaut un doute qu'un code copié) :
//   - préfixe Android « <#> » (messages de vérification automatique) : code ;
//   - un JETON (4 à 8 chiffres, éventuellement « 123 456 » ou « G-123456 ») ET un mot FORT (code, OTP, usage unique…) : code ;
//   - un jeton ET au moins deux mots FAIBLES (confirmation, sécurité, valable, ne le communiquez…) : code ;
//   - un jeton ET un seul mot faible : doute ;
//   - un mot fort SANS jeton (code écrit autrement, coupé…) : doute ;
//   - un jeton presque seul (message de 3 mots au plus) : doute ;
//   - sinon : normal. Les dates, heures, montants, pourcentages et numéros de téléphone ne sont pas des jetons.
const codesUsageUnique = (() => {
  const FORTS = [
    'code', 'codes', 'otp', 'usage unique', 'mot de passe', 'passcode', 'one-time', 'one time', 'verification code',
    'security code', 'login code', 'pin'
  ];
  const FAIBLES = [
    'confirmation', 'confirmer', 'verification', 'verifier', 'securite', 'securise', 'authentification', 'authentifier',
    'valable', 'expire', 'expirera', 'ne le communiquez', 'ne communiquez', 'ne le partagez', 'ne partagez', 'ne le donnez',
    'ne donnez', 'connexion', 'identification', 'verify', 'confirm', 'do not share', "don't share", 'expires', 'valid for'
  ];
  const plier = t => String(t).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const contient = (texte, mot) => new RegExp(`(?<![a-z])${mot.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(?![a-z])`).test(texte);

  // Retire ce qui ressemble à des chiffres mais n'est pas un code : dates, heures, montants, pourcentages, téléphones.
  function sansFauxJetons(t) {
    return t
      .replace(/\b\d{1,2}[/.-]\d{1,2}(?:[/.-]\d{2,4})?\b/g, ' ')                 // dates 12/03, 12/03/2026
      .replace(/\b\d{4}-\d{2}(?:-\d{2})?\b/g, ' ')                               // 2026-11, 2026-11-13
      .replace(/\b\d{1,2}\s?[h:]\s?\d{2}\b/g, ' ')                               // heures 14:30, 14h30
      .replace(/\d+(?:[.,]\d+)?\s?(?:€|eur|euros?|%|\$)/g, ' ')                  // montants, pourcentages
      .replace(/(?:€|\$)\s?\d+(?:[.,]\d+)?/g, ' ')
      .replace(/\+?\d(?:[\s.-]?\d){8,}/g, ' ');                                  // numéros longs (téléphones…)
  }
  function aUnJeton(t) {
    const net = sansFauxJetons(t);
    return /(?<![\w-])(?:[a-z]-)?\d{4,8}(?![\w-])/.test(net) || /(?<![\w-])\d{3}[ -]\d{3}(?![\w-])/.test(net);
  }

  function analyser(texte) {
    if (typeof texte !== 'string' || !texte.trim()) return { sorte: 'normal', raison: 'vide' };
    if (/^\s*<#>/.test(texte)) return { sorte: 'code', raison: 'prefixe-android' };
    // « code postal », « code promo », « code de la route » : le mot « code » n'y désigne pas un code de sécurité.
    const t = plier(texte).replace(/\bcodes? (?:postal|postaux|promo|promotionnel|de la route)\b/g, ' ');
    const jeton = aUnJeton(t);
    const fort = FORTS.some(m => contient(t, m));
    const faibles = FAIBLES.filter(m => contient(t, m)).length;
    if (jeton && fort) return { sorte: 'code', raison: 'jeton-et-mot-fort' };
    if (jeton && faibles >= 2) return { sorte: 'code', raison: 'jeton-et-mots-faibles' };
    if (jeton && faibles === 1) return { sorte: 'doute', raison: 'jeton-et-un-mot-faible' };
    if (fort) return { sorte: 'doute', raison: 'mot-fort-sans-jeton' };
    if (jeton && t.trim().split(/\s+/).length <= 3) return { sorte: 'doute', raison: 'jeton-presque-seul' };
    return { sorte: 'normal', raison: 'rien' };
  }

  // Comptage d'une liste : des NOMBRES seulement (aucun texte rendu).
  function compter(textes) {
    const n = { code: 0, doute: 0, normal: 0 };
    for (const x of textes || []) n[analyser(x).sorte]++;
    return n;
  }

  return { analyser, compter };
})();
