'use strict';

// Compte les échanges avec une IA payante, jour par jour, sur le téléphone seulement.
// Les réponses préparées (sans clé) sont gratuites et ne sont pas comptées.
const limiteIA = (() => {
  const cle = 'cap_echanges_ia_v1';
  const MAXIMUM = 60;
  const ALERTE = 50;

  function lire() {
    try {
      const valeur = JSON.parse(localStorage.getItem(cle));
      if (valeur && valeur.jour === dateDuJour() && Number.isSafeInteger(valeur.nombre) && valeur.nombre >= 0) return valeur.nombre;
    } catch (erreur) {
    }
    return 0;
  }

  function utilises() {
    return lire();
  }

  function peutEchanger() {
    return lire() < MAXIMUM;
  }

  function compter() {
    const nombre = Math.min(lire() + 1, MAXIMUM);
    try {
      localStorage.setItem(cle, JSON.stringify({ jour: dateDuJour(), nombre }));
    } catch (erreur) {
    }
    let alerte = '';
    if (nombre >= MAXIMUM) alerte = `Limite atteinte : ${MAXIMUM} échanges avec l’IA aujourd’hui. Je reprends demain.`;
    else if (nombre >= ALERTE) alerte = `Attention : ${nombre} échanges avec l’IA aujourd’hui sur ${MAXIMUM}.`;
    return { nombre, restants: MAXIMUM - nombre, alerte };
  }

  return { MAXIMUM, ALERTE, utilises, peutEchanger, compter };
})();
