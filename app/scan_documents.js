'use strict';

// Règles du scanner, sans DOM : pages d'un document, ordre, verso vide, nom du fichier, mode rafale.
const scanDocuments = (() => {
  const inactivite_rafale_ms = 5 * 60 * 1000;

  function deuxChiffres(n) { return String(n).padStart(2, '0'); }

  // Nom provisoire du fichier déposé dans 00_A_CLASSER : sans accent, trié par date. Le vrai nommage viendra au lot 3.3.
  function nomFichier(date, dejaPris = []) {
    const base = `SCAN-${date.getFullYear()}-${deuxChiffres(date.getMonth() + 1)}-${deuxChiffres(date.getDate())}`
      + `-${deuxChiffres(date.getHours())}h${deuxChiffres(date.getMinutes())}m${deuxChiffres(date.getSeconds())}`;
    const pris = new Set(dejaPris.map(nom => nom.toLowerCase()));
    let nom = `${base}.pdf`;
    for (let n = 2; pris.has(nom.toLowerCase()); n++) nom = `${base}-${n}.pdf`;
    return nom;
  }

  // horsLigne : '' (réseau et Google prêts), 'reseau' (pas de réseau) ou 'google' (pas connecté à Google).
  function messageEnregistre(nombrePages, horsLigne = '') {
    const pages = nombrePages === 1 ? '1 page enregistrée' : `${nombrePages} pages enregistrées`;
    if (horsLigne === 'reseau') return `${pages}. Pas de réseau : le scan est gardé sur le téléphone et partira tout seul au retour du réseau.`;
    if (horsLigne === 'google') return `${pages}. Cap n’est pas connecté à Google : le scan est gardé sur le téléphone et partira après la connexion.`;
    return `${pages}, en cours de classement.`;
  }

  // Phrase de l'indicateur « scans en attente » : jamais vide si quelque chose attend d'être envoyé.
  function messageEnAttente(nombre, horsLigne = '') {
    if (!nombre) return '';
    const un = nombre === 1;
    const tete = `${un ? '1 scan en attente' : `${nombre} scans en attente`} d’envoi : ${un ? 'gardé' : 'gardés'} sur le téléphone, `;
    if (horsLigne === 'reseau') return `${tete}${un ? 'il partira' : 'ils partiront'} au retour du réseau.`;
    if (horsLigne === 'google') return `${tete}${un ? 'il partira' : 'ils partiront'} après la connexion à Google.`;
    return `${tete}envoi en cours.`;
  }

  function creerSession() {
    let pages = [];
    let prochain = 1;
    let ignorees = 0;

    // Ajoute une page. Une page blanche n'est ignorée que s'il y a déjà une page (verso vide) : au moindre doute, on garde.
    function ajouter(page) {
      if (!page || !(page.jpeg instanceof Uint8Array)) throw new Error('Page invalide.');
      if (page.vide && pages.length > 0) {
        ignorees++;
        return { ajoutee: false, raison: 'vide', id: null };
      }
      const entree = { alertes: [], ...page, id: prochain++ };
      pages.push(entree);
      return { ajoutee: true, raison: '', id: entree.id };
    }

    function index(id) {
      const i = pages.findIndex(p => p.id === id);
      if (i < 0) throw new Error('Cette page n’existe plus.');
      return i;
    }

    function remplacer(id, page) {
      const i = index(id);
      pages[i] = { alertes: [], ...page, id };
    }

    function supprimer(id) {
      pages.splice(index(id), 1);
    }

    function deplacer(id, decalage) {
      const i = index(id);
      const j = Math.max(0, Math.min(pages.length - 1, i + decalage));
      if (i === j) return false;
      const [page] = pages.splice(i, 1);
      pages.splice(j, 0, page);
      return true;
    }

    function vider() {
      pages = [];
      ignorees = 0;
    }

    return {
      ajouter, remplacer, supprimer, deplacer, vider,
      pages: () => pages.slice(),
      nombre: () => pages.length,
      ignorees: () => ignorees,
      ordre: () => pages.map(p => p.id)
    };
  }

  // Mode rafale : plusieurs documents à la suite, chacun son fichier ; compte rendu à la fin.
  function creerRafale(delai = inactivite_rafale_ms) {
    let active = false;
    let derniere = 0;
    const compte = { scannes: 0, deposes: 0, enAttente: 0 };

    function demarrer(maintenant = Date.now()) {
      active = true; derniere = maintenant;
      compte.scannes = 0; compte.deposes = 0; compte.enAttente = 0;
    }
    function arreter() { active = false; }
    function toucher(maintenant = Date.now()) { if (active) derniere = maintenant; }
    function expiree(maintenant = Date.now()) { return active && maintenant - derniere >= delai; }
    function noter(scanne, depose) {
      compte.scannes += scanne ? 1 : 0;
      compte.deposes += depose ? 1 : 0;
      compte.enAttente = compte.scannes - compte.deposes;
    }
    function compteRendu() {
      const mot = n => (n > 1 ? 'scannés' : 'scanné');
      return `${compte.scannes} ${mot(compte.scannes)}, ${compte.deposes} déposé${compte.deposes > 1 ? 's' : ''}, ${compte.enAttente} en attente.`;
    }
    return { demarrer, arreter, toucher, expiree, noter, compteRendu, active: () => active, compte: () => ({ ...compte }) };
  }

  return { nomFichier, messageEnregistre, messageEnAttente, creerSession, creerRafale, inactivite_rafale_ms };
})();
