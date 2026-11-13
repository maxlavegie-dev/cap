'use strict';

// Accueil sur l'eau (étape A, 07/11/2026, plan accepté par Max), d'après le travail de Zencoder
// (Cap_eau_essai_v2_2026_11_07, lu sans rien y toucher) :
// - accueil : 3 boutons en colonne (Micro, Chercher, Autre), SOUS l'eau (l'eau passe devant, sans
//   jamais capter un toucher) ; « Chercher » ouvre, en attendant l'étape C, l'écran des tâches ;
// - écran « Autre » : Scanner, Réglages, interrupteur clair / sombre (écrans sur l'eau seulement), Fermer ;
// - écran « Réglages » : les réglages de Cap (textes inchangés) et le curseur d'intensité (MAQUETTE) ;
// - geste net de HAUT EN BAS sur l'accueil (rien d'ouvert) : retour à l'eau seule ;
// - alerte « Redonner l'accès à Google » visible PARTOUT : sous l'eau (sa petite eau à 35 %) sur les
//   écrans de Cap ; posée dans la fenêtre ouverte (musique, visionneuse…), au-dessus de l'eau, sinon.
// Aucun droit Google, aucun champ de connexion : seuls des boutons existants changent de place.
const accueilCap = (() => {
  const CLE_THEME = 'cap_theme_v1';
  const CLE_INTENSITE = 'cap_intensite_eau'; // même clé que la maquette de Zencoder ; NON reliée pour l'instant
  // Couleurs de l'eau en mode sombre : celles de l'eau v2 de Zencoder (fond sombre, pas noir pur).
  const EAU_SOMBRE = Object.freeze([Object.freeze([34, 40, 42]), Object.freeze([16, 20, 22])]);
  // 08/11/2026 (accord de Max) : couleurs de l'eau en mode CLAIR sur les écrans sur l'eau = celles de la visionneuse
  // et du lecteur de Zencoder (avant : tirées du fond pâle de Cap). L'écran des tâches garde l'ancienne eau (étape 2 à part).
  const EAU_CLAIRE = Object.freeze([Object.freeze([201, 227, 221]), Object.freeze([156, 182, 184])]);
  // Geste haut-bas : seuils réglables (accord de Max).
  const GESTE = Object.freeze({
    fractionHauteur: 0.3, // au moins 30 % de la hauteur de l'écran
    rapportVertical: 2, // trajet au moins 2 fois plus vertical qu'horizontal
    dureeMaxMs: 1000, // en moins d'une seconde
    bandeHautPx: 48 // départ ignoré tout en haut (rideau des notifications d'Android)
  });

  // 12/11/2026 (c169) : + « dicteeSaisie » : la dictée du micro pendant le mode « saisie » (remplaçable dans les tests).
  function brancher(doc, { eau = null, stockage = null, maintenant = () => Date.now(), creerPetiteEau = null, creerEauScanner = null,
    dicteeSaisie = () => (typeof dictee !== 'undefined' ? dictee : null) } = {}) {
    const el = id => doc.getElementById(id);
    const racine = doc.documentElement;
    const corps = doc.body;
    const autre = el('ecran-autre');
    const reglages = el('ecran-reglages');
    const bureau = el('ecran-bureau'); // 12/11/2026 (c165) : écran « Bureau » (Documents, Notes)
    const ouvrirChercher = el('ouvrir-chercher');
    const basculerVue = el('basculer-vue');
    const ecranComplet = el('ecran-complet');
    const alerte = el('alerte-google');
    const placeAlerte = alerte ? doc.createComment(' place de l’alerte Google ') : null;
    if (!autre || !reglages || !ouvrirChercher || !basculerVue || !ecranComplet || !alerte) return null;
    alerte.parentNode.insertBefore(placeAlerte, alerte);

    const lire = cle => { try { return stockage ? stockage.getItem(cle) : null; } catch (e) { return null; } };
    const ecrire = (cle, valeur) => { try { if (stockage) stockage.setItem(cle, valeur); } catch (e) { /* rien */ } };
    const vueComplete = () => corps.classList.contains('vue-complete');

    // ----- Écrans « Autre » et « Réglages » -----
    let ecranOuvert = null;
    const micro = el('ecran-micro'); // 08/11/2026 (étape 2)
    const chercher = el('ecran-chercher'); // 09/11/2026 (étape 1 de l'intégration de Zencoder)
    const messageAutre = el('message-autre');
    // 08/11/2026 (accord de Max, étape 1) : ouvertures et retours DOUX (transition_ecrans.js). Avant : montrer
    // faisait directement le travail de montrerDirect (gardé tel quel ci-dessous).
    function montrer(ecran) {
      if (typeof transitionEcrans !== 'undefined') transitionEcrans.changer(doc, () => montrerDirect(ecran));
      else montrerDirect(ecran);
    }
    function montrerDirect(ecran) {
      if (messageAutre) { messageAutre.hidden = true; messageAutre.textContent = ''; }
      if (el('message-bureau')) { el('message-bureau').hidden = true; el('message-bureau').textContent = ''; } // c165
      // 08/11/2026 (étape 2) : l'écran Micro s'ajoute. Avant : for (const e of [autre, reglages]) …
      // 09/11/2026 : + l'écran Chercher. Avant : for (const e of [autre, reglages, micro]) …
      for (const e of [autre, reglages, micro, chercher, bureau]) if (e) e.hidden = e !== ecran; // c165 : + Bureau
      ecranOuvert = ecran;
      racine.classList.toggle('ecran-cap-ouvert', Boolean(ecran));
      appliquerTheme();
    }
    // ----- 09/11/2026 (accord de Max, étape 3) : RÈGLE DU RETOUR : fermer ramène à l'écran d'où l'on vient -----
    // Petite pile EN MÉMOIRE seulement (rien de gardé : après un retour de Google, la page repart de l'accueil).
    // Ouvrir un écran depuis un autre note celui d'où l'on vient ; fermer (bouton, geste, « ferme ») y revient.
    // Rouvrir un écran déjà dans la pile la raccourcit (jamais de boucle). « accueil » et « eau » à la voix la vident
    // (événement « cap-vider-pile »). L'écran d'eau n'y entre jamais. Les fenêtres posées par-dessus ne changent pas.
    // Écrans : 'accueil', 'ecran-autre', 'ecran-reglages', 'ecran-micro', 'ecran-chercher', 'ecran-bureau' (c165), 'taches' (écran des tâches).
    const pile = [];
    const ecranCourant = () => (vueComplete() ? 'taches' : (ecranOuvert ? ecranOuvert.id : 'accueil'));
    function noterDepart(vers) {
      const ici = ecranCourant();
      if (vers === ici) return;
      const deja = pile.indexOf(vers);
      if (deja >= 0) pile.length = deja; // déjà dans la pile : on y revient, sans boucle
      else if (vers === 'accueil') pile.length = 0;
      else pile.push(ici);
    }
    function ouvrirEcran(ecran) {
      noterDepart(ecran ? ecran.id : 'accueil');
      montrer(ecran);
    }
    function revenir() {
      const ici = ecranCourant();
      const avant = pile.pop() || 'accueil';
      const vers = avant === 'accueil' || avant === 'taches' ? null : el(avant);
      const changer = fin => (typeof transitionEcrans !== 'undefined' ? transitionEcrans.changer(doc, fin) : fin());
      changer(() => {
        if (ici === 'taches' && avant !== 'taches' && !ecranComplet.hidden) basculerVue.click(); // ferme l'écran des tâches
        montrerDirect(vers);
        if (avant === 'taches' && ecranComplet.hidden) basculerVue.click();
      });
    }
    doc.addEventListener('cap-vider-pile', () => { pile.length = 0; });
    // Avant le 09/11/2026 : ouvrir = montrer(écran) ; fermer = montrer(null) (toujours l'accueil).
    el('ouvrir-autre').addEventListener('click', () => ouvrirEcran(autre));
    el('ouvrir-reglages-cap').addEventListener('click', () => ouvrirEcran(reglages));
    el('fermer-autre').addEventListener('click', () => revenir());
    if (el('fermer-bureau')) el('fermer-bureau').addEventListener('click', () => revenir()); // c165
    el('fermer-reglages').addEventListener('click', () => revenir());
    // 08/11/2026 (accord de Max, étape 2) : écran Micro. Le micro de l'accueil ouvre l'écran (aucune dictée) ;
    // « + » et le clavier touchent « + » et « Écrire une demande » (même code, mêmes fenêtres).
    // 09/11/2026 : « + » et la nouvelle icône sont dans l'accueil : branchés même sans écran Micro. Avant : if (micro) {
    if (micro || el('rangee-micro-accueil')) {
      const toucher = id => () => { const b = el(id); if (b) b.click(); };
      if (el('ouvrir-micro')) el('ouvrir-micro').addEventListener('click', () => ouvrirEcran(micro)); // 09/11/2026 : pile (avant : montrer)
      if (el('fermer-micro')) el('fermer-micro').addEventListener('click', () => revenir()); // 09/11/2026 : pile (avant : montrer(null))
      if (el('micro-ajouter')) el('micro-ajouter').addEventListener('click', toucher('ajouter'));
      if (el('micro-clavier')) el('micro-clavier').addEventListener('click', toucher('ouvrir-clavier'));
      if (el('micro-ecrire')) el('micro-ecrire').addEventListener('click', toucher('ouvrir-clavier')); // 09/11/2026 : icône provisoire
    }
    // 08/11/2026 (accord de Max) : Notes et Agenda décidés mais pas encore branchés : grisés, un toucher le dit.
    for (const [id, nom] of [['ouvrir-notes', 'Notes'], ['ouvrir-agenda', 'Agenda']]) {
      const bouton = el(id);
      if (bouton && messageAutre) bouton.addEventListener('click', () => { messageAutre.hidden = false; messageAutre.textContent = `${nom} : pas encore prêt.`; });
    }

    // « Chercher » : l'écran des tâches et rendez-vous, avec la barre de recherche (en attendant l'étape C).
    // 09/11/2026 (accord de Max) : solution d'attente REMPLACÉE par l'écran Chercher (ci-dessous) quand il existe.
    // Ligne d'avant, gardée pour une page sans cet écran :
    // ouvrirChercher.addEventListener('click', () => { if (ecranComplet.hidden) basculerVue.click(); });
    if (!chercher) ouvrirChercher.addEventListener('click', () => { if (ecranComplet.hidden) basculerVue.click(); });
    // ----- 09/11/2026 (accord de Max) : écran Chercher (maquette de Zencoder) -----
    // Chaque icône touche le MÊME bouton qu'avant (mêmes fenêtres, mêmes messages, rien en double) :
    // To-do = l'écran des tâches ; Documents = l'œil (visionneuse) ; Média = le Lecteur (musique) ; Photo = grisé.
    // La barre : le texte part dans la recherche de Cap (écran des tâches), résultats tout de suite.
    if (chercher) {
      const messageChercher = el('message-chercher');
      const champ = el('chercher-champ');
      const toucher = id => { const b = el(id); if (b) b.click(); };
      // Chercher disparaît doucement et l'écran des tâches sort du sable (une seule transition).
      function versTaches(texte) {
        noterDepart('taches'); // 09/11/2026 (étape 3) : « Fermer » des tâches ramènera ici
        const changer = fin => (typeof transitionEcrans !== 'undefined' ? transitionEcrans.changer(doc, fin) : fin());
        changer(() => {
          montrerDirect(null);
          if (ecranComplet.hidden) basculerVue.click();
          if (typeof texte === 'string') {
            // 09/11/2026 (partie 2 A) : la source choisie dans Chercher suit la recherche.
            const sourceChercher = el('chercher-source');
            const sourceTaches = el('source-recherche');
            if (sourceChercher && sourceTaches && sourceChercher.value && sourceTaches.querySelector(`option[value="${sourceChercher.value}"]`)) sourceTaches.value = sourceChercher.value;
            const saisie = el('saisie-recherche');
            if (saisie) { saisie.value = texte; saisie.dispatchEvent(new doc.defaultView.Event('input', { bubbles: true })); }
          }
        });
      }
      ouvrirChercher.addEventListener('click', () => {
        if (messageChercher) { messageChercher.hidden = true; messageChercher.textContent = ''; }
        if (champ) champ.value = '';
        if (el('propositions-chercher')) { el('propositions-chercher').replaceChildren(); el('propositions-chercher').hidden = true; } // 09/11/2026
        // 12/11/2026 (décision de Max, c167) : la loupe ouvre (ou referme) la LIGNE DE RECHERCHE de l'accueil ; l'écran Chercher
        // reste caché. Avant : ouvrirEcran(chercher); // 09/11/2026 : pile (avant : montrer(chercher))
        const bandeRecherche = el('bande-recherche-accueil');
        if (bandeRecherche) { bandeRecherche.hidden = !bandeRecherche.hidden; return; }
        ouvrirEcran(chercher);
      });
      el('chercher-todo').addEventListener('click', () => versTaches());
      // 09/11/2026 (accord de Max, mission C) : « À trier » : l'écran des tâches (même chemin que To-do, donc « Fermer »
      // revient à Chercher), ouvert sur la liste « À trier », la dernière phrase en haut (app.js, « cap-ouvrir-a-trier »).
      if (el('chercher-a-trier')) el('chercher-a-trier').addEventListener('click', () => {
        versTaches();
        doc.dispatchEvent(new doc.defaultView.CustomEvent('cap-ouvrir-a-trier'));
      });
      // 10/11/2026 (choix de Max) : 6e icône « Chantiers » : ouvre l'écran « Chantiers » (chantiers_ecran.js l'écoute).
      // Chercher reste dessous : « Fermer » y ramène.
      if (el('chercher-chantiers')) el('chercher-chantiers').addEventListener('click', () => {
        doc.dispatchEvent(new doc.defaultView.CustomEvent('cap-ouvrir-chantiers'));
      });
      el('chercher-documents').addEventListener('click', () => toucher('ouvrir-oeil'));
      el('chercher-media').addEventListener('click', () => toucher('ouvrir-lecteur'));
      el('chercher-photo').addEventListener('click', () => {
        if (messageChercher) { messageChercher.hidden = false; messageChercher.textContent = 'Photo : pas encore prêt.'; }
      });
      if (champ) {
        champ.addEventListener('keydown', e => {
          if (e.key !== 'Enter') return;
          e.preventDefault();
          // 11/11/2026 (accord de Max, c136) : Entrée RESTE dans Chercher : les résultats (ou « Rien trouvé ») s'affichent sous
          // la barre (app.js écoute « cap-chercher-valider ») ; plus de saut vers l'écran des tâches (vue tuiles).
          // Avant : const texte = champ.value.trim(); champ.value = ''; champ.blur(); versTaches(texte);
          champ.blur();
          champ.dispatchEvent(new doc.defaultView.CustomEvent('cap-chercher-valider', { bubbles: true }));
        });
        // c136 : toucher une TÂCHE dans les résultats de Chercher ouvre toujours l'écran des tâches, la tâche surlignée (même
        // chemin qu'avant : « Fermer » revient à Chercher). Avant : la proposition simulait la touche Entrée.
        // ----- 12/11/2026 (accord de Max, c169) : MODE « SAISIE » de l'accueil -----
        // Le champ de la ligne de recherche prend la main (le clavier s'ouvre) : affichage épuré : la barre, et dessous
        // SEULEMENT « + », le micro, le crayon (sur une ligne). Les autres icônes sont CACHÉES (rien effacé) et reviennent
        // quand le champ perd la main, après Entrée, ou quand le clavier se referme (la hauteur visible revient).
        // La bande du micro revient ensuite comme avant ; la ligne de recherche reste ouverte.
        // Décision de Max (choix b) : pendant la saisie, le micro ne sert QU'À LA RECHERCHE : la phrase dite remplit le
        // champ (les propositions suivent) ; aucune commande, rien dans « À trier ». « + » et le crayon gardent leur rôle.
        const navAccueil = el('accueil-boutons');
        const microAccueil = el('microphone');
        const outilsSaisie = ['micro-ajouter', 'micro-ecrire'].map(el).filter(Boolean);
        let saisie = null;
        let clavierVu = false;
        const entrerSaisie = () => {
          if (saisie || !navAccueil || vueComplete() || ecranOuvert) return;
          saisie = { cachesAvant: outilsSaisie.map(b => b.hidden) };
          outilsSaisie.forEach(b => { b.hidden = false; });
          navAccueil.classList.add('mode-saisie');
        };
        const sortirSaisie = () => {
          if (!saisie) return;
          outilsSaisie.forEach((b, i) => { b.hidden = saisie.cachesAvant[i]; });
          saisie = null;
          clavierVu = false;
          navAccueil.classList.remove('mode-saisie');
        };
        champ.addEventListener('focus', entrerSaisie);
        champ.addEventListener('blur', sortirSaisie);
        champ.addEventListener('keydown', e => { if (e.key === 'Enter') sortirSaisie(); });
        // Le clavier d'Android se ferme parfois sans que le champ perde la main : la hauteur visible revient : fin de saisie.
        const vv = doc.defaultView.visualViewport;
        if (vv) {
          let hauteurMax = vv.height;
          vv.addEventListener('resize', () => {
            hauteurMax = Math.max(hauteurMax, vv.height);
            if (!saisie) return;
            if (vv.height < hauteurMax * 0.85) { clavierVu = true; return; }
            if (clavierVu) { champ.blur(); sortirSaisie(); }
          });
        }
        // Pendant la saisie, toucher « + », le micro ou le crayon ne fait pas perdre la main au champ avant leur action
        // (sinon l'affichage bougerait sous le doigt).
        for (const b of [...outilsSaisie, microAccueil].filter(Boolean)) {
          for (const type of ['pointerdown', 'mousedown']) b.addEventListener(type, e => { if (saisie) e.preventDefault(); });
        }
        if (microAccueil) {
          // Le micro pendant la saisie : SA dictée remplit le champ ; le micro habituel (commandes, « À trier ») ne reçoit rien.
          microAccueil.addEventListener('pointerdown', e => { if (saisie) e.stopImmediatePropagation(); }, true);
          microAccueil.addEventListener('click', e => {
            if (!saisie) return;
            e.preventDefault();
            e.stopImmediatePropagation();
            const d = dicteeSaisie();
            if (!d || !d.disponible()) return;
            if (d.enCours()) { d.arreter(); return; }
            microAccueil.setAttribute('aria-pressed', 'true');
            const remplir = texte => { champ.value = String(texte || '').trim(); champ.dispatchEvent(new doc.defaultView.Event('input', { bubbles: true })); };
            d.demarrer({
              surProvisoire: texte => { if (texte) remplir(texte); },
              surFinal: texte => remplir(texte),
              surFin: () => microAccueil.setAttribute('aria-pressed', 'false')
            });
          }, true);
        }
        champ.addEventListener('cap-chercher-vers-taches', e => {
          champ.value = '';
          versTaches(String(e.detail || ''));
        });
      }
      el('fermer-chercher-cap').addEventListener('click', () => { if (champ) champ.value = ''; revenir(); }); // 09/11/2026 : pile (avant : montrer(null))
    }
    const fermerChercher = el('fermer-chercher');
    // 09/11/2026 (étape 3) : « Fermer » de l'écran des tâches revient à l'écran d'où l'on vient (Chercher, Autre…), sinon à
    // l'accueil. Avant : if (!ecranComplet.hidden) basculerVue.click();
    if (fermerChercher) fermerChercher.addEventListener('click', () => { if (!ecranComplet.hidden) revenir(); });

    // ----- Mode clair / sombre (écrans sur l'eau seulement ; l'écran des tâches reste clair) -----
    let sombre = lire(CLE_THEME) !== 'clair';
    const boutonTheme = el('bouton-theme-cap');
    function appliquerTheme() {
      const surEau = !vueComplete();
      racine.classList.toggle('theme-cap-sombre', sombre);
      racine.classList.toggle('theme-cap-clair', !sombre);
      if (boutonTheme) boutonTheme.setAttribute('aria-checked', String(sombre));
      // Sombre sur l'eau : couleurs ET effets de l'eau v2 de Zencoder (liseré de crête, houle, lumière).
      const v2 = typeof ecranEau !== 'undefined' ? ecranEau.EAU_V2 : null;
      // 08/11/2026 : clair sur l'eau = couleurs de Zencoder (EAU_CLAIRE) ; écran des tâches = ancienne eau (null).
      const couleurs = surEau ? (sombre ? EAU_SOMBRE : EAU_CLAIRE).map(c => [...c]) : null;
      if (eau && typeof eau.changerCouleurs === 'function') eau.changerCouleurs(couleurs, sombre && surEau ? v2 : null);
    }
    if (boutonTheme) boutonTheme.addEventListener('click', () => { sombre = !sombre; ecrire(CLE_THEME, sombre ? 'sombre' : 'clair'); appliquerTheme(); });
    // L'écran des tâches s'ouvre ou se ferme : l'eau reprend la bonne couleur.
    new doc.defaultView.MutationObserver(appliquerTheme).observe(corps, { attributes: true, attributeFilter: ['class'] });

    // ----- 12/11/2026 (accord de Max, c163) : NOUVEL ACCUEIL, grille 3 × 4. RÈGLE D'OR : chaque icône qui a un lien TOUCHE
    // l'ancien bouton (même destination, mêmes fenêtres, même retour : « Fermer » ramène à l'accueil quand on vient de
    // l'accueil). Sans lien : grisée, « Il n'y a pas encore de lien ». L'interrupteur et le nombre de scans en attente
    // sont ceux de l'écran Autre (recopiés, jamais en double).
    const LIENS_ACCUEIL = Object.freeze({ 'accueil-todo': 'chercher-todo', 'accueil-media': 'chercher-media', 'accueil-chantiers': 'chercher-chantiers',
      'accueil-oeil': 'ouvrir-oeil', 'accueil-a-trier': 'chercher-a-trier', 'accueil-scanner': 'ouvrir-scanner',
      'accueil-reglages': 'ouvrir-reglages-cap', 'accueil-theme': 'bouton-theme-cap' });
    for (const [id, ancien] of Object.entries(LIENS_ACCUEIL)) {
      if (el(id)) el(id).addEventListener('click', () => { const b = el(ancien); if (b) b.click(); });
    }
    // 12/11/2026 (accord de Max, c165) : l'icône page cornée ouvre l'écran « Bureau » ; « Documents » y touche l'ancien bouton
    // « Documents » de Chercher (la visionneuse, comme avant) ; « Notes » : grisée. Avant (c163) : elle touchait directement
    // « Documents » de Chercher.
    if (el('accueil-bureau') && bureau) el('accueil-bureau').addEventListener('click', () => ouvrirEcran(bureau));
    if (el('bureau-documents')) el('bureau-documents').addEventListener('click', () => { const b = el('chercher-documents'); if (b) b.click(); });
    const messageBureau = el('message-bureau');
    if (el('bureau-notes') && messageBureau) el('bureau-notes').addEventListener('click', () => { messageBureau.textContent = 'Il n’y a pas encore de lien.'; messageBureau.hidden = false; });
    const messageAccueil = el('message-accueil');
    let minuteurMessageAccueil = null;
    for (const b of doc.querySelectorAll('#accueil-boutons .bouton-pas-pret')) {
      b.addEventListener('click', () => {
        if (!messageAccueil) return;
        messageAccueil.textContent = 'Il n’y a pas encore de lien.';
        messageAccueil.hidden = false;
        clearTimeout(minuteurMessageAccueil);
        minuteurMessageAccueil = setTimeout(() => { messageAccueil.hidden = true; }, 4000);
      });
    }
    const themeAccueil = el('accueil-theme');
    if (themeAccueil && boutonTheme) {
      const suivreTheme = () => themeAccueil.setAttribute('aria-checked', boutonTheme.getAttribute('aria-checked') || 'true');
      suivreTheme();
      new doc.defaultView.MutationObserver(suivreTheme).observe(boutonTheme, { attributes: true, attributeFilter: ['aria-checked'] });
    }
    const scansAutre = el('scans-en-attente'); const scansAccueil = el('scans-accueil');
    if (scansAutre && scansAccueil) {
      const suivreScans = () => { scansAccueil.textContent = scansAutre.textContent; scansAccueil.hidden = scansAutre.hidden; };
      suivreScans();
      new doc.defaultView.MutationObserver(suivreScans).observe(scansAutre, { attributes: true, attributeFilter: ['hidden'], childList: true, characterData: true, subtree: true });
    }

    // ----- Curseur d'intensité : MAQUETTE (valeur gardée sous la clé de Zencoder, ne commande rien) -----
    const curseur = el('curseur-intensite-eau');
    if (curseur) {
      const gardee = Number(lire(CLE_INTENSITE));
      curseur.value = String(lire(CLE_INTENSITE) !== null && gardee >= 0 && gardee <= 100 ? gardee : 100);
      curseur.addEventListener('input', () => ecrire(CLE_INTENSITE, curseur.value));
    }

    // ----- Geste net de HAUT EN BAS sur l'accueil : retour à l'eau seule -----
    let depart = null;
    const accueilLibre = () => !vueComplete() && !ecranOuvert && !doc.querySelector('dialog[open]')
      && !racine.classList.contains('eau-ouverte');
    function retourEau() {
      const allerEau = el('aller-eau');
      if (allerEau) allerEau.click(); // même chemin que l'ancien bouton « Eau » (rien si l'eau est arrêtée)
    }
    doc.addEventListener('touchstart', e => {
      depart = null;
      if (e.touches.length !== 1 || !accueilLibre()) return;
      const cible = e.target && e.target.closest ? e.target : null;
      if (cible && cible.closest('input, textarea, select, #alerte-google, #ecran-eau')) return;
      const t = e.touches[0];
      if (t.clientY < GESTE.bandeHautPx) return;
      depart = { x: t.clientX, y: t.clientY, quand: maintenant() };
    }, { passive: true });
    doc.addEventListener('touchmove', e => { if (depart && e.touches.length !== 1) depart = null; }, { passive: true });
    doc.addEventListener('touchend', e => {
      const d = depart;
      depart = null;
      if (!d || e.touches.length || e.changedTouches.length !== 1 || !accueilLibre()) return;
      const t = e.changedTouches[0];
      const bas = t.clientY - d.y;
      const cote = Math.abs(t.clientX - d.x);
      const hauteur = doc.defaultView.innerHeight || 1;
      if (!(bas >= GESTE.fractionHauteur * hauteur && bas >= GESTE.rapportVertical * cote && maintenant() - d.quand <= GESTE.dureeMaxMs)) return;
      // 12/11/2026 (décision de Max, c167) : ligne de recherche ouverte : le geste la FERME (comme un écran) ; sinon, l'eau.
      const bandeRecherche = el('bande-recherche-accueil');
      if (bandeRecherche && !bandeRecherche.hidden) { bandeRecherche.hidden = true; return; }
      retourEau();
    }, { passive: true });
    doc.addEventListener('touchcancel', () => { depart = null; }, { passive: true });

    // ----- Alerte Google partout -----
    let petiteEau = null;
    // Eau de l'accueil en PAUSE pendant la musique et la visionneuse (fenêtres plein écran, qui la cachent) :
    // batterie (accord de Max, 07/11/2026) ; elle repart à la fermeture si l'eau est en marche.
    let eauEnPause = false;
    function pauseEau(fenetres) {
      const pleinEcran = fenetres.some(f => f.classList.contains('plein-ecran'));
      // 09/11/2026 (défaut 1) : filet de sécurité : sans fenêtre plein écran, l'eau en marche qui se serait arrêtée repart
      // (elle ne restait arrêtée qu'en changeant d'écran).
      if (eau && eau.fond && !pleinEcran && !eauEnPause && typeof eau.fond.etat === 'function' && !eau.fond.etat().active
        && (typeof eau.eauActive !== 'function' || eau.eauActive()) && !racine.classList.contains('eau-ouverte')) eau.fond.demarrer();
      if (!eau || !eau.fond || pleinEcran === eauEnPause) return;
      eauEnPause = pleinEcran;
      if (pleinEcran) eau.fond.arreter();
      else if ((typeof eau.eauActive !== 'function' || eau.eauActive()) && !racine.classList.contains('eau-ouverte')) eau.fond.demarrer();
    }
    // 08/11/2026 (lot D, accord de Max) : écran de scan = même fond et même eau que les autres écrans (couleurs du
    // mode clair ou sombre), animée seulement pendant qu'il est ouvert ; l'eau de l'accueil, cachée, est en pause.
    let eauScanner = null;
    function eauDuScanner() {
      const scanner = el('scanner');
      const toile = el('eau-scanner');
      if (!scanner || !toile) return;
      if (scanner.open && !eauScanner && typeof creerEauScanner === 'function') {
        eauScanner = creerEauScanner(toile);
        if (eauScanner) {
          const fenetre = doc.defaultView;
          const position = e => [e.clientX / (fenetre.innerWidth || 1), e.clientY / (fenetre.innerHeight || 1)];
          const reglages = typeof ecranEau !== 'undefined' ? ecranEau : null;
          // 08/11/2026 (accord de Max) : traînée continue entre deux positions du doigt (tracer), si l'eau la connaît.
          let dernier = null;
          scanner.addEventListener('pointerdown', e => { dernier = position(e); if (reglages) eauScanner.perturber(...dernier, reglages.EAU.forcePose, reglages.EAU.rayon); }, { passive: true });
          scanner.addEventListener('pointermove', e => {
            if (!reglages || !e.buttons) return;
            const p = position(e);
            if (dernier && typeof eauScanner.tracer === 'function') eauScanner.tracer(...dernier, ...p, reglages.forceGlisse(doc), reglages.EAU.rayon);
            else eauScanner.perturber(...p, reglages.forceGlisse(doc), reglages.EAU.rayon);
            dernier = p;
          }, { passive: true });
        }
      }
      if (!eauScanner) return;
      if (scanner.open) {
        const v2 = typeof ecranEau !== 'undefined' ? ecranEau.EAU_V2 : null;
        eauScanner.changerCouleurs((sombre ? EAU_SOMBRE : EAU_CLAIRE).map(c => [...c]), sombre ? v2 : null);
        eauScanner.demarrer();
      } else {
        eauScanner.arreter();
      }
    }
    // 09/11/2026 (accord de Max) : le petit micro de tous les écrans suit la fenêtre ouverte du dessus (comme la note de
    // musique) ; sans fenêtre, il est sur la page. Il ne bouge pas à l'écran (position fixe, en haut à droite).
    function placerPetitMicro(fenetres) {
      const petit = el('petit-micro');
      if (!petit) return;
      const dessus = fenetres.length ? fenetres[fenetres.length - 1] : corps;
      // 11/11/2026 (accord de Max, c118) : visionneuse : le micro, le livre et la synchronisation vont DANS son menu (bouton
      // rond blanc), en ligne ; partout ailleurs, rien ne change. La bulle et le signe restent dans la fenêtre (visibles).
      const menuVision = dessus.id === 'visionneuse-cap' ? el('menu-visionneuse-communs') : null;
      const hote = menuVision || dessus;
      if (petit.parentNode !== hote) hote.appendChild(petit);
      const bulle = el('bulle-micro'); // 09/11/2026 : la bulle suit le micro
      if (bulle && bulle.parentNode !== dessus) dessus.appendChild(bulle);
      const signe = el('signe-micro'); // 09/11/2026 (étape 4) : le pouce et la croix aussi
      if (signe && signe.parentNode !== dessus) dessus.appendChild(signe);
      const apprendre = el('bouton-apprendre'); // 09/11/2026 : le bouton « phrase à apprendre » aussi
      if (apprendre && apprendre.parentNode !== hote) hote.appendChild(apprendre); // c118 : hote (menu de la visionneuse)
      const synchro = el('bouton-synchro'); // 10/11/2026 (c98) : « Tout synchroniser » aussi
      if (synchro && synchro.parentNode !== hote) hote.appendChild(synchro);
    }
    // 09/11/2026 (défaut 5 vu par Max : pas de micro dans la fenêtre de gros choix ouverte par-dessus « Musique ») : la
    // fenêtre du DESSUS est la dernière OUVERTE (ordre d'ouverture), pas la dernière dans la page. Avant :
    // const fenetres = [...doc.querySelectorAll('dialog[open]')]; (ordre de la page : le micro partait dans « Musique », cachée).
    const ordreOuverture = [];
    function fenetresOuvertes() {
      const ouvertes = [...doc.querySelectorAll('dialog[open]')];
      for (let i = ordreOuverture.length - 1; i >= 0; i--) if (!ouvertes.includes(ordreOuverture[i])) ordreOuverture.splice(i, 1);
      for (const d of ouvertes) if (!ordreOuverture.includes(d)) ordreOuverture.push(d);
      return [...ordreOuverture];
    }
    function placerAlerte() {
      const fenetres = fenetresOuvertes();
      placerPetitMicro(fenetres); // 09/11/2026
      pauseEau(fenetres);
      eauDuScanner();
      const cible = fenetres.length ? fenetres[fenetres.length - 1] : null;
      if (cible) {
        if (alerte.parentNode !== cible) cible.appendChild(alerte);
      } else if (alerte.previousSibling !== placeAlerte) {
        placeAlerte.parentNode.insertBefore(alerte, placeAlerte.nextSibling);
      }
      // Sous l'eau seulement sur les écrans de Cap (pas dans une fenêtre) et seulement si elle est visible.
      const sousEau = !cible && !alerte.hidden;
      alerte.classList.toggle('alerte-sous-eau', sousEau);
      alerte.classList.toggle('alerte-dans-fenetre', Boolean(cible));
      racine.classList.toggle('alerte-google-visible', !alerte.hidden);
      if (!alerte.hidden) racine.style.setProperty('--hauteur-alerte', `${Math.ceil(alerte.getBoundingClientRect().height) + 16}px`);
      if (!petiteEau && sousEau && typeof creerPetiteEau === 'function') petiteEau = creerPetiteEau(el('eau-alerte'));
      if (petiteEau) { if (sousEau) petiteEau.demarrer(); else petiteEau.arreter(); }
    }
    const observateur = new doc.defaultView.MutationObserver(placerAlerte);
    observateur.observe(doc.body, { subtree: true, attributes: true, attributeFilter: ['open', 'hidden'] });
    placerAlerte();
    // 11/11/2026 (c118) : le menu du bouton rond blanc de la visionneuse (où ce code range le micro, le livre et la synchronisation).
    try { if (typeof visionneuseCap !== 'undefined' && visionneuseCap.brancherMenu) visionneuseCap.brancherMenu(doc); } catch (e) { /* rien */ }
    appliquerTheme();

    // 09/11/2026 : + pile (lecture seule, pour les essais).
    return { GESTE, montrer, placerAlerte, retourEau, theme: () => (sombre ? 'sombre' : 'clair'), ecranOuvert: () => ecranOuvert, eauScanner: () => eauScanner,
      pile: () => [...pile] };
  }

  return { CLE_THEME, CLE_INTENSITE, EAU_SOMBRE, EAU_CLAIRE, GESTE, brancher };
})();

if (typeof document !== 'undefined' && !(typeof window !== 'undefined' && window.CAP_TESTS)) {
  let stockage = null;
  try { stockage = window.localStorage; } catch (e) { stockage = null; }
  accueilCap.instance = accueilCap.brancher(document, {
    eau: (typeof ecranEau !== 'undefined' && ecranEau.instance) || null,
    stockage,
    // Petite eau de l'alerte : la même eau que partout, en moins fine (petite surface).
    creerPetiteEau: toile => (toile && typeof ecranEau !== 'undefined' ? ecranEau.creerCouche(toile, { cellules: 6000 }) : null),
    // 08/11/2026 (lot D) : eau de l'écran de scan : la même eau que partout (même finesse).
    creerEauScanner: toile => (toile && typeof ecranEau !== 'undefined' ? ecranEau.creerCouche(toile) : null)
  });
}
