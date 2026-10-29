'use strict';

const fermetureFenetres = (() => {
  const brouillons = new Map();
  const reglages = new WeakMap();
  const selecteurTexte = 'input:not([type]), input[type="text"], input[type="search"], input[type="tel"], input[type="email"], input[type="url"], textarea';
  let bandeau = null;
  let delaiBandeau;

  function noeud(balise, classe, texte) {
    const element = document.createElement(balise);
    if (classe) element.className = classe;
    if (texte !== undefined) element.textContent = texte;
    return element;
  }

  function bouton(texte, classe, action) {
    const element = noeud('button', classe, texte);
    element.type = 'button';
    element.addEventListener('click', action);
    return element;
  }

  function aDuTexte(dialogue) {
    return dialogue.dataset.modifie === '1'
      && Array.from(dialogue.querySelectorAll(selecteurTexte)).some(champ => !champ.disabled && champ.value.trim());
  }

  function photographier(dialogue) {
    const valeurs = {};
    dialogue.querySelectorAll('input[id], textarea[id], select[id]').forEach(champ => {
      if (champ.type === 'checkbox' || champ.type === 'radio') valeurs[champ.id] = { coche: champ.checked };
      else if (champ.type !== 'button' && champ.type !== 'submit') valeurs[champ.id] = { valeur: champ.value };
    });
    return valeurs;
  }

  function propre(dialogue) {
    delete dialogue.dataset.modifie;
    fermerQuestion(dialogue);
  }

  function restaurer(dialogue) {
    const options = reglages.get(dialogue);
    if (!options) return false;
    const cle = options.cle();
    const valeurs = brouillons.get(cle);
    if (!valeurs) return false;
    brouillons.delete(cle);
    const selects = [];
    for (const [id, etat] of Object.entries(valeurs)) {
      const champ = dialogue.querySelector(`#${CSS.escape(id)}`);
      if (!champ) continue;
      if ('coche' in etat) champ.checked = etat.coche;
      else if (champ.tagName === 'SELECT') {
        if (Array.from(champ.options).some(option => option.value === etat.valeur)) {
          champ.value = etat.valeur;
          selects.push(champ);
        }
      } else champ.value = etat.valeur;
    }
    selects.forEach(champ => champ.dispatchEvent(new Event('change', { bubbles: true })));
    dialogue.dataset.modifie = '1';
    return true;
  }

  function cacherBandeau() {
    clearTimeout(delaiBandeau);
    if (bandeau) bandeau.remove();
    bandeau = null;
  }

  function proposerAnnulation(texte, annuler) {
    cacherBandeau();
    bandeau = noeud('div', 'annulation-fenetre');
    bandeau.setAttribute('role', 'status');
    bandeau.append(noeud('span', '', texte), bouton('Annuler', 'bouton-annuler-fenetre', () => {
      cacherBandeau();
      annuler();
    }));
    const ouvertes = document.querySelectorAll('dialog[open]');
    (ouvertes[ouvertes.length - 1] || document.body).append(bandeau);
    delaiBandeau = setTimeout(cacherBandeau, 8000);
  }

  function fermerQuestion(dialogue) {
    dialogue.querySelector(':scope > .question-fermeture')?.remove();
  }

  function poserQuestion(dialogue) {
    const options = reglages.get(dialogue);
    fermerQuestion(dialogue);
    const zone = noeud('div', 'question-fermeture');
    zone.setAttribute('role', 'alertdialog');
    zone.setAttribute('aria-label', 'Tu as commencé à écrire');
    const continuer = bouton('Continuer', 'bouton-continuer', () => {
      fermerQuestion(dialogue);
      dialogue.querySelector(selecteurTexte)?.focus({ preventScroll: true });
    });
    zone.append(
      noeud('p', '', 'Tu as commencé à écrire. Que veux-tu faire ?'),
      noeud('div', 'actions-question', undefined)
    );
    zone.lastChild.append(
      bouton('Garder', 'bouton-garder', () => {
        brouillons.set(options.cle(), photographier(dialogue));
        propre(dialogue);
        options.retour();
      }),
      bouton('Jeter', 'bouton-jeter', () => {
        const cle = options.cle();
        const valeurs = photographier(dialogue);
        const relancer = options.rouvrir?.();
        propre(dialogue);
        options.retour();
        proposerAnnulation('Texte jeté.', () => {
          brouillons.set(cle, valeurs);
          relancer?.();
        });
      }),
      continuer
    );
    dialogue.append(zone);
    continuer.focus({ preventScroll: true });
  }

  function toucheACote(dialogue) {
    const options = reglages.get(dialogue);
    if (!options || !dialogue.open) return;
    if (dialogue.querySelector(':scope > .question-fermeture')) return;
    if (options.bloque?.()) return;
    if (aDuTexte(dialogue)) poserQuestion(dialogue);
    else {
      propre(dialogue);
      options.retour();
    }
  }

  function installer(dialogue, options = {}) {
    reglages.set(dialogue, {
      retour: options.retour || (() => dialogue.close()),
      cle: options.cle || (() => dialogue.id),
      rouvrir: options.rouvrir,
      bloque: options.bloque
    });
    dialogue.addEventListener('input', event => {
      if (event.target.matches?.(selecteurTexte)) dialogue.dataset.modifie = '1';
    });
    dialogue.addEventListener('click', event => {
      if (event.target !== dialogue) return;
      const cadre = dialogue.getBoundingClientRect();
      const dedans = event.clientX >= cadre.left && event.clientX <= cadre.right
        && event.clientY >= cadre.top && event.clientY <= cadre.bottom;
      if (!dedans) toucheACote(dialogue);
    });
    dialogue.addEventListener('close', () => {
      if (!dialogue.open) propre(dialogue);
    });
  }

  function aUnBrouillon(cle) { return brouillons.has(cle); }

  return { installer, restaurer, propre, toucheACote, aUnBrouillon };
})();
