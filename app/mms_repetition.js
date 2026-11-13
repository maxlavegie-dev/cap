'use strict';

// 12/11/2026 (accord écrit de Max, marche M3c) : RÉPÉTITION FICTIVE du rangement des MMS, dans le Drive du COMPTE CAP.
// - Crée seulement des DOSSIERS VIDES de répétition : « MMS des relations — RÉPÉTITION FICTIVE » (à la racine du compte Cap),
//   et dedans « Personne Test FICTIF » et « À trier ». Chacun porte une marque invisible (appProperties) : ce qui existe déjà
//   n'est jamais recréé (aucun doublon) ; une coupure au milieu se reprend sans rien refaire.
// - Aucun dossier « r_ » n'est créé ni touché ; aucun vrai MMS n'est copié ; aucun fichier n'est envoyé (dossiers vides
//   seulement, avec le droit de création déjà permis : google_compte_relations.js). Rien n'est effacé, renommé, déplacé.
// - Rien n'est créé sans le Oui de Max à l'écran (mms_ecran.js montre d'abord la liste). Une seule création à la fois (verrou).
// - La démonstration (demonstration) range de FAUX messages, sans aucun numéro (des empreintes tirées au hasard), avec la
//   même règle que pour les vrais (mms_rangement.js) : elle montre où chacun irait. Sans DOM.
const mmsRepetition = (() => {
  const DRIVE = 'https://www.googleapis.com/drive/v3/files';
  const DOSSIER = 'application/vnd.google-apps.folder';
  const NOM_RACINE = 'MMS des relations — RÉPÉTITION FICTIVE';
  const NOM_PERSONNE = 'Personne Test FICTIF';
  const NOM_A_TRIER = 'À trier';
  const MARQUES = Object.freeze({ racine: 'cap_mms_repetition_racine', dossier: 'cap_mms_repetition_dossier' });
  const echapper = texte => String(texte).replace(/\\/g, '\\\\').replace(/'/g, "\\'");

  async function parMarque(compte, cle, valeur) {
    const q = `appProperties has { key='${cle}' and value='${echapper(valeur)}' } and mimeType='${DOSSIER}' and trashed=false`;
    const params = new URLSearchParams({ q, fields: 'files(id,name,appProperties)', pageSize: '10', spaces: 'drive' });
    const corps = await (await compte.appeler(`${DRIVE}?${params}`)).json();
    const liste = Array.isArray(corps.files) ? corps.files : [];
    if (liste.length > 1) throw new Error(`Le compte Cap a ${liste.length} dossiers de répétition avec la même marque : rien ne sera créé. Préviens Claude Code.`);
    return liste[0] || null;
  }

  // LECTURE SEULE : ce qui existe et ce qui serait créé.
  async function preparer(compte) {
    const racine = await parMarque(compte, MARQUES.racine, '1');
    const personne = await parMarque(compte, MARQUES.dossier, 'personne_test');
    const aTrier = await parMarque(compte, MARQUES.dossier, 'a_trier');
    const aCreer = [];
    if (!racine) aCreer.push(`le dossier « ${NOM_RACINE} »`);
    if (!personne) aCreer.push(`dedans, le dossier « ${NOM_PERSONNE} »`);
    if (!aTrier) aCreer.push(`dedans, le dossier « ${NOM_A_TRIER} »`);
    return { racine, personne, aTrier, aCreer };
  }

  async function creerUn(compte, corps) {
    const reponse = await compte.appelerEcriture(`${DRIVE}?fields=id`, { method: 'POST', body: JSON.stringify(corps) });
    const r = await reponse.json();
    if (!r || !r.id) throw new Error('Google n’a pas rendu le dossier créé.');
    return r.id;
  }

  let enCours = false;
  // Crée ce qui manque (relu juste avant). Rend { cree: [noms], dejaLa }.
  async function creer(compte) {
    if (enCours) throw new Error('Une création est déjà en cours : attends qu’elle finisse.');
    enCours = true;
    try {
      const p = await preparer(compte);
      const cree = [];
      let idRacine = p.racine && p.racine.id;
      if (!idRacine) {
        idRacine = await creerUn(compte, { name: NOM_RACINE, mimeType: DOSSIER, parents: ['root'], appProperties: { [MARQUES.racine]: '1' } });
        cree.push(NOM_RACINE);
      }
      if (!p.personne) {
        await creerUn(compte, { name: NOM_PERSONNE, mimeType: DOSSIER, parents: [idRacine], appProperties: { [MARQUES.dossier]: 'personne_test' } });
        cree.push(NOM_PERSONNE);
      }
      if (!p.aTrier) {
        await creerUn(compte, { name: NOM_A_TRIER, mimeType: DOSSIER, parents: [idRacine], appProperties: { [MARQUES.dossier]: 'a_trier' } });
        cree.push(NOM_A_TRIER);
      }
      return { cree, dejaLa: !cree.length };
    } finally { enCours = false; }
  }

  // FAUX messages, FAUSSE personne, aucun numéro : où chacun irait. Rend [« … → … »].
  function demonstration(aleatoire = n => crypto.getRandomValues(new Uint8Array(n))) {
    const empreinte = () => [...aleatoire(32)].map(b => b.toString(16).padStart(2, '0')).join('');
    const connue = empreinte();
    const index = { version: 1, empreintes: { [connue]: [NOM_PERSONNE] } };
    const faux = [
      { id: 'FICTIF-1', image: true, groupe: false, empreinte: connue, quoi: 'Faux MMS 1 (photo) de la personne test' },
      { id: 'FICTIF-2', texte: true, groupe: false, empreinte: empreinte(), quoi: 'Faux MMS 2 (texte) d’un numéro inconnu' },
      { id: 'FICTIF-3', video: true, groupe: true, empreinte: connue, quoi: 'Faux MMS 3 (vidéo) envoyé à un groupe' },
      { id: 'FICTIF-4', image: true, groupe: false, empreinte: null, quoi: 'Faux MMS 4 (photo) d’un numéro masqué' }];
    return mmsRangement.classer(faux, index).map(m => `${m.quoi} → « ${m.destination.type === 'personne' ? m.destination.identifiant : NOM_A_TRIER} »`);
  }

  return Object.freeze({ NOM_RACINE, NOM_PERSONNE, NOM_A_TRIER, MARQUES, preparer, creer, demonstration });
})();
