'use strict';

// La frontière entre le cerveau et Cap : le cerveau (quel que soit le modèle d'IA) ne touche jamais
// aux tâches lui-même. Il demande une action de ce catalogue, et c'est ici que tout est vérifié.
// Les actions marquées « confirmation » ne sont jamais exécutées tout de suite : Cap formule une proposition,
// la dit à Max, et n'agit qu'après son « oui ».
const actionsCap = (() => {
  const CATALOGUE = [{
    nom: 'ajouter_tache',
    description: 'Ordre clair de Max : ajoute une seule tâche avec ses mots, dans une catégorie et une sous-catégorie qui existent déjà.',
    parametres: {
      intitule: 'le texte de la tâche, avec les mots de Max',
      categorie: 'une catégorie existante, ou vide pour À trier',
      sous_categorie: 'une sous-catégorie existante de cette catégorie, « À classer », ou vide pour laisser Cap choisir',
      date_dite: 'la phrase où chercher l’échéance (par défaut, l’intitulé)'
    },
    obligatoires: ['intitule']
  }, {
    nom: 'proposer_rangement',
    confirmation: true,
    description: 'Propose à Max de ranger une idée, une note ou une tâche que tu as reformulée toi-même, proprement et fidèlement. Cap lui demande son accord et ne range rien avant son oui.',
    parametres: {
      intitule: 'ta reformulation courte et fidèle de ce que Max a dit',
      categorie: 'ton meilleur choix de catégorie existante, ou vide pour À trier',
      sous_categorie: 'une sous-catégorie existante de cette catégorie, « À classer », ou vide',
      raison: 'si tu hésites sur l’endroit, quelques mots pour dire pourquoi ce choix',
      date_dite: 'la phrase où chercher l’échéance, s’il y en a une'
    },
    obligatoires: ['intitule']
  }, {
    nom: 'proposer_rendez_vous',
    confirmation: true,
    description: 'Propose d’inscrire un rendez-vous dans l’agenda. Cap redit le jour, la date, l’heure et le lieu à Max et attend son oui.',
    parametres: {
      titre: 'l’objet du rendez-vous',
      date: 'la date au format AAAA-MM-JJ',
      heure: 'l’heure de début au format HH:MM, vide si Max ne l’a pas dite',
      heure_fin: 'l’heure de fin au format HH:MM, vide sinon',
      lieu: 'le lieu ou l’adresse, vide sinon'
    },
    obligatoires: ['titre', 'date']
  }];

  const cle = valeur => String(valeur || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .toLocaleLowerCase('fr').replace(/\s+/g, ' ').trim();
  const plie = valeur => cle(valeur).replace(/[^a-z0-9]+/g, ' ').trim();
  const chaine = valeur => (typeof valeur === 'string' ? valeur.trim() : '');

  function categorieExistante(nom, parente = '') {
    const cherche = cle(nom);
    return listesChoix.categories(parente).find(categorie => cle(categorie) === cherche) || '';
  }

  // Trouve l'endroit exact où la tâche serait rangée, sans rien créer.
  function lieuTache(texte, categorie, sous_categorie) {
    const nomCategorie = categorie ? categorieExistante(categorie) : listesChoix.A_TRIER;
    if (!nomCategorie) throw new Error(`La catégorie « ${categorie} » n’existe pas. Rien n’a été ajouté.`);
    let sous = '';
    if (nomCategorie !== listesChoix.A_TRIER) {
      const disponibles = listesChoix.categories(nomCategorie);
      if (sous_categorie && sousCategories.estAClasser(sous_categorie)) {
        sous = disponibles.length ? sousCategories.A_CLASSER : '';
      } else if (sous_categorie) {
        sous = categorieExistante(sous_categorie, nomCategorie);
        if (!sous) throw new Error(`La sous-catégorie « ${sous_categorie} » n’existe pas dans ${nomCategorie}. Rien n’a été ajouté.`);
      } else {
        sous = sousCategories.trouver(texte, nomCategorie, disponibles, TACHES).sous_categorie;
      }
    }
    return { categorie: nomCategorie, sous_categorie: sous };
  }

  // Zéro perte : si l'intitulé a été reformulé, les mots exacts de Max sont gardés dans la note de la tâche.
  function noteMotsDeMax(intitule, mots) {
    const dits = chaine(mots);
    if (!dits || plie(dits).includes(plie(intitule))) return '';
    return `Dit par Max : « ${dits} »`;
  }

  function ajouterTache({ intitule, categorie = '', sous_categorie = '', date_dite = '', source = '', mots_max = '' } = {}) {
    const texte = chaine(intitule);
    if (!texte) throw new Error('Écris un intitulé pour cette tâche.');
    const lieu = lieuTache(texte, chaine(categorie), chaine(sous_categorie));
    const date = comprendreDemande.trouverDate(chaine(date_dite) || texte);
    const tache = creerTache({
      intitule: texte,
      categorie: lieu.categorie,
      sous_categorie: lieu.sous_categorie,
      echeance: date.date,
      note: noteMotsDeMax(texte, mots_max),
      origine: source === 'micro' ? 'dictée' : 'ajout à la main',
      fictif: false
    });
    return { tache, choix: date.choix };
  }

  function heureValide(heure) {
    return /^([01]\d|2[0-3]):[0-5]\d$/.test(heure);
  }

  function dateValide(date) {
    return /^\d{4}-\d{2}-\d{2}$/.test(date) && Number.isFinite(Date.parse(`${date}T12:00:00Z`))
      && new Date(`${date}T12:00:00Z`).toISOString().slice(0, 10) === date;
  }

  function uneHeureApres(heure) {
    const [h, m] = heure.split(':').map(Number);
    const fin = Math.min(h * 60 + m + 60, 23 * 60 + 59);
    return `${String(Math.floor(fin / 60)).padStart(2, '0')}:${String(fin % 60).padStart(2, '0')}`;
  }

  function rappelsValides(rappels) {
    const liste = Array.isArray(rappels) ? rappels : chaine(rappels).split(/[ ,;]+/).filter(Boolean);
    return liste.map(Number).filter(minutes => Number.isInteger(minutes) && minutes >= 0 && minutes <= 40320).slice(0, 5);
  }

  // « lundi 11 janvier 2027 », calculé par Cap (jamais par l'IA).
  function dateDite(date) {
    return new Intl.DateTimeFormat('fr-FR', { timeZone: 'UTC', weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })
      .format(new Date(`${date}T12:00:00Z`));
  }

  function heureParlee(heure) {
    const [h, m] = heure.split(':');
    return m === '00' ? `${Number(h)} h` : `${Number(h)} h ${m}`;
  }

  // Une heure dite par Max : « 15h30 », « 15 h », « 9:05 », « midi », « minuit ».
  function heureDite(texte) {
    const plat = cle(texte);
    if (/\bmidi\b/.test(plat) && !/\d/.test(plat)) return '12:00';
    if (/\bminuit\b/.test(plat) && !/\d/.test(plat)) return '00:00';
    const trouve = /(?<!\d)(\d{1,2}) ?(?:heures?|h|:) ?(\d{2})?(?!\d)/.exec(plat);
    if (!trouve) return '';
    const heures = Number(trouve[1]);
    const minutes = Number(trouve[2] || 0);
    if (heures > 23 || minutes > 59) return '';
    return `${String(heures).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
  }

  // Parmi plusieurs dates possibles, celle que Max désigne (« le 5 », « jeudi prochain », « aujourd'hui »).
  function dateChoisie(texte, choix) {
    const plat = cle(texte);
    const parJour = choix.filter(date => new RegExp(`(?<!\\d)${Number(date.slice(8))}(?!\\d)`).test(plat));
    if (parJour.length === 1) return parJour[0];
    if (/prochain|suivant|semaine prochaine|d apres|plus tard/.test(plat.replace(/'/g, ' '))) return choix[choix.length - 1];
    if (/aujourd|ce jour|cette semaine|celui ci|le premier/.test(plat)) return choix[0];
    return '';
  }

  // Proposition pour une action « confirmation » : ce que Cap dit à Max, et les paramètres exacts exécutés après son oui.
  // Renvoie { texte, parametres } ou, s'il manque un détail essentiel, { manque, texte, parametres, choix }.
  function preparerProposition(nom, parametres = {}) {
    if (nom === 'proposer_rangement') {
      const intitule = chaine(parametres.intitule);
      if (!intitule) throw new Error('Je n’ai rien à ranger.');
      const lieu = lieuTache(intitule, chaine(parametres.categorie), chaine(parametres.sous_categorie));
      const raison = chaine(parametres.raison).replace(/[.!?…]+$/, '');
      const texte = `Je mets « ${intitule} » dans ${[lieu.categorie, lieu.sous_categorie].filter(Boolean).join(', ')}${raison ? ` (${raison})` : ''}, ça te va ?`;
      return { texte, parametres: { ...parametres, intitule, ...lieu } };
    }
    if (nom === 'proposer_rendez_vous') {
      const titre = chaine(parametres.titre) || 'Rendez-vous';
      const lieu = chaine(parametres.lieu);
      const choix = (Array.isArray(parametres.choix_date) ? parametres.choix_date : []).filter(dateValide);
      let date = chaine(parametres.date);
      const heure = chaine(parametres.heure);
      const base = { titre, date, heure, lieu, rappels: rappelsValides(parametres.rappels) };
      if (!dateValide(date) && choix.length > 1) {
        return { manque: 'date', choix, parametres: base, texte: `Pour ce rendez-vous, c’est le ${choix.map(dateDite).join(' ou le ')} ?` };
      }
      if (!dateValide(date) && choix.length === 1) date = choix[0];
      if (!dateValide(date)) return { manque: 'date', choix: [], parametres: base, texte: 'Pour ce rendez-vous, quel jour ?' };
      if (!heureValide(heure)) return { manque: 'heure', choix: [], parametres: { ...base, date }, texte: 'À quelle heure ?' };
      const fin = chaine(parametres.heure_fin);
      const heure_fin = heureValide(fin) && fin > heure ? fin : uneHeureApres(heure);
      const objet = titre === 'Rendez-vous' ? 'Rendez-vous' : `Rendez-vous « ${titre} »`;
      const texte = `${objet} le ${dateDite(date)} à ${heureParlee(heure)}${lieu ? `, ${lieu}` : ''}, c’est bien ça ?`;
      return { texte, parametres: { ...base, date, heure, heure_fin } };
    }
    throw new Error('Cap ne sait pas proposer cette action.');
  }

  // Complète une proposition à laquelle il manquait la date ou l'heure. Renvoie les nouveaux paramètres, ou null.
  function completerProposition(proposition, texte) {
    if (proposition.manque === 'heure') {
      const heure = heureDite(texte);
      return heure ? { ...proposition.parametres, heure } : null;
    }
    if (proposition.manque === 'date' && proposition.choix.length) {
      const date = dateChoisie(texte, proposition.choix);
      return date ? { ...proposition.parametres, date, heure: proposition.parametres.heure || heureDite(texte) } : null;
    }
    return null;
  }

  // Après le oui de Max : le rendez-vous va dans l'agenda Cap – FICTIF (jamais l'agenda principal).
  function ajouterRendezVous(parametres) {
    const { texte, parametres: champs, manque } = preparerProposition('proposer_rendez_vous', parametres);
    if (manque) return Promise.reject(new Error(texte));
    return googleAgenda.creerRendezVous({
      titre: champs.titre, date: champs.date, heure: champs.heure, heure_fin: champs.heure_fin,
      lieu: champs.lieu, notes: '', telephone: '', mail: '', rappels: champs.rappels
    });
  }

  const EXECUTANTS = { ajouter_tache: ajouterTache, proposer_rangement: ajouterTache, proposer_rendez_vous: ajouterRendezVous };

  function executer(nom, parametres) {
    if (!Object.prototype.hasOwnProperty.call(EXECUTANTS, nom)) {
      throw new Error('Cap ne sait pas encore faire cette action. Rien n’a été fait.');
    }
    return EXECUTANTS[nom](parametres && typeof parametres === 'object' ? parametres : {});
  }

  function demandeConfirmation(nom) {
    return CATALOGUE.some(action => action.nom === nom && action.confirmation);
  }

  return { CATALOGUE, executer, categorieExistante, demandeConfirmation, preparerProposition, completerProposition, heureDite, dateDite };
})();
