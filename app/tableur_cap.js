'use strict';

// 09/11/2026 (décision de Max, séance 1) : le tableur « Commandes vocales (Cap) », dans le Drive du COMPTE CAP.
// - Cap le crée lui-même, VIDE, à la racine du Drive du compte Cap, avec les MÊMES colonnes que le tableur « Commandes
//   vocales » (lu, jamais modifié : seule sa ligne des titres est recopiée, aucune autre ligne, donc aucun prénom).
// - Il le retrouve par une MARQUE INVISIBLE (appProperties cap_role = commandes_vocales_cap) : renommé ou déplacé par Max,
//   il est retrouvé quand même ; jamais un deuxième.
// - Écriture par l'écriture LIMITÉE du compte Cap (googleCompteRelations.appelerEcriture : droit drive.file, et le code
//   ne laisse passer que créer, marquer, écrire des cases). Jamais de suppression, jamais d'effacement.
// - Séance 1 : créer et retrouver. Les phrases (bouton, reprise de « Phrases apprises ») viennent à la séance 2.
const tableurCap = (() => {
  const NOM = 'Commandes vocales (Cap)';
  const ONGLET = 'Commandes';
  const MODELE = 'Commandes vocales';
  const MARQUE = { cle: 'cap_role', valeur: 'commandes_vocales_cap' };
  const CLE_ID = 'cap_tableur_cap_id_v1';
  const CLE_MARQUE_POSEE = 'cap_tableur_cap_marque_v1';
  // 09/11/2026 (séance 2) : le tampon (changements qui attendent) et la copie gardée sur le téléphone.
  const CLE_TAMPON = 'cap_tableur_cap_tampon_v1';
  const CLE_COPIE = 'cap_tableur_cap_copie_v1';
  const BLOC = 'Expression seule (Cap)';
  const DRIVE = 'https://www.googleapis.com/drive/v3/files';
  const SHEETS = 'https://sheets.googleapis.com/v4/spreadsheets';
  const ID_VALIDE = /^[A-Za-z0-9_-]{10,200}$/;
  const envoyerJson = (methode, corps) => ({ method: methode, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(corps) });

  // dependances : { lire(url) → Response (lecture du compte Cap), ecrire(url, options) → Response (écriture limitée),
  //   stockage, connecte() → bool, lireCsv(texte) → lignes }
  function creer(dependances = {}) {
    const compte = () => (typeof googleCompteRelations !== 'undefined' ? googleCompteRelations : null);
    const lire = dependances.lire || (url => compte().appeler(url));
    const ecrire = dependances.ecrire || ((url, options) => compte().appelerEcriture(url, options));
    const connecte = dependances.connecte || (() => Boolean(compte() && compte().connecte()));
    const lireCsv = dependances.lireCsv || (texte => commandesVocales.lireCsv(texte));
    const maintenant = dependances.maintenant || (() => Date.now());
    const stockageDe = () => dependances.stockage || localStorage;
    const garde = cle => { try { return stockageDe().getItem(cle) || ''; } catch (erreur) { return ''; } };
    const garder = (cle, valeur) => { try { stockageDe().setItem(cle, valeur); } catch (erreur) { /* on retrouvera par la marque */ } };
    const json = async url => (await lire(url)).json();
    let ouverture = null;

    // La ligne des titres du tableur « Commandes vocales » (lu par le compte Cap, à qui Max l'a partagé en lecture).
    async function titresDuModele() {
      const q = `name='${MODELE}' and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false`;
      const liste = await json(`${DRIVE}?${new URLSearchParams({ q, fields: 'files(id)', pageSize: '10' })}`);
      const trouves = Array.isArray(liste.files) ? liste.files : [];
      if (trouves.length !== 1) throw new Error(trouves.length ? `Le compte Cap voit ${trouves.length} tableurs « ${MODELE} » : garde-en un seul partagé avec lui.` : `Le compte Cap ne voit pas le tableur « ${MODELE} ».`);
      const texte = await (await lire(`${DRIVE}/${encodeURIComponent(trouves[0].id)}/export?mimeType=${encodeURIComponent('text/csv')}`)).text();
      const titres = (lireCsv(texte)[0] || []).map(t => String(t || '').trim());
      while (titres.length && !titres[titres.length - 1]) titres.pop();
      if (!titres.length || !titres.some(t => /formulation/i.test(t))) throw new Error(`Les titres du tableur « ${MODELE} » n’ont pas pu être lus : rien n’est créé.`);
      return titres;
    }

    async function encorePresent(id) {
      try {
        const f = await json(`${DRIVE}/${encodeURIComponent(id)}?fields=id,trashed`);
        return Boolean(f && f.id && !f.trashed);
      } catch (erreur) {
        if (erreur.statut === 404 || /erreur 404/.test(String(erreur.message))) return false;
        throw erreur;
      }
    }
    async function chercherParMarque() {
      const q = `appProperties has { key='${MARQUE.cle}' and value='${MARQUE.valeur}' } and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false`;
      const r = await json(`${DRIVE}?${new URLSearchParams({ q, fields: 'files(id)', pageSize: '10' })}`);
      const f = (r.files || []).find(x => ID_VALIDE.test(x.id || ''));
      return f ? f.id : '';
    }
    async function poserMarque(id) {
      await ecrire(`${DRIVE}/${encodeURIComponent(id)}?fields=id`, envoyerJson('PATCH', { appProperties: { [MARQUE.cle]: MARQUE.valeur } }));
      garder(CLE_MARQUE_POSEE, id);
    }
    const lettre = n => String.fromCharCode(64 + Math.min(26, Math.max(1, n)));
    async function creerTableur() {
      const titres = await titresDuModele(); // d'abord : jamais un tableur créé avec des colonnes inventées
      const r = await (await ecrire(SHEETS, envoyerJson('POST', {
        properties: { title: NOM },
        sheets: [{ properties: { sheetId: 0, title: ONGLET, gridProperties: { frozenRowCount: 1 } } }]
      }))).json();
      if (!ID_VALIDE.test(r.spreadsheetId || '')) throw new Error('Google n’a pas rendu le tableur de Cap.');
      garder(CLE_ID, r.spreadsheetId); // gardé tout de suite : jamais un deuxième
      const plage = encodeURIComponent(`'${ONGLET}'!A1:${lettre(titres.length)}1`);
      await ecrire(`${SHEETS}/${encodeURIComponent(r.spreadsheetId)}/values/${plage}?valueInputOption=RAW`, envoyerJson('PUT', { values: [titres] }));
      await poserMarque(r.spreadsheetId);
      return { id: r.spreadsheetId, cree: true, titres };
    }
    async function ouvrir() {
      if (!connecte()) return { id: '', raison: 'pas_connecte' };
      const id = garde(CLE_ID);
      if (ID_VALIDE.test(id) && await encorePresent(id)) {
        if (garde(CLE_MARQUE_POSEE) !== id) await poserMarque(id); // marque pas encore posée (coupure la dernière fois)
        return { id, cree: false };
      }
      const marque = await chercherParMarque();
      if (marque) { garder(CLE_ID, marque); garder(CLE_MARQUE_POSEE, marque); return { id: marque, cree: false }; }
      return creerTableur();
    }
    function trouverOuCreer() {
      if (!ouverture) ouverture = ouvrir().finally(() => { ouverture = null; });
      return ouverture;
    }
    function adresse() {
      const id = garde(CLE_ID);
      return ID_VALIDE.test(id) ? `https://docs.google.com/spreadsheets/d/${encodeURIComponent(id)}/edit` : '';
    }
    // ----- 09/11/2026 (décision de Max, séance 2) : les PHRASES de Max dans ce tableur -----
    // Une ligne par phrase, aux colonnes du modèle (retrouvées par leur titre) : « Ce que je veux » et « Commande » = la
    // commande, « Bloc » = « Expression seule (Cap) » (reconnue dite en entier), « Formulation » = la phrase, « Code
    // commande », « Remarque » = « Ajoutée par Cap le … » + l'identifiant entre crochets [P-…] (pour retrouver la ligne).
    // On n'efface jamais : « retirée le … », « remplacée le … », « choisie par Max le … » s'AJOUTENT à la remarque.
    // Tout passe d'abord par le tampon du téléphone ; il se vide une opération à la fois, seulement après le
    // « c'est écrit » de Google. Pas de réseau, pas de droit : ça attend, rien n'est perdu.
    const jour = () => new Date(maintenant()).toLocaleDateString('fr-FR');
    const lireJson = (cle, defaut) => { try { const v = JSON.parse(garde(cle)); return v === null || v === '' ? defaut : v; } catch (erreur) { return defaut; } };
    function tampon() { const t = lireJson(CLE_TAMPON, []); return Array.isArray(t) ? t : []; }
    function mettreEnAttente(op) { const t = tampon(); t.push(op); stockageDe().setItem(CLE_TAMPON, JSON.stringify(t)); return t.length; }
    function dateCourte(q) { const d = new Date(q); return Number.isNaN(d.getTime()) ? '' : d.toLocaleDateString('fr-FR'); }
    function noterAjout(entree) {
      if (!entree || !entree.id || !String(entree.phrase || '').trim()) return tampon().length;
      const quand = dateCourte(entree.quand || maintenant());
      const remarque = `Ajoutée par Cap le ${quand} (${entree.origine || 'bouton'})${entree.choisie ? ` ; choisie par Max le ${jour()}` : ''}`;
      return mettreEnAttente({ type: 'ajout', id: entree.id, phrase: String(entree.phrase), code: String(entree.code || ''), commande: String(entree.commande || ''), remarque });
    }
    // Reprise d'une ligne de « Phrases apprises » (décision de Max) : même identifiant, marquée « reprise le … ».
    function noterReprise(ligne) {
      if (!ligne || !ligne.id || !String(ligne.phrase || '').trim()) return tampon().length;
      const etat = String(ligne.etat || '').trim();
      const remarque = `Reprise le ${jour()} de « Phrases apprises »${etat ? ` ; état d’origine : ${etat}` : ''}`;
      return mettreEnAttente({ type: 'ajout', id: ligne.id, phrase: String(ligne.phrase), code: String(ligne.code || ''), commande: String(ligne.commande || ''), remarque });
    }
    function noterEtat(id, texte) { return id ? mettreEnAttente({ type: 'etat', id, texte }) : tampon().length; }
    const noterRetrait = id => noterEtat(id, `retirée le ${jour()}`);
    const noterRemplacement = id => noterEtat(id, `remplacée le ${jour()}`);
    const noterChoix = id => noterEtat(id, `choisie par Max le ${jour()}`);

    const plie = s => String(s || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim();
    function colonnesDe(titres) {
      const i = motif => titres.findIndex(t => motif.test(plie(t)));
      return { ceQue: i(/^ce que/), commande: i(/^commande/), bloc: i(/^bloc/), formulation: i(/^formulation/), code: i(/^code/), remarque: i(/^remarque/) };
    }
    function ligneDe(op, titres) {
      const c = colonnesDe(titres);
      const l = titres.map(() => '');
      const mettre = (k, v) => { if (c[k] >= 0) l[c[k]] = v; };
      mettre('ceQue', op.code ? op.commande : 'À traiter à la main');
      mettre('commande', op.commande || (op.code ? '' : 'Aucune ne convient'));
      mettre('bloc', BLOC);
      mettre('formulation', op.phrase.replace(/[\t\n]+/g, ' '));
      mettre('code', op.code);
      mettre('remarque', `${op.remarque} [${op.id}]`);
      return l;
    }
    const identifiantDe = remarque => { const m = String(remarque || '').match(/\[(P-[A-Za-z0-9_-]+)\]/); return m ? m[1] : ''; };
    async function lignesDuTableur(id) {
      const texte = await (await lire(`${DRIVE}/${encodeURIComponent(id)}/export?mimeType=${encodeURIComponent('text/csv')}`)).text();
      return lireCsv(texte);
    }
    async function vider() {
      if (!tampon().length) return { envoyees: 0, attente: 0 };
      if (!connecte()) return { envoyees: 0, attente: tampon().length, raison: 'pas_connecte' };
      let envoyees = 0;
      try {
        const { id } = await trouverOuCreer();
        if (!id) return { envoyees: 0, attente: tampon().length, raison: 'pas_connecte' };
        const lignes = await lignesDuTableur(id);
        const titres = (lignes[0] || []).map(t => String(t || ''));
        while (titres.length && !titres[titres.length - 1].trim()) titres.pop();
        const col = colonnesDe(titres);
        if (col.remarque < 0 || col.formulation < 0) throw new Error('Le tableur « Commandes vocales (Cap) » n’a plus ses titres : rien n’est écrit.');
        const fin = lettre(titres.length);
        const L = lettre(col.remarque + 1);
        while (tampon().length) {
          const op = tampon()[0];
          const rang = lignes.findIndex((l, i) => i > 0 && identifiantDe(l[col.remarque]) === op.id);
          if (op.type === 'ajout') {
            if (rang < 0) { // pas déjà écrite (réponse de Google perdue la dernière fois)
              const ligne = ligneDe(op, titres);
              await ecrire(`${SHEETS}/${encodeURIComponent(id)}/values/${encodeURIComponent(`'${ONGLET}'!A:${fin}`)}:append?valueInputOption=RAW&insertDataOption=INSERT_ROWS`,
                envoyerJson('POST', { values: [ligne] }));
              lignes.push(ligne);
            }
          } else if (op.type === 'etat' && rang > 0) {
            const avant = String(lignes[rang][col.remarque] || '');
            const apres = avant.includes(op.texte) ? avant : (avant ? `${avant} ; ${op.texte}` : op.texte);
            if (apres !== avant) {
              await ecrire(`${SHEETS}/${encodeURIComponent(id)}/values/${encodeURIComponent(`'${ONGLET}'!${L}${rang + 1}`)}?valueInputOption=RAW`, envoyerJson('PUT', { values: [[apres]] }));
              lignes[rang][col.remarque] = apres;
            }
          } else if (op.type === 'etat' && tampon().slice(1).some(o => o.type === 'ajout' && o.id === op.id) && !op.repousse) {
            // La ligne n'est pas encore écrite (son ajout attend plus loin) : l'état passe après elle (une seule fois).
            stockageDe().setItem(CLE_TAMPON, JSON.stringify([...tampon().slice(1), { ...op, repousse: true }]));
            continue;
          } // ligne introuvable pour un état (effacée à la main) : rien à marquer, on passe
          stockageDe().setItem(CLE_TAMPON, JSON.stringify(tampon().slice(1))); // retiré SEULEMENT après le « c'est écrit »
          envoyees++;
        }
        return { envoyees, attente: 0, id };
      } catch (erreur) {
        return { envoyees, attente: tampon().length, erreur: erreur && erreur.message ? erreur.message : String(erreur) };
      }
    }
    let envoi = null;
    function envoyer() { if (!envoi) envoi = vider().finally(() => { envoi = null; }); return envoi; }

    // La copie du tableur sur le téléphone (reconnaître sans réseau) : phrase, code, commande, identifiant, et si la ligne
    // est écartée (« retirée » / « remplacée ») ou « choisie par Max ».
    async function lireEtGarder() {
      if (!connecte()) return { lu: false, raison: 'pas_connecte' };
      const { id } = await trouverOuCreer();
      if (!id) return { lu: false, raison: 'pas_connecte' };
      const lignes = await lignesDuTableur(id);
      const col = colonnesDe((lignes[0] || []).map(String));
      const copie = lignes.slice(1).map(l => {
        const remarque = String(l[col.remarque] || '');
        return { phrase: String(l[col.formulation] || ''), code: String(l[col.code] || '').trim(), commande: String(l[col.commande] || ''),
          id: identifiantDe(remarque), ecartee: /(retir|remplac)[ée]e? le /i.test(remarque), choisie: /choisie par Max le /i.test(remarque) };
      }).filter(x => x.phrase.trim());
      stockageDe().setItem(CLE_COPIE, JSON.stringify({ lu_le: new Date(maintenant()).toISOString(), lignes: copie }));
      return { lu: true, nombre: copie.length };
    }
    function copie() { const c = lireJson(CLE_COPIE, null); return c && Array.isArray(c.lignes) ? c.lignes : []; }

    // 09/11/2026 (séance 2) : + tampon, écriture, copie (même façon de faire que le petit tableur).
    return { trouverOuCreer, adresse, titresDuModele, tampon, enAttente: () => tampon().length, noterAjout, noterReprise, noterEtat,
      noterRetrait, noterRemplacement, noterChoix, envoyer, lireEtGarder, copie };
  }

  const defaut = creer();
  return { NOM, ONGLET, MODELE, MARQUE, CLE_ID, CLE_TAMPON, CLE_COPIE, BLOC, creer, ...defaut }; // 09/11/2026 : + CLE_TAMPON, CLE_COPIE, BLOC
})();
