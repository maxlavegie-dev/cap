'use strict';

// 09/11/2026 (accord de Max) : la liste des PHRASES À APPRENDRE. UNE SEULE liste, sur le téléphone seulement
// (localStorage) : la phrase dite par Max, la commande qu'il a choisie (ou aucune), la date et d'où elle vient
// (« bouton » : le bouton rond ; « hésitation » : la fenêtre de gros choix quand Cap hésitait).
// Cap n'écrit RIEN dans le tableur « Commandes vocales » et n'envoie rien : Max copie la liste (« Copier tout ») et la
// colle lui-même. Rien de tout cela ne va à l'IA. Rien n'est effacé sans que Max touche « Retirer ».
const phrasesApprendre = (() => {
  const CLE = 'cap_phrases_a_apprendre_v1';
  const MAX = 200;
  const ORIGINES = { bouton: 'bouton', hesitation: 'hésitation' };

  // Même pliage que le moteur des commandes : minuscules, sans accents, sans ponctuation.
  function plier(texte) {
    return String(texte || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/œ/g, 'oe')
      .replace(/[^a-z0-9]+/g, ' ').trim();
  }

  function idStable(e) {
    let h = 0;
    for (const c of `${e.quand}|${e.phrase}`) h = (h * 31 + c.charCodeAt(0)) >>> 0;
    return `P-${h.toString(36)}`;
  }
  function nouvelId(maintenant) { return `P-${Number(maintenant).toString(36)}-${Math.floor(Math.random() * 46656).toString(36)}`; }

  function lire(stockage) {
    try {
      const liste = JSON.parse(stockage.getItem(CLE));
      // 09/11/2026 (petit tableur) : chaque phrase a un IDENTIFIANT (pour retrouver sa ligne dans « Phrases apprises »).
      // Les phrases d'avant n'en avaient pas : on leur en donne un, toujours le même (calculé sur la date et la phrase).
      return Array.isArray(liste) ? liste.filter(e => e && typeof e.phrase === 'string').map(e => (e.id ? e : { ...e, id: idStable(e) })) : [];
    } catch (erreur) { return []; }
  }
  function ecrire(stockage, liste) {
    try { stockage.setItem(CLE, JSON.stringify(liste.slice(0, MAX))); return true; } catch (erreur) { return false; }
  }

  // entree : { phrase, code ('' = aucune ne convient), commande, origine ('bouton' | 'hesitation'), quand? }.
  // Rend { statut: 'ajoutee' | 'deja' | 'conflit' | 'vide' | 'pleine', existante?, nombre }.
  // Doublon : même phrase (pliée) et même commande = « deja », rien n'est ajouté ; même phrase, AUTRE commande =
  // « conflit » : rien n'est changé, c'est à Max de dire laquelle garder (garderNouvelle).
  function ajouter(stockage, entree, maintenant = Date.now()) {
    const phrase = String(entree && entree.phrase || '').trim();
    const liste = lire(stockage);
    if (!plier(phrase)) return { statut: 'vide', nombre: liste.length };
    const existante = liste.find(e => plier(e.phrase) === plier(phrase));
    const code = String(entree.code || '');
    if (existante) return { statut: (existante.code || '') === code ? 'deja' : 'conflit', existante, nombre: liste.length };
    if (liste.length >= MAX) return { statut: 'pleine', nombre: liste.length };
    const nouvelle = { id: nouvelId(maintenant), phrase, code, commande: String(entree.commande || (code ? code : 'Aucune ne convient')),
      origine: ORIGINES[entree.origine] || 'bouton', quand: new Date(entree.quand || maintenant).toISOString() };
    if (entree.choisie) nouvelle.choisie = true; // 09/11/2026 (séance 2) : choix fait par Max dans la fenêtre de choix
    liste.unshift(nouvelle);
    if (!ecrire(stockage, liste)) return { statut: 'pleine', nombre: liste.length - 1 };
    return { statut: 'ajoutee', nombre: liste.length, entree: nouvelle }; // 09/11/2026 : + entree (pour le petit tableur)
  }

  // Conflit tranché par Max : la nouvelle commande remplace l'ancienne pour cette phrase (date et origine nouvelles).
  // 09/11/2026 : + « remplacees » (les anciennes, pour écrire « remplacée le … » dans le petit tableur, sans rien effacer).
  function garderNouvelle(stockage, entree, maintenant = Date.now()) {
    const toutes = lire(stockage);
    const remplacees = toutes.filter(e => plier(e.phrase) === plier(entree.phrase));
    ecrire(stockage, toutes.filter(e => plier(e.phrase) !== plier(entree.phrase)));
    return { ...ajouter(stockage, entree, maintenant), remplacees };
  }

  // « Retirer » (une ligne, par son rang dans la liste montrée). Elle quitte la liste du téléphone ; dans le petit
  // tableur, sa ligne est seulement MARQUÉE « retirée » (09/11/2026, décision de Max : rien n'y est effacé).
  // 09/11/2026 : + retirerEntree (rend la phrase retirée, pour le petit tableur). retirer() rend toujours le nombre.
  function retirerEntree(stockage, rang) {
    const liste = lire(stockage);
    if (rang < 0 || rang >= liste.length) return null;
    const [partie] = liste.splice(rang, 1);
    ecrire(stockage, liste);
    return partie;
  }
  function retirer(stockage, rang) {
    retirerEntree(stockage, rang);
    return lire(stockage).length;
  }

  // « Copier tout » : une ligne par phrase, colonnes séparées par des tabulations, dans l'ordre du tableur
  // « Commandes vocales » (Ce que je veux, Commande, Bloc, Formulation, Code, Remarque). Bloc « Expression seule (Cap) » :
  // la phrase entière seulement. Max colle lui-même ; Cap n'écrit rien dans le tableur.
  function texteACopier(liste) {
    const date = q => { const d = new Date(q); return Number.isNaN(d.getTime()) ? '' : d.toLocaleDateString('fr-FR'); };
    return liste.map(e => [e.code ? e.commande : 'À traiter à la main', '', 'Expression seule (Cap)', e.phrase.replace(/[\t\n]+/g, ' '),
      e.code || '', `Ajoutée par Cap le ${date(e.quand)} (${e.origine})`].join('\t')).join('\n');
  }

  // 09/11/2026 (séance 2) : marque « choisie par Max » une phrase déjà dans la liste (même commande que son choix).
  function marquerChoisie(stockage, id) {
    const liste = lire(stockage);
    const e = liste.find(x => x.id === id);
    if (!e) return false;
    e.choisie = true;
    return ecrire(stockage, liste);
  }

  return { CLE, MAX, plier, lire, ajouter, garderNouvelle, retirer, retirerEntree, texteACopier, marquerChoisie }; // 09/11/2026 : + retirerEntree, marquerChoisie
})();
