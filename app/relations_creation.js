'use strict';

// Dossiers « Relations », ÉTAPE 3 (06/11/2026) : création des dossiers, testée UNIQUEMENT sur un faux
// Drive et un faux Dictionnaire (FICTIF). À cette étape, rien dans Cap n'appelle ce module avec le
// vrai Drive : aucun bouton ne le lance (étapes 4 et 5, chacune après le Oui de Max).
// Ce qui sera créé, dans « App Cap » : « Relations » › « r_Prénom Nom » › « Journal de bord » (Google
// Doc vide), « Reçus », « Envoyés ».
// Verrous :
//  - jamais de doublon : chaque élément porte une étiquette invisible (appProperties), cherchée dans
//    le Drive JUSTE AVANT sa création ; une coupure au milieu se reprend sans rien refaire ;
//  - une création à la fois, une personne après l'autre ; un second appui pendant le travail ne crée
//    rien (et après, tout est déjà là : rien n'est recréé) ;
//  - homonymes, fiches incomplètes, fiches sans type, changements de nom : rien n'est créé pour elles,
//    Cap s'arrête et montre les choix ; un changement de nom est seulement PROPOSÉ (« Renommer ? ») ;
//  - Cap ne supprime, ne renomme et ne déplace JAMAIS rien (seulement des lectures et des créations) ;
//  - une ligne dans le Journal Général par élément créé ;
//  - droits actuels seulement (drive.file) : Cap ne voit pas les dossiers faits à la main, d'où la
//    question de l'écran de vérification.
const relationsCreation = (() => {
  const drive = 'https://www.googleapis.com/drive/v3/files';
  const DOSSIER = 'application/vnd.google-apps.folder';
  const DOC = 'application/vnd.google-apps.document';
  const NOM_RACINE = 'Relations';
  const PARTIES = Object.freeze([
    Object.freeze({ cle: 'journal', nom: 'Journal de bord', type: DOC }),
    Object.freeze({ cle: 'recus', nom: 'Reçus', type: DOSSIER }),
    Object.freeze({ cle: 'envoyes', nom: 'Envoyés', type: DOSSIER })
  ]);
  const ETIQUETTES = Object.freeze({ racine: 'cap_relations', personne: 'cap_relation', ligne: 'cap_relation_ligne', partie: 'cap_relation_partie' });
  const QUESTION = 'As-tu déjà créé toi-même un dossier r_ pour l’une de ces personnes ?';
  let enCours = null;

  function echapper(texte) { return String(texte).replace(/\\/g, '\\\\').replace(/'/g, "\\'"); }
  async function lireJson(url, options) { return (await googleConnexion.appeler(url, options)).json(); }

  // Tous les fichiers (non jetés) qui répondent à la recherche, page après page. Lecture seulement.
  async function lister(q) {
    const fichiers = [];
    let page = '';
    for (let tour = 0; tour < 50; tour++) {
      const parametres = new URLSearchParams({ q, fields: 'nextPageToken,files(id,name,appProperties)', pageSize: '200' });
      if (page) parametres.set('pageToken', page);
      const reponse = await lireJson(`${drive}?${parametres}`);
      fichiers.push(...(reponse.files || []));
      page = reponse.nextPageToken || '';
      if (!page) break;
    }
    return fichiers;
  }

  async function trouver(cle, valeur, parent, type) {
    const q = `appProperties has { key='${cle}' and value='${echapper(valeur)}' } and '${echapper(parent)}' in parents `
      + `and mimeType='${type}' and trashed=false`;
    return (await lister(q))[0]?.id || '';
  }

  async function creer(nom, type, parent, proprietes) {
    const cree = await lireJson(`${drive}?fields=id`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: nom, mimeType: type, parents: [parent], appProperties: proprietes })
    });
    if (!cree.id) throw new Error(`« ${nom} » n’a pas pu être créé.`);
    return cree.id;
  }

  function noter(details) {
    journaux.ajouter('general', { action: 'Création (Relations)', resultat: 'créé', details, chantier: 'Relations' });
  }

  // Plan, en LECTURE seule : ce qui serait créé, ce qui existe déjà, ce qui demande le choix de Max.
  async function preparer(valeurs, appCap) {
    if (!appCap) throw new Error('Choisis d’abord le dossier « App Cap » dans « Réglages du Drive ».');
    const calcul = relations.calculer(valeurs);
    const racine = await trouver(ETIQUETTES.racine, 'racine', appCap, DOSSIER);
    const existants = racine
      ? (await lister(`'${echapper(racine)}' in parents and mimeType='${DOSSIER}' and trashed=false`))
        .filter(f => f.appProperties?.[ETIQUETTES.personne])
        .map(f => ({ id: f.id, nom: f.name, cle: f.appProperties[ETIQUETTES.personne], ligne: Number(f.appProperties[ETIQUETTES.ligne] || 0) }))
      : [];
    const parCle = new Map(existants.map(e => [e.cle, e]));
    const clesFiches = new Set(calcul.cles);
    const sansFiche = existants.filter(e => !clesFiches.has(e.cle));
    const plan = { calcul, aFaire: [], deja: [], renommages: [], orphelins: [] };
    for (const fiche of calcul.aCreer) {
      if (parCle.has(fiche.cle)) { plan.deja.push(fiche); continue; }
      // Même ligne du Dictionnaire qu'un dossier dont la fiche n'existe plus : sans doute un changement
      // de nom. Rien n'est créé ; Cap propose seulement « Renommer ? ».
      const ancien = sansFiche.find(e => e.ligne === fiche.numero && !plan.renommages.some(r => r.ancien === e.nom));
      if (ancien) plan.renommages.push({ numero: fiche.numero, ancien: ancien.nom, nouveau: fiche.nomDossier });
      else plan.aFaire.push(fiche);
    }
    plan.orphelins = sansFiche.filter(e => !plan.renommages.some(r => r.ancien === e.nom)).map(e => e.nom);
    plan.bloque = calcul.homonymes.length + calcul.incompletes.length + calcul.typeAbsent.length + plan.renommages.length > 0;
    return plan;
  }

  // Une personne : son dossier, puis ses trois parties ; chaque élément est cherché juste avant.
  async function creerPersonne(fiche, racine) {
    let crees = 0;
    let dossier = await trouver(ETIQUETTES.personne, fiche.cle, racine, DOSSIER);
    if (!dossier) {
      dossier = await creer(fiche.nomDossier, DOSSIER, racine, { [ETIQUETTES.personne]: fiche.cle, [ETIQUETTES.ligne]: String(fiche.numero) });
      noter(`${NOM_RACINE} › ${fiche.nomDossier}`);
      crees++;
    }
    for (const partie of PARTIES) {
      if (await trouver(ETIQUETTES.partie, partie.cle, dossier, partie.type)) continue;
      await creer(partie.nom, partie.type, dossier, { [ETIQUETTES.partie]: partie.cle });
      noter(`${NOM_RACINE} › ${fiche.nomDossier} › ${partie.nom}`);
      crees++;
    }
    return crees;
  }

  async function executer(plan, { appCap, sansLesFichesAChoisir = false, surProgres = () => {} }) {
    if (plan.bloque && !sansLesFichesAChoisir) return { arrete: true, crees: 0, personnes: 0 };
    let racine = await trouver(ETIQUETTES.racine, 'racine', appCap, DOSSIER);
    let crees = 0;
    const liste = [...plan.aFaire, ...plan.deja];
    if (!liste.length) return { arrete: false, crees: 0, personnes: 0 };
    if (!racine) {
      racine = await creer(NOM_RACINE, DOSSIER, appCap, { [ETIQUETTES.racine]: 'racine' });
      noter(NOM_RACINE);
      crees++;
    }
    let personnes = 0;
    for (const [i, fiche] of liste.entries()) {
      surProgres(i + 1, liste.length);
      const n = await creerPersonne(fiche, racine);
      crees += n;
      if (n) personnes++;
    }
    return { arrete: false, crees, personnes };
  }

  // Un seul travail à la fois : un second appui pendant le travail ne crée rien.
  function lancer(plan, options) {
    if (enCours) return Promise.resolve({ refuse: true, crees: 0, personnes: 0 });
    enCours = executer(plan, options).finally(() => { enCours = null; });
    return enCours;
  }

  // ----- Écran de vérification (textContent seulement) -----
  function ecran(doc, plan, { appCap } = {}) {
    const d = doc.getElementById('verification-relations');
    const el = id => doc.getElementById(id);
    const vider = noeud => { while (noeud.firstChild) noeud.firstChild.remove(); };
    const liste = (noeud, lignes) => {
      vider(noeud);
      for (const ligne of lignes) { const li = doc.createElement('li'); li.textContent = ligne; noeud.append(li); }
    };
    const montrer = (id, oui) => { el(id).hidden = !oui; };
    const etat = texte => { el('relations-etat').textContent = texte; };
    const nombre = plan.aFaire.length + plan.deja.length;
    let sansLesFichesAChoisir = false;
    let refuse = false;

    el('relations-nombre').textContent = `${plan.aFaire.length} dossier(s) « r_ » à créer dans « ${NOM_RACINE} »`
      + (plan.deja.length ? ` ; ${plan.deja.length} déjà créé(s) par Cap (complétés s’il leur manque une partie).` : '.');
    liste(el('relations-liste'), plan.aFaire.map(f => f.nomDossier));
    const problemes = [
      ...plan.calcul.homonymesNoms.map(h => `Homonymes : ${h.nomDossier} (lignes ${h.numeros.join(', ')}). Lequel est qui ?`),
      ...plan.calcul.incompletes.map(n => `Fiche incomplète (prénom ou nom manquant) : ligne ${n}.`),
      ...plan.calcul.typeAbsent.map(n => `Fiche sans type : ligne ${n}. Est-ce une personne ?`),
      ...plan.renommages.map(r => `Renommer ? « ${r.ancien} » deviendrait « ${r.nouveau} » (ligne ${r.numero}). Rien n’est fait tout seul.`)
    ];
    liste(el('relations-problemes'), problemes);
    montrer('relations-arret', plan.bloque);
    montrer('relations-question', !plan.bloque);
    montrer('relations-confirmer', false);
    el('relations-question-texte').textContent = QUESTION;
    el('relations-creer').disabled = false;
    etat(plan.orphelins.length ? `${plan.orphelins.length} dossier(s) « r_ » sans fiche dans le Dictionnaire : gardés tels quels (Cap ne supprime rien).` : '');

    el('relations-corriger').onclick = () => {
      montrer('relations-arret', false);
      etat('D’accord : rien n’est créé. Corrige le Dictionnaire, puis refais le calcul.');
    };
    el('relations-sans-probleme').onclick = () => {
      sansLesFichesAChoisir = true;
      montrer('relations-arret', false);
      montrer('relations-question', true);
    };
    el('relations-oui-deja').onclick = () => {
      refuse = true;
      montrer('relations-question', false);
      montrer('relations-confirmer', false);
      etat('D’accord : rien n’est créé. Cap ne voit pas les dossiers faits à la main : dis-moi lesquels, on les retirera de la liste d’abord.');
    };
    el('relations-non-jamais').onclick = () => {
      if (refuse) return;
      montrer('relations-question', false);
      if (!nombre) { etat('Rien à créer.'); return; }
      el('relations-creer').textContent = `Oui, crée ces ${nombre} dossier(s), une personne après l’autre`;
      montrer('relations-confirmer', true);
    };
    const travail = { promesse: null };
    el('relations-creer').onclick = () => {
      if (refuse || el('relations-creer').disabled) return;
      el('relations-creer').disabled = true;
      etat('Création en cours… (une personne après l’autre)');
      travail.promesse = lancer(plan, { appCap, sansLesFichesAChoisir,
        surProgres: (i, total) => etat(`Création en cours : personne ${i} sur ${total}…`) })
        .then(r => {
          if (r.refuse) return r;
          etat(r.arrete ? 'Arrêté : des fiches demandent ton choix. Rien n’a été créé.'
            : `Terminé : ${r.crees} élément(s) créé(s), pour ${r.personnes} personne(s). Rien n’a été supprimé.`);
          return r;
        })
        .catch(erreur => {
          etat(`Arrêt au milieu (${String(erreur && erreur.message || 'raison inconnue').slice(0, 120)}). Ce qui est fait est gardé ; relancer reprendra sans doublon.`);
          return { erreur };
        });
      return travail.promesse;
    };
    if (d && !d.open) { try { d.showModal(); } catch (e) { d.setAttribute('open', ''); } }
    el('relations-fermer').onclick = () => { if (d && d.open) d.close(); };
    return travail;
  }

  return { NOM_RACINE, PARTIES, ETIQUETTES, QUESTION, preparer, lancer, ecran };
})();
