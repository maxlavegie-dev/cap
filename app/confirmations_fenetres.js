'use strict';

// 10/11/2026 (accord de Max, c87) : RÉPONDRE AUX FENÊTRES DE CONFIRMATION, à la voix et au double toucher.
// 1. Voix (app.js, ajouterDictee, AVANT tout le reste) : quand une fenêtre de confirmation est ouverte et dit ce qu'elle va
//    faire, « oui » (ou « oui créer », « oui crée-le ») = « Oui » ; « non », « annuler » = « Non » / « Annuler ». La phrase
//    ENTIÈRE doit être l'un de ces mots ; « oui mais… » ou tout autre mot après « oui » / « non » = DOUTE : rien n'est
//    validé, Cap dit de toucher. Garde-fou : la fenêtre de l'annuaire (appel, message) ne se valide JAMAIS à la voix (son
//    verrou écrit : rien sans que Max touche « Oui ») ; « non » et « annuler » y marchent.
// 2. Hors fenêtre : « oui », « non », « annuler », « d'accord », « OK » dits SEULS, sans rien à confirmer (aucune fenêtre qui
//    attend une réponse, aucune proposition ou question de l'IA en attente) : rien n'est rangé dans « À trier » ; Cap dit
//    « Il n'y a rien à confirmer en ce moment ». Toute autre phrase suit son chemin habituel (zéro perte).
// 3. Double toucher (deux appuis à moins de 350 ms et de 40 px, jamais sur un bouton ni un champ) sur une fenêtre de
//    confirmation = « Non » / « Annuler » (rien n'est fait). La fenêtre des chantiers a déjà le sien (chantiers_ecran.js).
// Avant : un « oui » dit à la voix n'appuyait sur aucun bouton et devenait une tâche « oui » dans « À trier ».
const confirmationsFenetres = (() => {
  const plier = s => String(s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]+/g, ' ').trim();
  const PHRASES_OUI = new Set(['oui', 'oui creer', 'oui cree le', 'oui cree']);
  const PHRASES_NON = new Set(['non', 'annuler', 'annule']);
  const MOTS_SEULS = new Set(['oui', 'non', 'annuler', 'annule', 'd accord', 'daccord', 'ok', 'okay']);
  const visible = b => Boolean(b) && !b.hidden && !b.disabled && !(b.closest && b.closest('[hidden]'));

  // Les fenêtres de confirmation : comment savoir si elle attend, où sont « Oui » et « Non ». « oui: null » = jamais à la voix.
  const boutonTexte = (racine, motif) => [...racine.querySelectorAll('button')].find(b => motif.test(b.textContent.trim())) || null;
  const FENETRES = [
    // 11/11/2026 (accord de Max, c126) : la question de « ↺ » dans la visionneuse (« Tout remettre comme au départ ? ») ;
    // en PREMIER : elle est par-dessus tout le reste quand elle est affichée. Son double toucher est dans visionneuse_cap.js.
    { id: 'visionneuse-cap', attend: d => { const q = d.querySelector('#confirmer-depart-visionneuse'); return Boolean(q && !q.hidden); },
      oui: d => d.querySelector('#oui-depart-visionneuse'), non: d => d.querySelector('#non-depart-visionneuse'), doubleToucher: false },
    { id: 'chantiers-cap', attend: d => d.classList.contains('mode-confirmation'),
      oui: d => d.querySelector('#oui-dossier-chantier'), non: d => d.querySelector('#non-dossier-chantier'), doubleToucher: false },
    // 10/11/2026 (c98) : « Tout synchroniser » (son double toucher est dans synchro_tout.js).
    { id: 'synchro-tout', attend: d => d.classList.contains('mode-confirmation'),
      oui: d => d.querySelector('#oui-synchro-tout'), non: d => d.querySelector('#non-synchro-tout'), doubleToucher: false }, // c101 : noms uniques
    // 10/11/2026 (c90) : journaux des relations (son double toucher est dans journaux_relations.js).
    { id: 'journaux-relations', attend: d => d.classList.contains('mode-confirmation'),
      oui: d => d.querySelector('#oui-journal-relation'), non: d => d.querySelector('#non-journal-relation'), doubleToucher: false },
    { id: 'confirmation', attend: () => true,
      oui: d => d.querySelector('#confirmer-abandon'), non: d => d.querySelector('[data-fermer]') },
    { id: 'commande-annuaire', attend: d => Boolean(boutonTexte(d, /^Non$/)),
      oui: null, non: d => boutonTexte(d, /^Non$/), refusOui: 'Pour cela, touche « Oui » toi-même : je ne lance jamais un appel ou un message à la voix.' },
    // Fenêtres de choix (pas de « Oui ») : seulement le double toucher pour « Aucun » / fermer.
    { id: 'scanner-choix-emetteur', attend: () => false, oui: null, non: d => { const b = d.querySelectorAll('#scanner-choix-emetteur-cases button'); return b[b.length - 1] || null; } },
    { id: 'choix-commande', attend: () => false, oui: null, non: d => d.querySelector('#aucun-choix-commande') },
    { id: 'question-date', attend: () => false, oui: null, non: null, fermer: true }
  ];
  // Fenêtres où un mot seul peut être une réponse (on ne le refuse pas) : les confirmations ci-dessus et les choix à la voix.
  const ATTENDENT_UNE_REPONSE = '#choix-commande[open], #choix-voix[open], #question-date[open], #scanner-choix-emetteur[open], #commande-annuaire[open], #confirmation[open], #chantiers-cap[open].mode-confirmation, #journaux-relations[open].mode-confirmation, #synchro-tout[open].mode-confirmation, #visionneuse-cap[open] #confirmer-depart-visionneuse:not([hidden])';

  // « oui », « non », « doute » (commence par oui / non / annuler mais dit autre chose), ou null (autre phrase).
  function analyser(phrase) {
    const p = plier(phrase);
    if (PHRASES_OUI.has(p)) return 'oui';
    if (PHRASES_NON.has(p)) return 'non';
    const premier = p.split(' ')[0];
    if (['oui', 'non', 'annuler', 'annule'].includes(premier)) return 'doute';
    return null;
  }
  const motSeul = phrase => MOTS_SEULS.has(plier(phrase));

  function fenetreOuverte(doc) {
    for (const f of FENETRES) {
      const d = doc.getElementById(f.id);
      if (d && d.open && f.attend(d)) return { f, d };
    }
    return null;
  }

  // Réponse à la voix. null : aucune fenêtre de confirmation ouverte, ou phrase sans rapport (elle suit son chemin).
  // Sinon { resultat: 'oui' | 'non' | 'doute' | 'refus', message }.
  function repondreVoix(doc, phrase) {
    const ouverte = fenetreOuverte(doc);
    if (!ouverte) return null;
    const sens = analyser(phrase);
    if (!sens) return null;
    const { f, d } = ouverte;
    if (sens === 'doute') return { resultat: 'doute', message: 'Je ne suis pas sûr de ce que tu as dit : touche « Oui » ou « Non ». Rien n’a été fait.' };
    if (sens === 'oui') {
      if (!f.oui) return { resultat: 'refus', message: f.refusOui || 'Touche « Oui » toi-même. Rien n’a été fait.' };
      const b = f.oui(d);
      if (!visible(b)) return { resultat: 'doute', message: 'Je ne vois pas de bouton « Oui » à toucher : rien n’a été fait.' };
      b.click();
      return { resultat: 'oui', message: `J’ai touché « ${b.textContent.trim()} ».` };
    }
    const b = f.non && f.non(d);
    if (!visible(b)) return { resultat: 'doute', message: 'Je ne vois pas de bouton « Non » à toucher : rien n’a été fait.' };
    b.click();
    return { resultat: 'non', message: `J’ai touché « ${b.textContent.trim()} » : rien n’a été fait.` };
  }

  // Mot seul hors de toute fenêtre qui attend une réponse : vrai = ne pas le ranger.
  function rienAConfirmer(doc, phrase, { iaEnAttente = false } = {}) {
    if (!motSeul(phrase) || iaEnAttente) return false;
    return !doc.querySelector(ATTENDENT_UNE_REPONSE);
  }

  // Double toucher sur les fenêtres (sauf celle des chantiers, qui a le sien).
  function brancher(doc) {
    for (const f of FENETRES) {
      if (f.doubleToucher === false) continue;
      const d = doc.getElementById(f.id);
      if (!d || d.dataset.doubleToucher) continue;
      d.dataset.doubleToucher = '1';
      let dernier = null;
      d.addEventListener('pointerup', e => {
        if (!d.open || (e.target && e.target.closest && e.target.closest('button, input, textarea, select, a'))) { dernier = null; return; }
        const t = Date.now();
        if (dernier && t - dernier.t < 350 && Math.hypot(e.clientX - dernier.x, e.clientY - dernier.y) < 40) {
          dernier = null;
          if (f.fermer) { d.close(); return; }
          const b = f.non && f.non(d);
          if (visible(b)) b.click();
          return;
        }
        dernier = { t, x: e.clientX, y: e.clientY };
      });
    }
  }

  return { analyser, motSeul, repondreVoix, rienAConfirmer, brancher, FENETRES };
})();

if (typeof document !== 'undefined' && !(typeof window !== 'undefined' && window.CAP_TESTS)) confirmationsFenetres.brancher(document);
