'use strict';

const tuiles = (() => {
  const delaiAppuiLong = 500;
  let glissement = null;

  function noeud(balise, classe, texte) {
    const element = document.createElement(balise);
    if (classe) element.className = classe;
    if (texte !== undefined) element.textContent = texte;
    return element;
  }

  function iconeMicro() {
    const espace = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(espace, 'svg');
    svg.setAttribute('viewBox', '0 0 32 32');
    svg.setAttribute('width', '22');
    svg.setAttribute('height', '22');
    svg.setAttribute('fill', 'none');
    svg.setAttribute('stroke', 'currentColor');
    svg.setAttribute('stroke-width', '2');
    svg.setAttribute('stroke-linecap', 'round');
    svg.setAttribute('aria-hidden', 'true');
    svg.setAttribute('focusable', 'false');
    const rect = document.createElementNS(espace, 'rect');
    for (const [nom, valeur] of Object.entries({ x: 12, y: 4, width: 8, height: 15, rx: 4 })) rect.setAttribute(nom, valeur);
    const chemin = document.createElementNS(espace, 'path');
    chemin.setAttribute('d', 'M8 15v1a8 8 0 0 0 16 0v-1M16 24v5M12 29h8');
    svg.append(rect, chemin);
    return svg;
  }

  function creerTuile({ id, titre, compteur, classe = '', couleur, categorie, micro, deplacable }, rappels) {
    const tuile = noeud('div', `tuile ${classe}`.trim());
    tuile.dataset.tuile = id;
    if (categorie !== undefined) tuile.dataset.categorie = categorie;
    if (couleur) tuile.style.setProperty('--couleur-categorie', couleur);
    const ouvrir = noeud('button', 'ouvrir-tuile');
    ouvrir.type = 'button';
    ouvrir.append(noeud('span', 'titre-tuile', titre));
    if (compteur !== undefined) ouvrir.append(noeud('span', 'compteur-tuile', `(${compteur})`));
    ouvrir.setAttribute('aria-label', compteur !== undefined ? `${titre} (${compteur})` : titre);
    ouvrir.addEventListener('click', event => {
      if (tuile.dataset.vientDeGlisser === '1') {
        delete tuile.dataset.vientDeGlisser;
        event.preventDefault();
        return;
      }
      rappels.surOuvrir(id, categorie);
    });
    tuile.append(ouvrir);
    if (micro) {
      const bouton = noeud('button', 'micro-tuile');
      bouton.type = 'button';
      bouton.setAttribute('aria-label', `Dicter une tâche dans ${titre}`);
      bouton.append(iconeMicro());
      bouton.addEventListener('click', () => rappels.surMicro(categorie, bouton));
      tuile.append(bouton);
    }
    if (deplacable) {
      tuile.classList.add('deplacable');
      activerDeplacement(tuile, ouvrir, rappels);
    }
    return tuile;
  }

  function finirGlissement(annule) {
    const etat = glissement;
    glissement = null;
    if (!etat) return;
    clearTimeout(etat.minuteur);
    document.removeEventListener('pointermove', etat.bouger);
    document.removeEventListener('pointerup', etat.lacher);
    document.removeEventListener('pointercancel', etat.annuler);
    document.removeEventListener('touchmove', etat.bloquer);
    if (!etat.actif) return;
    etat.tuile.classList.remove('en-deplacement');
    etat.tuile.dataset.vientDeGlisser = '1';
    setTimeout(() => { delete etat.tuile.dataset.vientDeGlisser; }, 400);
    if (annule) return;
    const conteneur = etat.tuile.parentElement;
    if (!conteneur) return;
    const noms = Array.from(conteneur.querySelectorAll('.tuile.deplacable')).map(tuile => tuile.dataset.categorie);
    if (JSON.stringify(noms) !== JSON.stringify(etat.depart)) etat.rappels.surOrdre(noms);
  }

  function activerDeplacement(tuile, poignee, rappels) {
    tuile.addEventListener('contextmenu', event => event.preventDefault());
    poignee.addEventListener('pointerdown', event => {
      if (event.button !== 0 || glissement) return;
      const conteneur = tuile.parentElement;
      const etat = {
        tuile, rappels, actif: false, x: event.clientX, y: event.clientY,
        depart: Array.from(conteneur.querySelectorAll('.tuile.deplacable')).map(item => item.dataset.categorie)
      };
      etat.bouger = mouvement => {
        if (!etat.actif) {
          if (Math.hypot(mouvement.clientX - etat.x, mouvement.clientY - etat.y) > 10) finirGlissement(true);
          return;
        }
        const dessous = document.elementFromPoint(mouvement.clientX, mouvement.clientY)?.closest('.tuile.deplacable');
        if (!dessous || dessous === tuile || dessous.parentElement !== tuile.parentElement) return;
        const avant = tuile.compareDocumentPosition(dessous) & Node.DOCUMENT_POSITION_FOLLOWING;
        if (avant) dessous.after(tuile);
        else dessous.before(tuile);
      };
      etat.lacher = () => finirGlissement(false);
      etat.annuler = () => finirGlissement(true);
      etat.bloquer = toucher => { if (etat.actif && toucher.cancelable) toucher.preventDefault(); };
      etat.minuteur = setTimeout(() => {
        etat.actif = true;
        tuile.classList.add('en-deplacement');
        if (typeof navigator !== 'undefined' && navigator.vibrate) navigator.vibrate(30);
        rappels.surDebutDeplacement?.(tuile.dataset.categorie);
      }, delaiAppuiLong);
      glissement = etat;
      document.addEventListener('pointermove', etat.bouger);
      document.addEventListener('pointerup', etat.lacher);
      document.addEventListener('pointercancel', etat.annuler);
      document.addEventListener('touchmove', etat.bloquer, { passive: false });
    });
  }

  function afficher(conteneur, { fixes = [], categories = [], finales = [] }, rappels) {
    if (glissement) return false;
    const elements = [
      ...fixes.map(tuile => creerTuile({ ...tuile, classe: 'tuile-fixe' }, rappels)),
      ...categories.map(tuile => creerTuile({ ...tuile, id: `categorie:${tuile.categorie}`, classe: 'tuile-categorie',
        micro: true }, rappels)),
      ...finales.map(tuile => creerTuile({ ...tuile, classe: 'tuile-outil' }, rappels))
    ];
    conteneur.replaceChildren(...elements);
    return true;
  }

  function deplacementEnCours() { return Boolean(glissement?.actif); }

  return { afficher, deplacementEnCours };
})();
