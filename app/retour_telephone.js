'use strict';

// 13/11/2026 (accord de Max, décision A) : la touche RETOUR DU TÉLÉPHONE.
// La coque Android (MainActivity.onBackPressed) demande à la page : « y a-t-il quelque chose à fermer ? ». Ce module ferme
// alors la chose la PLUS HAUTE, UNE SEULE à la fois, et répond vrai ; s'il ne reste rien à fermer, il répond faux et la
// coque met Cap en arrière-plan (Cap reste en mémoire, rien n'est perdu).
// Ordre, du dessus vers le dessous :
//   1. la fenêtre (dialog) ouverte en DERNIER. Elle se ferme par son propre chemin, comme au doigt :
//      - visionneuse : son bouton caché « fermer-visionneuse » (site ou vidéo d'abord, puis la grille des chantiers, puis
//        la visionneuse : visionneuse_cap.js et visionneuse_web.js) ;
//      - lecteur MP3 qui joue : il passe en arrière-plan (la musique continue, comme « retourne à l'accueil ») ;
//      - fenêtre où Max a écrit : la question « Garder / Jeter » de fermeture_fenetres.js (rien de tapé n'est perdu) ;
//      - sinon son bouton « Fermer » visible ; sinon comme la touche Échap (événement « cancel », puis fermeture) ;
//      - SÉCURITÉ : si la même fenêtre est toujours ouverte au retour suivant (au moins 600 ms après) alors que son « Fermer »
//        a été touché, elle est fermée comme par Échap (une fenêtre ne bloque jamais le retour), SAUF si elle pose la question
//        « Garder / Jeter » (ce que Max a tapé n'est jamais perdu).
//   2. l'écran de Cap ouvert (Autre, Bureau, Chercher, Réglages, Micro) : son bouton « Fermer » (caché ou non) ;
//   3. « Tout voir » (la liste complète) : son « Fermer » ;
//   4. la ligne de recherche de l'accueil : cachée.
// Rien d'autre : l'accueil et l'écran d'eau ne se « ferment » pas (le retour quitte alors Cap). Aucun réseau, rien d'écrit.
const retourTelephone = (() => {
  const FERMER_ECRANS = Object.freeze({ 'ecran-autre': 'fermer-autre', 'ecran-reglages': 'fermer-reglages', 'ecran-micro': 'fermer-micro', 'ecran-chercher': 'fermer-chercher-cap', 'ecran-bureau': 'fermer-bureau' });
  // Fenêtres dont le bouton de fermeture est CACHÉ (il libère la mémoire, ferme d'abord ce qui est dessus).
  const FERMER_CACHES = Object.freeze({ 'visionneuse-cap': 'fermer-visionneuse' });

  function brancher(doc, {
    fermetureFenetres = null,
    maintenant = () => Date.now(),
    lecteurMp3 = () => (typeof relationsMp3 !== 'undefined' ? relationsMp3.instance : null)
  } = {}) {
    const el = id => doc.getElementById(id);
    // L'ordre d'ouverture des fenêtres : la dernière ouverte est au-dessus.
    const ordre = [];
    const noter = f => {
      const i = ordre.indexOf(f);
      if (i >= 0) ordre.splice(i, 1);
      if (f.open) ordre.push(f);
    };
    const Observateur = doc.defaultView && doc.defaultView.MutationObserver;
    const observateur = Observateur ? new Observateur(liste => {
      for (const m of liste) if (m.target && m.target.tagName === 'DIALOG') noter(m.target);
    }) : null;
    if (observateur) observateur.observe(doc.documentElement, { subtree: true, attributes: true, attributeFilter: ['open'] });

    function fenetreDuDessus() {
      const ouvertes = Array.from(doc.querySelectorAll('dialog[open]'));
      if (!ouvertes.length) return null;
      // Notées : la plus récente ; jamais notée (ouverte avant le branchement) : la dernière dans la page.
      const notees = ordre.filter(f => f.open && f.isConnected);
      return notees.length ? notees[notees.length - 1] : ouvertes[ouvertes.length - 1];
    }

    const visible = b => Boolean(b && !b.disabled && b.getClientRects().length > 0);
    const boutonFermer = f => Array.from(f.querySelectorAll('button')).find(b => b.textContent.trim() === 'Fermer' && visible(b)) || null;

    let dernier = null; // { fenetre, quand } : le dernier « Fermer » touché par le retour
    const DELAI_SECOURS_MS = 600;
    function commeEchap(f) {
      const annulation = new doc.defaultView.Event('cancel', { cancelable: true });
      f.dispatchEvent(annulation);
      if (!annulation.defaultPrevented && f.open) f.close();
      return true;
    }
    function fermerFenetre(f) {
      const question = Boolean(f.querySelector('.question-fermeture'));
      if (!question && dernier && dernier.fenetre === f && maintenant() - dernier.quand >= DELAI_SECOURS_MS) { dernier = null; return commeEchap(f); }
      const cache = FERMER_CACHES[f.id] ? el(FERMER_CACHES[f.id]) : null;
      if (cache) { cache.click(); dernier = f.open ? { fenetre: f, quand: maintenant() } : null; return true; } // sécurité aussi (son « cancel » fait le même nettoyage)
      if (f.id === 'lecteur-mp3-relations') {
        const l = lecteurMp3();
        if (l && l.etat && l.etat().actif && typeof l.arrierePlan === 'function') { l.arrierePlan(); return true; }
      }
      if (fermetureFenetres && typeof fermetureFenetres.gerer === 'function' && fermetureFenetres.gerer(f, fin => fin())) return true;
      const bouton = boutonFermer(f);
      if (bouton) { bouton.click(); dernier = f.open ? { fenetre: f, quand: maintenant() } : null; return true; }
      return commeEchap(f);
    }

    // Ferme UNE chose (la plus haute). Vrai si quelque chose a été fermé (ou une question posée) ; faux : rien à fermer.
    function retour() {
      if (observateur) for (const m of observateur.takeRecords()) if (m.target && m.target.tagName === 'DIALOG') noter(m.target); // ouvertures toutes récentes
      const f = fenetreDuDessus();
      if (f) return fermerFenetre(f);
      const ecran = doc.querySelector('.ecran-cap:not([hidden])');
      if (ecran) {
        const b = FERMER_ECRANS[ecran.id] ? el(FERMER_ECRANS[ecran.id]) : boutonFermer(ecran);
        if (b) { b.click(); return true; }
      }
      if (doc.body && doc.body.classList.contains('vue-complete') && el('fermer-chercher')) { el('fermer-chercher').click(); return true; }
      const bande = el('bande-recherche-accueil');
      if (bande && !bande.hidden) { bande.hidden = true; return true; }
      return false;
    }

    return { retour, fenetreDuDessus };
  }

  return { FERMER_ECRANS, FERMER_CACHES, brancher };
})();

// Dans Cap (pas dans les tests) : le point d'entrée appelé par la coque Android, et seulement lui.
if (typeof document !== 'undefined' && !(typeof window !== 'undefined' && window.CAP_TESTS)) {
  retourTelephone.instance = retourTelephone.brancher(document, {
    fermetureFenetres: typeof fermetureFenetres !== 'undefined' ? fermetureFenetres : null
  });
  window.capRetourTelephone = () => {
    try { return retourTelephone.instance ? retourTelephone.instance.retour() === true : false; } catch (erreur) {
      // Panne inattendue : Cap ne se quitte PAS s'il reste une fenêtre ; la plus haute est fermée comme par Échap.
      const ouvertes = document.querySelectorAll('dialog[open]');
      if (!ouvertes.length) return false;
      try { ouvertes[ouvertes.length - 1].close(); } catch (e) { /* rien */ }
      return true;
    }
  };
}
