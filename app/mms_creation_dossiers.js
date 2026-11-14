'use strict';

// 13/11/2026 (accord de Max, P5 = M3e, TEMPS 2) : CRÉATION des dossiers VIDES par expéditeur, dans le Drive du COMPTE CAP.
// - SEULEMENT après la fenêtre « Oui, créer » de Max, qui montre la liste EN NOMBRES (mms_ecran.js) ; « montre » = ce plan-là.
// - Garde avant tout (mmsDossiers.verifierPlan) : jamais deux fois la même clé ni le même nom, jamais hors de « MMS des
//   relations », jamais plus de dossiers que la liste montrée, jamais un numéro dans un nom.
// - Cap RELIT le Drive au début (racine, dossiers marqués) ET avant CHAQUE dossier (sa marque, corbeille comprise) : ce qui
//   existe n'est jamais recréé ; un dossier mis à la corbeille par Max n'est pas recréé non plus.
// - Chaque dossier porte sa marque (clé : empreinte, jamais le numéro) et sa date ; « MMS des relations » est marqué et daté.
// - UN dossier à la fois (verrou). À la PREMIÈRE erreur : arrêt net (rien d'autre n'est tenté). « Arrêter » (arreter())
//   arrête avant le dossier suivant. Une coupure se reprend sans doublon (les marques).
// - Dossiers VIDES seulement : ni « Reçus », ni « Envoyés », ni « Dialogue » ; AUCUN message copié, AUCUN fichier envoyé.
//   Rien n'est effacé, renommé, déplacé. L'ancien rangement « r_ » n'est pas touché (aucune recherche, aucune écriture).
const mmsCreationDossiers = (() => {
  const DRIVE = 'https://www.googleapis.com/drive/v3/files';
  const DOSSIER = 'application/vnd.google-apps.folder';
  const MARQUE_DATE = 'cap_mms_cree_le';
  const jour = d => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  let enCours = false;

  // Tous les dossiers portant cette marque, corbeille COMPRISE (lecture seule).
  async function parMarque(compte, cle, valeur) {
    if (!/^[a-z0-9_:-]+$/.test(String(valeur))) throw new Error('Marque illisible : arrêt, rien d’autre n’est créé.');
    const q = `appProperties has { key='${cle}' and value='${valeur}' } and mimeType='${DOSSIER}'`;
    const params = new URLSearchParams({ q, fields: 'files(id,trashed)', pageSize: '10', spaces: 'drive' });
    const corps = await (await compte.appeler(`${DRIVE}?${params}`)).json();
    return Array.isArray(corps.files) ? corps.files : [];
  }

  async function creerUn(compte, nom, parent, marques) {
    const reponse = await compte.appelerEcriture(`${DRIVE}?fields=id`, { method: 'POST', body: JSON.stringify({ name: nom, mimeType: DOSSIER, parents: [parent], appProperties: marques }) });
    const r = await reponse.json();
    if (!r || !r.id) throw new Error('Google n’a pas rendu le dossier créé.');
    return r.id;
  }

  // plan : celui montré dans « Oui, créer » ; montre : le même (sa copie), qui fixe la limite.
  // Rend { crees, dejaLa, corbeille, arrete, erreur, faits } (faits = créations tentées et réussies, racine comprise).
  async function creer(compte, plan, montre, { arreter = () => false, progres = () => {}, maintenant = () => new Date() } = {}) {
    if (enCours) throw new Error('Une création est déjà en cours : attends qu’elle finisse.');
    enCours = true;
    const rapport = { crees: 0, dejaLa: 0, corbeille: 0, arrete: false, erreur: null, faits: 0 };
    try {
      mmsDossiers.verifierPlan(plan, montre);
      const limite = montre.total;
      const date = jour(maintenant());
      const etat = await mmsDossiers.lireEtat(compte);
      if (etat.existants.length && plan.existants === 0) throw new Error('Des dossiers marqués existent, mais aucun ne correspond à la liste : la clé du téléphone a peut-être changé. Arrêt, rien n’est créé.');
      const compter = () => { if (rapport.faits + 1 > limite) throw new Error('Plus de dossiers que la liste montrée : arrêt.'); };
      let racine = etat.racineId;
      if (!racine) {
        if (arreter()) { rapport.arrete = true; return rapport; }
        compter();
        racine = await creerUn(compte, mmsDossiers.NOM_RACINE, 'root', { [mmsDossiers.MARQUES.racine]: '1', [MARQUE_DATE]: date });
        rapport.faits++; rapport.crees++; progres({ ...rapport });
      }
      if (plan.aTrier && plan.aTrier.creer && !etat.aTrierExiste) {
        if (arreter()) { rapport.arrete = true; return rapport; }
        if (!(await parMarque(compte, mmsDossiers.MARQUES.dossier, 'a_trier')).length) {
          compter();
          await creerUn(compte, mmsDossiers.NOM_A_TRIER, racine, { [mmsDossiers.MARQUES.dossier]: 'a_trier', [MARQUE_DATE]: date });
          rapport.faits++; rapport.crees++; progres({ ...rapport });
        }
      }
      for (const d of plan.dossiers) {
        if (arreter()) { rapport.arrete = true; break; }
        if (d.parent !== 'racine' || mmsDossiers.contientNumero(d.nom)) throw new Error('Dossier refusé par la garde : arrêt.');
        const deja = await parMarque(compte, mmsDossiers.MARQUES.dossier, d.cle); // relu juste avant
        if (deja.length) { if (deja.every(f => f && f.trashed === true)) rapport.corbeille++; else rapport.dejaLa++; continue; }
        compter();
        await creerUn(compte, d.nom, racine, { [mmsDossiers.MARQUES.dossier]: d.cle, [MARQUE_DATE]: date });
        rapport.faits++; rapport.crees++; progres({ ...rapport });
      }
    } catch (erreur) {
      rapport.erreur = String(erreur && erreur.message || 'raison inconnue').slice(0, 200); // arrêt NET : rien d'autre n'est tenté
    } finally { enCours = false; }
    return rapport;
  }

  return Object.freeze({ MARQUE_DATE, creer, enCours: () => enCours });
})();
