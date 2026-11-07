'use strict';

// Rond d'attente (07/11/2026, demandé par Max) : pendant une lecture lente (comptage du Drive,
// ouverture d'un PDF), le bouton montre un petit rond qui tourne et « Lecture en cours… ».
// Le bouton est grisé pendant le travail (pas de second appui), puis reprend son texte.
const attenteLecture = (() => {
  async function pendant(bouton, travail) {
    if (!bouton) return travail();
    const texte = bouton.textContent;
    bouton.disabled = true;
    bouton.classList.add('en-lecture');
    bouton.setAttribute('aria-busy', 'true');
    bouton.textContent = 'Lecture en cours…';
    try {
      return await travail();
    } finally {
      bouton.textContent = texte;
      bouton.classList.remove('en-lecture');
      bouton.removeAttribute('aria-busy');
      bouton.disabled = false;
    }
  }
  return { pendant };
})();
