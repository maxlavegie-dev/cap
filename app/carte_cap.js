'use strict';

// 12/11/2026 (accord de Max, c151, marche A2 de la « carte complète ») : LA CARTE d'un nom tapé dans Chercher.
// Vision de Max : quand il tape un nom, Cap ne devine pas ce qu'il veut ; il montre UNE carte avec tout ce qu'il sait.
// Construite pour accepter PLUSIEURS SOURCES : chaque source se déclare avec carteCap.ajouterSource({ nom, trouver, blocs }) ;
//   trouver(textePlie, plier) → [{ cle, titre, sorte, … }] : ce que la source propose dans Chercher ;
//   blocs(entree, plier)      → [{ type: 'lien', texte, href } | { type: 'texte', texte }] : ce qu'elle ajoute à la carte
//                                de cette entrée (une source peut compléter la carte d'une entrée trouvée par une autre,
//                                par la clé : le nom sans accents ni majuscules).
// c162 : « Voir dans Cap » ouvre les photos et PDF du dossier de la relation dans la visionneuse.
// c156 : un « + » en bas à droite montre tout le reste de la fiche (notes, naissance… seulement là).
// c155 : la carte d'une relation montre aussi ses coordonnées (copie du téléphone, c154) : Appeler, Écrire un mail.
// c152 : deuxième source, les chantiers (Dossier, Journal, Documents, Tâches, comme la fiche).
// Première source : les relations (memoire_relations.js, sur le téléphone) : « Ouvrir le dossier », « Ouvrir le
// journal » ou « Pas encore de journal ». Plus tard (décision de Max) : coordonnées du Dictionnaire, échéances, tâches,
// documents (Registre), chantiers liés, agenda : une source de plus = un petit ajout ici, sans toucher au reste.
// Verrous : tout reste sur le téléphone (aucune lecture du Drive ici, aucun envoi, jamais à l'IA) ; liens ouverts HORS de
// Cap (comme « Drive » d'un chantier et les liens des journaux des relations) ; construit avec textContent seulement.
const carteCap = (() => {
  const plier = texte => String(texte || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/\s+/g, ' ').trim();
  const sources = [];
  let stockageParDefaut = () => (typeof localStorage !== 'undefined' ? localStorage : null);

  function ajouterSource(source) {
    if (!source || !source.nom || sources.some(s => s.nom === source.nom)) return false;
    sources.push(source);
    return true;
  }
  function retirerSource(nom) { const i = sources.findIndex(s => s.nom === nom); if (i < 0) return false; sources.splice(i, 1); return true; }
  // Tout ce que les sources proposent pour le texte tapé (une source en panne ne bloque pas les autres).
  function trouver(texte) {
    const t = plier(texte);
    if (!t) return [];
    const resultats = [];
    for (const s of sources) {
      let trouves = [];
      try { trouves = s.trouver(t, plier) || []; } catch (erreur) { trouves = []; }
      for (const e of trouves) resultats.push({ ...e, source: s.nom });
    }
    return resultats;
  }
  // Ce que TOUTES les sources savent de cette entrée, dans l'ordre des sources.
  function blocs(entree) {
    const tous = [];
    for (const s of sources) {
      if (typeof s.blocs !== 'function') continue;
      try { tous.push(...(s.blocs(entree, plier) || [])); } catch (erreur) { /* une source en panne : les autres restent */ }
    }
    return tous;
  }

  // ----- Source n° 1 (A2) : les relations gardées sur le téléphone (A1) -----
  const adresseDossier = id => `https://drive.google.com/drive/folders/${encodeURIComponent(id)}`;
  const adresseJournal = id => `https://docs.google.com/document/d/${encodeURIComponent(id)}/edit`;
  const relationsGardees = () => {
    if (typeof memoireRelations === 'undefined') return [];
    const copie = memoireRelations.lire(stockageParDefaut());
    return copie ? copie.relations : [];
  };
  // ----- c155 (A3b) : COORDONNÉES de la personne, tirées de la copie du téléphone (coordonnees_relations.js, c154) -----
  // Par défaut (décision de Max) : nom, téléphone (« Appeler » : le clavier du téléphone s'ouvre avec le numéro, sans appeler
  // tout seul), mail (« Écrire un mail » : la messagerie s'ouvre), adresse postale. Tout le reste (notes, naissance, « Note pour
  // IA »…) n'est JAMAIS montré ici (seulement derrière le « + », A3c). Deux fiches au même nom : pas de coordonnées.
  const enTete = t => plier(t).replace(/[^a-z ]/g, '').trim();
  const valeurDe = (fiche, nom) => { const c = fiche.champs.find(x => enTete(x.titre) === nom); return c ? c.valeur : ''; };
  const numeroAppel = t => {
    const premier = String(t).split(/[,;/|\n]+/).find(x => /\d/.test(x)) || '';
    const n = premier.trim().replace(/[^\d+]/g, '').replace(/(?!^)\+/g, '');
    return n.replace(/\D/g, '').length >= 3 ? n : '';
  };
  const adresseMail = t => (String(t).match(/[^\s,;<>()"']+@[^\s,;<>()"']+\.[^\s,;<>()"']+/) || [''])[0];
  const ficheDe = nomDossier => (typeof coordonneesRelations !== 'undefined' ? coordonneesRelations.pour(stockageParDefaut(), nomDossier) : undefined);
  function blocsCoordonnees(nomDossier) {
    const fiche = ficheDe(nomDossier);
    if (fiche === undefined) return [];
    if (!fiche) return [{ type: 'texte', texte: 'Coordonnées : touche « Tout synchroniser » (ton compte Google personnel connecté).' }];
    if (fiche.etat === 'homonymes') return [{ type: 'texte', texte: `${fiche.nombre} fiches portent ce nom dans le Dictionnaire : pas de coordonnées.` }];
    if (fiche.etat !== 'trouve') return [{ type: 'texte', texte: 'Pas de coordonnées trouvées (le nom du dossier ne correspond plus au Dictionnaire).' }];
    const m = [];
    const nomComplet = [valeurDe(fiche, 'prenom'), valeurDe(fiche, 'nom')].filter(Boolean).join(' ');
    if (nomComplet) m.push({ type: 'texte', texte: nomComplet });
    const tel = valeurDe(fiche, 'telephone');
    if (tel) {
      m.push({ type: 'texte', texte: `Téléphone : ${tel}` });
      if (numeroAppel(tel)) m.push({ type: 'lien', texte: 'Appeler', href: `tel:${numeroAppel(tel)}` });
    }
    const mail = valeurDe(fiche, 'mail');
    if (mail) {
      m.push({ type: 'texte', texte: `Mail : ${mail}` });
      if (adresseMail(mail)) m.push({ type: 'lien', texte: 'Écrire un mail', href: `mailto:${adresseMail(mail)}` });
    }
    const adresse = valeurDe(fiche, 'adresse postale');
    if (adresse) m.push({ type: 'texte', texte: `Adresse : ${adresse}` });
    if (!m.length) m.push({ type: 'texte', texte: 'Pas de téléphone, de mail ni d’adresse dans le Dictionnaire.' });
    return m;
  }
  // c156 (A3c) : TOUT LE RESTE de la fiche (décision de Max), seulement derrière le « + » : chaque case remplie qui n'est pas
  // déjà montrée par défaut (prénom, nom, téléphone, mail, adresse postale), avec le titre de sa colonne ; notes, naissance,
  // « Note pour IA » comprises ; une colonne ajoutée plus tard au Dictionnaire y apparaît seule (aucune liste de colonnes ici).
  const PAR_DEFAUT = ['prenom', 'nom', 'telephone', 'mail', 'adresse postale'];
  function blocPlus(nomDossier) {
    const fiche = ficheDe(nomDossier);
    if (!fiche || fiche.etat !== 'trouve') return [];
    const dejaMontres = new Set();
    const reste = fiche.champs.filter(c => {
      const t = enTete(c.titre);
      if (PAR_DEFAUT.includes(t) && !dejaMontres.has(t)) { dejaMontres.add(t); return false; }
      return true;
    });
    return reste.length ? [{ type: 'plus', champs: reste }] : [];
  }
  // c162 : « Voir dans Cap » : le dossier de la relation dans la visionneuse (lu par visionneuse_cap.js, compte Cap, lecture seule).
  const voirDansCap = r => {
    const v = typeof visionneuseCap !== 'undefined' ? visionneuseCap.instance : null;
    if (v && typeof v.ouvrirDossier === 'function') void v.ouvrirDossier(r.idDossier, r.nom);
  };
  ajouterSource({
    nom: 'relations',
    trouver: (t, p) => relationsGardees().filter(r => p(r.nom).includes(t))
      .sort((a, b) => a.nom.localeCompare(b.nom, 'fr'))
      .map(r => ({ cle: p(r.nom), titre: r.nom, sorte: 'Relation', relation: r })),
    blocs: (entree, p) => {
      const r = entree.relation || relationsGardees().find(x => p(x.nom) === entree.cle);
      if (!r) return [];
      return [
        ...blocsCoordonnees(r.nomDossier), // c155 (A3b)
        { type: 'lien', texte: 'Ouvrir le dossier', href: adresseDossier(r.idDossier) },
        { type: 'action', texte: 'Voir dans Cap', faire: () => voirDansCap(r) }, // c162 : photos et PDF du dossier dans la visionneuse
        r.idJournal ? { type: 'lien', texte: 'Ouvrir le journal', href: adresseJournal(r.idJournal) } : { type: 'texte', texte: 'Pas encore de journal' },
        ...blocPlus(r.nomDossier) // c156 (A3c) : en dernier, en bas à droite
      ];
    }
  });

  // ----- Source n° 2 (c152, C1) : les chantiers de la copie du téléphone (Liste relue par « Tout synchroniser ») -----
  // La carte d'un chantier a les mêmes boutons que sa fiche : « Dossier » (lien hors de Cap, si son identifiant est connu),
  // puis « Journal » et « Documents » (s'il a un dossier) et « Tâches » : ils ouvrent la fiche et y font l'action.
  const chantiersGardes = () => {
    if (typeof chantiers === 'undefined' || typeof chantiers.copie !== 'function') return [];
    const copie = chantiers.copie(stockageParDefaut());
    return copie ? copie.chantiers.filter(c => c && c.id && c.nom) : [];
  };
  const dossiersGardes = () => {
    const st = stockageParDefaut();
    const ids = typeof chantiersDossiers !== 'undefined' && typeof chantiersDossiers.lireIds === 'function' ? chantiersDossiers.lireIds(st) : {};
    let avec = [];
    try { avec = JSON.parse((st && st.getItem('cap_chantiers_avec_dossier')) || '[]'); } catch (erreur) { avec = []; }
    return { ids, avec: new Set(Array.isArray(avec) ? avec.map(String) : []) };
  };
  const ouvrirFiche = (code, action) => () => {
    if (typeof chantiersEcran !== 'undefined' && typeof chantiersEcran.ouvrirFiche === 'function') void chantiersEcran.ouvrirFiche(code, action);
  };
  ajouterSource({
    nom: 'chantiers',
    trouver: (t, p) => chantiersGardes().filter(c => p(c.nom).includes(t))
      .sort((a, b) => a.nom.localeCompare(b.nom, 'fr'))
      .map(c => ({ cle: p(c.nom), titre: c.nom, sorte: 'Chantier', code: c.id })),
    blocs: entree => {
      if (!entree.code) return [];
      const { ids, avec } = dossiersGardes();
      const aUnDossier = Boolean(ids[entree.code]) || avec.has(entree.code);
      const morceaux = [];
      if (ids[entree.code]) morceaux.push({ type: 'lien', texte: 'Dossier', href: adresseDossier(ids[entree.code]) });
      else morceaux.push({ type: 'texte', texte: aUnDossier ? 'Dossier : touche « Tout synchroniser » pour retrouver son lien.' : 'Pas encore de dossier' });
      if (aUnDossier) morceaux.push({ type: 'action', texte: 'Journal', faire: ouvrirFiche(entree.code, 'journal') }, { type: 'action', texte: 'Documents', faire: ouvrirFiche(entree.code, 'documents') });
      morceaux.push({ type: 'action', texte: 'Tâches', faire: ouvrirFiche(entree.code, 'taches') });
      return morceaux;
    }
  });

  // ----- La fenêtre (une par page, branchée à la première ouverture) -----
  const instances = new WeakMap();
  function brancher(doc, { transition = (typeof choixSurEau !== 'undefined' ? choixSurEau : null) } = {}) {
    const fenetre = doc.getElementById('carte-cap');
    const titre = doc.getElementById('titre-carte-cap');
    const zone = doc.getElementById('blocs-carte-cap');
    const fermer = doc.getElementById('fermer-carte-cap');
    if (![fenetre, titre, zone, fermer].every(Boolean)) return null;
    function fermerFenetre() { if (!fenetre.open) return; if (transition) transition.fermer(fenetre); else fenetre.close(); }
    function ouvrir(entree) {
      titre.textContent = entree.titre || '';
      const morceaux = blocs(entree).map(b => {
        if (b.type === 'plus') { // c156 (A3c) : petit « + » en bas à droite ; le reste n'est construit qu'au toucher, retiré au 2e
          const bt = doc.createElement('button');
          bt.type = 'button';
          bt.className = 'choix-grand-affichage plus-carte';
          let reste = null;
          const regler = ouvert => { bt.textContent = ouvert ? '−' : '+'; bt.setAttribute('aria-expanded', String(ouvert)); bt.setAttribute('aria-label', ouvert ? 'Cacher le reste' : 'Tout voir'); };
          regler(false);
          bt.addEventListener('click', () => {
            if (reste) { reste.remove(); reste = null; regler(false); return; }
            reste = doc.createElement('div');
            reste.className = 'reste-carte';
            for (const c of b.champs) {
              const x = doc.createElement('p');
              x.className = 'relations-gros info-carte';
              x.textContent = `${c.titre} : ${c.valeur}`;
              reste.appendChild(x);
            }
            bt.after(reste);
            regler(true);
          });
          return bt;
        }
        if (b.type === 'action') { // c152 : un bouton qui ferme la carte puis fait l'action (ex. ouvrir la fiche d'un chantier)
          const bt = doc.createElement('button');
          bt.type = 'button';
          bt.className = 'choix-grand-affichage';
          bt.textContent = b.texte;
          bt.addEventListener('click', () => { fermerFenetre(); try { b.faire(); } catch (erreur) { /* rien de cassé */ } });
          return bt;
        }
        if (b.type === 'lien') {
          const a = doc.createElement('a');
          a.className = 'choix-grand-affichage';
          if (/^https:/.test(b.href)) { a.target = '_blank'; a.rel = 'noopener'; } // c155 : « tel: » et « mailto: » sans nouvel onglet
          a.href = b.href;
          a.textContent = b.texte;
          return a;
        }
        const x = doc.createElement('p');
        x.className = 'relations-gros info-carte';
        x.textContent = b.texte;
        return x;
      });
      if (!morceaux.length) { const x = doc.createElement('p'); x.className = 'relations-gros info-carte'; x.textContent = 'Je ne sais rien de plus pour l’instant.'; morceaux.push(x); }
      zone.replaceChildren(...morceaux);
      if (!fenetre.open) { if (transition) transition.ouvrir(fenetre); else fenetre.showModal(); }
    }
    fermer.addEventListener('click', () => fermerFenetre());
    return { ouvrir, fermer: fermerFenetre };
  }
  // origine : le bouton touché (sa page) ; sinon la page de Cap.
  function ouvrir(entree, origine) {
    const doc = (origine && origine.ownerDocument) || (typeof document !== 'undefined' ? document : null);
    if (!doc || !entree) return false;
    if (!instances.has(doc)) instances.set(doc, brancher(doc));
    const inst = instances.get(doc);
    if (!inst) return false;
    inst.ouvrir(entree);
    return true;
  }
  // Pour les tests : lire une autre mémoire que celle du téléphone.
  function reglerStockage(f) { stockageParDefaut = typeof f === 'function' ? f : stockageParDefaut; }

  return { plier, ajouterSource, retirerSource, trouver, blocs, ouvrir, brancher, reglerStockage, sources: () => sources.map(s => s.nom) };
})();
