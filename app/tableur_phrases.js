'use strict';

// 09/11/2026 (accord de Max, étude « petit tableur ») : le PETIT TABLEUR « Phrases apprises », dans le Drive de Max.
// - Cap le crée lui-même (à la racine du Drive ; Max le range lui-même dans « Cerveau de Cap »), avec le droit drive.file
//   déjà accordé : aucune nouvelle autorisation Google.
// - Cap le retrouve par une MARQUE INVISIBLE posée sur le fichier (appProperties cap_role = phrases_apprises), comme
//   l'agenda : si Max le renomme ou le déplace, Cap le retrouve quand même.
// - Chaque phrase rangée sur le téléphone part d'abord dans un TAMPON (localStorage) ; le tampon se vide une opération
//   à la fois, seulement quand Google a dit « c'est écrit ». Pas de réseau, connexion expirée : la phrase attend, jamais
//   perdue.
// - RIEN N'EST JAMAIS EFFACÉ : « Retirer » écrit « retirée le … » dans la colonne « État » ; une commande remplacée :
//   « remplacée le … ». Aucun appel de suppression, aucun effacement de cellules.
// - Le tableur principal « Commandes vocales » n'est JAMAIS touché ici (lecture seule, ailleurs). Rien ne va à l'IA.
const tableurPhrases = (() => {
  const NOM = 'Phrases apprises';
  const ONGLET = 'Phrases';
  const ENTETES = ['Phrase', 'Code', 'Commande', 'Date', 'Origine', 'État', 'Identifiant'];
  const MARQUE = { cle: 'cap_role', valeur: 'phrases_apprises' };
  const CLE_ID = 'cap_phrases_tableur_id_v1';
  const CLE_MARQUE_POSEE = 'cap_phrases_tableur_marque_v1';
  const CLE_TAMPON = 'cap_phrases_tampon_v1';
  const CLE_COPIE = 'cap_phrases_apprises_copie_v1';
  const DRIVE = 'https://www.googleapis.com/drive/v3/files';
  const SHEETS = 'https://sheets.googleapis.com/v4/spreadsheets';
  const ID_VALIDE = /^[A-Za-z0-9_-]{10,200}$/;

  function dateCourte(maintenant) { return new Date(maintenant).toLocaleDateString('fr-FR'); }
  function plage(cellules) { return encodeURIComponent(`'${ONGLET}'!${cellules}`); }

  // dependances : { appeler(url, options) → Response, stockage, connecte() → bool, maintenant() → ms }
  function creer(dependances = {}) {
    const appeler = dependances.appeler || ((url, options) => googleConnexion.appeler(url, options));
    const stockageDe = () => dependances.stockage || localStorage; // lu au moment voulu (pas au chargement)
    const stockage = { getItem: cle => stockageDe().getItem(cle), setItem: (cle, valeur) => stockageDe().setItem(cle, valeur) };
    const connecte = dependances.connecte || (() => typeof googleConnexion !== 'undefined' && googleConnexion.connecte());
    const maintenant = dependances.maintenant || (() => Date.now());
    let envoi = null;

    function lireJson(cle, defaut) { try { const v = JSON.parse(stockage.getItem(cle)); return v === null ? defaut : v; } catch (e) { return defaut; } }
    function ecrireJson(cle, valeur) { stockage.setItem(cle, JSON.stringify(valeur)); }
    async function json(url, options) { return (await appeler(url, options)).json(); }
    const envoyerJson = (methode, corps) => ({ method: methode, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(corps) });

    // ----- Le tampon (sur le téléphone) -----
    function tampon() { const t = lireJson(CLE_TAMPON, []); return Array.isArray(t) ? t : []; }
    function mettreEnAttente(operation) {
      const t = tampon();
      t.push(operation);
      ecrireJson(CLE_TAMPON, t); // si la mémoire est pleine, l'erreur remonte : Max est prévenu, rien n'est caché
      return t.length;
    }
    // Une phrase rangée (statut « ajoutee » de phrasesApprendre) : une ligne à ajouter.
    function noterAjout(entree, { etat = '' } = {}) {
      const quand = entree.quand ? new Date(entree.quand) : new Date(maintenant());
      return mettreEnAttente({ type: 'ajout', id: entree.id, ligne: [entree.phrase, entree.code || '', entree.commande || '',
        Number.isNaN(quand.getTime()) ? '' : quand.toLocaleDateString('fr-FR'), entree.origine || '', etat, entree.id] });
    }
    // « Retirer », commande remplacée, « déjà dans le principal » : on écrit l'état, on n'efface rien.
    function noterEtat(id, etat) { return mettreEnAttente({ type: 'etat', id, etat }); }
    function noterRetrait(id) { return noterEtat(id, `retirée le ${dateCourte(maintenant())}`); }
    function noterRemplacement(id) { return noterEtat(id, `remplacée le ${dateCourte(maintenant())}`); }

    // ----- Retrouver ou créer le petit tableur -----
    async function encorePresent(id) {
      try {
        const f = await json(`${DRIVE}/${encodeURIComponent(id)}?fields=id,trashed`);
        return Boolean(f && f.id && !f.trashed);
      } catch (erreur) {
        if (erreur.statut === 404) return false;
        throw erreur;
      }
    }
    async function chercherParMarque() {
      const q = `appProperties has { key='${MARQUE.cle}' and value='${MARQUE.valeur}' } and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false`;
      const trouves = await json(`${DRIVE}?${new URLSearchParams({ q, fields: 'files(id)', pageSize: '10' })}`);
      const f = (trouves.files || []).find(x => ID_VALIDE.test(x.id || ''));
      return f ? f.id : '';
    }
    async function poserMarque(id) {
      await appeler(`${DRIVE}/${encodeURIComponent(id)}?fields=id`, envoyerJson('PATCH', { appProperties: { [MARQUE.cle]: MARQUE.valeur } }));
      stockage.setItem(CLE_MARQUE_POSEE, id);
    }
    async function creerTableur() {
      const r = await json(SHEETS, envoyerJson('POST', {
        properties: { title: NOM },
        sheets: [{ properties: { sheetId: 0, title: ONGLET, gridProperties: { frozenRowCount: 1 } } }]
      }));
      if (!ID_VALIDE.test(r.spreadsheetId || '')) throw new Error('Google n’a pas rendu le petit tableur.');
      stockage.setItem(CLE_ID, r.spreadsheetId); // gardé tout de suite : jamais un deuxième tableur
      await appeler(`${SHEETS}/${encodeURIComponent(r.spreadsheetId)}/values/${plage('A1:G1')}?valueInputOption=RAW`,
        envoyerJson('PUT', { values: [ENTETES] }));
      await poserMarque(r.spreadsheetId);
      return r.spreadsheetId;
    }
    async function trouverOuCreer() {
      const garde = stockage.getItem(CLE_ID) || '';
      if (ID_VALIDE.test(garde) && await encorePresent(garde)) {
        if (stockage.getItem(CLE_MARQUE_POSEE) !== garde) await poserMarque(garde); // marque pas encore posée (coupure)
        return { id: garde, cree: false };
      }
      const marque = await chercherParMarque();
      if (marque) {
        stockage.setItem(CLE_ID, marque);
        stockage.setItem(CLE_MARQUE_POSEE, marque);
        return { id: marque, cree: false };
      }
      return { id: await creerTableur(), cree: true };
    }

    // ----- Vider le tampon (une opération à la fois ; on s'arrête à la première erreur) -----
    async function identifiants(id) {
      const r = await json(`${SHEETS}/${encodeURIComponent(id)}/values/${plage('G:G')}`);
      return (r.values || []).map(l => String((l && l[0]) || ''));
    }
    async function vider() {
      if (!tampon().length) return { envoyees: 0, attente: 0 };
      if (!connecte()) return { envoyees: 0, attente: tampon().length, raison: 'pas_connecte' };
      let envoyees = 0;
      try {
        const { id } = await trouverOuCreer();
        let ids = await identifiants(id);
        while (tampon().length) {
          const op = tampon()[0];
          if (op.type === 'ajout') {
            // Déjà écrite (réponse de Google perdue la dernière fois) : on ne la double pas.
            if (!ids.includes(op.id)) {
              await appeler(`${SHEETS}/${encodeURIComponent(id)}/values/${plage('A:G')}:append?valueInputOption=RAW&insertDataOption=INSERT_ROWS`,
                envoyerJson('POST', { values: [op.ligne] }));
              ids = await identifiants(id);
            }
          } else if (op.type === 'etat') {
            const rang = ids.indexOf(op.id);
            if (rang > 0) { // rang 0 = la ligne des titres
              await appeler(`${SHEETS}/${encodeURIComponent(id)}/values/${plage(`F${rang + 1}`)}?valueInputOption=RAW`,
                envoyerJson('PUT', { values: [[op.etat]] }));
            }
            // Ligne introuvable (Max l'a déplacée ou effacée lui-même) : rien à marquer, on passe.
          }
          ecrireJson(CLE_TAMPON, tampon().slice(1)); // retirée du tampon SEULEMENT après le « c'est écrit » de Google
          envoyees++;
        }
        return { envoyees, attente: 0, id };
      } catch (erreur) {
        return { envoyees, attente: tampon().length, erreur: erreur && erreur.message ? erreur.message : String(erreur) };
      }
    }
    function envoyer() {
      if (!envoi) envoi = vider().finally(() => { envoi = null; });
      return envoi;
    }

    // ----- Étape 2 : lire le petit tableur et garder une copie sur le téléphone (reconnaissance sans réseau) -----
    async function lireEtGarder() {
      if (!connecte()) return { lu: false, raison: 'pas_connecte' };
      const { id } = await trouverOuCreer();
      const r = await json(`${SHEETS}/${encodeURIComponent(id)}/values/${plage('A2:G')}`);
      const lignes = (r.values || []).map(l => ({ phrase: String(l[0] || ''), code: String(l[1] || ''), commande: String(l[2] || ''),
        etat: String(l[5] || ''), id: String(l[6] || '') })).filter(l => l.phrase.trim());
      ecrireJson(CLE_COPIE, { lu_le: new Date(maintenant()).toISOString(), lignes });
      return { lu: true, nombre: lignes.length };
    }
    function copie() { const c = lireJson(CLE_COPIE, null); return c && Array.isArray(c.lignes) ? c.lignes : []; }
    // 09/11/2026 (séance 2, reprise) : relit « Phrases apprises » SANS RIEN Y TOUCHER (ni création, ni marque) : seulement
    // si Cap connaît déjà son identifiant. Le petit tableur reste intact (décision de Max).
    async function lireSansToucher() {
      const id = stockage.getItem(CLE_ID) || '';
      if (!connecte() || !ID_VALIDE.test(id)) return { lu: false };
      const r = await json(`${SHEETS}/${encodeURIComponent(id)}/values/${plage('A2:G')}`);
      const lignes = (r.values || []).map(l => ({ phrase: String(l[0] || ''), code: String(l[1] || ''), commande: String(l[2] || ''),
        etat: String(l[5] || ''), id: String(l[6] || '') })).filter(l => l.phrase.trim());
      ecrireJson(CLE_COPIE, { lu_le: new Date(maintenant()).toISOString(), lignes });
      return { lu: true, nombre: lignes.length };
    }

    function adresse() {
      const id = stockage.getItem(CLE_ID) || '';
      return ID_VALIDE.test(id) ? `https://docs.google.com/spreadsheets/d/${encodeURIComponent(id)}/edit` : '';
    }

    return { tampon, enAttente: () => tampon().length, noterAjout, noterEtat, noterRetrait, noterRemplacement,
      trouverOuCreer, envoyer, lireEtGarder, lireSansToucher, copie, adresse }; // 09/11/2026 : + lireSansToucher
  }

  const defaut = creer();
  return { NOM, ONGLET, ENTETES, MARQUE, CLE_ID, CLE_TAMPON, CLE_COPIE, creer, ...defaut };
})();
