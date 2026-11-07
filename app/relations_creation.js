'use strict';

// Dossiers « Relations », ÉTAPE 3 (06/11/2026) : création des dossiers, testée UNIQUEMENT sur un faux
// Drive et un faux Dictionnaire (FICTIF). ÉTAPE 4 (06/11/2026, décision de Max) : un seul bouton,
// « Créer UN dossier d'essai », pour UNE personne choisie par Max (au plus 5 éléments créés) ; la
// création de toutes les personnes : ÉTAPE 5, un bouton à part, à la demande seulement.
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
  const envoi = 'https://www.googleapis.com/upload/drive/v3/files';
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
      const parametres = new URLSearchParams({ q, fields: 'nextPageToken,files(id,name,mimeType,appProperties)', pageSize: '200' });
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

  async function creer(nom, type, parent, proprietes, texte = '') {
    const infos = { name: nom, mimeType: type, parents: [parent], appProperties: proprietes };
    if (texte) return creerAvecTexte(infos, texte);
    const cree = await lireJson(`${drive}?fields=id`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(infos)
    });
    if (!cree.id) throw new Error(`« ${nom} » n’a pas pu être créé.`);
    return cree.id;
  }

  // 06/11/2026, demande de Max : le « Journal de bord » naît avec sa première entrée. Le document est
  // créé par l'envoi de fichiers du Drive (même adresse que les scans, droit drive.file) : un petit
  // texte que Google convertit lui-même en Google Doc. Pas de service Google Docs.
  // Correction du 06/11/2026 (anomalie vue par Max : « crÃ©ation » au lieu de « création ») : Google
  // a lu le texte brut comme s'il n'était pas en UTF-8, malgré « charset=UTF-8 ». Le texte part donc
  // en petite page HTML dont TOUS les caractères sont simples (A-Z, chiffres…) : chaque lettre
  // accentuée est écrite par son numéro (é → &#233;). Aucun encodage ne peut plus la déformer.
  function texteEnHtml(texte) {
    const sur = [...String(texte)].map(c => {
      if (c === '&') return '&amp;';
      if (c === '<') return '&lt;';
      if (c === '>') return '&gt;';
      if (c === '"') return '&quot;';
      const code = c.codePointAt(0);
      return code > 126 || code < 32 ? `&#${code};` : c;
    }).join('');
    return `<!DOCTYPE html><html><head><meta charset="utf-8"></head><body><p>${sur}</p></body></html>`;
  }

  async function creerAvecTexte(infos, texte) {
    const limite = `cap${Date.now().toString(36)}${Math.random().toString(36).slice(2)}`;
    // La fiche du fichier (JSON) reste en UTF-8 : les noms de dossiers accentués y sont déjà justes.
    const corps = `--${limite}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n${JSON.stringify(infos)}\r\n`
      + `--${limite}\r\nContent-Type: text/html; charset=UTF-8\r\n\r\n${texteEnHtml(texte)}\r\n--${limite}--`;
    const cree = await lireJson(`${envoi}?uploadType=multipart&fields=id,mimeType`, {
      method: 'POST', headers: { 'Content-Type': `multipart/related; boundary=${limite}` }, body: corps
    });
    if (!cree.id) throw new Error(`« ${infos.name} » n’a pas pu être créé.`);
    // Google n'a pas fait un Google Doc : on s'arrête (rien d'autre n'est créé, rien n'est supprimé).
    if (cree.mimeType && cree.mimeType !== infos.mimeType) throw new Error(`« ${infos.name} » n’a pas été converti en Google Doc : arrêt.`);
    return cree.id;
  }

  // Jour et heure de la première entrée : l'horloge du téléphone, écrite à l'heure de Paris.
  function dateHeure(date = new Date()) {
    const parties = new Intl.DateTimeFormat('en-GB', { timeZone: 'Europe/Paris', year: 'numeric', month: '2-digit',
      day: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).formatToParts(date);
    const v = type => parties.find(p => p.type === type).value;
    return `${v('day')}/${v('month')}/${v('year')}, ${v('hour')}:${v('minute')}`;
  }
  function premiereEntree(fiche, date = new Date()) {
    return `${dateHeure(date)} : création du dossier ${NOM_RACINE} de ${fiche.nomDossier.slice(relations.PREFIXE.length)}`;
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
    plan.nombreExistants = existants.length;
    plan.bloque = calcul.homonymes.length + calcul.incompletes.length + calcul.typeAbsent.length + plan.renommages.length > 0;
    return plan;
  }

  // Étape 4 (essai, décision de Max) : UNE seule personne, choisie par Max. Refusé si Cap a déjà créé
  // le dossier d'une AUTRE personne (jamais plus d'un dossier de personne avant l'étape 5).
  function planEssai(plan, numero) {
    const fiche = [...plan.aFaire, ...plan.deja].find(f => f.numero === numero);
    if (!fiche) throw new Error('Cette fiche ne peut pas servir d’essai. Rien n’a été créé.');
    const deja = plan.deja.includes(fiche);
    if (plan.nombreExistants > (deja ? 1 : 0)) {
      throw new Error('Un dossier d’essai existe déjà pour une autre personne : les autres attendent l’étape 5. Rien n’a été créé.');
    }
    return { calcul: plan.calcul, aFaire: deja ? [] : [fiche], deja: deja ? [fiche] : [], renommages: [], orphelins: [],
      nombreExistants: plan.nombreExistants, bloque: false, essai: true };
  }

  // Une personne : son dossier, puis ses trois parties ; chaque élément est cherché juste avant.
  async function creerPersonne(fiche, racine, fabriquer) {
    let crees = 0;
    let dossier = await trouver(ETIQUETTES.personne, fiche.cle, racine, DOSSIER);
    if (!dossier) {
      dossier = await fabriquer(fiche.nomDossier, DOSSIER, racine, { [ETIQUETTES.personne]: fiche.cle, [ETIQUETTES.ligne]: String(fiche.numero) });
      noter(`${NOM_RACINE} › ${fiche.nomDossier}`);
      crees++;
    }
    for (const partie of PARTIES) {
      if (await trouver(ETIQUETTES.partie, partie.cle, dossier, partie.type)) continue;
      await fabriquer(partie.nom, partie.type, dossier, { [ETIQUETTES.partie]: partie.cle },
        partie.cle === 'journal' ? premiereEntree(fiche) : '');
      noter(`${NOM_RACINE} › ${fiche.nomDossier} › ${partie.nom}`);
      crees++;
    }
    return crees;
  }

  async function executer(plan, { appCap, sansLesFichesAChoisir = false, surProgres = () => {} }) {
    if (plan.bloque && !sansLesFichesAChoisir) return { arrete: true, crees: 0, personnes: 0 };
    const liste = [...plan.aFaire, ...plan.deja];
    if (plan.essai && liste.length !== 1) throw new Error('Essai : une seule personne à la fois. Rien n’a été créé.');
    // Plafond : « Relations » + 4 éléments par personne (essai : au plus 5), jamais au-delà.
    const plafond = 1 + liste.length * (1 + PARTIES.length);
    let crees = 0;
    const fabriquer = async (...args) => {
      if (crees >= plafond) throw new Error('Plafond de créations atteint : arrêt, rien de plus n’est créé.');
      const id = await creer(...args);
      crees++;
      return id;
    };
    let racine = await trouver(ETIQUETTES.racine, 'racine', appCap, DOSSIER);
    if (!liste.length) return { arrete: false, crees: 0, personnes: 0 };
    if (!racine) {
      racine = await fabriquer(NOM_RACINE, DOSSIER, appCap, { [ETIQUETTES.racine]: 'racine' });
      noter(NOM_RACINE);
    }
    let personnes = 0;
    for (const [i, fiche] of liste.entries()) {
      surProgres(i + 1, liste.length);
      if (await creerPersonne(fiche, racine, fabriquer)) personnes++;
    }
    return { arrete: false, crees, personnes };
  }

  // ----- Réparation des accents des « Journal de bord » (06/11/2026, accord de Max) -----
  // Les journaux créés avant la correction ont une première entrée abîmée (« crÃ©ation »). Cap ne
  // répare QUE un journal qui contient exactement cette seule ligne abîmée, et seulement si la ligne
  // réparée est bien « JJ/MM/AAAA, HH:MM : création du dossier Relations de <nom du dossier> » (date et
  // heure d'origine gardées). Tout autre contenu (vide, écrit à la main, déjà juste) : on n'y touche pas.
  // Même document, même adresse ; Google garde l'ancienne version dans son historique : rien n'est perdu.
  // Jamais de suppression ; une ligne dans le Journal Général par réparation.
  const MODELE_ENTREE = /^(\d\d\/\d\d\/\d{4}, \d\d:\d\d) : création du dossier Relations de (.+)$/;
  let carteOctets = null;
  function octetsDe(texte) {
    if (!carteOctets) {
      carteOctets = new Map();
      const lecteur = new TextDecoder('windows-1252');
      for (let b = 0; b < 256; b++) carteOctets.set(lecteur.decode(new Uint8Array([b])), b);
      for (let b = 0x80; b < 0xA0; b++) if (!carteOctets.has(String.fromCharCode(b))) carteOctets.set(String.fromCharCode(b), b);
    }
    const octets = [];
    for (const c of texte) {
      if (!carteOctets.has(c)) return null;
      octets.push(carteOctets.get(c));
    }
    return new Uint8Array(octets);
  }
  // « crÃ©ation » → « création » (texte UTF-8 qui avait été lu comme un autre encodage). '' si impossible.
  function texteRepare(abime) {
    const octets = octetsDe(abime);
    if (!octets) return '';
    try { return new TextDecoder('utf-8', { fatal: true }).decode(octets); } catch (erreur) { return ''; }
  }
  function nettoyer(texte) { return String(texte || '').replace(/^\uFEFF/, '').replace(/\r\n/g, '\n').trim(); }
  function examiner(texteLu, nomDossier) {
    const texte = nettoyer(texteLu);
    const nom = nomDossier.slice(relations.PREFIXE.length);
    const conforme = t => { const m = MODELE_ENTREE.exec(t); return Boolean(m && m[2] === nom); };
    if (conforme(texte)) return { etat: 'juste' };
    if (!texte || texte.includes('\n')) return { etat: 'intouchable' };
    const repare = texteRepare(texte);
    if (repare && repare !== texte && conforme(repare)) return { etat: 'abime', apres: repare };
    return { etat: 'intouchable' };
  }
  async function lireTexte(id) {
    return (await googleConnexion.appeler(`${drive}/${encodeURIComponent(id)}/export?mimeType=text%2Fplain`)).text();
  }

  // Liste, en LECTURE seule : journaux à réparer, déjà justes, à ne pas toucher.
  async function preparerReparation(appCap) {
    if (!appCap) throw new Error('Choisis d’abord le dossier « App Cap » dans « Réglages du Drive ».');
    const plan = { aReparer: [], justes: [], intouchables: [] };
    const racine = await trouver(ETIQUETTES.racine, 'racine', appCap, DOSSIER);
    if (!racine) return plan;
    const personnes = (await lister(`'${echapper(racine)}' in parents and mimeType='${DOSSIER}' and trashed=false`))
      .filter(f => f.appProperties?.[ETIQUETTES.personne]);
    for (const personne of personnes) {
      const journal = await trouver(ETIQUETTES.partie, 'journal', personne.id, DOC);
      if (!journal) continue;
      const verdict = examiner(await lireTexte(journal), personne.name);
      const entree = { id: journal, nomDossier: personne.name, apres: verdict.apres || '' };
      ({ abime: plan.aReparer, juste: plan.justes, intouchable: plan.intouchables })[verdict.etat].push(entree);
    }
    for (const liste of Object.values(plan)) liste.sort((a, b) => a.nomDossier.localeCompare(b.nomDossier, 'fr'));
    return plan;
  }

  async function reparerUn(entree) {
    // Relu JUSTE AVANT : s'il a changé depuis la liste (écrit à la main…), on n'y touche pas.
    const avant = examiner(await lireTexte(entree.id), entree.nomDossier);
    if (avant.etat !== 'abime' || avant.apres !== entree.apres) return false;
    await googleConnexion.appeler(`${envoi}/${encodeURIComponent(entree.id)}?uploadType=media&fields=id`, {
      method: 'PATCH', headers: { 'Content-Type': 'text/html; charset=UTF-8' }, body: texteEnHtml(entree.apres)
    });
    // Vérifié après : sinon, arrêt (les journaux suivants ne sont pas touchés).
    if (examiner(await lireTexte(entree.id), entree.nomDossier).etat !== 'juste') {
      throw new Error(`Le « Journal de bord » de ${entree.nomDossier} n’a pas le bon texte après réparation : arrêt, les autres ne sont pas touchés.`);
    }
    journaux.ajouter('general', { action: 'Réparation des accents (Relations)', resultat: 'réparé',
      details: `${NOM_RACINE} › ${entree.nomDossier} › Journal de bord`, chantier: 'Relations' });
    return true;
  }

  // Un journal après l'autre ; un second appui pendant le travail ne fait rien.
  let reparationEnCours = null;
  function lancerReparation(entrees) {
    if (reparationEnCours) return Promise.resolve({ refuse: true, repares: 0, sautes: 0 });
    reparationEnCours = (async () => {
      let repares = 0;
      let sautes = 0;
      for (const entree of entrees) { if (await reparerUn(entree)) repares++; else sautes++; }
      return { repares, sautes };
    })().finally(() => { reparationEnCours = null; });
    return reparationEnCours;
  }

  // Bouton « Réparer les accents des Journaux de bord » : liste et nombres, puis UN journal pour
  // vérifier, puis « Oui, répare les N autres » ; chaque étape attend un appui de Max.
  function brancherReparation(doc, { appCap }) {
    const el = id => doc.getElementById(id);
    const bouton = el('reparer-relations');
    const zone = el('resume-reparer-relations');
    const un = el('reparer-un-relations');
    const tous = el('reparer-tous-relations');
    if (!bouton || !zone || !un || !tous) return;
    let plan = null;
    const ecrire = lignes => { zone.hidden = false; zone.textContent = lignes.join('\n'); };
    bouton.addEventListener('click', async () => {
      un.hidden = true;
      tous.hidden = true;
      ecrire(['Lecture des « Journal de bord »… (rien n’est modifié)']);
      try {
        const dossier = await appCap();
        if (!dossier) { ecrire(['Choisis d’abord le dossier « App Cap » dans « Réglages du Drive », avec Cap ouvert dans Chrome. Rien n’a été modifié.']); return; }
        plan = await preparerReparation(dossier.id);
        ecrire([`À réparer : ${plan.aReparer.length} « Journal de bord ».`,
          `Déjà justes : ${plan.justes.length}.`,
          `Pas touchés (vides, ou avec autre chose que la première entrée) : ${plan.intouchables.length}`
            + (plan.intouchables.length ? ` : ${plan.intouchables.map(e => e.nomDossier).join(', ')}.` : '.'),
          'Rien n’est encore modifié.']);
        if (plan.aReparer.length) {
          un.textContent = `Réparer UN journal pour vérifier : ${plan.aReparer[0].nomDossier}`;
          un.disabled = false;
          un.hidden = false;
        }
      } catch (erreur) {
        ecrire([`Lecture impossible (${String(erreur && erreur.message || 'raison inconnue').slice(0, 120)}). Rien n’a été modifié.`]);
      }
    });
    const reparer = async (entrees, bouton2, apres) => {
      if (bouton2.disabled) return;
      bouton2.disabled = true;
      ecrire(['Réparation en cours… (un journal après l’autre)']);
      try {
        const r = await lancerReparation(entrees);
        if (r.refuse) return;
        apres(r);
      } catch (erreur) {
        ecrire([`Arrêt : ${String(erreur && erreur.message || 'raison inconnue').slice(0, 200)} Rien n’a été supprimé.`]);
      }
    };
    un.addEventListener('click', () => reparer([plan.aReparer[0]], un, r => {
      un.hidden = true;
      const premier = plan.aReparer[0];
      ecrire([r.repares ? `Réparé : ${premier.nomDossier}. Première entrée : « ${premier.apres} ».` : `${premier.nomDossier} a changé depuis la liste : pas touché.`,
        'Ouvre ce « Journal de bord » pour vérifier. Si c’est juste, répare les autres.']);
      const reste = plan.aReparer.length - 1;
      if (reste > 0) {
        tous.textContent = `Oui, répare les ${reste} autres journaux`;
        tous.disabled = false;
        tous.hidden = false;
      }
    }));
    tous.addEventListener('click', () => reparer(plan.aReparer.slice(1), tous, r => {
      tous.hidden = true;
      ecrire([`Terminé : ${r.repares} journal(aux) réparé(s)` + (r.sautes ? ` ; ${r.sautes} pas touché(s) car modifié(s) depuis la liste.` : '.'), 'Rien n’a été supprimé.']);
    }));
  }

  // ----- Essai de visibilité (06/11/2026, accord de Max) : LECTURE SEULE, des NOMBRES seulement -----
  // Cap voit-il les fichiers que Max dépose à la main dans les dossiers « r_ » ? Pour chaque dossier
  // « r_ » créé par Cap : nombre de MP3, d'images, de sous-dossiers (et d'autres fichiers) VISIBLES par
  // Cap, en descendant dans les sous-dossiers (3 niveaux). Les éléments créés par Cap ne sont pas
  // comptés (on regarde quand même dans « Reçus » et « Envoyés »). Aucun nom de fichier n'est affiché
  // ni gardé ; rien n'est modifié ni créé.
  const PROFONDEUR_VISIBILITE = 3;
  function sorteDe(f) {
    if (f.mimeType === DOSSIER) return 'sousDossiers';
    if (/^audio\/(mpeg|mp3)$/.test(f.mimeType || '') || /\.mp3$/i.test(f.name || '')) return 'mp3';
    if (/^image\//.test(f.mimeType || '')) return 'images';
    return 'autres';
  }
  async function compterDans(dossier, compte, profondeur) {
    for (const f of await lister(`'${echapper(dossier)}' in parents and trashed=false`)) {
      const deCap = Boolean(f.appProperties?.[ETIQUETTES.partie] || f.appProperties?.[ETIQUETTES.personne]);
      if (!deCap) compte[sorteDe(f)]++;
      if (f.mimeType === DOSSIER && profondeur < PROFONDEUR_VISIBILITE) await compterDans(f.id, compte, profondeur + 1);
    }
  }
  async function essaiVisibilite(appCap) {
    if (!appCap) throw new Error('Choisis d’abord le dossier « App Cap » dans « Réglages du Drive ».');
    const racine = await trouver(ETIQUETTES.racine, 'racine', appCap, DOSSIER);
    if (!racine) return { dossiers: 0, lignes: [] };
    const personnes = (await lister(`'${echapper(racine)}' in parents and mimeType='${DOSSIER}' and trashed=false`))
      .filter(f => f.appProperties?.[ETIQUETTES.personne]);
    const lignes = [];
    for (const personne of personnes) {
      const compte = { mp3: 0, images: 0, sousDossiers: 0, autres: 0 };
      await compterDans(personne.id, compte, 1);
      lignes.push({ nomDossier: personne.name, ...compte });
    }
    lignes.sort((a, b) => a.nomDossier.localeCompare(b.nomDossier, 'fr'));
    return { dossiers: personnes.length, lignes };
  }
  function resumerVisibilite(r) {
    const avec = r.lignes.filter(l => l.mp3 + l.images + l.sousDossiers + l.autres > 0);
    const total = cle => r.lignes.reduce((n, l) => n + l[cle], 0);
    return [
      `Essai de visibilité (lecture seule, rien n’est modifié) : ${r.dossiers} dossier(s) « r_ » lus.`,
      ...avec.map(l => `${l.nomDossier} : ${l.mp3} MP3 · ${l.images} image(s) · ${l.sousDossiers} sous-dossier(s)` + (l.autres ? ` · ${l.autres} autre(s)` : '')),
      `${r.dossiers - avec.length} autre(s) dossier(s) : rien de visible à part ce que Cap a créé.`,
      `Total visible : ${total('mp3')} MP3, ${total('images')} image(s), ${total('sousDossiers')} sous-dossier(s), ${total('autres')} autre(s).`
    ].join('\n');
  }
  // 07/11/2026 (accord de Max) : après « Montrer « Relations » à Google », dire QUEL dossier a été
  // montré (son nom) et si c'est bien le « Relations » créé par Cap (même identifiant), le dossier d'une
  // personne, ou un autre dossier. Lecture seule : la fiche du dossier montré (nom, étiquette).
  async function verdictDossierMontre(choix, appCap) {
    let nom = choix.nom || '';
    let proprietes = {};
    try {
      const fiche = await lireJson(`${drive}/${encodeURIComponent(choix.id)}?fields=id%2Cname%2CappProperties`);
      nom = fiche.name || nom;
      proprietes = fiche.appProperties || {};
    } catch (erreur) { /* fiche illisible : on garde le nom donné par la fenêtre de Google */ }
    let racine = '';
    try { racine = appCap ? await trouver(ETIQUETTES.racine, 'racine', appCap, DOSSIER) : ''; } catch (erreur) { racine = ''; }
    const titre = `Dossier montré : « ${nom || 'nom inconnu'} »`;
    if (racine && choix.id === racine) return `${titre}\nOUI : c’est bien le « Relations » créé par Cap. Appuie de nouveau sur « Essai de visibilité ».`;
    if (proprietes[ETIQUETTES.personne]) return `${titre}\nNON : ce n’est pas « Relations », c’est le dossier d’une personne. Recommence et choisis « Relations ».`;
    if (!racine) return `${titre}\nJe ne sais pas : Cap ne retrouve pas son dossier « Relations » (choisis d’abord « App Cap »).`;
    return `${titre}\nNON : ce n’est pas le « Relations » créé par Cap (peut-être ton ancien dossier d’essai). Recommence et choisis l’autre.`;
  }

  function brancherVisibilite(doc, { appCap, montrer }) {
    const bouton = doc.getElementById('visibilite-relations');
    const montrerBouton = doc.getElementById('montrer-relations');
    const zone = doc.getElementById('resume-visibilite-relations');
    if (!bouton || !montrerBouton || !zone) return;
    // Le message reste visible sans faire défiler : la zone est ramenée au milieu de l'écran.
    const ecrire = texte => {
      zone.hidden = false;
      zone.textContent = texte;
      try { zone.scrollIntoView({ block: 'center' }); } catch (erreur) { /* rien */ }
    };
    bouton.addEventListener('click', () => attenteLecture.pendant(bouton, async () => {
      ecrire('Lecture des dossiers « r_ »… (rien n’est modifié)');
      try {
        const dossier = await appCap();
        if (!dossier) { ecrire('Choisis d’abord le dossier « App Cap » dans « Réglages du Drive », avec Cap ouvert dans Chrome.'); return; }
        ecrire(resumerVisibilite(await essaiVisibilite(dossier.id)));
      } catch (erreur) {
        ecrire(`Lecture impossible (${String(erreur && erreur.message || 'raison inconnue').slice(0, 120)}). Rien n’a été modifié.`);
      }
    }));
    // Temps 2 de l'essai : Max montre « Relations » (celui créé par Cap) au sélecteur Google, dans Chrome.
    montrerBouton.addEventListener('click', async () => {
      ecrire('Ouverture de la fenêtre de Google… (elle peut mettre quelques secondes)');
      try {
        const choix = await montrer();
        if (!choix) { ecrire('Rien n’a été choisi.'); return; }
        const dossier = await appCap().catch(() => null);
        ecrire(await verdictDossierMontre(choix, dossier && dossier.id));
      } catch (erreur) {
        ecrire(`Le sélecteur Google n’a pas pu s’ouvrir (${String(erreur && erreur.message || 'raison inconnue').slice(0, 120)}). Fais-le dans Chrome.`);
      }
    });
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
    const nombre = plan.aFaire.length;
    let sansLesFichesAChoisir = false;
    let refuse = false;

    if (plan.essai) {
      // Étape 4 : ce qui sera créé, élément par élément, avant toute question.
      const nom = [...plan.aFaire, ...plan.deja][0].nomDossier;
      el('relations-nombre').textContent = plan.deja.length
        ? 'Ce dossier d’essai existe déjà : Cap ajoutera seulement ce qui manque, sans doublon :'
        : 'Ce qui sera créé (un seul dossier d’essai) :';
      liste(el('relations-liste'), [`App Cap › ${NOM_RACINE} › ${nom}`, ...PARTIES.map(p => `${nom} › ${p.nom}`)]);
    } else {
      // Étape 5 : le nombre, puis les dossiers déjà faits (écartés : rien n'y est recréé ni réécrit).
      el('relations-nombre').textContent = `${plan.aFaire.length} dossier(s) « r_ » à créer dans « ${NOM_RACINE} »`
        + (plan.deja.length ? ` ; ${plan.deja.length} déjà fait(s), écarté(s) : rien n’y est recréé ni réécrit (Cap ajoute seulement une partie qui manquerait).` : '.');
      liste(el('relations-liste'), plan.aFaire.map(f => f.nomDossier));
    }
    const problemes = [
      ...plan.calcul.homonymesNoms.map(h => `Homonymes : ${h.nomDossier} (lignes ${h.numeros.join(', ')}). Lequel est qui ?`),
      ...plan.calcul.incompletes.map(n => `Fiche incomplète (prénom ou nom manquant) : ligne ${n}.`),
      ...plan.calcul.typeAbsent.map(n => `Fiche sans type : ligne ${n}. Est-ce une personne ?`),
      ...plan.renommages.map(r => `Renommer ? « ${r.ancien} » deviendrait « ${r.nouveau} » (ligne ${r.numero}). Rien n’est fait tout seul.`)
    ];
    liste(el('relations-problemes'), problemes);
    // Mis de côté, avec leur nombre (rien n'est créé pour eux).
    const fichesHomonymes = plan.calcul.homonymes.reduce((total, g) => total + g.length, 0);
    el('relations-mis-de-cote').textContent = `Mis de côté : ${plan.calcul.homonymes.length} homonyme(s) (${fichesHomonymes} fiche(s)), `
      + `${plan.calcul.incompletes.length} fiche(s) incomplète(s), ${plan.calcul.typeAbsent.length} fiche(s) sans type, `
      + `${plan.renommages.length} changement(s) de nom possible(s).`;
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
      if (!nombre && !plan.deja.length) { etat('Rien à créer.'); return; }
      el('relations-creer').textContent = plan.essai ? 'Oui, crée ce dossier'
        : nombre ? `Oui, crée ces ${nombre} dossiers` : `Oui, vérifie les ${plan.deja.length} dossiers déjà faits (rien n’est recréé)`;
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

  // Bouton « Créer UN dossier d'essai » (Réglages du Drive) : lit le Dictionnaire (Prénom, Nom, Type),
  // montre les personnes possibles ; Max en touche UNE ; l'écran de vérification s'ouvre. Rien n'est
  // créé avant « Oui, crée ce dossier ».
  function brancherEssai(doc, { lire, appCap }) {
    const bouton = doc.getElementById('essai-relations');
    const zone = doc.getElementById('resume-essai-relations');
    const choix = doc.getElementById('choix-essai-relations');
    if (!bouton || !zone || !choix) return;
    bouton.addEventListener('click', async () => {
      while (choix.firstChild) choix.firstChild.remove();
      zone.hidden = false;
      zone.textContent = 'Lecture de l’onglet « Dictionnaire »… (rien n’est créé)';
      try {
        const dossier = await appCap();
        if (!dossier) { zone.textContent = 'Choisis d’abord le dossier « App Cap » dans « Réglages du Drive », avec Cap ouvert dans Chrome. Rien n’a été créé.'; return; }
        const valeurs = await lire();
        if (!valeurs) { zone.textContent = 'Choisis d’abord le Dictionnaire général dans « Réglages du Drive ». Rien n’a été créé.'; return; }
        const plan = await preparer(valeurs, dossier.id);
        const possibles = [...plan.aFaire, ...plan.deja].sort((a, b) => a.nomDossier.localeCompare(b.nomDossier, 'fr'));
        zone.textContent = possibles.length ? 'Touche UNE personne pour l’essai (rien n’est encore créé) :' : 'Aucune fiche possible pour l’essai. Rien n’a été créé.';
        for (const fiche of possibles) {
          const b = doc.createElement('button');
          b.type = 'button';
          b.className = 'relations-gros-bouton';
          b.textContent = fiche.nomDossier;
          b.addEventListener('click', () => {
            try { ecran(doc, planEssai(plan, fiche.numero), { appCap: dossier.id }); } catch (erreur) { zone.textContent = erreur.message; }
          });
          choix.append(b);
        }
      } catch (erreur) {
        zone.textContent = `Le Dictionnaire n’a pas pu être lu (${String(erreur && erreur.message || 'raison inconnue').slice(0, 120)}). Rien n’a été créé.`;
      }
    });
  }

  // Étape 5 (06/11/2026, décision de Max) : bouton « Créer les dossiers de toutes les personnes ». Une
  // seule fois, à la demande : aucune mise à jour automatique. Lit le Dictionnaire (Prénom, Nom, Type),
  // puis ouvre l'écran de vérification ; rien n'est créé avant « Oui, crée ces N dossiers ».
  function brancherTous(doc, { lire, appCap }) {
    const bouton = doc.getElementById('tous-relations');
    const zone = doc.getElementById('resume-tous-relations');
    if (!bouton || !zone) return;
    bouton.addEventListener('click', async () => {
      zone.hidden = false;
      zone.textContent = 'Lecture de l’onglet « Dictionnaire »… (rien n’est créé)';
      try {
        const dossier = await appCap();
        if (!dossier) { zone.textContent = 'Choisis d’abord le dossier « App Cap » dans « Réglages du Drive », avec Cap ouvert dans Chrome. Rien n’a été créé.'; return; }
        const valeurs = await lire();
        if (!valeurs) { zone.textContent = 'Choisis d’abord le Dictionnaire général dans « Réglages du Drive ». Rien n’a été créé.'; return; }
        const plan = await preparer(valeurs, dossier.id);
        zone.textContent = 'Vérifie la liste dans la fenêtre qui s’ouvre. Rien n’est encore créé.';
        ecran(doc, plan, { appCap: dossier.id });
      } catch (erreur) {
        zone.textContent = `Le Dictionnaire n’a pas pu être lu (${String(erreur && erreur.message || 'raison inconnue').slice(0, 120)}). Rien n’a été créé.`;
      }
    });
  }

  return { NOM_RACINE, PARTIES, ETIQUETTES, QUESTION, premiereEntree, texteEnHtml, texteRepare, examiner, preparer, planEssai, lancer, ecran, brancherEssai, brancherTous,
    preparerReparation, lancerReparation, brancherReparation, essaiVisibilite, resumerVisibilite, brancherVisibilite };
})();

// Seuls points de départ dans Cap : le bouton d'essai (étape 4) et celui de toutes les personnes
// (étape 5). Jamais au démarrage, jamais de mise à jour automatique, jamais dans les tests.
if (typeof document !== 'undefined' && document.getElementById('essai-relations')
  && !(typeof window !== 'undefined' && window.CAP_TESTS) && typeof classement !== 'undefined' && typeof googlePicker !== 'undefined') {
  const sources = { lire: () => classement.lireDictionnairePersonnes(), appCap: async () => googlePicker.dossierAppCap() };
  relationsCreation.brancherEssai(document, sources);
  relationsCreation.brancherTous(document, sources);
  relationsCreation.brancherReparation(document, sources);
  relationsCreation.brancherVisibilite(document, { appCap: sources.appCap, montrer: () => googlePicker.choisir('relations') });
}
