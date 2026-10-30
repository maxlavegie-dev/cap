'use strict';

// Compte les échanges avec une IA payante, jour par jour, et la dépense du mois, sur le téléphone seulement.
// La limite par jour est un réglage que Max change lui-même dans Cap. Les réponses préparées sont gratuites et ne comptent pas.
const limiteIA = (() => {
  const cle = 'cap_echanges_ia_v1';
  const cleReglage = 'cap_reglages_ia_v1';
  const cleDepense = 'cap_depense_ia_v1';

  function lireJson(nom) {
    try {
      return JSON.parse(localStorage.getItem(nom));
    } catch (erreur) {
      return null;
    }
  }

  function ecrireJson(nom, valeur) {
    try {
      localStorage.setItem(nom, JSON.stringify(valeur));
      return true;
    } catch (erreur) {
      return false;
    }
  }

  function moisDuJour() {
    return dateDuJour().slice(0, 7);
  }

  function maximum() {
    const valeur = lireJson(cleReglage)?.limite;
    return Number.isSafeInteger(valeur) && valeur >= 1 && valeur <= REGLAGES_IA.limite_maximum ? valeur : REGLAGES_IA.limite_par_defaut;
  }

  function definirMaximum(valeur) {
    const nombre = Number(valeur);
    if (!Number.isSafeInteger(nombre) || nombre < 1 || nombre > REGLAGES_IA.limite_maximum) {
      throw new Error(`Choisis un nombre entier entre 1 et ${REGLAGES_IA.limite_maximum}.`);
    }
    if (!ecrireJson(cleReglage, { ...(lireJson(cleReglage) || {}), limite: nombre })) {
      throw new Error('Le réglage n’a pas pu être enregistré sur ce téléphone.');
    }
    return nombre;
  }

  // On prévient Max à partir des 5/6 de la limite (50 sur 60).
  function seuilAlerte() {
    return Math.max(1, Math.floor(maximum() * 5 / 6));
  }

  function utilises() {
    const valeur = lireJson(cle);
    return valeur && valeur.jour === dateDuJour() && Number.isSafeInteger(valeur.nombre) && valeur.nombre >= 0 ? valeur.nombre : 0;
  }

  function peutEchanger() {
    return utilises() < maximum();
  }

  function compter() {
    const limite = maximum();
    const nombre = Math.min(utilises() + 1, limite);
    ecrireJson(cle, { jour: dateDuJour(), nombre });
    let alerte = '';
    if (nombre >= limite) alerte = `C’était mon dernier échange avec l’IA aujourd’hui (${limite} sur ${limite}).`;
    else if (nombre >= seuilAlerte()) alerte = `Attention : ${nombre} échanges avec l’IA aujourd’hui sur ${limite}.`;
    return { nombre, restants: limite - nombre, alerte };
  }

  function depenseDuMois() {
    const valeur = lireJson(cleDepense);
    return valeur && valeur.mois === moisDuJour() && Number.isFinite(valeur.euros) && valeur.euros >= 0 ? valeur.euros : 0;
  }

  // Coût calculé à partir des jetons comptés par l'IA elle-même.
  function ajouterDepense(jetonsEntree, jetonsSortie) {
    const entree = Number.isFinite(jetonsEntree) && jetonsEntree > 0 ? jetonsEntree : 0;
    const sortie = Number.isFinite(jetonsSortie) && jetonsSortie > 0 ? jetonsSortie : 0;
    const dollars = (entree * REGLAGES_IA.dollars_par_million_entree + sortie * REGLAGES_IA.dollars_par_million_sortie) / 1e6;
    const euros = depenseDuMois() + dollars * REGLAGES_IA.euros_par_dollar;
    ecrireJson(cleDepense, { mois: moisDuJour(), euros });
    return euros;
  }

  return { maximum, definirMaximum, seuilAlerte, utilises, peutEchanger, compter, depenseDuMois, ajouterDepense };
})();
