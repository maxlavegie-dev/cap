'use strict';

const recherche = (() => {
  function normaliser(texte) {
    return String(texte ?? '').normalize('NFD').replace(/\p{M}/gu, '').toLocaleLowerCase('fr-FR');
  }

  function chercher(liste, requete, champs, accepter = () => true) {
    const texte = normaliser(requete).trim();
    if (!texte || !Array.isArray(liste)) return [];
    return liste.filter(item => item && accepter(item)
      && champs.some(champ => normaliser(item[champ]).includes(texte)));
  }

  function chercherTaches(liste, requete) {
    return chercher(liste, requete, ['intitule', 'categorie', 'sous_categorie', 'note'],
      tache => !tache.abandonnee_le);
  }

  function chercherRendezVous(liste, requete) {
    return chercher(liste, requete, ['titre', 'lieu', 'description']);
  }

  return { normaliser, chercherTaches, chercherRendezVous };
})();
