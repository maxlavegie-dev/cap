'use strict';

const listesChoix = (() => {
  const cle = 'cap_listes_v1';
  const cleEnvoi = 'cap_listes_a_envoyer_v1';
  const A_TRIER = 'À trier';
  const depart = [A_TRIER, 'Musique', 'Écriture', 'Quotidien'];
  const palette = ['#2f6f9f', '#a3542b', '#3d7d4a', '#7a4f9a', '#b0811f', '#a33b5c', '#2b7f7a', '#5b6b2e', '#8a5a3c', '#4a5fa8'];
  const gris = '#6f6f6f';
  const texte = valeur => (typeof valeur === 'string' ? valeur : '');
  const cleNom = nom => texte(nom).trim().toLocaleLowerCase('fr');
  const cleCategorie = (nom, parente) => `${cleNom(parente)}\u0000${cleNom(nom)}`;
  let donnees = { modeles: [], categories: [] };

  function nettoyerNom(valeur) {
    const nom = texte(valeur).replace(/\s+/g, ' ').trim().slice(0, 60).trim();
    if (!nom) throw new Error('Indique un nom pour continuer.');
    return nom;
  }

  function nettoyerEtapes(liste) {
    const etapes = (Array.isArray(liste) ? liste : []).map(etape => texte(etape).replace(/\s+/g, ' ').trim().slice(0, 120))
      .filter(Boolean);
    if (!etapes.length) throw new Error('Indique au moins une étape, une par ligne.');
    if (etapes.length > 20) throw new Error('Vingt étapes au maximum.');
    return etapes;
  }

  function modeleValide(modele) {
    return modele && texte(modele.nom).trim() && Array.isArray(modele.etapes)
      && modele.etapes.every(etape => typeof etape === 'string');
  }

  function categorieValide(categorie) {
    return categorie && texte(categorie.nom).trim();
  }

  function lireMemoire() {
    try {
      const brut = JSON.parse(localStorage.getItem(cle));
      if (!brut || typeof brut !== 'object') return { modeles: [], categories: [] };
      return {
        modeles: (Array.isArray(brut.modeles) ? brut.modeles : []).filter(modeleValide).map(modele => ({
          nom: modele.nom.trim(), etapes: [...modele.etapes], retiree_le: texte(modele.retiree_le), modifie_le: texte(modele.modifie_le)
        })),
        categories: (Array.isArray(brut.categories) ? brut.categories : []).filter(categorieValide).map(categorie => ({
          nom: categorie.nom.trim(), parente: texte(categorie.parente).trim(), couleur: texte(categorie.couleur),
          retiree_le: texte(categorie.retiree_le), modifie_le: texte(categorie.modifie_le), ordre: texte(categorie.ordre)
        }))
      };
    } catch (erreur) {
      return { modeles: [], categories: [] };
    }
  }

  function couleurLibre() {
    const utilisees = donnees.categories.filter(categorie => !categorie.parente).map(categorie => categorie.couleur);
    let choix = palette[0];
    let minimum = Infinity;
    for (const couleur of palette) {
      const nombre = utilisees.filter(item => item === couleur).length;
      if (nombre < minimum) { minimum = nombre; choix = couleur; }
    }
    return choix;
  }

  function trouverCategorie(nom, parente = '') {
    const recherche = cleCategorie(nom, parente);
    return donnees.categories.find(categorie => cleCategorie(categorie.nom, categorie.parente) === recherche);
  }

  function trouverModele(nom) {
    return donnees.modeles.find(modele => cleNom(modele.nom) === cleNom(nom));
  }

  function completer() {
    for (const [nom, etapes] of Object.entries(ETAPES_PAR_DEFAUT)) {
      if (!trouverModele(nom) && Array.isArray(etapes)) {
        donnees.modeles.push({ nom, etapes: [...etapes], retiree_le: '', modifie_le: '' });
      }
    }
    for (const modele of donnees.modeles) ETAPES_PAR_DEFAUT[modele.nom] = [...modele.etapes];
    const noms = [...depart, ...TACHES.map(tache => texte(tache.categorie).trim())].filter(Boolean);
    for (const nom of noms) {
      if (!trouverCategorie(nom)) donnees.categories.push({ nom, parente: '', couleur: '', retiree_le: '', modifie_le: '' });
    }
    for (const tache of TACHES) {
      const parente = texte(tache.categorie).trim();
      const nom = texte(tache.sous_categorie).trim();
      if (parente && nom && !trouverCategorie(nom, parente)) {
        donnees.categories.push({ nom, parente, couleur: '', retiree_le: '', modifie_le: '' });
      }
    }
    for (const categorie of donnees.categories) {
      if (categorie.parente || /^#[0-9a-f]{6}$/i.test(categorie.couleur)) continue;
      categorie.couleur = cleNom(categorie.nom) === cleNom(A_TRIER) ? gris : couleurLibre();
    }
  }

  function enregistrer(aEnvoyer = true) {
    localStorage.setItem(cle, JSON.stringify(donnees));
    if (aEnvoyer) localStorage.setItem(cleEnvoi, '1');
    window.dispatchEvent(new Event('cap-listes-changees'));
  }

  function maintenant() { return new Date().toISOString(); }

  function usage(categorie) {
    return TACHES.filter(tache => !tache.abandonnee_le && (categorie.parente
      ? cleNom(tache.categorie) === cleNom(categorie.parente) && cleNom(tache.sous_categorie) === cleNom(categorie.nom)
      : cleNom(tache.categorie) === cleNom(categorie.nom))).length;
  }

  function rang(categorie) {
    const valeur = Number.parseInt(categorie.ordre, 10);
    return Number.isFinite(valeur) && valeur > 0 ? valeur : Infinity;
  }

  function categories(parente = '') {
    return donnees.categories
      .map((categorie, ordre) => ({ categorie, ordre, rang: rang(categorie), usage: usage(categorie) }))
      .filter(({ categorie }) => !categorie.retiree_le && cleNom(categorie.parente) === cleNom(parente))
      .sort((a, b) => Number(cleNom(b.categorie.nom) === cleNom(A_TRIER)) - Number(cleNom(a.categorie.nom) === cleNom(A_TRIER))
        || (a.rang === b.rang ? 0 : a.rang < b.rang ? -1 : 1) || b.usage - a.usage || a.ordre - b.ordre)
      .map(({ categorie }) => categorie.nom);
  }

  function ordonner(noms, parente = '') {
    const cibles = noms.map(nom => trouverCategorie(nom, parente))
      .filter(categorie => categorie && !categorie.retiree_le && cleNom(categorie.nom) !== cleNom(A_TRIER));
    let change = false;
    cibles.forEach((categorie, indice) => {
      const valeur = String(indice + 1);
      if (categorie.ordre === valeur) return;
      categorie.ordre = valeur;
      categorie.modifie_le = maintenant();
      change = true;
    });
    if (change) enregistrer();
    return change;
  }

  function categoriesRetirees(parente = '') {
    return donnees.categories.filter(categorie => categorie.retiree_le && cleNom(categorie.parente) === cleNom(parente))
      .map(categorie => ({ nom: categorie.nom, retiree_le: categorie.retiree_le }));
  }

  function couleur(nom) {
    const categorie = trouverCategorie(nom);
    return categorie?.couleur || gris;
  }

  function modeles() {
    return donnees.modeles.filter(modele => !modele.retiree_le).map(modele => modele.nom);
  }

  function modelesRetires() {
    return donnees.modeles.filter(modele => modele.retiree_le).map(modele => ({ nom: modele.nom, retiree_le: modele.retiree_le }));
  }

  function etapes(nom) {
    const modele = trouverModele(nom);
    return modele ? [...modele.etapes] : [];
  }

  function ajouterCategorie(valeur, parente = '') {
    const nom = nettoyerNom(valeur);
    if (parente && (!trouverCategorie(parente) || trouverCategorie(parente).retiree_le)) {
      throw new Error('Cette catégorie est introuvable.');
    }
    const existante = trouverCategorie(nom, parente);
    if (existante && !existante.retiree_le) return existante.nom;
    if (existante) {
      existante.retiree_le = '';
      existante.modifie_le = maintenant();
    } else {
      donnees.categories.push({ nom, parente: parente ? trouverCategorie(parente).nom : '', couleur: parente ? '' : couleurLibre(),
        retiree_le: '', modifie_le: maintenant(), ordre: '' });
    }
    enregistrer();
    return existante ? existante.nom : nom;
  }

  function ajouterModele(valeur, liste) {
    const nom = nettoyerNom(valeur);
    const etapesPropres = nettoyerEtapes(liste);
    const existant = trouverModele(nom);
    if (existant && !existant.retiree_le) throw new Error('Ce modèle existe déjà.');
    if (existant) {
      existant.retiree_le = '';
      existant.etapes = etapesPropres;
      existant.modifie_le = maintenant();
    } else {
      donnees.modeles.push({ nom, etapes: etapesPropres, retiree_le: '', modifie_le: maintenant() });
    }
    ETAPES_PAR_DEFAUT[existant ? existant.nom : nom] = [...etapesPropres];
    enregistrer();
    return existant ? existant.nom : nom;
  }

  function elements(type, noms, parente) {
    return noms.map(nom => (type === 'modele' ? trouverModele(nom) : trouverCategorie(nom, parente))).filter(Boolean);
  }

  function changerRetrait(type, noms, parente, retrait) {
    const cibles = elements(type, noms, parente).filter(item => Boolean(item.retiree_le) !== retrait);
    if (!cibles.length) return [];
    const date = retrait ? dateDuJour() : '';
    for (const cible of cibles) {
      cible.retiree_le = date;
      cible.modifie_le = maintenant();
    }
    enregistrer();
    return cibles.map(cible => cible.nom);
  }

  function retirer(type, noms, parente = '') { return changerRetrait(type, noms, parente, true); }
  function remettre(type, noms, parente = '') { return changerRetrait(type, noms, parente, false); }

  function fusionner(distant) {
    for (const modele of (distant?.modeles || []).filter(modeleValide)) {
      const local = trouverModele(modele.nom);
      const copie = { nom: modele.nom.trim(), etapes: [...modele.etapes], retiree_le: texte(modele.retiree_le), modifie_le: texte(modele.modifie_le) };
      if (!local) donnees.modeles.push(copie);
      else if (copie.modifie_le > local.modifie_le) Object.assign(local, copie, { nom: local.nom });
    }
    for (const categorie of (distant?.categories || []).filter(categorieValide)) {
      const local = trouverCategorie(categorie.nom, categorie.parente);
      const copie = { nom: categorie.nom.trim(), parente: texte(categorie.parente).trim(), couleur: texte(categorie.couleur),
        retiree_le: texte(categorie.retiree_le), modifie_le: texte(categorie.modifie_le), ordre: texte(categorie.ordre) };
      if (!local) donnees.categories.push(copie);
      else {
        if (copie.modifie_le > local.modifie_le) {
          local.retiree_le = copie.retiree_le;
          local.modifie_le = copie.modifie_le;
          local.ordre = copie.ordre;
        }
        if (/^#[0-9a-f]{6}$/i.test(copie.couleur) && !copie.parente) local.couleur = copie.couleur;
      }
    }
    completer();
    enregistrer(false);
  }

  function exporter() {
    return JSON.parse(JSON.stringify(donnees));
  }

  function aEnvoyer() {
    try { return localStorage.getItem(cleEnvoi) === '1'; } catch (erreur) { return false; }
  }

  function marquerEnvoye() {
    try { localStorage.removeItem(cleEnvoi); } catch (erreur) {}
  }

  function recharger() {
    donnees = lireMemoire();
    completer();
    try { localStorage.setItem(cle, JSON.stringify(donnees)); } catch (erreur) {}
  }

  recharger();
  return { A_TRIER, categories, categoriesRetirees, couleur, modeles, modelesRetires, etapes, ajouterCategorie, ajouterModele,
    retirer, remettre, fusionner, exporter, aEnvoyer, marquerEnvoye, recharger, ordonner };
})();
