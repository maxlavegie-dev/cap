'use strict';

// Dossiers « Relations » (06/11/2026), ÉTAPE 2 : calcul de la liste, en LECTURE SEULE.
// Décision de Max : un dossier « Relations » à la racine de « App Cap » ; pour chaque personne de
// l'onglet « Dictionnaire » du Dictionnaire général, un dossier « r_Prénom Nom » (avec, plus tard,
// « Journal de bord », « Reçus », « Envoyés »). À cette étape, RIEN n'est créé : Cap compte seulement
// qui aurait un dossier, les homonymes, les fiches incomplètes, et l'écran ne montre QUE des nombres.
// Seules les colonnes Prénom, Nom et Type sont lues (jamais les notes ni les coordonnées), en mémoire ;
// l'IA ne voit rien de ce module. Cap ne supprime jamais rien.
const relations = (() => {
  const PREFIXE = 'r_';

  function cle(texte) {
    return String(texte || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/\s+/g, ' ').trim();
  }
  function propre(texte) {
    return String(texte || '').replace(/\s+/g, ' ').trim();
  }
  function colonne(entetes, nom) {
    return entetes.findIndex(e => cle(e).replace(/[^a-z ]/g, '').trim() === nom);
  }
  // Les SEULES colonnes demandées au Drive pour ce calcul : Prénom, Nom, Type (numéros, 0 = A).
  const COLONNES = Object.freeze(['prenom', 'nom', 'type']);
  function colonnesALire(entetes) {
    return COLONNES.map(nom => colonne(entetes || [], nom)).filter(i => i >= 0).sort((a, b) => a - b);
  }

  // valeurs : lignes de l'onglet « Dictionnaire » (1re ligne = en-têtes), colonnes Prénom, Nom, Type
  // au moins. Retour : { lues, aCreer: [{ numero, nomDossier, cle }], homonymes: [[numero…]],
  //   incompletes: [numero…], typeAbsent: [numero…], autres: nombre (organismes, lieux…) }.
  function calculer(valeurs) {
    const [entetes = [], ...lignes] = valeurs || [];
    const iPrenom = colonne(entetes, 'prenom');
    const iNom = colonne(entetes, 'nom');
    const iType = colonne(entetes, 'type');
    const resultat = { lues: 0, aCreer: [], homonymes: [], incompletes: [], typeAbsent: [], autres: 0 };
    const parCle = new Map();
    lignes.forEach((ligne, i) => {
      const numero = i + 2;
      const prenom = propre(iPrenom >= 0 ? ligne[iPrenom] : '');
      const nom = propre(iNom >= 0 ? ligne[iNom] : '');
      const type = cle(iType >= 0 ? ligne[iType] : '');
      if (!prenom && !nom && !type) return; // ligne vide
      resultat.lues++;
      if (type && !type.startsWith('personne')) { resultat.autres++; return; }
      if (!prenom || !nom) { resultat.incompletes.push(numero); return; }
      if (!type) { resultat.typeAbsent.push(numero); return; } // à vérifier par Max : rien de prévu
      const c = cle(`${prenom} ${nom}`);
      if (!parCle.has(c)) parCle.set(c, []);
      parCle.get(c).push({ numero, nomDossier: `${PREFIXE}${prenom} ${nom}`, cle: c });
    });
    for (const groupe of parCle.values()) {
      if (groupe.length > 1) resultat.homonymes.push(groupe.map(g => g.numero));
      else resultat.aCreer.push(groupe[0]);
    }
    return resultat;
  }

  // Résumé pour l'écran : des NOMBRES seulement, jamais un nom.
  function resumer(r) {
    const fichesHomonymes = r.homonymes.reduce((total, g) => total + g.length, 0);
    return [
      `Relations, calcul seulement (rien n’est créé) : ${r.lues} fiche(s) lue(s) dans l’onglet « Dictionnaire ».`,
      `Dossiers « r_ » à prévoir : ${r.aCreer.length}.`,
      `Homonymes à départager : ${r.homonymes.length} nom(s), ${fichesHomonymes} fiche(s) (aucun dossier prévu pour elles).`,
      `Fiches incomplètes (prénom ou nom manquant) : ${r.incompletes.length}.`,
      `Fiches sans type, à vérifier : ${r.typeAbsent.length}.`,
      `Fiches qui ne sont pas des personnes (organismes, lieux…) : ${r.autres}.`
    ].join('\n');
  }

  // Bouton de « Réglages du Drive ». source.lireDictionnairePersonnes() : lecture seule, en mémoire.
  function brancher(doc, source) {
    const bouton = doc.getElementById('calculer-relations');
    const zone = doc.getElementById('resume-relations');
    if (!bouton || !zone) return;
    bouton.addEventListener('click', async () => {
      zone.hidden = false;
      zone.textContent = 'Lecture de l’onglet « Dictionnaire »…';
      try {
        const valeurs = await source.lireDictionnairePersonnes();
        zone.textContent = valeurs ? resumer(calculer(valeurs))
          : 'Choisis d’abord le Dictionnaire général dans « Réglages du Drive », avec Cap ouvert dans Chrome.';
      } catch (erreur) {
        zone.textContent = `Le Dictionnaire n’a pas pu être lu (${String(erreur && erreur.message || 'raison inconnue').slice(0, 120)}). Rien n’a été créé.`;
      }
    });
  }

  return { PREFIXE, ONGLET: 'Dictionnaire', colonnesALire, calculer, resumer, brancher };
})();

if (typeof document !== 'undefined' && document.getElementById('calculer-relations')
  && !(typeof window !== 'undefined' && window.CAP_TESTS) && typeof classement !== 'undefined') {
  relations.brancher(document, classement);
}
