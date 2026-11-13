'use strict';

// 12/11/2026 (accord écrit de Max, marche M3b) : CLASSEMENT des MMS lus (mms_lecture.js) : à quelle personne, ou « À trier ».
// - Les personnes : celles qui ont un dossier « r_… » et une fiche trouvée dans la copie des coordonnées (c154, sur le
//   téléphone) ; leurs numéros sont pris dans les cases « Téléphone », « Deuxième téléphone », « Portable », « Coordonnées »…
// - L'index est fait en MÉMOIRE, à chaque fois, avec la clé du téléphone (index_relations.js, M1) : rien n'est gardé, aucun
//   numéro n'est rendu ni écrit. Les messages n'ont qu'une empreinte.
// - Règles : groupe (plusieurs destinataires) → « À trier » ; numéro masqué ou inconnu → « À trier » ; numéro de deux
//   personnes → « À trier » (Cap ne choisit pas) ; sinon : la personne.
// - Le résumé ne contient que des NOMBRES. Rien n'est copié, rien n'est envoyé (ni Drive, ni IA). Sans DOM.
const mmsRangement = (() => {
  const titreNumero = titre => {
    const t = String(titre || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
    return /telephone|portable|mobile|coordonnee|\btel\b/.test(t);
  };
  // Les morceaux qui ressemblent à un numéro dans une case (une case « Coordonnées » peut aussi avoir une adresse, un mail).
  function numerosDans(texte) {
    const morceaux = String(texte || '').match(/(?:\+|00)?\d[\d .()-]{6,}\d/g) || [];
    return morceaux.filter(m => typeof numeros !== 'undefined' && numeros.normaliserNumero(m));
  }

  // copie : coordonneesRelations.lire(…). Rend [{ identifiant (nom du dossier r_…), numeros }] (en mémoire seulement).
  function personnesDepuisCopie(copie) {
    const liste = [];
    for (const p of copie && Array.isArray(copie.personnes) ? copie.personnes : []) {
      if (!p || p.etat !== 'trouve' || !Array.isArray(p.champs)) continue;
      const nums = [];
      for (const champ of p.champs) if (champ && titreNumero(champ.titre)) nums.push(...numerosDans(champ.valeur));
      if (nums.length) liste.push({ identifiant: p.nomDossier, numeros: nums });
    }
    return liste;
  }

  // c177 : l'état des dossiers « r_ » de la copie, en NOMBRES : total, fiche avec numéro, fiche sans numéro, deux fiches au
  // même nom, fiche introuvable (total = la somme des quatre).
  function compterDossiers(copie) {
    const liste = copie && Array.isArray(copie.personnes) ? copie.personnes : [];
    const avecNumero = personnesDepuisCopie(copie).length;
    const trouvees = liste.filter(p => p && p.etat === 'trouve').length;
    const homonymes = liste.filter(p => p && p.etat === 'homonymes').length;
    return { total: liste.length, avecNumero, sansNumero: trouvees - avecNumero, homonymes, introuvable: liste.length - trouvees - homonymes };
  }

  // Lit la copie du téléphone et fait l'index en mémoire. Rend { cle, index, personnes (nombre), dossiers (nombres, c177) }.
  async function preparerIndex(stockage) {
    const cle = indexRelations.cleDuTelephone(stockage);
    if (!cle) throw new Error('La mémoire du téléphone ne répond pas : rien n’a été lu.');
    const copie = coordonneesRelations.lire(stockage);
    const personnes = personnesDepuisCopie(copie);
    const index = await indexRelations.construireIndex(personnes, cle);
    return { cle, index, personnes: personnes.length, dossiers: compterDossiers(copie) };
  }

  // messages : [{ id, date, image, video, texte, groupe, empreinte }]. Rend les mêmes, avec « destination ».
  function classer(messages, index) {
    const table = index && index.empreintes ? index.empreintes : {};
    return (Array.isArray(messages) ? messages : []).map(m => {
      let destination;
      const liste = m && m.empreinte && Object.prototype.hasOwnProperty.call(table, m.empreinte) ? table[m.empreinte] : null;
      if (m && m.groupe) destination = { type: 'a_trier', raison: 'groupe' };
      else if (!Array.isArray(liste) || !liste.length) destination = { type: 'a_trier', raison: 'inconnu' };
      else if (liste.length > 1) destination = { type: 'a_trier', raison: 'plusieurs' };
      else destination = { type: 'personne', identifiant: liste[0] };
      // c177 : l'expéditeur lui-même (même pour un message de groupe) : une fiche, deux fiches, ou aucune.
      const expediteur = !Array.isArray(liste) || !liste.length ? 'inconnu' : (liste.length > 1 ? 'plusieurs' : 'reconnu');
      return { ...m, destination, expediteur };
    });
  }

  // Des NOMBRES seulement. c176 : + ce qui explique le classement (expéditeur lisible ou non, un ou plusieurs destinataires,
  // expéditeurs différents, personnes avec un numéro dans la copie).
  // c177 : + dossiers (compterDossiers) et expéditeurs DIFFÉRENTS reconnus / inconnus / numéro de deux fiches.
  function resumer(classes, dossiers = null) {
    const c = Array.isArray(classes) ? classes : [];
    const versPersonne = c.filter(m => m.destination && m.destination.type === 'personne');
    const raison = r => c.filter(m => m.destination && m.destination.raison === r).length;
    const distincts = etat => new Set(c.filter(m => m.empreinte && m.expediteur === etat).map(m => m.empreinte)).size;
    return {
      total: c.length, versPersonne: versPersonne.length,
      personnes: new Set(versPersonne.map(m => m.destination.identifiant)).size,
      aTrier: c.length - versPersonne.length, inconnu: raison('inconnu'), groupe: raison('groupe'), plusieurs: raison('plusieurs'),
      sansExpediteur: c.filter(m => !m.empreinte).length,
      unDestinataire: c.filter(m => !m.groupe).length, plusieursDestinataires: c.filter(m => m.groupe).length,
      expediteurs: new Set(c.filter(m => m.empreinte).map(m => m.empreinte)).size,
      expediteursReconnus: distincts('reconnu'), expediteursInconnus: distincts('inconnu'), expediteursPartages: distincts('plusieurs'),
      dossiers: dossiers && typeof dossiers === 'object' ? { ...dossiers } : null
    };
  }

  const pluriel = (n, un, plusieurs) => `${n} ${n > 1 ? plusieurs : un}`;
  function texte(r) {
    if (!r || !r.total) return 'Aucun MMS reçu trouvé sur le téléphone.';
    let t = `${pluriel(r.total, 'MMS lu', 'MMS lus')} : ${r.versPersonne} d’une personne qui a un dossier « r_ » (${pluriel(r.personnes, 'personne', 'personnes')}), ${r.aTrier} à trier`;
    const details = [];
    if (r.inconnu) details.push(pluriel(r.inconnu, 'numéro inconnu ou masqué', 'numéros inconnus ou masqués'));
    if (r.groupe) details.push(pluriel(r.groupe, 'message de groupe', 'messages de groupe'));
    if (r.plusieurs) details.push(pluriel(r.plusieurs, 'numéro partagé par deux personnes', 'numéros partagés par deux personnes'));
    if (details.length) t += ` (${details.join(', ')})`;
    // c176 : l'explication, en nombres. c177 : + les deux lignes demandées par Max (dossiers « r_ », expéditeurs).
    const e = `Détail : ${r.sansExpediteur} sans numéro d’expéditeur lisible, ${r.unDestinataire} avec un seul destinataire, ${r.plusieursDestinataires} avec plusieurs destinataires.`;
    const lignes = [`${t}.`, e];
    const d = r.dossiers;
    if (d) lignes.push(`Dossiers r_ : ${d.total} au total ; fiche avec numéro : ${d.avecNumero} ; fiche sans numéro : ${d.sansNumero} ; deux fiches au même nom : ${d.homonymes} ; fiche introuvable : ${d.introuvable}.`);
    let x = `Expéditeurs différents : ${r.expediteurs}, dont reconnus : ${r.expediteursReconnus}, inconnus : ${r.expediteursInconnus}`;
    if (r.expediteursPartages) x += `, numéro de deux fiches : ${r.expediteursPartages}`;
    lignes.push(`${x}.`, 'Rien n’a été copié ni envoyé.');
    return lignes.join('\n');
  }

  return Object.freeze({ numerosDans, personnesDepuisCopie, compterDossiers, preparerIndex, classer, resumer, texte });
})();
