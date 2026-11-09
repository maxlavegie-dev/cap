import html
import json
import pathlib
import re
import struct
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

APP = pathlib.Path(__file__).resolve().parent
EDGE = pathlib.Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
SOURCES = ["donnees_fictives.js", "etapes_par_defaut.js", "stockage.js", "vibration.js", "annulation.js", "taches.js", "listes_choix.js", "annuaire.js", "indices_rangement.js", "sous_categories.js", "reglages_google.js", "google_compte_relations.js", "google_connexion.js", "cle_picker.js", "google_picker.js", "google_sheets.js", "google_agenda.js", "fichiers_vocaux_drive.js", "synchronisation.js", "dictee.js", "phrases_clavier.js", "preferences_clavier.js", "voix.js", "comprendre_dates.js", "comprendre_demande.js", "phrases_modifiables.js", "phrases_modifiables_etat.js", "commandes_annuaire.js", "fichiers_vocaux.js", "fichiers_vocaux_notes.js", "fichiers_vocaux_tableau.js", "fichiers_vocaux_echeancier.js", "fichiers_vocaux_a_faire.js", "reglages_ia.js", "limite_ia.js", "cle_ia.js", "actions_cap.js", "cerveau.js", "cerveau_prepare.js", "journal_ia.js", "cerveau_claude.js", "demandes.js", "recherche.js", "journal_actions.js", "fichiers_vocaux_controleur.js", "fiche_rendezvous.js", "choix_dates.js", "fermeture_fenetres.js", "fenetres_listes.js", "synchro_listes.js", "synchro_annuaire.js", "fiche_contact.js", "commande_annuaire_ui.js", "sauvegarde_drive.js", "scan_image.js", "scan_pdf.js", "scan_documents.js", "scan_file.js", "scan_depot.js", "classement.js", "journaux.js", "scan_lecture.js", "scan_nommage.js", "nommage_scan.js", "mots_courts.js", "emetteur.js", "relations.js", "attente.js", "commandes_vocales.js", "choix_sur_eau.js", "transition_ecrans.js", "relations_creation.js", "visionneuse_cap.js", "relations_compte.js", "relations_mp3.js", "scan_ecran.js", "tuiles.js", "mode_trier.js", "phrases_apprendre.js", "tableur_phrases.js", "tableur_cap.js", "numero_choix.js", "app.js", "ecran_eau.js", "accueil_cap.js", "geste_retour.js", "commandes_navigation.js", "commandes_musique.js", "commandes_visionneuse.js"]

TESTS_JS = r"""
(async () => {
  const CLE = 'cap_taches_v1';
  const PREFIXE_SAUVEGARDE = CLE + '_illisible_';
  const CLE_USAGE = 'cap_usage_phrases_v1';
  const CLE_HISTORIQUE = 'cap_historique_demandes_v1';
  const CLE_SILENCE = 'cap_reponse_silencieuse_v1';
  const resultats = [];
  const MESSAGE_ILLISIBLE = 'La liste enregistrée était illisible. Une copie complète a été conservée sur ce téléphone ; les tâches fictives sont affichées.';

  function instanceStockage() {
    return new Function(SOURCE_STOCKAGE + '\nreturn stockage;')();
  }

  function clesSauvegarde() {
    return Object.keys(localStorage).filter(cle => cle.startsWith(PREFIXE_SAUVEGARDE));
  }

  function reinitialiser() {
    for (const cle of Object.keys(localStorage)) {
      if (cle.startsWith(CLE)) localStorage.removeItem(cle);
    }
    for (const cle of [CLE_USAGE, CLE_HISTORIQUE, CLE_SILENCE, 'cap_google_file_v1']) localStorage.removeItem(cle);
    const chargement = stockage.charger();
    TACHES.splice(0, TACHES.length, ...chargement.taches);
    localStorage.removeItem('cap_annuaire_v1');
    localStorage.removeItem('cap_annuaire_a_envoyer_v1');
    annuaire.recharger();
  }

  function attendre(condition, message) {
    if (!condition) throw new Error(message);
  }

  function attendreEgal(reel, attendu, message) {
    const r = JSON.stringify(reel);
    const a = JSON.stringify(attendu);
    if (r !== a) throw new Error(`${message} : attendu ${a}, reçu ${r}`);
  }

  function attendreErreur(fonction, fragment) {
    let message = null;
    try {
      fonction();
    } catch (erreur) {
      message = String(erreur && erreur.message ? erreur.message : erreur);
    }
    attendre(message !== null && message.includes(fragment),
      `erreur attendue contenant « ${fragment} », reçu : ${message}`);
  }

  function test(nom, fonction) {
    try {
      reinitialiser();
      fonction();
      resultats.push({ nom, ok: true, erreur: '' });
    } catch (erreur) {
      resultats.push({ nom, ok: false, erreur: String(erreur && erreur.message ? erreur.message : erreur) });
    }
  }

  const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

  test('modèles complets : dates et fait cohérents', () => {
    attendre(TACHES.length > 0, 'liste vide');
    const identifiants = new Set(TACHES.map(t => t.id));
    for (const t of TACHES) {
      attendre(DATE_RE.test(t.date_entree), `date_entree invalide pour ${t.id}`);
      for (const champ of ['echeance', 'date_realisation', 'avant_le', 'abandonnee_le']) {
        attendre(t[champ] === '' || DATE_RE.test(t[champ]), `${champ} invalide pour ${t.id}`);
      }
      attendre(t.fait === (t.date_realisation !== ''), `fait incohérent avec date_realisation pour ${t.id}`);
      attendre(['haute', 'normale', 'basse'].includes(t.priorite), `priorité invalide pour ${t.id}`);
      attendre(t.parente === '' || identifiants.has(t.parente), `parente inconnue pour ${t.id}`);
    }
  });

  test('hiérarchie fictive : albums 3 + 2 titres', () => {
    const titres = TACHES.filter(t => t.categorie === 'Musique' && !t.parente);
    attendre(titres.filter(t => t.sous_categorie === 'Album A').length === 3, 'Album A doit avoir 3 titres');
    attendre(titres.filter(t => t.sous_categorie === 'Album B').length === 2, 'Album B doit avoir 2 titres');
    const etapesDe = id => TACHES.filter(t => t.parente === id);
    const lucioles = titres.find(t => t.intitule === 'Les lucioles du large');
    attendre(lucioles, 'titre Les lucioles du large introuvable');
    attendreEgal(etapesDe(lucioles.id).length, 4, 'étapes de Les lucioles du large');
    const autres = titres.filter(t => t.id !== lucioles.id);
    for (const titre of autres) {
      attendreEgal(etapesDe(titre.id).length, 3, `étapes de ${titre.intitule}`);
    }
    const roman = TACHES.find(t => t.intitule === 'Les jardins suspendus de minuit');
    attendreEgal(etapesDe(roman.id).length, 3, 'étapes du roman');
  });

  test('créer conserve l’intitulé exact, caractères HTML compris', () => {
    const intitule = '<b>Ça & "é" &amp; <i>x</i></b> ’';
    const tache = creerTache({ intitule, categorie: 'Test' });
    attendreEgal(TACHES.find(t => t.id === tache.id).intitule, intitule, 'intitulé en mémoire');
    const sauvegarde = JSON.parse(localStorage.getItem(CLE));
    attendreEgal(sauvegarde.find(t => t.id === tache.id).intitule, intitule, 'intitulé sauvegardé');
  });

  test('identifiants au format unique et sans doublon', () => {
    const nouvelles = [];
    for (let i = 0; i < 20; i++) nouvelles.push(creerTache({ intitule: `Tâche ${i}`, categorie: 'Test' }));
    const ids = TACHES.map(t => t.id);
    attendre(new Set(ids).size === ids.length, 'identifiant en double');
    for (const t of nouvelles) {
      attendre(/^T-[0-9a-z]{12}$/.test(t.id), `format d’identifiant incorrect : ${t.id}`);
    }
  });

  test('étapes par défaut : modèles, catégories et erreurs', () => {
    const parent = creerAvecEtapesParDefaut({ intitule: 'Titre test', categorie: 'Musique', sous_categorie: 'Album T' }, "Titre d'album");
    const etapes = TACHES.filter(t => t.parente === parent.id);
    attendreEgal(etapes.map(t => t.intitule), ETAPES_PAR_DEFAUT["Titre d'album"], 'étapes Titre d’album');
    for (const etape of etapes) {
      attendre(etape.categorie === 'Musique' && etape.sous_categorie === 'Album T', 'catégorie d’étape incorrecte');
    }
    const roman = creerAvecEtapesParDefaut({ intitule: 'Mon roman', categorie: 'Écriture', sous_categorie: 'Roman' }, 'Roman');
    attendreEgal(TACHES.filter(t => t.parente === roman.id).map(t => t.intitule), ETAPES_PAR_DEFAUT.Roman, 'étapes Roman');
    const avant = TACHES.length;
    attendreErreur(() => creerAvecEtapesParDefaut({ intitule: 'X' }, 'Inconnu'), 'introuvable');
    attendreErreur(() => creerAvecEtapesParDefaut({ intitule: 'X', parente: parent.id }, 'Roman'), 'réservées');
    attendreEgal(TACHES.length, avant, 'nombre de tâches après erreurs');
  });

  test('cocher et décocher : date locale', () => {
    const tache = creerTache({ intitule: 'Cocher', categorie: 'Test' });
    cocher(tache.id, true);
    const coche = TACHES.find(t => t.id === tache.id);
    attendre(coche.fait === true, 'tâche non cochée');
    attendreEgal(coche.date_realisation, dateDuJour(), 'date de réalisation');
    cocher(tache.id, false);
    const decochee = TACHES.find(t => t.id === tache.id);
    attendre(decochee.fait === false && decochee.date_realisation === '', 'tâche non décochée');
    attendreErreur(() => cocher(tache.id, 'oui'), 'cochée ou décochée');
  });

  test('abandon et remise sans perte et sans cascade', () => {
    const parent = creerTache({ intitule: 'Parent', categorie: 'Test' });
    const e1 = ajouterEtape(parent.id, 'Étape 1');
    const e2 = ajouterEtape(parent.id, 'Étape 2');
    const nombre = TACHES.length;
    abandonner(parent.id);
    attendreEgal(TACHES.find(t => t.id === parent.id).abandonnee_le, dateDuJour(), 'date d’abandon');
    attendre(TACHES.find(t => t.id === e1.id).abandonnee_le === '', 'cascade sur étape 1');
    attendre(TACHES.find(t => t.id === e2.id).abandonnee_le === '', 'cascade sur étape 2');
    attendreEgal(TACHES.length, nombre, 'nombre de tâches après abandon');
    attendreErreur(() => ajouterEtape(parent.id, 'Refusée'), 'Remets');
    remettre(parent.id);
    attendre(TACHES.find(t => t.id === parent.id).abandonnee_le === '', 'remise incomplète');
    attendreEgal(TACHES.length, nombre, 'nombre de tâches après remise');
    attendreEgal(TACHES.find(t => t.id === e1.id).intitule, 'Étape 1', 'intitulé conservé');
  });

  test('progression exclut les tâches abandonnées', () => {
    const parent = creerTache({ intitule: 'Projet', categorie: 'Test', sous_categorie: 'Progr' });
    const a = ajouterEtape(parent.id, 'A');
    const b = ajouterEtape(parent.id, 'B');
    creerTache({ intitule: 'Solo', categorie: 'Test', sous_categorie: 'Progr' });
    cocher(a.id, true);
    attendreEgal(avancementTache(parent.id), { faites: 1, total: 2 }, 'avancement tâche');
    attendreEgal(avancementSousCategorie('Test', 'Progr'), 50, 'avancement sous-catégorie');
    abandonner(b.id);
    attendreEgal(avancementTache(parent.id), { faites: 1, total: 1 }, 'avancement après abandon');
    attendreEgal(avancementSousCategorie('Test', 'Progr'), 100, 'sous-catégorie après abandon');
    remettre(b.id);
    attendreEgal(avancementSousCategorie('Test', 'Progr'), 50, 'sous-catégorie après remise');
  });

  test('joursRestants compte les jours civils en UTC', () => {
    attendreEgal(joursRestants(dateDuJour()), 0, 'aujourd’hui');
    const demain = new Date(`${dateDuJour()}T00:00:00Z`);
    demain.setUTCDate(demain.getUTCDate() + 1);
    attendreEgal(joursRestants(demain.toISOString().slice(0, 10)), 1, 'demain');
    attendreEgal(joursRestants('2026-03-30') - joursRestants('2026-03-29'), 1, 'changement d’heure de mars');
    attendreEgal(joursRestants('2026-10-26') - joursRestants('2026-10-25'), 1, 'changement d’heure d’octobre');
    attendreErreur(() => joursRestants('2026-02-30'), 'valide');
    attendreErreur(() => joursRestants('2026-13-01'), 'valide');
    attendreErreur(() => joursRestants('2026-1-01'), 'valide');
  });

  test('erreur d’enregistrement : retour arrière complet', () => {
    const parent = creerTache({ intitule: 'Avant', categorie: 'Test' });
    const avant = JSON.stringify(TACHES);
    const original = stockage.enregistrer;
    stockage.enregistrer = () => { throw new Error('Simulation'); };
    try {
      attendreErreur(() => creerTache({ intitule: 'Nouvelle', categorie: 'Test' }), 'Simulation');
      attendreErreur(() => cocher(parent.id, true), 'Simulation');
      attendreErreur(() => abandonner(parent.id), 'Simulation');
    } finally {
      stockage.enregistrer = original;
    }
    attendre(JSON.stringify(TACHES) === avant, 'liste modifiée après retour arrière');
    attendre(!TACHES.some(t => t.intitule === 'Nouvelle'), 'nouvelle tâche restée en mémoire');
    const restee = TACHES.find(t => t.id === parent.id);
    attendre(restee.fait === false && restee.abandonnee_le === '', 'modification restée en mémoire');
  });

  test('sauvegarde localStorage cohérente avec la mémoire', () => {
    const tache = creerTache({ intitule: 'Sauvegarde', categorie: 'Test' });
    cocher(tache.id, true);
    attendreEgal(JSON.parse(localStorage.getItem(CLE)), TACHES, 'contenu sauvegardé');
  });

  test('stockage : liste illisible copiée puis fictives affichées', () => {
    const brut = 'pas du json {';
    localStorage.setItem(CLE, brut);
    const chargement = instanceStockage().charger();
    const sauvegardes = clesSauvegarde();
    attendreEgal(sauvegardes.length, 1, 'nombre de copies de sécurité');
    attendre(localStorage.getItem(sauvegardes[0]) === brut, 'copie de sécurité différente de l’original');
    attendreEgal(chargement.message, MESSAGE_ILLISIBLE, 'message');
    attendreEgal(chargement.taches.length, TACHES_FICTIVES.length, 'nombre de tâches fictives');
    attendre(localStorage.getItem(CLE) === JSON.stringify(chargement.taches), 'fictives non sauvegardées');
  });

  test('stockage : liste vide [] ne relance pas les fictives', () => {
    localStorage.setItem(CLE, '[]');
    const chargement = instanceStockage().charger();
    attendreEgal(chargement.taches, [], 'liste chargée');
    attendreEgal(chargement.message, '', 'message');
    attendreEgal(clesSauvegarde().length, 0, 'copies de sécurité');
  });

  test('stockage : copie de sécurité refusée, original intact et verrouillé', () => {
    const brut = 'pas du json {';
    localStorage.setItem(CLE, brut);
    const original = Storage.prototype.setItem;
    Storage.prototype.setItem = function () { throw new Error('refus'); };
    let chargement;
    let instance;
    try {
      instance = instanceStockage();
      chargement = instance.charger();
    } finally {
      Storage.prototype.setItem = original;
    }
    attendre(chargement.message.startsWith('La liste enregistrée est illisible et sa copie de sécurité a échoué'),
      `message inattendu : ${chargement.message}`);
    attendre(localStorage.getItem(CLE) === brut, 'original modifié');
    attendreEgal(clesSauvegarde().length, 0, 'copies de sécurité');
    attendreErreur(() => instance.enregistrer(chargement.taches), 'Sauvegarde indisponible');
    attendre(localStorage.getItem(CLE) === brut, 'original modifié après verrouillage');
  });

  test('stockage : accès refusé en lecture, modifications bloquées', () => {
    const original = Storage.prototype.getItem;
    Storage.prototype.getItem = function () { throw new Error('refus'); };
    let chargement;
    let instance;
    try {
      instance = instanceStockage();
      chargement = instance.charger();
    } finally {
      Storage.prototype.getItem = original;
    }
    attendre(chargement.message.includes('inaccessible'), `message inattendu : ${chargement.message}`);
    attendreErreur(() => instance.enregistrer(chargement.taches), 'Sauvegarde indisponible');
  });

  test('stockage : conflit avec une autre fenêtre bloque l’écriture', () => {
    localStorage.setItem(CLE, JSON.stringify(TACHES_FICTIVES));
    const instance = instanceStockage();
    const chargement = instance.charger();
    localStorage.setItem(CLE, '[]');
    attendreErreur(() => instance.enregistrer(chargement.taches), 'autre fenêtre');
    attendre(localStorage.getItem(CLE) === '[]', 'contenu écrasé malgré le conflit');
  });

  function fauxConstructeur() {
    const instances = [];
    const comportement = { constructeur: false, start: false, stop: false };
    class FauxReconnaissance {
      constructor() {
        if (comportement.constructeur) throw new Error('constructeur');
        this.lang = '';
        this.interimResults = null;
        this.continuous = null;
        this.maxAlternatives = null;
        this.demarrages = 0;
        this.arrets = 0;
        instances.push(this);
      }
      start() {
        this.demarrages++;
        if (comportement.start) throw new Error('start');
      }
      stop() {
        this.arrets++;
        if (comportement.stop) throw new Error('stop');
      }
    }
    return { classe: FauxReconnaissance, instances, comportement };
  }

  function avecConstructeurs(sr, wk, fonction) {
    const noms = ['SpeechRecognition', 'webkitSpeechRecognition'];
    const avant = noms.map(nom => [nom, Object.prototype.hasOwnProperty.call(window, nom), window[nom]]);
    window.SpeechRecognition = sr;
    window.webkitSpeechRecognition = wk;
    try {
      return fonction();
    } finally {
      for (const [nom, existait, valeur] of avant) {
        if (existait) window[nom] = valeur;
        else delete window[nom];
      }
    }
  }

  function nouvelleDictee() {
    return new Function(SOURCE_DICTEE + '\nreturn dictee;')();
  }

  function rappels() {
    const journal = [];
    return {
      journal,
      surProvisoire: texte => journal.push(['provisoire', texte]),
      surFinal: texte => journal.push(['final', texte]),
      surErreur: code => journal.push(['erreur', code]),
      surFin: () => journal.push(['fin'])
    };
  }

  function segment(texte, final) {
    const liste = [{ transcript: texte }];
    liste.isFinal = final;
    return liste;
  }

  test('dictée : provisoire puis final, sans répétition', () => {
    const fake = fauxConstructeur();
    avecConstructeurs(fake.classe, undefined, () => {
      const d = nouvelleDictee();
      const r = rappels();
      d.demarrer(r);
      const instance = fake.instances[0];
      instance.onresult({ resultIndex: 0, results: [segment('  Bonjour <b>Ça</b> ', false)] });
      instance.onresult({ resultIndex: 0, results: [segment('Bonjour à tous', true)] });
      instance.onresult({ resultIndex: 1, results: [segment('Bonjour à tous', true), segment('merci', false)] });
      attendreEgal(r.journal, [['provisoire', '  Bonjour <b>Ça</b> '], ['final', 'Bonjour à tous'], ['provisoire', 'merci']], 'transmissions');
    });
  });

  test('dictée : réglages fr-FR, continu faux, une alternative', () => {
    const fake = fauxConstructeur();
    avecConstructeurs(fake.classe, undefined, () => {
      const d = nouvelleDictee();
      d.demarrer(rappels());
      attendreEgal(fake.instances.length, 1, 'nombre d’instances');
      const instance = fake.instances[0];
      attendreEgal([instance.lang, instance.interimResults, instance.continuous, instance.maxAlternatives, instance.demarrages],
        ['fr-FR', true, false, 1, 1], 'réglages');
      attendre(d.enCours(), 'écoute non démarrée');
    });
  });

  test('dictée : erreur API transmise, nouveau départ après onend', () => {
    const fake = fauxConstructeur();
    avecConstructeurs(fake.classe, undefined, () => {
      const d = nouvelleDictee();
      const r = rappels();
      d.demarrer(r);
      fake.instances[0].onerror({ error: 'network' });
      attendreEgal(r.journal, [['erreur', 'network']], 'erreur transmise');
      attendre(d.enCours(), 'état libéré avant onend');
      d.demarrer(r);
      fake.instances[0].onend();
      attendreEgal(r.journal, [['erreur', 'network'], ['erreur', 'occupee'], ['fin']], 'fin attendue');
      attendre(!d.enCours(), 'état non libéré après onend');
      d.demarrer(r);
      attendreEgal(fake.instances.length, 2, 'nouveau départ');
    });
  });

  test('dictée : pas de double départ', () => {
    const fake = fauxConstructeur();
    avecConstructeurs(fake.classe, undefined, () => {
      const d = nouvelleDictee();
      const r = rappels();
      d.demarrer(r);
      d.demarrer(r);
      attendreEgal(r.journal, [['erreur', 'occupee']], 'double départ');
      attendreEgal(fake.instances.length, 1, 'nombre d’instances');
      attendreEgal(fake.instances[0].demarrages, 1, 'nombre de démarrages');
    });
  });

  test('dictée : arrêt attend onend, pas de départ pendant l’arrêt', () => {
    const fake = fauxConstructeur();
    avecConstructeurs(fake.classe, undefined, () => {
      const d = nouvelleDictee();
      const r = rappels();
      d.demarrer(r);
      d.arreter();
      attendreEgal(fake.instances[0].arrets, 1, 'arrêts');
      attendre(d.enCours(), 'état libéré avant onend');
      d.demarrer(r);
      fake.instances[0].onend();
      attendre(!d.enCours(), 'état non libéré après onend');
      attendreEgal(r.journal, [['erreur', 'occupee'], ['fin']], 'arrêt');
    });
  });

  test('dictée : constructeurs absents, indisponible', () => {
    avecConstructeurs(undefined, undefined, () => {
      const d = nouvelleDictee();
      attendreEgal(d.disponible(), false, 'disponible');
      const r = rappels();
      d.demarrer(r);
      attendreEgal(r.journal, [['erreur', 'indisponible'], ['fin']], 'démarrage refusé');
      attendre(!d.enCours(), 'état coincé');
    });
  });

  test('dictée : webkitSpeechRecognition seul, disponible', () => {
    const fake = fauxConstructeur();
    avecConstructeurs(undefined, fake.classe, () => {
      attendreEgal(nouvelleDictee().disponible(), true, 'disponible');
    });
  });

  test('dictée : échecs constructeur, départ et arrêt sans état coincé', () => {
    const fake = fauxConstructeur();
    avecConstructeurs(fake.classe, undefined, () => {
      const d = nouvelleDictee();
      const r1 = rappels();
      fake.comportement.constructeur = true;
      d.demarrer(r1);
      attendreEgal(r1.journal, [['erreur', 'constructeur'], ['fin']], 'échec constructeur');
      attendre(!d.enCours(), 'état coincé après constructeur');
      fake.comportement.constructeur = false;
      const r2 = rappels();
      fake.comportement.start = true;
      d.demarrer(r2);
      attendreEgal(r2.journal, [['erreur', 'demarrage'], ['fin']], 'échec démarrage');
      attendre(!d.enCours(), 'état coincé après démarrage');
      fake.comportement.start = false;
      const r3 = rappels();
      d.demarrer(r3);
      attendre(d.enCours(), 'nouveau départ impossible');
      fake.comportement.stop = true;
      d.arreter();
      attendreEgal(r3.journal, [['erreur', 'arret']], 'échec arrêt');
      attendre(d.enCours(), 'écoute libérée alors que le micro pourrait écouter');
      d.demarrer(rappels());
      attendreEgal(fake.instances.length, 2, 'aucun départ supplémentaire après arrêt échoué');
      fake.instances[1].onend();
      attendre(!d.enCours(), 'état coincé après fin');
    });
  });

  test('dictée : anciens callbacks ignorés après fin', () => {
    const fake = fauxConstructeur();
    avecConstructeurs(fake.classe, undefined, () => {
      const d = nouvelleDictee();
      const r = rappels();
      d.demarrer(r);
      const ancienne = fake.instances[0];
      ancienne.onend();
      d.demarrer(r);
      const longueur = r.journal.length;
      ancienne.onresult({ resultIndex: 0, results: [segment('vieux', true)] });
      ancienne.onerror({ error: 'network' });
      ancienne.onend();
      attendreEgal(r.journal.length, longueur, 'callback ancien transmis');
      attendre(d.enCours(), 'nouvelle écoute arrêtée par un ancien callback');
    });
  });

  test('tâche dictée : À trier, origine dictée, intitulé exact sauvegardé', () => {
    const intitule = 'Appeler le garage « Dupont » : 2 pneus & <b>urgent</b> ’';
    const tache = creerTache({ intitule, categorie: 'À trier', origine: 'dictée' });
    const enMemoire = TACHES.find(t => t.id === tache.id);
    attendreEgal([enMemoire.intitule, enMemoire.categorie, enMemoire.origine], [intitule, 'À trier', 'dictée'], 'mémoire');
    const sauvee = JSON.parse(localStorage.getItem(CLE)).find(t => t.id === tache.id);
    attendreEgal([sauvee.intitule, sauvee.categorie, sauvee.origine], [intitule, 'À trier', 'dictée'], 'sauvegarde');
  });

  test('dictée : constructeur lu au démarrage, pas à la création', () => {
    const d = nouvelleDictee();
    const fake = fauxConstructeur();
    avecConstructeurs(fake.classe, undefined, () => {
      attendreEgal(d.disponible(), true, 'disponible après injection');
      d.demarrer(rappels());
      attendreEgal(fake.instances.length, 1, 'constructeur non lu au démarrage');
      d.arreter();
      fake.instances[0].onend();
    });
  });

  function micro() {
    return document.getElementById('microphone');
  }

  // 09/11/2026 (étape 2) : le premier toucher du GROS MICRO fait seulement apparaître « + » et la nouvelle icône ;
  // pour parler, un deuxième toucher. Avant : un seul toucher (micro().click()).
  function parlerAuGrosMicro(bouton) {
    const plus = bouton.ownerDocument.getElementById('micro-ajouter');
    if (plus && plus.hidden) bouton.click();
    bouton.click();
  }
  // 09/11/2026 : tests devenus sans objet (écran Micro, bouton « continu » retirés) : gardés tels quels, plus lancés.
  const testsRemplaces = [];
  async function testRemplace(nom) { testsRemplaces.push(nom); }
  function cliquerMicro() {
    parlerAuGrosMicro(micro()); // 09/11/2026 (avant : micro().click())
  }

  function texteStatut() {
    return Array.from(document.getElementById('statut').childNodes)
      .filter(noeud => noeud.nodeType === Node.TEXT_NODE)
      .map(noeud => noeud.textContent)
      .join('');
  }

  function sessionMicro(fonction) {
    if (document.getElementById('ecran-complet').hidden) document.getElementById('basculer-vue').click();
    const fake = fauxConstructeur();
    avecConstructeurs(fake.classe, undefined, () => {
      try {
        fonction(fake);
      } finally {
        for (const instance of fake.instances) instance.onend();
      }
    });
  }

  test('micro : état actif, provisoire puis final', () => {
    sessionMicro(fake => {
      cliquerMicro();
      attendreEgal(micro().getAttribute('aria-pressed'), 'true', 'état actif');
      attendreEgal(micro().getAttribute('aria-label'), 'Arrêter la dictée', 'libellé actif');
      const instance = fake.instances[0];
      instance.onresult({ resultIndex: 0, results: [segment('Bonjour', false)] });
      attendreEgal(texteStatut(), 'Bonjour', 'provisoire');
      instance.onresult({ resultIndex: 0, results: [segment('  <b>Ça</b> & "x"  ', true)] });
      attendreEgal(texteStatut(), 'Ajoutée dans À trier : « <b>Ça</b> & "x" »', 'final');
      attendre(Array.from(document.querySelectorAll('#liste-taches .intitule')).some(s => s.textContent === '<b>Ça</b> & "x"'),
        'intitulé non affiché tel quel');
      attendre(document.querySelector('#liste-taches b') === null, 'HTML interprété');
      instance.onend();
      attendreEgal(micro().getAttribute('aria-pressed'), 'false', 'état repos');
      attendreEgal(micro().getAttribute('aria-label'), 'Dicter une tâche', 'libellé repos');
      attendreEgal(texteStatut(), 'Ajoutée dans À trier : « <b>Ça</b> & "x" »', 'message conservé après fin');
    });
  });

  test('micro : À trier en premier, sans sous-titre', () => {
    sessionMicro(fake => {
      cliquerMicro();
      fake.instances[0].onresult({ resultIndex: 0, results: [segment('Note', true)] });
      const premiere = document.querySelector('#liste-taches section.categorie');
      attendreEgal(premiere.querySelector('h2').textContent, 'À trier', 'première catégorie');
      const sousSection = Array.from(document.querySelectorAll('#liste-taches section.sous-categorie'))
        .find(s => Array.from(s.querySelectorAll('.intitule')).some(i => i.textContent === 'Note'));
      attendre(sousSection && !sousSection.querySelector('h3'), 'sous-titre présent pour À trier');
    });
  });

  test('micro : Annuler abandonne sans supprimer', () => {
    sessionMicro(fake => {
      cliquerMicro();
      fake.instances[0].onresult({ resultIndex: 0, results: [segment('Pain', true)] });
      fake.instances[0].onend();
      const avant = TACHES.length;
      const bouton = document.querySelector('.annuler-dictee');
      attendre(bouton, 'bouton Annuler absent');
      attendreEgal(getComputedStyle(bouton).pointerEvents, 'auto', 'bouton cliquable');
      bouton.click();
      const tache = TACHES.find(t => t.intitule === 'Pain');
      attendreEgal(tache.abandonnee_le, dateDuJour(), 'date d’abandon');
      attendreEgal(TACHES.length, avant, 'nombre de tâches');
      attendreEgal(texteStatut(), 'Tâche abandonnée : tu la retrouves dans les tâches abandonnées.', 'annonce');
    });
  });

  test('micro : sauvegarde refusée, texte conservé après fin', () => {
    const original = stockage.enregistrer;
    stockage.enregistrer = () => { throw new Error('Simulation'); };
    try {
      sessionMicro(fake => {
        cliquerMicro();
        fake.instances[0].onresult({ resultIndex: 0, results: [segment('Acheter du lait', true)] });
        fake.instances[0].onend();
        attendreEgal(texteStatut(), 'Simulation Texte dicté à recopier : « Acheter du lait »', 'message');
        attendre(!TACHES.some(t => t.intitule === 'Acheter du lait'), 'tâche créée malgré le refus');
      });
    } finally {
      stockage.enregistrer = original;
    }
  });

  test('micro : codes d’erreur, fin attendue et retour normal', () => {
    sessionMicro(fake => {
      cliquerMicro();
      fake.instances[0].onerror({ error: 'aborted' });
      attendreEgal(texteStatut(), '', 'arrêt volontaire silencieux');
      fake.instances[0].onend();
      cliquerMicro();
      attendreEgal(fake.instances.length, 2, 'retour normal');
      fake.instances[1].onerror({ error: 'network' });
      attendreEgal(texteStatut(), "La dictée a besoin d'internet pour l'instant.", 'message réseau');
      fake.instances[1].onend();
      attendreEgal(micro().getAttribute('aria-pressed'), 'false', 'état repos après erreur');
      cliquerMicro();
      attendreEgal(fake.instances.length, 3, 'nouveau départ après erreur');
      attendreEgal(micro().getAttribute('aria-pressed'), 'true', 'état actif après erreur');
    });
  });

  test('micro : tous les messages d’erreur et final vide', () => {
    sessionMicro(fake => {
      const messages = {
        'not-allowed': 'Le micro est bloqué. Autorise-le pour cette page dans le navigateur.',
        'service-not-allowed': 'Le micro est bloqué. Autorise-le pour cette page dans le navigateur.',
        'no-speech': "Je n'ai rien entendu, réessaie.",
        'audio-capture': 'Aucun micro trouvé.',
        inconnu: "La dictée n'a pas marché, réessaie."
      };
      for (const [code, message] of Object.entries(messages)) {
        cliquerMicro();
        const instance = fake.instances.at(-1);
        instance.onerror({ error: code });
        instance.onend();
        attendreEgal(texteStatut(), message, code);
        attendreEgal(micro().getAttribute('aria-pressed'), 'false', 'repos');
      }
      const avant = TACHES.length;
      cliquerMicro();
      const instance = fake.instances.at(-1);
      instance.onresult({ resultIndex: 0, results: [segment('   ', true)] });
      instance.onend();
      attendreEgal(TACHES.length, avant, 'aucune tâche vide créée');
      attendreEgal(texteStatut(), "Je n'ai rien entendu, réessaie.", 'final vide');
    });
  });

  test('micro : deuxième clic arrête, fin attendue', () => {
    sessionMicro(fake => {
      cliquerMicro();
      cliquerMicro();
      attendreEgal(fake.instances.length, 1, 'nouvelle écoute au lieu d’arrêt');
      attendreEgal(fake.instances[0].arrets, 1, 'arrêt demandé');
      attendreEgal(micro().getAttribute('aria-pressed'), 'true', 'état avant fin');
      fake.instances[0].onend();
      attendreEgal(micro().getAttribute('aria-pressed'), 'false', 'état après fin');
    });
  });

  test('micro : indisponible, message sans état actif', () => {
    avecConstructeurs(undefined, undefined, () => {
      cliquerMicro();
      attendreEgal(texteStatut(), "La dictée n'est pas disponible dans ce navigateur. Utilise le bouton +.", 'message');
      attendreEgal(micro().getAttribute('aria-pressed'), 'false', 'état');
    });
  });

  test('micro : bouton Annuler expire après 8 secondes', () => {
    const original = window.setTimeout;
    const delais = [];
    window.setTimeout = (fonction, delai, ...args) => {
      if (delai === 8000) {
        delais.push(fonction);
        return 0;
      }
      return original.call(window, fonction, delai, ...args);
    };
    try {
      sessionMicro(fake => {
        cliquerMicro();
        fake.instances[0].onresult({ resultIndex: 0, results: [segment('Lait', true)] });
        fake.instances[0].onend();
        attendreEgal(delais.length, 1, 'délai d’expiration');
        attendre(document.querySelector('.annuler-dictee'), 'Annuler absent avant délai');
        delais[0]();
        attendre(document.querySelector('.annuler-dictee') === null, 'Annuler toujours présent');
      });
    } finally {
      window.setTimeout = original;
    }
  });

  test('micro note : silence de 40 secondes, enregistre ce qui est dicté, aucune entrée vide', () => {
    const original = {
      sessionActive: fichiersVocauxControleur.sessionActive,
      detecterOuvertureNote: fichiersVocauxControleur.detecterOuvertureNote,
      ouvrirSession: fichiersVocauxControleur.ouvrirSession,
      accumuler: fichiersVocauxControleur.accumuler,
      fermerSession: fichiersVocauxControleur.fermerSession
    };
    let active = false;
    let morceaux = [];
    let fermetures = 0;
    fichiersVocauxControleur.sessionActive = () => active;
    fichiersVocauxControleur.detecterOuvertureNote = texte => (texte === 'bloc-notes, note' ? { fichier: 'bloc_notes' } : null);
    fichiersVocauxControleur.ouvrirSession = () => { active = true; morceaux = []; };
    fichiersVocauxControleur.accumuler = texte => { if (texte) morceaux.push(texte); };
    fichiersVocauxControleur.fermerSession = () => ({
      then(resolve) {
        fermetures += 1;
        active = false;
        const message = morceaux.length ? `C'est noté. Ajouté à ton bloc-notes : ${morceaux.join(' ')}.`
          : "Je n'ai rien noté, rien à enregistrer.";
        resolve({ type: 'reponse', message, parole: message });
        return Promise.resolve();
      }
    });
    const originalNow = Date.now;
    let maintenant = originalNow();
    Date.now = () => maintenant;
    try {
      sessionMicro(fake => {
        cliquerMicro();
        fake.instances[0].onresult({ resultIndex: 0, results: [segment('bloc-notes, note', true)] });
        fake.instances[0].onend();
        attendreEgal(active, true, 'session de dictée libre ouverte');
        attendreEgal(fake.instances.length, 2, 'réécoute automatique après ouverture, sans retoucher le micro');
        fake.instances[1].onresult({ resultIndex: 0, results: [segment('Acheter du lait', true)] });
        fake.instances[1].onend();
        attendreEgal(morceaux, ['Acheter du lait'], 'morceau dicté accumulé');
        attendreEgal(fake.instances.length, 3, 'réécoute après un bout dicté');
        maintenant += 41000;
        fake.instances[2].onend();
        attendreEgal(fermetures, 1, 'session fermée après 40 secondes de silence');
        attendreEgal(active, false, 'session bien fermée, pas bloquée');
        attendreEgal(fake.instances.length, 3, 'pas de nouvelle écoute lancée après le silence');
        attendreEgal(micro().getAttribute('aria-pressed'), 'false', 'micro au repos après le silence');
        attendre(texteStatut().includes('Acheter du lait'), 'ce qui a été dicté est quand même enregistré');
      });
    } finally {
      Date.now = originalNow;
      Object.assign(fichiersVocauxControleur, original);
    }
  });

  test('micro note : silence de 40 secondes sans rien dicté, aucune entrée vide créée', () => {
    const original = {
      sessionActive: fichiersVocauxControleur.sessionActive,
      detecterOuvertureNote: fichiersVocauxControleur.detecterOuvertureNote,
      ouvrirSession: fichiersVocauxControleur.ouvrirSession,
      accumuler: fichiersVocauxControleur.accumuler,
      fermerSession: fichiersVocauxControleur.fermerSession
    };
    let active = false;
    const morceaux = [];
    let fermetures = 0;
    fichiersVocauxControleur.sessionActive = () => active;
    fichiersVocauxControleur.detecterOuvertureNote = texte => (texte === 'bloc-notes, note' ? { fichier: 'bloc_notes' } : null);
    fichiersVocauxControleur.ouvrirSession = () => { active = true; };
    fichiersVocauxControleur.accumuler = texte => { if (texte) morceaux.push(texte); };
    fichiersVocauxControleur.fermerSession = () => ({
      then(resolve) {
        fermetures += 1;
        active = false;
        const message = morceaux.length ? `Ajouté : ${morceaux.join(' ')}.` : "Je n'ai rien noté, rien à enregistrer.";
        resolve({ type: 'reponse', message, parole: message });
        return Promise.resolve();
      }
    });
    const originalNow = Date.now;
    let maintenant = originalNow();
    Date.now = () => maintenant;
    try {
      sessionMicro(fake => {
        cliquerMicro();
        fake.instances[0].onresult({ resultIndex: 0, results: [segment('bloc-notes, note', true)] });
        fake.instances[0].onend();
        maintenant += 41000;
        fake.instances[1].onend();
        attendreEgal(fermetures, 1, 'session fermée après le silence même sans dictée');
        attendreEgal(morceaux, [], 'rien accumulé');
        attendreEgal(texteStatut(), "Je n'ai rien noté, rien à enregistrer.", 'aucune entrée vide annoncée');
      });
    } finally {
      Date.now = originalNow;
      Object.assign(fichiersVocauxControleur, original);
    }
  });

  test('catalogue : 11 phrases, 4 catégories, actions exactes', () => {
    attendreEgal(PHRASES_CLAVIER.map(p => p.id),
      ['retrouver', 'dictionnaire', 'dernier-mail', 'agenda', 'ajouter-tache', 'rappel', 'resumer-mails', 'brouillon', 'reformuler', 'continuer', 'annuler'], 'identifiants');
    attendreEgal(PHRASES_CLAVIER.map(p => p.debut),
      ['Retrouve-moi...', 'Cherche dans mon dictionnaire...', 'Retrouve le dernier mail de...', "Qu'est-ce que j'ai le...", 'Ajoute à ma to-do...', 'Rappelle-moi de...', 'Résume mes mails de...', 'Prépare un brouillon de réponse à...', 'Reformule en plus...', 'Continue.', 'Annule.'], 'débuts');
    attendreEgal([...new Set(PHRASES_CLAVIER.map(p => p.categorie))], ['Retrouver', 'Agenda et to-do', 'Mails', 'Général'], 'catégories');
    attendreEgal(PHRASES_CLAVIER.filter(p => p.action !== '').map(p => [p.id, p.action]), [['ajouter-tache', 'ajouter_tache']], 'actions');
    attendreEgal(PHRASES_CLAVIER.filter(p => !p.a_completer).map(p => p.id), ['continuer', 'annuler'], 'phrases sans complément');
  });

  test('composerTexte : … ou ... retirés, complément garde ses caractères', () => {
    attendreEgal(composerTexte(PHRASES_CLAVIER.find(p => p.id === 'brouillon'), '  Marc Dupont  '),
      'Prépare un brouillon de réponse à Marc Dupont', 'points ASCII');
    attendreEgal(composerTexte({ debut: 'Retrouve-moi…' }, '  le pain  '), 'Retrouve-moi le pain', 'points Unicode');
    attendreEgal(composerTexte({ debut: 'Cherche  …' }, ''), 'Cherche', 'complément vide');
    attendreEgal(composerTexte({ debut: 'Reformule en plus...' }, ' Ça & "é" <b>x</b> ’ '),
      'Reformule en plus Ça & "é" <b>x</b> ’', 'complément exact');
  });

  test('ajouter-tache : complément dans À trier, origine et fictif exacts', () => {
    const clavier = traiterDemande({ texte: 'Ajoute à ma to-do... acheter du pain', source: 'clavier', id_phrase: 'ajouter-tache', complement: '  acheter du pain  ' });
    attendreEgal([clavier.tache.intitule, clavier.tache.categorie, clavier.tache.sous_categorie, clavier.tache.origine, clavier.tache.fictif],
      ['acheter du pain', 'À trier', '', 'ajout à la main', false], 'tâche clavier');
    attendreEgal(clavier.message, 'Ajoutée dans À trier : « acheter du pain »', 'message');
    const micro = traiterDemande({ texte: 'Ajoute à ma to-do... lait', source: 'micro', id_phrase: 'ajouter-tache', complement: 'lait' });
    attendreEgal([micro.tache.intitule, micro.tache.origine, micro.tache.fictif], ['lait', 'dictée', false], 'tâche micro');
  });

  test('saisie libre : intitulé mot pour mot, HTML non interprété, historique exact', () => {
    const texte = '  Note <i>vite</i> & "ça" ’  ';
    const resultat = traiterDemande({ texte, source: 'saisie' });
    attendreEgal([resultat.type, resultat.tache.intitule, resultat.tache.origine, resultat.tache.fictif],
      ['tache', 'Note <i>vite</i> & "ça" ’', 'ajout à la main', false], 'tâche');
    attendreEgal(resultat.message, 'Ajoutée dans À trier : « Note <i>vite</i> & "ça" ’ »', 'message');
    const historique = preferencesClavier.historique();
    attendreEgal(historique.length, 1, 'nombre d’entrées');
    attendreEgal([historique[0].texte, historique[0].id_phrase, historique[0].complement, historique[0].source],
      [texte, '', '', 'saisie'], 'champs historique');
    attendre(!Number.isNaN(Date.parse(historique[0].date)), 'date d’historique invalide');
  });

  test('Continuer et Annuler : pas de tâche, historique et usage enregistrés', () => {
    const avant = TACHES.length;
    const continuer = traiterDemande({ texte: 'Continue.', source: 'clavier', id_phrase: 'continuer' });
    attendreEgal([continuer.type, continuer.message],
      ['attente_cerveau', '« Continue. » marchera quand le cerveau de Cap sera branché.'], 'Continuer');
    const annuler = traiterDemande({ texte: 'Annule.', source: 'micro', id_phrase: 'annuler' });
    attendreEgal([annuler.type, annuler.message], ['annuler', ''], 'Annuler');
    attendreEgal(TACHES.length, avant, 'tâche créée');
    attendreEgal(preferencesClavier.plusUtilisees(5).map(p => p.id), ['continuer', 'annuler'], 'usages');
    attendreEgal(preferencesClavier.historique().map(e => [e.id_phrase, e.source, e.texte]),
      [['annuler', 'micro', 'Annule.'], ['continuer', 'clavier', 'Continue.']], 'historique');
  });

  test('demande vide : message exact, rien dans historique ni usage', () => {
    const avant = TACHES.length;
    attendreEgal(traiterDemande({ texte: '   ', source: 'micro' }), { type: 'vide', message: "Je n'ai rien entendu, réessaie." }, 'micro vide');
    attendreEgal(traiterDemande({ texte: ' ', source: 'saisie' }), { type: 'vide', message: "Je n'ai rien reçu, réessaie." }, 'saisie vide');
    attendreEgal(traiterDemande({ texte: 'Ajoute à ma to-do...', source: 'micro', id_phrase: 'ajouter-tache', complement: '   ' }),
      { type: 'vide', message: "Je n'ai rien entendu, réessaie." }, 'complément vide');
    attendreEgal(TACHES.length, avant, 'tâche créée');
    attendreEgal(preferencesClavier.historique(), [], 'historique');
    attendreEgal(preferencesClavier.plusUtilisees(5), [], 'usages');
  });

  test('compteurs : ordre décroissant, égalité dans l’ordre du catalogue, phrases utilisées seulement', () => {
    preferencesClavier.compterUtilisation('rappel');
    preferencesClavier.compterUtilisation('brouillon');
    preferencesClavier.compterUtilisation('retrouver');
    preferencesClavier.compterUtilisation('brouillon');
    preferencesClavier.compterUtilisation('retrouver');
    preferencesClavier.compterUtilisation('inconnue');
    attendreEgal(preferencesClavier.plusUtilisees(10).map(p => p.id), ['retrouver', 'brouillon', 'rappel'], 'ordre');
    attendreEgal(preferencesClavier.plusUtilisees(2).map(p => p.id), ['retrouver', 'brouillon'], 'limite');
    attendreEgal(preferencesClavier.plusUtilisees(0), [], 'limite nulle');
    attendreEgal(preferencesClavier.plusUtilisees(-3), [], 'limite négative');
    attendreEgal(JSON.parse(localStorage.getItem(CLE_USAGE)), { rappel: 1, brouillon: 2, retrouver: 2 }, 'stockage');
  });

  test('historique : 20 entrées maximum, plus récente en premier, champs exacts', () => {
    for (let i = 0; i <= 20; i++) {
      traiterDemande({ texte: `Demande ${i}`, source: 'saisie', id_phrase: 'rappel', complement: `c${i}` });
    }
    const historique = preferencesClavier.historique();
    attendreEgal(historique.length, 20, 'longueur');
    attendreEgal(historique[0].texte, 'Demande 20', 'plus récente');
    attendreEgal(historique[19].texte, 'Demande 1', 'plus ancienne conservée');
    attendreEgal(Object.keys(historique[0]).sort(), ['complement', 'date', 'id_phrase', 'source', 'texte'], 'champs');
    attendreEgal([historique[0].id_phrase, historique[0].complement, historique[0].source], ['rappel', 'c20', 'saisie'], 'valeurs');
    attendre(historique.every(e => Number.isFinite(Date.parse(e.date))), 'date invalide');
    attendreEgal(JSON.parse(localStorage.getItem(CLE_USAGE)).rappel, 21, 'usage');
  });

  test('réponse silencieuse : vrai par défaut, faux stocké et relu', () => {
    attendreEgal(preferencesClavier.silencieux(), true, 'défaut');
    preferencesClavier.definirSilencieux('non');
    attendreEgal(preferencesClavier.silencieux(), true, 'valeur non booléenne');
    attendreEgal(localStorage.getItem(CLE_SILENCE), null, 'rien stocké');
    preferencesClavier.definirSilencieux(false);
    attendreEgal(localStorage.getItem(CLE_SILENCE), 'false', 'stockage');
    attendreEgal(preferencesClavier.silencieux(), false, 'relecture');
  });

  test('préférences vides : valeurs par défaut', () => {
    attendreEgal([preferencesClavier.plusUtilisees(5), preferencesClavier.historique(), preferencesClavier.silencieux()],
      [[], [], true], 'valeurs par défaut');
  });

  test('données invalides : JSON cassé ou structure fausse, valeurs vides, tâches intactes', () => {
    const taches = JSON.stringify(TACHES);
    for (const brut of ['{pas json', '[1]', 'null', '{"rappel":-1}', '{"rappel":1.5}', '{"rappel":"2"}']) {
      localStorage.setItem(CLE_USAGE, brut);
      attendreEgal(preferencesClavier.plusUtilisees(5), [], `usages : ${brut}`);
    }
    for (const brut of ['{pas json', 'null', '[{"texte":"a"}]',
      '[{"texte":"a","id_phrase":"","complement":"","source":"autre","date":"2026-10-28T00:00:00.000Z"}]',
      '[{"texte":"a","id_phrase":"","complement":"","source":"saisie","date":"pas une date"}]']) {
      localStorage.setItem(CLE_HISTORIQUE, brut);
      attendreEgal(preferencesClavier.historique(), [], `historique : ${brut}`);
    }
    for (const brut of ['pas json', '"non"', '1', 'null']) {
      localStorage.setItem(CLE_SILENCE, brut);
      attendreEgal(preferencesClavier.silencieux(), true, `silencieux : ${brut}`);
    }
    attendreEgal(JSON.stringify(TACHES), taches, 'tâches modifiées');
  });

  test('localStorage refusé : lecture et écriture sans erreur, méthodes restaurées', () => {
    const getItemOriginal = Storage.prototype.getItem;
    const setItemOriginal = Storage.prototype.setItem;
    let lecture;
    Storage.prototype.getItem = function () { throw new Error('refus'); };
    try {
      lecture = [preferencesClavier.plusUtilisees(5), preferencesClavier.historique(), preferencesClavier.silencieux()];
    } finally {
      Storage.prototype.getItem = getItemOriginal;
    }
    attendreEgal(lecture, [[], [], true], 'lecture refusée');
    Storage.prototype.setItem = function () { throw new Error('refus'); };
    try {
      preferencesClavier.compterUtilisation('rappel');
      preferencesClavier.ajouterHistorique({ texte: 'Test', source: 'saisie' });
      preferencesClavier.definirSilencieux(false);
    } finally {
      Storage.prototype.setItem = setItemOriginal;
    }
    attendreEgal([localStorage.getItem(CLE_USAGE), localStorage.getItem(CLE_HISTORIQUE), localStorage.getItem(CLE_SILENCE)],
      [null, null, null], 'rien écrit');
  });

  test('demande : erreur de création propagée, ni historique ni usage', () => {
    const avant = TACHES.length;
    const original = stockage.enregistrer;
    stockage.enregistrer = () => { throw new Error('Simulation'); };
    try {
      attendreErreur(() => traiterDemande({ texte: 'Retrouve-moi la facture', source: 'clavier', id_phrase: 'retrouver', complement: 'la facture' }), 'Simulation');
    } finally {
      stockage.enregistrer = original;
    }
    attendreEgal(TACHES.length, avant, 'tâche restée');
    attendreEgal(preferencesClavier.historique(), [], 'historique');
    attendreEgal(preferencesClavier.plusUtilisees(5), [], 'usages');
  });

  function avecClavier(fonction) {
    const panneau = document.getElementById('clavier');
    document.getElementById('ouvrir-clavier').click();
    try {
      attendre(panneau.open, 'panneau non ouvert');
      document.getElementById('enlever-phrase').click();
      document.getElementById('saisie-demande').value = '';
      fonction(panneau, document.getElementById('saisie-demande'));
    } finally {
      panneau.close();
    }
  }

  function choisirDebut(debut) {
    const bouton = Array.from(document.querySelectorAll('#categories-clavier button'))
      .find(b => b.textContent === debut);
    attendre(bouton, `phrase absente : ${debut}`);
    bouton.click();
  }

  test('clavier : ouverture, catégories, grandes touches et silence mémorisé', () => {
    avecClavier(panneau => {
      attendreEgal(Array.from(panneau.querySelectorAll('#categories-clavier h3')).map(n => n.textContent),
        ['Retrouver', 'Agenda et to-do', 'Mails', 'Général'], 'catégories');
      attendreEgal(panneau.querySelectorAll('#categories-clavier button').length, 11, 'touches');
      attendreEgal(document.getElementById('section-plus-utilisees').hidden, true, 'favoris masqués');
      attendreEgal(document.getElementById('section-historique').hidden, true, 'historique masqué');
      for (const bouton of panneau.querySelectorAll('button')) {
        attendre(parseFloat(getComputedStyle(bouton).minHeight) >= 56, 'touche trop petite');
      }
      const interrupteur = document.getElementById('reponse-silencieuse');
      attendreEgal(interrupteur.getAttribute('aria-checked'), 'true', 'silence par défaut');
      interrupteur.click();
      attendreEgal(preferencesClavier.silencieux(), false, 'silence changé');
      panneau.close();
      document.getElementById('ouvrir-clavier').click();
      attendreEgal(interrupteur.getAttribute('aria-checked'), 'false', 'silence relu');
    });
  });

  test('clavier : compléter, envoyer, fermer et afficher la tâche avec Annuler', () => {
    avecClavier((panneau, saisie) => {
      choisirDebut('Ajoute à ma to-do...');
      attendre(document.activeElement === saisie, 'focus champ');
      attendreEgal(document.getElementById('debut-phrase').textContent, 'Ajoute à ma to-do...', 'début choisi');
      saisie.value = 'acheter du pain';
      document.getElementById('formulaire-demande').requestSubmit();
      attendre(!panneau.open, 'panneau encore ouvert');
      attendreEgal(saisie.value, '', 'champ non vidé');
      attendre(document.getElementById('phrase-selectionnee').hidden, 'phrase non vidée');
      attendre(Array.from(document.querySelectorAll('#liste-taches .intitule')).some(n => n.textContent === 'acheter du pain'), 'tâche non visible');
      attendreEgal(texteStatut(), 'Ajoutée dans À trier : « acheter du pain »', 'annonce');
      const bouton = document.querySelector('#statut .annuler-dictee');
      attendre(bouton, 'Annuler absent');
      bouton.click();
      attendreEgal(TACHES.find(t => t.intitule === 'acheter du pain').abandonnee_le, dateDuJour(), 'abandon sans perte');
    });
  });

  test('clavier : phrase composée et saisie libre affichées sans HTML interprété', () => {
    avecClavier((panneau, saisie) => {
      choisirDebut('Retrouve-moi...');
      saisie.value = 'le mail <b>FICTIF</b>';
      document.getElementById('formulaire-demande').requestSubmit();
      attendreEgal(preferencesClavier.historique()[0].texte, 'Retrouve-moi le mail <b>FICTIF</b>', 'composition');
      document.getElementById('ouvrir-clavier').click();
      saisie.value = '<i>FICTIF</i> & texte libre';
      document.getElementById('formulaire-demande').requestSubmit();
      attendreEgal(TACHES.at(-1).intitule, '<i>FICTIF</i> & texte libre', 'texte libre');
      attendreEgal(preferencesClavier.historique()[0].source, 'saisie', 'origine libre');
      attendre(!document.querySelector('#liste-taches b, #liste-taches i'), 'HTML interprété');
    });
  });

  test('clavier : historique relancé à l’identique, favoris et limites affichées', () => {
    for (let i = 0; i < 12; i++) {
      preferencesClavier.ajouterHistorique({ texte: `Retrouve-moi FICTIF ${i}`, source: 'clavier', id_phrase: 'retrouver', complement: `FICTIF ${i}` });
    }
    for (const phrase of PHRASES_CLAVIER.slice(0, 6)) preferencesClavier.compterUtilisation(phrase.id);
    avecClavier(panneau => {
      attendreEgal(document.querySelectorAll('#plus-utilisees button').length, 4, '4 favoris maximum');
      attendreEgal(document.querySelectorAll('#historique-demandes button').length, 10, '10 demandes maximum');
      const avant = preferencesClavier.historique()[0];
      const bouton = document.querySelector('#historique-demandes button');
      attendreEgal(bouton.textContent, avant.texte, 'texte affiché');
      bouton.click();
      attendre(!panneau.open, 'panneau encore ouvert');
      const apres = preferencesClavier.historique()[0];
      for (const champ of ['texte', 'source', 'id_phrase', 'complement']) attendreEgal(apres[champ], avant[champ], champ);
      attendreEgal(TACHES.at(-1).intitule, avant.texte, 'tâche relancée');
    });
  });

  test('clavier : Continue envoyé immédiatement sans tâche', () => {
    avecClavier(panneau => {
      const avant = TACHES.length;
      choisirDebut('Continue.');
      attendre(!panneau.open, 'panneau non fermé');
      attendreEgal(TACHES.length, avant, 'tâche créée');
      attendreEgal(texteStatut(), '« Continue. » marchera quand le cerveau de Cap sera branché.', 'message');
      attendre(!document.querySelector('#statut .annuler-dictee'), 'Annuler inapproprié');
    });
  });

  test('clavier : erreur conserve panneau, complément et phrase sélectionnée', () => {
    avecClavier((panneau, saisie) => {
      choisirDebut('Ajoute à ma to-do...');
      saisie.value = 'FICTIF à conserver';
      const original = stockage.enregistrer;
      stockage.enregistrer = () => { throw new Error('Simulation clavier'); };
      try {
        document.getElementById('formulaire-demande').requestSubmit();
        attendre(panneau.open, 'panneau fermé malgré erreur');
        attendreEgal(saisie.value, 'FICTIF à conserver', 'texte perdu');
        attendre(!document.getElementById('phrase-selectionnee').hidden, 'phrase perdue');
        const erreur = panneau.querySelector('.erreur');
        attendre(!erreur.hidden && erreur.textContent.includes('Simulation clavier'), 'erreur absente');
        attendreEgal(preferencesClavier.historique(), [], 'historique après erreur');
      } finally {
        stockage.enregistrer = original;
      }
    });
  });

  test('clavier : demande vide et complément manquant gardent le panneau', () => {
    avecClavier((panneau, saisie) => {
      const avant = TACHES.length;
      saisie.value = '  ';
      document.getElementById('formulaire-demande').requestSubmit();
      attendre(panneau.open, 'panneau fermé sur vide');
      choisirDebut('Retrouve-moi...');
      document.getElementById('formulaire-demande').requestSubmit();
      attendre(panneau.open, 'panneau fermé sans complément');
      attendreEgal(TACHES.length, avant, 'tâche vide créée');
      attendreEgal(preferencesClavier.historique(), [], 'historique vide');
      document.getElementById('enlever-phrase').click();
      attendre(document.getElementById('phrase-selectionnee').hidden, 'phrase non enlevée');
    });
  });

  test('micro : porte d’entrée commune alimente l’historique sans phrase', () => {
    sessionMicro(fake => {
      cliquerMicro();
      fake.instances[0].onresult({ resultIndex: 0, results: [segment('FICTIF micro commun', true)] });
      const entree = preferencesClavier.historique()[0];
      attendreEgal([entree.texte, entree.source, entree.id_phrase, entree.complement],
        ['FICTIF micro commun', 'micro', '', ''], 'historique micro');
    });
  });

  function nettoyerGoogle() {
    for (const espace of [localStorage, sessionStorage]) {
      for (const cle of Object.keys(espace)) {
        if (cle.startsWith('cap_google_')) espace.removeItem(cle);
      }
    }
  }

  function espaceMemoire() {
    const valeurs = new Map();
    return {
      getItem: cle => valeurs.has(cle) ? valeurs.get(cle) : null,
      setItem: (cle, valeur) => valeurs.set(cle, String(valeur)),
      removeItem: cle => valeurs.delete(cle)
    };
  }

  function objetIsole(source, nom, parametres) {
    return new Function(...Object.keys(parametres), source + `\nreturn ${nom};`)(...Object.values(parametres));
  }

  function contexteGoogle() {
    const contexte = {
      localStorage: espaceMemoire(), sessionStorage: espaceMemoire(), window: new EventTarget(),
      navigator: { onLine: true }, requetes: [], redirections: [], historiques: [],
      intervalles: [], delais: new Map(), cadres: [], maintenant: Date.now(),
      location: { hash: '', pathname: '/tests.html', search: '?fictif=1' }
    };
    contexte.Date = class extends Date { static now() { return contexte.maintenant; } };
    contexte.setInterval = (rappel, delai) => contexte.intervalles.push({ rappel, delai });
    let prochainDelai = 0;
    contexte.setTimeout = (rappel, delai) => {
      contexte.delais.set(++prochainDelai, { rappel, delai });
      return prochainDelai;
    };
    contexte.clearTimeout = id => contexte.delais.delete(id);
    contexte.location.assign = adresse => contexte.redirections.push(new URL(adresse));
    contexte.history = { replaceState: (...argumentsAppel) => {
      contexte.historiques.push(argumentsAppel);
      contexte.location.hash = '';
    } };
    contexte.repondre = async () => { throw new Error('Requête simulée non prévue'); };
    contexte.fetch = async (adresse, options = {}) => {
      const requete = { url: new URL(adresse), methode: options.method || 'GET', options,
        corps: (() => { try { return options.body ? JSON.parse(options.body) : null; } catch (e) { return null; } })() };
      contexte.requetes.push(requete);
      // Faux Drive pour l'identifiant de l'agenda (appProperties du tableau des tâches FICTIF).
      if (requete.url.pathname === '/drive/v3/files/tableau-agenda-fictif') {
        if (requete.methode === 'PATCH') Object.assign(contexte.proprietesDrive, requete.corps.appProperties);
        return reponseGoogle(requete.methode === 'PATCH' ? { id: 'tableau-agenda-fictif' }
          : { appProperties: { ...contexte.proprietesDrive } });
      }
      return contexte.repondre(requete);
    };
    contexte.proprietesDrive = {};
    contexte.tableauAgenda = { trouverOuCreer: async () => ({ id: 'tableau-agenda-fictif', cree: false }) };
    contexte.googleConnexion = { connecte: () => true, appeler: contexte.fetch };
    contexte.stockage = objetIsole(SOURCE_STOCKAGE, 'stockage', {
      localStorage: contexte.localStorage, TACHES_FICTIVES
    });
    contexte.stockage.charger();
    contexte.TACHES = TACHES_FICTIVES.filter(tache => !tache.parente).slice(0, 3).map(tache => ({ ...tache }));
    contexte.stockage.enregistrer(contexte.TACHES);
    contexte.connexion = () => objetIsole(SOURCE_GOOGLE_CONNEXION, 'googleConnexion', {
      localStorage: contexte.localStorage, sessionStorage: contexte.sessionStorage,
      window: contexte.window, location: contexte.location, history: contexte.history,
      fetch: contexte.fetch, REGLAGES_GOOGLE, crypto, navigator: contexte.navigator, Date: contexte.Date
    });
    contexte.sheets = () => objetIsole(SOURCE_GOOGLE_SHEETS, 'googleSheets', {
      localStorage: contexte.localStorage, googleConnexion: contexte.googleConnexion,
      REGLAGES_GOOGLE, TACHES: contexte.TACHES, stockage: contexte.stockage,
      ETAPES_PAR_DEFAUT, PHRASES_CLAVIER, window: contexte.window
    });
    contexte.sync = googleSheets => objetIsole(SOURCE_SYNCHRONISATION, 'synchronisation', {
      localStorage: contexte.localStorage, window: contexte.window, navigator: contexte.navigator,
      googleConnexion: contexte.googleConnexion, googleSheets, TACHES: contexte.TACHES,
      stockage: contexte.stockage, setInterval: contexte.setInterval, Date: contexte.Date
    });
    contexte.agenda = () => objetIsole(SOURCE_GOOGLE_AGENDA, 'googleAgenda', {
      localStorage: contexte.localStorage, googleConnexion: contexte.googleConnexion, REGLAGES_GOOGLE,
      navigator: contexte.navigator, googleSheets: contexte.tableauAgenda
    });
    return contexte;
  }

  function reponseGoogle(contenu, statut = 200) {
    return new Response(JSON.stringify(contenu), { status: statut, headers: { 'Content-Type': 'application/json' } });
  }

  async function attendreRejet(fonction, fragment) {
    let message = '';
    try { await fonction(); } catch (erreur) { message = String(erreur.message || erreur); }
    attendre(message.includes(fragment), `rejet attendu contenant « ${fragment} », reçu : ${message}`);
  }

  async function testAsync(nom, fonction) {
    let contexte;
    try {
      nettoyerGoogle();
      reinitialiser();
      contexte = contexteGoogle();
      await fonction(contexte);
      for (const requete of contexte.requetes) {
        const patchAgendaFictif = requete.methode === 'PATCH' && contexte.agendaModifiable
          && requete.url.origin === 'https://www.googleapis.com'
          && requete.url.pathname === `/calendar/v3/calendars/${encodeURIComponent(contexte.agendaModifiable)}/events/rdv-fictif`
          && contexte.agendaModifiable !== 'primary';
        // Seule autre modification permise : ranger l'identifiant de l'agenda ou du dossier des scans
        // en information invisible du tableau (appProperties), une seule clé connue à la fois, sans
        // toucher au contenu, au nom ni à rien d'autre du fichier.
        const clesRangees = ['["cap_agenda_id"]', '["cap_dossier_documents_personnels"]',
          '["cap_fichier_architecture"]', '["cap_fichier_tableur_classement"]',
          '["cap_dossier_journaux"]', '["cap_journal_numerisation"]', '["cap_journal_general"]'];
        const patchIdentifiantAgenda = requete.methode === 'PATCH'
          && requete.url.origin === 'https://www.googleapis.com'
          && requete.url.pathname.startsWith('/drive/v3/files/')
          && JSON.stringify(Object.keys(requete.corps || {})) === '["appProperties"]'
          && clesRangees.includes(JSON.stringify(Object.keys(requete.corps.appProperties || {})));
        const patchReparationRelations = contexte.reparationRelations === true && requete.methode === 'PATCH'
          && requete.url.origin === 'https://www.googleapis.com' && /^\/upload\/drive\/v3\/files\/[^/]+$/.test(requete.url.pathname)
          && requete.url.searchParams.get('uploadType') === 'media';
        attendre(['GET', 'POST'].includes(requete.methode) || patchAgendaFictif || patchIdentifiantAgenda || patchReparationRelations,
          'opération destructive interdite');
        attendre(!/:clear(?:\?|$)|:batchClear(?:\?|$)/.test(requete.url.href), 'effacement interdit');
        attendre(!requete.corps?.requests?.some(action => Object.keys(action).some(cle => /delete|cutPaste/i.test(cle))),
          'suppression de lignes ou de feuilles interdite');
      }
      resultats.push({ nom, ok: true, erreur: '' });
    } catch (erreur) {
      resultats.push({ nom, ok: false, erreur: String(erreur.message || erreur) });
    } finally {
      for (const cadre of contexte?.cadres || []) cadre.remove();
      nettoyerGoogle();
    }
  }

  const CHAMPS_GOOGLE = ['id', 'intitule', 'categorie', 'sous_categorie', 'fait', 'date_entree',
    'echeance', 'date_realisation', 'priorite', 'parente', 'note', 'avant_le', 'abandonnee_le', 'origine', 'fictif'];
  const ENTETES_GOOGLE = ['Identifiant', 'Intitulé', 'Catégorie', 'Sous-catégorie', 'Fait', "Date d'entrée",
    'Échéance', 'Date de réalisation', 'Priorité', 'Tâche parente', 'Note', 'Avant le', 'Abandonnée le', 'Origine', 'Fictif'];
  const ligneGoogle = tache => CHAMPS_GOOGLE.map(champ => tache[champ]);
  const lireFileGoogle = contexte => JSON.parse(contexte.localStorage.getItem('cap_google_file_v1') || '[]');

  for (const espace of ['sessionStorage', 'localStorage']) {
    await testAsync(`Google OAuth : retour valide avec état en ${espace}`, async c => {
      c[espace].setItem('cap_google_etat_v1', 'etat-fictif');
      c.location.hash = '#access_token=jeton-fictif&expires_in=3600&token_type=Bearer&state=etat-fictif';
      const connexion = c.connexion();
      attendre(connexion.connecte(), 'connexion refusée');
      attendreEgal(connexion.jeton(), 'jeton-fictif', 'jeton');
      attendreEgal(c.location.hash, '', 'fragment effacé');
      attendreEgal(c.historiques, [[null, '', '/tests.html?fictif=1']], 'URL nettoyée sans navigation');
      for (const stockageEtat of [c.localStorage, c.sessionStorage]) {
        attendreEgal(stockageEtat.getItem('cap_google_etat_v1'), null, 'état consommé');
      }
      attendreEgal(c.requetes.length, 0, 'aucun réseau au retour OAuth');
    });
  }

  await testAsync('Google OAuth : mauvais état refusé et fragment effacé', async c => {
    c.sessionStorage.setItem('cap_google_etat_v1', 'attendu-fictif');
    c.localStorage.setItem('cap_google_jeton_v1', JSON.stringify({ jeton: 'ancien-fictif', expiration: Date.now() + 3600000 }));
    c.location.hash = '#access_token=intrus-fictif&expires_in=3600&token_type=Bearer&state=incorrect-fictif';
    const connexion = c.connexion();
    attendre(!connexion.connecte(), 'mauvais état accepté');
    attendre(connexion.message().includes('sécurité'), 'erreur de sécurité absente');
    attendreEgal(c.localStorage.getItem('cap_google_jeton_v1'), null, 'ancien jeton retiré');
    attendreEgal(c.sessionStorage.getItem('cap_google_etat_v1'), null, 'état retiré');
    attendreEgal(c.location.hash, '', 'fragment retiré même en erreur');
    attendreEgal(c.historiques.length, 1, 'nettoyage du fragment');
  });

  await testAsync('Google OAuth : redirection et nouvel état aléatoire', async c => {
    const connexion = c.connexion();
    connexion.seConnecter();
    connexion.seConnecter();
    attendreEgal(c.redirections.length, 2, 'redirections simulées');
    const [premiere, seconde] = c.redirections;
    attendreEgal(seconde.origin + seconde.pathname, 'https://accounts.google.com/o/oauth2/v2/auth', 'destination OAuth');
    const parametres = seconde.searchParams;
    for (const [cle, valeur] of Object.entries({ client_id: REGLAGES_GOOGLE.id_client,
      redirect_uri: REGLAGES_GOOGLE.adresse_retour, response_type: 'token',
      scope: REGLAGES_GOOGLE.autorisations.join(' '), include_granted_scopes: 'true' })) {
      attendreEgal(parametres.get(cle), valeur, `paramètre ${cle}`);
    }
    attendre(/^[a-f0-9]{64}$/.test(parametres.get('state')), 'état insuffisant');
    attendre(premiere.searchParams.get('state') !== parametres.get('state'), 'état réutilisé');
    for (const espace of [c.localStorage, c.sessionStorage]) {
      attendreEgal(espace.getItem('cap_google_etat_v1'), parametres.get('state'), 'état enregistré');
    }
    attendre(!parametres.has('client_secret'), 'secret dans la redirection');
    attendreEgal(c.requetes.length, 0, 'aucun fetch de connexion');
  });

  await testAsync('Google connexion : Response, statut HTTP et destinations autorisées', async c => {
    c.localStorage.setItem('cap_google_jeton_v1', JSON.stringify({ jeton: 'jeton-fictif', expiration: Date.now() + 3600000 }));
    const connexion = c.connexion();
    c.repondre = async () => reponseGoogle({ fictif: true });
    const reponse = await connexion.appeler('https://www.googleapis.com/drive/v3/files');
    attendre(reponse instanceof Response, 'Response non renvoyée');
    attendreEgal(await reponse.json(), { fictif: true }, 'contenu réponse');
    attendreEgal(c.requetes[0].options.headers.get('Authorization'), 'Bearer jeton-fictif', 'autorisation');
    attendreEgal(c.requetes[0].options.cache, 'no-store', 'jeton hors cache');
    attendreEgal(c.requetes[0].options.redirect, 'error', 'redirections interdites');
    c.repondre = async () => reponseGoogle({}, 403);
    let statut;
    try { await connexion.appeler('https://sheets.googleapis.com/v4/spreadsheets'); }
    catch (erreur) { statut = erreur.statut; }
    attendreEgal(statut, 403, 'statut HTTP conservé');
    const nombre = c.requetes.length;
    await attendreRejet(() => connexion.appeler('http://www.googleapis.com/drive/v3/files'), 'non autorisée');
    await attendreRejet(() => connexion.appeler('https://accounts.google.com/o/oauth2/v2/auth'), 'non autorisée');
    attendreEgal(c.requetes.length, nombre, 'destinations interdites jamais appelées');
  });

  await testAsync('Google Sheets : création RAW, entêtes, trois onglets et cases booléennes', async c => {
    c.repondre = async r => {
      if (r.methode === 'GET' && r.url.pathname === '/drive/v3/files') return reponseGoogle({ files: [] });
      if (r.methode === 'POST' && r.url.pathname === '/v4/spreadsheets') return reponseGoogle({ spreadsheetId: 'tableau-fictif' });
      if (r.methode === 'POST' && ['/v4/spreadsheets/tableau-fictif/values:batchUpdate', '/v4/spreadsheets/tableau-fictif:batchUpdate'].includes(r.url.pathname)) return reponseGoogle({});
      throw new Error(`Requête inattendue : ${r.url}`);
    };
    const sheets = c.sheets();
    attendreEgal(await sheets.trouverOuCreer(), { id: 'tableau-fictif', cree: true }, 'tableau créé');
    const creation = c.requetes.find(r => r.url.pathname === '/v4/spreadsheets').corps;
    attendreEgal(creation.properties.title, REGLAGES_GOOGLE.nom_fichier_taches, 'nom fictif');
    attendreEgal(creation.sheets.map(onglet => onglet.properties.title), Object.values(REGLAGES_GOOGLE.onglets), 'trois onglets');
    attendre(creation.sheets.every(onglet => onglet.properties.gridProperties.frozenRowCount === 1), 'entêtes non figées');
    const remplissage = c.requetes.find(r => r.url.pathname.endsWith('/values:batchUpdate')).corps;
    attendreEgal(remplissage.valueInputOption, 'RAW', 'écriture brute');
    attendreEgal(remplissage.data.length, 6, 'six onglets remplis');
    attendreEgal(remplissage.data[0].values, [ENTETES_GOOGLE, ...c.TACHES.map(ligneGoogle)], 'entêtes et tâches exactes');
    attendreEgal(remplissage.data[1].values, [['Modèle', 'Étape', 'Retirée le', 'Modifiée le'], ...Object.entries(ETAPES_PAR_DEFAUT).flatMap(([modele, etapes]) => etapes.map(etape => [modele, etape, '', '']))], 'modèles');
    attendreEgal(remplissage.data[2].values, [['Catégorie', 'Sous-catégorie de', 'Couleur', 'Retirée le', 'Modifiée le', 'Ordre']], 'catégories');
    attendreEgal(remplissage.data[3].values, [['Date et heure', 'Venu de', 'Ce que Max a dit ou touché', 'Ce que Cap a compris', 'Ce que Cap a fait']], 'journal');
    attendreEgal(remplissage.data[4].values, [['Identifiant', 'Catégorie', 'Début', 'À compléter', 'Action'], ...PHRASES_CLAVIER.map(p => [p.id, p.categorie, p.debut, p.a_completer, p.action])], 'phrases');
    attendreEgal(remplissage.data[5].values, [['Identifiant', 'Prénom', 'Nom', 'Type', 'Rôle', 'Lien avec Max', 'Appellations et surnoms',
      'Coordonnées', 'Téléphone', 'Mail', 'Domaine', 'Note pour IA', 'Date de naissance / anniversaire', 'Adresse postale',
      'Deuxième téléphone', 'Deuxième mail', 'Fonction / titre', 'Site web', 'Note', 'Supprimé le', 'Modifié le', 'Historique']], 'annuaire');
    const validations = c.requetes.find(r => r.url.pathname.endsWith('tableau-fictif:batchUpdate')).corps.requests;
    attendreEgal(validations.map(r => r.setDataValidation.range.startColumnIndex), [4, 14], 'colonnes booléennes');
    attendre(validations.every(r => r.setDataValidation.rule.condition.type === 'BOOLEAN' && r.setDataValidation.rule.strict), 'validation booléenne');
    attendreEgal(c.localStorage.getItem('cap_google_fichier_v1'), 'tableau-fictif', 'identifiant conservé');
  });

  async function sheetsExistant(c, lignes) {
    c.localStorage.setItem('cap_google_fichier_v1', 'tableau-fictif');
    c.repondre = async r => {
      if (r.methode === 'GET' && r.url.pathname === '/drive/v3/files/tableau-fictif') return reponseGoogle({ id: 'tableau-fictif', trashed: false });
      if (r.methode === 'GET' && r.url.pathname.startsWith('/v4/spreadsheets/tableau-fictif/values/')) {
        attendreEgal(r.url.searchParams.get('valueRenderOption'), 'UNFORMATTED_VALUE', 'lecture sans formatage');
        return reponseGoogle({ values: [ENTETES_GOOGLE, ...lignes] });
      }
      if (r.methode === 'POST' && (r.url.pathname.endsWith('/values:batchUpdate') || r.url.pathname.endsWith(':append'))) return reponseGoogle({});
      throw new Error(`Requête inattendue : ${r.url}`);
    };
    const sheets = c.sheets();
    attendreEgal(await sheets.trouverOuCreer(), { id: 'tableau-fictif', cree: false }, 'tableau retrouvé');
    return sheets;
  }

  await testAsync('Google Sheets : mise à jour ligne existante et append sans effacement', async c => {
    const [existante, nouvelle] = c.TACHES;
    const sheets = await sheetsExistant(c, [[], ligneGoogle(existante)]);
    const modifiee = { ...existante, intitule: '=FICTIF <b>texte exact</b>' };
    attendreEgal(await sheets.ecrireTaches([modifiee, nouvelle]), [existante.id, nouvelle.id], 'identifiants écrits');
    const misesAJour = c.requetes.filter(r => r.methode === 'POST');
    attendreEgal(misesAJour.length, 2, 'update et append seulement');
    attendreEgal(misesAJour[0].corps, { valueInputOption: 'RAW', data: [{ range: "'Tâches'!A3:O3", values: [ligneGoogle(modifiee)] }] }, 'ligne exacte mise à jour');
    attendreEgal(misesAJour[1].url.searchParams.get('valueInputOption'), 'RAW', 'append brut');
    attendreEgal(misesAJour[1].url.searchParams.get('insertDataOption'), 'INSERT_ROWS', 'ajout sans écraser');
    attendreEgal(misesAJour[1].corps.values, [ligneGoogle(nouvelle)], 'nouvelle tâche exacte');
  });

  await testAsync('Google Sheets : lignes illisibles, doublons et parents protégés', async c => {
    const [parent, doublon, invalide] = c.TACHES;
    const enfant = { ...parent, id: 'enfant-fictif', intitule: 'Étape FICTIF', parente: parent.id };
    const orpheline = { ...parent, id: 'orpheline-fictive', parente: 'parent-inconnu-fictif' };
    const lignes = [ligneGoogle(parent), ligneGoogle(doublon), ligneGoogle(doublon),
      ligneGoogle({ ...invalide, fait: 'illisible' }), ligneGoogle(enfant), ligneGoogle(orpheline)];
    const sheets = await sheetsExistant(c, lignes);
    const lecture = await sheets.lireTaches();
    attendreEgal(lecture.taches.map(t => t.id), [parent.id, enfant.id], 'seules les lignes valides admises');
    attendreEgal([...lecture.lignes], [[parent.id, 2], [enfant.id, 6]], 'numéros de lignes');
    attendreEgal(lecture.illisibles.map(l => l.ligne).sort((a, b) => a - b), [3, 4, 5, 7], 'lignes protégées');
    attendreEgal(await sheets.ecrireTaches([parent, doublon, invalide, orpheline]), [parent.id], 'seule la tâche saine écrite');
    const ecritures = c.requetes.filter(r => r.methode === 'POST');
    attendreEgal(ecritures.length, 1, 'aucun append des identifiants protégés');
    attendreEgal(ecritures[0].corps.data.map(d => d.range), ["'Tâches'!A2:O2"], 'aucune ligne illisible touchée');
  });

  await testAsync('Google Sheets : entêtes illisibles bloquent toute écriture', async c => {
    const sheets = await sheetsExistant(c, []);
    c.repondre = async () => reponseGoogle({ values: [['Entêtes FICTIF incorrectes']] });
    await attendreRejet(() => sheets.ecrireTaches(c.TACHES), 'colonnes');
    attendreEgal(c.requetes.filter(r => r.methode !== 'GET').length, 0, 'aucune écriture');
  });

  function fauxSheetsSync(c, distantes, illisibles = []) {
    const envois = [];
    return {
      envois,
      trouverOuCreer: async () => ({ id: 'tableau-fictif', cree: false }),
      lireTaches: async () => ({ taches: distantes.map(t => ({ ...t })), illisibles,
        lignes: new Map(distantes.map((t, indice) => [t.id, indice + 2])) }),
      ecrireTaches: async taches => { envois.push(taches.map(t => ({ ...t }))); return taches.map(t => t.id); }
    };
  }

  await testAsync('Google sync : fusion remote hors file, local en file et zéro perte', async c => {
    const [horsFile, enFile, absente] = c.TACHES;
    const inconnue = { ...horsFile, id: 'distante-fictive', intitule: 'Inconnue locale FICTIF' };
    const protege = { ...horsFile, id: 'protegee-fictive' };
    c.TACHES.push(protege);
    c.stockage.enregistrer(c.TACHES);
    c.localStorage.setItem('cap_google_file_v1', JSON.stringify([enFile.id]));
    const sheets = fauxSheetsSync(c, [{ ...horsFile, note: 'Google FICTIF' },
      { ...enFile, note: 'Ancienne version Google FICTIF' }, inconnue], [{ id: protege.id, ligne: 9 }]);
    const sync = c.sync(sheets);
    await sync.demarrer();
    attendreEgal(c.TACHES.find(t => t.id === horsFile.id).note, 'Google FICTIF', 'Google gagne hors file');
    attendreEgal(c.TACHES.find(t => t.id === enFile.id), enFile, 'local gagne en file');
    attendreEgal(c.TACHES.find(t => t.id === inconnue.id), inconnue, 'inconnue importée');
    attendreEgal(c.TACHES.find(t => t.id === absente.id), absente, 'absente conservée');
    attendreEgal(c.TACHES.find(t => t.id === protege.id), protege, 'illisible distante ne retire pas le local');
    attendreEgal(c.TACHES.length, 5, 'aucune tâche perdue');
    attendreEgal(sheets.envois.flat().map(t => t.id).sort(), [enFile.id, absente.id].sort(), 'absente et file envoyées, protégée ignorée');
    attendreEgal(lireFileGoogle(c), [], 'file acquittée');
    attendreEgal(JSON.parse(c.localStorage.getItem(CLE)), c.TACHES, 'fusion sauvegardée');
    attendre(sync.etat().includes('illisibles'), 'avertissement des lignes illisibles');
  });

  await testAsync('Google sync : échec de validation, mémoire et sauvegarde intactes', async c => {
    const avant = JSON.stringify(c.TACHES);
    const sauvegarde = c.localStorage.getItem(CLE);
    c.localStorage.setItem('cap_google_file_v1', JSON.stringify([c.TACHES[1].id]));
    const queue = c.localStorage.getItem('cap_google_file_v1');
    const sheets = fauxSheetsSync(c, [{ ...c.TACHES[0], parente: 'parent-absent-fictif' }]);
    const sync = c.sync(sheets);
    await sync.demarrer();
    attendreEgal(JSON.stringify(c.TACHES), avant, 'mémoire inchangée');
    attendreEgal(c.localStorage.getItem(CLE), sauvegarde, 'sauvegarde inchangée');
    attendreEgal(c.localStorage.getItem('cap_google_file_v1'), queue, 'file inchangée');
    attendreEgal(sheets.envois.length, 0, 'aucun envoi après validation refusée');
    attendre(sync.etat().includes('interrompue'), 'erreur visible');
  });

  await testAsync('Google sync : panne réseau garde la file puis reprise sans perte', async c => {
    const sheets = fauxSheetsSync(c, c.TACHES);
    const sync = c.sync(sheets);
    await sync.demarrer();
    const envoyer = sheets.ecrireTaches;
    sheets.ecrireTaches = async () => { throw new TypeError('Réseau FICTIF indisponible'); };
    c.navigator.onLine = false;
    sync.signaler([c.TACHES[0].id, c.TACHES[0].id]);
    attendreEgal(lireFileGoogle(c), [c.TACHES[0].id], 'file dédupliquée hors connexion');
    c.navigator.onLine = true;
    await sync.envoyer();
    attendreEgal(lireFileGoogle(c), [c.TACHES[0].id], 'file conservée après panne');
    attendre(sync.etat().includes('attente'), 'panne annoncée');
    sheets.ecrireTaches = envoyer;
    await sync.envoyer();
    attendreEgal(lireFileGoogle(c), [], 'file vidée après succès');
    attendreEgal(sheets.envois.flat().map(t => t.id), [c.TACHES[0].id], 'tâche envoyée une fois avec succès');
    attendreEgal(sync.etat(), 'synchronisé', 'reprise terminée');
  });

  await testAsync('Google sync : fetch échoue, file persistante puis retour en ligne', async c => {
    c.localStorage.setItem('cap_google_jeton_v1', JSON.stringify({ jeton: 'jeton-fictif', expiration: Date.now() + 3600000 }));
    c.googleConnexion = c.connexion();
    const sheets = await sheetsExistant(c, c.TACHES.map(ligneGoogle));
    const repondre = c.repondre;
    const sync = c.sync(sheets);
    await sync.demarrer();
    c.navigator.onLine = false;
    sync.signaler([c.TACHES[0].id]);
    c.repondre = async () => { throw new TypeError('Fetch FICTIF interrompu'); };
    c.navigator.onLine = true;
    await sync.envoyer();
    attendreEgal(lireFileGoogle(c), [c.TACHES[0].id], 'file persistante après fetch refusé');
    const nouvelleSession = c.sync(c.sheets());
    c.repondre = repondre;
    c.window.dispatchEvent(new Event('online'));
    await nouvelleSession.demarrer();
    await sync.envoyer();
    attendreEgal(lireFileGoogle(c), [], 'file reprise et acquittée');
    attendre(c.requetes.some(r => r.methode === 'POST' && r.url.pathname.endsWith('/values:batchUpdate')), 'écriture Google simulée absente');
  });

  await testAsync('Google sync : verrou et nouvelle version pendant un envoi', async c => {
    const sheets = fauxSheetsSync(c, c.TACHES);
    const sync = c.sync(sheets);
    await sync.demarrer();
    c.navigator.onLine = false;
    sync.signaler([c.TACHES[0].id]);
    let terminer;
    const appels = [];
    sheets.ecrireTaches = async taches => {
      appels.push(taches.map(tache => ({ ...tache })));
      if (appels.length === 1) await new Promise(resolve => { terminer = resolve; });
      return taches.map(tache => tache.id);
    };
    c.navigator.onLine = true;
    const premier = sync.envoyer();
    const second = sync.envoyer();
    attendre(premier === second, 'deux envois concurrents');
    await Promise.resolve();
    c.TACHES[0].note = 'Nouvelle note FICTIF pendant l’envoi';
    c.stockage.enregistrer(c.TACHES);
    sync.signaler([c.TACHES[0].id]);
    terminer();
    await premier;
    attendreEgal(appels.length, 2, 'la nouvelle version doit être envoyée séparément');
    attendreEgal(appels[1][0].note, c.TACHES[0].note, 'dernière version conservée');
    attendreEgal(lireFileGoogle(c), [], 'seule la dernière version réussie acquittée');
  });

  await testAsync('Google sync : 401 retire le jeton mais conserve la file', async c => {
    c.localStorage.setItem('cap_google_jeton_v1', JSON.stringify({ jeton: 'jeton-fictif', expiration: Date.now() + 3600000 }));
    c.googleConnexion = c.connexion();
    const sheets = fauxSheetsSync(c, c.TACHES);
    const sync = c.sync(sheets);
    await sync.demarrer();
    c.navigator.onLine = false;
    sync.signaler([c.TACHES[0].id]);
    c.navigator.onLine = true;
    let deconnexions = 0;
    c.window.addEventListener('cap-google-deconnecte', () => deconnexions++);
    c.repondre = async () => reponseGoogle({}, 401);
    sheets.ecrireTaches = async () => c.googleConnexion.appeler('https://sheets.googleapis.com/v4/spreadsheets/tableau-fictif');
    const avant = JSON.stringify(c.TACHES);
    await sync.envoyer();
    attendreEgal(deconnexions, 1, 'déconnexion signalée');
    attendre(!c.googleConnexion.connecte(), 'jeton invalide conservé');
    attendreEgal(lireFileGoogle(c), [c.TACHES[0].id], 'file conservée après 401');
    attendreEgal(JSON.stringify(c.TACHES), avant, 'aucune tâche modifiée');
    await sync.envoyer();
    attendreEgal(c.requetes.length, 1, 'pas de nouvel appel sans connexion');
  });

  await testAsync('Google Agenda : heures Paris et horaires de journées entières', async c => {
    c.localStorage.setItem('cap_google_agenda_v1', 'agenda-fictif');
    c.repondre = async r => {
      if (r.methode === 'GET' && r.url.pathname === '/calendar/v3/calendars/agenda-fictif') return reponseGoogle({ id: 'agenda-fictif' });
      if (r.methode === 'GET' && r.url.pathname === '/calendar/v3/calendars/agenda-fictif/events') {
        attendreEgal(r.url.searchParams.get('singleEvents'), 'true', 'récurrences dépliées');
        attendreEgal(r.url.searchParams.get('orderBy'), 'startTime', 'tri chronologique');
        attendreEgal(r.url.searchParams.get('maxResults'), '5', 'limite');
        return reponseGoogle({ items: [
          { summary: 'Horaire FICTIF', start: { dateTime: '2030-01-10T09:15:00Z' } },
          { summary: 'Journée FICTIF', start: { date: '2030-01-11' }, description: '14h30 – lieu FICTIF' },
          { summary: 'Autre FICTIF', start: { date: '2030-01-12' }, description: '9:05 – lieu FICTIF' },
          { summary: 'Sans heure FICTIF', start: { date: '2030-01-13' }, description: 'Toute la journée' },
          { summary: 'Annulé FICTIF', status: 'cancelled', start: { date: '2030-01-14' } }
        ] });
      }
      throw new Error(`Requête inattendue : ${r.url}`);
    };
    attendreEgal((await c.agenda().prochainsRendezVous(5)).map(({ titre, date, heure, journee_entiere }) =>
      ({ titre, date, heure, journee_entiere })), [
      { titre: 'Horaire FICTIF', date: '2030-01-10', heure: '10:15', journee_entiere: false },
      { titre: 'Journée FICTIF', date: '2030-01-11', heure: '14:30', journee_entiere: true },
      { titre: 'Autre FICTIF', date: '2030-01-12', heure: '09:05', journee_entiere: true },
      { titre: 'Sans heure FICTIF', date: '2030-01-13', heure: '', journee_entiere: true }
    ], 'rendez-vous normalisés');
    attendre(c.requetes.filter(r => r.url.pathname.startsWith('/calendar/')).every(r => r.methode === 'GET'),
      'lecture seule de l’agenda existant');
    attendreEgal(c.proprietesDrive.cap_agenda_id, 'agenda-fictif', 'identifiant de l’agenda rangé dans le Drive');
  });

  await testAsync('Google Agenda : agenda secondaire, quatre FICTIF, jamais le principal', async c => {
    c.localStorage.setItem('cap_google_agenda_v1', 'primary');
    c.proprietesDrive.cap_agenda_id = 'primary';
    c.repondre = async r => {
      if (r.methode === 'POST' && r.url.pathname === '/calendar/v3/calendars') {
        attendreEgal(r.corps.summary, REGLAGES_GOOGLE.nom_agenda, 'nom de l’agenda secondaire');
        return reponseGoogle({ id: 'agenda-secondaire-fictif' });
      }
      if (r.methode === 'POST' && r.url.pathname === '/calendar/v3/calendars/agenda-secondaire-fictif/events') return reponseGoogle({ id: 'evenement-fictif' });
      if (r.methode === 'GET' && r.url.pathname === '/calendar/v3/calendars/agenda-secondaire-fictif') return reponseGoogle({ id: 'agenda-secondaire-fictif' });
      throw new Error(`Requête inattendue : ${r.url}`);
    };
    const agenda = c.agenda();
    attendreEgal(await agenda.trouverOuCreer(), 'agenda-secondaire-fictif', 'agenda secondaire créé');
    const evenements = c.requetes.filter(r => r.methode === 'POST' && r.url.pathname.endsWith('/events'));
    attendreEgal(evenements.length, 4, 'quatre rendez-vous fictifs');
    attendre(evenements.every(r => r.corps.summary.startsWith('FICTIF – ')), 'rendez-vous non marqué fictif');
    attendreEgal(c.requetes.find(r => r.methode === 'POST' && r.url.pathname === '/calendar/v3/calendars').corps.timeZone,
      'Europe/Paris', 'fuseau de l’agenda');
    const aujourdHuiParis = new Intl.DateTimeFormat('sv-SE', { timeZone: 'Europe/Paris' }).format(new Date());
    for (const evenement of evenements) {
      const date = (evenement.corps.start.date || evenement.corps.start.dateTime).slice(0, 10);
      const jours = (new Date(`${date}T12:00:00Z`) - new Date(`${aujourdHuiParis}T12:00:00Z`)) / 86400000;
      attendre(jours >= 1 && jours <= 7, 'rendez-vous hors des sept prochains jours');
    }
    attendreEgal(evenements.filter(r => r.corps.start.date).length, 1, 'une journée entière');
    attendreEgal(evenements.filter(r => r.corps.start.dateTime).length, 3, 'trois rendez-vous horaires');
    attendre(evenements.every(r => r.corps.end.date || r.corps.end.dateTime), 'fin manquante');
    attendreEgal(await agenda.trouverOuCreer(), 'agenda-secondaire-fictif', 'agenda réutilisé');
    attendreEgal(c.requetes.filter(r => r.methode === 'POST').length, 5, 'aucune seconde création');
    attendre(c.requetes.every(r => !r.url.pathname.includes('/calendars/primary')), 'agenda principal touché');
    attendreEgal(c.proprietesDrive.cap_agenda_id, 'agenda-secondaire-fictif', 'nouvel agenda rangé dans le Drive');
    attendre(c.requetes.every(r => !r.url.pathname.includes('calendarList')), 'liste des agendas lue sans droit');
  });

  await testAsync('Google Agenda : nouvel appareil, agenda retrouvé par le Drive, aucune création', async c => {
    c.proprietesDrive.cap_agenda_id = 'agenda-deja-cree-fictif';
    c.repondre = async r => {
      if (r.methode === 'GET' && r.url.pathname === '/calendar/v3/calendars/agenda-deja-cree-fictif') {
        return reponseGoogle({ id: 'agenda-deja-cree-fictif' });
      }
      throw new Error(`Requête inattendue : ${r.url}`);
    };
    const agenda = c.agenda();
    attendreEgal(await agenda.trouverOuCreer(), 'agenda-deja-cree-fictif', 'agenda du Drive réutilisé');
    attendreEgal(c.localStorage.getItem('cap_google_agenda_v1'), 'agenda-deja-cree-fictif', 'identifiant gardé sur l’appareil');
    attendreEgal(c.requetes.filter(r => r.methode !== 'GET').length, 0, 'aucune création ni écriture');
    attendreEgal(await agenda.trouverOuCreer(), 'agenda-deja-cree-fictif', 'deuxième ouverture');
    attendreEgal(c.requetes.filter(r => r.url.pathname.startsWith('/drive/')).length, 1, 'Drive relu une seule fois');
  });

  await testAsync('Dossier des scans : choisi dans Chrome, rangé dans le Drive, retrouvé par la coque, oublié partout', async c => {
    const sélecteur = espace => objetIsole(SOURCE_GOOGLE_PICKER, 'googlePicker', {
      localStorage: espace, googleConnexion: c.googleConnexion, googleSheets: c.tableauAgenda,
      REGLAGES_GOOGLE, clePicker: { presente: () => true, lire: () => 'cle-fictive' }, window: c.window
    });
    // Chrome : Max a choisi le dossier avec la fenêtre de Google.
    const chrome = sélecteur(c.localStorage);
    chrome.enregistrerDossier('dossier-docs-fictif', 'Documents Personnels', 'documents_personnels');
    await chrome.rangerDansDrive('documents_personnels');
    attendreEgal(c.proprietesDrive.cap_dossier_documents_personnels, 'dossier-docs-fictif', 'identifiant rangé dans le Drive');
    await chrome.rangerDansDrive('documents_personnels');
    attendreEgal(c.requetes.filter(r => r.methode === 'PATCH').length, 1, 'rangé une seule fois');
    attendreEgal(chrome.dossierAppCap(), null, 'App Cap touché par le choix des scans');
    // Coque : mémoire séparée, rien de choisi sur l'appareil.
    const memoireCoque = espaceMemoire();
    const coque = sélecteur(memoireCoque);
    attendreEgal(coque.dossierDocumentsPersonnels(), null, 'choix présent avant relecture');
    attendreEgal((await coque.retrouverDepuisDrive('documents_personnels')).id, 'dossier-docs-fictif', 'dossier retrouvé par la coque');
    attendreEgal(coque.dossierDocumentsPersonnels().nom, 'Documents Personnels', 'nom affiché');
    const lectures = c.requetes.length;
    await coque.retrouverDepuisDrive('documents_personnels');
    attendreEgal(c.requetes.length, lectures, 'Drive relu alors que le dossier est déjà connu');
    // Oubli dans Chrome : effacé ici et dans le Drive ; un nouvel appareil ne le retrouve plus.
    await chrome.oublierDossier('documents_personnels');
    attendreEgal(chrome.dossierDocumentsPersonnels(), null, 'oubli sur l’appareil');
    attendreEgal(c.proprietesDrive.cap_dossier_documents_personnels, null, 'oubli dans le Drive');
    attendreEgal(await sélecteur(espaceMemoire()).retrouverDepuisDrive('documents_personnels'), null, 'dossier oublié retrouvé');
    attendre(c.requetes.every(r => r.url.pathname === '/drive/v3/files/tableau-agenda-fictif'), 'autre fichier du Drive touché');
  });

  await testAsync('Sélecteur Google : diagnostic étape par étape, jamais la clé ni le jeton, alerte si Google se tait', async c => {
    const CLE = 'CLE-SECRETE-FICTIVE-123456';
    const JETON = 'JETON-SECRET-FICTIF-789';
    function monter({ cle = true, connecte = true, reponses = [] } = {}) {
      const fenetres = [];
      const fauxGoogle = { picker: {
        Action: { PICKED: 'picked', CANCEL: 'cancel', LOADED: 'loaded' },
        ViewId: { FOLDERS: 'folders' },
        DocsView: class { setSelectFolderEnabled() { return this; } setIncludeFolders() { return this; } setMimeTypes() { return this; } },
        PickerBuilder: class {
          addView() { return this; } setOAuthToken(j) { this.jeton = j; return this; } setDeveloperKey(k) { this.cle = k; return this; }
          setTitle() { return this; } setCallback(f) { this.rappel = f; return this; }
          build() { const b = this; return { setVisible: () => { fenetres.push(b); for (const r of reponses) b.rappel(r); } }; }
        }
      } };
      const piqueur = objetIsole(SOURCE_GOOGLE_PICKER, 'googlePicker', {
        localStorage: espaceMemoire(), googleConnexion: { connecte: () => connecte, jeton: () => JETON },
        googleSheets: c.tableauAgenda, REGLAGES_GOOGLE, google: fauxGoogle,
        clePicker: { presente: () => cle, lire: () => CLE },
        window: { gapi: { load: (nom, options) => options.callback() } }
      });
      return { piqueur, fenetres };
    }
    const sansSecret = lignes => lignes.every(l => !l.includes(CLE) && !l.includes(JETON) && !l.includes('123456') && !l.includes('789'));

    // Choix réussi : toutes les étapes, puis la réponse de Google.
    let lignes = [];
    let m = monter({ reponses: [{ action: 'loaded' }, { action: 'picked', docs: [{ id: 'dossier-fictif', name: 'Documents Personnels' }] }] });
    const choisi = await m.piqueur.choisir('documents_personnels', { noter: t => lignes.push(t), delaiSilence: 50 });
    attendreEgal(choisi.id, 'dossier-fictif', 'dossier choisi');
    attendre(lignes.some(l => l.includes('Clé du sélecteur')) && lignes.some(l => l.includes('Fenêtre de Google demandée'))
      && lignes.some(l => l.includes('« picked »')), `étapes manquantes : ${lignes.join(' | ')}`);
    attendre(sansSecret(lignes), 'clé ou jeton dans le diagnostic');
    attendreEgal([m.fenetres[0].cle, m.fenetres[0].jeton], [CLE, JETON], 'clé et jeton bien donnés à Google seulement');
    await new Promise(r => setTimeout(r, 80));
    attendre(!lignes.some(l => l.includes('pas répondu')), 'alerte de silence après une réponse');

    // Google ne répond pas du tout : alerte et réouverture demandée.
    lignes = [];
    let silences = 0;
    m = monter({ reponses: [] });
    void m.piqueur.choisir('documents_personnels', { noter: t => lignes.push(t), surSilence: () => silences++, delaiSilence: 30 });
    await new Promise(r => setTimeout(r, 80));
    attendreEgal(silences, 1, 'réouverture non demandée');
    attendre(lignes.some(l => l.includes('pas répondu')), 'alerte de silence absente');
    attendre(sansSecret(lignes), 'clé ou jeton dans le diagnostic');

    // Clé absente : arrêt immédiat, rien d'ouvert.
    lignes = [];
    m = monter({ cle: false });
    await attendreRejet(() => m.piqueur.choisir('documents_personnels', { noter: t => lignes.push(t) }), 'clé');
    attendreEgal(m.fenetres.length, 0, 'fenêtre ouverte sans clé');
    attendre(sansSecret(lignes), 'clé ou jeton dans le diagnostic');
  });

  // ---------- Classement des scans, étape 1 : FAUX Doc et FAUX tableur (noms inventés) ----------
  // Faux Doc au format de l'export HTML du Drive : chaque niveau de puce est une liste à part, dont
  // la classe finit par « -N » ; titre du Doc en p.title ; titres en h1…h6 ; textes dans des span.
  function fauxDocArchitecture(ajout = '') {
    const puces = (niveau, noms) => `<ul class="lst-kix_fictif-${niveau} start">`
      + noms.map(nom => `<li class="c1 li-bullet-0"><span class="c0">${nom}</span></li>`).join('') + '</ul>';
    return '<html><head><style>.c0{font-weight:400}</style></head><body class="c2 doc-content">'
      + '<p class="c3 title"><span>Architecture FICTIVE des archives</span></p>'
      + '<h2 class="c4"><span>Règles pour Cap</span></h2>'
      + puces(0, Array.from({ length: 7 }, (_, i) => `Règle fictive ${i + 1}`))
      + '<h2 class="c4"><span>00_A_CLASSER (le premier)</span></h2>' + puces(0, ['Dossier_main_fictif'])
      + '<h2 class="c4"><span>01_IDENTITE_ET_ETAT_CIVIL</span></h2>' + puces(0, ['Pieces_identite'])
      + '<h2 class="c4"><span>02_MAISON</span></h2>'
      + '<p class="c5"><span>Commentaire libre sans puce</span></p>'
      + puces(0, ['Prenom_fictif'])
      + puces(1, ['Factures_energie', 'Rénovation_et_expertises', 'Artisans'])
      + puces(2, ['Plomberie', 'Electricite'])
      + puces(0, ['Autre_fictif (aucun sous-dossier pour l’instant)'])
      + ajout + '</body></html>';
  }
  function fauxTableurClassement() {
    return [
      ['Mot-clé repéré', 'Organisme', 'Chemin de destination', 'Type de document', 'Modèle de titre'],
      ['carte test Prenom_fictif', 'Mairie Fictive', '01_IDENTITE_ET_ETAT_CIVIL / Pieces_identite', 'Carte d’identité', '[date] Carte test Prenom_fictif Nom_fictif'],
      ['syndic fictif', 'Syndic Fictif', '02_MAISON / Prenom_fictif / Factures_energie', 'Relevé', '[date] Releve syndic fictif Prenom_fictif'],
      ['devis fictif', 'Artisan Fictif', '02_MAISON / Prenom_fictif / Artisans / Plomberie', 'Devis', '[date] Devis plomberie Prenom_fictif'],
      ['renovation fictive', 'Service Fictif', '02_MAISON / Prenom_fictif / Renovation_et_expertises', 'Convocation', '[date] Convocation renovation Prenom_fictif'],
      ['banque fictive', 'Banque Fictive', '04_BANQUE_ET_FINANCES / Prenom_fictif / Comptes_bancaires', 'Relevé', '[date] Releve banque fictive'],
      ['', '', '', '', ''],
      ['ligne incomplète fictive', 'Organisme Fictif', '', 'Courrier', '']
    ];
  }

  await testAsync('Classement étape 1 : Doc lu par niveaux, règles et 00_A_CLASSER écartés, parenthèses retirées', async c => {
    const classementIsole = objetIsole(SOURCE_CLASSEMENT, 'classement', { googleConnexion: c.googleConnexion, googlePicker: {} });
    const arbre = classementIsole.analyserArchitecture(fauxDocArchitecture());
    attendreEgal(arbre.racine.enfants.map(e => e.nom), ['01_IDENTITE_ET_ETAT_CIVIL', '02_MAISON'], 'dossiers principaux');
    attendreEgal(arbre.sections_ignorees, 2, 'règles et 00_A_CLASSER écartés');
    const maison = arbre.racine.enfants[1];
    attendreEgal(maison.enfants.map(e => e.nom), ['Prenom_fictif', 'Autre_fictif'], 'niveau 1 et parenthèse retirée');
    attendreEgal(maison.enfants[0].enfants.map(e => e.nom), ['Factures_energie', 'Rénovation_et_expertises', 'Artisans'], 'niveau 2, accent gardé');
    attendreEgal(maison.enfants[0].enfants[2].enfants.map(e => e.nom), ['Plomberie', 'Electricite'], 'niveau 3');
    attendre(!JSON.stringify(arbre).includes('Règle fictive') && !JSON.stringify(arbre).includes('Dossier_main_fictif'), 'règle ou archive faite main lue comme dossier');
    attendreEgal(arbre.doutes.length, 0, 'doutes inattendus');
  });

  await testAsync('Classement étape 1 : tableur de 5 lignes, chemins vérifiés dans le Doc, nom exact du Doc gardé', async c => {
    const classementIsole = objetIsole(SOURCE_CLASSEMENT, 'classement', { googleConnexion: c.googleConnexion, googlePicker: {} });
    const arbre = classementIsole.analyserArchitecture(fauxDocArchitecture());
    const tableur = classementIsole.analyserTableur(fauxTableurClassement());
    attendreEgal(tableur.lignes.length, 5, 'lignes lues');
    attendreEgal(tableur.ignorees.map(l => l.numero), [8], 'ligne incomplète écartée (ligne 8), ligne vide ignorée');
    attendreEgal(tableur.lignes[2].chemin, ['02_MAISON', 'Prenom_fictif', 'Artisans', 'Plomberie'], 'chemin coupé sur « / »');
    const v = tableur.lignes.map(l => classementIsole.verifierChemin(l.chemin, arbre));
    attendreEgal(v.map(x => x.ok), [true, true, true, true, false], 'chemins trouvés');
    attendreEgal(v[3].noms[2], 'Rénovation_et_expertises', 'sans accent dans le tableur, nom exact du Doc');
    attendreEgal([v[4].raison, v[4].niveau], ['absent_du_doc', 0], 'chemin absent du Doc refusé');
    const resume = classementIsole.resumer(tableur, arbre);
    attendreEgal([resume.lignes, resume.lignes_ignorees, resume.dossiers_principaux, resume.chemins_trouves, resume.chemins_absents],
      [5, 1, 2, 4, 1], 'résumé');
    const texte = classementIsole.texteResume(resume);
    attendre(['Prenom_fictif', 'Fictive', 'MAISON', 'carte test'].every(mot => !texte.includes(mot)), 'un nom apparaît dans le résumé');
    // Doublon dans le Doc : deux noms identiques sans accents au même endroit = refus, jamais de choix.
    const double = fauxDocArchitecture('<ul class="lst-kix_autre-0 start"><li><span>prénom_FICTIF</span></li></ul>');
    const arbreDouble = classementIsole.analyserArchitecture(double);
    attendreEgal(arbreDouble.doutes.map(d => d.type), ['double'], 'doublon signalé');
    attendreEgal(classementIsole.verifierChemin(['02_MAISON', 'Prenom_fictif', 'Factures_energie'], arbreDouble).raison,
      'double_dans_le_doc', 'chemin passant par un doublon refusé');
  });

  await testAsync('Classement étape 1 : lecture dans le Drive, première feuille quel que soit son nom, lecture seule', async c => {
    const piqueur = {
      dossierChoisi: role => ({ architecture: { id: 'doc-fictif' }, tableur_classement: { id: 'tableur-fictif' } })[role],
      retrouverDepuisDrive: async () => null
    };
    c.repondre = async r => {
      if (r.url.hostname === 'sheets.googleapis.com' && r.url.pathname === '/v4/spreadsheets/tableur-fictif') {
        return reponseGoogle({ sheets: [{ properties: { title: 'Feuille fictive' } }, { properties: { title: 'Autre' } }] });
      }
      if (r.url.hostname === 'sheets.googleapis.com' && r.url.pathname.startsWith('/v4/spreadsheets/tableur-fictif/values/')) {
        attendreEgal(decodeURIComponent(r.url.pathname.split('/values/')[1]), "'Feuille fictive'!A:E", 'première feuille lue');
        return reponseGoogle({ values: fauxTableurClassement() });
      }
      if (r.url.hostname === 'www.googleapis.com' && r.url.pathname === '/drive/v3/files/doc-fictif/export') {
        attendreEgal(r.url.searchParams.get('mimeType'), 'text/html', 'Doc exporté en page HTML par le Drive');
        return new Response(fauxDocArchitecture(), { status: 200, headers: { 'Content-Type': 'text/html' } });
      }
      throw new Error(`Requête inattendue : ${r.url}`);
    };
    const classementIsole = objetIsole(SOURCE_CLASSEMENT, 'classement', { googleConnexion: c.googleConnexion, googlePicker: piqueur });
    const lecture = await classementIsole.lire();
    attendreEgal([lecture.resume.lignes, lecture.resume.chemins_trouves], [5, 4], 'lecture complète');
    attendreEgal(lecture.etats, ['Tableur : lu.', 'Doc : lu.'], 'un message par fichier');
    attendre(c.requetes.every(r => r.methode === 'GET'), 'écriture pendant la lecture');
    attendre(c.requetes.every(r => r.url.hostname !== 'docs.googleapis.com'), 'service Google Docs utilisé');
    // Rien de choisi : Cap le dit, sans aucune requête.
    const sansChoix = objetIsole(SOURCE_CLASSEMENT, 'classement', { googleConnexion: c.googleConnexion,
      googlePicker: { dossierChoisi: () => null, retrouverDepuisDrive: async () => null } });
    const avant = c.requetes.length;
    await attendreRejet(() => sansChoix.lire(), 'Choisis d’abord le Doc');
    attendreEgal(c.requetes.length, avant, 'requête sans fichier choisi');
  });

  await testAsync('Classement : Doc refusé par Google (service non activé) = raison affichée, tableur lu, connexion gardée', async c => {
    preparerConnexion(c);
    let deconnexions = 0;
    c.window.addEventListener('cap-google-deconnecte', () => deconnexions++);
    const piqueur = {
      dossierChoisi: role => ({ architecture: { id: 'doc-fictif' }, tableur_classement: { id: 'tableur-fictif' } })[role],
      retrouverDepuisDrive: async () => null
    };
    c.repondre = async r => {
      if (r.url.pathname === '/v4/spreadsheets/tableur-fictif') return reponseGoogle({ sheets: [{ properties: { title: 'Feuille fictive' } }] });
      if (r.url.pathname.startsWith('/v4/spreadsheets/tableur-fictif/values/')) return reponseGoogle({ values: fauxTableurClassement() });
      if (r.url.pathname === '/drive/v3/files/doc-fictif/export') {
        return reponseGoogle({ error: { code: 403, status: 'PERMISSION_DENIED', message: 'Message FICTIF de Google',
          details: [{ reason: 'SERVICE_DISABLED' }] } }, 403);
      }
      throw new Error(`Requête inattendue : ${r.url}`);
    };
    const classementIsole = objetIsole(SOURCE_CLASSEMENT, 'classement', { googleConnexion: c.googleConnexion, googlePicker: piqueur });
    let message = '';
    try { await classementIsole.lire(); } catch (erreur) { message = erreur.message; }
    attendre(message.includes('Tableur : lu.'), `tableur non signalé lu : ${message}`);
    attendre(message.includes('Doc : refusé (erreur 403, raison : SERVICE_DISABLED)'), `raison absente : ${message}`);
    attendre(!message.includes('jeton-fictif') && !message.includes('doc-fictif') && !message.includes('Message FICTIF'), 'jeton, identifiant ou texte brut affiché');
    attendreEgal(deconnexions, 0, 'déconnexion pour un service non activé');
    attendre(c.googleConnexion.connecte(), 'jeton retiré pour un service non activé');
    // Un 403 sans raison connue : comportement d'avant, déconnexion (redonner l'accès).
    c.repondre = async () => reponseGoogle({}, 403);
    await attendreRejet(() => c.googleConnexion.appeler('https://www.googleapis.com/drive/v3/files/doc-fictif'), '403');
    attendreEgal(deconnexions, 1, 'déconnexion attendue pour un 403 sans raison');
    // L'ancien service Google Docs n'est plus une adresse permise.
    await attendreRejet(() => c.connexion().appeler('https://docs.googleapis.com/v1/documents/doc-fictif'), 'Adresse Google non autorisée');
  });

  await testAsync('Émetteur : Dictionnaire lu dans ses trois onglets, colonnes autorisées seulement (jamais notes ni naissance), gardé en mémoire seulement', async c => {
    const piqueur = { dossierChoisi: role => (role === 'dictionnaire' ? { id: 'dico-fictif' } : null), retrouverDepuisDrive: async () => null };
    const entetes = {
      'Ancienne liste': ['First Name', 'Last Name', 'Notes', 'Birthday', 'Phone 1 - Value'],
      'Tri contacts': ['Nom dans les contacts', 'Note d’origine', 'Téléphone', 'Remarques', 'Décision'],
      Dictionnaire: ['Prénom', 'Nom', 'Type', 'Note pour IA', 'Téléphone', 'Date de naissance / anniversaire', 'Domaine', 'Note']
    };
    const colonnes = {
      'Ancienne liste': { A: ['First Name', 'Jean'], B: ['Last Name', 'Fictif'], E: ['Phone 1 - Value', '04 00 00 00 01'] },
      'Tri contacts': { A: ['Nom dans les contacts', 'Cabinet FICTIF des Lilas'], C: ['Téléphone', '04 00 00 00 05'] },
      Dictionnaire: { A: ['Prénom', 'Jean'], B: ['Nom', 'Fictif'], C: ['Type', 'Personne'], E: ['Téléphone', '04 00 00 00 01'], G: ['Domaine', 'Maison FICTIVE'] }
    };
    const demandees = [];
    c.repondre = async r => {
      if (r.url.hostname !== 'sheets.googleapis.com' || r.url.pathname !== '/v4/spreadsheets/dico-fictif/values:batchGet') throw new Error(`Requête inattendue : ${r.url}`);
      const plages = r.url.searchParams.getAll('ranges');
      demandees.push(...plages);
      if (plages.every(pl => pl.endsWith('!1:1'))) return reponseGoogle({ valueRanges: plages.map(pl => ({ values: [entetes[pl.split("'")[1]]] })) });
      attendreEgal(r.url.searchParams.get('majorDimension'), 'COLUMNS', 'colonnes demandées une par une');
      return reponseGoogle({ valueRanges: plages.map(pl => {
        const [, onglet, morceau] = /^'(.+)'!([A-Z]+):[A-Z]+$/.exec(pl);
        return { values: [colonnes[onglet][morceau]] };
      }) });
    };
    let ecrit = false;
    const espion = { getItem: () => null, setItem: () => { ecrit = true; }, removeItem: () => { ecrit = true; } };
    const classementIsole = objetIsole(SOURCE_CLASSEMENT, 'classement', { googleConnexion: c.googleConnexion, googlePicker: piqueur, emetteur, localStorage: espion, sessionStorage: espion, indexedDB: undefined });
    const entrees = await classementIsole.lireDictionnaire();
    const colonnesLues = demandees.filter(pl => !pl.endsWith('!1:1'));
    attendreEgal(colonnesLues, ["'Ancienne liste'!A:A", "'Ancienne liste'!B:B", "'Ancienne liste'!E:E", "'Tri contacts'!A:A", "'Tri contacts'!C:C",
      "'Dictionnaire'!A:A", "'Dictionnaire'!B:B", "'Dictionnaire'!C:C", "'Dictionnaire'!E:E", "'Dictionnaire'!G:G"], 'seules les colonnes autorisées sont demandées');
    attendreEgal(entrees.map(e => [e.onglet, e.numero]), [['Ancienne liste', 2], ['Tri contacts', 2], ['Dictionnaire', 2]], 'une entrée par ligne, onglet et numéro');
    attendre(c.requetes.every(r => r.methode === 'GET'), 'écriture dans le Dictionnaire');
    const nombre = c.requetes.length;
    attendre((await classementIsole.lireDictionnaire()) === entrees, 'deuxième scan : pas gardé en mémoire');
    attendreEgal(c.requetes.length, nombre, 'Dictionnaire relu alors qu’il est en mémoire');
    attendre(!ecrit, 'quelque chose a été écrit sur le téléphone');
  });

  // ---------- 06/11/2026 : dossiers « Relations », étape 2 (calcul seulement, données FICTIVES) ----------
  function dictionnaireRelationsFictif() {
    return [
      ['Prénom', 'Nom', 'Type'],
      ['Jean', 'Fictif', 'Personne'],
      ['Jeanne', 'Exemple-FICTIF', 'personne'],
      ['Paul', 'Modèle-FICTIF', 'Personne'],
      ['paul', 'modele-fictif', 'Personne'],
      ['Séverine-FICTIF', '', 'Personne'],
      ['', 'Dupont-FICTIF', 'Personne'],
      ['Cabinet FICTIF', '', 'Organisme'],
      ['Marc', 'Essai-FICTIF', ''],
      ['', '', ''],
      [' Zoé ', ' Test   FICTIF ', 'Personne (pro)'],
      ['Jean-Baptiste-FICTIF (Jibé)', 'Essai-FICTIF', 'Personne']
    ];
  }

  test('Relations (étape 2) : calcul de la liste sur un faux Dictionnaire, homonymes, fiches incomplètes, rien d’autre', () => {
    const r = relations.calculer(dictionnaireRelationsFictif());
    attendreEgal(r.lues, 10, 'fiches lues (ligne vide ignorée)');
    attendreEgal(r.aCreer.map(d => [d.numero, d.nomDossier]), [[2, 'r_Jean Fictif'], [3, 'r_Jeanne Exemple-FICTIF'], [11, 'r_Zoé Test FICTIF'], [12, 'r_Jibé Essai-FICTIF']], 'dossiers à prévoir');
    // Décision de Max : « Prénom (Diminutif) » → le dossier ne porte que le diminutif et le nom, sans parenthèse.
    attendre(r.aCreer.every(d => !/[()]/.test(d.nomDossier)), 'parenthèse dans un nom de dossier');
    attendreEgal(['Jean-Baptiste-FICTIF (Jibé)', 'Jean-Baptiste-FICTIF', '(Jibé)', 'Jean-Baptiste-FICTIF ( )', 'Jean-Baptiste-FICTIF  ( Jibé )'].map(relations.prenomDuDossier),
      ['Jibé', 'Jean-Baptiste-FICTIF', 'Jibé', 'Jean-Baptiste-FICTIF ( )', 'Jibé'], 'prénom du dossier');
    attendreEgal(r.homonymes, [[4, 5]], 'homonymes (majuscules et accents ignorés), aucun dossier prévu pour eux');
    attendreEgal(r.incompletes, [6, 7], 'fiches incomplètes');
    attendreEgal(r.typeAbsent, [9], 'fiche sans type : à vérifier, rien de prévu');
    attendreEgal(r.autres, 1, 'organisme écarté');
    // Colonnes dans un autre ordre, avec d'autres colonnes autour : même résultat.
    const melange = dictionnaireRelationsFictif().map(l => ['x', l[2], 'y', l[1], l[0]]);
    melange[0] = ['Note pour IA', 'Type', 'Téléphone', 'NOM', 'prénom'];
    attendreEgal(relations.calculer(melange).aCreer.length, 4, 'colonnes reconnues par leur titre');
    attendreEgal(relations.colonnesALire(['Note pour IA', 'Type', 'Téléphone', 'NOM', 'prénom', 'Date de naissance']), [1, 3, 4], 'seules Prénom, Nom, Type sont à lire');
    attendreEgal(relations.calculer([]).lues, 0, 'Dictionnaire vide');
    // Le résumé ne montre que des nombres, jamais un nom.
    const texte = relations.resumer(r);
    for (const mot of ['Jean', 'Fictif', 'Paul', 'Zoé', 'Séverine-FICTIF', 'Marc', 'Cabinet', 'FICTIF']) attendre(!texte.includes(mot), `un nom apparaît à l’écran : ${mot}`);
    attendre(texte.includes('Dossiers « r_ » à prévoir : 4.') && texte.includes('Homonymes à départager : 1 nom(s), 2 fiche(s)')
      && texte.includes('Fiches incomplètes (prénom ou nom manquant) : 2.') && texte.includes('rien n’est créé'), `résumé : ${texte}`);
    // Le module ne parle jamais au Drive, n'écrit rien sur le téléphone, ne crée rien.
    for (const interdit of ['googleConnexion', 'fetch(', 'POST', 'PATCH', 'DELETE', 'localStorage', 'sessionStorage', 'indexedDB', 'innerHTML', 'cerveau', 'files?']) {
      attendre(!SOURCE_RELATIONS.includes(interdit), `relations.js contient « ${interdit} »`);
    }
  });

  await testAsync('Relations (étape 2) : le bouton lit le faux Dictionnaire et n’affiche que des nombres ; Dictionnaire pas choisi ou illisible : rien créé', async c => {
    const ui = preparerInterface(c);
    const bouton = ui.parId('calculer-relations');
    const zone = ui.parId('resume-relations');
    attendre(bouton && zone && zone.hidden, 'bouton ou zone absents');
    let appels = 0;
    const reponses = [async () => dictionnaireRelationsFictif(), async () => null, async () => { throw new Error('refus FICTIF'); }];
    relations.brancher(ui.doc, { lireDictionnairePersonnes: () => reponses[appels++]() });
    bouton.click();
    await attendreQue(() => /prévoir : 4/.test(zone.textContent), `résumé absent : ${zone.textContent}`);
    attendre(!zone.hidden && !/Jean|Fictif|Paul|Zoé/i.test(zone.textContent), 'un nom est affiché');
    bouton.click();
    await attendreQue(() => /Choisis d’abord le Dictionnaire/.test(zone.textContent), 'message sans Dictionnaire');
    bouton.click();
    await attendreQue(() => /n’a pas pu être lu.*Rien n’a été créé/.test(zone.textContent), 'message d’erreur');
    attendreEgal(c.requetes.length, 0, 'une requête Google est partie');
  });

  await testAsync('Relations (étape 2) : lecture du Dictionnaire = onglet « Dictionnaire », colonnes Prénom, Nom, Type seulement, GET seulement, rien gardé', async c => {
    const piqueur = { dossierChoisi: role => (role === 'dictionnaire' ? { id: 'dico-fictif' } : null), retrouverDepuisDrive: async () => null };
    const entetes = ['Prénom', 'Note pour IA', 'Nom', 'Téléphone', 'Type', 'Date de naissance / anniversaire'];
    const colonnes = { A: ['Prénom', 'Jean', 'Séverine-FICTIF'], C: ['Nom', 'Fictif'], E: ['Type', 'Personne', 'Personne'] };
    const demandees = [];
    c.repondre = async r => {
      if (r.url.hostname !== 'sheets.googleapis.com' || r.url.pathname !== '/v4/spreadsheets/dico-fictif/values:batchGet') throw new Error(`Requête inattendue : ${r.url}`);
      const plages = r.url.searchParams.getAll('ranges');
      demandees.push(...plages);
      if (plages.length === 1 && plages[0] === "'Dictionnaire'!1:1") return reponseGoogle({ valueRanges: [{ values: [entetes] }] });
      return reponseGoogle({ valueRanges: plages.map(pl => ({ values: [colonnes[/!([A-Z]+):/.exec(pl)[1]]] })) });
    };
    let ecrit = false;
    const espion = { getItem: () => null, setItem: () => { ecrit = true; }, removeItem: () => { ecrit = true; } };
    const classementIsole = objetIsole(SOURCE_CLASSEMENT, 'classement', { googleConnexion: c.googleConnexion, googlePicker: piqueur, emetteur, relations, localStorage: espion, sessionStorage: espion, indexedDB: undefined });
    const lignes = await classementIsole.lireDictionnairePersonnes();
    attendreEgal(demandees, ["'Dictionnaire'!1:1", "'Dictionnaire'!A:A", "'Dictionnaire'!C:C", "'Dictionnaire'!E:E"], 'colonnes demandées');
    attendreEgal(lignes, [['Prénom', 'Nom', 'Type'], ['Jean', 'Fictif', 'Personne'], ['Séverine-FICTIF', '', 'Personne']], 'lignes reconstituées');
    attendreEgal(relations.calculer(lignes).incompletes, [3], 'calcul sur la lecture');
    attendre(c.requetes.every(r => r.methode === 'GET'), 'écriture dans le Drive');
    attendre(!ecrit, 'quelque chose a été écrit sur le téléphone');
    const sansChoix = objetIsole(SOURCE_CLASSEMENT, 'classement', { googleConnexion: c.googleConnexion, googlePicker: { dossierChoisi: () => null, retrouverDepuisDrive: async () => null }, emetteur, relations });
    attendreEgal(await sansChoix.lireDictionnairePersonnes(), null, 'Dictionnaire pas choisi');
  });

  // ---------- 06/11/2026 : dossiers « Relations », étape 3 (création sur un FAUX Drive seulement) ----------
  // Faux Drive : comprend les recherches de Cap (étiquette invisible, parent, type), crée en mémoire,
  // peut « couper » après N créations. Tout est FICTIF.
  function fauxDriveRelations(c, { coupureApres = Infinity } = {}) {
    const f = { fichiers: [], creations: 0, coupureApres, remplacements: 0, deformerApresRemplacement: false };
    let numero = 0;
    c.repondre = async r => {
      const exporter = /^\/drive\/v3\/files\/([^/]+)\/export$/.exec(r.url.pathname);
      if (exporter) {
        attendreEgal([r.methode, r.url.searchParams.get('mimeType')], ['GET', 'text/plain'], 'lecture du texte');
        const doc = f.fichiers.find(x => x.id === decodeURIComponent(exporter[1]));
        // Comme Google : marque d'encodage au début et fin de ligne Windows.
        return new Response(`﻿${doc.contenu}\r\n`, { status: 200, headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
      }
      const fiche = /^\/drive\/v3\/files\/([^/]+)$/.exec(r.url.pathname);
      if (fiche) {
        attendreEgal(r.methode, 'GET', 'fiche lue seulement');
        const x = f.fichiers.find(y => y.id === decodeURIComponent(fiche[1]) && (!y.aLaMain || f.mainVisible));
        return x ? reponseGoogle({ id: x.id, name: x.name, appProperties: x.appProperties }) : reponseGoogle({ error: { code: 404 } }, 404);
      }
      const remplacer = /^\/upload\/drive\/v3\/files\/([^/]+)$/.exec(r.url.pathname);
      if (remplacer) {
        attendreEgal([r.methode, r.url.searchParams.get('uploadType')], ['PATCH', 'media'], 'remplacement du contenu');
        attendre(/^text\/html; charset=UTF-8$/.test(r.options.headers['Content-Type']), 'type du contenu');
        attendre(/^[\x20-\x7e]*$/.test(r.options.body), 'caractère non simple dans la page envoyée');
        const doc = f.fichiers.find(x => x.id === decodeURIComponent(remplacer[1]));
        attendre(doc && doc.mimeType === 'application/vnd.google-apps.document', 'remplacement d’autre chose qu’un Google Doc');
        f.remplacements++;
        doc.contenu = f.deformerApresRemplacement ? 'contenu FICTIF déformé' : new DOMParser().parseFromString(r.options.body, 'text/html').body.textContent;
        return reponseGoogle({ id: doc.id });
      }
      const envoiTexte = r.url.pathname === '/upload/drive/v3/files';
      attendre(['https://www.googleapis.com/drive/v3/files', 'https://www.googleapis.com/upload/drive/v3/files'].includes(r.url.origin + r.url.pathname), `adresse inattendue : ${r.url}`);
      if (r.methode === 'POST') {
        if (f.creations >= f.coupureApres) throw new Error('coupure FICTIVE du réseau');
        let infos = r.corps;
        let contenu = '';
        if (envoiTexte) {
          attendreEgal(r.url.searchParams.get('uploadType'), 'multipart', 'envoi multipart');
          const limite = /boundary=(\S+)/.exec(r.options.headers['Content-Type'])[1];
          const morceaux = r.options.body.split(`--${limite}`).slice(1, -1).map(m => m.replace(/^\r\n/, '').replace(/\r\n$/, ''));
          const [enteteInfos, json] = morceaux[0].split('\r\n\r\n');
          const [enteteTexte, texte] = morceaux[1].split('\r\n\r\n');
          attendre(/application\/json; charset=UTF-8/.test(enteteInfos) && /text\/html; charset=UTF-8/.test(enteteTexte), 'en-têtes de l’envoi');
          infos = JSON.parse(json);
          // Correction des accents : la page envoyée ne contient QUE des caractères simples ; on la lit
          // comme Google le ferait (une page HTML), pour retrouver le texte de la première entrée.
          attendre(/^[\x20-\x7e]*$/.test(texte), `caractère non simple dans la page envoyée : ${texte}`);
          attendre(/<meta charset="utf-8">/.test(texte), 'page sans « charset »');
          contenu = new DOMParser().parseFromString(texte, 'text/html').body.textContent;
        }
        f.creations++;
        const nouveau = { id: `fictif-${++numero}`, name: infos.name, mimeType: infos.mimeType, parents: infos.parents, appProperties: infos.appProperties || {}, trashed: false, contenu };
        f.fichiers.push(nouveau);
        return reponseGoogle({ id: nouveau.id, mimeType: nouveau.mimeType });
      }
      attendreEgal(r.methode, 'GET', 'méthode inattendue');
      const q = r.url.searchParams.get('q') || '';
      const etiquette = /appProperties has \{ key='([^']+)' and value='((?:[^'\\]|\\.)*)' \}/.exec(q);
      const parent = /'([^']+)' in parents/.exec(q)?.[1];
      const type = /mimeType='([^']+)'/.exec(q)?.[1];
      attendre(/trashed=false/.test(q), 'recherche sans « trashed=false »');
      const trouves = f.fichiers.filter(x => !x.trashed && (!x.aLaMain || f.mainVisible) && (!parent || x.parents.includes(parent)) && (!type || x.mimeType === type)
        && (!etiquette || x.appProperties[etiquette[1]] === etiquette[2].replace(/\\(.)/g, '$1')));
      return reponseGoogle({ files: trouves.map(x => ({ id: x.id, name: x.name, mimeType: x.mimeType, appProperties: x.appProperties })) });
    };
    f.noms = () => f.fichiers.filter(x => !x.aLaMain).map(x => x.name).sort();
    f.aLaMain = (name, mimeType, parent) => { const x = { id: `main-${++numero}`, name, mimeType, parents: [parent], appProperties: {}, trashed: false, contenu: '', aLaMain: true }; f.fichiers.push(x); return x; };
    f.mainVisible = false;
    return f;
  }
  function dictionnaireCreationFictif() {
    return [['Prénom', 'Nom', 'Type'], ['Jean', 'Fictif', 'Personne'], ['Jeanne', 'Exemple-FICTIF', 'Personne']];
  }
  function creationIsolee(c, instant = null) {
    const lignes = [];
    const journal = { ajouter: (j, l) => lignes.push([j, l]) };
    // Horloge fixée (instant FICTIF) : seule la date « maintenant » est remplacée.
    const DateFixe = instant === null ? Date : class extends Date { constructor(...a) { super(...(a.length ? a : [instant])); } static now() { return new Date(instant).getTime(); } };
    const module = objetIsole(SOURCE_RELATIONS_CREATION, 'relationsCreation', { googleConnexion: { appeler: c.fetch }, relations, journaux: journal, Date: DateFixe });
    return { module, lignes };
  }
  const ATTENDUS_DEUX = ['Envoyés', 'Envoyés', 'Journal de bord', 'Journal de bord', 'Relations', 'Reçus', 'Reçus', 'r_Jean Fictif', 'r_Jeanne Exemple-FICTIF'];

  await testAsync('Relations (étape 3, FAUX Drive) : création complète, une ligne de journal par création, puis deux appuis de suite = aucun doublon', async c => {
    const drive = fauxDriveRelations(c);
    const { module, lignes } = creationIsolee(c);
    const plan = await module.preparer(dictionnaireCreationFictif(), 'appcap-fictif');
    attendreEgal([plan.aFaire.length, plan.deja.length, plan.bloque], [2, 0, false], 'plan');
    attendreEgal(drive.creations, 0, 'le plan a créé quelque chose');
    // Deux appuis de suite : le second ne crée rien.
    const [premier, second] = await Promise.all([module.lancer(plan, { appCap: 'appcap-fictif' }), module.lancer(plan, { appCap: 'appcap-fictif' })]);
    attendre(second.refuse && second.crees === 0, 'le second appui a été pris en compte');
    attendreEgal(premier.crees, 9, 'éléments créés');
    attendreEgal(drive.noms(), ATTENDUS_DEUX, 'arborescence créée');
    const relationsId = drive.fichiers.find(x => x.name === 'Relations');
    attendreEgal(relationsId.parents, ['appcap-fictif'], '« Relations » à la racine de App Cap');
    const jean = drive.fichiers.find(x => x.name === 'r_Jean Fictif');
    attendreEgal(jean.parents, [relationsId.id], 'dossier de la personne dans Relations');
    attendreEgal(drive.fichiers.filter(x => x.parents[0] === jean.id).map(x => [x.name, x.mimeType]).sort(),
      [['Envoyés', 'application/vnd.google-apps.folder'], ['Journal de bord', 'application/vnd.google-apps.document'], ['Reçus', 'application/vnd.google-apps.folder']], 'contenu du dossier');
    attendreEgal(lignes.length, 9, 'une ligne de Journal Général par création');
    attendre(lignes.every(([j, l]) => j === 'general' && l.chantier === 'Relations' && l.resultat === 'créé'), 'lignes de journal');
    // Nouvel appui plus tard (nouveau plan) : tout est déjà là, rien n'est recréé.
    const plan2 = await module.preparer(dictionnaireCreationFictif(), 'appcap-fictif');
    attendreEgal([plan2.aFaire.length, plan2.deja.length], [0, 2], 'déjà présents reconnus par leur étiquette');
    const encore = await module.lancer(plan2, { appCap: 'appcap-fictif' });
    attendreEgal([encore.crees, drive.fichiers.length, lignes.length], [0, 9, 9], 'doublon créé');
    // Même avec l'ANCIEN plan (fait avant la création) : la vérification juste avant évite tout doublon.
    attendreEgal((await module.lancer(plan, { appCap: 'appcap-fictif' })).crees, 0, 'ancien plan : doublon');
    attendre(c.requetes.every(r => ['GET', 'POST'].includes(r.methode) && r.url.hostname === 'www.googleapis.com'), 'adresse ou méthode non permise');
    attendre(c.requetes.every(r => !/trashed\s*=\s*true|removeParents|addParents/i.test(decodeURIComponent(r.url.search)) && !/trash|delete|copy/i.test(r.url.pathname) && !(r.corps && 'trashed' in r.corps)), 'suppression ou déplacement');
  });

  await testAsync('Relations (étape 3, FAUX Drive) : coupure au milieu, puis reprise sans doublon ; dossier déjà présent complété seulement', async c => {
    const drive = fauxDriveRelations(c, { coupureApres: 3 });
    const { module, lignes } = creationIsolee(c);
    const plan = await module.preparer(dictionnaireCreationFictif(), 'appcap-fictif');
    await attendreRejet(() => module.lancer(plan, { appCap: 'appcap-fictif' }), 'coupure FICTIVE');
    attendreEgal(drive.fichiers.length, 3, 'éléments créés avant la coupure');
    attendreEgal(lignes.length, 3, 'une ligne par création, même avant la coupure');
    drive.coupureApres = Infinity;
    const reprise = await module.lancer(await module.preparer(dictionnaireCreationFictif(), 'appcap-fictif'), { appCap: 'appcap-fictif' });
    attendreEgal(reprise.crees, 6, 'reprise : seulement ce qui manquait');
    attendreEgal(drive.noms(), ATTENDUS_DEUX, 'arborescence après reprise (sans doublon)');
    attendreEgal(lignes.length, 9, 'lignes de journal après reprise');
  });

  await testAsync('Relations (étape 3, FAUX Drive) : homonyme, fiche incomplète, sans type, changement de nom = arrêt, rien créé ; « continuer pour les autres » seulement après choix', async c => {
    const drive = fauxDriveRelations(c);
    const { module } = creationIsolee(c);
    const valeurs = [['Prénom', 'Nom', 'Type'], ['Jean', 'Fictif', 'Personne'], ['Paul', 'Modèle-FICTIF', 'Personne'], ['paul', 'modele-fictif', 'Personne'],
      ['Séverine-FICTIF', '', 'Personne'], ['Marc', 'Essai-FICTIF', '']];
    const plan = await module.preparer(valeurs, 'appcap-fictif');
    attendre(plan.bloque, 'pas d’arrêt malgré les fiches à choisir');
    const r = await module.lancer(plan, { appCap: 'appcap-fictif' });
    attendre(r.arrete && r.crees === 0 && drive.creations === 0, 'création malgré l’arrêt');
    // Choix de Max : seulement les autres fiches → seulement Jean.
    await module.lancer(plan, { appCap: 'appcap-fictif', sansLesFichesAChoisir: true });
    attendreEgal(drive.fichiers.filter(x => x.name.startsWith('r_')).map(x => x.name), ['r_Jean Fictif'], 'homonymes, incomplète ou sans type créés');
    // Changement de nom dans le Dictionnaire (même ligne 2) : « Renommer ? » proposé, rien créé, rien renommé.
    const renomme = [['Prénom', 'Nom', 'Type'], ['Jean', 'Fictif-Nouveau', 'Personne']];
    const plan2 = await module.preparer(renomme, 'appcap-fictif');
    attendreEgal(plan2.renommages, [{ numero: 2, ancien: 'r_Jean Fictif', nouveau: 'r_Jean Fictif-Nouveau' }], 'renommage proposé');
    attendre(plan2.bloque && plan2.aFaire.length === 0, 'nouveau dossier prévu malgré le changement de nom');
    const avant = drive.fichiers.length;
    await module.lancer(plan2, { appCap: 'appcap-fictif' });
    attendreEgal(drive.fichiers.length, avant, 'création malgré le changement de nom');
    attendre(drive.fichiers.some(x => x.name === 'r_Jean Fictif'), 'ancien dossier touché');
    // Fiche retirée du Dictionnaire : son dossier est gardé tel quel.
    const plan3 = await module.preparer([['Prénom', 'Nom', 'Type'], ['Jeanne', 'Exemple-FICTIF', 'Personne']], 'appcap-fictif');
    attendreEgal(plan3.orphelins, [], 'ligne 2 réutilisée : pas un orphelin mais…');
    attendreEgal(plan3.renommages.length, 1, '… un renommage possible (même ligne)');
    attendre(c.requetes.every(q => ['GET', 'POST'].includes(q.methode)), 'méthode non permise');
  });

  await testAsync('Relations (étape 3, FAUX Drive) : écran de vérification, question « dossier r_ fait à la main » : Oui = rien créé ; Non puis Oui = création ; choix en très gros', async c => {
    const ui = preparerInterface(c);
    const drive = fauxDriveRelations(c);
    const { module } = creationIsolee(c);
    const el = id => ui.parId(id);
    let plan = await module.preparer(dictionnaireCreationFictif(), 'appcap-fictif');
    module.ecran(ui.doc, plan, { appCap: 'appcap-fictif' });
    attendre(el('verification-relations').open, 'écran de vérification fermé');
    attendre(/^2 dossier/.test(el('relations-nombre').textContent), `nombre : ${el('relations-nombre').textContent}`);
    attendreEgal([...el('relations-liste').children].map(li => li.textContent), ['r_Jean Fictif', 'r_Jeanne Exemple-FICTIF'], 'liste');
    attendreEgal(el('relations-question-texte').textContent, 'As-tu déjà créé toi-même un dossier r_ pour l’une de ces personnes ?', 'question');
    attendre(el('relations-confirmer').hidden, 'bouton de création visible avant la réponse');
    el('relations-oui-deja').click();
    el('relations-creer').click();
    await new Promise(r => setTimeout(r, 50));
    attendreEgal(drive.creations, 0, 'création malgré « Oui, j’ai déjà créé »');
    attendre(/rien n’est créé/.test(el('relations-etat').textContent), 'message après Oui');
    // Nouveau passage : Non, puis confirmation explicite.
    plan = await module.preparer(dictionnaireCreationFictif(), 'appcap-fictif');
    const travail = module.ecran(ui.doc, plan, { appCap: 'appcap-fictif' });
    el('relations-non-jamais').click();
    attendre(!el('relations-confirmer').hidden && /2 dossier/.test(el('relations-creer').textContent), 'confirmation absente');
    el('relations-creer').click();
    el('relations-creer').click();
    await travail.promesse;
    attendreEgal(drive.fichiers.length, 9, 'création après Non puis Oui (un seul passage)');
    attendre(/Terminé : 9 élément/.test(el('relations-etat').textContent), `état : ${el('relations-etat').textContent}`);
    // Arrêt : choix montrés en très gros.
    const bloque = await module.preparer([['Prénom', 'Nom', 'Type'], ['Séverine-FICTIF', '', 'Personne']], 'appcap-fictif');
    module.ecran(ui.doc, bloque, { appCap: 'appcap-fictif' });
    attendre(!el('relations-arret').hidden && el('relations-question').hidden, 'arrêt non montré');
    attendre(/ligne 2/.test(el('relations-problemes').textContent), 'fiche à choisir non montrée');
    const taille = parseFloat(ui.cadre.contentWindow.getComputedStyle(el('relations-corriger')).fontSize);
    attendre(taille >= 20, `choix pas en très gros : ${taille}px`);
    el('relations-corriger').click();
    attendre(/rien n’est créé/.test(el('relations-etat').textContent), 'message après « je corrige »');
    el('relations-fermer').click();
  });

  // 06/11/2026, demande de Max : le « Journal de bord » naît avec sa première entrée datée (heure de Paris).
  await testAsync('Relations (FAUX Drive) : le « Journal de bord » naît avec sa première entrée datée (heure de Paris, horloge fixée, accents), étiquette gardée, reprise sans doublon', async c => {
    // Hiver : 21:50 en temps universel = 22:50 à Paris (instant FICTIF).
    const drive = fauxDriveRelations(c, { coupureApres: 2 });
    const { module, lignes } = creationIsolee(c, '2026-11-06T21:50:00Z');
    const valeurs = [['Prénom', 'Nom', 'Type'], ['Zoé-FICTIF (Zézé)', 'Lefèvre-FICTIF', 'Personne'], ['Jean', 'Fictif', 'Personne']];
    // Coupure juste avant le premier « Journal de bord » : rien d'autre n'est perdu ni doublé.
    await attendreRejet(async () => module.lancer(await module.preparer(valeurs, 'appcap-fictif'), { appCap: 'appcap-fictif' }), 'coupure FICTIVE');
    attendreEgal(drive.fichiers.map(x => x.name), ['Relations', 'r_Zézé Lefèvre-FICTIF'], 'créés avant la coupure');
    drive.coupureApres = Infinity;
    await module.lancer(await module.preparer(valeurs, 'appcap-fictif'), { appCap: 'appcap-fictif' });
    const journauxDeBord = drive.fichiers.filter(x => x.name === 'Journal de bord');
    attendreEgal(journauxDeBord.length, 2, 'un Journal de bord par personne, sans doublon');
    const dossierDe = nom => drive.fichiers.find(x => x.name === nom).id;
    const texteDe = nom => journauxDeBord.find(x => x.parents[0] === dossierDe(nom)).contenu;
    attendreEgal(texteDe('r_Zézé Lefèvre-FICTIF'), '06/11/2026, 22:50 : création du dossier Relations de Zézé Lefèvre-FICTIF', 'première entrée (texte exact, accents)');
    attendreEgal(texteDe('r_Jean Fictif'), '06/11/2026, 22:50 : création du dossier Relations de Jean Fictif', 'première entrée de la seconde personne');
    attendre(journauxDeBord.every(x => x.mimeType === 'application/vnd.google-apps.document' && x.appProperties.cap_relation_partie === 'journal'), 'type ou étiquette du Journal de bord');
    attendre(drive.fichiers.filter(x => x.name !== 'Journal de bord').every(x => x.contenu === ''), 'texte ailleurs que dans le Journal de bord');
    attendreEgal(drive.fichiers.length, 9, 'éléments créés');
    attendreEgal(lignes.length, 9, 'lignes du Journal Général');
    // Une nouvelle passe ne réécrit ni ne recrée aucun Journal de bord.
    await module.lancer(await module.preparer(valeurs, 'appcap-fictif'), { appCap: 'appcap-fictif' });
    attendreEgal(drive.fichiers.length, 9, 'doublon');
    attendre(c.requetes.every(r => ['GET', 'POST'].includes(r.methode) && r.url.hostname === 'www.googleapis.com'), 'adresse ou méthode non permise');
    attendreEgal(c.requetes.filter(r => r.url.pathname.startsWith('/upload/')).length, 3, 'envois de texte (2 réussis, 1 coupé)');
    // Été (heure d'été de Paris) : 08:05 en temps universel = 10:05 ; minuit passé : la date de Paris.
    attendreEgal(creationIsolee(c, '2026-07-01T08:05:00Z').module.premiereEntree({ nomDossier: 'r_Jean Fictif' }), '01/07/2026, 10:05 : création du dossier Relations de Jean Fictif', 'heure d’été');
    attendreEgal(creationIsolee(c, '2026-12-31T23:30:00Z').module.premiereEntree({ nomDossier: 'r_Jean Fictif' }), '01/01/2027, 00:30 : création du dossier Relations de Jean Fictif', 'changement de jour à Paris');
  });

  await testAsync('Relations (FAUX Drive) : accents de la première entrée (é, è, à, ç, ô) envoyés sans aucun caractère déformable, relus exacts', async c => {
    const drive = fauxDriveRelations(c);
    const { module } = creationIsolee(c, '2026-11-06T21:50:00Z');
    const valeurs = [['Prénom', 'Nom', 'Type'], ['Jérôme-FICTIF (Gégè)', 'Garçon-à-Côté-FICTIF', 'Personne']];
    await module.lancer(await module.preparer(valeurs, 'appcap-fictif'), { appCap: 'appcap-fictif' });
    const journal = drive.fichiers.find(x => x.name === 'Journal de bord');
    attendreEgal(journal.contenu, '06/11/2026, 22:50 : création du dossier Relations de Gégè Garçon-à-Côté-FICTIF', 'accents de la première entrée');
    // La page envoyée : seulement des caractères simples, chaque accent écrit par son numéro.
    const envoi = c.requetes.find(r => r.url.pathname.startsWith('/upload/')).options.body;
    const page = envoi.split('Content-Type: text/html; charset=UTF-8\r\n\r\n')[1].split('\r\n--')[0];
    for (const [lettre, code] of [['é', 233], ['è', 232], ['à', 224], ['ç', 231], ['ô', 244]]) {
      attendre(!page.includes(lettre) && page.includes(`&#${code};`), `« ${lettre} » mal envoyé`);
    }
    // Le nom du dossier (fiche JSON du fichier) reste juste, accents compris.
    attendre(drive.fichiers.some(x => x.name === 'r_Gégè Garçon-à-Côté-FICTIF'), 'nom de dossier accentué');
    // Caractères spéciaux : jamais pris pour du code.
    attendreEgal(module.texteEnHtml('a < b & c > d "e"'), '<!DOCTYPE html><html><head><meta charset="utf-8"></head><body><p>a &lt; b &amp; c &gt; d &quot;e&quot;</p></body></html>', 'caractères spéciaux');
    attendreEgal(new DOMParser().parseFromString(module.texteEnHtml('Œuvre ’ ô 🎵 é'), 'text/html').body.textContent, 'Œuvre ’ ô 🎵 é', 'relecture exacte');
  });

  // ---------- 06/11/2026 : réparation des accents des « Journal de bord » déjà créés (FAUX Drive) ----------
  // Abîme un texte comme Google l'a fait : les octets UTF-8 lus comme un autre encodage (« é » → « Ã© »).
  function abimer(texte) { return new TextDecoder('windows-1252').decode(new TextEncoder().encode(texte)); }
  async function driveAbimeFictif(c) {
    const drive = fauxDriveRelations(c);
    const { module, lignes } = creationIsolee(c, '2026-11-06T22:20:00Z');
    const valeurs = [['Prénom', 'Nom', 'Type'], ['Jean', 'Fictif', 'Personne'], ['Jérôme-FICTIF (Gégè)', 'Garçon-à-Côté-FICTIF', 'Personne'],
      ['Jeanne', 'Exemple-FICTIF', 'Personne'], ['Zoé-FICTIF (Zézé)', 'Lefèvre-FICTIF', 'Personne'], ['Paul', 'Vide-FICTIF', 'Personne']];
    await module.lancer(await module.preparer(valeurs, 'appcap-fictif'), { appCap: 'appcap-fictif' });
    const journalDe = nom => drive.fichiers.find(x => x.name === 'Journal de bord' && x.parents[0] === drive.fichiers.find(y => y.name === nom).id);
    // Avant la correction : premières entrées abîmées ; l'une complétée à la main ; une vide ; une juste.
    for (const nom of ['r_Jean Fictif', 'r_Gégè Garçon-à-Côté-FICTIF']) journalDe(nom).contenu = abimer(journalDe(nom).contenu);
    journalDe('r_Jeanne Exemple-FICTIF').contenu = `${abimer(journalDe('r_Jeanne Exemple-FICTIF').contenu)}\nnote ajoutée à la main FICTIVE`;
    journalDe('r_Paul Vide-FICTIF').contenu = '';
    c.reparationRelations = true;
    return { drive, module, lignes, journalDe, creations: drive.creations, lignesAvant: lignes.length };
  }

  test('Réparation des accents : texte abîmé retrouvé exactement (é, è, à, ç, ô, œ, ’), sinon rien', () => {
    const m = objetIsole(SOURCE_RELATIONS_CREATION, 'relationsCreation', { googleConnexion: {}, relations, journaux: {} });
    const juste = '06/11/2026, 23:20 : création du dossier Relations de Gégè Garçon-à-Côté-FICTIF';
    attendreEgal(abimer(juste).includes('crÃ©ation'), true, 'abîmé comme chez Max');
    attendreEgal(m.texteRepare(abimer(juste)), juste, 'réparé exactement');
    attendreEgal(m.texteRepare(abimer('é è à ç ô œ ’ Œ')), 'é è à ç ô œ ’ Œ', 'autres accents');
    attendreEgal(m.examiner(abimer(juste), 'r_Gégè Garçon-à-Côté-FICTIF'), { etat: 'abime', apres: juste }, 'abîmé');
    attendreEgal(m.examiner(`﻿${juste}\r\n`, 'r_Gégè Garçon-à-Côté-FICTIF'), { etat: 'juste' }, 'déjà juste');
    attendreEgal(m.examiner(abimer(juste), 'r_Autre Personne-FICTIF'), { etat: 'intouchable' }, 'nom d’un autre dossier');
    attendreEgal(m.examiner(`${abimer(juste)}\nsuite FICTIVE`, 'r_Gégè Garçon-à-Côté-FICTIF'), { etat: 'intouchable' }, 'autre chose écrit');
    attendreEgal(m.examiner('', 'r_Gégè Garçon-à-Côté-FICTIF'), { etat: 'intouchable' }, 'vide');
    attendreEgal(m.examiner('texte libre FICTIF 🎵', 'r_Gégè Garçon-à-Côté-FICTIF'), { etat: 'intouchable' }, 'texte libre');
  });

  await testAsync('Réparation des accents (FAUX Drive) : liste en lecture seule, UN journal pour vérifier, puis les autres ; écrit à la main, vide ou juste : pas touché ; rien supprimé', async c => {
    const { drive, module, lignes, journalDe, creations, lignesAvant } = await driveAbimeFictif(c);
    const plan = await module.preparerReparation('appcap-fictif');
    attendreEgal(plan.aReparer.map(e => e.nomDossier), ['r_Gégè Garçon-à-Côté-FICTIF', 'r_Jean Fictif'], 'à réparer');
    attendreEgal(plan.justes.map(e => e.nomDossier), ['r_Zézé Lefèvre-FICTIF'], 'déjà justes');
    attendreEgal(plan.intouchables.map(e => e.nomDossier), ['r_Jeanne Exemple-FICTIF', 'r_Paul Vide-FICTIF'], 'pas touchés');
    attendreEgal(drive.remplacements, 0, 'modification pendant la liste');
    // UN journal pour vérifier.
    attendreEgal(await module.lancerReparation([plan.aReparer[0]]), { repares: 1, sautes: 0 }, 'premier');
    attendreEgal(journalDe('r_Gégè Garçon-à-Côté-FICTIF').contenu, '06/11/2026, 23:20 : création du dossier Relations de Gégè Garçon-à-Côté-FICTIF', 'réparé (date et heure d’origine)');
    attendre(journalDe('r_Jean Fictif').contenu.includes('Ã©'), 'second réparé trop tôt');
    // Puis les autres.
    attendreEgal(await module.lancerReparation(plan.aReparer.slice(1)), { repares: 1, sautes: 0 }, 'les autres');
    attendreEgal(journalDe('r_Jean Fictif').contenu, '06/11/2026, 23:20 : création du dossier Relations de Jean Fictif', 'second réparé');
    attendre(journalDe('r_Jeanne Exemple-FICTIF').contenu.endsWith('\nnote ajoutée à la main FICTIVE'), 'journal écrit à la main touché');
    attendreEgal(journalDe('r_Paul Vide-FICTIF').contenu, '', 'journal vide touché');
    attendreEgal([drive.remplacements, drive.creations, lignes.length - lignesAvant], [2, creations, 2], 'remplacements, créations, lignes de journal');
    attendre(lignes.slice(lignesAvant).every(([j, l]) => j === 'general' && l.resultat === 'réparé' && l.chantier === 'Relations'), 'lignes du Journal Général');
    // Nouvelle liste : plus rien à réparer.
    attendreEgal((await module.preparerReparation('appcap-fictif')).aReparer.length, 0, 'encore à réparer');
    attendre(c.requetes.every(r => ['GET', 'POST', 'PATCH'].includes(r.methode) && r.url.hostname === 'www.googleapis.com'), 'adresse ou méthode non permise');
    attendre(c.requetes.filter(r => r.methode === 'PATCH').every(r => r.url.pathname.startsWith('/upload/drive/v3/files/')), 'modification ailleurs');
  });

  await testAsync('Réparation des accents (FAUX Drive) : journal modifié depuis la liste = pas touché ; texte faux après réparation = arrêt, les autres pas touchés', async c => {
    const { drive, module, journalDe } = await driveAbimeFictif(c);
    let plan = await module.preparerReparation('appcap-fictif');
    journalDe('r_Gégè Garçon-à-Côté-FICTIF').contenu += '\nécrit par Max entre-temps FICTIF';
    attendreEgal(await module.lancerReparation(plan.aReparer), { repares: 1, sautes: 1 }, 'modifié entre-temps');
    attendre(journalDe('r_Gégè Garçon-à-Côté-FICTIF').contenu.endsWith('entre-temps FICTIF'), 'journal modifié touché');
    // Google rendrait un texte faux : arrêt au premier, le suivant n'est pas touché.
    const autre = await driveAbimeFictif(c);
    plan = await autre.module.preparerReparation('appcap-fictif');
    autre.drive.deformerApresRemplacement = true;
    await attendreRejet(() => autre.module.lancerReparation(plan.aReparer), 'pas le bon texte');
    attendreEgal(autre.drive.remplacements, 1, 'le suivant a été touché');
    attendre(autre.journalDe('r_Jean Fictif').contenu.includes('Ã©'), 'le suivant a été touché');
  });

  await testAsync('Réparation des accents (FAUX Drive) : écran : nombres, « Réparer UN journal pour vérifier », puis « Oui, répare les N autres » ; double appui sans effet', async c => {
    const ui = preparerInterface(c);
    const { drive, module } = await driveAbimeFictif(c);
    const el = id => ui.parId(id);
    module.brancherReparation(ui.doc, { appCap: async () => ({ id: 'appcap-fictif' }) });
    attendre(el('reparer-un-relations').hidden && el('reparer-tous-relations').hidden, 'boutons visibles trop tôt');
    el('reparer-relations').click();
    await attendreQue(() => !el('reparer-un-relations').hidden, `liste absente : ${el('resume-reparer-relations').textContent}`);
    const texte = el('resume-reparer-relations').textContent;
    attendre(texte.includes('À réparer : 2') && texte.includes('Déjà justes : 1') && texte.includes('Pas touchés (vides, ou avec autre chose que la première entrée) : 2') && texte.includes('Rien n’est encore modifié'), `liste : ${texte}`);
    attendreEgal(el('reparer-un-relations').textContent, 'Réparer UN journal pour vérifier : r_Gégè Garçon-à-Côté-FICTIF', 'bouton du premier');
    attendreEgal(drive.remplacements, 0, 'modification avant l’appui');
    el('reparer-un-relations').click();
    el('reparer-un-relations').click();
    await attendreQue(() => !el('reparer-tous-relations').hidden, `après le premier : ${el('resume-reparer-relations').textContent}`);
    attendreEgal(drive.remplacements, 1, 'un seul journal réparé');
    attendre(/Réparé : r_Gégè Garçon-à-Côté-FICTIF/.test(el('resume-reparer-relations').textContent), 'compte rendu du premier');
    attendreEgal(el('reparer-tous-relations').textContent, 'Oui, répare les 1 autres journaux', 'bouton des autres');
    el('reparer-tous-relations').click();
    el('reparer-tous-relations').click();
    await attendreQue(() => /Terminé : 1 journal/.test(el('resume-reparer-relations').textContent), `fin : ${el('resume-reparer-relations').textContent}`);
    attendreEgal(drive.remplacements, 2, 'réparations en trop');
    attendre(parseFloat(ui.cadre.contentWindow.getComputedStyle(el('reparer-un-relations')).fontSize) >= 20, 'bouton pas en gros');
  });

  // ---------- 06/11/2026 : essai de visibilité (FAUX Drive, fichiers « déposés à la main » FICTIFS) ----------
  async function driveVisibiliteFictif(c) {
    const drive = fauxDriveRelations(c);
    const { module } = creationIsolee(c, '2026-11-06T22:20:00Z');
    const valeurs = [['Prénom', 'Nom', 'Type'], ['Jean', 'Fictif', 'Personne'], ['Jeanne', 'Exemple-FICTIF', 'Personne'], ['Paul', 'Image-FICTIF', 'Personne'], ['Zoé', 'Rien-FICTIF', 'Personne']];
    await module.lancer(await module.preparer(valeurs, 'appcap-fictif'), { appCap: 'appcap-fictif' });
    const id = nom => drive.fichiers.find(x => x.name === nom).id;
    const album = drive.aLaMain('Album FICTIF', 'application/vnd.google-apps.folder', id('r_Jean Fictif'));
    drive.aLaMain('01 morceau FICTIF secret.mp3', 'audio/mpeg', album.id);
    drive.aLaMain('02 morceau FICTIF secret.mp3', 'audio/mpeg', album.id);
    drive.aLaMain('chanson FICTIVE secrète.mp3', 'application/octet-stream', id('r_Jeanne Exemple-FICTIF'));
    for (let n = 1; n <= 4; n++) drive.aLaMain(`photo FICTIVE secrète ${n}.jpg`, 'image/jpeg', id('r_Paul Image-FICTIF'));
    // Déposé à la main DANS « Reçus » (créé par Cap) : compté aussi.
    const recusPaul = drive.fichiers.find(x => x.name === 'Reçus' && x.parents[0] === id('r_Paul Image-FICTIF'));
    drive.aLaMain('note FICTIVE secrète.pdf', 'application/pdf', recusPaul.id);
    return { drive, module };
  }

  await testAsync('Essai de visibilité (FAUX Drive) : nombres seulement par dossier (MP3, images, sous-dossiers), rien de Cap compté, aucun nom de fichier, rien modifié', async c => {
    const { drive, module } = await driveVisibiliteFictif(c);
    const avant = c.requetes.length;
    const creations = drive.creations;
    // Fichiers déposés à la main invisibles (comme Cap pourrait les voir avec drive.file) : tout à zéro.
    let r = await module.essaiVisibilite('appcap-fictif');
    attendreEgal(r.dossiers, 4, 'dossiers lus');
    attendre(r.lignes.every(l => l.mp3 + l.images + l.sousDossiers + l.autres === 0), 'éléments de Cap comptés');
    attendre(/4 autre\(s\) dossier\(s\) : rien de visible/.test(module.resumerVisibilite(r)) && /Total visible : 0 MP3, 0 image\(s\), 0 sous-dossier\(s\), 0 autre\(s\)\./.test(module.resumerVisibilite(r)), 'résumé à zéro');
    // Visibles : nombres justes, y compris dans un sous-dossier et dans « Reçus ».
    drive.mainVisible = true;
    r = await module.essaiVisibilite('appcap-fictif');
    attendreEgal(r.lignes.map(l => [l.nomDossier, l.mp3, l.images, l.sousDossiers, l.autres]),
      [['r_Jean Fictif', 2, 0, 1, 0], ['r_Jeanne Exemple-FICTIF', 1, 0, 0, 0], ['r_Paul Image-FICTIF', 0, 4, 0, 1], ['r_Zoé Rien-FICTIF', 0, 0, 0, 0]], 'nombres par dossier');
    const texte = module.resumerVisibilite(r);
    attendreEgal(texte, ['Essai de visibilité (lecture seule, rien n’est modifié) : 4 dossier(s) « r_ » lus.',
      'r_Jean Fictif : 2 MP3 · 0 image(s) · 1 sous-dossier(s)', 'r_Jeanne Exemple-FICTIF : 1 MP3 · 0 image(s) · 0 sous-dossier(s)',
      'r_Paul Image-FICTIF : 0 MP3 · 4 image(s) · 0 sous-dossier(s) · 1 autre(s)', '1 autre(s) dossier(s) : rien de visible à part ce que Cap a créé.',
      'Total visible : 3 MP3, 4 image(s), 1 sous-dossier(s), 1 autre(s).'].join('\n'), 'résumé');
    attendre(!/secr|morceau|photo|chanson|note|Album|\.mp3|\.jpg|\.pdf/i.test(texte), 'un nom de fichier est affiché');
    // Lecture seule.
    attendre(c.requetes.slice(avant).every(q => q.methode === 'GET' && q.url.hostname === 'www.googleapis.com' && q.url.pathname === '/drive/v3/files'), 'autre chose qu’une lecture');
    attendreEgal(drive.creations, creations, 'création pendant l’essai');
  });

  await testAsync('Essai de visibilité (FAUX Drive) : écran (essai, « Montrer « Relations » à Google », nouvel essai) ; App Cap absent ; sélecteur refusé', async c => {
    const ui = preparerInterface(c);
    const { drive, module } = await driveVisibiliteFictif(c);
    const el = id => ui.parId(id);
    let montres = 0;
    let refuser = false;
    module.brancherVisibilite(ui.doc, { appCap: async () => ({ id: 'appcap-fictif' }),
      montrer: async () => { if (refuser) throw new Error('fenêtre FICTIVE refusée'); montres++; drive.mainVisible = true; return { id: drive.fichiers.find(x => x.name === 'Relations').id, nom: 'Relations' }; } });
    attendre(el('resume-visibilite-relations').hidden, 'zone visible trop tôt');
    el('visibilite-relations').click();
    await attendreQue(() => /Total visible : 0 MP3/.test(el('resume-visibilite-relations').textContent), `premier essai : ${el('resume-visibilite-relations').textContent}`);
    el('montrer-relations').click();
    await attendreQue(() => /OUI : c’est bien le « Relations » créé par Cap/.test(el('resume-visibilite-relations').textContent), `après le sélecteur : ${el('resume-visibilite-relations').textContent}`);
    attendreEgal(montres, 1, 'sélecteur');
    el('visibilite-relations').click();
    await attendreQue(() => /Total visible : 3 MP3, 4 image/.test(el('resume-visibilite-relations').textContent), `second essai : ${el('resume-visibilite-relations').textContent}`);
    attendre(!/secr|morceau|photo|chanson|\.mp3|\.jpg/i.test(el('resume-visibilite-relations').textContent), 'nom de fichier affiché');
    refuser = true;
    el('montrer-relations').click();
    await attendreQue(() => /n’a pas pu s’ouvrir/.test(el('resume-visibilite-relations').textContent), 'sélecteur refusé');
    const ui2 = preparerInterface(c);
    await driveVisibiliteFictif(c);
    module.brancherVisibilite(ui2.doc, { appCap: async () => null, montrer: async () => null });
    const avant = c.requetes.length;
    ui2.parId('visibilite-relations').click();
    await attendreQue(() => /Choisis d’abord le dossier « App Cap »/.test(ui2.parId('resume-visibilite-relations').textContent), 'App Cap absent');
    attendre(c.requetes.slice(avant).every(q => q.methode === 'GET'), 'modification');
  });

  await testAsync('Dossier montré à Google (FAUX Drive) : nom en gros, OUI si c’est le « Relations » de Cap, NON sinon (dossier d’une personne, ancien dossier) ; message visible sans défiler', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const { drive, module } = await driveVisibiliteFictif(c);
    const el = id => ui.parId(id);
    // Un ancien « Relations » fait à la main (pas de Cap), montré par erreur.
    const ancien = drive.aLaMain('Relations', 'application/vnd.google-apps.folder', 'appcap-fictif');
    const relationsCap = drive.fichiers.find(x => x.name === 'Relations' && !x.aLaMain);
    const personne = drive.fichiers.find(x => x.name === 'r_Jean Fictif');
    let reponse = null;
    module.brancherVisibilite(ui.doc, { appCap: async () => ({ id: 'appcap-fictif' }), montrer: async () => { drive.mainVisible = true; return reponse; } });
    // La fenêtre « Réglages du Drive » ouverte, en haut, sur un écran de téléphone.
    const fenetre = el('reglages-drive');
    fenetre.showModal();
    fenetre.scrollTop = 0;
    const verifier = async (choix, attendu) => {
      reponse = choix;
      fenetre.scrollTop = 0;
      el('montrer-relations').click();
      await attendreQue(() => attendu.test(el('resume-visibilite-relations').textContent), `message : ${el('resume-visibilite-relations').textContent}`);
      const zone = el('resume-visibilite-relations').getBoundingClientRect();
      const cadre = fenetre.getBoundingClientRect();
      attendre(zone.height > 0 && zone.top >= Math.max(0, cadre.top) - 1 && zone.bottom <= Math.min(ui.cadre.contentWindow.innerHeight, cadre.bottom) + 1,
        `message hors de l’écran (haut ${Math.round(zone.top)}, bas ${Math.round(zone.bottom)}, fenêtre ${Math.round(cadre.top)}–${Math.round(cadre.bottom)})`);
    };
    await verifier({ id: relationsCap.id, nom: 'Relations' }, /^Dossier montré : « Relations »\nOUI : c’est bien le « Relations » créé par Cap/);
    await verifier({ id: personne.id, nom: 'r_Jean Fictif' }, /^Dossier montré : « r_Jean Fictif »\nNON : ce n’est pas « Relations », c’est le dossier d’une personne/);
    await verifier({ id: ancien.id, nom: 'Relations' }, /^Dossier montré : « Relations »\nNON : ce n’est pas le « Relations » créé par Cap/);
    // Fiche illisible (dossier inconnu) : le nom donné par la fenêtre de Google, et NON.
    await verifier({ id: 'inconnu-fictif', nom: 'Dossier FICTIF' }, /^Dossier montré : « Dossier FICTIF »\nNON/);
    await verifier(null, /^Rien n’a été choisi\.$/);
    attendre(parseFloat(ui.cadre.contentWindow.getComputedStyle(el('resume-visibilite-relations')).fontSize) >= 20, 'message pas en gros');
    attendre(c.requetes.every(q => ['GET', 'POST'].includes(q.methode)), 'modification');
    fenetre.close();
  });

  // ----- Compte Google NEUF dédié à Cap (07/11/2026) : FAUX compte, FAUX Drive -----
  const COMPTE_CAP_FICTIF = 'compte-cap-fictif@id.gle';
  function compteRelationsIsole(c) {
    return objetIsole(SOURCE_GOOGLE_COMPTE_RELATIONS, 'googleCompteRelations', {
      localStorage: c.localStorage, sessionStorage: c.sessionStorage, location: c.location, history: c.history,
      fetch: c.fetch, REGLAGES_GOOGLE, crypto, Date: c.Date });
  }
  const relationsCompte0 = () => objetIsole(SOURCE_RELATIONS_COMPTE, 'relationsCompte', { window: { CAP_TESTS: true } });
  // Connexion simulée : bouton, page de Google, retour dans Cap (la page est rechargée).
  function connecterCompteFictif(c, saisie = '  Compte-Cap-FICTIF@id.gle ') {
    let m = compteRelationsIsole(c);
    m.enregistrerAdresse(saisie);
    m.seConnecter();
    const url = c.redirections.at(-1);
    c.location.hash = `#access_token=jeton-compte-cap-fictif&expires_in=3600&token_type=Bearer&state=${url.searchParams.get('state')}`;
    m = compteRelationsIsole(c);
    return { m, url };
  }
  function pdfFictif() {
    // Deux pages de 200 x 200 : un carré noir en haut à gauche, puis en bas à droite.
    const flux = t => `<< /Length ${t.length} >>\nstream\n${t}\nendstream`;
    const objets = [null, '<< /Type /Catalog /Pages 2 0 R >>', '<< /Type /Pages /Kids [3 0 R 5 0 R] /Count 2 >>',
      '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] /Contents 4 0 R >>', flux('0 0 0 rg 20 120 60 60 re f'),
      '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] /Contents 6 0 R >>', flux('0 0 0 rg 120 20 60 60 re f')];
    let texte = '%PDF-1.4\n';
    const positions = [];
    for (let i = 1; i < objets.length; i++) { positions.push(texte.length); texte += `${i} 0 obj\n${objets[i]}\nendobj\n`; }
    const debutXref = texte.length;
    texte += `xref\n0 ${objets.length}\n0000000000 65535 f \n` + positions.map(n => `${String(n).padStart(10, '0')} 00000 n \n`).join('')
      + `trailer\n<< /Size ${objets.length} /Root 1 0 R >>\nstartxref\n${debutXref}\n%%EOF\n`;
    return new TextEncoder().encode(texte);
  }
  function fauxDriveCompteCap(c, { compte = COMPTE_CAP_FICTIF } = {}) {
    const DOSSIER_F = 'application/vnd.google-apps.folder';
    const f = { fichiers: [], compte, autorisations: [] };
    let n = 0;
    f.ajouter = (name, mimeType, parent = 'root', contenu = null) => {
      const x = { id: `cc-${++n}`, name, mimeType, parents: [parent], contenu };
      f.fichiers.push(x);
      return x;
    };
    c.repondre = async r => {
      attendreEgal(r.methode, 'GET', 'compte Cap : lecture seulement');
      attendre(r.options.body === undefined, 'compte Cap : contenu envoyé');
      f.autorisations.push(new Headers(r.options.headers).get('Authorization'));
      if (r.url.pathname === '/drive/v3/about') return reponseGoogle({ user: { emailAddress: f.compte } });
      if (r.url.pathname === '/drive/v3/files/root') return reponseGoogle({ id: 'root' });
      const media = /^\/drive\/v3\/files\/([^/]+)$/.exec(r.url.pathname);
      if (media && r.url.searchParams.get('alt') === 'media') {
        const x = f.fichiers.find(y => y.id === decodeURIComponent(media[1]));
        return new Response(x.contenu, { status: 200, headers: { 'Content-Type': x.mimeType } });
      }
      if (r.url.pathname !== '/drive/v3/files') throw new Error(`adresse inattendue : ${r.url.pathname}`);
      const q = r.url.searchParams.get('q');
      const parent = /^'([^']+)' in parents and trashed=false$/.exec(q);
      let liste;
      if (parent) liste = f.fichiers.filter(x => x.parents[0] === parent[1]);
      else if (q === 'trashed=false') liste = f.fichiers;
      else if (q === `name='Relations' and mimeType='${DOSSIER_F}' and 'root' in parents and trashed=false`) {
        liste = f.fichiers.filter(x => x.name === 'Relations' && x.mimeType === DOSSIER_F && x.parents[0] === 'root');
      } else throw new Error(`recherche inattendue : ${q}`);
      // Pages de 2 éléments : la suite (nextPageToken) doit être lue.
      const debut = Number(r.url.searchParams.get('pageToken') || 0);
      return reponseGoogle({ files: liste.slice(debut, debut + 2).map(({ id, name, mimeType, parents, contenu, taille }) =>
        ({ id, name, mimeType, parents, ...(taille || contenu ? { size: String(taille || contenu.length) } : {}) })),
        ...(debut + 2 < liste.length ? { nextPageToken: String(debut + 2) } : {}) });
    };
    return f;
  }
  function remplirCompteCapFictif(f) {
    const D = 'application/vnd.google-apps.folder';
    const rel = f.ajouter('Relations', D);
    const jean = f.ajouter('r_Jean Fictif', D, rel.id);
    const album = f.ajouter('Album FICTIF', D, jean.id);
    f.ajouter('01 morceau FICTIF secret.mp3', 'audio/mpeg', album.id);
    f.ajouter('02 morceau FICTIF secret.mp3', 'application/octet-stream', album.id);
    const liste = f.ajouter('Playlist FICTIVE', D, jean.id);
    f.ajouter('03 morceau FICTIF secret.mp3', 'audio/mpeg', liste.id);
    const paule = f.ajouter('r_Paule Image-FICTIF', D, rel.id);
    for (let i = 1; i <= 4; i++) f.ajouter(`photo FICTIVE secrète ${i}.jpg`, 'image/jpeg', paule.id);
    const pdf1 = f.ajouter('lettre FICTIVE secrète.pdf', 'application/pdf', paule.id, pdfFictif());
    const marc = f.ajouter('r_Marc Pdf-FICTIF', D, rel.id);
    const divers = f.ajouter('Divers FICTIF', D, marc.id);
    f.ajouter('facture FICTIVE secrète.pdf', 'application/pdf', divers.id, pdfFictif());
    f.ajouter('texte FICTIF secret.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', divers.id);
    f.ajouter('r_Zoé Rien-FICTIF', D, rel.id);
    f.ajouter('notes FICTIVES secrètes.txt', 'text/plain', rel.id);
    // Un autre « Relations » rangé ailleurs (pas à la racine) : ignoré.
    const ailleurs = f.ajouter('Ailleurs FICTIF', D);
    f.ajouter('Relations', D, ailleurs.id);
    return { pdf1 };
  }

  // ----- 09/11/2026 (décision de Max, séance 1) : écriture LIMITÉE du compte Cap et tableur « Commandes vocales (Cap) » -----
  await testAsync('Compte Cap, écriture LIMITÉE (09/11/2026, FAUX) : seuls passent : créer un tableur, poser la marque (appProperties seuls), écrire ou ajouter des cases ; refusés AVANT Google : suppression, corbeille, déplacement, renommage, partage, effacement, mise en page ; la lecture reste en lecture seule', async c => {
    const { m } = connecterCompteFictif(c);
    const ok = (url, methode, corps = '') => m.ecritureAutorisee(new URL(url), methode, corps);
    const ID = 'FICTIF_tableur_cap_0123456789';
    attendre(ok('https://sheets.googleapis.com/v4/spreadsheets', 'POST', '{}'), 'créer refusé');
    attendre(ok(`https://www.googleapis.com/drive/v3/files/${ID}?fields=id`, 'PATCH', '{"appProperties":{"cap_role":"x"}}'), 'marque refusée');
    attendre(ok(`https://sheets.googleapis.com/v4/spreadsheets/${ID}/values/${encodeURIComponent("'Commandes'!A1:F1")}?valueInputOption=RAW`, 'PUT', '{}'), 'écrire refusé');
    attendre(ok(`https://sheets.googleapis.com/v4/spreadsheets/${ID}/values/${encodeURIComponent("'Commandes'!A:F")}:append?valueInputOption=RAW&insertDataOption=INSERT_ROWS`, 'POST', '{}'), 'ajouter refusé');
    const refus = [
      [`https://www.googleapis.com/drive/v3/files/${ID}`, 'DELETE', ''],
      [`https://www.googleapis.com/drive/v3/files/${ID}`, 'PATCH', '{"trashed":true}'],
      [`https://www.googleapis.com/drive/v3/files/${ID}`, 'PATCH', '{"name":"autre FICTIF"}'],
      [`https://www.googleapis.com/drive/v3/files/${ID}?addParents=abc&removeParents=def`, 'PATCH', '{"appProperties":{"a":"b"}}'],
      [`https://www.googleapis.com/drive/v3/files/${ID}`, 'PATCH', '{"appProperties":{"a":"b"},"name":"x"}'],
      [`https://www.googleapis.com/drive/v3/files/${ID}/permissions`, 'POST', '{"role":"writer"}'],
      [`https://sheets.googleapis.com/v4/spreadsheets/${ID}/values/${encodeURIComponent("'Commandes'!A1:F9")}:clear`, 'POST', '{}'],
      [`https://sheets.googleapis.com/v4/spreadsheets/${ID}/values:batchClear`, 'POST', '{}'],
      [`https://sheets.googleapis.com/v4/spreadsheets/${ID}:batchUpdate`, 'POST', '{"requests":[{"deleteDimension":{}}]}'],
      ['https://www.googleapis.com/drive/v3/files', 'POST', '{"name":"x"}'],
      ['http://sheets.googleapis.com/v4/spreadsheets', 'POST', '{}'],
      ['https://sheets.googleapis.com/v4/spreadsheets?fields=x', 'POST', '{}']
    ];
    for (const [url, methode, corps] of refus) attendre(!ok(url, methode, corps), `laissé passer : ${methode} ${url} ${corps}`);
    const avant = c.requetes.length;
    await attendreRejet(() => m.appelerEcriture(`https://www.googleapis.com/drive/v3/files/${ID}`, { method: 'DELETE' }), 'non autorisée');
    attendreEgal(c.requetes.length, avant, 'une demande refusée est partie chez Google');
    await attendreRejet(() => m.appeler(`https://www.googleapis.com/drive/v3/files/${ID}`, { method: 'PATCH', body: '{}' }), 'Lecture seule');
    for (const mot of ['DELETE', 'batchClear', 'deleteDimension', 'permissions']) attendre(!SOURCE_TABLEUR_CAP_TEST.includes(mot), `« ${mot} » dans tableur_cap.js`);
    attendre(!/method:\s*'DELETE'/.test(SOURCE_COMPTE_RELATIONS_C77), 'une suppression dans le compte Cap');
  });

  test('Tableur de Cap (09/11/2026) : son fichier n’efface rien, ne touche pas au tableur modèle (lecture seule), n’appelle ni l’IA ni fetch directement', () => {
    const src = SOURCE_TABLEUR_CAP_TEST;
    for (const mot of ['DELETE', ':clear', 'batchClear', 'deleteDimension', 'trashed: true', 'fetch(', 'XMLHttpRequest', 'cerveau', 'anthropic', 'claude', 'innerHTML', 'addParents'])
      attendre(!src.includes(mot), `tableur_cap.js contient « ${mot} »`);
  });

  await testAsync('Tableur « Commandes vocales (Cap) » (09/11/2026, séance 1, FAUX Google FICTIF) : créé VIDE à la racine du Drive du compte Cap avec les titres EXACTS du tableur modèle (aucune autre ligne recopiée) et la marque invisible ; retrouvé ensuite (et après un renommage, sur un nouvel appareil) sans jamais un 2e ; modèle jamais écrit ; titres illisibles : rien créé ; pas connecté : rien demandé', async () => {
    const TITRES = ['Commande', 'Intention', 'Bloc', 'Formulation', 'Code commande', 'Remarque (FICTIVE, datée)'];
    const MODELE_ID = 'FICTIF_PRINCIPAL_modele_0123456789';
    const g = { fichiers: new Map(), lectures: [], ecritures: [], numero: 0, csv: [TITRES, ['Navigation', '', 'Mot-clé', 'prénom secret FICTIF', 'NAV-02', '']].map(l => l.map(x => (/[",]/.test(x) ? `"${x.replace(/"/g, '""')}"` : x)).join(',')).join('\n') };
    g.fichiers.set(MODELE_ID, { id: MODELE_ID, nom: 'Commandes vocales', appProperties: {} });
    const reponse = corps => ({ ok: true, status: 200, json: async () => corps, text: async () => corps });
    const lire = async url => {
      const u = new URL(url); g.lectures.push(u.href);
      const chemin = decodeURIComponent(u.pathname);
      let m;
      if (chemin === '/drive/v3/files') {
        const q = u.searchParams.get('q');
        const nom = q.match(/name='([^']+)'/); const k = q.match(/key='([^']+)' and value='([^']+)'/);
        return reponse({ files: [...g.fichiers.values()].filter(f => !f.trashed && ((nom && f.nom === nom[1]) || (k && f.appProperties[k[1]] === k[2]))).map(f => ({ id: f.id })) });
      }
      if ((m = chemin.match(/^\/drive\/v3\/files\/([^/]+)\/export$/))) return reponse(g.csv);
      if ((m = chemin.match(/^\/drive\/v3\/files\/([^/]+)$/))) { const f = g.fichiers.get(m[1]); if (!f) throw new Error('Google n’a pas pu lire (erreur 404). Rien n’a été modifié.'); return reponse({ id: f.id, trashed: Boolean(f.trashed) }); }
      throw new Error(`lecture inattendue ${u.href}`);
    };
    const ecrire = async (url, options) => {
      const u = new URL(url); g.ecritures.push([options.method, u.href]);
      if (u.href.includes(MODELE_ID)) throw new Error('le tableur modèle a été écrit');
      const corps = JSON.parse(options.body); const chemin = decodeURIComponent(u.pathname);
      let m;
      if (chemin === '/v4/spreadsheets') { const id = `FICTIF_tableur_cap_${++g.numero}_abcdef`; g.fichiers.set(id, { id, nom: corps.properties.title, parents: corps.parents || null, appProperties: {}, lignes: [] }); return reponse({ spreadsheetId: id }); }
      if ((m = chemin.match(/^\/drive\/v3\/files\/([^/]+)$/))) { const f = g.fichiers.get(m[1]); f.appProperties = { ...f.appProperties, ...corps.appProperties }; return reponse({}); }
      if ((m = chemin.match(/^\/v4\/spreadsheets\/([^/]+)\/values\/(.+)$/))) { g.fichiers.get(m[1]).lignes.push(...corps.values); return reponse({}); }
      throw new Error(`écriture inattendue ${u.href}`);
    };
    const fauxStockagePT = () => { const m = new Map(); return { getItem: k => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)), removeItem: k => m.delete(k) }; }; // (la même, définie plus loin)
    let connecte = false;
    const s = fauxStockagePT();
    const tc = tableurCap.creer({ lire, ecrire, stockage: s, connecte: () => connecte, lireCsv: commandesVocales.lireCsv });
    attendreEgal((await tc.trouverOuCreer()).raison, 'pas_connecte', 'pas connecté');
    attendreEgal(g.lectures.length + g.ecritures.length, 0, 'Google appelé sans connexion');
    connecte = true;
    const r = await tc.trouverOuCreer();
    attendre(r.cree && r.id, `pas créé : ${JSON.stringify(r)}`);
    const f = g.fichiers.get(r.id);
    attendre(f.nom === 'Commandes vocales (Cap)' && f.parents === null, `nom ou rangement : ${f.nom} ${JSON.stringify(f.parents)}`);
    attendreEgal(f.lignes, [TITRES], 'titres pas recopiés à l’identique, ou une ligne du modèle recopiée');
    attendreEgal(f.appProperties, { cap_role: 'commandes_vocales_cap' }, 'marque');
    attendre(!JSON.stringify(f.lignes).includes('prénom secret'), 'une ligne du modèle recopiée');
    attendreEgal(tc.adresse(), `https://docs.google.com/spreadsheets/d/${r.id}/edit`, 'adresse');
    attendreEgal((await tc.trouverOuCreer()).cree, false, 'recréé');
    f.nom = 'Mes commandes FICTIVES';
    const tc2 = tableurCap.creer({ lire, ecrire, stockage: fauxStockagePT(), connecte: () => true, lireCsv: commandesVocales.lireCsv });
    attendreEgal((await tc2.trouverOuCreer()).id, r.id, 'pas retrouvé par la marque');
    attendreEgal([...g.fichiers.values()].filter(x => x.id !== MODELE_ID).length, 1, 'un 2e tableur créé');
    attendre(!g.ecritures.some(([, url]) => url.includes(MODELE_ID)), 'modèle écrit');
    // Titres illisibles : rien n'est créé.
    g.csv = '';
    for (const x of [...g.fichiers.keys()]) if (x !== MODELE_ID) g.fichiers.get(x).trashed = true;
    const avant = g.numero;
    await attendreRejet(() => tableurCap.creer({ lire, ecrire, stockage: fauxStockagePT(), connecte: () => true, lireCsv: commandesVocales.lireCsv }).trouverOuCreer(), 'titres');
    attendreEgal(g.numero, avant, 'tableur créé sans titres lus');
  });

  await testAsync('Compte Cap (FAUX) : connexion avec lecture seule pour CE compte seulement, identifiant gardé sur le téléphone, retour pris sans gêner la connexion du compte personnel', async c => {
    // Le compte personnel garde exactement ses deux droits limités.
    attendreEgal([...REGLAGES_GOOGLE.autorisations], ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/calendar.app.created'], 'droits du compte personnel');
    // 09/11/2026 (décision de Max, tableur « Commandes vocales (Cap) ») : + drive.file. Avant : ['…/drive.readonly'] seul.
    attendreEgal([...REGLAGES_GOOGLE.autorisations_relations], ['https://www.googleapis.com/auth/drive.readonly', 'https://www.googleapis.com/auth/drive.file'], 'droit du compte Cap');
    const vierge = compteRelationsIsole(c);
    await attendreRejet(() => vierge.seConnecter(), 'identifiant du compte Cap');
    await attendreRejet(() => vierge.enregistrerAdresse('pas un identifiant'), 'incomplet');
    const { m, url } = connecterCompteFictif(c);
    attendreEgal(url.origin + url.pathname, 'https://accounts.google.com/o/oauth2/v2/auth', 'page de Google');
    // 09/11/2026 : + drive.file (avant : drive.readonly seul).
    attendreEgal(url.searchParams.get('scope'), 'https://www.googleapis.com/auth/drive.readonly https://www.googleapis.com/auth/drive.file', 'droit demandé');
    attendreEgal(url.searchParams.get('include_granted_scopes'), 'false', 'droits mélangés');
    attendreEgal(url.searchParams.get('login_hint'), COMPTE_CAP_FICTIF, 'compte proposé à Google');
    attendreEgal(url.searchParams.get('response_type'), 'token', 'type de réponse');
    attendreEgal(url.searchParams.get('client_id'), REGLAGES_GOOGLE.id_client, 'identifiant client');
    attendreEgal(url.searchParams.get('redirect_uri'), REGLAGES_GOOGLE.adresse_retour, 'adresse de retour');
    attendre(m.connecte(), 'compte Cap non connecté au retour');
    attendreEgal(m.adresse(), COMPTE_CAP_FICTIF, 'identifiant nettoyé');
    attendreEgal(c.localStorage.getItem('cap_google_relations_adresse_v1'), COMPTE_CAP_FICTIF, 'identifiant gardé sur le téléphone');
    attendreEgal(c.location.hash, '', 'retour effacé');
    attendreEgal(c.requetes.length, 0, 'réseau au retour');
    // Le compte personnel n'a rien vu de ce retour : pas connecté, aucun message d'alerte.
    const perso = c.connexion();
    attendre(!perso.connecte() && perso.message() === '', `compte personnel gêné : ${perso.message()}`);
    // Un retour du compte personnel n'est pas pris par le module du compte Cap.
    c.localStorage.setItem('cap_google_etat_v1', 'etat-perso-fictif');
    c.location.hash = '#access_token=jeton-perso-fictif&expires_in=3600&token_type=Bearer&state=etat-perso-fictif';
    compteRelationsIsole(c);
    attendre(c.location.hash.includes('jeton-perso-fictif'), 'retour du compte personnel avalé');
    const perso2 = c.connexion();
    attendreEgal(perso2.jeton(), 'jeton-perso-fictif', 'compte personnel');
    attendreEgal(compteRelationsIsole(c).connecte(), true, 'compte Cap toujours connecté');
    // Refus chez Google : message, rien de gardé.
    const c2 = contexteGoogle();
    let m2 = compteRelationsIsole(c2);
    m2.enregistrerAdresse(COMPTE_CAP_FICTIF);
    m2.seConnecter();
    c2.location.hash = `#error=access_denied&state=${c2.redirections[0].searchParams.get('state')}`;
    m2 = compteRelationsIsole(c2);
    attendre(!m2.connecte() && /pas été connecté/.test(m2.message()), 'refus');
    // Changer d'identifiant jette l'ancienne connexion.
    const m3 = compteRelationsIsole(c);
    m3.enregistrerAdresse('autre-compte-fictif@id.gle');
    attendre(!m3.connecte(), 'connexion gardée pour un autre compte');
  });

  await testAsync('Compte Cap (FAUX) : mauvais compte choisi chez Google = connexion jetée, rien lu ; lecture seule imposée', async c => {
    const f = fauxDriveCompteCap(c, { compte: 'perso-fictif@gmail.com' });
    remplirCompteCapFictif(f);
    const { m } = connecterCompteFictif(c);
    await attendreRejet(() => relationsCompte0().compter(m), 'Mauvais compte');
    attendre(!m.connecte(), 'jeton gardé');
    attendre(/perso-fictif@gmail\.com/.test(m.message()), 'compte connecté non nommé');
    attendreEgal(c.requetes.map(q => q.url.pathname), ['/drive/v3/about'], 'lu malgré le mauvais compte');
    // Bon compte : lectures seulement ; toute autre demande est refusée sans rien envoyer.
    const c2 = contexteGoogle();
    fauxDriveCompteCap(c2);
    const { m: bon } = connecterCompteFictif(c2);
    for (const [adresse, options] of [['https://www.googleapis.com/drive/v3/files', { method: 'POST', body: '{}' }],
      ['https://www.googleapis.com/drive/v3/files/x', { method: 'PATCH' }], ['https://www.googleapis.com/drive/v3/files/x', { method: 'DELETE' }],
      ['https://www.googleapis.com/drive/v3/files', { body: 'x' }], ['https://sheets.googleapis.com/v4/spreadsheets/x', {}],
      ['https://www.googleapis.com/upload/drive/v3/files', {}], ['http://www.googleapis.com/drive/v3/files', {}]]) {
      await attendreRejet(() => bon.appeler(adresse, options), adresse.includes('sheets') || adresse.includes('upload') || adresse.startsWith('http:') ? 'non autorisée' : 'Lecture seule');
    }
    attendreEgal(c2.requetes.length, 0, 'demande envoyée');
    // Jeton expiré : rien envoyé.
    c2.maintenant += 3600 * 1000;
    await attendreRejet(() => bon.appeler('https://www.googleapis.com/drive/v3/files'), 'expirée');
    attendreEgal(c2.requetes.length, 0, 'demande envoyée après expiration');
  });

  await testAsync('Compte Cap (FAUX Drive) : comptage par dossier « r_ » (MP3, images, PDF, albums), sous-dossiers et pages suivantes lus, aucun nom de fichier, lectures seulement', async c => {
    const f = fauxDriveCompteCap(c);
    remplirCompteCapFictif(f);
    const { m } = connecterCompteFictif(c);
    const module = relationsCompte0();
    const r = await module.compter(m);
    attendreEgal(r.lignes.map(l => [l.nomDossier, l.mp3, l.images, l.pdf, l.albums, l.sousDossiers, l.autres]),
      [['r_Jean Fictif', 3, 0, 0, 2, 0, 0], ['r_Marc Pdf-FICTIF', 0, 0, 1, 0, 1, 1], ['r_Paule Image-FICTIF', 0, 4, 1, 0, 0, 0], ['r_Zoé Rien-FICTIF', 0, 0, 0, 0, 0, 0]], 'nombres');
    attendreEgal(r.pdfs.length, 2, 'PDF trouvés');
    const texte = module.resumer(r);
    attendreEgal(texte, ['Compte Cap (lecture seule, rien n’est modifié) : 4 dossier(s) « r_ ».',
      'r_Jean Fictif : 3 MP3 · 0 image(s) · 0 PDF · 2 album(s)',
      'r_Marc Pdf-FICTIF : 0 MP3 · 0 image(s) · 1 PDF · 0 album(s) · 1 autre(s) sous-dossier(s) · 1 autre(s) fichier(s)',
      'r_Paule Image-FICTIF : 0 MP3 · 4 image(s) · 1 PDF · 0 album(s)', 'r_Zoé Rien-FICTIF : 0 MP3 · 0 image(s) · 0 PDF · 0 album(s)',
      '1 autre(s) élément(s) dans « Relations » (pas des dossiers « r_ »).', 'Total : 3 MP3, 4 image(s), 2 PDF, 2 album(s).'].join('\n'), 'résumé');
    attendre(!/secr|morceau|photo|lettre|facture|notes|Album FICTIF|Playlist|Divers|\.mp3|\.jpg|\.pdf|\.txt/i.test(texte), 'un nom de fichier est affiché');
    attendre(c.requetes.some(q => q.url.searchParams.get('pageToken')), 'pages suivantes non lues');
    attendre(c.requetes.every(q => q.methode === 'GET'), 'autre chose qu’une lecture');
    attendre(f.autorisations.every(a => a === 'Bearer jeton-compte-cap-fictif'), 'mauvais jeton utilisé');
    // Aucun « Relations » à la racine, ou deux : rien n'est choisi au hasard.
    const c2 = contexteGoogle();
    const f2 = fauxDriveCompteCap(c2);
    const { m: m2 } = connecterCompteFictif(c2);
    attendre(/^Aucun dossier « Relations »/.test(module.resumer(await module.compter(m2))), 'aucun Relations');
    f2.ajouter('Relations', 'application/vnd.google-apps.folder');
    f2.ajouter('Relations', 'application/vnd.google-apps.folder');
    attendre(/^2 dossiers « Relations »/.test(module.resumer(await module.compter(m2))), 'deux Relations');
  });

  // « Documents » FICTIF (lot 2) : dossiers sur plusieurs niveaux, PDF, boucle de dossiers (garde-fou).
  function remplirDocumentsFictif(f) {
    const D = 'application/vnd.google-apps.folder';
    const docs = f.ajouter('Documents', D);
    const papiers = f.ajouter('01 Papiers FICTIF', D, docs.id);
    const n1 = f.ajouter('Niveau 1 FICTIF', D, papiers.id);
    const n2 = f.ajouter('Niveau 2 FICTIF', D, n1.id);
    const n3 = f.ajouter('Niveau 3 FICTIF', D, n2.id);
    const n4 = f.ajouter('Niveau 4 FICTIF', D, n3.id);
    const profond = f.ajouter('papier FICTIF secret profond.pdf', 'application/pdf', n4.id, pdfFictif());
    f.ajouter('vide FICTIF secret.txt', 'text/plain', n1.id);
    const maison = f.ajouter('02 Maison FICTIVE', D, docs.id);
    f.ajouter('plan FICTIF secret.jpg', 'image/jpeg', maison.id);
    f.ajouter('bail FICTIF secret.pdf', 'application/pdf', maison.id, pdfFictif());
    // Boucle : « Niveau 1 » est aussi rangé dans « Niveau 2 » (compté une seule fois).
    n1.parents.push(n2.id);
    // « 02 Maison » est aussi rangé dans « Niveau 3 » : compté une seule fois (avec « 01 Papiers », lu avant).
    maison.parents.push(n3.id);
    f.ajouter('03 Vide FICTIF', D, docs.id);
    f.ajouter('perdu FICTIF secret.pdf', 'application/pdf', docs.id, pdfFictif());
    return { profond };
  }

  await testAsync('Compte Cap (lot 2, FAUX Drive) : comptage rapide en quelques demandes (liste complète, pas une demande par dossier), « Relations » et « Documents » à toute profondeur, boucle sans effet, aucun nom de fichier', async c => {
    const f = fauxDriveCompteCap(c);
    remplirCompteCapFictif(f);
    const { profond } = remplirDocumentsFictif(f);
    const { m } = connecterCompteFictif(c);
    const module = relationsCompte0();
    const r = await module.compter(m);
    // Relations inchangé.
    attendreEgal(module.resumer(r).split('\n').at(-1), 'Total : 3 MP3, 4 image(s), 2 PDF, 2 album(s).', 'Relations');
    const d = r.documents;
    attendreEgal(d.lignes.map(l => [l.nomDossier, l.dossiers, l.pdf, l.images, l.autres]),
      [['01 Papiers FICTIF', 5, 2, 1, 1], ['02 Maison FICTIVE', 0, 0, 0, 0], ['03 Vide FICTIF', 0, 0, 0, 0]], 'Documents');
    attendre(d.pdfs.includes(profond.id) && d.pdfs.length === 3, 'PDF de Documents');
    const texte = module.resumerDocuments(d);
    attendreEgal(texte, ['« Documents » : 3 dossier(s) au premier niveau.',
      '01 Papiers FICTIF : 5 sous-dossier(s) · 2 PDF · 1 image(s) · 1 autre(s) fichier(s)',
      '02 Maison FICTIVE : 0 sous-dossier(s) · 0 PDF · 0 image(s) · 0 autre(s) fichier(s)',
      '03 Vide FICTIF : 0 sous-dossier(s) · 0 PDF · 0 image(s) · 0 autre(s) fichier(s)',
      '1 fichier(s) directement dans « Documents ».',
      'Total « Documents » : 8 dossier(s), 3 PDF, 1 image(s), 1 autre(s) fichier(s).'].join('\n'), 'résumé Documents');
    attendre(!/secr|Niveau \d|\.pdf|\.jpg|\.txt/i.test(texte), 'un nom de fichier ou de sous-dossier est affiché');
    // Quelques demandes : qui est connecté, la racine, puis la liste complète (pages de 2 ici).
    const chemins = c.requetes.map(q => q.url.pathname);
    attendreEgal(chemins.slice(0, 2), ['/drive/v3/about', '/drive/v3/files/root'], 'premières demandes');
    attendreEgal(c.requetes.length, 2 + Math.ceil(f.fichiers.length / 2), 'nombre de demandes');
    attendre(c.requetes.slice(2).every(q => q.url.searchParams.get('q') === 'trashed=false'), 'une demande par dossier');
    attendre(c.requetes.every(q => q.methode === 'GET'), 'autre chose qu’une lecture');
    attendre(/files\(id,name,mimeType,parents,size\)/.test(c.requetes[2].url.searchParams.get('fields')), 'parents non demandés');
    // Sans « Documents », ou avec deux : message clair.
    const c2 = contexteGoogle();
    const f2 = fauxDriveCompteCap(c2);
    const { m: m2 } = connecterCompteFictif(c2);
    attendre(/^Aucun dossier « Documents »/.test(module.resumerDocuments((await module.compter(m2)).documents)), 'aucun Documents');
    f2.ajouter('Documents', 'application/vnd.google-apps.folder');
    f2.ajouter('Documents', 'application/vnd.google-apps.folder');
    attendre(/^2 dossiers « Documents »/.test(module.resumerDocuments((await module.compter(m2)).documents)), 'deux Documents');
  });

  await testAsync('Compte Cap (lot 2, écran, FAUX Drive) : le comptage montre « Relations » puis « Documents », et le bouton PDF compte aussi les PDF de « Documents »', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const f = fauxDriveCompteCap(c);
    remplirCompteCapFictif(f);
    remplirDocumentsFictif(f);
    const { m } = connecterCompteFictif(c);
    const module = relationsCompte0();
    const el = id => ui.parId(id);
    module.brancher(ui.doc, { compte: m, pdfjs: () => module.chargerPdfjs(document, window) });
    el('compter-compte-relations').click();
    await attendreQue(() => /Total « Documents » : 8 dossier\(s\), 3 PDF/.test(el('resume-documents-compte').textContent), `écran : ${el('resume-documents-compte').textContent}`);
    // Deux zones séparées, chacune avec son titre ; « Relations » ne contient plus « Documents ».
    attendre(/Total : 3 MP3, 4 image\(s\), 2 PDF/.test(el('resume-compte-relations').textContent) && !/Documents/.test(el('resume-compte-relations').textContent), 'zone Relations');
    attendreEgal([el('resume-compte-relations').dataset.titre, el('resume-documents-compte').dataset.titre], ['Relations', 'Documents'], 'titres');
    attendre(!el('resume-documents-compte').hidden && el('resume-documents-compte').classList.contains('bloc-resultat'), 'zone Documents cachée');
    attendre(el('resume-compte-relations').compareDocumentPosition(el('resume-documents-compte')) & Node.DOCUMENT_POSITION_FOLLOWING, 'ordre Relations puis Documents');
    attendreEgal(el('pdf-compte-relations').textContent, 'Afficher les PDF dans Cap (5)', 'bouton PDF');
    attendre(!el('pdf-compte-relations').hidden, 'bouton PDF caché');
  });

  test('Lecteur de PDF : pdf.js chargé à la demande depuis Cap (pdfjs/, jamais Internet), une seule fois, nouvel essai possible après un échec', () => {
    const module = relationsCompte0();
    const scripts = [];
    const faux = { head: { appendChild: x => scripts.push(x) }, createElement: () => ({}) };
    const fenetre = {};
    const p1 = module.chargerPdfjs(faux, fenetre);
    attendre(module.chargerPdfjs(faux, fenetre) === p1, 'chargé deux fois');
    attendreEgal(scripts.map(x => x.src), ['pdfjs/pdf.min.js'], 'adresse du lecteur');
    scripts[0].onerror();
    p1.catch(() => {});
    module.chargerPdfjs(faux, fenetre).catch(() => {});
    attendreEgal(scripts.length, 2, 'pas de nouvel essai après un échec');
    fenetre.pdfjsLib = { GlobalWorkerOptions: {} };
    scripts[1].onload();
    attendreEgal(fenetre.pdfjsLib.GlobalWorkerOptions.workerSrc, 'pdfjs/pdf.worker.min.js', 'worker local');
    attendre(window.pdfjsLib && /^3\.11\.174$/.test(window.pdfjsLib.version), 'version de pdf.js');
  });

  await testAsync('Compte Cap (FAUX Drive) : écran (identifiant affiché, connexion, comptage, bouton PDF) et PDF dessiné DANS Cap par pdf.js, page suivante, fermer', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const f = fauxDriveCompteCap(c);
    remplirCompteCapFictif(f);
    const { m } = connecterCompteFictif(c);
    const module = relationsCompte0();
    const el = id => ui.parId(id);
    module.brancher(ui.doc, { compte: m, pdfjs: () => module.chargerPdfjs(document, window) });
    attendreEgal(el('adresse-compte-relations').value, COMPTE_CAP_FICTIF, 'identifiant affiché');
    attendre(el('pdf-compte-relations').hidden, 'bouton PDF trop tôt');
    // Retour de Google : « Réglages du Drive » rouvert, puis le compte connecté affiché (et il reste).
    attendre(el('reglages-drive').open, 'Réglages du Drive pas rouverts au retour');
    await attendreQue(() => el('resume-compte-relations').textContent === `Compte Cap connecté : ${COMPTE_CAP_FICTIF}. Touche « Compter ce que Cap voit dans le compte Cap ».`,
      `message de retour : ${el('resume-compte-relations').textContent}`);
    attendre(!el('resume-compte-relations').hidden, 'message caché');
    attendre(!/jeton/.test(el('resume-compte-relations').textContent), 'jeton affiché');
    const texteBouton = el('compter-compte-relations').textContent;
    el('compter-compte-relations').click();
    // Rond d'attente : tout de suite « Lecture en cours… », bouton grisé, puis texte d'origine.
    attendre(el('compter-compte-relations').disabled && el('compter-compte-relations').classList.contains('en-lecture')
      && el('compter-compte-relations').textContent === 'Lecture en cours…', 'pas de rond d’attente');
    await attendreQue(() => /Total : 3 MP3, 4 image\(s\), 2 PDF/.test(el('resume-compte-relations').textContent), `comptage : ${el('resume-compte-relations').textContent}`);
    await attendreQue(() => !el('compter-compte-relations').disabled, 'bouton resté grisé');
    attendreEgal([el('compter-compte-relations').textContent, el('compter-compte-relations').classList.contains('en-lecture')], [texteBouton, false], 'bouton pas remis');
    attendre(!el('pdf-compte-relations').hidden && el('pdf-compte-relations').textContent === 'Afficher les PDF dans Cap (2)', 'bouton PDF');
    el('pdf-compte-relations').click();
    await attendreReel(() => el('page-pdf-relations').textContent === 'PDF 1 sur 2 · Page 1 sur 2', `PDF : ${el('page-pdf-relations').textContent}`);
    attendre(el('pdf-avant-relations').disabled && !el('pdf-apres-relations').disabled, 'boutons du PDF 1');
    attendre(el('lecteur-pdf-relations').open, 'lecteur fermé');
    const canvas = el('canvas-pdf-relations');
    attendre(canvas.width >= 200 && canvas.height === canvas.width, `taille du dessin ${canvas.width} x ${canvas.height}`);
    const noir = (x, y) => { const p = canvas.getContext('2d').getImageData(Math.floor(canvas.width * x), Math.floor(canvas.height * y), 1, 1).data; return p[3] > 200 && p[0] + p[1] + p[2] < 100; };
    attendre(noir(0.25, 0.25) && !noir(0.75, 0.75), 'page 1 mal dessinée');
    attendre(el('pdf-precedente-relations').disabled && !el('pdf-suivante-relations').disabled, 'boutons de page 1');
    el('pdf-suivante-relations').click();
    await attendreReel(() => el('page-pdf-relations').textContent === 'PDF 1 sur 2 · Page 2 sur 2' && noir(0.75, 0.75), 'page 2');
    attendre(!noir(0.25, 0.25), 'page 2 mal dessinée');
    // PDF suivant : le 2e PDF s'ouvre à sa page 1.
    const mediasAvant = c.requetes.filter(q => q.url.searchParams.get('alt') === 'media').length;
    el('pdf-apres-relations').click();
    await attendreReel(() => el('page-pdf-relations').textContent === 'PDF 2 sur 2 · Page 1 sur 2' && noir(0.25, 0.25), `PDF suivant : ${el('page-pdf-relations').textContent}`);
    attendre(!el('pdf-avant-relations').disabled && el('pdf-apres-relations').disabled, 'boutons du PDF 2');
    attendreEgal(c.requetes.filter(q => q.url.searchParams.get('alt') === 'media').length, mediasAvant + 1, 'PDF suivant non lu');
    const ids = c.requetes.filter(q => q.url.searchParams.get('alt') === 'media').map(q => q.url.pathname);
    attendre(ids.at(-1) !== ids.at(-2), 'toujours le même PDF');
    el('pdf-avant-relations').click();
    await attendreReel(() => el('page-pdf-relations').textContent === 'PDF 1 sur 2 · Page 1 sur 2', 'PDF précédent');
    el('pdf-fermer-relations').click();
    attendre(!el('lecteur-pdf-relations').open, 'lecteur pas fermé');
    attendre(c.requetes.every(q => q.methode === 'GET'), 'modification');
    attendre(c.requetes.some(q => q.url.searchParams.get('alt') === 'media'), 'PDF non lu par le Drive');
    // Connexion depuis l'écran : identifiant écrit, page de Google demandée avec ce compte.
    el('adresse-compte-relations').value = 'Autre-Compte-FICTIF@id.gle';
    el('connecter-compte-relations').click();
    attendreEgal(c.redirections.at(-1).searchParams.get('login_hint'), 'autre-compte-fictif@id.gle', 'compte demandé');
    attendre(/PAS ton compte personnel/.test(el('resume-compte-relations').textContent), 'avertissement');
    // Rien d'automatique : seul le branchement des boutons (hors tests).
    const fin = SOURCE_RELATIONS_COMPTE.slice(SOURCE_RELATIONS_COMPTE.lastIndexOf('})();'));
    attendreEgal(fin.match(/relationsCompte\.\w+/g), ['relationsCompte.brancher', 'relationsCompte.chargerPdfjs'], 'départ automatique');
    attendre(/!\(typeof window !== 'undefined' && window\.CAP_TESTS\)/.test(fin), 'branché dans les tests');
  });

  await testAsync('Compte Cap (confort, FAUX) : au retour d’un refus, « Réglages du Drive » rouvert avec la réponse exacte de Google ; mauvais compte affiché ; sans retour, rien ne s’ouvre', async c => {
    let m = compteRelationsIsole(c);
    m.enregistrerAdresse(COMPTE_CAP_FICTIF);
    m.seConnecter();
    c.location.hash = `#error=access_denied<b>&state=${c.redirections.at(-1).searchParams.get('state')}`;
    m = compteRelationsIsole(c);
    attendre(m.retourRecent(), 'retour non vu');
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const el = id => ui.parId(id);
    relationsCompte0().brancher(ui.doc, { compte: m, pdfjs: async () => { throw new Error('inutile'); } });
    attendre(el('reglages-drive').open, 'Réglages pas rouverts');
    attendreEgal(el('resume-compte-relations').textContent, 'Le compte Cap n’a pas été connecté (refusé ou annulé ; réponse de Google : « access_deniedb »). Rien n’a été lu.', 'réponse de Google');
    attendreEgal(c.requetes.length, 0, 'lecture malgré le refus');
    // Mauvais compte au retour : affiché, connexion jetée.
    const c2 = contexteGoogle();
    fauxDriveCompteCap(c2, { compte: 'perso-fictif@gmail.com' });
    const { m: m2 } = connecterCompteFictif(c2);
    const ui2 = preparerInterface(c2, { largeur: 412, hauteur: 900 });
    relationsCompte0().brancher(ui2.doc, { compte: m2, pdfjs: async () => { throw new Error('inutile'); } });
    await attendreQue(() => /^Mauvais compte : Google a connecté « perso-fictif@gmail\.com »/.test(ui2.parId('resume-compte-relations').textContent), `mauvais compte : ${ui2.parId('resume-compte-relations').textContent}`);
    attendre(!m2.connecte(), 'mauvais compte gardé');
    // Vérification lente : si Max a touché « Compter » entre-temps, son résultat n'est pas écrasé.
    const c4 = contexteGoogle();
    remplirCompteCapFictif(fauxDriveCompteCap(c4));
    const { m: m4 } = connecterCompteFictif(c4);
    let finirVerification;
    const lent = { ...m4, verifier: () => new Promise(ok => { finirVerification = ok; }) };
    const ui4 = preparerInterface(c4, { largeur: 412, hauteur: 900 });
    relationsCompte0().brancher(ui4.doc, { compte: lent, pdfjs: async () => { throw new Error('inutile'); } });
    ui4.parId('compter-compte-relations').click();
    await attendreQue(() => /^Total : /m.test(ui4.parId('resume-compte-relations').textContent), 'comptage');
    finirVerification('Compte Cap connecté : FICTIF.');
    await new Promise(ok => setTimeout(ok, 0));
    attendre(/^Total : /m.test(ui4.parId('resume-compte-relations').textContent), 'résultat du comptage écrasé');
    // Chargement normal (pas de retour de Google) : rien ne s'ouvre, rien n'est lu.
    const c3 = contexteGoogle();
    const m3 = compteRelationsIsole(c3);
    attendre(!m3.retourRecent(), 'retour inventé');
    const ui3 = preparerInterface(c3, { largeur: 412, hauteur: 900 });
    relationsCompte0().brancher(ui3.doc, { compte: m3, pdfjs: async () => { throw new Error('inutile'); } });
    attendre(!ui3.parId('reglages-drive').open && ui3.parId('resume-compte-relations').hidden, 'ouvert sans retour');
    attendreEgal(c3.requetes.length, 0, 'lecture sans retour');
  });

  test('Confort : séparations entre les blocs des Réglages du Drive ; messages des dossiers et de la clé gardés (plus effacés après 2,6 s)', () => {
    const modele = new DOMParser().parseFromString(SOURCE_HTML, 'text/html');
    attendreEgal(modele.querySelectorAll('#reglages-drive > hr.separation-reglages').length, 8, 'séparations');
    attendre(/\.separation-reglages \{[^}]*border-top: 3px solid/.test(SOURCE_STYLE), 'trait invisible');
    for (const texte of ['Clé du sélecteur Google enregistrée sur ce téléphone.', 'Dossier « App Cap » enregistré.']) {
      const i = SOURCE_APP.indexOf(texte);
      attendre(i > 0 && !/^[^)]*\)?, true\)/.test(SOURCE_APP.slice(i + texte.length, i + texte.length + 12)), `${texte} encore effacé`);
    }
  });

  // ----- Musique de « Relations » (07/11/2026) : FAUX Drive, FAUX lecteur (sauf un test du vrai) -----
  const relationsMp30 = () => objetIsole(SOURCE_RELATIONS_MP3, 'relationsMp3', { window: { CAP_TESTS: true } });
  function remplirMusiqueFictive(f) {
    const D = 'application/vnd.google-apps.folder';
    const son = new TextEncoder().encode('ID3 son FICTIF');
    const rel = f.ajouter('Relations', D);
    const ana = f.ajouter('r_Ana Musique-FICTIF', D, rel.id);
    for (const nom of ['Zèbre FICTIF.mp3', '03 - Trois FICTIF.mp3', 'alpha FICTIF.mp3', '01 Un FICTIF.mp3']) f.ajouter(nom, 'audio/mpeg', ana.id, son);
    f.ajouter('pochette FICTIVE.jpg', 'image/jpeg', ana.id);
    const divers = f.ajouter('Divers FICTIF', D, ana.id);
    f.ajouter('caché FICTIF.mp3', 'application/octet-stream', divers.id, son);
    const album = f.ajouter('Album Été FICTIF', D, ana.id);
    for (const nom of ['10 Dix FICTIF.mp3', '2 Deux FICTIF.mp3', '01 Premier FICTIF.mp3', 'Bonus FICTIF.mp3']) f.ajouter(nom, 'audio/mpeg', album.id, son);
    f.ajouter('Album vide FICTIF', D, ana.id);
    const gros = f.ajouter('99 Énorme FICTIF.mp3', 'audio/mpeg', ana.id, son);
    gros.taille = 70 * 1000 * 1000;
    const bob = f.ajouter('r_Bob Seul-FICTIF', D, rel.id);
    const seul = f.ajouter('Seul FICTIF.mp3', 'audio/mpeg', bob.id, son);
    f.ajouter('r_Zoé Sans-Musique-FICTIF', D, rel.id);
    f.ajouter('perdu FICTIF.mp3', 'audio/mpeg', rel.id, son);
    return { seul, gros };
  }
  function fauxLecteurZencoder() {
    const appels = [];
    // « audio » : faux lecteur audio, pour simuler la fin d'un morceau (événement « ended »).
    return { appels, objet: { jouerFichier: (adresse, titre) => appels.push(['jouer', adresse, titre]), arreter: () => appels.push(['arreter']), audio: new EventTarget() } };
  }
  function fausseAdresses() {
    const faites = [];
    const liberees = [];
    let n = 0;
    return { faites, liberees, createObjectURL: contenu => { faites.push(contenu); return `blob:FICTIF-${++n}`; }, revokeObjectURL: a => liberees.push(a) };
  }

  test('Musique : noms affichés sans extension ni numéro, ordre numéro puis alphabétique', () => {
    const m = relationsMp30();
    attendreEgal(['03 - Trois FICTIF.mp3', '01Un.MP3', '12.mp3', 'Sans numéro FICTIF.mp3'].map(m.nomMorceau), ['Trois FICTIF', 'Un', '12', 'Sans numéro FICTIF'], 'noms');
    // Un nom commençant par un signe (« (Live) », « _ ») passe après les morceaux numérotés.
    const tries = m.trier(['b.mp3', '(Live) FICTIF.mp3', '10 x.mp3', 'A.mp3', '_intro FICTIF.mp3', '2 y.mp3', '01 z.mp3'].map(nomFichier => ({ nomFichier })));
    attendreEgal(tries.slice(0, 3).map(x => x.nomFichier), ['01 z.mp3', '2 y.mp3', '10 x.mp3'], 'numéros d’abord');
    attendreEgal(tries.slice(3).map(x => x.nomFichier).filter(n => /^[Ab]/.test(n)), ['A.mp3', 'b.mp3'], 'ordre alphabétique');
  });

  await testAsync('Musique (FAUX Drive) : MP3 d’un dossier « r_ » (morceaux libres puis albums en liste de lecture, numéros continus), dossiers sans musique écartés, lectures seulement', async c => {
    const f = fauxDriveCompteCap(c);
    remplirMusiqueFictive(f);
    const { m } = connecterCompteFictif(c);
    const arbre = await relationsCompte0().lireArbre(m);
    const r = relationsMp30().dossiersAvecMp3(arbre, relationsCompte0().sorte);
    attendreEgal(r.dossiers.map(d => [d.nom, d.musique.total]), [['r_Ana Musique-FICTIF', 10], ['r_Bob Seul-FICTIF', 1]], 'dossiers');
    const ana = r.dossiers[0].musique;
    attendreEgal(ana.libres.map(x => [x.numero, x.nom]), [[1, 'Un FICTIF'], [2, 'Trois FICTIF'], [3, 'Énorme FICTIF'], [4, 'alpha FICTIF'], [5, 'caché FICTIF'], [6, 'Zèbre FICTIF']], 'morceaux libres');
    attendreEgal(ana.albums.map(a => [a.nom, a.morceaux.map(x => [x.numero, x.nom])]),
      [['Album Été FICTIF', [[7, 'Premier FICTIF'], [8, 'Deux FICTIF'], [9, 'Dix FICTIF'], [10, 'Bonus FICTIF']]]], 'album');
    attendre(ana.libres[2].taille === 70 * 1000 * 1000, 'taille lue');
    attendre(c.requetes.every(q => q.methode === 'GET'), 'autre chose qu’une lecture');
  });

  await testAsync('Musique (écran, FAUX Drive) : dossiers en très gros, liste un morceau par ligne (gros numéro + nom), un appui lance le morceau dans le lecteur de Zencoder ; arrêter libère la mémoire', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const f = fauxDriveCompteCap(c);
    const { gros } = remplirMusiqueFictive(f);
    const { m } = connecterCompteFictif(c);
    const el = id => ui.parId(id);
    const z = fauxLecteurZencoder();
    const adresses = fausseAdresses();
    let chargements = 0;
    let vidages = 0;
    const lecteur = async () => { chargements++; return z.objet; };
    lecteur.vider = () => { vidages++; };
    relationsMp30().brancher(ui.doc, { compte: m, arbre: () => relationsCompte0().lireArbre(m), sorte: relationsCompte0().sorte, stockage: c.localStorage,
      lecteur, urls: adresses });
    el('musique-compte-relations').click();
    attendre(el('musique-relations').open, 'fenêtre de musique fermée');
    await attendreQue(() => el('liste-musique-relations').querySelectorAll('button.choix-grand-affichage').length === 2, `dossiers : ${el('etat-musique-relations').textContent}`);
    attendreEgal([...el('liste-musique-relations').querySelectorAll('button')].map(b => b.textContent), ['r_Ana Musique-FICTIF (10 MP3)', 'r_Bob Seul-FICTIF (1 MP3)'], 'boutons des dossiers');
    el('liste-musique-relations').querySelector('button').click();
    const lignes = [...el('liste-musique-relations').querySelectorAll('button.ligne-morceau')];
    attendreEgal(lignes.map(b => [b.querySelector('.numero-morceau').textContent, b.querySelector('.nom-morceau').textContent]).slice(0, 2), [['1', 'Un FICTIF'], ['2', 'Trois FICTIF']], 'lignes');
    attendreEgal(lignes.length, 10, 'nombre de lignes');
    attendreEgal([...el('liste-musique-relations').querySelectorAll('h3')].map(h => h.textContent), ['Morceaux', 'Album Été FICTIF (liste de lecture, 4)'], 'titres');
    // Une seule ligne : gros numéro et nom côte à côte, nom coupé s'il est trop long.
    const styleNom = ui.cadre.contentWindow.getComputedStyle(lignes[0].querySelector('.nom-morceau'));
    attendre(styleNom.whiteSpace === 'nowrap' && styleNom.textOverflow === 'ellipsis', 'nom sur plusieurs lignes');
    attendre(parseFloat(ui.cadre.contentWindow.getComputedStyle(lignes[0].querySelector('.numero-morceau')).fontSize) >= 30, 'numéro pas assez gros');
    attendre(!el('retour-musique-relations').hidden, 'retour aux dossiers caché');
    attendreEgal(z.appels.length, 0, 'lancé sans appui');
    // Appui sur le morceau 2 : lu par le compte Cap, donné au lecteur de Zencoder.
    lignes[1].click();
    attendre(el('lecteur-mp3-relations').open, 'lecteur pas ouvert');
    await attendreQue(() => z.appels.length === 1, `lecteur : ${el('etat-lecteur-mp3').textContent}`);
    attendreEgal(z.appels[0], ['jouer', 'blob:FICTIF-1', '2. Trois FICTIF'], 'morceau lancé');
    const media = c.requetes.filter(q => q.url.searchParams.get('alt') === 'media');
    attendreEgal(media.map(q => decodeURIComponent(q.url.pathname.split('/').pop())), [f.fichiers.find(x => x.name === '03 - Trois FICTIF.mp3').id], 'mauvais fichier lu');
    // Plus de titre en double au-dessus du lecteur : le message est caché une fois le morceau lancé.
    attendre(el('etat-lecteur-mp3').hidden && el('etat-lecteur-mp3').textContent === '', `titre en double : ${el('etat-lecteur-mp3').textContent}`);
    // Plein écran : le lecteur occupe toute la fenêtre, sans marge ni cadre blanc ; le bouton est posé dessus.
    const vue = ui.cadre.contentWindow;
    const boite = el('lecteur-mp3-relations').getBoundingClientRect();
    attendreEgal([boite.left, boite.top, boite.width, boite.height], [0, 0, 412, 900], 'lecteur pas en plein écran');
    const cadreLecteur = el('cadre-lecteur-mp3').getBoundingClientRect();
    attendreEgal([cadreLecteur.left, cadreLecteur.top, cadreLecteur.width, cadreLecteur.height], [0, 0, 412, 900], 'cadre du lecteur pas en plein écran');
    attendreEgal(vue.getComputedStyle(el('lecteur-mp3-relations')).paddingTop, '0px', 'marge intérieure');
    // 08/11/2026 : « Arrêter et fermer » et « Musique en arrière-plan » cachés (geste de haut en bas ; note ronde).
    // La note ronde est posée sur le lecteur, en haut à droite, discrète, au-dessus du cadre de Zencoder.
    const note = el('indicateur-musique').getBoundingClientRect();
    attendre(el('lecteur-mp3-relations').contains(el('indicateur-musique')) && !el('indicateur-musique').hidden, 'note ronde absente du lecteur');
    // 09/11/2026 : la note est à GAUCHE du petit micro de tous les écrans (12 + 52 + 8 px), même taille (52 px).
    // Avant : attendre(note.top >= 0 && note.top <= 60 && note.right >= 412 - 13 && note.width === 48, …)
    // 09/11/2026 (bouton « phrase à apprendre » entre le micro et la note) : la note à 124 px du bord (avant : 72 px).
    attendre(note.top >= 0 && note.top <= 60 && Math.abs(note.right - (412 - 124)) <= 1 && note.width === 52, `note pas en haut à droite : ${JSON.stringify(note)}`);
    attendreEgal(vue.getComputedStyle(el('indicateur-musique')).position, 'fixed', 'note hors du lecteur');
    const centreNote = ui.doc.elementFromPoint(note.left + note.width / 2, note.top + note.height / 2);
    attendre(el('indicateur-musique').contains(centreNote), 'note sous le lecteur');
    // Autre morceau : l'adresse précédente est libérée.
    lignes[6].click();
    await attendreQue(() => z.appels.length === 2, 'deuxième morceau');
    attendreEgal(z.appels[1], ['jouer', 'blob:FICTIF-2', '7. Premier FICTIF'], 'morceau de l’album');
    attendreEgal(adresses.liberees, ['blob:FICTIF-1'], 'mémoire non libérée');
    // Trop gros : refusé sans rien charger.
    const avant = c.requetes.length;
    lignes[2].click();
    await attendreQue(() => /trop gros/.test(el('etat-lecteur-mp3').textContent), 'gros fichier');
    attendreEgal(c.requetes.length, avant, 'gros fichier chargé');
    attendre(gros.taille > relationsMp30().TAILLE_MAX, 'taille');
    // Arrêter et fermer : arrêt, mémoire libérée, chargé une seule fois.
    attendre(!el('etat-lecteur-mp3').hidden, 'message du gros fichier caché');
    el('fermer-lecteur-mp3').click();
    attendre(!el('lecteur-mp3-relations').open, 'lecteur resté ouvert');
    await attendreQue(() => vidages === 1, 'lecteur pas vidé à la fermeture');
    attendreEgal(z.appels.at(-1), ['arreter'], 'pas arrêté');
    attendreEgal(adresses.liberees, ['blob:FICTIF-1', 'blob:FICTIF-2'], 'mémoire non libérée à la fermeture');
    attendre(c.requetes.every(q => q.methode === 'GET'), 'autre chose qu’une lecture');
    // Retour aux dossiers, puis dossier d'un seul morceau : lancement direct.
    el('retour-musique-relations').click();
    el('liste-musique-relations').querySelectorAll('button')[1].click();
    await attendreQue(() => z.appels.length === 4 && z.appels[3][2] === '1. Seul FICTIF', `lancement direct : ${JSON.stringify(z.appels)}`);
    attendre(el('lecteur-mp3-relations').open, 'lecteur pas ouvert pour un seul morceau');
    // Fermeture par le retour du téléphone (sans le bouton : « cancel », puis fermeture) : arrêt et vidage aussi.
    el('lecteur-mp3-relations').dispatchEvent(new Event('cancel'));
    el('lecteur-mp3-relations').close();
    await attendreQue(() => vidages === 2, 'fermeture par le retour : lecteur pas vidé');
    attendreEgal(z.appels.at(-1), ['arreter'], 'musique pas arrêtée par le retour');
    attendreEgal(adresses.liberees.length, 3, 'mémoire non libérée par le retour');
  });

  await testAsync('Musique (écran, FAUX Drive) : un seul dossier avec de la musique = sa liste tout de suite ; fermer sans avoir joué ne charge pas le lecteur ; connexion expirée = message, rien lu', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const f = fauxDriveCompteCap(c);
    const D = 'application/vnd.google-apps.folder';
    const rel = f.ajouter('Relations', D);
    const r = f.ajouter('r_Unique FICTIF', D, rel.id);
    f.ajouter('01 A FICTIF.mp3', 'audio/mpeg', r.id, new Uint8Array(4));
    f.ajouter('02 B FICTIF.mp3', 'audio/mpeg', r.id, new Uint8Array(4));
    const { m } = connecterCompteFictif(c);
    const el = id => ui.parId(id);
    let chargements = 0;
    relationsMp30().brancher(ui.doc, { compte: m, arbre: () => relationsCompte0().lireArbre(m), sorte: relationsCompte0().sorte, stockage: c.localStorage,
      lecteur: async () => { chargements++; return fauxLecteurZencoder().objet; }, urls: fausseAdresses() });
    el('musique-compte-relations').click();
    await attendreQue(() => el('liste-musique-relations').querySelectorAll('button.ligne-morceau').length === 2, 'liste directe');
    attendre(el('retour-musique-relations').hidden, 'retour inutile affiché');
    el('fermer-lecteur-mp3').click();
    attendreEgal(chargements, 0, 'lecteur chargé pour rien');
    c.maintenant += 3600 * 1000;
    el('liste-musique-relations').querySelector('button.ligne-morceau').click();
    // Connexion finie : proposition d'autoriser d'abord ; « Jouer quand même » essaie, puis la place est gardée.
    attendre(!el('avertissement-musique-relations').hidden, 'pas d’avertissement');
    [...el('avertissement-musique-relations').querySelectorAll('button')].find(b => b.textContent === 'Jouer quand même').click();
    await attendreQue(() => /La connexion du compte Cap a expiré/.test(el('etat-lecteur-mp3').textContent), `expiration : ${el('etat-lecteur-mp3').textContent}`);
    attendre(!el('etat-lecteur-mp3').classList.contains('en-lecture'), 'rond resté');
    attendre(!el('reconnecter-lecteur-mp3').hidden, 'bouton d’autorisation caché');
  });

  // Étape 3 : morceau suivant et connexion qui expire.
  function brancherMusique(c, ui, m, z, adresses) {
    relationsMp30().brancher(ui.doc, { compte: m, arbre: () => relationsCompte0().lireArbre(m), sorte: relationsCompte0().sorte,
      stockage: c.localStorage, lecteur: async () => z.objet, urls: adresses || fausseAdresses() });
  }
  async function ouvrirDossierAna(ui) {
    const el = id => ui.parId(id);
    el('musique-compte-relations').click();
    await attendreQue(() => el('liste-musique-relations').querySelectorAll('button.choix-grand-affichage').length === 2, 'dossiers');
    el('liste-musique-relations').querySelector('button').click();
    return [...el('liste-musique-relations').querySelectorAll('button.ligne-morceau')];
  }
  const idsLus = c => c.requetes.filter(q => q.url.searchParams.get('alt') === 'media').map(q => decodeURIComponent(q.url.pathname.split('/').pop()));
  const idDe = (f, nom) => f.fichiers.find(x => x.name === nom).id;

  await testAsync('Musique (étape 3, FAUX Drive) : à la fin d’un morceau, le suivant de la MÊME liste se lance (chargé à l’avance) ; fin de liste = arrêt ; lecteur fermé = rien', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const f = fauxDriveCompteCap(c);
    remplirMusiqueFictive(f);
    const { m } = connecterCompteFictif(c);
    const el = id => ui.parId(id);
    const z = fauxLecteurZencoder();
    brancherMusique(c, ui, m, z);
    const lignes = await ouvrirDossierAna(ui);
    // Morceau 8 de l'album (« Deux ») : le 9 (« Dix ») est chargé pendant l'écoute.
    lignes[7].click();
    await attendreQue(() => z.appels.length === 1 && idsLus(c).includes(idDe(f, '10 Dix FICTIF.mp3')), `préchargement : ${JSON.stringify(idsLus(c))}`);
    attendreEgal(z.appels[0][2], '8. Deux FICTIF', 'morceau lancé');
    const lusAvant = idsLus(c).length;
    z.objet.audio.dispatchEvent(new Event('ended'));
    await attendreQue(() => z.appels.length === 2, 'suivant pas lancé');
    attendreEgal(z.appels[1][2], '9. Dix FICTIF', 'mauvais suivant');
    // Le 9 venait du chargement à l'avance ; le 10 (« Bonus ») est maintenant chargé à son tour.
    await attendreQue(() => idsLus(c).length === lusAvant + 1, 'préchargement du 10');
    attendreEgal(idsLus(c).at(-1), idDe(f, 'Bonus FICTIF.mp3'), 'le 9 relu au lieu du préchargé');
    z.objet.audio.dispatchEvent(new Event('ended'));
    await attendreQue(() => z.appels.length === 3, 'dernier morceau');
    attendreEgal(z.appels[2][2], '10. Bonus FICTIF', 'dernier de l’album');
    // Fin de l'album : rien d'autre (pas de passage à une autre liste).
    z.objet.audio.dispatchEvent(new Event('ended'));
    await new Promise(ok => setTimeout(ok, 50));
    attendreEgal(z.appels.length, 3, 'lecture après la fin de l’album');
    // Morceaux libres : le dernier (6, « Zèbre ») ne passe pas à l'album.
    lignes[5].click();
    await attendreQue(() => z.appels.length === 4, 'morceau 6');
    z.objet.audio.dispatchEvent(new Event('ended'));
    await new Promise(ok => setTimeout(ok, 50));
    attendreEgal(z.appels.length, 4, 'passage des morceaux libres à l’album');
    // Lecteur fermé : une fin de morceau ne relance rien.
    lignes[0].click();
    await attendreQue(() => z.appels.length === 5, 'morceau 1');
    el('fermer-lecteur-mp3').click();
    await attendreQue(() => z.appels.at(-1)[0] === 'arreter', 'pas arrêté');
    const n = z.appels.length;
    z.objet.audio.dispatchEvent(new Event('ended'));
    await new Promise(ok => setTimeout(ok, 50));
    attendreEgal(z.appels.length, n, 'relancé après la fermeture');
    attendre(c.requetes.every(q => q.methode === 'GET'), 'autre chose qu’une lecture');
  });

  await testAsync('Musique (étape 3, FAUX Drive) : connexion bientôt finie = proposition d’autoriser d’abord (place gardée : identifiants et numéro, jamais un nom) ; au retour, « Reprendre la musique au morceau N » en un appui', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const f = fauxDriveCompteCap(c);
    remplirMusiqueFictive(f);
    const { m } = connecterCompteFictif(c);
    const el = id => ui.parId(id);
    const z = fauxLecteurZencoder();
    brancherMusique(c, ui, m, z);
    attendre(el('reprendre-musique-relations').hidden, 'reprise sans place gardée');
    const lignes = await ouvrirDossierAna(ui);
    // Il reste 20 minutes : dernier morceau d'une liste = lancé sans question.
    c.maintenant += 40 * 60 * 1000;
    attendreEgal(m.minutesRestantes(), 20, 'minutes restantes');
    lignes[9].click();
    await attendreQue(() => z.appels.length === 1, 'dernier morceau pas lancé');
    attendre(el('avertissement-musique-relations').hidden, 'question inutile');
    el('fermer-lecteur-mp3').click();
    // Morceau 7 (début de l'album) : question, deux gros boutons.
    lignes[6].click();
    const avert = el('avertissement-musique-relations');
    attendre(!avert.hidden && /finit dans 20 minute/.test(avert.textContent), `avertissement : ${avert.textContent}`);
    attendreEgal([...avert.querySelectorAll('button')].map(b => b.textContent), ['Autoriser la lecture du compte Cap', 'Jouer quand même'], 'boutons');
    attendreEgal(z.appels.filter(a => a[0] === 'jouer').length, 1, 'lancé sans réponse');
    avert.querySelector('button').click();
    const place = JSON.parse(c.localStorage.getItem('cap_musique_reprise_v1'));
    attendreEgal(Object.keys(place).sort(), ['dossier', 'morceau', 'numero'], 'place gardée');
    attendreEgal([place.morceau, place.numero], [idDe(f, '01 Premier FICTIF.mp3'), 7], 'mauvaise place');
    attendre(!/FICTIF/.test(c.localStorage.getItem('cap_musique_reprise_v1')), 'un nom est gardé');
    attendreEgal(c.redirections.at(-1).origin, 'https://accounts.google.com', 'Google pas ouvert');
    // Retour de Google (page rechargée) : le bouton de reprise attend, un appui relance le morceau 7.
    const { m: m2 } = connecterCompteFictif(c);
    const ui2 = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const z2 = fauxLecteurZencoder();
    brancherMusique(c, ui2, m2, z2);
    const reprise = ui2.parId('reprendre-musique-relations');
    attendre(!reprise.hidden, 'bouton de reprise caché');
    attendreEgal(reprise.textContent, 'Reprendre la musique au morceau 7', 'texte de la reprise');
    reprise.click();
    await attendreQue(() => z2.appels.length === 1, `reprise : ${ui2.parId('etat-musique-relations').textContent}`);
    attendreEgal(z2.appels[0][2], '7. Premier FICTIF', 'mauvais morceau repris');
    attendre(ui2.parId('musique-relations').open && ui2.parId('liste-musique-relations').querySelectorAll('button.ligne-morceau').length === 10, 'liste du dossier absente');
    attendreEgal(c.localStorage.getItem('cap_musique_reprise_v1'), null, 'place gardée après la reprise');
    attendre(reprise.hidden, 'bouton de reprise resté');
  });

  await testAsync('Musique (étape 3, FAUX Drive) : connexion qui expire en plein album : le morceau chargé à l’avance joue encore, puis place gardée et bouton « Autoriser » sur le lecteur', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const f = fauxDriveCompteCap(c);
    remplirMusiqueFictive(f);
    const { m } = connecterCompteFictif(c);
    const el = id => ui.parId(id);
    const z = fauxLecteurZencoder();
    brancherMusique(c, ui, m, z);
    const lignes = await ouvrirDossierAna(ui);
    lignes[6].click();
    await attendreQue(() => idsLus(c).includes(idDe(f, '2 Deux FICTIF.mp3')), 'préchargement du 8');
    // La connexion expire pendant le morceau 7.
    c.maintenant += 3600 * 1000;
    z.objet.audio.dispatchEvent(new Event('ended'));
    await attendreQue(() => z.appels.length === 2, 'le morceau chargé à l’avance n’a pas joué');
    attendreEgal(z.appels[1][2], '8. Deux FICTIF', 'morceau de marge');
    z.objet.audio.dispatchEvent(new Event('ended'));
    await attendreQue(() => /La connexion du compte Cap a expiré/.test(el('etat-lecteur-mp3').textContent), `message : ${el('etat-lecteur-mp3').textContent}`);
    attendre(/morceau 9/.test(el('etat-lecteur-mp3').textContent) && !el('etat-lecteur-mp3').hidden, 'numéro absent');
    attendre(!el('reconnecter-lecteur-mp3').hidden, 'bouton caché');
    attendreEgal(JSON.parse(c.localStorage.getItem('cap_musique_reprise_v1')).numero, 9, 'place');
    attendre(!el('reprendre-musique-relations').hidden, 'reprise pas proposée');
    el('reconnecter-lecteur-mp3').click();
    attendreEgal(c.redirections.at(-1).origin, 'https://accounts.google.com', 'Google pas ouvert');
    // Bouton posé sur le lecteur, en bas, visible, sans toucher la note ronde (08/11/2026 : plus de bouton en dessous).
    const autoriser = el('reconnecter-lecteur-mp3').getBoundingClientRect();
    const centreAutoriser = ui.doc.elementFromPoint(autoriser.left + autoriser.width / 2, autoriser.top + autoriser.height / 2);
    attendre(autoriser.bottom <= 900 && autoriser.top >= el('indicateur-musique').getBoundingClientRect().bottom && el('reconnecter-lecteur-mp3').contains(centreAutoriser), 'bouton « Autoriser » mal placé');
  });

  await testAsync('Musique : chargement du lecteur de Zencoder dans un cadre (lecteur_mp3/index.html), une seule fois ; nouvel essai si le lecteur ne répond pas', async () => {
    // Le vrai cadre ne peut pas être chargé dans ces tests (temps simulé du navigateur) : faux cadre.
    const fauxCadre = () => {
      const ecouteurs = [];
      const cadre = { ecouteurs, contentWindow: { location: { href: 'about:blank' } },
        set src(v) { this.adresse = v; },
        addEventListener: (type, f) => ecouteurs.push([type, f]),
        removeEventListener: (type, f) => { const i = ecouteurs.findIndex(e => e[1] === f); if (i >= 0) ecouteurs.splice(i, 1); } };
      return cadre;
    };
    const module = relationsMp30();
    const cadre = fauxCadre();
    const charger = module.chargeurLecteur(cadre);
    const p1 = charger();
    attendre(charger() === p1, 'chargé deux fois');
    attendreEgal(cadre.adresse, 'lecteur_mp3/index.html', 'adresse du lecteur');
    const zencoder = { jouerFichier() {}, arreter() {} };
    cadre.contentWindow.lecteurMp3Zencoder = zencoder;
    // La page blanche (fermeture précédente) finit de charger : ignorée, on attend le lecteur.
    cadre.ecouteurs[0][1]();
    attendreEgal(cadre.ecouteurs.length, 1, 'page blanche prise pour le lecteur');
    cadre.contentWindow.location.href = 'https://cap.fictif/app/lecteur_mp3/index.html';
    cadre.ecouteurs[0][1]();
    attendre(await p1 === zencoder, 'lecteur');
    // Fermeture : vidé (page blanche), puis rechargé à la prochaine ouverture (la sortie du sable se rejoue).
    charger.vider();
    attendreEgal(cadre.adresse, 'about:blank', 'pas vidé');
    const p3 = charger();
    attendre(p3 !== p1 && cadre.adresse === 'lecteur_mp3/index.html', 'pas rechargé');
    // Page chargée sans la ligne ajoutée : refus, puis nouvel essai possible.
    const cadre2 = fauxCadre();
    const charger2 = module.chargeurLecteur(cadre2);
    const p2 = charger2();
    cadre2.contentWindow.location.href = 'https://cap.fictif/app/lecteur_mp3/index.html';
    cadre2.ecouteurs[0][1]();
    await attendreRejet(() => p2, 'pas pu démarrer');
    charger2();
    attendreEgal(cadre2.ecouteurs.length, 1, 'pas de nouvel essai');
  });

  test('Musique : la liste des dossiers et des MP3 ne va jamais vers l’IA ; rien d’effacé ni d’écrit dans le Drive', () => {
    for (const interdit of ['cerveau', 'demandes', 'claude', 'method:', "'POST'", "'PATCH'", "'DELETE'"]) {
      attendre(!SOURCE_RELATIONS_MP3.toLowerCase().includes(interdit.toLowerCase()), `relations_mp3.js contient « ${interdit} »`);
    }
    // Sur le téléphone, une seule chose est gardée : la place pour reprendre (vérifiée par les tests de l'étape 3).
    attendreEgal((SOURCE_RELATIONS_MP3.match(/stockage\.(setItem|getItem|removeItem)\(CLE_REPRISE/g) || []).length, 3, 'stockage');
    // 08/11/2026 : plus la marque du retour direct dans la musique (l’heure de la demande seulement, jamais un nom ni un identifiant).
    attendreEgal((SOURCE_RELATIONS_MP3.match(/stockage\.(setItem|removeItem)\(CLE_RETOUR_MUSIQUE/g) || []).length, 2, 'marque de retour');
    attendre(SOURCE_RELATIONS_MP3.includes('stockage.setItem(CLE_RETOUR_MUSIQUE, String(maintenant()))'), 'marque de retour : autre chose que l’heure de la demande');
    attendreEgal((SOURCE_RELATIONS_MP3.match(/stockage\./g) || []).length, 5, 'autre chose gardé');
    const fin = SOURCE_RELATIONS_MP3.slice(SOURCE_RELATIONS_MP3.lastIndexOf('})();'));
    attendre(/!\(typeof window !== 'undefined' && window\.CAP_TESTS\)/.test(fin), 'branché dans les tests');
  });

  // ----- Étape A (07/11/2026) : accueil sur l'eau, Autre, Réglages, geste haut-bas, alerte partout -----
  const pause = () => new Promise(r => setTimeout(r, 0));
  function brancherAccueil(c, ui, options = {}) {
    const eau = { couleurs: [], effets: [], changerCouleurs(cs, ef) { this.couleurs.push(cs); this.effets.push(ef || null); } };
    const petite = { active: false, demarrages: 0, demarrer() { this.active = true; this.demarrages++; }, arreter() { this.active = false; } };
    const module = accueilCap.brancher(ui.doc, { eau, stockage: c.localStorage, creerPetiteEau: () => petite, ...options });
    return { module, eau, petite };
  }
  const centreDe = el => { const r = el.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; };
  const touchable = (ui, el) => { const touche = ui.doc.elementFromPoint(...centreDe(el)); return touche === el || el.contains(touche); };

  await testAsync('Étape A : accueil = Micro, Chercher, Autre en colonne ; « Autre » (Scanner, Réglages, clair/sombre, Fermer) ; « Réglages » regroupe les réglages, textes des boutons Google INCHANGÉS ; « Chercher » ouvre les tâches', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    brancherAccueil(c, ui);
    const el = id => ui.parId(id);
    for (const id of ['ouvrir-chercher', 'microphone', 'ouvrir-autre']) /* 09/11/2026 : nouvel ordre, gros micro */ attendre(touchable(ui, el(id)), `${id} pas touchable sur l’accueil`); // 08/11/2026 (étape 2) : le micro de l'accueil est « ouvrir-micro » (avant : « microphone », déplacé dans l'écran Micro)
    attendre(el('ecran-autre').hidden && el('ecran-reglages').hidden, 'écran ouvert au départ');
    // Textes des boutons liés à Google : exactement les mêmes qu'avant l'étape A.
    attendreEgal(['connexion-google', 'redonner-acces-google', 'ouvrir-reglages-drive', 'ouvrir-reglages-ia'].map(id => el(id).textContent.trim()),
      ['Autoriser Cap (agenda et Drive)', 'Redonner l’accès à Google', 'Réglages du Drive', 'Réglages du cerveau'], 'texte d’un bouton Google changé');
    for (const id of ['connexion-google', 'ouvrir-reglages-drive', 'ouvrir-reglages-ia', 'synchroniser-maintenant', 'sauvegarder-maintenant', 'ouvrir-reglages-phrases', 'interrupteur-eau', 'ouvrir-aide']) {
      attendre(el('ecran-reglages').contains(el(id)), `${id} pas dans « Réglages »`);
    }
    attendre(el('ecran-autre').contains(el('ouvrir-scanner')) && el('ecran-autre').contains(el('scans-en-attente')), 'Scanner pas dans « Autre »');
    // « Autre » : Scanner, Réglages, interrupteur, Fermer ; l'accueil disparaît.
    el('ouvrir-autre').click();
    transitionEcrans.terminer(ui.doc); // 08/11/2026 : mesures prises APRÈS la transition douce (transition_ecrans.js)
    attendre(!el('ecran-autre').hidden && el('ecran-reglages').hidden, '« Autre » pas ouvert');
    attendreEgal(ui.cadre.contentWindow.getComputedStyle(el('accueil-boutons')).display, 'none', 'accueil encore là sous « Autre »');
    // 08/11/2026 (décision de Max) : « Fermer » de « Autre » caché (le geste de retour suffit) ; avant : touchable.
    attendre(el('fermer-autre').hidden && !el('fermer-autre').getClientRects().length, '« Fermer » encore affiché dans « Autre »');
    for (const id of ['ouvrir-scanner', 'ouvrir-reglages-cap', 'bouton-theme-cap']) attendre(touchable(ui, el(id)), `${id} pas touchable dans « Autre »`);
    attendreEgal(el('ouvrir-scanner').textContent.trim(), 'Scanner', 'nom du bouton Scanner (lecteurs d’écran)');
    // « Réglages » : chaque réglage est atteignable (en faisant défiler si besoin).
    el('ouvrir-reglages-cap').click();
    attendre(!el('ecran-reglages').hidden && el('ecran-autre').hidden, '« Réglages » pas ouvert');
    for (const id of ['connexion-google', 'synchroniser-maintenant', 'ouvrir-reglages-drive', 'sauvegarder-maintenant', 'ouvrir-reglages-ia', 'ouvrir-reglages-phrases', 'interrupteur-eau', 'ouvrir-aide', 'curseur-intensite-eau', 'fermer-reglages']) {
      if (el(id).hidden) continue; // montré seulement quand il sert (ex. « Synchroniser maintenant » sans envoi en attente)
      el(id).scrollIntoView({ block: 'center' });
      attendre(touchable(ui, el(id)), `${id} pas touchable dans « Réglages »`);
    }
    attendre(!ui.doc.querySelector('#ecran-reglages input[type="password"], #ecran-reglages input[type="email"]'), 'champ de connexion dans « Réglages »');
    el('fermer-reglages').click();
    // 09/11/2026 (règle du retour) : Réglages ouvert depuis Autre revient à Autre, puis Autre revient à l'accueil.
    // Avant : « Fermer » de Réglages ramenait directement à l'accueil.
    attendre(el('ecran-reglages').hidden && !el('ecran-autre').hidden, 'Réglages ne revient pas à Autre');
    el('fermer-autre').click();
    attendre(el('ecran-reglages').hidden && el('ecran-autre').hidden && touchable(ui, el('ouvrir-autre')), 'retour à l’accueil impossible');
    el('ouvrir-autre').click();
    el('fermer-autre').click();
    attendre(el('ecran-autre').hidden, '« Fermer » de « Autre »');
    // « Chercher » : l'écran des tâches, avec la barre de recherche, « + » et « Écrire une demande » ; « Fermer » revient.
    // 09/11/2026 (accord de Max) : « Chercher » ouvre l'écran Chercher (4 icônes, barre, « Fermer ») ; To-do ouvre
    // l'écran des tâches. Avant : el('ouvrir-chercher').click() ouvrait directement l'écran des tâches.
    el('ouvrir-chercher').click();
    transitionEcrans.terminer(ui.doc);
    // 09/11/2026 : « Fermer » de Chercher caché (décision de Max) : retiré de la liste des boutons touchables.
    for (const id of ['chercher-todo', 'chercher-documents', 'chercher-media', 'chercher-photo', 'chercher-champ']) attendre(touchable(ui, el(id)), `${id} pas touchable dans l’écran Chercher`);
    el('chercher-todo').click();
    transitionEcrans.terminer(ui.doc); // 08/11/2026 : mesures prises APRÈS la transition douce (transition_ecrans.js)
    attendre(!el('ecran-complet').hidden && !el('zone-recherche').hidden && el('ecran-chercher').hidden, '« Chercher » pas ouvert');
    for (const id of ['saisie-recherche', 'ajouter', 'ouvrir-clavier', 'fermer-chercher']) attendre(touchable(ui, el(id)), `${id} pas touchable dans « Chercher »`);
    el('fermer-chercher').click();
    // 09/11/2026 (règle du retour) : les tâches reviennent à l'écran Chercher, puis l'accueil.
    attendre(el('ecran-complet').hidden && !el('ecran-chercher').hidden, 'les tâches ne reviennent pas à Chercher');
    el('fermer-chercher-cap').click();
    transitionEcrans.terminer(ui.doc);
    attendre(el('ecran-complet').hidden && el('zone-recherche').hidden && touchable(ui, el('ouvrir-chercher')), 'retour depuis « Chercher »');
    // Ancien bouton « Eau » : gardé, caché.
    attendre(el('aller-eau') && el('aller-eau').hidden, 'bouton « Eau » encore visible');
  });

  await testAsync('Étape A : clair / sombre (lune à gauche = sombre par défaut, soleil à droite = clair), gardé sur le téléphone ; eau sombre sur l’accueil, claire dans « Chercher » ; curseur d’intensité en MAQUETTE', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const { eau } = brancherAccueil(c, ui);
    const el = id => ui.parId(id);
    const html = ui.doc.documentElement;
    attendre(html.classList.contains('theme-cap-sombre') && el('bouton-theme-cap').getAttribute('aria-checked') === 'true', 'sombre pas par défaut');
    attendreEgal(eau.couleurs.at(-1), accueilCap.EAU_SOMBRE.map(x => [...x]), 'eau pas sombre sur l’accueil');
    attendre(eau.effets.at(-1) === ecranEau.EAU_V2, 'effets de l’eau v2 absents en sombre');
    el('ouvrir-autre').click();
    const curseur = () => el('bouton-theme-cap').querySelector('.curseur-theme').getBoundingClientRect();
    const gauche = curseur().left;
    el('bouton-theme-cap').click();
    attendre(html.classList.contains('theme-cap-clair') && !html.classList.contains('theme-cap-sombre'), 'pas passé en clair');
    attendreEgal(c.localStorage.getItem(accueilCap.CLE_THEME), 'clair', 'choix non gardé');
    // 08/11/2026 (accord de Max) : clair sur l'eau = couleurs de la visionneuse et du lecteur de Zencoder, sans effets v2.
    attendreEgal(eau.couleurs.at(-1), accueilCap.EAU_CLAIRE.map(x => [...x]), 'eau pas aux couleurs de Zencoder en mode clair');
    attendreEgal(accueilCap.EAU_CLAIRE.map(x => [...x]), [[201, 227, 221], [156, 182, 184]], 'couleurs claires de Zencoder');
    attendreEgal(eau.effets.at(-1), null, 'effets v2 en mode clair');
    // Doigt qui glisse : 4 en clair sur l'eau ; 7 (inchangé) dans « Chercher » et en sombre.
    attendreEgal(ecranEau.forceGlisse(ui.doc), 4, 'doigt pas adouci en mode clair');
    ui.doc.body.classList.add('vue-complete');
    attendreEgal(ecranEau.forceGlisse(ui.doc), ecranEau.EAU.forceGlisse, 'doigt changé dans « Chercher »');
    ui.doc.body.classList.remove('vue-complete');
    // 08/11/2026 : le glissement du curseur (0,25 s) avance en temps RÉEL : attente réelle (test instable sinon).
    await attendreReel(() => curseur().left > gauche, 'le curseur ne va pas vers le soleil (droite)');
    el('bouton-theme-cap').click();
    attendreEgal(c.localStorage.getItem(accueilCap.CLE_THEME), 'sombre', 'retour au sombre non gardé');
    attendreEgal([ecranEau.forceGlisse(ui.doc), ecranEau.EAU.forceGlisse], [7, 7], 'doigt changé en mode sombre');
    el('fermer-autre').click();
    // « Chercher » (écran des tâches) : toujours clair, même en mode sombre.
    el('ouvrir-chercher').click();
    el('chercher-todo').click(); // 09/11/2026 : l'écran des tâches s'ouvre par To-do (avant : par « Chercher » directement)
    await pause();
    attendreEgal(eau.couleurs.at(-1), null, 'eau sombre derrière les tâches');
    attendreEgal(eau.effets.at(-1), null, 'effets v2 derrière les tâches');
    el('fermer-chercher').click();
    await pause();
    attendreEgal(eau.couleurs.at(-1), accueilCap.EAU_SOMBRE.map(x => [...x]), 'eau pas redevenue sombre');
    // Choix relu au démarrage.
    c.localStorage.setItem(accueilCap.CLE_THEME, 'clair');
    const ui2 = preparerInterface(c, { largeur: 412, hauteur: 900 });
    brancherAccueil(c, ui2);
    attendre(ui2.doc.documentElement.classList.contains('theme-cap-clair') && ui2.parId('bouton-theme-cap').getAttribute('aria-checked') === 'false', 'choix clair non relu');
    // Curseur d'intensité : maquette, valeur gardée sous la clé de Zencoder, rien d'autre ne bouge.
    attendreEgal(el('curseur-intensite-eau').value, '100', 'valeur par défaut');
    const avant = eau.couleurs.length;
    el('curseur-intensite-eau').value = '40';
    el('curseur-intensite-eau').dispatchEvent(new Event('input'));
    attendreEgal(c.localStorage.getItem('cap_intensite_eau'), '40', 'valeur non gardée');
    attendreEgal(eau.couleurs.length, avant, 'le curseur maquette commande quelque chose');
    const ui3 = preparerInterface(c, { largeur: 412, hauteur: 900 });
    brancherAccueil(c, ui3);
    attendreEgal(ui3.parId('curseur-intensite-eau').value, '40', 'valeur non relue');
    attendre(/maquette, non reliée/.test(ui3.doc.querySelector('label[for="curseur-intensite-eau"]').textContent), 'étiquette « maquette » absente');
  });

  test('Eau v2 de Zencoder (07/11/2026) : réglages repris tels quels ; en sombre, liseré clair sur le haut des vagues et eau qui bouge ; sans effets, l’eau d’avant', () => {
    attendreEgal(JSON.parse(JSON.stringify(ecranEau.EAU_V2)), { houle: { intensite: 0.15, vitesse: 0.00022, frequence: 1.6 },
      reflet: { intensite: 0.5, vitesse: 0.00018, taille: 2.2 }, lisereCrete: { intensite: 0.35, couleur: [214, 230, 226] } }, 'réglages de Zencoder');
    const faire = effets => {
      const toile = document.createElement('canvas');
      toile.style.cssText = 'position:fixed;left:0;top:0;width:200px;height:200px;';
      document.body.append(toile);
      const couche = ecranEau.creerCouche(toile, { raf: () => 1, caf: () => {}, couleurs: accueilCap.EAU_SOMBRE.map(c => [...c]), effets });
      couche.demarrer();
      couche.perturber(0.5, 0.5, 40, 4);
      for (let i = 1; i <= 4; i++) couche.avancer(i * 16);
      const pixels = Array.from(couche.pixels());
      couche.arreter();
      toile.remove();
      return pixels;
    };
    const sans = faire(null);
    const avec = faire(ecranEau.EAU_V2);
    const clarte = px => { let max = 0; for (let i = 0; i < px.length; i += 4) max = Math.max(max, px[i] + px[i + 1] + px[i + 2]); return max; };
    const moyenne = px => { let s = 0; for (let i = 0; i < px.length; i += 4) s += px[i] + px[i + 1] + px[i + 2]; return s / (px.length / 4); };
    attendre(clarte(avec) > clarte(sans) + 150, `pas de liseré clair sur les vagues (${clarte(avec)} contre ${clarte(sans)})`);
    attendre(Math.abs(moyenne(avec) - moyenne(sans)) < 40, 'l’eau v2 change toute la teinte');
    attendre(sans.length === avec.length && sans.some((v, i) => v !== avec[i]), 'aucune différence avec les effets');
  });

  await testAsync('Étape A : geste net de HAUT EN BAS sur l’accueil = retour à l’eau seule ; jamais pour un geste court, lent, de travers, depuis le tout haut, ni quand quelque chose est ouvert', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    let temps = 0;
    const { module } = brancherAccueil(c, ui, { maintenant: () => temps });
    const el = id => ui.parId(id);
    let retours = 0;
    el('aller-eau').addEventListener('click', () => { retours++; });
    const geste = (x, y, fx, fy, duree = 200) => {
      temps = 0;
      const debut = new Event('touchstart', { bubbles: true });
      Object.defineProperties(debut, { touches: { value: [{ clientX: x, clientY: y }] }, changedTouches: { value: [] } });
      ui.doc.elementFromPoint(x, y).dispatchEvent(debut);
      temps = duree;
      const fin = new Event('touchend', { bubbles: true });
      Object.defineProperties(fin, { touches: { value: [] }, changedTouches: { value: [{ clientX: fx, clientY: fy }] } });
      ui.doc.elementFromPoint(x, y).dispatchEvent(fin);
    };
    attendreEgal(module.GESTE.fractionHauteur, 0.3, 'seuil de hauteur');
    geste(200, 200, 205, 500);
    attendreEgal(retours, 1, 'geste net (300 px sur 900, droit, rapide) sans retour à l’eau');
    // Même départ SUR un bouton de l'accueil : le geste compte aussi (« n'importe où »).
    const [mx, my] = centreDe(el('ouvrir-chercher'));
    geste(mx, my - 100, mx, my + 220);
    attendreEgal(retours, 2, 'geste parti d’un bouton ignoré');
    for (const [nom, args] of [['court', [200, 200, 200, 400]], ['lent', [200, 200, 200, 600, 1500]], ['de travers', [100, 200, 300, 500]],
      ['tout en haut', [200, 20, 200, 500]], ['vers le haut', [200, 700, 200, 200]]]) {
      geste(...args);
      attendreEgal(retours, 2, `geste ${nom} pris pour un retour à l’eau`);
    }
    // Quelque chose d'ouvert : « Autre », « Chercher », une fenêtre : rien.
    el('ouvrir-autre').click();
    geste(200, 200, 200, 600);
    el('fermer-autre').click();
    el('ouvrir-chercher').click();
    geste(200, 200, 200, 600);
    // 09/11/2026 : l'écran Chercher (fermé par son « Fermer »), puis l'écran des tâches par To-do.
    // Avant : el('ouvrir-chercher').click() ouvrait directement l'écran des tâches.
    el('fermer-chercher-cap').click();
    el('ouvrir-chercher').click();
    el('chercher-todo').click();
    geste(200, 200, 200, 600);
    el('fermer-chercher').click();
    el('fermer-chercher-cap').click(); // 09/11/2026 (règle du retour) : les tâches reviennent à Chercher, qu'on ferme aussi
    el('clavier').showModal();
    geste(200, 200, 200, 600);
    el('clavier').close();
    attendreEgal(retours, 2, 'retour à l’eau alors que quelque chose est ouvert');
    geste(200, 200, 200, 600);
    attendreEgal(retours, 3, 'geste plus pris en compte après fermeture');
  });

  await testAsync('Étape A : alerte « Redonner l’accès à Google » partout : sous sa petite eau sur les écrans de Cap, DANS la fenêtre ouverte (musique…) au-dessus de l’eau ; ne cache aucun bouton ; texte inchangé', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const { petite } = brancherAccueil(c, ui);
    const el = id => ui.parId(id);
    const alerte = el('alerte-google');
    const place = alerte.previousSibling;
    attendre(place && place.nodeType === 8, 'repère de place absent');
    attendre(!petite.active, 'petite eau sans alerte');
    el('texte-alerte-google').textContent = 'Google a refusé (FICTIF).';
    alerte.hidden = false;
    await pause();
    attendre(alerte.classList.contains('alerte-sous-eau') && petite.active, 'alerte pas sous l’eau sur l’accueil');
    attendreEgal(ui.cadre.contentWindow.getComputedStyle(el('eau-alerte')).opacity, '0.35', 'eau de l’alerte pas à 35 %');
    attendreEgal(ui.cadre.contentWindow.getComputedStyle(el('eau-alerte')).pointerEvents, 'none', 'l’eau de l’alerte capte les touchers');
    attendre(touchable(ui, el('redonner-acces-google')), 'bouton de l’alerte pas touchable');
    // Elle ne cache aucun bouton de l'accueil, ni de « Autre », ni de « Chercher ».
    for (const id of ['ouvrir-chercher', 'microphone', 'ouvrir-autre']) /* 09/11/2026 : nouvel ordre, gros micro */ attendre(touchable(ui, el(id)), `${id} caché par l’alerte`); // 08/11/2026 (étape 2) : le micro de l'accueil est « ouvrir-micro » (avant : « microphone », déplacé dans l'écran Micro)
    el('ouvrir-autre').click();
    await pause();
    transitionEcrans.terminer(ui.doc); // 08/11/2026 : mesures APRÈS la transition douce ; « Fermer » de « Autre » caché (décision de Max)
    for (const id of ['ouvrir-scanner', 'ouvrir-reglages-cap', 'bouton-theme-cap', 'redonner-acces-google']) attendre(touchable(ui, el(id)), `${id} caché dans « Autre »`);
    el('fermer-autre').click();
    el('ouvrir-chercher').click();
    await pause();
    transitionEcrans.terminer(ui.doc);
    // 09/11/2026 : l'écran Chercher d'abord (icônes, barre, « Fermer », alerte), puis l'écran des tâches par To-do.
    for (const id of ['chercher-todo', 'chercher-photo', 'chercher-champ', 'redonner-acces-google']) attendre(touchable(ui, el(id)), `${id} caché dans l’écran Chercher`); // 09/11/2026 : sans « Fermer » (caché)
    el('chercher-todo').click();
    await pause();
    transitionEcrans.terminer(ui.doc);
    for (const id of ['fermer-chercher', 'saisie-recherche', 'redonner-acces-google']) attendre(touchable(ui, el(id)), `${id} caché dans « Chercher »`);
    el('fermer-chercher').click();
    // Lecteur de musique ouvert (fenêtre au-dessus de tout) : l'alerte y est posée, au-dessus de l'eau, touchable.
    el('lecteur-mp3-relations').showModal();
    await pause();
    attendre(el('lecteur-mp3-relations').contains(alerte), 'alerte pas dans la fenêtre de musique');
    attendre(alerte.classList.contains('alerte-dans-fenetre') && !alerte.classList.contains('alerte-sous-eau') && !petite.active, 'alerte encore « sous l’eau » dans la musique');
    attendre(touchable(ui, el('redonner-acces-google')), 'bouton de l’alerte pas touchable dans la musique');
    // 08/11/2026 : la note ronde (seul bouton de Cap posé sur le lecteur) passe SOUS l'alerte, touchable.
    el('indicateur-musique').hidden = false;
    el('lecteur-mp3-relations').appendChild(el('indicateur-musique'));
    attendre(touchable(ui, el('indicateur-musique')) && el('indicateur-musique').getBoundingClientRect().top >= alerte.getBoundingClientRect().bottom, 'note ronde cachée par l’alerte');
    el('indicateur-musique').hidden = true;
    attendre(el('etat-lecteur-mp3').getBoundingClientRect().top >= alerte.getBoundingClientRect().bottom || el('etat-lecteur-mp3').hidden, 'message du lecteur sous l’alerte');
    el('lecteur-mp3-relations').close();
    await pause();
    attendre(alerte.previousSibling === place && alerte.classList.contains('alerte-sous-eau') && petite.active, 'alerte pas revenue à sa place');
    alerte.hidden = true;
    await pause();
    attendre(!petite.active && !ui.doc.documentElement.classList.contains('alerte-google-visible'), 'petite eau encore active sans alerte');
    attendreEgal(el('redonner-acces-google').textContent, 'Redonner l’accès à Google', 'texte du bouton changé');
  });

  await testAsync('Étape A (musique) : « Redonner l’accès à Google » pendant la musique = place du morceau gardée (dossier et numéro, jamais un nom)', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const f = fauxDriveCompteCap(c);
    remplirMusiqueFictive(f);
    const { m } = connecterCompteFictif(c);
    const z = fauxLecteurZencoder();
    brancherMusique(c, ui, m, z);
    const lignes = await ouvrirDossierAna(ui);
    lignes[7].click();
    await attendreQue(() => z.appels.length === 1, 'morceau pas lancé');
    ui.parId('alerte-google').hidden = false;
    ui.parId('redonner-acces-google').click();
    const place = JSON.parse(c.localStorage.getItem('cap_musique_reprise_v1'));
    attendreEgal([Object.keys(place).sort(), place.numero], [['dossier', 'morceau', 'numero'], 8], 'place non gardée');
    attendre(!/FICTIF/.test(c.localStorage.getItem('cap_musique_reprise_v1')), 'un nom est gardé');
  });

  await testAsync('Mode conversation : « Arrêter » répond au VRAI doigt (il n’est plus traversé par le toucher), sur l’accueil sous l’eau comme dans « Chercher »', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const bandeau = ui.parId('bandeau-live');
    const bouton = ui.parId('arreter-live');
    bandeau.hidden = false;
    const centre = el => { const r = el.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; };
    for (const ecran of ['accueil', 'chercher']) {
      if (ecran === 'chercher') ui.parId('basculer-vue').click();
      transitionEcrans.terminer(ui.doc); // 08/11/2026 : mesures prises APRÈS la transition douce (transition_ecrans.js)
      const touche = ui.doc.elementFromPoint(...centre(bouton));
      attendre(touche === bouton || bouton.contains(touche), `« Arrêter » traversé par le doigt (${ecran}) : ${touche ? (touche.id || touche.tagName) : 'rien'}`);
      attendreEgal(ui.cadre.contentWindow.getComputedStyle(bouton).pointerEvents, 'auto', `« Arrêter » ne prend pas le toucher (${ecran})`);
    }
    // La barre du bas laisse toujours passer les touchers ailleurs (vers l'eau).
    attendreEgal(ui.cadre.contentWindow.getComputedStyle(ui.doc.querySelector('footer.dictee')).pointerEvents, 'none', 'barre du bas qui capte les touchers');
  });

  // ----- Étape B, lot 1 (07/11/2026) : visionneuse de Zencoder branchée, PDF du Drive -----
  const visionneuseCap0 = () => objetIsole(SOURCE_VISIONNEUSE_CAP, 'visionneuseCap', { window: { CAP_TESTS: true } });
  function fausseVisionneuse() {
    const appels = [];
    let vidages = 0;
    const objet = { montrerFichier: (adresse, titre) => appels.push(['montrer', adresse, titre]), fermer: () => appels.push(['fermer']) };
    const charger = async () => objet;
    charger.vider = () => { vidages++; };
    return { appels, charger, vidages: () => vidages };
  }

  await testAsync('Visionneuse (lot 1, FAUX Drive) : PDF lus par le compte Cap et donnés à la visionneuse de Zencoder, 4 au plus, sans nom de fichier ; fermeture = documents fermés, mémoire libérée, cadre vidé ; retour du téléphone aussi', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const f = fauxDriveCompteCap(c);
    const ids = [];
    for (let i = 1; i <= 6; i++) ids.push(f.ajouter(`document secret FICTIF ${i}.pdf`, 'application/pdf', 'root', pdfFictif()).id);
    const { m } = connecterCompteFictif(c);
    const el = id => ui.parId(id);
    const v = fausseVisionneuse();
    const adresses = fausseAdresses();
    const module = visionneuseCap0();
    attendreEgal(module.MAX_DOCUMENTS, 4, 'limite');
    const vis = module.brancher(ui.doc, { compte: m, visionneuse: v.charger, urls: adresses });
    // 08/11/2026 (vignettes) : plusieurs documents passent par les vignettes ; l'ouverture en grand (4 au plus) est
    // gardée sous le nom « ouvrirEnGrand » et testée ici. Avant : await vis.ouvrir(ids.map(id => ({ id })));
    await vis.ouvrirEnGrand(ids.map(id => ({ id })));
    attendre(el('visionneuse-cap').open, 'visionneuse pas ouverte');
    attendreEgal(v.appels.map(x => x.slice(1)), [['blob:FICTIF-1', 'PDF 1.pdf'], ['blob:FICTIF-2', 'PDF 2.pdf'], ['blob:FICTIF-3', 'PDF 3.pdf'], ['blob:FICTIF-4', 'PDF 4.pdf']], 'documents donnés');
    attendreEgal(c.requetes.filter(q => q.url.searchParams.get('alt') === 'media').map(q => decodeURIComponent(q.url.pathname.split('/').pop())), ids.slice(0, 4), 'PDF lus');
    attendre(c.requetes.every(q => q.methode === 'GET'), 'autre chose qu’une lecture');
    attendre(/4 documents au plus à la fois : 2 autre/.test(el('etat-visionneuse').textContent) && !el('etat-visionneuse').hidden, `message : ${el('etat-visionneuse').textContent}`);
    attendre(!/secret|FICTIF \d/.test(el('etat-visionneuse').textContent + JSON.stringify(v.appels)), 'un nom de fichier est montré');
    // Plein écran, bouton « Fermer la visionneuse » posé dessus et touchable.
    const boite = el('visionneuse-cap').getBoundingClientRect();
    attendreEgal([boite.left, boite.top, boite.width, boite.height], [0, 0, 412, 900], 'visionneuse pas en plein écran');
    const centre = e => { const r = e.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; };
    attendreEgal(ui.doc.elementFromPoint(...centre(el('fermer-visionneuse'))), el('fermer-visionneuse'), 'bouton de fermeture caché');
    el('fermer-visionneuse').click();
    attendre(!el('visionneuse-cap').open, 'pas fermée');
    attendreEgal(v.appels.at(-1), ['fermer'], 'documents pas fermés');
    attendreEgal(adresses.liberees, ['blob:FICTIF-1', 'blob:FICTIF-2', 'blob:FICTIF-3', 'blob:FICTIF-4'], 'mémoire pas libérée');
    attendreEgal(v.vidages(), 1, 'cadre pas vidé');
    // Retour du téléphone (« cancel ») : même nettoyage.
    await vis.ouvrir([{ id: ids[5] }]);
    el('visionneuse-cap').dispatchEvent(new Event('cancel'));
    el('visionneuse-cap').close();
    attendreEgal([v.appels.at(-1)[0], v.vidages(), adresses.liberees.length], ['fermer', 2, 5], 'retour du téléphone sans nettoyage');
    // Connexion expirée : message clair, rien d'ouvert.
    c.maintenant += 3600 * 1000;
    const avant = v.appels.length;
    await vis.ouvrir([{ id: ids[0] }]);
    attendre(/connexion du compte Cap a expiré/.test(el('etat-visionneuse').textContent), `expiration : ${el('etat-visionneuse').textContent}`);
    attendreEgal(v.appels.length, avant, 'document ouvert malgré l’expiration');
  });

  await testAsync('Visionneuse (lot 1) : chargement de la page de Zencoder (visionneuse/index.html) dans un cadre, page blanche ignorée, vidée puis rechargée ; nouvel essai si elle ne répond pas', async () => {
    const fauxCadre = () => {
      const ecouteurs = [];
      return { ecouteurs, contentWindow: { location: { href: 'about:blank' } }, set src(v) { this.adresse = v; },
        addEventListener: (type, f) => ecouteurs.push([type, f]),
        removeEventListener: (type, f) => { const i = ecouteurs.findIndex(e => e[1] === f); if (i >= 0) ecouteurs.splice(i, 1); } };
    };
    const module = visionneuseCap0();
    const cadre = fauxCadre();
    const charger = module.chargeur(cadre);
    const p1 = charger();
    attendre(charger() === p1 && cadre.adresse === 'visionneuse/index.html', 'chargée deux fois ou mauvaise adresse');
    cadre.contentWindow.Visualiseur = { montrerFichier() {}, fermer() {} };
    cadre.ecouteurs[0][1]();
    attendreEgal(cadre.ecouteurs.length, 1, 'page blanche prise pour la visionneuse');
    cadre.contentWindow.location.href = 'https://cap.fictif/app/visionneuse/index.html';
    cadre.ecouteurs[0][1]();
    attendre(await p1 === cadre.contentWindow.Visualiseur, 'visionneuse');
    charger.vider();
    attendre(cadre.adresse === 'about:blank' && charger() !== p1 && cadre.adresse === 'visionneuse/index.html', 'pas vidée puis rechargée');
    const cadre2 = fauxCadre();
    const charger2 = module.chargeur(cadre2);
    const p2 = charger2();
    cadre2.contentWindow.location.href = 'https://cap.fictif/app/visionneuse/index.html';
    cadre2.ecouteurs[0][1]();
    await attendreRejet(() => p2, 'pas pu démarrer');
  });

  await testAsync('Visionneuse (lot 1, écran, FAUX Drive) : « Afficher les PDF dans Cap » ouvre la VISIONNEUSE (l’ancien petit lecteur n’est plus utilisé)', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const f = fauxDriveCompteCap(c);
    remplirCompteCapFictif(f);
    const { m } = connecterCompteFictif(c);
    const el = id => ui.parId(id);
    const ouvertures = [];
    relationsCompte0().brancher(ui.doc, { compte: m, pdfjs: async () => { throw new Error('ancien lecteur utilisé'); }, visionneuse: () => ({ ouvrir: async liste => { ouvertures.push(liste); } }) });
    el('compter-compte-relations').click();
    await attendreQue(() => !el('pdf-compte-relations').hidden, 'bouton PDF absent');
    el('pdf-compte-relations').click();
    await pause();
    attendreEgal(ouvertures.length, 1, 'visionneuse pas appelée');
    attendreEgal(ouvertures[0].map(x => Object.keys(x)), [['id'], ['id']], 'liste donnée à la visionneuse');
    attendre(!el('lecteur-pdf-relations').open, 'ancien petit lecteur ouvert');
  });

  await testAsync('Visionneuse et musique (lot 1) : eau de l’accueil EN PAUSE pendant la fenêtre plein écran, relancée après ; alerte Google posée dans la visionneuse, qui descend d’autant', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const fond = { marche: true, arrets: 0, departs: 0, arreter() { this.marche = false; this.arrets++; }, demarrer() { this.marche = true; this.departs++; } };
    const { petite } = brancherAccueil(c, ui, { eau: { fond, eauActive: () => true, changerCouleurs() {} } });
    const el = id => ui.parId(id);
    for (const id of ['visionneuse-cap', 'lecteur-mp3-relations']) {
      el(id).showModal();
      await pause();
      attendre(!fond.marche, `eau pas en pause pendant ${id}`);
      el(id).close();
      await pause();
      attendre(fond.marche, `eau pas relancée après ${id}`);
    }
    // Une petite fenêtre (pas plein écran) ne met pas l'eau en pause.
    const arrets = fond.arrets;
    el('clavier').showModal();
    await pause();
    attendreEgal(fond.arrets, arrets, 'eau en pause pour une petite fenêtre');
    el('clavier').close();
    // Alerte dans la visionneuse : posée dans la fenêtre, au-dessus de l'eau ; la visionneuse descend.
    el('texte-alerte-google').textContent = 'Refus FICTIF.';
    el('alerte-google').hidden = false;
    el('visionneuse-cap').showModal();
    await pause();
    attendre(el('visionneuse-cap').contains(el('alerte-google')) && !petite.active, 'alerte pas dans la visionneuse');
    const centre = e => { const r = e.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; };
    attendreEgal(ui.doc.elementFromPoint(...centre(el('redonner-acces-google'))), el('redonner-acces-google'), 'bouton de l’alerte caché dans la visionneuse');
    attendre(el('cadre-visionneuse').getBoundingClientRect().top >= el('alerte-google').getBoundingClientRect().bottom, 'la visionneuse est sous l’alerte (ses boutons du haut seraient cachés)');
    attendreEgal(ui.doc.elementFromPoint(...centre(el('fermer-visionneuse'))), el('fermer-visionneuse'), 'bouton de fermeture caché par l’alerte');
    el('visionneuse-cap').close();
  });

  // ----- 08/11/2026 : fond de l'eau seule = fond de l'accueil (noir en sombre, pâle en clair) -----
  await testAsync('Eau seule (08/11/2026) : même fond que l’accueil selon lune/soleil (pas de gris puis noir au geste) ; « Revenir aux vagues » lisible sur le noir', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const h = horlogeEau();
    const ecran = ecranEau.monter(ui.parId('ecran-eau'), { raf: h.raf, caf: h.caf, reglages: { fond: 'aucun', dureeSortieMs: 0 } });
    ecran.afficher();
    const fenetre = ui.cadre.contentWindow;
    const fondDe = e => fenetre.getComputedStyle(e).backgroundColor;
    const racine = ui.doc.documentElement;
    attendreEgal([fondDe(ui.parId('ecran-eau')), fondDe(ui.doc.body)], ['rgb(10, 12, 12)', 'rgb(10, 12, 12)'], 'fond de l’eau seule (sombre)');
    racine.classList.add('theme-cap-clair');
    // 08/11/2026 (accord de Max) : fond clair = celui de la visionneuse et du lecteur de Zencoder (#d9e4e2).
    attendreEgal([fondDe(ui.parId('ecran-eau')), fondDe(ui.doc.body)], ['rgb(217, 228, 226)', 'rgb(217, 228, 226)'], 'fond de l’eau seule (clair)');
    const reglageEau = () => ['toile-eau', 'eau-accueil'].map(id => { const s = fenetre.getComputedStyle(ui.parId(id)); return [s.opacity, s.filter]; });
    attendreEgal(reglageEau(), [['0.6', 'blur(1.2px)'], ['0.6', 'blur(1.2px)']], 'eau claire : transparence 60 % et flou 1,2 px');
    ui.doc.body.classList.add('vue-complete');
    attendreEgal(reglageEau()[1], ['0.55', 'blur(1.4px)'], 'eau de « Chercher » changée (étape 2 à part)');
    ui.doc.body.classList.remove('vue-complete');
    racine.classList.remove('theme-cap-clair');
    racine.classList.add('theme-cap-sombre');
    attendreEgal(fondDe(ui.parId('ecran-eau')), 'rgb(10, 12, 12)', 'fond de l’eau seule (sombre, réglage lune)');
    attendreEgal(reglageEau(), [['0.55', 'blur(1.4px)'], ['0.55', 'blur(1.4px)']], 'eau sombre changée');
    // « Revenir aux vagues » sur le noir : contraste texte / bouton (posé sur le fond noir) au moins 4,5.
    const rgb = t => (t.match(/[0-9.]+/g) || []).map(Number);
    const lum = c => { const v = c.slice(0, 3).map(x => x / 255).map(x => (x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4)); return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]; };
    const contraste = (a, b) => { const [l1, l2] = [lum(a), lum(b)].sort((x, y) => y - x); return (l1 + 0.05) / (l2 + 0.05); };
    const style = fenetre.getComputedStyle(ui.parId('bouton-revenir-vagues'));
    const fondBouton = rgb(style.backgroundColor);
    const alpha = fondBouton.length > 3 ? fondBouton[3] : 1;
    const vu = [10, 12, 12].map((c, i) => c * (1 - alpha) + fondBouton[i] * alpha);
    const valeur = contraste(rgb(style.color), vu);
    attendre(valeur >= 4.5, `« Revenir aux vagues » peu lisible sur le noir (contraste ${valeur.toFixed(2)})`);
  });

  // ----- 08/11/2026 : zoom de la visionneuse (pincement sans saut au lâcher, dézoom au quart) -----
  await testAsync('Visionneuse (08/11/2026, vraie page de Zencoder copiée) : pincer puis lâcher ne fait plus sauter le zoom ; dézoom jusqu’au quart, zoom jusqu’à 6 ; le double appui d’un doigt marche toujours', async () => {
    const cadre = document.createElement('iframe');
    cadre.style.cssText = 'position:fixed;left:0;top:0;width:412px;height:800px;border:0';
    document.body.appendChild(cadre);
    try {
      cadre.src = '/visionneuse/index.html';
      await attendreReel(() => cadre.contentWindow && cadre.contentWindow.Visualiseur && cadre.contentDocument.readyState === 'complete', 'visionneuse pas chargée');
      const toile = document.createElement('canvas');
      toile.width = 400; toile.height = 300;
      toile.getContext('2d').fillRect(0, 0, 400, 300);
      cadre.contentWindow.Visualiseur.montrerFichier(toile.toDataURL('image/png'), 'image FICTIVE.png');
      const d = cadre.contentDocument;
      await attendreReel(() => d.querySelector('.carte-document') && parseFloat(d.querySelector('.carte-document').style.width) > 0, 'image pas montrée');
      const carte = d.querySelector('.carte-document');
      const largeur = () => parseFloat(carte.style.width);
      const depart = largeur();
      const W = cadre.contentWindow;
      const pointeur = (type, id, x, y) => carte.dispatchEvent(new W.PointerEvent(type, { pointerId: id, clientX: x, clientY: y, bubbles: true, pointerType: 'touch', isPrimary: id === 1 }));
      // Pincement : doigts de 200 px à `fin` px d'écart, puis les deux doigts levés presque ensemble.
      function pincer(fin) {
        pointeur('pointerdown', 1, 106, 400); pointeur('pointerdown', 2, 306, 400);
        pointeur('pointermove', 1, 206 - fin / 2, 400); pointeur('pointermove', 2, 206 + fin / 2, 400);
        pointeur('pointerup', 1, 206 - fin / 2, 400); pointeur('pointerup', 2, 206 + fin / 2, 400);
      }
      const proche = (a, b) => Math.abs(a - b) < 1;
      pincer(100); // rapetisser de moitié, à partir de la taille d'ouverture
      attendre(proche(largeur(), depart * 0.5), `saut au lâcher après un dézoom : ${largeur()} au lieu de ${depart * 0.5}`);
      pincer(100); // encore : bloqué au quart
      attendre(proche(largeur(), depart * 0.25), `dézoom pas jusqu’au quart : ${largeur()} au lieu de ${depart * 0.25}`);
      pincer(800); // agrandir ×4 → taille d'ouverture
      attendre(proche(largeur(), depart), `retour exact à la taille d’ouverture impossible : ${largeur()}`);
      pincer(400); // agrandir ×2, puis lâcher : il reste agrandi
      attendre(proche(largeur(), depart * 2), `saut au lâcher après un zoom : ${largeur()} au lieu de ${depart * 2}`);
      for (let i = 0; i < 3; i++) pincer(800);
      attendre(proche(largeur(), depart * 6), `zoom maximum : ${largeur()} au lieu de ${depart * 6}`);
      // Double appui d'un doigt : retour à la taille d'ouverture, puis agrandi à 2,5.
      const tape = () => { pointeur('pointerdown', 1, 206, 400); pointeur('pointerup', 1, 206, 400); };
      // L'horloge de la page doit dépasser le délai du double appui (sinon le tout premier appui compte double).
      await attendreReel(() => W.performance.now() > 1000, 'horloge de la visionneuse trop jeune');
      tape(); tape();
      attendre(proche(largeur(), depart), `double appui sans retour à la taille d’ouverture : ${largeur()}`);
      await attendreReel(() => true, '');
      tape(); tape();
      attendre(proche(largeur(), depart * 2.5), `double appui sans agrandissement : ${largeur()}`);
    } finally {
      cadre.remove();
    }
  });

  // ----- 08/11/2026 : « Autre » à 5 icônes et l'œil (visionneuse directe) -----
  await testAsync('Autre (08/11/2026) : 6 icônes symétriques (Scanner et œil, Notes et Agenda grisés, Lecteur et Réglages en bas ; avant : Réglages centré), lune/soleil et Fermer, tout visible sans défiler ; Notes et Agenda disent « pas encore prêt »', async c => {
    for (const [largeur, hauteur] of [[412, 800], [412, 915], [360, 640]]) {
      const ui = preparerInterface(c, { largeur, hauteur });
      brancherAccueil(c, ui);
      const el = id => ui.parId(id);
      el('ouvrir-autre').click();
      transitionEcrans.terminer(ui.doc); // 08/11/2026 : mesures prises APRÈS la transition douce (transition_ecrans.js)
      await pause();
      // 08/11/2026 (décision de Max) : « Fermer » de « Autre » caché (le geste de retour suffit) ; avant : dans la liste.
      const ids = ['ouvrir-scanner', 'ouvrir-oeil', 'ouvrir-notes', 'ouvrir-agenda', 'ouvrir-lecteur', 'ouvrir-reglages-cap', 'bouton-theme-cap'];
      for (const id of ids) {
        const r = el(id).getBoundingClientRect();
        attendre(r.top >= 0 && r.bottom <= hauteur + 1 && (id === 'bouton-theme-cap' || (r.width >= 48 && r.height >= 48)), `${id} hors écran ou trop petit (${largeur}×${hauteur})`);
        if (!el(id).classList.contains('bouton-pas-pret')) attendre(touchable(ui, el(id)), `${id} pas touchable (${largeur}×${hauteur})`);
      }
      attendre(el('ecran-autre').scrollHeight <= el('ecran-autre').clientHeight + 1, `« Autre » défile (${largeur}×${hauteur})`);
      const R = id => el(id).getBoundingClientRect();
      const cx = id => R(id).left + R(id).width / 2;
      const milieu = largeur / 2;
      const proche = (a, b) => Math.abs(a - b) <= 2;
      attendre(proche(R('ouvrir-scanner').top, R('ouvrir-oeil').top) && cx('ouvrir-scanner') < cx('ouvrir-oeil'), 'Scanner et œil pas côte à côte en haut');
      attendre(proche(R('ouvrir-notes').top, R('ouvrir-agenda').top) && R('ouvrir-notes').top >= R('ouvrir-scanner').bottom, 'Notes et Agenda pas au milieu');
      // 08/11/2026 : Lecteur (à gauche) et Réglages (à droite) côte à côte en bas (avant : Réglages seul, centré).
      attendre(R('ouvrir-reglages-cap').top >= R('ouvrir-notes').bottom && proche(R('ouvrir-lecteur').top, R('ouvrir-reglages-cap').top) && cx('ouvrir-lecteur') < cx('ouvrir-reglages-cap'), 'Lecteur et Réglages pas côte à côte en bas');
      attendre(proche(milieu - cx('ouvrir-lecteur'), cx('ouvrir-reglages-cap') - milieu) && proche(R('ouvrir-lecteur').width, R('ouvrir-scanner').width), 'Lecteur pas symétrique ou pas de la même taille');
      attendre(proche(milieu - cx('ouvrir-scanner'), cx('ouvrir-oeil') - milieu) && proche(milieu - cx('ouvrir-notes'), cx('ouvrir-agenda') - milieu), 'pas symétrique');
      attendre(proche(R('ouvrir-reglages-cap').width, R('ouvrir-scanner').width), 'Réglages pas de la même taille');
      attendre(R('bouton-theme-cap').top >= R('ouvrir-reglages-cap').bottom && el('fermer-autre').hidden, 'lune/soleil pas en dessous, ou « Fermer » affiché');
      // Grisés, et un toucher le dit ; fermer efface le message.
      for (const [id, nom] of [['ouvrir-notes', 'Notes'], ['ouvrir-agenda', 'Agenda']]) {
        attendre(el(id).getAttribute('aria-disabled') === 'true' && Number(ui.cadre.contentWindow.getComputedStyle(el(id)).opacity) < 0.5, `${nom} pas grisé`);
        el(id).click();
        attendre(!el('message-autre').hidden && el('message-autre').textContent === `${nom} : pas encore prêt.`, `${nom} : message absent`);
      }
      el('fermer-autre').click();
      attendre(el('message-autre').hidden, 'message gardé après Fermer');
    }
  });

  await testAsync('Œil sans proposition (09/11/2026, décision de Max, bloc c76, FAUX Drive) : 3 PDF FICTIFS dans « Documents » du compte Cap connecté : l’œil ouvre la visionneuse VIDE : aucune vignette, aucun document montré, aucune lecture du Drive, aucun message ; « Choisir un fichier » reste à Max', async c => {
    const f = fauxDriveCompteCap(c);
    remplirCompteCapFictif(f);
    const D = 'application/vnd.google-apps.folder';
    const docs = f.ajouter('Documents', D);
    for (let i = 1; i <= 3; i++) f.ajouter(`papier FICTIF ${i}.pdf`, 'application/pdf', docs.id, pdfFictif());
    const { m } = connecterCompteFictif(c);
    const v = fausseVisionneuse();
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    brancherAccueil(c, ui);
    const el = id => ui.parId(id);
    const vis = visionneuseCap0().brancher(ui.doc, { compte: m, visionneuse: v.charger, urls: fausseAdresses(), stockage: c.localStorage, vignette: async () => new Blob(['vignette FICTIVE']) });
    relationsCompte0().brancher(ui.doc, { compte: m, pdfjs: async () => { throw new Error('ancien lecteur'); }, visionneuse: () => vis, stockage: c.localStorage, maintenant: () => c.maintenant });
    for (let i = 0; i < 5; i++) await pause(); // la vérification du compte (« about ») se fait d'abord, hors de l'œil
    const requetes = c.requetes.length;
    el('ouvrir-oeil').click();
    await attendreQue(() => el('visionneuse-cap').open, 'visionneuse pas ouverte');
    for (let i = 0; i < 5; i++) await pause(); // laisser finir une éventuelle lecture
    attendre(!el('vignettes-cap').open && el('grille-vignettes').querySelectorAll('.vignette').length === 0, 'des propositions (vignettes) sont montrées');
    attendreEgal(v.appels.filter(x => x[0] === 'montrer').length, 0, 'un document a été montré');
    attendreEgal(c.requetes.slice(requetes).map(q => `${q.methode} ${q.url.pathname}`), [], 'le Drive a été lu');
    attendre(el('etat-visionneuse').hidden && !el('etat-visionneuse').textContent, `message affiché : ${el('etat-visionneuse').textContent}`);
    attendre(el('autoriser-visionneuse').hidden, 'bouton Google montré');
  });

  await testAsync('Œil (08/11/2026, FAUX Drive) : ouvre DIRECTEMENT la visionneuse avec les PDF du compte Cap ; sans identifiant ou sans connexion, message clair et « Autoriser la lecture du compte Cap » ; au retour de Google, la visionneuse se rouvre seule ; sans cette demande, retour habituel', async c => {
    const f = fauxDriveCompteCap(c);
    remplirCompteCapFictif(f);
    const v = fausseVisionneuse();
    const adresses = fausseAdresses();
    const brancherTout = (ui, m) => {
      // 08/11/2026 (vignettes) : vignette FICTIVE (la vraie fabrication est testée à part).
      const vis = visionneuseCap0().brancher(ui.doc, { compte: m, visionneuse: v.charger, urls: adresses, stockage: c.localStorage, maintenant: () => c.maintenant,
        vignette: async () => new Blob(['vignette FICTIVE']) });
      // 09/11/2026 (bloc c76) : ce test garde l'ANCIENNE lecture de l'œil (propositions), conservée dans le code ; l'œil de
      // Cap ouvre maintenant la visionneuse vide (test « Œil sans proposition »). Avant : sans propositionsOeil.
      relationsCompte0().brancher(ui.doc, { compte: m, pdfjs: async () => { throw new Error('ancien lecteur'); }, visionneuse: () => vis, stockage: c.localStorage, maintenant: () => c.maintenant, propositionsOeil: true });
      return vis;
    };
    // 1. Aucun identifiant : message, pas de bouton Google.
    let ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    let el = id => ui.parId(id);
    let m = compteRelationsIsole(c);
    brancherTout(ui, m);
    el('ouvrir-oeil').click();
    await pause();
    attendre(el('visionneuse-cap').open && /Identifiant du compte Cap absent/.test(el('etat-visionneuse').textContent) && el('autoriser-visionneuse').hidden, `sans identifiant : ${el('etat-visionneuse').textContent}`);
    el('fermer-visionneuse').click();
    // 2. Identifiant, pas connecté : message + « Autoriser la lecture du compte Cap » (texte exact), touchable.
    m.enregistrerAdresse(COMPTE_CAP_FICTIF);
    el('ouvrir-oeil').click();
    await pause();
    attendre(/pas connecté/.test(el('etat-visionneuse').textContent) && !el('autoriser-visionneuse').hidden, `sans connexion : ${el('etat-visionneuse').textContent}`);
    attendreEgal(el('autoriser-visionneuse').textContent, 'Autoriser la lecture du compte Cap', 'texte du bouton Google');
    attendre(touchable(ui, el('autoriser-visionneuse')), 'bouton « Autoriser » caché');
    attendreEgal(v.appels.length, 0, 'document ouvert sans connexion');
    const avant = c.redirections.length;
    el('autoriser-visionneuse').click();
    attendreEgal(c.redirections.length, avant + 1, 'page de Google pas ouverte');
    const url = c.redirections.at(-1);
    attendreEgal(url.searchParams.get('scope'), REGLAGES_GOOGLE.autorisations_relations.join(' '), 'droits demandés changés');
    attendre(c.localStorage.getItem(visionneuseCap.CLE_RETOUR), 'demande de retour pas notée');
    // 3. Retour de Google (page rechargée) : la visionneuse se rouvre SEULE avec les PDF ; marque effacée.
    c.location.hash = `#access_token=jeton-compte-cap-fictif&expires_in=3600&token_type=Bearer&state=${url.searchParams.get('state')}`;
    m = compteRelationsIsole(c); // lit le retour de Google AVANT le reste de Cap (comme dans la vraie page)
    ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    el = id => ui.parId(id);
    brancherTout(ui, m);
    // 08/11/2026 (vignettes) : plusieurs PDF = vignettes ; toucher une vignette ouvre CE PDF en grand.
    // Avant : les 2 PDF ouverts en grand d'un coup (v.appels.length === 2, ['PDF 1.pdf', 'PDF 2.pdf']).
    await attendreQue(() => el('vignettes-cap').open && el('grille-vignettes').querySelectorAll('.vignette img').length === 2, `vignettes pas montrées au retour : ${el('etat-visionneuse').textContent}`);
    attendre(!el('reglages-drive').open, 'pas la visionneuse au retour');
    attendreEgal(c.localStorage.getItem(visionneuseCap.CLE_RETOUR), null, 'marque gardée');
    el('grille-vignettes').querySelector('.vignette').click();
    await attendreQue(() => v.appels.length === 1, 'vignette touchée : PDF pas ouvert');
    attendre(el('visionneuse-cap').open, 'pas la visionneuse après le toucher');
    attendreEgal(v.appels.map(x => x[2]), ['PDF 1.pdf'], 'PDF donné');
    attendre(c.requetes.every(q => q.methode === 'GET'), 'autre chose qu’une lecture');
    el('fermer-visionneuse').click();
    attendre(el('vignettes-cap').open, 'les vignettes ne reviennent pas après « Fermer la visionneuse »');
    el('fermer-vignettes').click();
    // 4. Connecté : l'œil ouvre directement les vignettes des PDF.
    await attendreQue(() => !el('vignettes-cap').open, 'vignettes pas fermées après « Fermer »');
    el('ouvrir-oeil').click();
    await attendreQue(() => el('vignettes-cap').open && el('grille-vignettes').querySelectorAll('.vignette img').length === 2, 'œil connecté : vignettes pas montrées');
    attendre(el('autoriser-visionneuse').hidden, 'bouton « Autoriser » affiché alors que connecté');
    el('fermer-vignettes').click();
    await attendreQue(() => !el('vignettes-cap').open, 'vignettes pas fermées');
    // 5. Connexion expirée : message et bouton, jamais un écran vide.
    c.maintenant += 3600 * 1000;
    el('ouvrir-oeil').click();
    await pause();
    attendre(el('visionneuse-cap').open && !el('etat-visionneuse').hidden && /expiré/.test(el('etat-visionneuse').textContent) && !el('autoriser-visionneuse').hidden, `expiration : ${el('etat-visionneuse').textContent}`);
    el('fermer-visionneuse').click();
    attendre(el('autoriser-visionneuse').hidden, 'bouton gardé après fermeture');
    // 6. Retour de Google SANS demande récente de la visionneuse : « Réglages du Drive » comme avant.
    m.seConnecter();
    c.localStorage.setItem(visionneuseCap.CLE_RETOUR, String(c.maintenant - visionneuseCap.DUREE_RETOUR_MS - 1));
    c.location.hash = `#access_token=jeton-compte-cap-fictif&expires_in=3600&token_type=Bearer&state=${c.redirections.at(-1).searchParams.get('state')}`;
    m = compteRelationsIsole(c); // lit le retour de Google AVANT le reste de Cap (comme dans la vraie page)
    ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    el = id => ui.parId(id);
    brancherTout(ui, m);
    await pause();
    attendre(el('reglages-drive').open && !el('visionneuse-cap').open, 'retour habituel cassé');
  });

  // ----- 08/11/2026 : lot D, apparence de l'écran de scan (Zencoder) -----
  await testAsync('Scan, lot D (08/11/2026) : fond et eau des autres écrans (sombre et clair), eau de l’accueil en pause ; caméra, « Page 1 », petit « Mode rafale », grille 2×2 (photo, appareil, Google Scan, Fermer) touchable et lisible ; mêmes éléments', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const fond = { marche: true, arreter() { this.marche = false; }, demarrer() { this.marche = true; } };
    const eauScan = { couleurs: [], effets: [], marche: false, touches: 0, changerCouleurs(cs, ef) { this.couleurs.push(cs); this.effets.push(ef || null); },
      demarrer() { this.marche = true; }, arreter() { this.marche = false; }, perturber() { this.touches++; } };
    const { module } = brancherAccueil(c, ui, { eau: { fond, eauActive: () => true, changerCouleurs() {} }, creerEauScanner: () => eauScan });
    const el = id => ui.parId(id);
    const fenetre = ui.cadre.contentWindow;
    const scanner = el('scanner');
    // Mêmes éléments qu'avant le lot D (identifiants utilisés par scan_ecran.js).
    for (const id of ['scanner-camera', 'scanner-video', 'scanner-compteur', 'scanner-rafale', 'scanner-capturer', 'scanner-fichier', 'scanner-google', 'scanner-fermer', 'scanner-revue', 'scanner-pages', 'scanner-etat', 'scanner-proposition', 'titre-scanner']) {
      attendre(scanner.contains(el(id)), `${id} absent de l’écran de scan`);
    }
    attendreEgal(el('scanner-google').textContent.trim(), 'Utiliser Google Scan', 'texte de Google Scan');
    el('scanner-google').hidden = false; // dans l'application Android (pont présent), le bouton est visible
    scanner.showModal();
    await pause();
    // Fond et eau : ceux des autres écrans ; l'eau de l'accueil (cachée) en pause.
    attendreEgal(fenetre.getComputedStyle(scanner).backgroundColor, fenetre.getComputedStyle(ui.doc.body).backgroundColor, 'fond du scan différent (sombre)');
    attendreEgal(fenetre.getComputedStyle(scanner).backgroundColor, 'rgb(10, 12, 12)', 'fond sombre');
    attendre(eauScan.marche && !fond.marche, 'eau du scan arrêtée ou eau de l’accueil pas en pause');
    // 08/11/2026 (demande de Max) : les deux textes retirés (aide et « Tous les scans sont déposés… ») ; rien ne défile.
    attendre(!/bien à plat|Tous les scans sont déposés/.test(scanner.innerText), 'texte retiré encore visible : ' + scanner.innerText.slice(0, 200));
    attendre(scanner.scrollHeight <= scanner.clientHeight + 1, `l’écran de scan défile (${scanner.scrollHeight} > ${scanner.clientHeight})`);
    attendreEgal([eauScan.couleurs.at(-1), eauScan.effets.at(-1)], [accueilCap.EAU_SOMBRE.map(x => [...x]), ecranEau.EAU_V2], 'eau sombre du scan');
    attendreEgal(fenetre.getComputedStyle(el('eau-scanner')).pointerEvents, 'none', 'l’eau du scan capte les touchers');
    // Disposition : caméra, « Page 1 », petit « Mode rafale », puis la grille 2×2.
    const R = id => el(id).getBoundingClientRect();
    const rafale = scanner.querySelector('.interrupteur-rafale').getBoundingClientRect();
    attendre(R('scanner-camera').bottom <= R('scanner-compteur').top && R('scanner-compteur').bottom <= rafale.top && rafale.bottom <= R('scanner-capturer').top, 'ordre caméra, Page 1, rafale, grille');
    const fichier = scanner.querySelector('.bouton-fichier');
    const B = [R('scanner-capturer'), fichier.getBoundingClientRect(), R('scanner-google'), R('scanner-fermer')];
    const proche = (x, y) => Math.abs(x - y) <= 2;
    attendre(proche(B[0].top, B[1].top) && proche(B[2].top, B[3].top) && B[2].top >= B[0].bottom && proche(B[0].left, B[2].left) && proche(B[1].left, B[3].left) && B[0].right <= B[1].left, 'pas une grille 2×2');
    attendre(proche(B[0].left, 412 - B[1].right), 'grille pas centrée');
    attendre(rafale.height < B[0].height && rafale.width < 412 * 0.7 && proche(rafale.left + rafale.width / 2, 206), '« Mode rafale » pas plus petit ou pas centré');
    for (const [nom, e] of [['scanner-capturer', el('scanner-capturer')], ['bouton-fichier', fichier], ['scanner-google', el('scanner-google')], ['scanner-fermer', el('scanner-fermer')], ['rafale', scanner.querySelector('.interrupteur-rafale')]]) {
      const r = e.getBoundingClientRect();
      attendre(r.bottom <= 900 && r.height >= 48, `${nom} hors écran ou trop petit`);
      attendre(touchable(ui, e), `${nom} pas touchable`);
    }
    // Lisibilité, dans le PIRE cas (eau la plus foncée derrière), en sombre puis en clair : au moins 7:1.
    const rgb = s => (s.match(/[0-9.]+/g) || []).map(Number);
    const lum = col => { const v = col.slice(0, 3).map(x => x / 255).map(x => (x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4)); return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]; };
    const contraste = (x, y) => { const [l1, l2] = [lum(x), lum(y)].sort((m, n) => n - m); return (l1 + 0.05) / (l2 + 0.05); };
    const melange = (dessus, alpha, dessous) => dessous.map((v, i) => v * (1 - alpha) + dessus[i] * alpha);
    function verifier(mode, couleursEau) {
      const fondEcran = rgb(fenetre.getComputedStyle(scanner).backgroundColor);
      const opacite = Number(fenetre.getComputedStyle(el('eau-scanner')).opacity);
      const pire = couleursEau.map(col => col.map(v => Math.max(0, v - 22)));
      for (const e of [el('scanner-capturer'), fichier.querySelector('span'), el('scanner-google'), el('scanner-fermer'), el('scanner-compteur'), scanner.querySelector('.interrupteur-rafale span')]) {
        for (const eauPire of pire) {
          let vu = melange(eauPire, opacite, fondEcran);
          const couches = [];
          for (let x = e; x && x !== scanner; x = x.parentElement) couches.push(rgb(fenetre.getComputedStyle(x).backgroundColor));
          for (const couche of couches.reverse()) if (couche.length >= 3) vu = melange(couche, couche.length === 4 ? couche[3] : 1, vu);
          const ratio = contraste(rgb(fenetre.getComputedStyle(e).color), vu);
          attendre(ratio >= 7, `${mode} : « ${e.textContent.trim().slice(0, 30)} » peu lisible (${ratio.toFixed(1)}:1)`);
        }
      }
    }
    verifier('sombre', accueilCap.EAU_SOMBRE);
    // Mode clair : vert d'eau, eau de Zencoder à 60 %.
    scanner.close();
    await pause();
    attendre(!eauScan.marche && fond.marche, 'eau du scan pas arrêtée, ou eau de l’accueil pas relancée');
    el('ouvrir-autre').click();
    el('bouton-theme-cap').click();
    attendreEgal(module.theme(), 'clair', 'pas en clair');
    scanner.showModal();
    await pause();
    attendreEgal(fenetre.getComputedStyle(scanner).backgroundColor, 'rgb(217, 228, 226)', 'fond clair du scan');
    attendreEgal([eauScan.couleurs.at(-1), eauScan.effets.at(-1)], [accueilCap.EAU_CLAIRE.map(x => [...x]), null], 'eau claire du scan');
    attendreEgal([fenetre.getComputedStyle(el('eau-scanner')).opacity, fenetre.getComputedStyle(el('eau-scanner')).filter], ['0.6', 'blur(1.2px)'], 'eau claire : 60 % et flou 1,2 px');
    verifier('clair', accueilCap.EAU_CLAIRE);
    // Toucher l'écran fait bouger l'eau du scan.
    const avantTouches = eauScan.touches;
    el('scanner-compteur').dispatchEvent(new fenetre.PointerEvent('pointerdown', { bubbles: true, clientX: 200, clientY: 300 }));
    attendre(eauScan.touches > avantTouches, 'l’eau du scan ne bouge pas au toucher');
    scanner.close();
  });

  // ----- 08/11/2026 : vagues sans remise à zéro et traînée continue (accord de Max) -----
  await testAsync('Vagues (08/11/2026) : traînée continue entre deux points du doigt ; l’état passe de l’eau seule à l’accueil au geste (et retour avec « Eau ») ; une pause ne vide plus l’eau', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const h = horlogeEau();
    const energie = e => { let s = 0; for (const v of e.buf1) s += Math.abs(v); for (const v of e.buf2) s += Math.abs(v); return s; };
    // 1. Une couche seule : un geste rapide laisse une traînée, pas deux points.
    const toile = ui.doc.createElement('canvas');
    toile.style.cssText = 'position:fixed;inset:0;width:412px;height:900px';
    ui.doc.body.appendChild(toile);
    const couche = ecranEau.creerCouche(toile, { raf: () => 1, caf: () => {} });
    couche.demarrer();
    const avant = couche.touchers();
    couche.tracer(0.1, 0.5, 0.9, 0.5, 1, ecranEau.EAU.rayon);
    attendre(couche.touchers() - avant >= 8, `traînée trop courte (${couche.touchers() - avant} touches)`);
    const etat = couche.exporterEtat();
    const milieu = Math.round(0.5 * etat.lignes) * etat.colonnes;
    let touches = 0;
    for (let x = Math.round(0.15 * etat.colonnes); x <= Math.round(0.85 * etat.colonnes); x++) if (etat.buf1[milieu + x] !== 0) touches++;
    attendre(touches >= Math.round(0.7 * etat.colonnes) - 1, `trous dans la traînée (${touches} carreaux)`);
    // Pause puis reprise : les vagues restent (plus de tableaux vidés).
    couche.arreter();
    couche.demarrer();
    attendreEgal(energie(couche.exporterEtat()), energie(etat), 'vagues vidées à la reprise');
    // Recopie : même taille = identique ; autre taille = vagues gardées quand même.
    const toile2 = ui.doc.createElement('canvas');
    toile2.style.cssText = 'position:fixed;inset:0;width:300px;height:500px';
    ui.doc.body.appendChild(toile2);
    const autre = ecranEau.creerCouche(toile2, { raf: () => 1, caf: () => {} });
    attendre(autre.importerEtat(etat) && energie(autre.exporterEtat()) > 0, 'vagues perdues entre deux tailles');
    toile.remove(); toile2.remove();
    // 2. L'écran d'eau complet : le geste vers le haut passe les vagues à l'eau de l'accueil, qui démarre.
    const memoire = new Map();
    const stockage = { getItem: k => memoire.get(k) ?? null, setItem: (k, v) => memoire.set(k, v) };
    const ecran = ecranEau.auDemarrage(ui.doc, { stockage, raf: h.raf, caf: h.caf, reglages: { fond: 'aucun', dureeSortieMs: 0 } });
    attendre(ecran.etat().visible && !ecran.fond.etat().active, 'eau seule absente ou accueil déjà en marche');
    const fenetre = ui.cadre.contentWindow;
    const surface = ui.parId('surface-eau');
    const toucher = (type, x, y) => surface.dispatchEvent(new fenetre.PointerEvent(type, { bubbles: true, pointerId: 7, clientX: x, clientY: y, buttons: type === 'pointerup' ? 0 : 1 }));
    toucher('pointerdown', 60, 300);
    toucher('pointermove', 350, 320);
    toucher('pointerup', 350, 320);
    ecran.entrerDansCap();
    attendre(!ecran.etat().visible && ecran.fond.etat().active, 'accueil pas en marche après le geste');
    const recue = ecran.fond.exporterEtat();
    attendre(recue && energie(recue) > 1, 'l’eau de l’accueil repart de zéro (remise à zéro)');
    // 3. Toucher ailleurs sur l'accueil : traînée continue aussi.
    const tAvant = ecran.fond.etat().touchers;
    const cible = ui.doc.body;
    cible.dispatchEvent(new fenetre.PointerEvent('pointerdown', { bubbles: true, pointerId: 8, clientX: 40, clientY: 600, buttons: 1 }));
    cible.dispatchEvent(new fenetre.PointerEvent('pointermove', { bubbles: true, pointerId: 8, clientX: 380, clientY: 600, buttons: 1 }));
    cible.dispatchEvent(new fenetre.PointerEvent('pointerup', { bubbles: true, pointerId: 8, clientX: 380, clientY: 600 }));
    attendre(ecran.fond.etat().touchers - tAvant >= 4, `accueil : pas de traînée (${ecran.fond.etat().touchers - tAvant} touches)`);
    // 4. Retour à l'eau seule (bouton « Eau ») : elle reprend les vagues de l'accueil.
    const energieAccueil = energie(ecran.fond.exporterEtat());
    ecran.afficher();
    attendre(ecran.etat().visible && !ecran.fond.etat().active, 'eau seule pas rouverte');
    const vagues = ecran.etatVagues();
    const depuis = ecran.fond.exporterEtat();
    if (vagues.colonnes === depuis.colonnes && vagues.lignes === depuis.lignes) attendreEgal(energie(vagues), energieAccueil, 'eau seule : vagues de l’accueil pas reprises');
    else attendre(energie(vagues) > 0, 'eau seule : vagues de l’accueil pas reprises');
  });

  // ----- 08/11/2026 : descente douce vers l'eau seule (accord de Max) -----
  await testAsync('Descente douce (08/11/2026) : retour à l’eau seule = date et boutons qui s’enfoncent, flous, en fondu, eau seule qui revient en fondu ; eau de l’accueil arrêtée à la fin ; geste vers le haut pendant la descente = arrêt propre ; animations réduites = d’un coup', async c => {
    const options = reduit => ({ stockage: { getItem: () => 'oui', setItem: () => {} }, animationsReduites: reduit, reglages: { fond: 'aucun', dureeSortieMs: 150 } });
    let ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    let h = horlogeEau();
    const ecran = ecranEau.auDemarrage(ui.doc, { ...options(false), raf: h.raf, caf: h.caf });
    const html = ui.doc.documentElement;
    const fenetre = ui.cadre.contentWindow;
    attendre(!ecran.etat().visible && ecran.fond.etat().active, 'accueil pas affiché au départ');
    // 1. Retour (même chemin que le geste de haut en bas) : descente, l'eau de l'accueil tourne encore.
    ui.parId('aller-eau').click();
    attendre(ecran.etat().visible && ecran.etat().descente && ecran.etat().animation, 'descente pas commencée');
    attendre(ui.parId('ecran-eau').classList.contains('eau-revient') && html.classList.contains('cap-descend'), 'classes de la descente absentes');
    attendreEgal(fenetre.getComputedStyle(ui.doc.querySelector('.ecran')).animationName, 'cap-descend-dans-le-sable', 'les boutons ne s’enfoncent pas');
    attendreEgal(fenetre.getComputedStyle(ui.parId('ecran-eau')).animationName, 'eau-revient', 'l’eau seule ne revient pas en fondu');
    attendre(ecran.fond.etat().active, 'eau de l’accueil arrêtée dès le début (figée sous le fondu)');
    attendre(fenetre.getComputedStyle(ui.parId('ecran-eau')).pointerEvents !== 'none', 'eau seule pas touchable pendant la descente');
    const regle = [...ui.doc.styleSheets].flatMap(s => { try { return [...s.cssRules]; } catch (e) { return []; } })
      .find(r => r.name === 'cap-descend-dans-le-sable');
    attendre(regle && /blur\(6px\)/.test(regle.cssText) && /translateY\(14vh\)/.test(regle.cssText) && /opacity: 0/.test(regle.cssText), 'descente : flou, enfoncement ou fondu absent');
    await attendreQue(() => !ecran.etat().descente, 'descente pas finie');
    attendre(ecran.etat().visible && !ecran.fond.etat().active && !html.classList.contains('cap-descend') && !ui.parId('ecran-eau').classList.contains('eau-revient'), 'fin de descente incorrecte');
    // 2. Montée, puis nouvelle descente interrompue par le geste vers le haut : arrêt propre, Cap remonte.
    ecran.entrerDansCap();
    await attendreQue(() => !ecran.etat().visible, 'montée pas finie');
    ui.parId('aller-eau').click();
    attendre(ecran.etat().descente, 'seconde descente pas commencée');
    ecran.entrerDansCap();
    attendre(!ecran.etat().descente && !html.classList.contains('cap-descend') && html.classList.contains('cap-monte') && ecran.fond.etat().active, 'descente pas arrêtée proprement');
    await attendreQue(() => !ecran.etat().visible, 'remontée pas finie');
    await new Promise(ok => setTimeout(ok, 300));
    attendre(ecran.fond.etat().active && !ecran.etat().visible, 'la descente annulée a arrêté l’eau de l’accueil');
    // 3. Animations réduites : d'un coup, comme avant.
    ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    h = horlogeEau();
    const ecranReduit = ecranEau.auDemarrage(ui.doc, { ...options(true), raf: h.raf, caf: h.caf });
    ui.parId('aller-eau').click();
    attendre(ecranReduit.etat().visible && !ecranReduit.etat().descente && !ecranReduit.fond.etat().active && !ui.doc.documentElement.classList.contains('cap-descend'), 'animations réduites : pas d’un coup');
  });

  // ----- 08/11/2026 : icône « Lecteur » dans Autre (demande de Max) -----
  await testAsync('Lecteur (08/11/2026, FAUX Drive) : l’icône de Autre ouvre la musique du compte Cap (dossiers, morceau, lecteur) ; identifiant absent, pas connecté, expiré, aucun MP3 = message clair, jamais vide ; Fermer ramène à Autre', async c => {
    const el0 = ui => id => ui.parId(id);
    const brancher = (ui, m, z) => {
      brancherAccueil(c, ui);
      relationsMp30().brancher(ui.doc, { compte: m, arbre: () => relationsCompte0().lireArbre(m), sorte: relationsCompte0().sorte, stockage: c.localStorage,
        lecteur: async () => z.objet, urls: fausseAdresses() });
    };
    // 1. Aucun identifiant : message, pas de bouton Google, pas de lecture du Drive.
    let ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    let el = el0(ui);
    let m = compteRelationsIsole(c);
    brancher(ui, m, fauxLecteurZencoder());
    el('ouvrir-autre').click();
    const svg = el('ouvrir-lecteur').querySelector('svg');
    attendre(svg && el('ouvrir-lecteur').textContent.trim() === 'Lecteur', 'icône du Lecteur absente ou sans nom');
    const avantRequetes = c.requetes.length;
    el('ouvrir-lecteur').click();
    await pause();
    attendre(el('musique-relations').open && /Identifiant du compte Cap absent/.test(el('etat-musique-relations').textContent) && el('autoriser-musique-relations').hidden, `sans identifiant : ${el('etat-musique-relations').textContent}`);
    attendreEgal(c.requetes.length, avantRequetes, 'Drive lu sans identifiant');
    attendre(el('ouvrir-lecteur').querySelector('svg'), 'dessin de l’icône effacé');
    el('fermer-musique-relations').click();
    // 08/11/2026 : « Fermer » attend la fin du fondu (choix_sur_eau.js) avant de fermer.
    await attendreQue(() => !el('musique-relations').open && !el('ecran-autre').hidden, 'Fermer ne ramène pas à Autre');
    // 2. Identifiant, pas connecté : message + « Autoriser la lecture du compte Cap » (même texte, même droit).
    m.enregistrerAdresse(COMPTE_CAP_FICTIF);
    el('ouvrir-lecteur').click();
    await pause();
    attendre(/pas connecté/.test(el('etat-musique-relations').textContent) && !el('autoriser-musique-relations').hidden, `sans connexion : ${el('etat-musique-relations').textContent}`);
    attendreEgal(el('autoriser-musique-relations').textContent, 'Autoriser la lecture du compte Cap', 'texte du bouton Google');
    attendre(touchable(ui, el('autoriser-musique-relations')), 'bouton « Autoriser » caché');
    const avant = c.redirections.length;
    el('autoriser-musique-relations').click();
    attendreEgal(c.redirections.length, avant + 1, 'page de Google pas ouverte');
    attendreEgal(c.redirections.at(-1).searchParams.get('scope'), REGLAGES_GOOGLE.autorisations_relations.join(' '), 'droits demandés changés');
    // 3. Connecté, aucun « Relations » : message clair.
    fauxDriveCompteCap(c);
    ({ m } = connecterCompteFictif(c));
    ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    el = el0(ui);
    brancher(ui, m, fauxLecteurZencoder());
    el('ouvrir-autre').click();
    el('ouvrir-lecteur').click();
    await attendreQue(() => /Aucun dossier « Relations »/.test(el('etat-musique-relations').textContent), `Drive vide : ${el('etat-musique-relations').textContent}`);
    attendre(el('autoriser-musique-relations').hidden, 'bouton « Autoriser » alors que connecté');
    el('fermer-musique-relations').click();
    // 4. Connecté avec de la musique : dossiers, morceau, lecteur ; « Arrêter et fermer » puis « Fermer » = Autre.
    const f = fauxDriveCompteCap(c);
    remplirMusiqueFictive(f);
    const z = fauxLecteurZencoder();
    ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    el = el0(ui);
    brancher(ui, m, z);
    el('ouvrir-autre').click();
    el('ouvrir-lecteur').click();
    await attendreQue(() => el('liste-musique-relations').querySelectorAll('button.choix-grand-affichage').length === 2, `dossiers : ${el('etat-musique-relations').textContent}`);
    el('liste-musique-relations').querySelector('button').click();
    el('liste-musique-relations').querySelector('button.ligne-morceau').click();
    await attendreQue(() => z.appels.length === 1, `lecteur : ${el('etat-lecteur-mp3').textContent}`);
    attendre(el('lecteur-mp3-relations').open, 'lecteur pas ouvert');
    attendre(c.requetes.every(q => q.methode === 'GET'), 'autre chose qu’une lecture');
    el('fermer-lecteur-mp3').click();
    attendre(!el('lecteur-mp3-relations').open && el('musique-relations').open, 'Arrêter et fermer : pas de retour à la liste');
    el('fermer-musique-relations').click();
    // 08/11/2026 : « Fermer » attend la fin du fondu (choix_sur_eau.js) avant de fermer.
    await attendreQue(() => !el('musique-relations').open && !el('ecran-autre').hidden, 'Fermer ne ramène pas à Autre');
    // 5. Connexion expirée : message et bouton, jamais une fenêtre vide.
    c.maintenant += 3600 * 1000;
    el('ouvrir-lecteur').click();
    await pause();
    attendre(el('musique-relations').open && /expiré|pas connecté/.test(el('etat-musique-relations').textContent) && !el('autoriser-musique-relations').hidden, `expiration : ${el('etat-musique-relations').textContent}`);
    el('fermer-musique-relations').click();
    attendre(el('autoriser-musique-relations').hidden, 'bouton gardé après fermeture');
  });

  // ----- 08/11/2026 : retour direct dans la musique après la page de Google (accord de Max) -----
  await testAsync('Lecteur, retour direct (08/11/2026, FAUX Drive) : « Autoriser » touché dans la musique = au retour de Google, Autre puis la musique s’ouvrent seules (dossiers lus), marque effacée ; marque trop vieille ou absente = « Réglages du Drive » comme avant', async c => {
    attendreEgal(relationsMp30().CLE_RETOUR_MUSIQUE, visionneuseCap.CLE_RETOUR_MUSIQUE, 'marques différentes');
    attendre(visionneuseCap.CLE_RETOUR_MUSIQUE !== visionneuseCap.CLE_RETOUR, 'même marque que la visionneuse');
    const f = fauxDriveCompteCap(c);
    remplirMusiqueFictive(f);
    const toutBrancher = (ui, m, z) => {
      brancherAccueil(c, ui);
      relationsMp30().brancher(ui.doc, { compte: m, arbre: () => relationsCompte0().lireArbre(m), sorte: relationsCompte0().sorte, stockage: c.localStorage,
        lecteur: async () => z.objet, urls: fausseAdresses(), maintenant: () => c.maintenant });
      relationsCompte0().brancher(ui.doc, { compte: m, pdfjs: async () => { throw new Error('ancien lecteur'); }, visionneuse: () => null, stockage: c.localStorage, maintenant: () => c.maintenant });
    };
    // 1. Pas connecté : « Autoriser » dans la musique note la demande de retour, puis la page de Google.
    let m = compteRelationsIsole(c);
    let ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    let el = id => ui.parId(id);
    m.enregistrerAdresse(COMPTE_CAP_FICTIF);
    toutBrancher(ui, m, fauxLecteurZencoder());
    el('ouvrir-autre').click();
    el('ouvrir-lecteur').click();
    await pause();
    attendre(/tu reviendras ici/.test(el('etat-musique-relations').textContent) && !el('autoriser-musique-relations').hidden, `sans connexion : ${el('etat-musique-relations').textContent}`);
    el('autoriser-musique-relations').click();
    const url = c.redirections.at(-1);
    attendreEgal(url.searchParams.get('scope'), REGLAGES_GOOGLE.autorisations_relations.join(' '), 'droits demandés changés');
    attendreEgal(c.localStorage.getItem(visionneuseCap.CLE_RETOUR_MUSIQUE), String(c.maintenant), 'demande de retour pas notée');
    attendreEgal(c.localStorage.getItem(visionneuseCap.CLE_RETOUR), null, 'marque de la visionneuse posée à tort');
    // 2. Retour de Google (page rechargée) : Autre, puis la musique, toutes seules ; marque effacée.
    c.location.hash = `#access_token=jeton-compte-cap-fictif&expires_in=3600&token_type=Bearer&state=${url.searchParams.get('state')}`;
    m = compteRelationsIsole(c);
    ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    el = id => ui.parId(id);
    toutBrancher(ui, m, fauxLecteurZencoder());
    attendre(el('musique-relations').open && !el('ecran-autre').hidden, 'musique ou Autre pas rouverts au retour');
    await attendreQue(() => el('liste-musique-relations').querySelectorAll('button.choix-grand-affichage').length === 2, `dossiers pas lus au retour : ${el('etat-musique-relations').textContent}`);
    attendre(!el('reglages-drive').open && el('autoriser-musique-relations').hidden, 'Réglages du Drive ouvert, ou bouton « Autoriser » alors que connecté');
    attendreEgal(c.localStorage.getItem(visionneuseCap.CLE_RETOUR_MUSIQUE), null, 'marque gardée');
    attendre(c.requetes.every(q => q.methode === 'GET'), 'autre chose qu’une lecture');
    el('fermer-musique-relations').click();
    // 08/11/2026 : « Fermer » attend la fin du fondu (choix_sur_eau.js) avant de fermer.
    await attendreQue(() => !el('musique-relations').open && !el('ecran-autre').hidden, 'Fermer ne ramène pas à Autre');
    // 3. Marque trop vieille (plus de 10 min) : retour habituel, « Réglages du Drive ».
    m.seConnecter();
    c.localStorage.setItem(visionneuseCap.CLE_RETOUR_MUSIQUE, String(c.maintenant - visionneuseCap.DUREE_RETOUR_MS - 1));
    c.location.hash = `#access_token=jeton-compte-cap-fictif&expires_in=3600&token_type=Bearer&state=${c.redirections.at(-1).searchParams.get('state')}`;
    m = compteRelationsIsole(c);
    ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    el = id => ui.parId(id);
    toutBrancher(ui, m, fauxLecteurZencoder());
    await pause();
    attendre(el('reglages-drive').open && !el('musique-relations').open, 'retour habituel cassé');
    attendreEgal(c.localStorage.getItem(visionneuseCap.CLE_RETOUR_MUSIQUE), null, 'vieille marque gardée');
  });

  // ----- 08/11/2026 : écran de choix sur l'eau (règle générale de Max), appliqué au choix des dossiers de musique -----
  await testAsync('Choix sur l’eau (08/11/2026, FAUX Drive) : dossiers de musique = gros boutons sur l’eau, sans titre, sans texte d’aide, sans fenêtre ; « Fermer » identique aux boutons ; l’écran d’avant disparaît puis les boutons sortent du sable ; fermeture inverse ; lisible en sombre et en clair ; animations réduites = d’un coup', async c => {
    const f = fauxDriveCompteCap(c);
    remplirMusiqueFictive(f);
    const { m } = connecterCompteFictif(c);
    const ouvrirTout = () => {
      const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
      brancherAccueil(c, ui);
      relationsMp30().brancher(ui.doc, { compte: m, arbre: () => relationsCompte0().lireArbre(m), sorte: relationsCompte0().sorte, stockage: c.localStorage,
        lecteur: async () => fauxLecteurZencoder().objet, urls: fausseAdresses() });
      return ui;
    };
    let ui = ouvrirTout();
    let el = id => ui.parId(id);
    const vue = () => ui.cadre.contentWindow;
    const html = () => ui.doc.documentElement;
    const fenetre = () => el('musique-relations');
    el('ouvrir-autre').click();
    // Une fenêtre déjà ouverte dessous (comme « Réglages du Drive ») disparaît aussi.
    el('reglages-drive').showModal();
    el('ouvrir-lecteur').click();
    attendre(fenetre().open && fenetre().classList.contains('fenetre-choix'), 'fenêtre de choix pas ouverte');
    await attendreQue(() => el('liste-musique-relations').querySelectorAll('button.choix-grand-affichage').length === 2, `dossiers : ${el('etat-musique-relations').textContent}`);
    // Rien d'autre que les boutons : pas de titre, pas de texte d'aide, pas de cadre ni de fond.
    attendre(!fenetre().querySelector('h2') && !/Musique de/.test(fenetre().innerText), 'titre encore là');
    attendreEgal(el('etat-musique-relations').textContent, '', 'texte d’aide encore là');
    attendreEgal(vue().getComputedStyle(el('etat-musique-relations')).display, 'none', 'place du texte d’aide gardée');
    const sf = vue().getComputedStyle(fenetre());
    attendreEgal([sf.backgroundColor, sf.borderTopWidth, sf.boxShadow, vue().getComputedStyle(fenetre(), '::backdrop').backgroundColor], ['rgba(0, 0, 0, 0)', '0px', 'none', 'rgba(0, 0, 0, 0)'], 'fenêtre, cadre ou voile encore là');
    const boite = fenetre().getBoundingClientRect();
    attendreEgal([boite.left, boite.top, boite.width, boite.height], [0, 0, 412, 900], 'pas posé sur toute l’eau');
    // « Fermer » : exactement l'allure des boutons de dossiers.
    const dossier = el('liste-musique-relations').querySelector('button.choix-grand-affichage');
    const allure = b => { const s = vue().getComputedStyle(b); const r = b.getBoundingClientRect();
      return [r.left, r.width, s.fontFamily, s.fontSize, s.fontWeight, s.color, s.backgroundColor, s.borderTopWidth, s.borderTopStyle, s.borderTopColor, s.borderRadius, s.boxShadow, s.paddingTop, s.textAlign, s.lineHeight]; };
    attendreEgal(allure(el('fermer-musique-relations')), allure(dossier), '« Fermer » différent des boutons de dossiers');
    attendre(touchable(ui, el('fermer-musique-relations')) && touchable(ui, dossier), 'boutons pas touchables');
    // Transition d'entrée : l'écran d'avant (accueil, Autre, fenêtre dessous) disparaît, puis les boutons sortent du sable.
    attendre(html().classList.contains('choix-ouvert') && el('reglages-drive').classList.contains('cache-sous-choix'), 'écran d’avant pas caché');
    attendreEgal(vue().getComputedStyle(ui.doc.querySelector('.ecran')).transitionDuration, '0.45s', 'pas de fondu de l’écran d’avant');
    const sEnfant = vue().getComputedStyle(el('liste-musique-relations'));
    attendreEgal([sEnfant.animationName, sEnfant.animationDelay, sEnfant.animationDuration], ['cap-monte-du-sable', '0.45s', '1s'], 'les boutons ne sortent pas du sable après la disparition');
    // Lisible sur l'eau, en sombre puis en clair (au moins 7:1 sur le fond de l'eau).
    const rgb = s => (s.match(/[0-9.]+/g) || []).map(Number);
    const lum = col => { const v = col.slice(0, 3).map(x => x / 255).map(x => (x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4)); return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]; };
    const contraste = (x, y) => { const [l1, l2] = [lum(x), lum(y)].sort((u, w) => w - u); return (l1 + 0.05) / (l2 + 0.05); };
    const lisible = mode => {
      const r = contraste(rgb(vue().getComputedStyle(dossier).color), rgb(vue().getComputedStyle(ui.doc.body).backgroundColor));
      attendre(r >= 7, `${mode} : boutons peu lisibles (${r.toFixed(1)}:1)`);
    };
    lisible('sombre');
    html().classList.remove('theme-cap-sombre');
    html().classList.add('theme-cap-clair');
    lisible('clair');
    html().classList.remove('theme-cap-clair');
    html().classList.add('theme-cap-sombre');
    // Fermeture : les boutons disparaissent d'abord (fenêtre encore là), puis l'écran d'avant remonte du sable.
    el('fermer-musique-relations').click();
    attendre(fenetre().open && fenetre().classList.contains('choix-sortie'), 'pas de disparition des boutons avant la fermeture');
    await attendreQue(() => !fenetre().open, 'fenêtre pas fermée');
    await attendreQue(() => html().classList.contains('choix-retour') || !html().classList.contains('choix-ouvert'), 'écran d’avant pas revenu');
    attendre(!html().classList.contains('choix-ouvert') && !el('reglages-drive').classList.contains('cache-sous-choix') && el('reglages-drive').open, 'fenêtre de dessous perdue');
    attendreEgal(vue().getComputedStyle(ui.doc.querySelector('.ecran')).animationName, 'cap-monte-du-sable', 'l’écran d’avant ne remonte pas du sable');
    await attendreQue(() => !html().classList.contains('choix-retour'), 'retour jamais fini');
    el('reglages-drive').close();
    // Animations réduites : ouverture et fermeture d'un coup, sans classe d'animation.
    ui = ouvrirTout();
    el = id => ui.parId(id);
    ui.cadre.contentWindow.matchMedia = q => ({ matches: /reduce/.test(q), addEventListener() {}, removeEventListener() {} });
    el('ouvrir-autre').click();
    el('ouvrir-lecteur').click();
    attendre(fenetre().open && !fenetre().classList.contains('choix-entree'), 'animations réduites : animation d’entrée');
    await attendreQue(() => el('liste-musique-relations').querySelectorAll('button.choix-grand-affichage').length === 2, 'dossiers (animations réduites)');
    el('fermer-musique-relations').click();
    attendre(!fenetre().open, 'animations réduites : fermeture pas immédiate');
    await pause();
    attendre(!html().classList.contains('choix-retour') && !html().classList.contains('choix-ouvert'), 'animations réduites : classes restées');
  });

  // ----- 08/11/2026 : liste des morceaux à la règle, eau jouable, geste et arrière-plan du lecteur (décisions de Max) -----
  await testAsync('Musique (08/11/2026, FAUX Drive) : liste des morceaux = gros boutons identiques sans titre ; dossiers ↔ morceaux en fondu puis sable ; eau jouable derrière ; geste de haut en bas (bord droit) = fondu du son, lecteur en vapeur, liste qui ressort ; « Musique en arrière-plan » = la musique continue, indicateur qui ramène au lecteur', async c => {
    const f = fauxDriveCompteCap(c);
    remplirMusiqueFictive(f);
    const { m } = connecterCompteFictif(c);
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const el = id => ui.parId(id);
    const vue = ui.cadre.contentWindow;
    brancherAccueil(c, ui);
    const z = fauxLecteurZencoder();
    z.objet.audio.volume = 0.8;
    relationsMp30().brancher(ui.doc, { compte: m, arbre: () => relationsCompte0().lireArbre(m), sorte: relationsCompte0().sorte, stockage: c.localStorage,
      lecteur: async () => z.objet, urls: fausseAdresses() });
    // Eau de l'accueil réelle (aiguillage des touchers seulement).
    const eau = ecranEau.eauAccueil(ui.doc, { raf: () => 1, caf: () => {} });
    eau.demarrer();
    const fenetre = el('musique-relations');
    el('ouvrir-autre').click();
    el('ouvrir-lecteur').click();
    await attendreQue(() => el('liste-musique-relations').querySelectorAll('button.choix-grand-affichage').length === 2, 'dossiers');
    // 1. Eau jouable derrière l'écran de choix (et toujours ignorée dans une fenêtre ordinaire).
    const toucher = cible => cible.dispatchEvent(new vue.PointerEvent('pointerdown', { bubbles: true, pointerId: 3, clientX: 200, clientY: 400, buttons: 1 }));
    let avant = eau.etat().touchers;
    toucher(el('liste-musique-relations').querySelector('button'));
    attendre(eau.etat().touchers > avant, 'l’eau ne bouge pas derrière l’écran de choix');
    // 2. Dossier → morceaux : fantôme de l'ancien écran (inerte, sans identifiants) qui disparaît, puis le sable.
    el('liste-musique-relations').querySelector('button').click();
    const fantome = fenetre.querySelector('.choix-fantome');
    attendre(fantome && fantome.inert && fantome.getAttribute('aria-hidden') === 'true' && !fantome.querySelector('[id]') && /FICTIF/.test(fantome.textContent), 'pas de fantôme de l’écran des dossiers');
    attendre(fenetre.classList.contains('choix-entree'), 'les morceaux ne sortent pas du sable');
    attendreEgal(vue.getComputedStyle(el('liste-musique-relations')).animationName, 'cap-monte-du-sable', 'animation des morceaux');
    await attendreQue(() => !fenetre.querySelector('.choix-fantome'), 'fantôme jamais retiré');
    // 3. Liste à la règle : pas de titre ni de texte d'aide ; chaque morceau = gros bouton identique à « Fermer ».
    const lignes = [...el('liste-musique-relations').querySelectorAll('button.ligne-morceau')];
    attendreEgal(lignes.length, 10, 'morceaux');
    attendre([...fenetre.querySelectorAll('.titre-liste-morceaux')].every(h => vue.getComputedStyle(h).display === 'none'), 'titres encore visibles');
    attendreEgal(el('etat-musique-relations').textContent, '', 'texte d’aide');
    const allure = b => { const s = vue.getComputedStyle(b); const r = b.getBoundingClientRect();
      return [r.left, r.width, s.fontFamily, s.fontSize, s.fontWeight, s.color, s.backgroundColor, s.borderTopWidth, s.borderTopStyle, s.borderTopColor, s.borderRadius, s.paddingTop]; };
    attendreEgal(allure(lignes[0]), allure(el('fermer-musique-relations')), 'morceau différent de « Fermer »');
    attendreEgal(allure(el('retour-musique-relations')), allure(el('fermer-musique-relations')), '« Retour aux dossiers » différent de « Fermer »');
    attendre(parseFloat(vue.getComputedStyle(lignes[0].querySelector('.numero-morceau')).fontSize) > parseFloat(vue.getComputedStyle(lignes[0]).fontSize), 'numéro pas plus gros');
    // 4. Le lecteur : bande du geste au bord droit, hors des curseurs de Zencoder (qui s'arrêtent à 90 % de la largeur).
    lignes[1].click();
    await attendreQue(() => z.appels.length === 1, 'morceau pas lancé');
    // 08/11/2026, 11h45 : plus de grand bouton ; la note ronde est là, discrète (45 %), touchable.
    attendre(el('fermer-lecteur-mp3').hidden && el('arriere-plan-lecteur').hidden, 'grand bouton encore affiché');
    attendre(!el('indicateur-musique').hidden && el('indicateur-musique').classList.contains('indicateur-discret') && touchable(ui, el('indicateur-musique')), 'note ronde absente ou pas touchable sur le lecteur');
    attendreEgal(vue.getComputedStyle(el('indicateur-musique')).opacity, '0.45', 'transparence de la note');
    const bande = el('geste-fermer-lecteur').getBoundingClientRect();
    attendre(bande.right >= 411 && bande.width <= 40 && bande.left >= 0.9 * 412 - 1 && bande.top >= 0.1 * 900 && bande.bottom <= 900 - 140 && bande.top >= el('indicateur-musique').getBoundingClientRect().bottom + 8, `bande du geste mal placée : ${JSON.stringify(bande)}`);
    // Un petit geste ou un geste de côté ne ferme rien.
    const glisser = (dx, dy) => {
      const g = el('geste-fermer-lecteur');
      g.dispatchEvent(new vue.PointerEvent('pointerdown', { bubbles: true, pointerId: 9, clientX: 395, clientY: 250 }));
      g.dispatchEvent(new vue.PointerEvent('pointerup', { bubbles: true, pointerId: 9, clientX: 395 + dx, clientY: 250 + dy }));
    };
    glisser(0, 80);
    glisser(-200, 260);
    attendre(el('lecteur-mp3-relations').open && !el('lecteur-mp3-relations').classList.contains('lecteur-vapeur'), 'fermé par un faux geste');
    // Geste net de haut en bas : fondu du son, vapeur, puis la liste ressort ; musique arrêtée.
    glisser(0, 300);
    attendre(el('lecteur-mp3-relations').classList.contains('lecteur-vapeur') && fenetre.classList.contains('choix-entree'), 'pas de vapeur ou liste qui ne ressort pas');
    await attendreQue(() => z.objet.audio.volume < 0.8, 'pas de fondu du son');
    attendre(!z.appels.some(x => x[0] === 'arreter'), 'son coupé net avant le fondu');
    await attendreQue(() => !el('lecteur-mp3-relations').open, 'lecteur pas fermé par le geste');
    attendre(z.appels.some(x => x[0] === 'arreter') && el('indicateur-musique').hidden && fenetre.open, 'musique pas arrêtée, indicateur affiché, ou liste perdue');
    // 5. « Musique en arrière-plan » : la musique continue, l'indicateur ramène au lecteur.
    z.objet.audio.volume = 0.8;
    const n = z.appels.length;
    el('liste-musique-relations').querySelectorAll('button.ligne-morceau')[0].click(); // suivant : « Trois » (jouable)
    await attendreQue(() => z.appels.length === n + 1, 'morceau pas relancé');
    const arrets = z.appels.filter(x => x[0] === 'arreter').length;
    el('indicateur-musique').click(); // 08/11/2026, 11h45 : la note passe la musique en arrière-plan
    attendre(!el('indicateur-musique').classList.contains('indicateur-discret') && !el('lecteur-mp3-relations').contains(el('indicateur-musique')), 'note pas pleinement visible tout de suite');
    await attendreQue(() => !el('lecteur-mp3-relations').open, 'lecteur pas fermé (arrière-plan)');
    attendreEgal(z.appels.filter(x => x[0] === 'arreter').length, arrets, 'musique arrêtée en arrière-plan');
    attendreEgal(z.objet.audio.volume, 0.8, 'volume baissé en arrière-plan');
    attendre(!el('indicateur-musique').hidden && fenetre.contains(el('indicateur-musique')) && touchable(ui, el('indicateur-musique')), 'indicateur absent ou pas touchable sur la liste');
    // Fin du morceau en arrière-plan : le suivant joue, sans ramener le lecteur.
    z.objet.audio.dispatchEvent(new Event('ended'));
    await attendreQue(() => z.appels.length === n + 2, 'morceau suivant pas joué en arrière-plan');
    attendre(!el('lecteur-mp3-relations').open, 'lecteur revenu tout seul');
    // La liste fermée : l'indicateur reste, sur Autre.
    el('fermer-musique-relations').click();
    await attendreQue(() => !fenetre.open, 'liste pas fermée');
    await pause();
    attendre(!el('indicateur-musique').hidden && !fenetre.contains(el('indicateur-musique')) && touchable(ui, el('indicateur-musique')), 'indicateur perdu sur Autre');
    // Toucher l'indicateur : le lecteur revient ; la note y reste, discrète (08/11/2026, 11h45).
    el('indicateur-musique').click();
    attendre(el('lecteur-mp3-relations').open && !el('indicateur-musique').hidden && el('indicateur-musique').classList.contains('indicateur-discret') && el('lecteur-mp3-relations').contains(el('indicateur-musique')), 'l’indicateur ne ramène pas au lecteur, ou note pas discrète');
    glisser(0, 300);
    await attendreQue(() => !el('lecteur-mp3-relations').open, 'lecteur pas fermé');
    attendre(el('indicateur-musique').hidden, 'indicateur après l’arrêt');
    eau.arreter();
  });

  // ----- 08/11/2026 : retouches d'affichage du lecteur de Zencoder (décisions de Max), dans la VRAIE page du lecteur -----
  await testAsync('Lecteur (08/11/2026, vraie page de Zencoder) : étiquette « FICTIF — essai lecteur » cachée ; lecture et pause dessinées, centrées, sans émoji ni focus qui reste ; « Choisir » au lieu de « Choisir un MP3 » (même bouton) ; fichier de Zencoder inchangé', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const cadre = ui.doc.createElement('iframe');
    cadre.style.cssText = 'position:fixed;inset:0;width:412px;height:900px;border:0';
    ui.doc.body.appendChild(cadre);
    const z = await relationsMp30().chargeurLecteur(cadre)();
    attendre(z && typeof z.jouerFichier === 'function', 'lecteur pas chargé');
    const d = cadre.contentDocument;
    const vue = cadre.contentWindow;
    const s = (sel, prop) => vue.getComputedStyle(d.querySelector(sel))[prop];
    // 1. L'étiquette : cachée (affichage seulement), son texte est toujours dans la page.
    attendreEgal(s('#lecteur .etiquette-fictif', 'display'), 'none', 'étiquette encore affichée');
    attendre(/FICTIF/.test(d.querySelector('.etiquette-fictif').textContent), 'texte de Zencoder effacé');
    // 4. « Choisir » : même bouton, même place, même fonction (ouvre le choix de fichier), texte d'origine gardé.
    const choisir = d.getElementById('bouton-choisir');
    attendreEgal([choisir.textContent, choisir.dataset.texteZencoder], ['Choisir', 'Choisir un MP3'], 'texte du bouton');
    let ouvert = 0;
    d.getElementById('entree-fichier').click = () => { ouvert++; };
    choisir.click();
    attendreEgal(ouvert, 1, '« Choisir » n’ouvre plus le choix de fichier');
    // 2. et 3. Lecture et pause : caractères cachés, dessins centrés (triangle décalé à droite), aucun état qui reste.
    const lecture = d.getElementById('bouton-lecture');
    attendreEgal(lecture.dataset.icone, 'lecture', 'dessin de lecture');
    attendreEgal(s('#bouton-lecture', 'color'), 'rgba(0, 0, 0, 0)', 'caractère ▶ encore visible');
    attendre(/M7\.5 5v14l11-7z/.test(decodeURIComponent(s('#bouton-lecture', 'backgroundImage'))), 'triangle pas décalé à droite');
    attendreEgal([s('#bouton-lecture', 'backgroundPosition'), s('#bouton-lecture', 'backgroundRepeat')], ['50% 50%', 'no-repeat'], 'dessin pas centré');
    attendre(s('#bouton-lecture', 'backgroundColor') !== 'rgba(0, 0, 0, 0)', 'rond du bouton perdu');
    lecture.textContent = '⏸'; // ce que fait le lecteur de Zencoder au toucher
    await pause();
    attendreEgal(lecture.dataset.icone, 'pause', 'dessin de pause');
    attendre(/M7 5h3\.5v14H7zM13\.5 5H17v14h-3\.5z/.test(decodeURIComponent(s('#bouton-lecture', 'backgroundImage'))), 'pause pas centrée');
    attendreEgal([d.getElementById('bouton-debut').dataset.icone, d.getElementById('bouton-fin').dataset.icone], ['debut', 'fin'], 'début et fin');
    for (const id of ['bouton-debut', 'bouton-lecture', 'bouton-fin', 'bouton-choisir']) {
      const b = d.getElementById(id);
      attendreEgal([vue.getComputedStyle(b).webkitTapHighlightColor, vue.getComputedStyle(b).outlineStyle], ['rgba(0, 0, 0, 0)', 'none'], `${id} : surbrillance`);
      b.focus();
      b.dispatchEvent(new vue.PointerEvent('pointerup', { bubbles: true }));
      await pause();
      attendre(d.activeElement !== b, `${id} : reste « actif » après le toucher`);
    }
    // Une seule fois, même si la page est retouchée deux fois.
    relationsMp30().retoucherLecteur(d);
    attendreEgal(d.querySelectorAll('#retouches-cap').length, 1, 'retouches en double');
    cadre.remove();
  });

  // ----- 08/11/2026 : plus d'étiquette de maquette « FICTIF » à l'écran (décision de Max) -----
  await testAsync('Étiquettes de maquette (08/11/2026) : « FICTIF — essai visualiseur » cachée dans la VRAIE visionneuse (texte gardé, fichier de Zencoder inchangé) ; aucune étiquette de maquette dans les écrans de Cap ni dans le lecteur', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const cadre = ui.doc.createElement('iframe');
    cadre.style.cssText = 'position:fixed;inset:0;width:412px;height:900px;border:0';
    ui.doc.body.appendChild(cadre);
    const v = await visionneuseCap0().chargeur(cadre)();
    attendre(v && typeof v.montrerFichier === 'function', 'visionneuse pas chargée');
    const d = cadre.contentDocument;
    const etiquette = d.querySelector('#visualiseur .etiquette-fictif');
    attendre(etiquette && /FICTIF/.test(etiquette.textContent), 'texte de Zencoder effacé');
    attendreEgal(cadre.contentWindow.getComputedStyle(etiquette).display, 'none', 'étiquette encore affichée dans la visionneuse');
    // Le reste de l'écran d'accueil de la visionneuse est toujours là (rien d'autre ne dépendait de l'étiquette).
    attendre(d.getElementById('bouton-choisir') && d.getElementById('titre-fichier') && cadre.contentWindow.getComputedStyle(d.getElementById('bouton-choisir')).display !== 'none', 'visionneuse abîmée');
    visionneuseCap0().retoucherVisionneuse(d);
    attendreEgal(d.querySelectorAll('#retouches-cap').length, 1, 'retouche en double');
    cadre.remove();
    // Écrans de Cap (texte écrit dans la page, hors commentaires et scripts) : aucune étiquette de maquette.
    const marcheur = ui.doc.createTreeWalker(ui.doc.body, NodeFilter.SHOW_TEXT);
    const trouves = [];
    for (let n = marcheur.nextNode(); n; n = marcheur.nextNode()) {
      if (n.parentElement && n.parentElement.closest('script, style')) continue;
      // Les DONNÉES fictives (tâches « FICTIF — … ») restent (règle de Max) : seules les étiquettes de maquette comptent.
      if (/FICTIF\s*[—-]\s*essai|essai (lecteur|visualiseur)|maquette/i.test(n.textContent)) trouves.push(n.textContent.trim().slice(0, 60));
    }
    // Exception signalée à Max, pas modifiée : « Intensité de l’eau (maquette, non reliée) » (Réglages) dit honnêtement que
    // ce curseur ne commande encore rien ; ce n'est pas une étiquette de Zencoder.
    attendreEgal(trouves.filter(x => !/^Intensité de l’eau \(maquette, non reliée\)$/.test(x)), [], 'étiquette de maquette dans les écrans de Cap');
  });

  // ----- 08/11/2026 : commandes vocales, étape 1 : lecture du tableur (FAUX tableur FICTIF uniquement) -----
  await testAsync('Commandes vocales (08/11/2026, FAUX tableur FICTIF) : copie réduite sur le téléphone, sans « RETIRER », sans les lignes de noms (Cible, Nom d’appel), sans les lignes sans code ; 4 champs ; lecture seule de la première feuille A:F ; résumé en nombres seulement', async () => {
    const titres = ['Ce que je veux', 'Commande', 'Bloc', 'Formulation', 'Code commande', 'Remarque (Claude, datée)'];
    const faux = [titres,
      ['Ouvrir l’écran Autre FICTIF', 'Ouvrir Autre', 'Mot-clé', 'autre fictif', 'NAV-02'],
      ['Ouvrir l’écran Autre FICTIF', 'Ouvrir Autre', 'Verbe d’ouverture', 'ouvre', 'nav-02'],
      ['Passer en mode sombre FICTIF', 'Mode sombre', 'Mot-clé', 'le noir fictif', 'NAV-10', 'RETIRER 08/11/2026 : trop vague (FICTIF)'],
      ['Appeler FICTIF', 'Appel téléphonique', "Nom d'appel", 'Prénom-Secret-FICTIF', 'TEL-01'], // apostrophe droite, comme dans le vrai tableur
      ['Appeler FICTIF', 'Appel téléphonique', 'Cible', 'Autre-Prénom-Secret-FICTIF', 'COMMUN'],
      ['Appeler FICTIF', 'Appel téléphonique', 'Verbe d’appel', 'appelle', 'TEL-01'],
      ['Donner la météo FICTIF', 'Météo', 'Mot-clé', 'la météo fictive', ''],
      ['', '', '', '', ''],
      ['Arrêter la dictée FICTIF', 'Dictée', 'Verbe d’arrêt', 'terminé', 'DIC-02', 'CONFLIT 08/11/2026 (FICTIF)']];
    const r = commandesVocales.analyser(faux);
    attendreEgal(r.compte, { lues: 8, gardees: 4, retirees: 1, noms_exclus: 2, sans_code: 1, codes: 3 }, 'compte');
    attendreEgal(r.lignes.map(l => [l.code, l.formulation]), [['NAV-02', 'autre fictif'], ['NAV-02', 'ouvre'], ['TEL-01', 'appelle'], ['DIC-02', 'terminé']], 'lignes gardées');
    // 4 champs ; plus « conflit » (vrai) seulement sur les lignes « CONFLIT » (étape 2, 08/11/2026).
    attendre(r.lignes.every(l => ['code,commande,bloc,formulation', 'code,commande,bloc,formulation,conflit'].includes(Object.keys(l).join())), 'autre chose que 4 champs');
    attendreEgal(r.lignes.filter(l => l.conflit).map(l => l.formulation), ['terminé'], 'ligne « CONFLIT » marquée');
    attendre(!JSON.stringify(r).includes('Secret'), 'un nom de personne gardé');
    // Colonnes dans un autre ordre : retrouvées par leur titre.
    const melange = faux.map(l => [l[4], l[3], l[5], l[2], l[1], l[0]]);
    attendreEgal(commandesVocales.analyser(melange).lignes, r.lignes, 'colonnes dans un autre ordre');
    await attendreRejet(async () => commandesVocales.analyser([['Commande', 'Bloc'], ['x', 'y']]), 'Formulation');
    const resume = commandesVocales.texteResume(r.compte, '08/11/2026 FICTIF');
    attendre(/4 formulation\(s\) gardée\(s\)/.test(resume) && /1 « à retirer », 2 ligne\(s\) de noms/.test(resume) && !/ouvre|appelle|autre fictif/.test(resume), `résumé : ${resume}`);
    // Lecture : fichier choisi (faux), deux lectures GET de la première feuille, copie gardée sur le (faux) téléphone.
    const appels = [];
    const memoire = new Map();
    const stockage = { getItem: k => memoire.get(k) ?? null, setItem: (k, v) => memoire.set(k, v), removeItem: k => memoire.delete(k) };
    const reponse = donnees => ({ json: async () => donnees });
    const copie = await commandesVocales.lireEtGarder({
      fichier: async () => ({ id: 'tableur-FICTIF' }),
      appeler: async (url, options) => { appels.push([url, options]); return url.includes('/values/') ? reponse({ values: faux }) : reponse({ sheets: [{ properties: { title: 'Feuille FICTIVE' } }] }); },
      stockage, maintenant: Date.UTC(2026, 10, 8, 12)
    });
    attendreEgal(appels.length, 2, 'nombre de lectures');
    attendre(appels.every(([url, options]) => url.startsWith('https://sheets.googleapis.com/v4/spreadsheets/tableur-FICTIF') && options === undefined), 'autre chose qu’une lecture du tableur');
    attendre(decodeURIComponent(appels[1][0]).includes("'Feuille FICTIVE'!A:F"), 'pas la première feuille A:F');
    attendreEgal([copie.compte.gardees, commandesVocales.copie(stockage).lignes.length, commandesVocales.copie(stockage).lu_le], [4, 4, '2026-11-08T12:00:00.000Z'], 'copie du téléphone');
    attendre([...memoire.keys()].join() === commandesVocales.CLE_COPIE, 'autre chose gardé');
    commandesVocales.oublier(stockage);
    attendreEgal(commandesVocales.copie(stockage), null, 'copie pas oubliée');
    await attendreRejet(() => commandesVocales.lireEtGarder({ fichier: async () => null, stockage }), 'Choisis d’abord le tableur');
  });

  // ----- 08/11/2026, 13h : commandes vocales lues avec le COMPTE CAP (option 4), FAUX tableur FICTIF -----
  await testAsync('Commandes vocales, compte Cap (08/11/2026, FAUX tableur FICTIF) : retrouvé par son nom exact, exporté en CSV (lecture seule, API Drive), mêmes exclusions ; identifiant absent, pas connecté, introuvable, en double = message clair ; CSV avec guillemets, virgules et retours à la ligne', async () => {
    // CSV de l'export Google : guillemets, virgules et retours à la ligne dans les cellules.
    attendreEgal(commandesVocales.lireCsv('﻿a,b\r\n"c, d","e ""f""\nsuite"\n,\n'), [['a', 'b'], ['c, d', 'e "f"\nsuite'], ['', '']], 'lecture du CSV');
    const csv = [
      'Ce que je veux,Commande,Bloc,Formulation,Code commande,"Remarque (Claude, datée)"',
      'Ouvrir l’écran Autre FICTIF,Ouvrir Autre,Mot-clé,autre fictif,NAV-02,',
      '"Ouvrir, FICTIF",Ouvrir Autre,Verbe d’ouverture,"ouvre, s’il te plaît",NAV-02,',
      'Mode sombre FICTIF,Mode sombre,Mot-clé,le noir fictif,NAV-10,"RETIRER 08/11/2026 : trop vague, FICTIF"',
      "Appeler FICTIF,Appel téléphonique,Nom d'appel,Prénom-Secret-FICTIF,TEL-01,",
      'Appeler FICTIF,Appel téléphonique,Cible,Autre-Prénom-Secret-FICTIF,COMMUN,',
      'Météo FICTIVE,Météo,Mot-clé,la météo fictive,,'
    ].join('\r\n');
    const appels = [];
    const memoire = new Map();
    const stockage = { getItem: k => memoire.get(k) ?? null, setItem: (k, v) => memoire.set(k, v), removeItem: k => memoire.delete(k) };
    const fauxCompte = (fichiers, { adresse = 'compte-cap@FICTIF', connecte = true } = {}) => ({
      adresse: () => adresse, connecte: () => connecte,
      appeler: async (url, options) => {
        appels.push([url, options]);
        if (url.includes('/export?')) return { text: async () => csv };
        return { json: async () => ({ files: fichiers }) };
      }
    });
    const copie = await commandesVocales.lireAvecCompteCap({ compte: fauxCompte([{ id: 'tableur-FICTIF' }]), stockage, maintenant: Date.UTC(2026, 10, 8, 13) });
    attendreEgal(copie.compte, { lues: 6, gardees: 2, retirees: 1, noms_exclus: 2, sans_code: 1, codes: 1 }, 'compte');
    attendreEgal(copie.lignes.map(l => l.formulation), ['autre fictif', 'ouvre, s’il te plaît'], 'formulations gardées');
    attendre(!JSON.stringify(commandesVocales.copie(stockage)).includes('Secret'), 'un nom de personne gardé sur le téléphone');
    // Deux lectures seulement, sur l'API Drive : recherche par nom exact, puis export CSV.
    attendreEgal(appels.length, 2, 'nombre de lectures');
    attendre(appels.every(([url, options]) => url.startsWith('https://www.googleapis.com/drive/v3/files') && options === undefined), 'autre chose qu’une lecture Drive');
    const q = new URL(appels[0][0]).searchParams.get('q');
    attendreEgal(q, "name='Commandes vocales' and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false", 'recherche');
    attendre(appels[1][0] === 'https://www.googleapis.com/drive/v3/files/tableur-FICTIF/export?mimeType=text%2Fcsv', `export : ${appels[1][0]}`);
    // Messages clairs, rien de lu.
    appels.length = 0;
    await attendreRejet(() => commandesVocales.lireAvecCompteCap({ compte: fauxCompte([], { adresse: '' }), stockage }), 'Identifiant du compte Cap absent');
    await attendreRejet(() => commandesVocales.lireAvecCompteCap({ compte: fauxCompte([], { connecte: false }), stockage }), 'pas connecté');
    attendreEgal(appels.length, 0, 'lecture sans connexion');
    await attendreRejet(() => commandesVocales.lireAvecCompteCap({ compte: fauxCompte([]), stockage }), 'partage-le avec le compte Cap');
    await attendreRejet(() => commandesVocales.lireAvecCompteCap({ compte: fauxCompte([{ id: 'a' }, { id: 'b' }]), stockage }), '2 tableurs');
    // La vraie porte du compte Cap n'accepte que l'API Drive en lecture : la recherche et l'export y passent.
    attendre(/www\.googleapis\.com/.test(SOURCE_GOOGLE_COMPTE_RELATIONS) && /\/drive\/v3\//.test(SOURCE_GOOGLE_COMPTE_RELATIONS), 'porte du compte Cap changée');
  });

  await testAsync('Commandes vocales (08/11/2026, 13h) : Réglages du Drive : « Lire les commandes vocales » actif, bouton de la fenêtre de choix caché, « Autoriser la lecture du compte Cap » prêt (caché) ; textes Google inchangés', async c => {
    const d = preparerInterface(c, { largeur: 412, hauteur: 900 }).doc;
    attendre(d.getElementById('choisir-commandes-vocales').hidden, 'bouton de la fenêtre de choix visible');
    attendre(!d.getElementById('lire-commandes-vocales').hidden && !d.getElementById('lire-commandes-vocales').disabled, '« Lire les commandes vocales » pas actif');
    attendreEgal([d.getElementById('lire-commandes-vocales').textContent, d.getElementById('autoriser-commandes-vocales').textContent], ['Lire les commandes vocales', 'Autoriser la lecture du compte Cap'], 'textes des boutons');
    attendre(d.getElementById('autoriser-commandes-vocales').hidden, '« Autoriser » visible d’office');
  });

  // ----- 08/11/2026 : commandes vocales, étape 2 : reconnaître la commande (FAUX tableur FICTIF) -----
  test('Commandes vocales, étape 2 (08/11/2026, FAUX tableur FICTIF) : action + cible du même code, verbes COMMUNS de la commande, variantes de transcription, code sans cible, accents et apostrophes ; égalité signalée ; « CONFLIT » signalé ; rien de reconnu ; aucune action lancée', () => {
    const L = (code, commande, bloc, formulation, conflit) => ({ code, commande, bloc, formulation, ...(conflit ? { conflit: true } : {}) });
    const lignes = [
      L('COMMUN', 'Navigation', 'Verbe d’ouverture', 'ouvre'),
      L('COMMUN', 'Navigation', 'Verbe d’ouverture', 'va dans'),
      L('COMMUN', 'Navigation', 'Complément de lieu', 'dans l’application'),
      L('NAV-02', 'Ouvrir Autre', 'Mot-clé', 'le menu autre'),
      L('NAV-02', 'Ouvrir Autre', 'Mot-clé', 'autre'),
      L('NAV-02', 'Navigation', 'Écran cible', 'l’écran autre'),
      L('NAV-02', 'Ouvrir Autre', 'Variante de transcription', 'ouvre notre'),
      L('NAV-08', 'Revenir à l’eau', 'Verbe de retour', 'remets-moi'),
      L('NAV-08', 'Revenir à l’eau', 'Mot-clé', 'l’eau seule'),
      L('NAV-08', 'Revenir à l’eau', 'Variante de transcription', 'l’os seul'),
      L('NAV-09', 'Fermer', 'Verbe de fermeture', 'ferme'),
      L('NAV-09', 'Fermer', 'Verbe de fermeture', 'termine', true),
      L('NAV-09', 'Fermer', 'Mot-clé', 'ça'),
      L('NAV-24', 'Quitter l’application', 'Verbe de fermeture de l’application', 'ferme'),
      L('NAV-24', 'Quitter l’application', 'Mot-clé', 'cap fictif'),
      L('DIC-02', 'Dictée', 'Verbe d’arrêt', 'stop'),
      L('DIC-02', 'Dictée', 'Variante de transcription', 'arrête'),
      L('ZZZ-01', 'Essai FICTIF', 'Verbe d’essai', 'essaie'),
      L('ZZZ-01', 'Essai FICTIF', 'Mot-clé', 'le truc fictif'),
      L('ZZZ-02', 'Essai FICTIF bis', 'Verbe d’essai', 'essaie'),
      L('ZZZ-02', 'Essai FICTIF bis', 'Mot-clé', 'le chat fictif')
    ];
    const r = phrase => commandesVocales.reconnaitre(phrase, lignes);
    const code = phrase => { const x = r(phrase); return x.statut === 'reconnu' ? x.code : x.statut; };
    // Verbes COMMUNS de la commande « Navigation » + mot-clé du code ; accents, majuscules, ponctuation.
    attendreEgal(code('Ouvre l’écran Autre !'), 'NAV-02', 'ouvre + écran autre');
    attendreEgal(code('Va dans le menu autre, dans l’application'), 'NAV-02', 'va dans + menu autre');
    attendreEgal(r('Ouvre l’écran Autre').mots, ['ouvre', 'l ecran autre'], 'mots reconnus (le plus long)');
    // Variante entière qui contient déjà le verbe.
    attendreEgal(code('ouvre notre'), 'NAV-02', 'variante entière');
    // Action et cible du code lui-même ; variante de transcription de la cible.
    attendreEgal(code('Remets-moi l’eau seule'), 'NAV-08', 'eau seule');
    attendreEgal(code('remets moi l’os seul'), 'NAV-08', 'variante de la cible');
    // Une cible seule, ou un verbe seul, ne suffisent pas quand le code a des cibles.
    // 08/11/2026 (correction A, décision de Max, question 12) : « ferme » seul ferme l'écran en cours (NAV-09).
    // Avant : ['rien', 'incomplet'] (ERREUR de l'étape 0, qui donnait « Je ne suis pas une IA »), et encore avant ['rien', 'rien'].
    attendreEgal([code('l’eau seule'), code('ferme')], ['rien', 'NAV-09'], 'cible seule ou verbe seul');
    // Même verbe pour deux codes : la cible décide.
    attendreEgal([code('ferme ça'), code('ferme cap fictif')], ['NAV-09', 'NAV-24'], 'la cible départage');
    // Code sans cible : le verbe (ou sa variante) suffit.
    attendreEgal([code('stop'), code('Arrête !')], ['DIC-02', 'DIC-02'], 'code sans cible');
    // Mots entiers seulement (« stopper » n'est pas « stop »).
    attendreEgal(code('il faut stopper'), 'rien', 'mot entier');
    // Égalité : signalée, jamais tranchée.
    // 09/11/2026 (mission D) : l'hésitation porte aussi « options » (les possibilités, pour la fenêtre de gros choix).
    // Avant : attendreEgal(r(…), { statut: 'ambigu', codes: [...], commandes: [...] }, 'égalité');
    const egalite = r('essaie le truc fictif et le chat fictif');
    attendreEgal({ statut: egalite.statut, codes: egalite.codes, commandes: egalite.commandes }, { statut: 'ambigu', codes: ['ZZZ-01', 'ZZZ-02'], commandes: ['Essai FICTIF', 'Essai FICTIF bis'] }, 'égalité');
    attendreEgal(egalite.options.map(o => [o.statut, o.code]), [['reconnu', 'ZZZ-01'], ['reconnu', 'ZZZ-02']], 'possibilités gardées');
    // Ligne « CONFLIT » : reconnue mais signalée.
    const conflit = r('termine ça');
    attendre(conflit.statut === 'reconnu' && conflit.code === 'NAV-09' && conflit.conflit === true, 'conflit pas signalé');
    attendre(/CONFLIT/.test(commandesVocales.texteReconnaissance(conflit)), 'texte du conflit');
    // Rien, phrase vide, pas de tableur.
    attendreEgal([code('bonjour'), code('   '), commandesVocales.reconnaitre('ouvre autre', []).statut], ['rien', 'rien', 'pas_de_tableur'], 'rien');
    attendreEgal(commandesVocales.texteReconnaissance(r('ouvre autre')), 'Commande reconnue : NAV-02 (Ouvrir Autre). Mots reconnus : « ouvre », « autre ».', 'texte');
    // Aucune action : le module ne touche ni aux écrans ni au cerveau.
    attendre(!/click\(|showModal|montrer\(|cerveau|actionsCap/.test(SOURCE_COMMANDES_VOCALES_TEST), 'le module lance une action');
  });

  await testAsync('Commandes vocales, étape 2 (08/11/2026) : Réglages du Drive : champ « Phrase à essayer » simple (texte, ni mot de passe ni adresse), bouton « Reconnaître la phrase », résultat affiché', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const champ = ui.parId('phrase-commandes-vocales');
    attendre(champ && champ.type === 'text' && champ.getAttribute('autocomplete') === 'off' && !/mot de passe|e-mail|adresse|identifiant/i.test(ui.doc.querySelector('label[for="phrase-commandes-vocales"]').textContent), 'champ qui ressemble à une connexion');
    attendreEgal(ui.parId('reconnaitre-commandes-vocales').textContent, 'Reconnaître la phrase', 'texte du bouton');
    champ.value = 'ouvre autre';
    ui.parId('reconnaitre-commandes-vocales').click();
    const zone = ui.parId('resultat-commandes-vocales');
    attendre(!zone.hidden && zone.textContent.length > 0, 'pas de résultat affiché');
  });

  // ----- 08/11/2026 : geste RETOUR universel (accord de Max, choix A) -----
  function brancherGesteRetour(c, ui, temps) {
    const m = objetIsole(SOURCE_GESTE_RETOUR_TEST, 'gesteRetour', { window: { CAP_TESTS: true } });
    return m.brancher(ui.doc, { fermetureFenetres: ui.fermetureFenetres, maintenant: () => temps.t });
  }
  // Glissement simulé : départ sur « cible » en (x, y), arrivée en (fx, fy) après « duree » ms.
  function glisserRetour(ui, temps, cible, [x, y, fx, fy, duree = 200]) {
    temps.t = 0;
    const debut = new Event('touchstart', { bubbles: true });
    Object.defineProperties(debut, { touches: { value: [{ clientX: x, clientY: y }] }, changedTouches: { value: [] } });
    cible.dispatchEvent(debut);
    temps.t = duree;
    const fin = new Event('touchend', { bubbles: true });
    Object.defineProperties(fin, { touches: { value: [] }, changedTouches: { value: [{ clientX: fx, clientY: fy }] } });
    cible.dispatchEvent(fin);
  }
  const NET = [200, 200, 205, 450]; // 250 px sur 900, droit, rapide
  const attendreMs = ms => new Promise(r => setTimeout(r, ms)); // vraie attente (pause() ne prend pas de durée)

  await testAsync('Geste RETOUR (08/11/2026) : réglages (20 %, 2 fois plus vertical, 1,5 s, bande du haut 48 px, fondu 450 ms) ; script chargé après l’accueil et gardé hors connexion', async c => {
    const m = objetIsole(SOURCE_GESTE_RETOUR_TEST, 'gesteRetour', { window: { CAP_TESTS: true } });
    attendreEgal({ ...m.REGLAGES }, { fractionHauteur: 0.2, rapportVertical: 2, dureeMaxMs: 1500, bandeHautPx: 48, fonduMs: 450 }, 'réglages');
    attendre(SOURCE_HTML.indexOf('src="geste_retour.js"') > SOURCE_HTML.indexOf('src="accueil_cap.js"'), 'script pas chargé après accueil_cap.js');
    attendre(/geste-retour-sortie[\s\S]*450ms/.test(SOURCE_STYLE), 'fondu de 450 ms absent');
  });

  await testAsync('Geste RETOUR (08/11/2026) : écrans « Autre » et « Réglages » : glisser de haut en bas, parti de n’importe où (même d’un bouton), fond puis ferme ; « Fermer » reste en secours', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    brancherAccueil(c, ui);
    const temps = { t: 0 };
    brancherGesteRetour(c, ui, temps);
    const el = id => ui.parId(id);
    for (const [ouvrir, ecran, fermer, depart] of [['ouvrir-autre', 'ecran-autre', 'fermer-autre', 'ouvrir-scanner'], ['ouvrir-reglages-cap', 'ecran-reglages', 'fermer-reglages', 'fermer-reglages']]) {
      el('ouvrir-autre').click();
      if (ouvrir !== 'ouvrir-autre') el(ouvrir).click();
      attendre(!el(ecran).hidden, `${ecran} pas ouvert`);
      glisserRetour(ui, temps, el(depart), NET);
      attendre(el(ecran).classList.contains('geste-retour-sortie') && !el(ecran).hidden, `${ecran} : pas de fondu`);
      await attendreQue(() => el(ecran).hidden && !el(ecran).classList.contains('geste-retour-sortie'), `${ecran} pas fermé après le fondu`);
      // 09/11/2026 (règle du retour) : Réglages, ouvert depuis Autre, revient à Autre ; Autre revient à l'accueil.
      if (ecran === 'ecran-reglages') { attendre(!el('ecran-autre').hidden, 'Réglages ne revient pas à Autre'); el('fermer-autre').click(); transitionEcrans.terminer(ui.doc); }
      attendre(!ui.doc.documentElement.classList.contains('ecran-cap-ouvert'), 'retour à l’accueil manqué');
      attendreEgal(el(fermer).textContent, 'Fermer', 'bouton Fermer de secours');
    }
  });

  await testAsync('Geste RETOUR (08/11/2026) : jamais pour un geste court, lent, de travers, vers le haut, ni parti tout en haut de l’écran (rideau des notifications)', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    brancherAccueil(c, ui);
    const temps = { t: 0 };
    brancherGesteRetour(c, ui, temps);
    const el = id => ui.parId(id);
    el('ouvrir-autre').click();
    for (const [nom, args] of [['court', [200, 200, 200, 350]], ['lent', [200, 200, 200, 600, 1600]], ['de travers', [100, 200, 300, 450]],
      ['vers le haut', [200, 700, 200, 200]], ['tout en haut', [200, 20, 200, 500]]]) {
      glisserRetour(ui, temps, el('ecran-autre'), args);
      attendre(!el('ecran-autre').hidden && !el('ecran-autre').classList.contains('geste-retour-sortie'), `geste ${nom} : Autre fermé`);
    }
  });

  await testAsync('Geste RETOUR (08/11/2026) : fenêtre ordinaire (Aide) : même sortie commune que « toucher à côté », après le fondu', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const temps = { t: 0 };
    brancherGesteRetour(c, ui, temps);
    const aide = ui.parId('aide');
    aide.showModal();
    glisserRetour(ui, temps, ui.parId('titre-aide'), NET);
    attendre(aide.open && aide.classList.contains('geste-retour-sortie'), 'pas de fondu avant la fermeture');
    await attendreQue(() => !aide.open && !aide.classList.contains('geste-retour-sortie'), 'Aide pas fermée');
  });

  await testAsync('Geste RETOUR (08/11/2026) : texte commencé = « Garder / Jeter » tout de suite, sans fondu ni fermeture (zéro perte)', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const temps = { t: 0 };
    brancherGesteRetour(c, ui, temps);
    const ajout = ui.parId('ajout-tache');
    ajout.showModal();
    const champ = ui.parId('intitule');
    champ.value = 'Tâche FICTIF commencée';
    champ.dispatchEvent(new Event('input', { bubbles: true }));
    glisserRetour(ui, temps, ui.parId('titre-ajout'), NET);
    const question = ajout.querySelector(':scope > .question-fermeture');
    attendre(question && /Garder/.test(question.textContent) && /Jeter/.test(question.textContent), 'question Garder / Jeter absente');
    attendre(ajout.open && !ajout.classList.contains('geste-retour-sortie'), 'fenêtre fermée ou en fondu');
    attendreEgal(champ.value, 'Tâche FICTIF commencée', 'texte perdu');
    // Un 2e geste pendant la question ne ferme rien.
    glisserRetour(ui, temps, ui.parId('titre-ajout'), NET);
    await attendreMs(500);
    attendre(ajout.open && champ.value === 'Tâche FICTIF commencée', 'fermé pendant la question');
  });

  await testAsync('Geste RETOUR (08/11/2026) : liste défilée = le doigt la fait défiler, rien ne se ferme ; liste tout en haut = fermeture', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const temps = { t: 0 };
    brancherGesteRetour(c, ui, temps);
    const aide = ui.parId('aide');
    aide.showModal();
    const liste = ui.doc.createElement('div');
    liste.style.cssText = 'height:120px;overflow:auto';
    const long = ui.doc.createElement('p');
    long.style.height = '900px';
    long.textContent = 'Liste FICTIF';
    liste.append(long);
    aide.append(liste);
    liste.scrollTop = 60;
    attendre(liste.scrollTop > 0, 'liste pas défilée');
    glisserRetour(ui, temps, long, NET);
    await attendreMs(550);
    attendre(aide.open && !aide.classList.contains('geste-retour-sortie'), 'fermée alors que la liste était défilée');
    liste.scrollTop = 0;
    glisserRetour(ui, temps, long, NET);
    await attendreQue(() => !aide.open, 'liste tout en haut : pas fermée');
  });

  await testAsync('Geste RETOUR (08/11/2026) : champs de texte, curseurs et déplacement de tuile exclus', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const temps = { t: 0 };
    brancherGesteRetour(c, ui, temps);
    const aide = ui.parId('aide');
    aide.showModal();
    // 09/11/2026 (défaut 3) : un champ d'UNE ligne ne bloque plus le geste (voir le test « Défaut 3 ») ; le curseur et le
    // texte sur plusieurs lignes, si. Avant : for (const type of ['text', 'range']) …
    for (const type of ['range']) {
      const champ = ui.doc.createElement('input');
      champ.type = type;
      aide.append(champ);
      glisserRetour(ui, temps, champ, NET);
    }
    const zone = ui.doc.createElement('textarea');
    aide.append(zone);
    glisserRetour(ui, temps, zone, NET);
    await attendreMs(550);
    attendre(aide.open, 'fermée depuis un champ ou un curseur');
    const tuile = ui.doc.createElement('div');
    tuile.className = 'tuile en-deplacement';
    ui.doc.body.append(tuile);
    glisserRetour(ui, temps, ui.parId('titre-aide'), NET);
    await attendreMs(550);
    attendre(aide.open, 'fermée pendant le déplacement d’une tuile');
    tuile.remove();
  });

  await testAsync('Geste RETOUR (08/11/2026) : la visionneuse PDF, la visionneuse et le lecteur MP3 ne se ferment jamais par ce geste (boutons et geste du bord droit gardés)', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const temps = { t: 0 };
    brancherGesteRetour(c, ui, temps);
    for (const id of ['lecteur-pdf-relations', 'visionneuse-cap', 'lecteur-mp3-relations']) {
      const f = ui.parId(id);
      f.showModal();
      glisserRetour(ui, temps, f, NET);
      await attendreMs(550);
      attendre(f.open && !f.classList.contains('geste-retour-sortie'), `${id} fermé par le geste`);
      f.close();
    }
    attendreEgal(ui.parId('pdf-fermer-relations').textContent, 'Fermer', 'bouton de la visionneuse PDF');
    attendre(ui.parId('geste-fermer-lecteur'), 'bande du bord droit du lecteur absente');
  });

  await testAsync('Geste RETOUR (08/11/2026) : fenêtre sans sortie commune = son bouton « Fermer » ; fenêtre de choix = « Fermer » tout de suite (sa propre sortie) ; animations réduites = fermeture immédiate', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const temps = { t: 0 };
    brancherGesteRetour(c, ui, temps);
    // Vérification (relations) : son bouton Fermer, après le fondu.
    const verif = ui.parId('verification-relations');
    let clics = 0;
    const bouton = ui.parId('relations-fermer');
    bouton.addEventListener('click', () => { clics++; verif.close(); });
    verif.showModal();
    ui.parId('relations-confirmer').hidden = false;
    glisserRetour(ui, temps, verif, NET);
    attendre(clics === 0 && verif.classList.contains('geste-retour-sortie'), 'pas de fondu avant Fermer');
    await attendreQue(() => clics === 1 && !verif.open, 'Fermer pas touché');
    // Fenêtre de choix (musique) : « Fermer » touché tout de suite, pas de second fondu.
    const musique = ui.parId('musique-relations');
    let clicsMusique = 0;
    ui.parId('fermer-musique-relations').addEventListener('click', () => { clicsMusique++; });
    musique.showModal();
    glisserRetour(ui, temps, musique, NET);
    attendre(clicsMusique === 1 && !musique.classList.contains('geste-retour-sortie'), 'fenêtre de choix : Fermer pas touché tout de suite');
    musique.close();
    // Animations réduites : fermeture immédiate, sans fondu.
    ui.cadre.contentWindow.matchMedia = q => ({ matches: /reduce/.test(q), addEventListener() {}, removeEventListener() {} });
    const aide = ui.parId('aide');
    aide.showModal();
    glisserRetour(ui, temps, ui.parId('titre-aide'), NET);
    attendre(!aide.open && !aide.classList.contains('geste-retour-sortie'), 'animations réduites : pas fermée tout de suite');
  });

  await testAsync('Geste RETOUR (08/11/2026) : sur l’accueil et sur « Tout voir », ce module ne fait rien (leurs propres gestes restent)', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const temps = { t: 0 };
    const m = brancherGesteRetour(c, ui, temps);
    let clics = 0;
    for (const b of ui.doc.querySelectorAll('button')) if (b.textContent.trim() === 'Fermer') b.addEventListener('click', () => { clics++; });
    glisserRetour(ui, temps, ui.doc.body, NET);
    await attendreMs(550);
    attendreEgal(clics, 0, 'un Fermer touché depuis l’accueil');
    attendre(typeof m.fermer === 'function', 'module pas branché');
  });

  // ----- 08/11/2026 : ouvertures DOUCES des écrans (étape 1 de l'écran Micro, accord de Max) -----
  const attendreMsT = ms => new Promise(r => setTimeout(r, ms));
  const affiche = (ui, el) => el.getClientRects().length > 0;
  const finTransition = async (ui) => { await attendreQue(() => !ui.doc.querySelector('.ecran-part, .ecran-entree, .ecran-entree-directe'), 'transition pas finie'); };

  await testAsync('Ouvertures douces (08/11/2026) : réglages (fondu 450 ms, sortie du sable 1 s) ; script chargé avant l’application et gardé hors connexion ; animations réduites coupées dans le style', async c => {
    attendreEgal({ ...transitionEcrans.REGLAGES }, { sortieMs: 450, entreeMs: 1000 }, 'réglages');
    // 09/11/2026 : + l'écran Chercher. Avant : ['accueil-boutons', 'ecran-autre', 'ecran-reglages', 'ecran-micro', 'ecran-complet', 'zone-recherche']
    attendreEgal(transitionEcrans.ECRANS, ['accueil-boutons', 'ecran-autre', 'ecran-reglages', 'ecran-micro', 'ecran-chercher', 'ecran-complet', 'zone-recherche'], 'écrans concernés'); // + écran Micro (étape 2)
    attendre(SOURCE_HTML.indexOf('src="transition_ecrans.js"') > 0 && SOURCE_HTML.indexOf('src="transition_ecrans.js"') < SOURCE_HTML.indexOf('src="app.js"'), 'script pas chargé avant app.js');
    attendre(/prefers-reduced-motion: reduce\) \{ \.ecran-part, \.ecran-entree, \.ecran-entree-directe \{ animation: none; \} \}/.test(SOURCE_STYLE), 'animations réduites pas coupées');
    attendre(/\.ecran-entree \{ animation: cap-monte-du-sable 1000ms [^;]* 450ms both; \}/.test(SOURCE_STYLE), 'sortie du sable après le fondu absente');
  });

  await testAsync('Ouvertures douces (08/11/2026) : accueil → « Autre » : les 3 boutons restent dessinés et fondent (sans capter le doigt), puis « Autre » sort du sable ; l’état change tout de suite', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    brancherAccueil(c, ui);
    const el = id => ui.parId(id);
    el('ouvrir-autre').click();
    attendre(!el('ecran-autre').hidden && ui.doc.documentElement.classList.contains('ecran-cap-ouvert'), 'état pas changé tout de suite');
    const accueil = el('accueil-boutons');
    attendre(affiche(ui, accueil) && accueil.classList.contains('ecran-part') && accueil.inert, 'accueil pas en train de fondre');
    attendreEgal(ui.cadre.contentWindow.getComputedStyle(accueil).pointerEvents, 'none', 'accueil qui fond capte le doigt');
    attendre(el('ecran-autre').classList.contains('ecran-entree'), '« Autre » ne sort pas du sable');
    await attendreMsT(600);
    attendre(!affiche(ui, accueil) && !accueil.classList.contains('ecran-part') && !accueil.inert && !accueil.getAttribute('style'), 'accueil pas rangé après le fondu');
    await finTransition(ui);
    attendre(touchable(ui, el('ouvrir-reglages-cap')) && touchable(ui, el('ouvrir-scanner')), 'boutons de « Autre » pas touchables à la fin'); // « Fermer » caché (08/11/2026)
  });

  await testAsync('Ouvertures douces (08/11/2026) : « Autre » → « Réglages », puis « Fermer » → accueil : chaque fois l’écran d’avant fond, puis le nouveau sort du sable', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    brancherAccueil(c, ui);
    const el = id => ui.parId(id);
    el('ouvrir-autre').click();
    await finTransition(ui);
    el('ouvrir-reglages-cap').click();
    attendre(el('ecran-autre').classList.contains('ecran-part') && el('ecran-reglages').classList.contains('ecran-entree'), 'Autre → Réglages sans transition');
    await finTransition(ui);
    el('fermer-reglages').click();
    // 09/11/2026 (règle du retour) : Réglages → Autre (d'où il venait), puis Autre → accueil, en douceur chaque fois.
    // Avant : Réglages → accueil directement.
    attendre(el('ecran-reglages').classList.contains('ecran-part') && el('ecran-autre').classList.contains('ecran-entree'), 'Réglages → Autre sans transition');
    await finTransition(ui);
    el('fermer-autre').click();
    attendre(el('ecran-autre').classList.contains('ecran-part') && el('accueil-boutons').classList.contains('ecran-entree'), 'Autre → accueil sans transition');
    await finTransition(ui);
    attendre(el('ecran-reglages').hidden && touchable(ui, el('ouvrir-autre')), 'accueil pas revenu');
  });

  await testAsync('Ouvertures douces (08/11/2026) : « Chercher » s’ouvre et se ferme en douceur (accueil ↔ « Tout voir » et sa barre de recherche)', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    brancherAccueil(c, ui);
    const el = id => ui.parId(id);
    // 09/11/2026 : accueil → écran Chercher → (To-do) écran des tâches, chaque fois en douceur, UNE seule transition
    // à chaque toucher. Avant : « Chercher » ouvrait directement l'écran des tâches.
    el('ouvrir-chercher').click();
    attendre(!el('ecran-chercher').hidden, 'écran Chercher pas ouvert tout de suite');
    attendre(el('accueil-boutons').classList.contains('ecran-part') && el('ecran-chercher').classList.contains('ecran-entree'), 'accueil → Chercher sans transition');
    await finTransition(ui);
    el('chercher-todo').click();
    attendre(!el('ecran-complet').hidden && el('ecran-chercher').hidden, 'Chercher pas ouvert tout de suite');
    attendre(el('ecran-chercher').classList.contains('ecran-part'), 'Chercher ne fond pas');
    attendre(!el('accueil-boutons').classList.contains('ecran-entree') && !el('accueil-boutons').classList.contains('ecran-part'), 'l’accueil apparaît entre les deux');
    attendre(el('ecran-complet').classList.contains('ecran-entree') && el('zone-recherche').classList.contains('ecran-entree'), '« Tout voir » ne sort pas du sable');
    await finTransition(ui);
    el('fermer-chercher').click();
    // 09/11/2026 (règle du retour) : les tâches, ouvertes depuis Chercher, reviennent à Chercher (douceur), puis l'accueil.
    attendre(el('ecran-complet').hidden && el('ecran-complet').classList.contains('ecran-part') && el('ecran-chercher').classList.contains('ecran-entree'), 'retour de Chercher sans transition');
    await finTransition(ui);
    el('fermer-chercher-cap').click();
    attendre(el('accueil-boutons').classList.contains('ecran-entree'), 'Chercher → accueil sans transition');
    await finTransition(ui);
    attendre(!affiche(ui, el('ecran-complet')) && touchable(ui, el('ouvrir-chercher')), 'accueil pas revenu');
  });

  await testAsync('Ouvertures douces (08/11/2026) : animations réduites = aucune transition, tout d’un coup', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    ui.cadre.contentWindow.matchMedia = q => ({ matches: /reduce/.test(q), addEventListener() {}, removeEventListener() {} });
    brancherAccueil(c, ui);
    const el = id => ui.parId(id);
    for (const id of ['ouvrir-autre', 'ouvrir-reglages-cap', 'fermer-reglages', 'ouvrir-chercher', 'chercher-todo']) { // 09/11/2026 : + To-do
      el(id).click();
      attendre(!ui.doc.querySelector('.ecran-part, .ecran-entree, .ecran-entree-directe'), `${id} : transition malgré les animations réduites`);
    }
    attendre(!affiche(ui, el('accueil-boutons')) && affiche(ui, el('ecran-complet')), 'Chercher pas ouvert d’un coup');
  });

  await testAsync('Ouvertures douces (08/11/2026) : changement rapide (ouvrir puis fermer aussitôt) : rien ne reste coincé (ni fondu, ni style, ni écran inerte)', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    brancherAccueil(c, ui);
    const el = id => ui.parId(id);
    el('ouvrir-autre').click();
    el('fermer-autre').click();
    el('ouvrir-autre').click();
    el('ouvrir-reglages-cap').click();
    el('fermer-reglages').click();
    await finTransition(ui);
    await attendreMsT(100);
    for (const id of transitionEcrans.ECRANS) {
      const x = el(id);
      attendre(!x.inert || id === 'ecran-complet' || id === 'zone-recherche', `${id} resté inerte`);
      attendre(!x.getAttribute('style'), `${id} garde un style forcé : ${x.getAttribute('style')}`);
    }
    // 09/11/2026 (règle du retour) : Réglages (ouvert depuis Autre) revient à Autre. Avant : l'accueil.
    attendre(!el('ecran-autre').hidden && el('ecran-reglages').hidden && touchable(ui, el('ouvrir-scanner')), 'mauvais écran à la fin');
  });

  await testAsync('Ouvertures douces (08/11/2026) : après le geste de retour (écran déjà fondu), l’accueil sort du sable sans attendre un second fondu', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    brancherAccueil(c, ui);
    const temps = { t: 0 };
    brancherGesteRetour(c, ui, temps);
    const el = id => ui.parId(id);
    el('ouvrir-autre').click();
    await finTransition(ui);
    glisserRetour(ui, temps, el('ecran-autre'), NET);
    await attendreQue(() => el('ecran-autre').hidden, 'geste de retour sans effet');
    attendre(!el('ecran-autre').classList.contains('ecran-part'), 'second fondu après le geste');
    attendre(el('accueil-boutons').classList.contains('ecran-entree-directe'), 'accueil attend un second fondu');
    await finTransition(ui);
    attendre(touchable(ui, el('ouvrir-autre')), 'accueil pas revenu');
  });

  await testAsync('Ouvertures douces (08/11/2026) : le glissement vers les tâches (bas vers haut) passe aussi par la transition douce', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    brancherAccueil(c, ui);
    glisser(ui, ui.doc.querySelector('.ecran'), 200, 700, 200, 300);
    attendre(!ui.parId('ecran-complet').hidden && ui.parId('ecran-complet').classList.contains('ecran-entree'), 'glissement sans transition');
    await finTransition(ui);
  });

  // ----- 08/11/2026 : écran Micro (étape 2, accord de Max) et « Fermer » retiré de « Autre » -----
  const ouvrirEcranMicro = async (ui) => { ui.parId('ouvrir-micro').click(); await finTransition(ui); };

  await testRemplace('Écran Micro (08/11/2026) : accueil INCHANGÉ à l’œil (un seul micro, Chercher, Autre ; ni « + » ni clavier) ; le micro de l’accueil a le même dessin que le vrai micro', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    brancherAccueil(c, ui);
    const el = id => ui.parId(id);
    const nav = el('accueil-boutons');
    attendreEgal([...nav.querySelectorAll('button')].map(b => b.id), ['ouvrir-micro', 'ouvrir-chercher', 'ouvrir-autre'], 'boutons de l’accueil');
    attendreEgal(el('ouvrir-micro').querySelector('svg').innerHTML, el('microphone').querySelector('svg').innerHTML, 'dessin du micro différent');
    for (const id of ['microphone', 'micro-ajouter', 'micro-clavier', 'ajouter', 'ouvrir-clavier']) attendre(!affiche(ui, el(id)), `${id} visible sur l’accueil`);
    attendre(touchable(ui, el('ouvrir-micro')), 'micro de l’accueil pas touchable');
  });

  await testRemplace('Écran Micro (08/11/2026) : toucher le micro de l’accueil NE lance PAS la dictée ; l’accueil s’efface doucement puis la rangée sort du sable', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    brancherAccueil(c, ui);
    const el = id => ui.parId(id);
    const avant = el('statut').textContent;
    el('ouvrir-micro').click();
    attendreEgal(el('statut').textContent, avant, 'la dictée a été tentée au toucher du micro de l’accueil');
    attendre(!el('ecran-micro').hidden && el('ecran-autre').hidden, 'écran Micro pas ouvert');
    attendre(el('accueil-boutons').classList.contains('ecran-part') && el('ecran-micro').classList.contains('ecran-entree'), 'pas de transition douce');
    await finTransition(ui);
    attendre(!affiche(ui, el('accueil-boutons')), 'accueil encore là');
  });

  for (const [largeur, hauteur] of [[412, 915], [360, 640]]) {
    await testRemplace(`Écran Micro (08/11/2026) : « + » à gauche, micro au milieu, clavier à droite, sur une rangée centrée, gros boutons IDENTIQUES, sans cadre ni fond, aucun « Fermer » affiché (${largeur}×${hauteur})`, async c => {
      const ui = preparerInterface(c, { largeur, hauteur });
      brancherAccueil(c, ui);
      const el = id => ui.parId(id);
      await ouvrirEcranMicro(ui);
      const ids = ['micro-ajouter', 'microphone', 'micro-clavier'];
      const R = ids.map(id => el(id).getBoundingClientRect());
      attendre(R[0].right <= R[1].left && R[1].right <= R[2].left, 'ordre « + » / micro / clavier faux');
      attendre(R.every(r => Math.abs(r.top - R[0].top) < 1 && Math.abs(r.width - R[0].width) < 1 && Math.abs(r.height - R[0].height) < 1), 'boutons pas identiques ou pas alignés');
      attendre(R[0].width >= 64 && R.every(r => r.left >= 0 && r.right <= largeur && r.top >= 0 && r.bottom <= hauteur), 'boutons trop petits ou hors écran');
      attendre(Math.abs((R[1].left + R[1].right) / 2 - largeur / 2) < 2, 'micro pas au milieu');
      const vue = ui.cadre.contentWindow;
      for (const id of ids) {
        const s = vue.getComputedStyle(el(id));
        attendre(s.borderTopStyle === 'none' && s.backgroundColor === 'rgba(0, 0, 0, 0)' && s.boxShadow === 'none', `${id} a un cadre ou un fond`);
        attendre(touchable(ui, el(id)), `${id} pas touchable`);
      }
      const s = vue.getComputedStyle(el('ecran-micro'));
      attendre(s.backgroundColor === 'rgba(0, 0, 0, 0)' && s.borderTopStyle === 'none', 'écran Micro avec un fond ou un cadre');
      attendre(el('fermer-micro').hidden && !affiche(ui, el('fermer-micro')), '« Fermer » affiché');
    });
  }

  await testRemplace('Écran Micro (08/11/2026) : SEUL le micro du milieu lance la dictée (le même bouton et le même code qu’avant)', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    brancherAccueil(c, ui);
    const el = id => ui.parId(id);
    await ouvrirEcranMicro(ui);
    attendre(el('ecran-micro').contains(el('microphone')) && el('microphone').getAttribute('aria-label') === 'Dicter une tâche', 'vrai micro pas au milieu');
    parlerAuGrosMicro(el('microphone')); // 09/11/2026 : deux touchers
    // Dictée simulée indisponible : le code de dictée répond (preuve qu'il est bien branché sur ce bouton).
    attendre(/dictée n'est pas disponible/.test(el('statut').textContent), `le micro du milieu ne lance pas la dictée : ${el('statut').textContent}`);
  });

  await testRemplace('Écran Micro (08/11/2026) : « + » ouvre « Ajouter une tâche », le clavier ouvre « Écrire une demande » ; en les fermant, on reste sur l’écran Micro', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    brancherAccueil(c, ui);
    const el = id => ui.parId(id);
    await ouvrirEcranMicro(ui);
    el('micro-ajouter').click();
    attendre(el('ajout-tache').open && el('titre-ajout').textContent === 'Ajouter une tâche', '« + » n’ouvre pas « Ajouter une tâche »');
    el('ajout-tache').close();
    el('micro-clavier').click();
    attendre(el('clavier').open, 'le clavier n’ouvre pas « Écrire une demande »');
    el('clavier').close();
    attendre(!el('ecran-micro').hidden && affiche(ui, el('microphone')), 'écran Micro quitté');
  });

  await testRemplace('Écran Micro (08/11/2026) : le geste de retour (haut en bas) le ferme et ramène l’accueil en douceur ; animations réduites : tout d’un coup', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    brancherAccueil(c, ui);
    const temps = { t: 0 };
    brancherGesteRetour(c, ui, temps);
    const el = id => ui.parId(id);
    await ouvrirEcranMicro(ui);
    glisserRetour(ui, temps, el('ecran-micro'), NET);
    attendre(el('ecran-micro').classList.contains('geste-retour-sortie'), 'pas de fondu');
    await attendreQue(() => el('ecran-micro').hidden, 'geste de retour sans effet');
    await finTransition(ui);
    attendre(touchable(ui, el('ouvrir-micro')), 'accueil pas revenu');
    ui.cadre.contentWindow.matchMedia = q => ({ matches: /reduce/.test(q), addEventListener() {}, removeEventListener() {} });
    el('ouvrir-micro').click();
    attendre(!el('ecran-micro').hidden && !ui.doc.querySelector('.ecran-part, .ecran-entree') && affiche(ui, el('microphone')), 'animations réduites : pas d’un coup');
    glisserRetour(ui, temps, el('ecran-micro'), NET);
    attendre(el('ecran-micro').hidden, 'animations réduites : geste pas immédiat');
  });

  await testAsync('« Autre » (08/11/2026, décision de Max) : « Fermer » retiré de l’écran (bouton gardé, caché) ; le geste de retour ferme quand même « Autre »', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    brancherAccueil(c, ui);
    const temps = { t: 0 };
    brancherGesteRetour(c, ui, temps);
    const el = id => ui.parId(id);
    el('ouvrir-autre').click();
    await finTransition(ui);
    attendre(el('fermer-autre') && el('fermer-autre').textContent === 'Fermer' && el('fermer-autre').hidden && !affiche(ui, el('fermer-autre')), '« Fermer » encore affiché, ou effacé');
    attendre(/décision de Max\) : « Fermer » retiré de l'écran/.test(SOURCE_HTML), 'commentaire daté absent');
    glisserRetour(ui, temps, el('ouvrir-scanner'), NET);
    await attendreQue(() => el('ecran-autre').hidden, 'le geste ne ferme plus « Autre »');
  });

  // ----- 08/11/2026 : bouton « continu » (étape 3, accord de Max) -----
  const dicteeDisponible = ui => Object.assign(ui.dictee, { disponible: () => true, enCours: () => false, arreter() {}, demarrer() {} });

  for (const [largeur, hauteur] of [[412, 915], [360, 640]]) {
    await testRemplace(`Bouton « continu » (08/11/2026) : sous la rangée, centré sous le micro, identique aux trois autres, sans cadre ni fond au repos, icône de Zencoder (${largeur}×${hauteur})`, async c => {
      const ui = preparerInterface(c, { largeur, hauteur });
      brancherAccueil(c, ui);
      const el = id => ui.parId(id);
      await ouvrirEcranMicro(ui);
      const m = el('microphone').getBoundingClientRect();
      const r = el('micro-continu').getBoundingClientRect();
      attendre(r.top >= m.bottom && Math.abs((r.left + r.right) / 2 - (m.left + m.right) / 2) < 2, '« continu » pas sous le micro');
      attendre(Math.abs(r.width - m.width) < 1 && Math.abs(r.height - m.height) < 1 && r.bottom <= hauteur, '« continu » pas identique ou hors écran');
      const s = ui.cadre.contentWindow.getComputedStyle(el('micro-continu'));
      attendre(s.backgroundColor === 'rgba(0, 0, 0, 0)' && s.borderTopStyle === 'none' && s.boxShadow === 'none', '« continu » a un cadre ou un fond au repos');
      attendre(touchable(ui, el('micro-continu')), '« continu » pas touchable');
      attendre(el('micro-continu').querySelector('path[d="M20 11a8 8 0 1 0-2.6 5.9"]'), 'icône de Zencoder absente');
      attendreEgal([el('micro-continu').getAttribute('aria-pressed'), el('micro-continu').getAttribute('aria-label')], ['false', 'Conversation continue'], 'état au repos');
    });
  }

  await testRemplace('Bouton « continu » (08/11/2026) : un toucher lance la conversation (micro « live », sans bandeau depuis le 08/11/2026), état actif TRÈS visible ; un 2e toucher l’arrête ; sans dictée : message clair, rien d’actif', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    ui.cadre.contentWindow.matchMedia = q => ({ matches: /reduce/.test(q), addEventListener() {}, removeEventListener() {} });
    brancherAccueil(c, ui);
    const el = id => ui.parId(id);
    await ouvrirEcranMicro(ui);
    el('micro-continu').click();
    attendre(/dictée n'est pas disponible/.test(el('statut').textContent) && el('micro-continu').getAttribute('aria-pressed') === 'false' && el('bandeau-live').hidden, 'sans dictée : état faux');
    dicteeDisponible(ui);
    el('micro-continu').click();
    attendre(el('microphone').classList.contains('live') && el('bandeau-live').hidden, 'conversation pas lancée, ou bandeau affiché (retiré le 08/11/2026)');
    attendreEgal([el('micro-continu').getAttribute('aria-pressed'), el('micro-continu').getAttribute('aria-label')], ['true', 'Arrêter la conversation continue'], 'état actif');
    const s = ui.cadre.contentWindow.getComputedStyle(el('micro-continu'));
    attendre(s.backgroundColor === 'rgba(222, 242, 236, 0.95)' && s.color === 'rgb(22, 32, 29)' && s.boxShadow !== 'none', `état actif pas très visible : ${s.backgroundColor} ${s.color}`);
    el('micro-continu').click();
    attendre(el('bandeau-live').hidden && !el('microphone').classList.contains('live') && el('micro-continu').getAttribute('aria-pressed') === 'false', 'conversation pas arrêtée');
    attendre(/Mode conversation arrêté/.test(el('statut').textContent), 'arrêt pas annoncé');
  });

  await testRemplace('Bouton « continu » (08/11/2026) : l’appui long du micro ne lance plus la conversation ; un appui court dicte toujours', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    brancherAccueil(c, ui);
    const el = id => ui.parId(id);
    await ouvrirEcranMicro(ui);
    let dictees = 0;
    Object.assign(ui.dictee, { disponible: () => true, enCours: () => false, arreter() {}, demarrer() { dictees++; } });
    const avantDelais = c.delais.size;
    el('microphone').dispatchEvent(new Event('pointerdown'));
    // 08/11/2026 : minuteries simulées : l'appui long ne doit même pas prévoir de minuterie de 2 s.
    attendre(![...c.delais.values()].some(d => d.delai === 2000) || c.delais.size === avantDelais, 'l’appui long prévoit encore la conversation');
    await attendreMsT(2200);
    el('microphone').dispatchEvent(new Event('pointerup'));
    attendre(el('bandeau-live').hidden && !el('microphone').classList.contains('live') && dictees === 0, 'l’appui long lance encore la conversation');
    parlerAuGrosMicro(el('microphone')); // 09/11/2026 : deux touchers
    attendreEgal(dictees, 1, 'l’appui court ne dicte plus');
  });

  await testRemplace('Bouton « continu » (08/11/2026) : fermer l’écran Micro par le geste n’arrête PAS la conversation ; en revenant, « continu » est toujours actif', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    brancherAccueil(c, ui);
    const temps = { t: 0 };
    brancherGesteRetour(c, ui, temps);
    const el = id => ui.parId(id);
    dicteeDisponible(ui);
    await ouvrirEcranMicro(ui);
    el('micro-continu').click();
    glisserRetour(ui, temps, el('ecran-micro'), NET);
    await attendreQue(() => el('ecran-micro').hidden, 'geste sans effet');
    attendre(el('microphone').classList.contains('live') && el('micro-continu').getAttribute('aria-pressed') === 'true', 'conversation arrêtée en fermant l’écran');
    await finTransition(ui);
    await ouvrirEcranMicro(ui);
    attendreEgal(el('micro-continu').getAttribute('aria-pressed'), 'true', '« continu » pas actif au retour');
    el('arreter-live').click();
    attendreEgal(el('micro-continu').getAttribute('aria-pressed'), 'false', '« Arrêter » ne remet pas « continu » au repos');
  });

  // ----- 08/11/2026 : halo du micro de l'accueil et bandeau « Arrêter » retiré (décision de Max) -----
  await testRemplace('Halo (08/11/2026) : pendant la conversation, le micro de l’accueil porte un léger halo FIXE (sans clignoter), aucun bandeau ; le toucher rouvre l’écran Micro où « continu » arrête ; halo enlevé à l’arrêt', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    ui.cadre.contentWindow.matchMedia = q => ({ matches: /reduce/.test(q), addEventListener() {}, removeEventListener() {} });
    brancherAccueil(c, ui);
    const temps = { t: 0 };
    brancherGesteRetour(c, ui, temps);
    const el = id => ui.parId(id);
    dicteeDisponible(ui);
    const vue = ui.cadre.contentWindow;
    attendre(vue.getComputedStyle(el('ouvrir-micro')).boxShadow === 'none' && !el('ouvrir-micro').classList.contains('conversation-en-cours'), 'halo au repos');
    el('ouvrir-micro').click();
    el('micro-continu').click();
    attendre(el('bandeau-live').hidden, 'bandeau « Arrêter » affiché');
    glisserRetour(ui, temps, el('ecran-micro'), NET);
    attendre(el('ecran-micro').hidden && touchable(ui, el('ouvrir-micro')), 'retour à l’accueil manqué');
    const s = vue.getComputedStyle(el('ouvrir-micro'));
    attendre(el('ouvrir-micro').classList.contains('conversation-en-cours') && s.boxShadow !== 'none' && s.animationName === 'none', `pas de halo fixe : ${s.boxShadow} / ${s.animationName}`);
    attendreEgal(el('ouvrir-micro').getAttribute('aria-label'), 'Micro (conversation en cours)', 'nom pour le lecteur d’écran');
    attendre(el('bandeau-live').hidden, 'bandeau affiché sur l’accueil');
    el('ouvrir-micro').click();
    attendre(!el('ecran-micro').hidden && el('micro-continu').getAttribute('aria-pressed') === 'true', '« continu » pas allumé au retour');
    el('micro-continu').click();
    attendre(!el('microphone').classList.contains('live') && !el('ouvrir-micro').classList.contains('conversation-en-cours') && el('ouvrir-micro').getAttribute('aria-label') === 'Micro', 'halo pas enlevé à l’arrêt');
    attendre(/décision de Max\) : bandeau « Arrêter » retiré/.test(SOURCE_APP) && /const BANDEAU_LIVE = false;/.test(SOURCE_APP), 'code du bandeau pas gardé désactivé avec commentaire daté');
  });

  // ----- 08/11/2026 : commandes vocales, ÉTAPE 0 du codage (socle), FAUX tableur FICTIF uniquement -----
  // Faux tableur : mêmes colonnes que le vrai (A Commande, B Intention, C Bloc, D Formulation, E Code, F Remarque).
  const TABLEUR_FICTIF_0 = [
    ['Commande', 'Intention', 'Bloc', 'Formulation', 'Code commande', 'Remarque (Claude, datée)'],
    ['Navigation', '', 'Verbe d’ouverture', 'ouvre', 'COMMUN', ''],
    ['Ouvrir Autre', '', 'Mot-clé', 'autre', 'NAV-02', ''],
    ['Navigation', '', 'Écran cible', 'l’écran autre', 'NAV-02', ''], // relie NAV-02 aux verbes COMMUNS « Navigation » (comme le vrai tableur)
    ['Fermer', '', 'Verbe de fermeture', 'ferme', 'NAV-09', ''],
    ['Fermer', '', 'Mot-clé', 'ça', 'NAV-09', ''],
    ['Dictée', '', 'Verbe d’arrêt', 'stop', 'DIC-02', ''],
    ['Dictée', '', 'Verbe d’arrêt', 'arrête', 'DIC-02', ''],
    ['Arrêter la musique', '', 'Verbe d’arrêt de la musique', 'arrête', 'MUS-07', 'RETIRER 08/11/2026 : seul = dictée'],
    ['Arrêter la musique', '', 'Expression complète', 'arrête la musique', 'MUS-07', ''],
    ['Pause', '', 'Verbe de pause', 'mets en pause', 'MUS-05', ''],
    ['Pause', '', 'Verbe de pause', 'pause', 'MUS-05', ''],
    ['Pause', '', 'Mot-clé', 'la musique', 'MUS-05', ''],
    ['Pause', '', 'Expression de pause', 'j’ai un appel', 'MUS-05', ''],
    ['Volume chiffré', '', 'Expression complète', 'mets le volume à [NOMBRE]', 'MUS-21', ''],
    ['Position', '', 'Expression complète', 'avance de [DURÉE]', 'MUS-23', ''],
    ['Position', '', 'Expression complète', 'avance à [DURÉE]', 'MUS-23', ''],
    ['Lancer un morceau', '', 'Verbe de lecture MP3', 'mets-moi', 'MUS-01', ''],
    ['Lancer un morceau', '', 'Cible de titre', '[TITRE]', 'MUS-01', ''],
    ['Lancer un morceau', '', 'Cible de personne', 'un morceau de [PRÉNOM]', 'MUS-01', ''],
    ['Lancer un morceau', '', 'Cible de personne', 'un morceau de Zorglub', 'MUS-01', ''], // majuscule hors crochets : écartée
    ['Morceau suivant', '', 'Verbe de passage au suivant', 'passe au', 'MUS-12', ''],
    ['Morceau suivant', '', 'Mot-clé', 'suivant', 'MUS-12', ''],
    ['Document suivant', '', 'Verbe de passage au suivant', 'passe au', 'VIS-04', ''],
    ['Document suivant', '', 'Mot-clé', 'suivant', 'VIS-04', ''],
    ['Ouvrir la visionneuse', '', 'Expression complète', 'ouvre l’œil', 'VIS-01', ''],
    ['Recherche par contenu', '', 'Expression complète', 'trouve le document qui parle de [SUJET]', 'DOC-03', ''],
    ['Appel', '', 'Verbe d’appel', 'appelle', 'TEL-01', ''],
    ['Appel', '', 'Cible', 'Prénom Réel FICTIF', 'TEL-01', ''], // bloc « Cible » : jamais copié
    ['Appel', '', 'Mot-clé', 'ma sœur', 'TEL-01', '']
  ];
  const analyseFictive0 = () => commandesVocales.analyser(TABLEUR_FICTIF_0);

  test('Commandes vocales, étape 0 (08/11/2026, FAUX tableur FICTIF) : copie sans « RETIRER », sans bloc « Cible », sans majuscule hors crochets dans les « Cible de … » ; blocs « Expression » et espaces réservés gardés', () => {
    const { lignes, compte } = analyseFictive0();
    attendre(!lignes.some(l => /Zorglub|Prénom Réel/.test(l.formulation)), 'un nom a été copié');
    attendreEgal([compte.retirees, compte.noms_exclus], [1, 2], 'comptes écartés');
    attendre(lignes.some(l => l.formulation === '[TITRE]') && lignes.some(l => l.formulation === 'un morceau de [PRÉNOM]'), 'cibles à espaces réservés perdues');
    attendre(lignes.some(l => l.bloc === 'Expression complète'), 'expressions perdues');
  });

  test('Commandes vocales, étape 0 (08/11/2026, FICTIF) : expression complète seule ; « œ » = « oe » ; verbe seul pour la pause ; « arrête » seul = dictée, « arrête la musique » = musique', () => {
    const { lignes } = analyseFictive0();
    const code = (phrase, ctx) => { const r = commandesVocales.reconnaitre(phrase, lignes, ctx); return r.statut === 'reconnu' ? r.code : r.statut; };
    attendreEgal([code('Ouvre l’œil'), code('ouvre l oeil')], ['VIS-01', 'VIS-01'], 'œ / oe');
    attendreEgal([code('pause'), code('mets en pause'), code('J’ai un appel !')], ['MUS-05', 'MUS-05', 'MUS-05'], 'pause');
    attendreEgal([code('arrête'), code('stop'), code('arrête la musique')], ['DIC-02', 'DIC-02', 'MUS-07'], 'arrête');
    attendreEgal(code('ouvre autre'), 'NAV-02', 'navigation');
  });

  test('Commandes vocales, étape 0 (08/11/2026, FICTIF) : [NOMBRE] en chiffres ou en lettres, « pour cent », hésitations (dernier chiffre) ; [DURÉE] relative ou précise ; [SUJET], [TITRE], [PRÉNOM]', () => {
    const { lignes } = analyseFictive0();
    const r = phrase => commandesVocales.reconnaitre(phrase, lignes);
    attendreEgal(r('mets le volume à 75').valeurs, { nombre: 75 }, '75');
    attendreEgal(r('Mets le, mets le volume à, à 75').valeurs, { nombre: 75 }, 'hésitation de Max');
    attendreEgal(r('euh mets le volume à soixante quinze pour cent').valeurs, { nombre: 75 }, 'en lettres');
    attendreEgal(r('mets le volume à 25 euh non mets le volume à 10').valeurs, { nombre: 10 }, 'dernier chiffre dit');
    attendreEgal([commandesVocales.lireNombre('quatre vingt dix'), commandesVocales.lireNombre('cent'), commandesVocales.lireNombre('150')], [90, 100, null], 'nombres');
    attendreEgal(r('mets le volume à 150').statut, 'rien', 'hors 0 à 100');
    attendreEgal([r('avance de 10 secondes').valeurs, r('avance à 2 minutes 40').valeurs], [{ duree: 10 }, { duree: 160 }], 'durées');
    attendreEgal(r('avance de 10 secondes').mots, ['avance de'], 'relatif : le mot « de » est gardé');
    attendreEgal(r('trouve le document qui parle de impôts FICTIF').valeurs, { sujet: 'impots fictif' }, 'sujet');
    const morceau = r('mets-moi un morceau de Toto FICTIF');
    attendre(morceau.statut === 'reconnu' && morceau.code === 'MUS-01' && morceau.valeurs.prenom === 'toto fictif', `prénom : ${JSON.stringify(morceau)}`);
  });

  test('Commandes vocales, étape 0 (08/11/2026, FICTIF) : « passe au suivant » : la fenêtre ouverte décide (lecteur → morceau, visionneuse → document), sinon égalité signalée', () => {
    const { lignes } = analyseFictive0();
    const r = (ouvert) => commandesVocales.reconnaitre('passe au suivant', lignes, { ouvert });
    attendreEgal([r('lecteur').code, r('visionneuse').code, r('').statut], ['MUS-12', 'VIS-04', 'ambigu'], 'contexte');
  });

  test('Commandes vocales, étape 0 (08/11/2026, FICTIF) : micro du milieu : commande → traitée ici (pas encore branchée : dit honnêtement) ; phrase incomplète → « Je ne suis pas une IA… » ; sinon chemin d’avant (À trier) ; appel → chemin d’avant', () => {
    const { lignes } = analyseFictive0();
    const d = (phrase, contexte = {}) => commandesVocales.deciderMicro(phrase, { lignes, contexte });
    attendreEgal(d('ouvre autre'), { statut: 'pas_encore', code: 'NAV-02', message: 'J’ai compris « Ouvrir Autre », mais je ne sais pas encore le faire.' }, 'commande');
    // 08/11/2026 (correction A) : « ferme » n'est plus « incomplet » (il ferme) ; avant : ['ouvre', 'Ouvre-moi', 'ferme', 'mets-moi s’il te plaît'].
    for (const phrase of ['ouvre', 'Ouvre-moi', 'mets-moi s’il te plaît']) attendreEgal(d(phrase), { statut: 'incomplet', message: 'Je ne suis pas une IA, dis-moi ce que tu veux.' }, `incomplet : ${phrase}`);
    for (const phrase of ['mets du sel FICTIF dans la soupe', 'acheter du pain FICTIF', 'appelle ma sœur', 'appelle']) attendreEgal(d(phrase), null, `chemin d’avant : ${phrase}`);
    attendreEgal(commandesVocales.deciderMicro('ouvre autre', { lignes: [] }), null, 'sans tableur : chemin d’avant');
    attendre(d('passe au suivant').statut === 'ambigu' && /J’hésite/.test(d('passe au suivant').message), 'égalité');
  });

  test('Commandes vocales, étape 0 (08/11/2026, FICTIF) : une action branchée est appelée avec la reconnaissance et la fenêtre ouverte ; son message est rendu', () => {
    const { lignes } = analyseFictive0();
    const appels = [];
    commandesVocales.brancherAction('MUS-21', (r, contexte) => { appels.push([r.valeurs.nombre, contexte.ouvert]); return `Volume FICTIF à ${r.valeurs.nombre}.`; });
    try {
      attendreEgal(commandesVocales.deciderMicro('mets le volume à 40', { lignes, contexte: { ouvert: 'lecteur' } }), { statut: 'fait', code: 'MUS-21', message: 'Volume FICTIF à 40.' }, 'action');
      attendreEgal(appels, [[40, 'lecteur']], 'appel');
    } finally { commandesVocales.brancherAction('MUS-21', undefined); }
  });

  test('Commandes vocales, étape 0 (08/11/2026) : rapide sur un gros faux tableur (13 000 lignes FICTIF) : moins de 300 ms par phrase', () => {
    const gros = [TABLEUR_FICTIF_0[0]];
    for (let i = 0; i < 13000; i++) gros.push([`Commande FICTIF ${i % 40}`, '', i % 3 ? 'Mot-clé' : 'Verbe FICTIF', `mot${i} fictif${i % 97}`, `MUS-${String(30 + (i % 40)).padStart(2, '0')}`, '']);
    for (const l of TABLEUR_FICTIF_0.slice(1)) gros.push(l);
    const { lignes } = commandesVocales.analyser(gros);
    commandesVocales.reconnaitre('ouvre autre', lignes); // préparation (une fois)
    const debut = performance.now();
    const r = commandesVocales.reconnaitre('mets le volume à 30', lignes);
    const duree = performance.now() - debut;
    attendre(r.code === 'MUS-21' && duree < 300, `trop lent ou faux : ${Math.round(duree)} ms, ${JSON.stringify(r)}`);
  });

  await testAsync('Commandes vocales, étape 0 (08/11/2026, FICTIF) : dans Cap, le micro du milieu : « ouvre autre » → aucune tâche, réponse honnête ; « ouvre » → « Je ne suis pas une IA… » ; « acheter du pain FICTIF » → tâche « À trier » ; le clavier garde le chemin d’avant', async c => {
    const cle = commandesVocales.CLE_COPIE;
    const avantCopie = localStorage.getItem(cle);
    localStorage.setItem(cle, JSON.stringify({ lu_le: new Date(0).toISOString(), compte: {}, lignes: analyseFictive0().lignes }));
    try {
      const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
      brancherAccueil(c, ui);
      const el = id => ui.parId(id);
      const dicter = phrase => {
        Object.assign(ui.dictee, { disponible: () => true, enCours: () => false, arreter() {}, demarrer(r) { r.surFinal(phrase); if (r.surFin) r.surFin(); } });
        parlerAuGrosMicro(el('microphone')); // 09/11/2026 : deux touchers
      };
      const nombre = TACHES.length; // les tâches de Cap sont dans TACHES (comme les autres tests de dictée)
      dicter('ouvre autre');
      attendreEgal(el('statut').textContent, 'J’ai compris « Ouvrir Autre », mais je ne sais pas encore le faire.', 'réponse');
      dicter('Ouvre');
      attendreEgal(el('statut').textContent, 'Je ne suis pas une IA, dis-moi ce que tu veux.', 'incomplet');
      attendreEgal(TACHES.length, nombre, 'une tâche a été créée pour une commande');
      dicter('acheter du pain FICTIF');
      const nouvelle = TACHES.slice(nombre);
      attendre(nouvelle.length === 1 && nouvelle[0].intitule === 'acheter du pain FICTIF' && nouvelle[0].categorie === 'À trier', `pas rangé dans À trier : ${JSON.stringify(nouvelle.map(x => [x.intitule, x.categorie]))}`);
      // Clavier (choix B) : « ouvre » ne reçoit pas la réponse des commandes.
      el('ouvrir-clavier').click();
      el('saisie-demande').value = 'ouvre';
      el('formulaire-demande').requestSubmit();
      attendre(el('statut').textContent !== commandesVocales.PAS_UNE_IA, 'le clavier répond comme le micro des commandes');
      TACHES.slice(nombre).forEach(tache => abandonner(tache.id));
    } finally {
      if (avantCopie === null) localStorage.removeItem(cle); else localStorage.setItem(cle, avantCopie);
    }
  });

  // ----- 08/11/2026 : commandes vocales, ÉTAPE 1 (navigation et dictée), FAUX tableur FICTIF -----
  const TABLEUR_FICTIF_1 = [
    ...TABLEUR_FICTIF_0,
    ['Navigation', '', 'Écran cible', 'chercher', 'NAV-01', ''],
    ['Navigation', '', 'Écran cible', 'les réglages', 'NAV-03', ''],
    ['Navigation', '', 'Écran cible', 'le scanner', 'NAV-04', ''],
    ['Navigation', '', 'Écran cible', 'l’agenda', 'NAV-05', ''],
    ['Navigation', '', 'Écran cible', 'les notes', 'NAV-06', ''],
    ['Revenir à l’accueil', '', 'Verbe de retour', 'reviens à', 'NAV-07', ''],
    ['Revenir à l’accueil', '', 'Mot-clé', 'l’accueil', 'NAV-07', ''],
    ['Revenir à l’eau', '', 'Verbe de retour', 'remets-moi', 'NAV-08', ''],
    ['Revenir à l’eau', '', 'Mot-clé', 'l’eau seule', 'NAV-08', ''],
    ['Passer en mode sombre', '', 'Verbe', 'passe en', 'NAV-10', ''],
    ['Passer en mode sombre', '', 'Mot-clé', 'mode sombre', 'NAV-10', ''],
    ['Passer en mode clair', '', 'Verbe', 'passe en', 'NAV-11', ''],
    ['Passer en mode clair', '', 'Mot-clé', 'mode clair', 'NAV-11', ''],
    ['Navigation', '', 'Écran cible', 'mes tâches', 'NAV-13', ''],
    ['Navigation', '', 'Écran cible', 'l’aide', 'NAV-21', ''],
    ['Navigation', '', 'Écran cible', 'le micro', 'NAV-22', ''],
    ['Quitter l’application', '', 'Verbe de fermeture de l’application', 'quitte', 'NAV-24', ''],
    ['Quitter l’application', '', 'Mot-clé', 'cap fictif', 'NAV-24', ''],
    ['Dictée', '', 'Expression complète', 'lance la dictée', 'DIC-01', '']
  ];
  async function interfaceCommandes1(c, essai, { reduit = false } = {}) {
    const cle = commandesVocales.CLE_COPIE;
    const avantCopie = localStorage.getItem(cle);
    localStorage.setItem(cle, JSON.stringify({ lu_le: new Date(0).toISOString(), compte: {}, lignes: commandesVocales.analyser(TABLEUR_FICTIF_1).lignes }));
    const nombre = TACHES.length;
    try {
      const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
      if (reduit) ui.cadre.contentWindow.matchMedia = q => ({ matches: /reduce/.test(q), addEventListener() {}, removeEventListener() {} });
      brancherAccueil(c, ui);
      const temps = { t: 0 };
      const g = brancherGesteRetour(c, ui, temps);
      commandesNavigation.brancher(ui.doc, { geste: () => g });
      const el = id => ui.parId(id);
      const dicter = phrase => {
        Object.assign(ui.dictee, { disponible: () => true, enCours: () => false, arreter() {}, demarrer(r) { r.surFinal(phrase); if (r.surFin) r.surFin(); } });
        parlerAuGrosMicro(el('microphone')); // 09/11/2026 : deux touchers
        return el('statut').textContent;
      };
      await essai({ ui, el, dicter });
      attendreEgal(TACHES.length, nombre, 'une commande a créé une tâche');
    } finally {
      TACHES.slice(nombre).forEach(tache => abandonner(tache.id));
      if (avantCopie === null) localStorage.removeItem(cle); else localStorage.setItem(cle, avantCopie);
      for (const code of Object.keys(commandesNavigation.PAS_PRET).concat(['NAV-01', 'NAV-02', 'NAV-03', 'NAV-04', 'NAV-07', 'NAV-08', 'NAV-09', 'NAV-10', 'NAV-11', 'NAV-13', 'NAV-21', 'NAV-22', 'NAV-24'])) commandesVocales.brancherAction(code, undefined);
    }
  }

  await testAsync('Commandes vocales, étape 1 (08/11/2026, FICTIF) : depuis l’écran Micro, « ouvre autre », « ouvre les réglages », « reviens à l’accueil » : le même écran que le doigt, en douceur, sans tâche créée', async c => {
    await interfaceCommandes1(c, async ({ ui, el, dicter }) => {
      // 09/11/2026 : plus d'écran Micro (avant : el('ouvrir-micro').click()).
      await finTransition(ui);
      attendreEgal(dicter('ouvre autre'), 'J’ouvre Autre.', 'réponse');
      attendre(!el('ecran-autre').hidden && el('ecran-micro').hidden && el('ecran-autre').classList.contains('ecran-entree'), 'Autre pas ouvert en douceur');
      await finTransition(ui);
      attendreEgal(dicter('ouvre les réglages'), 'J’ouvre Réglages.', 'réponse');
      attendre(!el('ecran-reglages').hidden && el('ecran-autre').hidden, 'Réglages pas ouvert');
      await finTransition(ui);
      attendreEgal(dicter('reviens à l’accueil'), 'Retour à l’accueil.', 'réponse');
      await finTransition(ui);
      attendre(el('ecran-reglages').hidden && !ui.doc.documentElement.classList.contains('ecran-cap-ouvert') && touchable(ui, el('microphone')), 'accueil pas revenu'); // 09/11/2026 : le gros micro (avant : ouvrir-micro)
    });
  });

  await testAsync('Commandes vocales, étape 1 (08/11/2026, FICTIF) : « ouvre chercher » et « mes tâches » ouvrent « Tout voir » (l’écran Micro se ferme d’abord) ; « ferme ça » referme', async c => {
    await interfaceCommandes1(c, async ({ ui, el, dicter }) => {
      // 09/11/2026 : plus d'écran Micro (avant : el('ouvrir-micro').click()).
      await finTransition(ui);
      // 09/11/2026 : « ouvre chercher » = l'écran Chercher (4 icônes, barre) ; « ferme ça » le referme (sortie douce) ;
      // « mes tâches » = To-do, l'écran des tâches. Avant : « ouvre chercher » ouvrait directement « Tout voir ».
      attendreEgal(dicter('ouvre chercher'), 'J’ouvre Chercher.', 'réponse');
      attendre(!el('ecran-chercher').hidden && el('ecran-micro').hidden && el('ecran-complet').hidden, 'Chercher pas ouvert proprement');
      await finTransition(ui);
      attendreEgal(dicter('ouvre chercher'), 'Chercher est déjà ouvert.', 'déjà ouvert');
      attendreEgal(dicter('ferme ça'), 'Je ferme.', 'fermer Chercher');
      await attendreQue(() => el('ecran-chercher').hidden, 'Chercher pas fermé');
      await finTransition(ui);
      attendreEgal(dicter('ouvre mes tâches'), 'J’ouvre tes tâches.', 'mes tâches');
      attendre(!el('ecran-complet').hidden, 'tâches pas ouvertes');
      await finTransition(ui);
    });
  });

  await testAsync('Commandes vocales, étape 1 (08/11/2026, FICTIF) : « ferme ça » sur l’écran Micro : même sortie douce que le geste de retour, puis l’accueil ; rien à fermer : dit', async c => {
    await interfaceCommandes1(c, async ({ ui, el, dicter }) => {
      // 09/11/2026 : plus d'écran Micro : « ferme ça » sur l'écran Chercher. Avant : écran Micro.
      el('ouvrir-chercher').click();
      await finTransition(ui);
      attendreEgal(dicter('ferme ça'), 'Je ferme.', 'réponse');
      attendre(el('ecran-chercher').classList.contains('geste-retour-sortie'), 'pas de sortie douce');
      await attendreQue(() => el('ecran-chercher').hidden, 'écran Chercher pas fermé');
      await finTransition(ui);
      attendreEgal(dicter('ferme ça'), 'Il n’y a rien à fermer.', 'rien à fermer');
    });
  });

  await testAsync('Commandes vocales, étape 1 (08/11/2026, FICTIF) : « passe en mode clair / sombre » : l’interrupteur lune / soleil ; déjà fait : dit', async c => {
    await interfaceCommandes1(c, async ({ el, dicter }) => {
      const sombre = () => el('bouton-theme-cap').getAttribute('aria-checked') === 'true';
      if (!sombre()) el('bouton-theme-cap').click();
      attendreEgal(dicter('passe en mode clair'), 'Mode clair.', 'clair');
      attendre(!sombre(), 'pas passé en clair');
      attendreEgal(dicter('passe en mode clair'), 'C’est déjà le mode clair.', 'déjà clair');
      attendreEgal(dicter('passe en mode sombre'), 'Mode sombre.', 'sombre');
      attendre(sombre(), 'pas passé en sombre');
    });
  });

  await testAsync('Commandes vocales, étape 1 (08/11/2026, FICTIF) : agenda, notes : « pas encore prêt » ; scanner, aide, eau seule : le même bouton que le doigt ; quitter Cap : réponse franche', async c => {
    await interfaceCommandes1(c, async ({ ui, el, dicter }) => {
      attendreEgal(dicter('ouvre l’agenda'), 'Agenda : pas encore prêt.', 'agenda');
      attendreEgal(dicter('ouvre les notes'), 'Notes : pas encore prêt.', 'notes');
      let scanner = 0, eau = 0;
      el('ouvrir-scanner').addEventListener('click', () => { scanner++; });
      el('aller-eau').addEventListener('click', () => { eau++; });
      attendreEgal(dicter('ouvre le scanner'), 'J’ouvre le scanner.', 'scanner');
      attendreEgal(scanner, 1, 'bouton du scanner pas touché');
      if (el('scanner').open) el('scanner').close();
      attendreEgal(dicter('ouvre l’aide'), 'J’ouvre l’aide.', 'aide');
      attendre(el('aide').open, 'aide pas ouverte');
      el('aide').close();
      attendreEgal(dicter('remets-moi l’eau seule'), 'Retour à l’eau.', 'eau');
      attendreEgal(eau, 1, 'bouton de l’eau pas touché');
      attendreEgal(dicter('quitte cap fictif'), 'Je ne peux pas fermer Cap moi-même : utilise le bouton des applications d’Android.', 'quitter');
      attendreEgal(dicter('ouvre le micro'), 'Voici le micro.', 'micro');
      // 09/11/2026 : plus d'écran Micro : « + » et la nouvelle icône apparaissent autour du gros micro, sans écouter.
      // Avant : attendre(!el('ecran-micro').hidden, 'écran Micro pas ouvert');
      attendre(el('ecran-micro').hidden && !el('micro-ajouter').hidden && !el('micro-ecrire').hidden && el('microphone').getAttribute('aria-pressed') === 'false', '« + » et l’icône pas montrés (ou écoute lancée)');
      await finTransition(ui);
    });
  });

  await testAsync('Commandes vocales, étape 1 (08/11/2026, FICTIF) : dictée : « stop » / « arrête » → « Dictée arrêtée. » (conversation arrêtée aussi) ; « lance la dictée » → Cap réécoute, sans parler', async c => {
    await interfaceCommandes1(c, async ({ ui, el, dicter }) => {
      attendreEgal(dicter('stop'), 'Dictée arrêtée.', 'stop');
      attendreEgal(dicter('arrête'), 'Dictée arrêtée.', 'arrête');
      let ecoutes = 0;
      const paroles = [];
      Object.assign(ui.dictee, { disponible: () => true, enCours: () => false, arreter() {}, demarrer(r) { ecoutes++; if (ecoutes === 1) { r.surFinal('lance la dictée'); if (r.surFin) r.surFin(); } } });
      const voixAvant = ui.cadre.contentWindow.speechSynthesis;
      parlerAuGrosMicro(el('microphone')); // 09/11/2026 : deux touchers
      attendreEgal(el('statut').textContent, 'Je t’écoute.', 'réponse');
      // Minuteries simulées dans les tests : on déclenche la relance de 400 ms.
      const relance = [...c.delais.entries()].find(([, d]) => d.delai === 400);
      attendre(relance, 'pas de relance prévue');
      c.delais.delete(relance[0]);
      relance[1].rappel();
      attendreEgal(ecoutes, 2, 'Cap ne réécoute pas');
      // Conversation continue en cours : « stop » au micro du milieu l'arrête aussi.
      Object.assign(ui.dictee, { demarrer() {} });
      el('micro-continu').click();
      attendre(el('microphone').classList.contains('live'), 'conversation pas lancée');
      attendreEgal(commandesVocales.deciderMicro('stop', { lignes: commandesVocales.analyser(TABLEUR_FICTIF_1).lignes }).message, 'Dictée arrêtée.', 'réponse pendant la conversation');
      attendre(!el('microphone').classList.contains('live'), 'conversation pas arrêtée');
      void voixAvant; void paroles;
    });
  });

  test('Commandes vocales, étape 1 (08/11/2026) : chaque code de navigation et de dictée du plan a son action (NAV-01 à NAV-24, DIC-01, DIC-02)', () => {
    const ui = { doc: document };
    const avant = new Map();
    const codes = Array.from({ length: 24 }, (_, i) => `NAV-${String(i + 1).padStart(2, '0')}`).concat(['DIC-01', 'DIC-02']);
    for (const code of codes) avant.set(code, commandesVocales.actionBranchee(code));
    const m = commandesNavigation.brancher(document, { geste: () => null });
    try {
      const manquants = codes.filter(code => !commandesVocales.actionBranchee(code));
      attendreEgal(manquants, [], 'codes sans action');
      void ui; void m;
    } finally {
      for (const code of codes) if (code.startsWith('NAV') && !avant.get(code)) commandesVocales.brancherAction(code, undefined);
    }
  });

  // ----- 08/11/2026 : corrections A, B, C, D (accord de Max), FAUX tableur FICTIF -----
  const TABLEUR_FICTIF_ABC = [
    TABLEUR_FICTIF_0[0],
    ['Fermer', '', 'Verbe de fermeture', 'ferme', 'NAV-09', ''],
    ['Fermer', '', 'Verbe de fermeture', 'referme', 'NAV-09', ''],
    ['Fermer', '', 'Tournure de besoin', 'je veux que tu fermes', 'NAV-09', ''],
    ['Fermer', '', 'Mot-clé', 'ça', 'NAV-09', ''],
    ['Fermer', '', 'Mot-clé', 'cet écran', 'NAV-09', ''],
    ['Fermer', '', 'Variante de transcription', 'fermer', 'NAV-09', ''],
    ['Fermer', '', 'Variante de transcription', 'ca', 'NAV-09', ''],
    ['Revenir à l’eau', '', 'Verbe de retour', 'remets-moi', 'NAV-08', ''],
    ['Revenir à l’eau', '', 'Verbe de retour', 'fais-moi voir', 'NAV-08', ''],
    ['Revenir à l’eau', '', 'Tournure de besoin', 'je veux voir', 'NAV-08', ''],
    ['Revenir à l’eau', '', 'Tournure de besoin', 'je ne veux plus voir', 'NAV-08', ''],
    ['Revenir à l’eau', '', 'Mot-clé', 'l’eau', 'NAV-08', ''],
    ['Revenir à l’eau', '', 'Mot-clé', 'que l’eau', 'NAV-08', ''],
    ['Revenir à l’eau', '', 'Mot-clé', 'les boutons', 'NAV-08', ''],
    ['Pause', '', 'Verbe de pause', 'pause', 'MUS-05', ''],
    ['Pause', '', 'Mot-clé', 'la musique', 'MUS-05', ''],
    ['Reprendre', '', 'Verbe de reprise', 'reprends', 'MUS-06', ''],
    ['Reprendre', '', 'Mot-clé', 'la musique', 'MUS-06', ''],
    ['Navigation', '', 'Verbe d’ouverture', 'ouvre', 'COMMUN', ''],
    ['Navigation', '', 'Écran cible', 'autre', 'NAV-02', ''],
    ['Navigation', '', 'Variante de transcription', 'ouvre notre', 'NAV-02', '']
  ];
  const codeABC = phrase => {
    const r = commandesVocales.reconnaitre(phrase, commandesVocales.analyser(TABLEUR_FICTIF_ABC).lignes);
    return r.statut === 'reconnu' ? r.code : r.statut;
  };

  test('Correction A (08/11/2026, FICTIF) : « ferme », « ferme-le », « referme s’il te plaît », « je veux que tu fermes » ferment ; « rappelle-moi de fermer le gaz » et « je ferme la porte du garage » restent des tâches ; « ça » seul ne ferme rien', () => {
    for (const phrase of ['ferme', 'Ferme-le !', 'referme s’il te plaît', 'je veux que tu fermes', 'ferme ça', 'ferme cet écran', 'fermer']) attendreEgal(codeABC(phrase), 'NAV-09', phrase);
    for (const phrase of ['rappelle-moi de fermer le gaz FICTIF', 'je ferme la porte du garage FICTIF', 'ça']) attendreEgal(codeABC(phrase), 'rien', phrase);
  });

  test('Correction A (08/11/2026, FICTIF) : même prudence pour la pause et la reprise : « pause », « reprends » seuls marchent ; « fais une pause café FICTIF » reste une tâche ; « mets la musique en pause » marche (verbe + mot-clé)', () => {
    attendreEgal([codeABC('pause'), codeABC('Pause !'), codeABC('reprends'), codeABC('reprends s’il te plaît')], ['MUS-05', 'MUS-05', 'MUS-06', 'MUS-06'], 'verbe seul');
    attendreEgal([codeABC('fais une pause café FICTIF'), codeABC('je reprends le travail FICTIF')], ['rien', 'rien'], 'dans une phrase');
    attendreEgal(codeABC('pause la musique'), 'MUS-05', 'verbe + mot-clé');
  });

  test('Correction B (08/11/2026, FICTIF) : le petit mot devant le mot-clé est libre (« mon eau », « ton eau », « mes boutons ») ; une variante comme « ouvre notre » reste exacte', () => {
    for (const phrase of ['fais-moi voir mon eau', 'remets-moi ton eau', 'remets-moi l’eau', 'je veux voir que mon eau', 'je ne veux plus voir mes boutons']) attendreEgal(codeABC(phrase), 'NAV-08', phrase);
    attendreEgal(commandesVocales.reconnaitre('ouvre l’autre', commandesVocales.analyser(TABLEUR_FICTIF_ABC).lignes).mots, ['ouvre', 'autre'], '« notre » pas pris pour un petit mot');
  });

  test('Correction C (08/11/2026, FICTIF) : « ne » ignoré (« je ne veux voir que l’eau ») ; vraie négation (« ne ferme pas ça », « ne remets jamais l’eau ») : jamais une commande', () => {
    attendreEgal([codeABC('je ne veux voir que l’eau'), codeABC('je n’veux voir que l’eau')], ['NAV-08', 'NAV-08'], 'ne ignoré');
    attendreEgal([codeABC('ne ferme pas ça'), codeABC('ne remets jamais l’eau'), codeABC('je ne veux rien fermer')], ['rien', 'rien', 'rien'], 'négation');
  });

  await testAsync('Correction D (08/11/2026, FICTIF) : « Réglages du Drive » montre les 10 dernières phrases du micro du milieu et la réponse de Cap ; téléphone seulement ; jamais dans le code de l’IA', async c => {
    const cle = commandesVocales.CLE_COPIE;
    const avantCopie = localStorage.getItem(cle);
    const avantEntendues = localStorage.getItem(commandesVocales.CLE_ENTENDUES);
    localStorage.setItem(cle, JSON.stringify({ lu_le: new Date(0).toISOString(), compte: {}, lignes: commandesVocales.analyser(TABLEUR_FICTIF_ABC).lignes }));
    localStorage.removeItem(commandesVocales.CLE_ENTENDUES);
    const nombre = TACHES.length;
    try {
      const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
      brancherAccueil(c, ui);
      const el = id => ui.parId(id);
      const dicter = phrase => {
        Object.assign(ui.dictee, { disponible: () => true, enCours: () => false, arreter() {}, demarrer(r) { r.surFinal(phrase); if (r.surFin) r.surFin(); } });
        parlerAuGrosMicro(el('microphone')); // 09/11/2026 : deux touchers
      };
      el('ouvrir-reglages-drive').click();
      attendre(!el('vide-phrases-entendues').hidden && el('liste-phrases-entendues').children.length === 0, 'liste pas vide au départ');
      el('reglages-drive').close();
      dicter('ouvre');
      dicter('acheter du pain FICTIF');
      for (let i = 0; i < 10; i++) dicter('ouvre');
      el('ouvrir-reglages-drive').click();
      const lignes = [...el('liste-phrases-entendues').children].map(li => li.textContent);
      attendreEgal(lignes.length, 10, 'pas 10 lignes');
      attendre(/« ouvre » → Je ne suis pas une IA, dis-moi ce que tu veux\.$/.test(lignes[0]) && el('vide-phrases-entendues').hidden, `ligne : ${lignes[0]}`);
      attendre(!lignes.some(l => /acheter du pain/.test(l)), 'la 11e phrase la plus ancienne est encore là');
      el('reglages-drive').close();
      // Téléphone seulement : clé locale, jamais citée par le code de l'IA ni par la synchronisation.
      for (const [nom, source] of [['cerveau_claude.js', SOURCE_CERVEAU_CLAUDE_TEST], ['journal_ia.js', SOURCE_JOURNAL_IA_TEST], ['synchronisation.js', SOURCE_SYNCHRONISATION_TEST]]) {
        attendre(!/phrases_entendues|entendues\(/.test(source), `${nom} lit les phrases entendues`);
      }
    } finally {
      TACHES.slice(nombre).forEach(tache => abandonner(tache.id));
      if (avantCopie === null) localStorage.removeItem(cle); else localStorage.setItem(cle, avantCopie);
      if (avantEntendues === null) localStorage.removeItem(commandesVocales.CLE_ENTENDUES); else localStorage.setItem(commandesVocales.CLE_ENTENDUES, avantEntendues);
    }
  });

  // ----- 08/11/2026 : commandes vocales, ÉTAPE 2a (commander la musique), FAUX tableur et FAUX Drive FICTIFS -----
  const TABLEUR_FICTIF_2A = [
    TABLEUR_FICTIF_0[0],
    ['Dictée', '', 'Verbe d’arrêt', 'arrête', 'DIC-02', ''],
    ['Dictée', '', 'Verbe d’arrêt', 'stop', 'DIC-02', ''],
    ['Pause', '', 'Verbe de pause', 'pause', 'MUS-05', ''],
    ['Pause', '', 'Mot-clé', 'la musique', 'MUS-05', ''],
    ['Reprendre', '', 'Verbe de reprise', 'reprends', 'MUS-06', ''],
    ['Reprendre', '', 'Mot-clé', 'la musique', 'MUS-06', ''],
    ['Arrêter la musique', '', 'Verbe d’arrêt de la musique', 'arrête', 'MUS-07', 'RETIRER 08/11/2026 : seul = dictée'],
    ['Arrêter la musique', '', 'Verbe d’arrêt de la musique', 'stop', 'MUS-07', 'RETIRER 08/11/2026 : seul = dictée'],
    ['Arrêter la musique', '', 'Expression complète', 'arrête la musique', 'MUS-07', ''],
    ['Arrêter la musique', '', 'Expression complète', 'stop le morceau', 'MUS-07', ''],
    ['Monter le volume', '', 'Verbe de hausse du volume', 'monte', 'MUS-08', ''],
    ['Monter le volume', '', 'Mot-clé', 'le son', 'MUS-08', ''],
    ['Monter le volume', '', 'Expression complète', 'mets le son à fond', 'MUS-08', ''],
    ['Baisser le volume', '', 'Verbe de baisse du volume', 'baisse', 'MUS-09', ''],
    ['Baisser le volume', '', 'Mot-clé', 'le son', 'MUS-09', ''],
    ['Couper le son', '', 'Verbe de coupure du son', 'coupe', 'MUS-10', ''],
    ['Couper le son', '', 'Mot-clé', 'le son', 'MUS-10', ''],
    ['Remettre le son', '', 'Expression complète', 'remets le son', 'MUS-11', ''],
    ['Morceau suivant', '', 'Verbe de passage au suivant', 'passe au', 'MUS-12', ''],
    ['Morceau suivant', '', 'Mot-clé', 'le suivant', 'MUS-12', ''],
    ['Morceau suivant', '', 'Mot-clé', 'morceau suivant', 'MUS-12', ''],
    ['Morceau précédent', '', 'Verbe de retour au précédent', 'reviens au', 'MUS-13', ''],
    ['Morceau précédent', '', 'Mot-clé', 'morceau précédent', 'MUS-13', ''],
    ['Rejouer', '', 'Verbe de rejeu', 'rejoue', 'MUS-14', ''],
    ['Rejouer', '', 'Mot-clé', 'le même', 'MUS-14', ''],
    ['Remettre au début', '', 'Verbe de retour au début', 'recommence', 'MUS-15', ''],
    ['Remettre au début', '', 'Verbe de retour au début', 'reviens', 'MUS-15', ''], // comme le vrai tableur : « reviens » seul ne doit PAS suffire
    ['Remettre au début', '', 'Mot-clé', 'le morceau', 'MUS-15', ''],
    ['Afficher le lecteur', '', 'Expression complète', 'montre-moi le player', 'MUS-19', ''],
    ['Volume chiffré', '', 'Expression complète', 'mets le volume à [NOMBRE]', 'MUS-21', ''],
    ['Titre du morceau', '', 'Expression complète', 'c’est quoi ce morceau', 'MUS-22', ''],
    ['Position', '', 'Expression complète', 'avance de [DURÉE]', 'MUS-23', ''],
    ['Position', '', 'Expression complète', 'recule de [DURÉE]', 'MUS-23', ''],
    ['Position', '', 'Expression complète', 'avance à [DURÉE]', 'MUS-23', ''],
    ['Document suivant', '', 'Mot-clé', 'le suivant', 'VIS-04', '']
  ];
  // Musique FICTIVE lancée puis passée en arrière-plan (la note ronde), comme le fait Max avant de parler.
  async function musiqueEnArrierePlan(c) {
    const f = fauxDriveCompteCap(c);
    remplirMusiqueFictive(f);
    const { m } = connecterCompteFictif(c);
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const el = id => ui.parId(id);
    brancherAccueil(c, ui);
    const audio = Object.assign(new EventTarget(), { paused: true, currentTime: 0, duration: 200, volume: 0.8,
      play() { this.paused = false; }, pause() { this.paused = true; } });
    const appels = [];
    const objet = { audio, jouerFichier: (adresse, titre) => { appels.push(['jouer', titre]); audio.paused = false; audio.currentTime = 0; }, arreter: () => { appels.push(['arreter']); audio.paused = true; } };
    const tele = relationsMp30().brancher(ui.doc, { compte: m, arbre: () => relationsCompte0().lireArbre(m), sorte: relationsCompte0().sorte, stockage: c.localStorage,
      lecteur: async () => objet, urls: fausseAdresses() });
    el('ouvrir-autre').click();
    el('ouvrir-lecteur').click();
    await attendreQue(() => el('liste-musique-relations').querySelectorAll('button.choix-grand-affichage').length === 2, 'dossiers');
    el('liste-musique-relations').querySelector('button').click();
    await attendreQue(() => el('liste-musique-relations').querySelectorAll('button.ligne-morceau').length === 10, 'morceaux');
    el('liste-musique-relations').querySelectorAll('button.ligne-morceau')[0].click();
    await attendreQue(() => appels.length === 1, 'morceau pas lancé');
    el('indicateur-musique').click();
    await attendreQue(() => !el('lecteur-mp3-relations').open, 'pas en arrière-plan');
    commandesMusique.brancher({ lecteur: () => tele });
    const lignes = commandesVocales.analyser(TABLEUR_FICTIF_2A).lignes;
    const dire = (phrase, contexte = { ouvert: 'lecteur' }) => { const d = commandesVocales.deciderMicro(phrase, { lignes, contexte }); return d ? d.message : null; };
    return { ui, el, audio, appels, tele, dire, lignes };
  }
  const debrancherMusique = () => { for (let i = 5; i <= 23; i++) commandesVocales.brancherAction(`MUS-${String(i).padStart(2, '0')}`, undefined); };

  await testAsync('Commandes vocales, étape 2a (08/11/2026, FICTIF) : musique en arrière-plan : « pause », « reprends », « arrête » seul = dictée (la musique continue), « arrête la musique » l’arrête', async c => {
    try {
      const { el, audio, tele, dire } = await musiqueEnArrierePlan(c);
      attendreEgal([dire('pause'), audio.paused], ['Pause.', true], 'pause');
      attendreEgal(dire('pause'), 'La musique est déjà en pause.', 'déjà en pause');
      attendreEgal([dire('reprends'), audio.paused], ['Je reprends la musique.', false], 'reprise');
      attendreEgal(dire('arrête'), 'Dictée arrêtée.', '« arrête » seul');
      attendre(tele.etat().actif && !audio.paused, '« arrête » seul a touché la musique');
      attendreEgal(dire('arrête la musique'), 'Musique arrêtée.', 'arrêter la musique');
      await attendreQue(() => !tele.etat().actif && el('indicateur-musique').hidden, 'musique pas arrêtée, ou note restée');
      attendreEgal(dire('pause'), 'Aucune musique en cours.', 'plus de musique');
    } finally { debrancherMusique(); }
  });

  await testAsync('Commandes vocales, étape 2a (08/11/2026, FICTIF) : volume : chiffre, plus fort, à fond, moins fort ; « tais-toi » / « silence » coupent, « remets le son » rend le volume d’avant', async c => {
    try {
      const { audio, dire } = await musiqueEnArrierePlan(c);
      attendreEgal([dire('mets le volume à 40'), audio.volume], ['Volume à 40.', 0.4], 'chiffre');
      attendreEgal([dire('monte le son'), Math.round(audio.volume * 100)], ['Je monte le volume (55).', 55], 'plus fort');
      attendreEgal([dire('baisse le son'), Math.round(audio.volume * 100)], ['Je baisse le volume (40).', 40], 'moins fort');
      attendreEgal([dire('tais-toi'), audio.volume], ['Son coupé.', 0], 'tais-toi');
      attendreEgal([dire('remets le son'), audio.volume], ['Son remis.', 0.4], 'son remis au volume d’avant');
      attendreEgal([dire('Silence !'), audio.volume], ['Son coupé.', 0], 'silence');
      attendreEgal(dire('silence'), 'Le son est déjà coupé.', 'déjà coupé');
      attendreEgal([dire('mets le son à fond'), audio.volume], ['Je monte le volume (100).', 1], 'à fond');
      attendreEgal([dire('mets le volume à zéro'), audio.volume], ['Son coupé.', 0], 'zéro = couper');
      attendreEgal(dire('il fait silence dans la maison FICTIF'), null, '« silence » dans une phrase : pas une commande');
    } finally { debrancherMusique(); }
  });

  await testAsync('Commandes vocales, étape 2a (08/11/2026, FICTIF) : « un autre », « le suivant », « morceau précédent », « recommence », « rejoue », avancer / reculer / aller à, « c’est quoi ce morceau », « montre-moi le player »', async c => {
    try {
      const { el, audio, appels, dire } = await musiqueEnArrierePlan(c);
      const n = appels.length;
      attendreEgal(dire('un autre'), 'Morceau suivant.', 'un autre');
      await attendreQue(() => appels.length === n + 1, 'morceau suivant pas joué');
      // (Le 3e morceau du faux Drive est volontairement trop gros : on reste sur les deux premiers.)
      attendreEgal(dire('morceau précédent'), 'Morceau précédent.', 'précédent');
      await attendreQue(() => appels.length === n + 2 && appels[n + 1][1] === appels[0][1], 'précédent pas joué');
      attendreEgal(dire('morceau précédent'), 'C’est le premier morceau de la liste.', 'premier');
      attendreEgal(dire('le suivant'), 'Morceau suivant.', 'le suivant (la musique joue : le morceau)');
      await attendreQue(() => appels.length === n + 3 && appels[n + 2][1] === appels[n][1], 'suivant pas joué');
      attendreEgal(dire('un autre jour FICTIF'), null, '« un autre » dans une phrase : pas une commande');
      audio.currentTime = 50;
      attendreEgal([dire('avance de 10 secondes'), audio.currentTime], ['J’avance de 10 secondes.', 60], 'avance');
      attendreEgal([dire('recule de 30 secondes'), audio.currentTime], ['Je recule de 30 secondes.', 30], 'recule');
      attendreEgal([dire('avance à 2 minutes 40'), audio.currentTime], ['Je vais à 2 minutes 40.', 160], 'aller à');
      attendreEgal([dire('recommence'), audio.currentTime], ['Je reprends le morceau au début.', 0], 'recommence');
      attendre(dire('reviens') !== 'Je reprends le morceau au début.', '« reviens » seul remet au début');
      audio.currentTime = 90; audio.paused = true;
      attendreEgal([dire('rejoue'), audio.currentTime, audio.paused], ['Je rejoue ce morceau.', 0, false], 'rejoue');
      attendre(/^Ce morceau s’appelle « .*FICTIF.* »\.$/.test(dire('c’est quoi ce morceau')), 'titre');
      attendreEgal(dire('montre-moi le player'), 'Voici le lecteur.', 'player');
      attendre(el('lecteur-mp3-relations').open, 'lecteur pas revenu');
    } finally { debrancherMusique(); }
  });

  await testAsync('Commandes vocales, étape 2a (08/11/2026, FICTIF) : « le suivant » sans musique ni fenêtre : égalité dite (« J’hésite… »), rien choisi ; sans musique : « Aucune musique en cours. »', async c => {
    try {
      commandesMusique.brancher({ lecteur: () => ({ pause: () => 'Aucune musique en cours.', suivant: () => 'Aucune musique en cours.' }) });
      const lignes = commandesVocales.analyser(TABLEUR_FICTIF_2A).lignes;
      const d = commandesVocales.deciderMicro('le suivant', { lignes, contexte: {} });
      attendre(d && d.statut === 'ambigu' && /J’hésite/.test(d.message), `pas d’égalité dite : ${JSON.stringify(d)}`);
      attendreEgal(commandesVocales.deciderMicro('pause', { lignes, contexte: {} }).message, 'Aucune musique en cours.', 'sans musique');
    } finally { debrancherMusique(); }
  });

  // ----- 08/11/2026 : commandes vocales, ÉTAPE 2b (lancer la musique), FAUX tableur et FAUX Drive FICTIFS -----
  const TABLEUR_FICTIF_2B = [
    TABLEUR_FICTIF_0[0],
    ['Lancer un morceau', '', 'Verbe de lecture MP3', 'mets-moi', 'MUS-01', ''],
    ['Lancer un morceau', '', 'Cible de titre', '[TITRE]', 'MUS-01', ''],
    ['Lancer un morceau', '', 'Cible de personne', 'un morceau de [PRÉNOM]', 'MUS-01', ''],
    ['Lancer un morceau', '', 'Cible de personne', 'un truc de [PRÉNOM]', 'MUS-01', ''],
    ['Toute la musique d’une personne', '', 'Verbe de lecture MP3', 'mets-moi', 'MUS-02', ''],
    ['Toute la musique d’une personne', '', 'Cible de personne', 'toute la musique de [PRÉNOM]', 'MUS-02', ''],
    ['Album entier', '', 'Expression complète', 'mets-moi l’album [TITRE] en entier', 'MUS-03', ''],
    ['Au hasard', '', 'Expression complète', 'mets-moi un morceau au hasard', 'MUS-04', ''],
    ['Choisir un fichier', '', 'Expression complète', 'choisis un fichier', 'MUS-18', '']
  ];
  async function musiqueALancer(c, { connecte = true, tirage = 0 } = {}) {
    const f = fauxDriveCompteCap(c);
    remplirMusiqueFictive(f);
    const { m } = connecterCompteFictif(c);
    if (!connecte) m.seDeconnecter ? m.seDeconnecter() : null;
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const el = id => ui.parId(id);
    brancherAccueil(c, ui);
    const audio = Object.assign(new EventTarget(), { paused: true, currentTime: 0, duration: 200, volume: 0.8, play() { this.paused = false; }, pause() { this.paused = true; } });
    const appels = [];
    const objet = { audio, jouerFichier: (adresse, titre) => { appels.push(['jouer', titre]); audio.paused = false; }, arreter: () => { appels.push(['arreter']); audio.paused = true; } };
    const compte = connecte ? m : { ...m, connecte: () => false };
    const tele = relationsMp30().brancher(ui.doc, { compte, arbre: () => relationsCompte0().lireArbre(m), sorte: relationsCompte0().sorte, stockage: c.localStorage,
      lecteur: async () => objet, urls: fausseAdresses(), hasard: () => tirage });
    commandesMusique.brancher({ lecteur: () => tele });
    const lignes = commandesVocales.analyser(TABLEUR_FICTIF_2B).lignes;
    const dire = async phrase => {
      const d = commandesVocales.deciderMicro(phrase, { lignes, contexte: {} });
      if (!d) return null;
      return d.suite ? await d.suite : d.message;
    };
    return { ui, el, appels, tele, dire, f }; // 09/11/2026 : + f (le faux Drive)
  }
  const debrancherMusiqueTout = () => { for (let i = 1; i <= 23; i++) commandesVocales.brancherAction(`MUS-${String(i).padStart(2, '0')}`, undefined); };

  await testAsync('L’ORDRE GAGNE (09/11/2026, décision de Max, bloc c75, FAUX Drive FICTIF) : fenêtre « Musique » : « trois » dit seul touche la 3e ligne, pas le morceau « Trois FICTIF » (2e ligne)', async c => {
    try {
      const { ui, el } = await musiqueALancer(c);
      el('ouvrir-lecteur').click();
      await attendreQue(() => el('musique-relations').open && el('liste-musique-relations').querySelectorAll('button').length >= 2, 'dossiers pas montrés');
      el('liste-musique-relations').querySelector('button').click(); // le dossier de la première personne FICTIVE
      await attendreQue(() => el('liste-musique-relations').querySelectorAll('.ligne-morceau').length >= 3, 'morceaux pas montrés');
      const lignes = [...el('liste-musique-relations').querySelectorAll('button')];
      attendre(/Trois FICTIF/.test(lignes[1].textContent) && !/Trois FICTIF/.test(lignes[2].textContent), `ordre inattendu : ${lignes.map(b => b.textContent).join(' | ')}`);
      const touchees = [];
      lignes.forEach((b, i) => b.addEventListener('click', () => touchees.push(i + 1), true));
      Object.assign(ui.dictee, { disponible: () => true, enCours: () => false, arreter() {}, demarrer(r) { r.surFinal('trois'); if (r.surFin) r.surFin(); } });
      el('petit-micro').click();
      attendreEgal(touchees, [3], '« trois » n’a pas touché la 3e ligne');
    } finally { debrancherMusiqueTout(); }
  });

  // ----- 09/11/2026 (décision de Max, bloc c74) : PLAYLIST PAR DÉFAUT, FAUX Drive FICTIF -----
  await testAsync('Playlist par défaut (09/11/2026, bloc c74, FAUX Drive FICTIF) : « mets la zik » / « mets la musique » / « mets la zic » : le lecteur S’ALLUME (affiché) avec TOUS les MP3 jouables de Relations, dossier par dossier (« É » trié comme « E », avant « G »), trop gros exclus ; toujours depuis le PREMIER morceau ; musique déjà là : le lecteur seulement, rien relancé', async c => {
    try {
      const { el, appels, tele, dire, f } = await musiqueALancer(c);
      const D = 'application/vnd.google-apps.folder';
      const son = new TextEncoder().encode('ID3 son FICTIF');
      const rel = f.fichiers.find(x => x.name === 'Relations');
      const gaston = f.ajouter('r_Gaston Musique-FICTIF', D, rel.id);
      f.ajouter('Gamme FICTIVE.mp3', 'audio/mpeg', gaston.id, son);
      const elodie = f.ajouter('r_Élodie Musique-FICTIF', D, rel.id);
      f.ajouter('Écho FICTIF.mp3', 'audio/mpeg', elodie.id, son);
      const reponse = await dire('mets la zik');
      attendreEgal(reponse, 'Je mets la musique : 12 morceaux, en commençant par le premier.', 'réponse');
      await attendreQue(() => appels.filter(x => x[0] === 'jouer').length === 1, 'rien lancé');
      const premier = appels.find(x => x[0] === 'jouer')[1];
      attendre(el('lecteur-mp3-relations').open && !tele.etat().arrierePlan, 'lecteur pas affiché (il doit s’allumer)');
      // L'ordre : on avance morceau par morceau jusqu'au bout.
      const titres = [premier];
      for (let i = 0; i < 11; i++) {
        const n = appels.filter(x => x[0] === 'jouer').length;
        tele.suivant();
        await attendreQue(() => appels.filter(x => x[0] === 'jouer').length === n + 1, `morceau ${i + 2} pas lancé`);
        titres.push(appels.filter(x => x[0] === 'jouer').at(-1)[1]);
      }
      const ou = mot => titres.findIndex(x => x.includes(mot));
      attendre(ou('Seul FICTIF') > ou('Bonus FICTIF') && ou('Écho FICTIF') > ou('Seul FICTIF') && ou('Gamme FICTIVE') > ou('Écho FICTIF'), `ordre des dossiers : ${JSON.stringify(titres)}`);
      attendre(!titres.some(x => /Énorme/.test(x)), 'morceau trop gros dans la liste');
      // Musique en arrière-plan : « mets la musique » ramène le lecteur, ne relance rien.
      tele.arrierePlan();
      await attendreQue(() => tele.etat().actif && tele.etat().arrierePlan, 'pas passée en arrière-plan');
      const avant = appels.filter(x => x[0] === 'jouer').length;
      attendreEgal(await dire('mets la musique'), 'Voici le lecteur.', 'musique déjà là');
      await attendreMs(50);
      attendreEgal(appels.filter(x => x[0] === 'jouer').length, avant, 'musique relancée');
      // Arrêtée : « mets la zic » repart du PREMIER morceau.
      tele.arreter();
      await attendreMs(400);
      attendre(!tele.etat().actif, 'pas arrêtée');
      attendreEgal(await dire('mets la zic'), 'Je mets la musique : 12 morceaux, en commençant par le premier.', 'relance');
      await attendreQue(() => appels.filter(x => x[0] === 'jouer').length === avant + 1, 'pas relancée');
      attendreEgal(appels.filter(x => x[0] === 'jouer').at(-1)[1], premier, 'pas repartie du premier morceau');
      // « mets la zik et la suite » : pas la phrase entière : pas la playlist.
      attendre((await dire('mets la zik et la suite FICTIVE')) !== 'Je mets la musique : 12 morceaux, en commençant par le premier.', 'reconnue sans être dite en entier');
    } finally { debrancherMusiqueTout(); }
  });

  await testAsync('Playlist par défaut (09/11/2026, bloc c74, FICTIF) : une phrase apprise avant (« mets la zik » → « Lancer un morceau ») passe à « Afficher le lecteur » au démarrage : l’ancienne ligne « remplacée le … » dans le tampon du petit tableur, rien effacé', async c => {
    // 09/11/2026 (séance 2) : les changements vont dans le tampon de « Commandes vocales (Cap) » (avant : cap_phrases_tampon_v1, ses champs « ligne » et « etat »).
    const cles = ['cap_phrases_a_apprendre_v1', 'cap_tableur_cap_tampon_v1', 'cap_phrases_tableur_reprise_v1', 'cap_phrases_apprises_copie_v1', 'cap_tableur_cap_reprise_v1'];
    const avant = cles.map(k => localStorage.getItem(k));
    try {
      localStorage.setItem('cap_phrases_tableur_reprise_v1', 'FICTIF');
      localStorage.removeItem('cap_tableur_cap_tampon_v1');
      localStorage.setItem('cap_tableur_cap_reprise_v1', 'FICTIF'); // la reprise est testée à part
      localStorage.setItem('cap_phrases_a_apprendre_v1', JSON.stringify([
        { id: 'P-zik', phrase: 'mets la zik', code: 'MUS-01', commande: 'Lancer un morceau', origine: 'hésitation', quand: '2030-01-10T10:00:00Z' },
        { id: 'P-autre', phrase: 'ouvre la boîte fictive', code: 'NAV-03', commande: 'Ouvrir Réglages', origine: 'bouton', quand: '2030-01-10T10:00:00Z' }]));
      localStorage.setItem('cap_phrases_apprises_copie_v1', JSON.stringify({ lignes: [{ phrase: 'mets la musique', code: 'MUS-01', commande: 'Lancer un morceau', etat: '', id: 'P-ailleurs' }] }));
      preparerInterface(c, { largeur: 412, hauteur: 900 });
      const liste = JSON.parse(localStorage.getItem('cap_phrases_a_apprendre_v1'));
      attendreEgal(liste.map(e => [e.phrase, e.code]).sort(), [['mets la zik', 'MUS-19'], ['ouvre la boîte fictive', 'NAV-03']], 'liste');
      const tampon = JSON.parse(localStorage.getItem('cap_tableur_cap_tampon_v1') || '[]');
      attendre(tampon.some(o => o.type === 'etat' && o.id === 'P-zik' && /^remplacée le /.test(o.texte)), `ancienne pas marquée : ${JSON.stringify(tampon)}`);
      attendre(tampon.some(o => o.type === 'ajout' && o.phrase === 'mets la zik' && o.code === 'MUS-19'), 'nouvelle pas ajoutée');
      attendre(tampon.some(o => o.type === 'etat' && o.id === 'P-ailleurs' && /^remplacée le /.test(o.texte)), 'ligne d’un autre appareil pas marquée');
      attendre(!tampon.some(o => o.id === 'P-autre' && o.type === 'etat'), 'une autre phrase touchée');
      // Deuxième démarrage : rien de plus.
      const n = tampon.length;
      preparerInterface(c, { largeur: 412, hauteur: 900 });
      attendreEgal(JSON.parse(localStorage.getItem('cap_tableur_cap_tampon_v1')).length, n, 'refait au 2e démarrage');
    } finally { cles.forEach((k, i) => { if (avant[i] === null) localStorage.removeItem(k); else localStorage.setItem(k, avant[i]); }); }
  });

  await testAsync('Commandes vocales, étape 2b (08/11/2026, FAUX Drive FICTIF) : « mets-moi trois » lance le morceau EN ARRIÈRE-PLAN (l’écran Micro reste, la note ronde est là) ; « un truc de bob » lance sa musique ; personne sans musique : dit', async c => {
    try {
      const { el, appels, tele, dire } = await musiqueALancer(c);
      // 09/11/2026 : plus d'écran Micro (avant : el('ouvrir-micro').click()).
      attendreEgal(await dire('mets-moi trois'), 'Je mets « Trois FICTIF ».', 'titre');
      await attendreQue(() => appels.length === 1 && /Trois FICTIF/.test(appels[0][1]), 'morceau pas lancé');
      attendre(!el('lecteur-mp3-relations').open && tele.etat().arrierePlan && !el('indicateur-musique').hidden && !el('accueil-boutons').hidden /* 09/11/2026 : l'accueil (plus d'écran Micro) */, 'pas en arrière-plan, ou écran Micro couvert');
      attendreEgal(await dire('mets-moi un truc de bob'), 'Je mets « Seul FICTIF ».', 'personne');
      await attendreQue(() => appels.length === 2 && /Seul FICTIF/.test(appels[1][1]), 'musique de la personne pas lancée');
      attendreEgal(await dire('mets-moi un truc de zoé'), 'Je ne trouve pas de musique de « zoe » dans Cap.', 'personne sans musique');
      attendreEgal(await dire('mets-moi xyzzy'), 'Je ne trouve pas de morceau « xyzzy ».', 'rien trouvé');
      attendreEgal(appels.length, 2, 'un morceau a été lancé sans être trouvé');
    } finally { debrancherMusiqueTout(); }
  });

  await testAsync('Commandes vocales, étape 2b (08/11/2026, FAUX Drive FICTIF) : plusieurs réponses : Cap ne devine pas, il montre les choix en très gros avec de gros numéros ; un toucher lance', async c => {
    try {
      const { ui, el, appels, dire } = await musiqueALancer(c);
      const reponse = await dire('mets-moi fictif');
      attendre(/^J’ai trouvé \d+ morceaux.*touche le bon numéro\.$/.test(reponse), `réponse : ${reponse}`);
      attendreEgal(appels.length, 0, 'Cap a deviné');
      const choix = [...el('liste-musique-relations').querySelectorAll('button.ligne-choix-voix')];
      attendre(el('musique-relations').open && choix.length >= 2 && choix.length <= 9, 'choix pas montrés');
      attendreEgal(choix.map(b => b.querySelector('.numero-morceau').textContent).slice(0, 3), ['1', '2', '3'], 'gros numéros');
      const vue = ui.cadre.contentWindow;
      attendre(parseFloat(vue.getComputedStyle(choix[0].querySelector('.numero-morceau')).fontSize) > parseFloat(vue.getComputedStyle(choix[0]).fontSize), 'numéro pas plus gros');
      choix[1].click();
      await attendreQue(() => appels.length === 1, 'le toucher ne lance pas');
    } finally { debrancherMusiqueTout(); }
  });

  await testAsync('Commandes vocales, étape 2b (08/11/2026, FAUX Drive FICTIF) : album entier, toute la musique d’une personne, au hasard (seulement avec « au hasard »), « choisis un fichier »', async c => {
    try {
      const { el, appels, dire } = await musiqueALancer(c, { tirage: 0 });
      attendreEgal(await dire('mets-moi l’album été en entier'), 'Je mets l’album « Album Été FICTIF ».', 'album');
      await attendreQue(() => appels.length === 1 && /Premier FICTIF/.test(appels[0][1]), 'album pas lancé au premier morceau');
      attendreEgal(await dire('mets-moi toute la musique de bob'), 'Je mets toute la musique de Bob Seul.', 'toute la musique');
      await attendreQue(() => appels.length === 2, 'musique de la personne pas lancée');
      const hasard = await dire('mets-moi un morceau au hasard');
      attendre(/^Je mets « .* »\.$/.test(hasard), `hasard : ${hasard}`);
      await attendreQue(() => appels.length === 3, 'hasard pas lancé');
      attendreEgal(await dire('choisis un fichier'), 'Touche « Choisir » dans le lecteur pour prendre un MP3 du téléphone.', 'choisir');
      attendre(el('lecteur-mp3-relations').open, 'lecteur pas affiché pour « Choisir »');
    } finally { debrancherMusiqueTout(); }
  });

  await testAsync('Commandes vocales, étape 2b (08/11/2026, FAUX Drive FICTIF) : compte Cap pas connecté : message clair et « Autoriser la lecture du compte Cap » montré ; rien lancé', async c => {
    try {
      const { el, appels, dire } = await musiqueALancer(c, { connecte: false });
      const reponse = await dire('mets-moi trois');
      attendre(/pas connecté.*Autoriser la lecture du compte Cap/.test(reponse), `réponse : ${reponse}`);
      await attendreQue(() => el('musique-relations').open && !el('autoriser-musique-relations').hidden, 'bouton de reconnexion absent');
      attendreEgal(appels.length, 0, 'musique lancée sans connexion');
      attendre(!/cerveau|traiterDemande|journalIa/.test(SOURCE_RELATIONS_MP3_TEST), 'le lecteur parle à l’IA');
    } finally { debrancherMusiqueTout(); }
  });

  // ----- 08/11/2026 : « arrête la musique » (défaut c50) et reprise automatique de la musique, FICTIF -----
  // Faux tableur FIDÈLE au vrai : les verbes d'arrêt de MUS-07 et MUS-10 sont tous « RETIRER » (seulement avec un
  // mot-clé), les mots-clés sont des lignes à part, il n'y a pas d'expression « arrête la musique ».
  const TABLEUR_FICTIF_ARRET = [
    TABLEUR_FICTIF_0[0],
    ['Dictée', '', 'Verbe d’arrêt', 'arrête', 'DIC-02', ''],
    ['Dictée', '', 'Verbe d’arrêt', 'stop', 'DIC-02', ''],
    ['Arrêter la musique', '', 'Verbe d’arrêt de la musique', 'arrête', 'MUS-07', 'RETIRER 08/11/2026 : verbe d’arrêt seul = dictée (DIC-02) ; garder seulement avec une cible'],
    ['Arrêter la musique', '', 'Verbe d’arrêt de la musique', 'stop', 'MUS-07', 'RETIRER 08/11/2026 : verbe d’arrêt seul = dictée (DIC-02) ; garder seulement avec une cible'],
    ['Arrêter la musique', '', 'Verbe d’arrêt de la musique', 'coupe', 'MUS-07', 'RETIRER 08/11/2026 : doublon avec MUS-10'],
    ['Arrêter la musique', '', 'Verbe d’arrêt de la musique', 'mets fin à', 'MUS-07', ''],
    ['Arrêter la musique', '', 'Mot-clé', 'la musique', 'MUS-07', ''],
    ['Arrêter la musique', '', 'Mot-clé', 'le morceau', 'MUS-07', ''],
    ['Arrêter la musique', '', 'Mot-clé', 'le player', 'MUS-07', ''],
    ['Couper le son', '', 'Verbe de coupure du son', 'coupe', 'MUS-10', 'RETIRER 08/11/2026 : doublon avec MUS-07 ; garder seulement avec « son » ou « volume »'],
    ['Couper le son', '', 'Verbe de coupure du son', 'mets en sourdine', 'MUS-10', ''],
    ['Couper le son', '', 'Mot-clé', 'le son', 'MUS-10', '']
  ];

  test('« arrête la musique » (08/11/2026, défaut constaté sur c50, faux tableur FIDÈLE au vrai) : avec un mot-clé = arrêter la musique / couper le son ; « arrête », « stop » seuls = la dictée ; « coupe » seul : rien', () => {
    const lignes = commandesVocales.analyser(TABLEUR_FICTIF_ARRET).lignes;
    const code = phrase => { const r = commandesVocales.reconnaitre(phrase, lignes); return r.statut === 'reconnu' ? r.code : r.statut; };
    for (const phrase of ['arrête la musique', 'Stop le morceau !', 'arrête le player', 'coupe la musique', 'mets fin à la musique']) attendreEgal(code(phrase), 'MUS-07', phrase);
    attendreEgal(code('coupe le son'), 'MUS-10', 'coupe le son');
    attendreEgal([code('arrête'), code('stop'), code('coupe')], ['DIC-02', 'DIC-02', 'rien'], 'verbes seuls');
  });

  // Faux lecteur pour la reprise automatique : « Android » met la musique en pause pendant l'écoute.
  function fauxLecteurReprise({ joue = true, pauseVoulue = false } = {}) {
    const f = { actif: true, enPause: !joue, pauseVoulue, reprises: 0 };
    f.etat = () => ({ actif: f.actif, enPause: f.enPause, pauseVoulue: f.pauseVoulue && f.enPause, arrierePlan: true });
    f.reprendre = () => { f.reprises++; f.enPause = false; return 'Je reprends la musique.'; };
    return f;
  }
  const declencherDelai = (c, ms) => {
    const d = [...c.delais.entries()].find(([, x]) => x.delai === ms);
    if (!d) return false;
    c.delais.delete(d[0]);
    d[1].rappel();
    return true;
  };

  await testAsync('Reprise automatique (08/11/2026, FICTIF) : musique coupée par l’écoute (appui simple) : Cap la relance 1,5 s après ; jamais si Max a demandé la pause ; rien si elle ne jouait pas', async c => {
    const avant = relationsMp3.instance;
    try {
      for (const [nom, options, attendu] of [['coupée par l’écoute', {}, 1], ['pause voulue', { pauseVoulue: true }, 0], ['ne jouait pas', { joue: false }, 0]]) {
        const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
        const lecteur = fauxLecteurReprise(options);
        relationsMp3.instance = lecteur;
        Object.assign(ui.dictee, { disponible: () => true, enCours: () => false, arreter() {},
          demarrer(r) { lecteur.enPause = true; /* Android coupe la musique pendant l'écoute */ r.surFinal('acheter du pain FICTIF'); r.surFin(); } });
        const nombre = TACHES.length;
        parlerAuGrosMicro(ui.parId('microphone')); // 09/11/2026 : deux touchers
        TACHES.slice(nombre).forEach(tache => abandonner(tache.id));
        const prevu = declencherDelai(c, 1500);
        attendreEgal([nom, lecteur.reprises], [nom, attendu], 'reprise');
        if (options.joue === false) attendre(!prevu, 'reprise prévue alors que rien ne jouait');
      }
    } finally { relationsMp3.instance = avant; }
  });

  await testAsync('Reprise automatique (08/11/2026, FICTIF) : écoute continue : Cap prévient une fois (« la musique est en pause pendant la conversation, elle reprendra à l’arrêt ») ; à l’arrêt, la musique repart', async c => {
    const avant = relationsMp3.instance;
    try {
      const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
      brancherAccueil(c, ui);
      const lecteur = fauxLecteurReprise();
      relationsMp3.instance = lecteur;
      Object.assign(ui.dictee, { disponible: () => true, enCours: () => false, arreter() {}, demarrer() { lecteur.enPause = true; } });
      ui.parId('micro-continu').click();
      attendre(/La musique est en pause pendant la conversation, elle reprendra à l’arrêt\./.test(ui.parId('statut').textContent), `message absent : ${ui.parId('statut').textContent}`);
      ui.parId('micro-continu').click();
      attendre(declencherDelai(c, 1500), 'reprise pas prévue à l’arrêt');
      attendreEgal(lecteur.reprises, 1, 'musique pas relancée à l’arrêt');
    } finally { relationsMp3.instance = avant; }
  });

  // ----- 08/11/2026 : commandes vocales, ÉTAPE 3a (visionneuse : ouvrir, PDF ou image par nom), FICTIF -----
  // Faux tableur bâti comme le vrai (VIS-02 : expressions complètes, mots-clés, cibles [TITRE] et [DOSSIER], une ligne RETIRER).
  const TABLEUR_FICTIF_3A = [
    TABLEUR_FICTIF_0[0],
    ['Navigation', '', 'Verbe d’ouverture', 'ouvre', 'COMMUN', ''],
    ['Ouvrir la visionneuse', '', 'Expression complète', 'ouvre la visionneuse', 'VIS-01', ''],
    ['Ouvrir la visionneuse', '', 'Expression complète', 'ouvre l’œil', 'VIS-01', ''],
    ['Ouvrir la visionneuse', '', 'Mot-clé', 'la visionneuse', 'VIS-01', ''],
    ['Ouvrir la visionneuse', '', 'Verbe d’affichage', 'affiche', 'VIS-01', 'RETIRER 08/11/2026 : jamais seul'],
    ['Afficher un PDF', '', 'Expression complète', 'affiche le pdf', 'VIS-02', ''],
    ['Afficher un PDF', '', 'Expression complète', 'affiche-moi le pdf', 'VIS-02', ''],
    ['Afficher un PDF', '', 'Expression complète', 'ouvre le pdf', 'VIS-02', ''],
    ['Afficher un PDF', '', 'Mot-clé', 'le pdf', 'VIS-02', ''],
    ['Afficher un PDF', '', 'Cible de document', '[TITRE]', 'VIS-02', ''],
    ['Afficher un PDF', '', 'Cible de document', 'dans le dossier [DOSSIER]', 'VIS-02', ''],
    ['Afficher un PDF', '', 'Tournure de besoin', 'je veux voir le pdf', 'VIS-02', ''],
    ['Afficher une image', '', 'Expression complète', 'montre la photo', 'VIS-03', ''],
    ['Afficher une image', '', 'Mot-clé', 'la photo', 'VIS-03', ''],
    ['Afficher une image', '', 'Cible de document', '[TITRE]', 'VIS-03', ''],
    ['Lancer un morceau', '', 'Verbe de lecture MP3', 'mets-moi', 'MUS-01', ''],
    ['Lancer un morceau', '', 'Cible de titre', '[TITRE]', 'MUS-01', '']
  ];

  test('Étape 3a (08/11/2026, FICTIF) : « affiche le pdf impôts » = VIS-02 avec le nom entier ; « affiche le pdf » seul = VIS-02 sans nom ; dossier ; « ouvre l’oeil » ; « affiche » seul n’est jamais une commande ; [TITRE] = tout ce qui suit le verbe', () => {
    const lignes = commandesVocales.analyser(TABLEUR_FICTIF_3A).lignes;
    const r = phrase => commandesVocales.reconnaitre(phrase, lignes);
    const x = r('affiche le pdf impôts fictif');
    attendre(x.code === 'VIS-02' && x.valeurs && x.valeurs.titre === 'impots fictif', `nom : ${JSON.stringify(x)}`);
    const y = r('affiche le pdf');
    attendre(y.code === 'VIS-02' && !y.valeurs, `sans nom : ${JSON.stringify(y)}`);
    // 09/11/2026 (décision de Max, avant publication) : plus aucun type de document de santé, même fictif. Avant : « dossier santé fictif ».
    const z = r('affiche-moi le pdf dans le dossier factures fictif');
    attendre(z.code === 'VIS-02' && z.valeurs && z.valeurs.dossier === 'factures fictif', `dossier : ${JSON.stringify(z)}`);
    attendreEgal([r('ouvre l’oeil').code, r('ouvre la visionneuse').code, r('montre la photo plage fictif').valeurs], ['VIS-01', 'VIS-01', { titre: 'plage fictif' }], 'œil, visionneuse, photo');
    attendre(r('affiche').statut !== 'reconnu' && r('affiche le menu fictif').statut !== 'reconnu', '« affiche » sans mot de contenu reconnu');
    attendreEgal(r('mets-moi bohemian rhapsody fictif s’il te plaît').valeurs, { titre: 'bohemian rhapsody fictif' }, 'titre entier (et pas le dernier mot)');
  });

  async function visionneuseALaVoix(c, { connecte = true } = {}) {
    const f = fauxDriveCompteCap(c);
    const D = 'application/vnd.google-apps.folder';
    const docs = f.ajouter('Documents', D);
    // 09/11/2026 (décision de Max, avant publication) : « Factures FICTIF » et « Devis FICTIF » (avant : un dossier et un document de santé).
    const factures = f.ajouter('Factures FICTIF', D, docs.id);
    for (const nom of ['Devis FICTIF.pdf', 'Facture eau FICTIF.pdf', 'Facture gaz FICTIF.pdf']) f.ajouter(nom, 'application/pdf', factures.id);
    const rel = f.ajouter('Relations', D);
    const ana = f.ajouter('r_Ana Image-FICTIF', D, rel.id);
    f.ajouter('Photo plage FICTIF.jpg', 'image/jpeg', ana.id);
    const { m } = connecterCompteFictif(c);
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    brancherAccueil(c, ui);
    const ouvertures = [];
    const annonces = [];
    const fausseVisionneuse = { ouvrir: async liste => { ouvertures.push(liste); }, annoncer: (texte, options) => { annonces.push([texte, options || {}]); } };
    const compte = connecte ? m : { ...m, connecte: () => false };
    commandesVisionneuse.brancher(ui.doc, { compte, lireArbre: x => relationsCompte0().lireArbre(x), sorte: relationsCompte0().sorte, visionneuse: () => fausseVisionneuse });
    const lignes = commandesVocales.analyser(TABLEUR_FICTIF_3A).lignes;
    const dire = async phrase => { const d = commandesVocales.deciderMicro(phrase, { lignes, contexte: {} }); if (!d) return null; return d.suite ? await d.suite : d.message; };
    return { ui, el: id => ui.parId(id), ouvertures, annonces, dire };
  }
  const debrancherVision = () => { for (let i = 1; i <= 8; i++) commandesVocales.brancherAction(`VIS-0${i}`, undefined); };

  await testAsync('Étape 3a (08/11/2026, FAUX Drive FICTIF) : un seul PDF ou une seule image trouvés : ouverts dans la visionneuse ; plusieurs, ou « affiche le pdf » sans nom : gros choix numérotés (Cap ne devine pas) ; rien trouvé : dit', async c => {
    try {
      const { ui, el, ouvertures, dire } = await visionneuseALaVoix(c);
      attendreEgal(await dire('affiche le pdf devis'), 'J’ouvre « Devis FICTIF ».', 'un PDF');
      attendre(ouvertures.length === 1 && ouvertures[0].length === 1 && ouvertures[0][0].sorte === 'pdf', 'PDF pas ouvert');
      attendreEgal(await dire('montre la photo plage'), 'J’ouvre « Photo plage FICTIF ».', 'une image');
      attendreEgal(ouvertures[1][0].sorte, 'image', 'image ouverte comme une image');
      attendre(/^J’ai trouvé 2 PDF : touche le bon numéro\.$/.test(await dire('affiche le pdf facture')), 'plusieurs PDF : pas de choix');
      attendreEgal(ouvertures.length, 2, 'Cap a deviné');
      const choix = [...el('liste-choix-voix').querySelectorAll('button.ligne-choix-voix')];
      attendre(el('choix-voix').open && choix.length === 2 && choix[0].querySelector('.numero-morceau').textContent === '1', 'choix pas montrés en gros numéros');
      const vue = ui.cadre.contentWindow;
      attendre(parseFloat(vue.getComputedStyle(choix[0].querySelector('.numero-morceau')).fontSize) > parseFloat(vue.getComputedStyle(choix[0]).fontSize), 'numéro pas plus gros');
      attendreEgal(el('fermer-choix-voix').textContent, 'Fermer', '« Fermer » des choix');
      choix[1].click();
      attendreEgal(ouvertures.length, 3, 'le toucher n’ouvre pas');
      attendreEgal(await dire('affiche le pdf'), 'Quel PDF ? : touche le bon numéro.', 'sans nom : demande lequel');
      attendreEgal(el('liste-choix-voix').querySelectorAll('button.ligne-choix-voix').length, 3, 'tous les PDF proposés');
      attendreEgal(await dire('affiche-moi le pdf dans le dossier factures'), 'Quel PDF ? : touche le bon numéro.', 'dossier');
      attendreEgal(await dire('affiche le pdf xyzzy'), 'Je ne trouve pas de PDF « xyzzy ».', 'rien trouvé');
    } finally { debrancherVision(); }
  });

  await testAsync('Étape 3a (08/11/2026, FAUX Drive FICTIF) : compte Cap pas connecté : la visionneuse le dit avec « Autoriser » ; « ouvre l’œil » = le même bouton que l’œil de « Autre »', async c => {
    try {
      const { el, ouvertures, annonces, dire } = await visionneuseALaVoix(c, { connecte: false });
      attendre(/pas connecté.*Autoriser la lecture du compte Cap/.test(await dire('affiche le pdf devis')), 'message');
      attendre(annonces.length === 1 && annonces[0][1].autorisation === true, '« Autoriser » pas proposé dans la visionneuse');
      attendreEgal(ouvertures.length, 0, 'ouvert sans connexion');
      let oeil = 0;
      el('ouvrir-oeil').addEventListener('click', () => { oeil++; });
      attendreEgal(await dire('ouvre l’œil'), 'J’ouvre la visionneuse.', 'œil');
      attendreEgal(oeil, 1, 'bouton de l’œil pas touché');
      attendre(!/cerveau|traiterDemande|journalIa/.test(SOURCE_COMMANDES_VISIONNEUSE_TEST), 'la visionneuse à la voix parle à l’IA');
    } finally { debrancherVision(); }
  });

  await testAsync('Étape 3a (08/11/2026) : la visionneuse montre une image comme une image (« Image N.jpg ») et un PDF comme un PDF', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const titres = [];
    const compte = { appeler: async () => ({ blob: async () => new Blob(['FICTIF']) }) };
    const v = visionneuseCap.brancher(ui.doc, { compte, visionneuse: async () => ({ montrerFichier: (adresse, titre) => titres.push(titre), fermer() {} }), urls: fausseAdresses() });
    await v.ouvrirEnGrand([{ id: 'a', sorte: 'image' }, { id: 'b' }]); // 08/11/2026 (vignettes) : avant, v.ouvrir
    attendreEgal(titres, ['Image 1.jpg', 'PDF 2.pdf'], 'titres');
    ui.parId('fermer-visionneuse').click();
  });

  // ----- 08/11/2026 : étape 3b, petit micro de la visionneuse (FICTIF) -----
  async function visionneuseAvecMicro(c) {
    const cle = commandesVocales.CLE_COPIE;
    const avantCopie = localStorage.getItem(cle);
    localStorage.setItem(cle, JSON.stringify({ lu_le: new Date(0).toISOString(), compte: {}, lignes: commandesVocales.analyser(TABLEUR_FICTIF_1).lignes }));
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    brancherAccueil(c, ui); // 09/11/2026 : pose le petit micro de tous les écrans dans la fenêtre du dessus
    ui.parId('visionneuse-cap').showModal();
    await pause();
    const remettre = () => { if (avantCopie === null) localStorage.removeItem(cle); else localStorage.setItem(cle, avantCopie); };
    return { ui, el: id => ui.parId(id), remettre };
  }

  await testAsync('Étape 3b (08/11/2026) : petit micro FIXE tout en haut à droite de la visionneuse, icône seule (aucun mot), touchable ; « Fermer la visionneuse » reste', async c => {
    const { ui, el, remettre } = await visionneuseAvecMicro(c);
    try {
      // 09/11/2026 : le petit micro de TOUS les écrans (posé dans la visionneuse) remplace celui de la visionneuse (caché).
      // Avant : const m = el('micro-visionneuse');
      attendre(el('micro-visionneuse').hidden, 'ancien micro de la visionneuse encore affiché');
      const m = el('petit-micro');
      attendre(m && el('visionneuse-cap').contains(m), 'micro absent de la visionneuse');
      const r = m.getBoundingClientRect();
      attendre(r.right >= 412 - 20 && r.top < 160 && r.width >= 48 && r.height >= 48, `micro mal placé : ${JSON.stringify(r)}`);
      attendreEgal(m.textContent.trim(), '', 'mot affiché sur le micro');
      attendre(m.getAttribute('aria-label') && touchable(ui, m), 'micro sans nom ou pas touchable');
      attendreEgal(ui.cadre.contentWindow.getComputedStyle(m).position, 'fixed', 'micro qui bouge avec la page'); // 09/11/2026 : fixe (avant : absolute dans la visionneuse)
      // 09/11/2026 (décision de Max) : le gros « Fermer la visionneuse » du bas est CACHÉ (gardé pour la voix, le « Fermer »
      // du haut et le retour du téléphone). Avant : attendre(touchable(ui, el('fermer-visionneuse')), '« Fermer la visionneuse » perdu');
      attendre(el('fermer-visionneuse') && el('fermer-visionneuse').hidden && !affiche(ui, el('fermer-visionneuse')), '« Fermer la visionneuse » du bas encore affiché');
    } finally { remettre(); }
  });

  await testAsync('Étape 3b (08/11/2026, FICTIF) : appui simple = une phrase, par le même chemin que le micro du milieu (commandes d’abord, la visionneuse ouverte départage) ; sinon « À trier »', async c => {
    const { el, ui, remettre } = await visionneuseAvecMicro(c);
    const nombre = TACHES.length;
    try {
      const dicter = phrase => { Object.assign(ui.dictee, { disponible: () => true, enCours: () => false, arreter() {}, demarrer(r) { r.surFinal(phrase); if (r.surFin) r.surFin(); } }); el('micro-visionneuse').click(); };
      dicter('stop');
      attendreEgal(el('statut').textContent, 'Dictée arrêtée.', 'commande');
      dicter('passe au suivant');
      attendreEgal(el('statut').textContent, 'J’ai compris « Document suivant », mais je ne sais pas encore le faire.', 'la visionneuse ouverte décide (document, pas morceau)');
      attendreEgal(TACHES.length, nombre, 'tâche créée pour une commande');
      dicter('acheter du pain FICTIF');
      attendre(TACHES.slice(nombre).some(x => x.intitule === 'acheter du pain FICTIF' && x.categorie === 'À trier'), 'pas rangé dans À trier');
      // Pendant l'écoute d'une phrase : le micro se colore (sans surbrillance).
      Object.assign(ui.dictee, { demarrer() {} });
      el('micro-visionneuse').click();
      await pause();
      attendre(el('micro-visionneuse').classList.contains('en-ecoute') && el('micro-visionneuse').getAttribute('aria-pressed') === 'false', 'pas d’état d’écoute');
    } finally { TACHES.slice(nombre).forEach(x => abandonner(x.id)); remettre(); }
  });

  await testAsync('Étape 3b (08/11/2026, FICTIF) : appui long (2 s) = conversation continue, micro en SURBRILLANCE ; le clic qui suit l’appui long ne l’arrête pas ; un toucher l’arrête', async c => {
    const { el, ui, remettre } = await visionneuseAvecMicro(c);
    ui.cadre.contentWindow.matchMedia = q => ({ matches: /reduce/.test(q), addEventListener() {}, removeEventListener() {} });
    try {
      Object.assign(ui.dictee, { disponible: () => true, enCours: () => false, arreter() {}, demarrer() {} });
      const m = el('micro-visionneuse');
      const fondAvant = ui.cadre.contentWindow.getComputedStyle(m).backgroundColor;
      m.dispatchEvent(new Event('pointerdown'));
      const appui = [...c.delais.entries()].find(([, d]) => d.delai === 2000);
      attendre(appui, 'pas d’appui long prévu');
      c.delais.delete(appui[0]);
      appui[1].rappel();
      m.dispatchEvent(new Event('pointerup'));
      await pause();
      attendre(el('microphone').classList.contains('live') && m.getAttribute('aria-pressed') === 'true', 'conversation pas lancée');
      await attendreQue(() => ui.cadre.contentWindow.getComputedStyle(m).backgroundColor === 'rgb(255, 255, 255)' && fondAvant !== 'rgb(255, 255, 255)', 'pas de surbrillance'); // transition douce de 0,9 s
      m.click(); // le clic qui suit l'appui long
      attendre(el('microphone').classList.contains('live'), 'le clic après l’appui long a arrêté la conversation');
      m.click();
      await pause();
      attendre(!el('microphone').classList.contains('live') && m.getAttribute('aria-pressed') === 'false', 'conversation pas arrêtée');
    } finally { remettre(); }
  });

  // ----- 08/11/2026 : VIGNETTES des documents (accord de Max), FICTIF -----
  function visionneuseVignettes(c, { expire = false } = {}) {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const v = fausseVisionneuse();
    const adresses = fausseAdresses();
    const lectures = [];
    const compte = { appeler: async url => { lectures.push(url); if (expire) throw new Error('La connexion du compte Cap a expiré.'); return { blob: async () => new Blob(['document FICTIF']) }; },
      seConnecter: () => { c.redirections.push(new URL('https://accounts.google.com/FICTIF')); } };
    const vis = visionneuseCap0().brancher(ui.doc, { compte, visionneuse: v.charger, urls: adresses, stockage: c.localStorage, maintenant: () => c.maintenant,
      vignette: async () => new Blob(['vignette FICTIVE']) });
    return { ui, el: id => ui.parId(id), v, adresses, lectures, vis };
  }

  await testAsync('Vignettes (08/11/2026, FICTIF) : 45 documents = 40 vignettes légères sur l’eau (3 par rangée, sans nom), chargées une à une, puis « Suivants » ; toucher une vignette ouvre CE document en grand ; « Fermer la visionneuse » ramène aux vignettes ; « Fermer » libère leur mémoire', async c => {
    const { ui, el, v, adresses, vis } = visionneuseVignettes(c);
    attendreEgal(vis.MAX_VIGNETTES, 40, 'plafond');
    const liste = Array.from({ length: 45 }, (_, i) => ({ id: `doc-${i + 1}`, sorte: i % 2 ? 'image' : 'pdf' }));
    await vis.ouvrir(liste);
    attendre(el('vignettes-cap').open && !el('visionneuse-cap').open, 'vignettes pas ouvertes (ou visionneuse ouverte)');
    const boutons = [...el('grille-vignettes').querySelectorAll('button.vignette')];
    attendreEgal(boutons.length, 40, 'nombre de vignettes');
    attendreEgal(boutons.filter(b => b.querySelector('img')).length, 40, 'vignettes pas toutes chargées');
    attendre(boutons.every(b => !b.textContent.trim() && /^Document \d+$/.test(b.getAttribute('aria-label'))), 'un nom ou un texte est montré');
    const r = boutons.slice(0, 4).map(b => b.getBoundingClientRect());
    attendre(Math.abs(r[0].top - r[2].top) < 1 && r[3].top > r[0].bottom && r[0].width >= 90, 'pas 3 vignettes par rangée');
    attendre(!el('suivants-vignettes').hidden && el('suivants-vignettes').textContent === 'Suivants', '« Suivants » absent');
    attendreEgal(el('fermer-vignettes').textContent, 'Fermer', '« Fermer »');
    attendreEgal(v.appels.length, 0, 'un document ouvert en grand sans toucher');
    // Toucher la 3e vignette : CE document en grand, par-dessus.
    boutons[2].click();
    await attendreQue(() => v.appels.length === 1, 'pas ouvert en grand');
    attendre(el('visionneuse-cap').open && el('vignettes-cap').open, 'visionneuse pas par-dessus les vignettes');
    attendreEgal(v.appels[0][2], 'PDF 1.pdf', 'document');
    el('fermer-visionneuse').click();
    attendre(!el('visionneuse-cap').open && el('vignettes-cap').open, 'les vignettes ne reviennent pas');
    // « Suivants » : les 5 derniers.
    const avantSuivants = adresses.liberees.length;
    el('suivants-vignettes').click();
    await attendreQue(() => el('grille-vignettes').querySelectorAll('button.vignette img').length === 5, 'les 5 suivants pas montrés');
    attendre(adresses.liberees.length >= avantSuivants + 40, 'mémoire des 40 premières vignettes pas libérée');
    attendre(el('suivants-vignettes').hidden, '« Suivants » encore là à la fin');
    el('fermer-vignettes').click();
    await attendreQue(() => !el('vignettes-cap').open, 'vignettes pas fermées');
    await attendreQue(() => el('grille-vignettes').children.length === 0, 'grille pas vidée');
    attendre(adresses.liberees.length >= avantSuivants + 45, 'mémoire des vignettes pas libérée');
    void ui;
  });

  await testAsync('Vignettes (08/11/2026, FICTIF) : un seul document s’ouvre directement en grand (pas de vignettes) ; connexion expirée pendant le chargement : message et « Autoriser la lecture du compte Cap »', async c => {
    let x = visionneuseVignettes(c);
    await x.vis.ouvrir([{ id: 'seul' }]);
    attendre(x.el('visionneuse-cap').open && !x.el('vignettes-cap').open && x.v.appels.length === 1, 'un seul document : pas en grand');
    x.el('fermer-visionneuse').click();
    x = visionneuseVignettes(c, { expire: true });
    await x.vis.ouvrir([{ id: 'a' }, { id: 'b' }]);
    attendre(/expiré/.test(x.el('etat-vignettes').textContent) && !x.el('etat-vignettes').hidden && !x.el('autoriser-vignettes').hidden, 'expiration pas dite');
    attendreEgal(x.el('autoriser-vignettes').textContent, 'Autoriser la lecture du compte Cap', 'texte du bouton Google');
    const avant = c.redirections.length;
    x.el('autoriser-vignettes').click();
    attendre(c.redirections.length === avant + 1 && c.localStorage.getItem(visionneuseCap.CLE_RETOUR), 'Google pas ouvert, ou retour pas noté');
  });

  await testAsync('Vignettes (08/11/2026) : une vraie photo FICTIVE de 1200 × 900 devient une vignette JPEG de 360 pixels de large', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const toile = ui.doc.createElement('canvas');
    toile.width = 1200; toile.height = 900;
    toile.getContext('2d').fillRect(0, 0, 1200, 900);
    const grande = await new Promise(ok => toile.toBlob(ok, 'image/png'));
    const petite = await visionneuseCap0().fabriquerVignette(ui.doc, 'image', grande, null);
    attendreEgal(petite.type, 'image/jpeg', 'type');
    const image = await ui.cadre.contentWindow.createImageBitmap(petite);
    attendreEgal([image.width, image.height], [360, 270], 'taille');
    attendre(petite.size < grande.size || petite.size < 60000, 'vignette pas légère');
  });

  // ----- 08/11/2026 : étape 3c (visionneuse à la voix : suivant / précédent, pages, fermer), FICTIF -----
  const TABLEUR_FICTIF_3C = [
    TABLEUR_FICTIF_0[0],
    ['Fermer', '', 'Verbe de fermeture', 'ferme', 'NAV-09', ''],
    ['Fermer', '', 'Mot-clé', 'ça', 'NAV-09', ''],
    ['Document suivant', '', 'Verbe de passage au suivant', 'passe', 'VIS-04', ''],
    ['Document suivant', '', 'Verbe de passage au suivant', 'zappe', 'VIS-04', 'RETIRER 08/11/2026 : FICTIF, jamais lu'],
    ['Document suivant', '', 'Mot-clé', 'le suivant', 'VIS-04', ''],
    ['Document suivant', '', 'Expression complète', 'montre le document suivant', 'VIS-04', ''],
    ['Document précédent', '', 'Verbe de retour au précédent', 'reviens au', 'VIS-05', ''],
    ['Document précédent', '', 'Mot-clé', 'le précédent', 'VIS-05', ''],
    ['Fermer la visionneuse', '', 'Expression complète', 'ferme la visionneuse', 'VIS-06', ''],
    ['Fermer la visionneuse', '', 'Expression complète', 'ferme-la-moi', 'VIS-06', ''],
    ['Pages d’un PDF', '', 'Expression complète', 'page suivante', 'VIS-08', ''],
    ['Pages d’un PDF', '', 'Expression complète', 'page précédente', 'VIS-08', ''],
    ['Pages d’un PDF', '', 'Expression complète', 'tourne la page', 'VIS-08', ''],
    ['Pages d’un PDF', '', 'Expression complète', 'retourne la page', 'VIS-08', ''],
    ['Pages d’un PDF', '', 'Expression complète', 'va à la page [NOMBRE]', 'VIS-08', ''],
    ['Pages d’un PDF', '', 'Expression complète', 'première page', 'VIS-08', ''],
    ['Pages d’un PDF', '', 'Expression complète', 'dernière page', 'VIS-08', ''],
    ['Morceau suivant', '', 'Mot-clé', 'le suivant', 'MUS-12', '']
  ];
  // Fausse page de PDF de la visionneuse (mêmes classes que la page de Zencoder) : « page X sur Y », boutons ‹ ›.
  function faussePagePdf(ui, total) {
    const zone = ui.doc.createElement('div');
    const carte = ui.doc.createElement('div');
    carte.className = 'carte-document';
    const etiquette = ui.doc.createElement('div');
    etiquette.className = 'etiquette-page-pdf';
    let n = 1;
    const montrer = () => { etiquette.textContent = `page ${n} sur ${total}`; };
    const bouton = (classe, d) => { const b = ui.doc.createElement('button'); b.className = `bouton-page-pdf ${classe}`; b.addEventListener('click', () => { if (n + d >= 1 && n + d <= total) { n += d; montrer(); } }); return b; };
    carte.append(etiquette, bouton('bouton-page-precedente', -1), bouton('bouton-page-suivante', 1));
    zone.append(carte);
    montrer();
    return { zone, page: () => n };
  }
  function visionneuse3c(c, nombre) {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const v = fausseVisionneuse();
    const pdf = faussePagePdf(ui, 5);
    const compte = { appeler: async () => ({ blob: async () => new Blob(['document FICTIF']) }), seConnecter() {} };
    const vis = visionneuseCap0().brancher(ui.doc, { compte, visionneuse: v.charger, urls: fausseAdresses(), stockage: c.localStorage,
      vignette: async () => new Blob(['vignette FICTIVE']), pageZencoder: () => pdf.zone });
    commandesVisionneuse.brancher(ui.doc, { visionneuse: () => vis, compte: null });
    const lignes = commandesVocales.analyser(TABLEUR_FICTIF_3C).lignes;
    const dire = phrase => { const d = commandesVocales.deciderMicro(phrase, { lignes, contexte: { ouvert: 'visionneuse' } }); return d ? d.message : null; };
    return { ui, el: id => ui.parId(id), v, vis, pdf, dire, lignes, liste: Array.from({ length: nombre }, (_, i) => ({ id: `doc-${i + 1}` })) };
  }

  test('Étape 3c (08/11/2026, faux tableur bâti comme le vrai) : « le suivant » : visionneuse = document, lecteur = morceau ; pages : suivante, précédente, première, dernière, numéro (dernier dit) ; « zappe » (RETIRER) jamais lu', () => {
    const lignes = commandesVocales.analyser(TABLEUR_FICTIF_3C).lignes;
    const r = (phrase, ouvert = 'visionneuse') => commandesVocales.reconnaitre(phrase, lignes, { ouvert });
    attendreEgal([r('le suivant').code, r('le suivant', 'lecteur').code, r('passe le suivant').code], ['VIS-04', 'MUS-12', 'VIS-04'], 'suivant');
    attendreEgal(r('va à la page, à la page 12').valeurs, { nombre: 12 }, 'hésitation : dernier chiffre');
    attendreEgal([r('page suivante').code, r('tourne la page').code, r('première page').code, r('ferme la visionneuse').code], ['VIS-08', 'VIS-08', 'VIS-08', 'VIS-06'], 'pages et fermer');
    attendre(!lignes.some(l => l.formulation === 'zappe'), 'ligne RETIRER lue');
  });

  await testAsync('Étape 3c (08/11/2026, FICTIF) : vignette touchée, puis « le suivant » / « le précédent » : le document d’à côté en grand (l’ancien est libéré) ; bouts de liste dits ; grille seule : « Touche une vignette »', async c => {
    try {
      const { el, v, vis, dire, liste } = visionneuse3c(c, 5);
      await vis.ouvrir(liste);
      attendreEgal(dire('le suivant'), 'Touche une vignette pour l’ouvrir.', 'grille seule, 5 documents');
      el('grille-vignettes').querySelectorAll('.vignette')[1].click();
      await attendreQue(() => v.appels.filter(x => x[0] === 'montrer').length === 1, 'vignette pas ouverte');
      attendreEgal(dire('le suivant'), 'Document suivant.', 'suivant');
      await attendreQue(() => v.appels.filter(x => x[0] === 'montrer').length === 2, 'suivant pas ouvert');
      attendre(v.appels.some(x => x[0] === 'fermer'), 'ancien document pas fermé');
      attendreEgal(dire('le précédent'), 'Document précédent.', 'précédent');
      attendreEgal(dire('reviens au précédent'), 'Document précédent.', 'précédent encore');
      attendreEgal(dire('le précédent'), 'C’est le premier document.', 'premier');
    } finally { debrancherVision(); }
  });

  await testAsync('Étape 3c (08/11/2026, FICTIF) : pages d’un PDF ouvert, par les boutons ‹ › de la visionneuse : suivante, numéro, dernière, première ; hors limites dit ; aucun PDF ouvert : dit', async c => {
    try {
      const { el, v, vis, pdf, dire, liste } = visionneuse3c(c, 3);
      attendreEgal(dire('page suivante'), 'Aucun PDF n’est ouvert.', 'rien d’ouvert');
      await vis.ouvrir(liste);
      el('grille-vignettes').querySelector('.vignette').click();
      await attendreQue(() => v.appels.length >= 1, 'pas ouvert');
      attendreEgal([dire('page suivante'), pdf.page()], ['Page 2.', 2], 'suivante');
      attendreEgal([dire('va à la page 4'), pdf.page()], ['Page 4.', 4], 'numéro');
      attendreEgal([dire('dernière page'), pdf.page()], ['Page 5.', 5], 'dernière');
      attendreEgal(dire('tourne la page'), 'C’est déjà la dernière page.', 'au bout');
      attendreEgal([dire('retourne la page'), pdf.page()], ['Page 4.', 4], 'précédente');
      attendreEgal([dire('première page'), pdf.page()], ['Page 1.', 1], 'première');
      attendreEgal(dire('va à la page 9'), 'Ce PDF n’a que 5 pages.', 'trop loin');
    } finally { debrancherVision(); }
  });

  await testAsync('Étape 3c (08/11/2026, FICTIF) : « ferme la visionneuse » : d’abord le document (retour aux vignettes), puis les vignettes ; « ferme » seul fait pareil ; grille de 45 : « le suivant » = 40 vignettes suivantes', async c => {
    const avant = visionneuseCap.instance;
    try {
      const { el, v, vis, dire, liste } = visionneuse3c(c, 3);
      visionneuseCap.instance = vis;
      commandesNavigation.brancher(el('ecran-micro').ownerDocument, { geste: () => null });
      await vis.ouvrir(liste);
      el('grille-vignettes').querySelector('.vignette').click();
      await attendreQue(() => el('visionneuse-cap').open, 'pas ouvert');
      attendreEgal(dire('ferme la visionneuse'), 'Je ferme le document : voici les vignettes.', 'fermer le document');
      attendre(!el('visionneuse-cap').open && el('vignettes-cap').open, 'pas revenu aux vignettes');
      attendreEgal(dire('ferme'), 'Je ferme les documents.', '« ferme » seul : les vignettes');
      await attendreQue(() => !el('vignettes-cap').open, 'vignettes pas fermées');
      attendreEgal(dire('ferme-la-moi'), 'La visionneuse n’est pas ouverte.', 'plus rien');
      void v;
      const grand = visionneuse3c(c, 45);
      await grand.vis.ouvrir(grand.liste);
      attendreEgal(grand.dire('le suivant'), 'Vignettes suivantes.', '40 suivantes');
      await attendreQue(() => grand.el('grille-vignettes').querySelectorAll('.vignette').length === 5, 'pas les 5 dernières');
      attendreEgal(grand.dire('le précédent'), 'Vignettes précédentes.', '40 précédentes');
    } finally {
      visionneuseCap.instance = avant;
      debrancherVision();
      for (const code of ['NAV-01', 'NAV-02', 'NAV-03', 'NAV-04', 'NAV-07', 'NAV-08', 'NAV-09', 'NAV-10', 'NAV-11', 'NAV-13', 'NAV-21', 'NAV-22', 'NAV-24', ...Object.keys(commandesNavigation.PAS_PRET)]) commandesVocales.brancherAction(code, undefined);
    }
  });

  // ----- 08/11/2026 : petit micro sur l'écran des vignettes (accord de Max), FICTIF -----
  async function grilleAvecMicro(c, nombre = 45) {
    const cle = commandesVocales.CLE_COPIE;
    const avantCopie = localStorage.getItem(cle);
    localStorage.setItem(cle, JSON.stringify({ lu_le: new Date(0).toISOString(), compte: {}, lignes: commandesVocales.analyser(TABLEUR_FICTIF_3C).lignes }));
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    brancherAccueil(c, ui); // 09/11/2026 : pose le petit micro de tous les écrans dans la fenêtre du dessus
    const v = fausseVisionneuse();
    const adresses = fausseAdresses();
    const compte = { appeler: async () => ({ blob: async () => new Blob(['document FICTIF']) }), seConnecter() {} };
    const vis = visionneuseCap0().brancher(ui.doc, { compte, visionneuse: v.charger, urls: adresses, stockage: c.localStorage, vignette: async () => new Blob(['vignette FICTIVE']) });
    commandesVisionneuse.brancher(ui.doc, { visionneuse: () => vis, compte: null });
    const avantInstance = visionneuseCap.instance;
    visionneuseCap.instance = vis;
    commandesNavigation.brancher(ui.doc, { geste: () => null });
    await vis.ouvrir(Array.from({ length: nombre }, (_, i) => ({ id: `doc-${i + 1}` })));
    const remettre = () => {
      visionneuseCap.instance = avantInstance;
      if (avantCopie === null) localStorage.removeItem(cle); else localStorage.setItem(cle, avantCopie);
      for (let i = 1; i <= 8; i++) commandesVocales.brancherAction(`VIS-0${i}`, undefined);
      for (const code of ['NAV-01', 'NAV-02', 'NAV-03', 'NAV-04', 'NAV-07', 'NAV-08', 'NAV-09', 'NAV-10', 'NAV-11', 'NAV-13', 'NAV-21', 'NAV-22', 'NAV-24', ...Object.keys(commandesNavigation.PAS_PRET)]) commandesVocales.brancherAction(code, undefined);
    };
    const dicter = phrase => { Object.assign(ui.dictee, { disponible: () => true, enCours: () => false, arreter() {}, demarrer(r) { r.surFinal(phrase); if (r.surFin) r.surFin(); } }); ui.parId('micro-vignettes').click(); return ui.parId('statut').textContent; };
    return { ui, el: id => ui.parId(id), v, adresses, vis, dicter, remettre };
  }
  const seCoupent = (a, b) => a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom;

  await testAsync('Micro des vignettes (08/11/2026) : en haut à droite, FIXE, icône seule, touchable ; il ne cache AUCUNE vignette, même en faisant défiler la grille', async c => {
    const { ui, el, remettre } = await grilleAvecMicro(c, 45);
    try {
      el('vignettes-cap').classList.remove('choix-entree'); // mesures APRÈS la sortie du sable (figée au début dans le navigateur de test)
      await pause();
      // 09/11/2026 : le petit micro de TOUS les écrans remplace celui des vignettes (caché). Avant : const m = el('micro-vignettes');
      attendre(el('micro-vignettes').hidden, 'ancien micro des vignettes encore affiché');
      const m = el('petit-micro');
      attendre(el('vignettes-cap').contains(m) && !m.textContent.trim() && m.getAttribute('aria-label'), 'micro absent, ou avec un mot');
      attendreEgal(ui.cadre.contentWindow.getComputedStyle(m).position, 'fixed', 'micro qui défile avec la grille');
      const boite = () => m.getBoundingClientRect();
      attendre(boite().right >= 412 - 20 && boite().top < 160, `micro mal placé : ${JSON.stringify(boite())}`);
      attendre(touchable(ui, m), 'micro pas touchable');
      const fenetre = el('vignettes-cap');
      for (const defilement of [0, 300, 900, 5000]) {
        fenetre.scrollTop = defilement;
        const cachees = [...el('grille-vignettes').querySelectorAll('.vignette')].filter(v => seCoupent(v.getBoundingClientRect(), boite()));
        attendreEgal(cachees.length, 0, `vignette sous le micro (défilement ${defilement})`);
        attendre(!seCoupent(el('fermer-vignettes').getBoundingClientRect(), boite()) && !seCoupent(el('suivants-vignettes').getBoundingClientRect(), boite()), `bouton sous le micro (défilement ${defilement})`);
      }
    } finally { remettre(); }
  });

  await testAsync('Micro des vignettes (08/11/2026, FICTIF) : « le suivant » / « le précédent » = 40 vignettes d’après / d’avant ; « ferme » ferme les vignettes ; une phrase de dictée va dans « À trier » ; la mémoire ne grossit pas', async c => {
    const { el, adresses, dicter, remettre } = await grilleAvecMicro(c, 45);
    const nombre = TACHES.length;
    try {
      for (let tour = 0; tour < 3; tour++) {
        attendreEgal(dicter('le suivant'), 'Vignettes suivantes.', 'suivant');
        await attendreQue(() => el('grille-vignettes').querySelectorAll('.vignette img').length === 5, 'les 5 dernières pas montrées');
        attendreEgal(dicter('le précédent'), 'Vignettes précédentes.', 'précédent');
        await attendreQue(() => el('grille-vignettes').querySelectorAll('.vignette img').length === 40, 'les 40 premières pas montrées');
        attendre(adresses.faites.length - adresses.liberees.length <= 40, `mémoire qui grossit : ${adresses.faites.length - adresses.liberees.length} vignettes gardées`);
      }
      dicter('acheter du pain FICTIF');
      attendre(TACHES.slice(nombre).some(x => x.intitule === 'acheter du pain FICTIF' && x.categorie === 'À trier'), 'dictée pas rangée dans À trier');
      attendreEgal(dicter('ferme'), 'Je ferme les documents.', 'ferme');
      await attendreQue(() => !el('vignettes-cap').open, 'vignettes pas fermées');
    } finally { TACHES.slice(nombre).forEach(x => abandonner(x.id)); remettre(); }
  });

  // ----- 09/11/2026 : défauts vus par Max sur c72 (accueil, eau, Cap muet dans la visionneuse), FICTIF -----
  const TABLEUR_FICTIF_C73 = [...TABLEUR_FICTIF_3C, ...TABLEUR_FICTIF_1.slice(1).filter(l => ['NAV-07', 'NAV-08'].includes(l[4]))];
  async function grilleC73(c, essai) {
    const g = await grilleAvecMicro(c, 3);
    const cle = commandesVocales.CLE_COPIE;
    localStorage.setItem(cle, JSON.stringify({ lu_le: new Date(0).toISOString(), compte: {}, lignes: commandesVocales.analyser(TABLEUR_FICTIF_C73).lignes }));
    const nombre = TACHES.length;
    const signe = () => (g.el('signe-micro').hidden ? '' : (g.el('signe-micro').classList.contains('signe-pouce-visible') ? 'pouce' : 'croix'));
    const dire = phrase => { g.el('signe-micro').hidden = true; Object.assign(g.ui.dictee, { disponible: () => true, enCours: () => false, arreter() {}, demarrer(r) { r.surFinal(phrase); if (r.surFin) r.surFin(); } }); g.el('petit-micro').click(); return g.el('statut').textContent; };
    try { await essai({ ...g, signe, dire }); } finally { TACHES.slice(nombre).forEach(x => abandonner(x.id)); g.remettre(); }
  }

  await testAsync('Défauts 2 et 3 (09/11/2026, vus par Max sur c72, FICTIF) : document ouvert depuis les vignettes : « reviens à l’accueil » FERME la visionneuse et les vignettes (on voit l’accueil), pouce ; « remets-moi l’eau seule » aussi, et l’eau revient', async c => {
    await grilleC73(c, async ({ el, vis, signe, dire, adresses }) => {
      el('grille-vignettes').querySelector('.vignette').click();
      await attendreQue(() => el('visionneuse-cap').open, 'document pas ouvert');
      attendreEgal(dire('reviens à l’accueil'), 'Retour à l’accueil.', 'réponse');
      await attendreQue(() => !el('visionneuse-cap').open && !el('vignettes-cap').open, 'visionneuse ou vignettes encore par-dessus l’accueil');
      attendreEgal(signe(), 'pouce', 'signe');
      attendre(adresses.faites.length === adresses.liberees.length, 'mémoire pas libérée');
      await vis.ouvrir([{ id: 'doc-1' }, { id: 'doc-2' }]);
      attendre(el('vignettes-cap').open, 'vignettes pas rouvertes');
      let eau = 0;
      el('aller-eau').addEventListener('click', () => { eau++; }); // l'écran d'eau lui-même est testé à part
      attendreEgal(dire('remets-moi l’eau seule'), 'Retour à l’eau.', 'réponse eau');
      await attendreQue(() => !el('vignettes-cap').open, 'vignettes encore par-dessus l’eau');
      attendreEgal(eau, 1, 'bouton de l’eau pas touché');
    });
  });

  await testAsync('Défauts 4 et 5 (09/11/2026, vus par Max sur c72, FICTIF) : vignettes ouvertes (et un document par-dessus) : une phrase rangée dans « À trier » reçoit son POUCE, une commande sa réponse ; Cap n’est plus jamais muet ; la fenêtre de gros choix (vraie question) reste sans signe', async c => {
    await grilleC73(c, async ({ el, signe, dire }) => {
      dire('acheter du pain FICTIF');
      attendreEgal(signe(), 'pouce', 'vignettes ouvertes : phrase rangée sans signe');
      el('grille-vignettes').querySelector('.vignette').click();
      await attendreQue(() => el('visionneuse-cap').open, 'document pas ouvert');
      dire('allume le grille-pain FICTIF');
      attendreEgal(signe(), 'pouce', 'document ouvert : phrase rangée sans signe');
    });
  });

  await testAsync('Défaut 1 (09/11/2026, vu par Max sur c72) : une commande qui ne fait rien (« … déjà … ») montre la CROIX et la phrase, jamais un pouce sans effet ; « afficher le lecteur » déjà affiché le dit', async c => {
    await interfaceCommandes1(c, async ({ ui, el, dicter }) => {
      el('ouvrir-chercher').click();
      transitionEcrans.terminer(ui.doc);
      el('signe-micro').hidden = true;
      attendreEgal(dicter('chercher'), 'Chercher est déjà ouvert.', 'réponse');
      attendre(!el('signe-micro').hidden && el('signe-micro').classList.contains('signe-croix-visible'), 'pas la croix pour « déjà ouvert »');
    });
    attendre(/Le lecteur est déjà affiché\./.test(SOURCE_RELATIONS_MP3_TEST_C73), 'message « déjà affiché » absent');
  });

  await testAsync('Visionneuse VIDE (09/11/2026, décision de Max, FAUX Drive) : aucun PDF : la visionneuse s’ouvre SANS aucun texte (ni « Aucun PDF », ni « aucun fichier charge ») ; « Choisir un fichier » en haut à gauche ; le petit livre et le petit micro en haut à droite', async c => {
    const f = fauxDriveCompteCap(c);
    const { m } = connecterCompteFictif(c);
    m.enregistrerAdresse(COMPTE_CAP_FICTIF);
    f.ajouter('Relations', 'application/vnd.google-apps.folder', 'root');
    const v = fausseVisionneuse();
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    brancherAccueil(c, ui);
    const el = id => ui.parId(id);
    const vis = visionneuseCap0().brancher(ui.doc, { compte: m, visionneuse: v.charger, urls: fausseAdresses(), stockage: c.localStorage, vignette: async () => new Blob(['vignette FICTIVE']) });
    relationsCompte0().brancher(ui.doc, { compte: m, pdfjs: async () => { throw new Error('ancien lecteur'); }, visionneuse: () => vis, stockage: c.localStorage, maintenant: () => c.maintenant });
    el('ouvrir-oeil').click();
    await attendreQue(() => el('visionneuse-cap').open && !el('etat-visionneuse').classList.contains('en-lecture'), 'visionneuse pas ouverte');
    await pause();
    attendre(el('etat-visionneuse').hidden && !el('etat-visionneuse').textContent, `texte dans la visionneuse vide : ${el('etat-visionneuse').textContent}`);
    attendre(el('autoriser-visionneuse').hidden, 'bouton Google montré');
    attendre(el('visionneuse-cap').contains(el('petit-micro')) && el('visionneuse-cap').contains(el('bouton-apprendre')), 'petit micro ou petit livre absent');
    // Les retouches posées dans la page de Zencoder (affichage seul).
    const page = ui.doc.implementation.createHTMLDocument('FICTIF');
    visionneuseCap.retoucherVisionneuse(page);
    const regles = page.getElementById('retouches-cap').textContent;
    attendre(/#titre-fichier \{ display: none !important; \}/.test(regles), '« aucun fichier charge » encore visible');
    attendre(/#bouton-choisir \{ position: fixed !important; top: 12px !important; left: 12px !important;/.test(regles), '« Choisir un fichier » pas en haut à gauche');
  });

  // ----- 09/11/2026 (décision de Max, bloc c74) : répondre par le RANG dans toutes les fenêtres de choix, FICTIF -----
  test('Rang dans un choix (09/11/2026, bloc c74) : « numéro 1 / un », « le premier », « la première », « le deuxième », « la seconde », « le 3e », « 1er », « d’eux »… ; mais « la première page », « un autre morceau » ne sont PAS des rangs', () => {
    const cas = { 'numéro 1': 1, 'numéro un': 1, 'Numéro un.': 1, 'le premier': 1, 'la première': 1, 'premier': 1, '1er': 1, 'le 1er': 1, 'la 1re': 1, 'la 1ère': 1,
      'le deuxième': 2, 'la deuxième': 2, 'le second': 2, 'la seconde': 2, 'le 2e': 2, 'la 2ème': 2, 'numéro 2': 2, 'n° 2': 2, 'deux': 2, 'de': 2, 'd’eux': 2,
      'c’est le troisième': 3, 'je prends la troisième': 3, 'le numéro trois': 3, '3': 3, 'la quatrième': 4, 'le dixième': 10, 'numéro 12': 12, 'le dix-septième': 17 };
    for (const [phrase, n] of Object.entries(cas)) attendreEgal(numeroChoix.rang(phrase), n, phrase);
    for (const phrase of ['la première page', 'un autre morceau', 'mets la zik', 'ouvre la boîte fictive', '', 'oui', 'redire', 'le dernier', 'numéro']) attendreEgal(numeroChoix.rang(phrase), null, `« ${phrase} » lu comme un rang`);
  });

  await testAsync('Rang dans un choix (09/11/2026, bloc c74, FICTIF) : fenêtre des VIGNETTES (3 documents) : « la deuxième » touche la 2e vignette (pouce) ; « numéro 7 » : « Il n’y a que 3 choix » (croix), rien touché', async c => {
    await grilleC73(c, async ({ el, signe, dire }) => {
      const vignettes = [...el('grille-vignettes').querySelectorAll('.vignette')];
      attendreEgal(vignettes.length, 3, 'vignettes');
      const touchees = [];
      vignettes.forEach((v, i) => v.addEventListener('click', () => touchees.push(i + 1)));
      dire('numéro 7');
      attendreEgal(touchees, [], 'touchée hors limite');
      attendre(/Il n’y a que 3 choix/.test(el('statut').textContent) && signe() === 'croix', `hors limite : ${el('statut').textContent} ${signe()}`);
      dire('la deuxième');
      attendreEgal(touchees, [2], 'pas la 2e vignette');
      attendreEgal(signe(), 'pouce', 'signe');
      await attendreQue(() => el('visionneuse-cap').open, 'document pas ouvert');
    });
  });

  test('Rang dans un choix (09/11/2026, bloc c74) : chaque fenêtre de choix existe avec sa liste de propositions (musique, choix de la voix, vignettes, date, émetteur du scan, annuaire)', () => {
    const page = new DOMParser().parseFromString(SOURCE_INDEX_C74, 'text/html');
    for (const [fenetre, liste] of [['choix-voix', 'liste-choix-voix'], ['musique-relations', 'liste-musique-relations'], ['vignettes-cap', 'grille-vignettes'], ['question-date', 'choix-question-date'], ['scanner-choix-emetteur', 'scanner-choix-emetteur-cases'], ['commande-annuaire', 'commande-annuaire-corps'], ['choix-commande', 'liste-choix-commande']]) {
      const f = page.getElementById(fenetre);
      attendre(f && f.tagName === 'DIALOG' && f.querySelector(`#${liste}`), `${fenetre} ou ${liste} absent`);
    }
  });

  await testAsync('Micro des vignettes (08/11/2026, FICTIF) : appui long = conversation, surbrillance ; document ouvert depuis la grille : le micro de la visionneuse prend la place, au même endroit, sans doublon touchable', async c => {
    const { ui, el, v, remettre } = await grilleAvecMicro(c, 6);
    try {
      Object.assign(ui.dictee, { disponible: () => true, enCours: () => false, arreter() {}, demarrer() {} });
      const m = el('micro-vignettes');
      m.dispatchEvent(new Event('pointerdown'));
      const appui = [...c.delais.entries()].find(([, d]) => d.delai === 2000);
      attendre(appui, 'pas d’appui long prévu');
      c.delais.delete(appui[0]);
      appui[1].rappel();
      m.dispatchEvent(new Event('pointerup'));
      await pause();
      attendre(el('microphone').classList.contains('live') && m.getAttribute('aria-pressed') === 'true', 'conversation pas lancée en surbrillance');
      m.click(); m.click();
      await pause();
      attendre(!el('microphone').classList.contains('live'), 'conversation pas arrêtée');
      // Document ouvert depuis la grille.
      // 09/11/2026 : UN SEUL petit micro : sur la grille, puis dans la visionneuse (même endroit), puis de retour sur la
      // grille. Avant : micro de la visionneuse et micro des vignettes, deux boutons au même endroit.
      const petit = el('petit-micro');
      await pause();
      const avant = petit.getBoundingClientRect();
      attendre(el('vignettes-cap').contains(petit) && touchable(ui, petit), 'petit micro pas sur la grille');
      el('grille-vignettes').querySelector('.vignette').click();
      await attendreQue(() => el('visionneuse-cap').open && v.appels.length >= 1, 'document pas ouvert');
      await pause();
      const r = petit.getBoundingClientRect();
      attendre(el('visionneuse-cap').contains(petit) && touchable(ui, petit), 'le petit micro n’est pas celui qu’on touche dans la visionneuse');
      attendre(Math.abs(avant.top - r.top) < 2 && Math.abs(avant.right - r.right) < 2, 'le petit micro a bougé');
      el('fermer-visionneuse').click();
      await pause();
      attendre(el('vignettes-cap').contains(petit) && touchable(ui, petit), 'petit micro pas revenu sur la grille');
    } finally { remettre(); }
  });

  // ----- 09/11/2026 : écran CHERCHER repris de la maquette de Zencoder (accord de Max), FICTIF -----
  const seCroisent = (a, b) => a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom;

  await testAsync('Écran Chercher (09/11/2026) : 4 icônes 2 × 2 sans texte (To-do, Documents, Média, Photo), barre, « Fermer » VISIBLE ; Photo GRISÉ (le dit, n’ouvre rien) ; pas de lumière de bord ; tout touchable, rien ne se chevauche, même avec l’alerte', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    brancherAccueil(c, ui);
    const el = id => ui.parId(id);
    el('ouvrir-chercher').click();
    transitionEcrans.terminer(ui.doc);
    attendre(!el('ecran-chercher').hidden && el('ecran-complet').hidden && ui.doc.documentElement.classList.contains('ecran-cap-ouvert'), 'écran Chercher pas ouvert (ou écran des tâches ouvert)');
    const icones = ['chercher-todo', 'chercher-documents', 'chercher-media', 'chercher-photo'].map(el);
    attendre(icones.every(b => b.querySelector('svg') && !b.querySelector('span:not(.visuellement-cache)') && b.closest('.grille-chercher')), 'icônes : pas seules, ou du texte visible');
    attendreEgal(icones.map(b => b.querySelector('.visuellement-cache').textContent), ['To-do', 'Documents', 'Média', 'Photo (pas encore prêt)'], 'noms lus par le téléphone');
    const r = icones.map(b => b.getBoundingClientRect());
    attendre(Math.abs(r[0].top - r[1].top) < 1 && Math.abs(r[2].top - r[3].top) < 1 && r[2].top > r[0].bottom && Math.abs(r[0].width - r[3].width) < 1 && r[0].width >= 80, `pas une grille 2 × 2 de grosses icônes identiques : ${JSON.stringify(r.map(x => [x.left, x.top, x.width]))}`);
    attendre(el('chercher-photo').classList.contains('bouton-pas-pret') && el('chercher-photo').getAttribute('aria-disabled') === 'true', 'Photo pas grisé');
    attendreEgal(Number(ui.cadre.contentWindow.getComputedStyle(el('chercher-photo')).opacity), 0.35, 'Photo pas grisé comme Notes et Agenda');
    attendreEgal(el('fermer-chercher-cap').textContent, 'Fermer', 'texte de « Fermer »');
    // 09/11/2026 (après l'essai c58) : « Fermer » CACHÉ, le geste suffit. Avant : visible (première décision de Max).
    attendre(el('fermer-chercher-cap').hidden && !affiche(ui, el('fermer-chercher-cap')), '« Fermer » encore affiché');
    attendreEgal(el('chercher-champ').getAttribute('placeholder'), 'Chercher', 'texte de la barre');
    attendre(!/FICTIF/.test(el('ecran-chercher').textContent + el('chercher-champ').getAttribute('placeholder')), 'étiquette de maquette affichée');
    attendre(!ui.doc.getElementById('lumiere-bord') && !el('ecran-chercher').querySelector('[class*="lumiere"]'), 'lumière de bord reprise (étape 3, pas maintenant)');
    const tous = [...icones, el('chercher-champ')]; // 09/11/2026 : sans « Fermer » (caché)
    for (const b of tous) attendre(touchable(ui, b), `${b.id} pas touchable`);
    for (let i = 0; i < tous.length; i++) for (let j = i + 1; j < tous.length; j++) attendre(!seCroisent(tous[i].getBoundingClientRect(), tous[j].getBoundingClientRect()), `${tous[i].id} chevauche ${tous[j].id}`);
    // Photo : le dit, n'ouvre rien.
    el('chercher-photo').click();
    attendre(!el('message-chercher').hidden && el('message-chercher').textContent === 'Photo : pas encore prêt.', 'Photo ne dit rien');
    attendre(!ui.doc.querySelector('dialog[open]') && !el('ecran-chercher').hidden, 'Photo a ouvert quelque chose');
    // Alerte Google affichée : tout reste visible et touchable.
    el('texte-alerte-google').textContent = 'Connexion à Google à refaire (FICTIF).';
    el('alerte-google').hidden = false;
    await pause();
    transitionEcrans.terminer(ui.doc);
    for (const b of [...tous, el('redonner-acces-google')]) attendre(touchable(ui, b), `${b.id} caché par l’alerte`);
    el('alerte-google').hidden = true;
    // « Fermer » : retour à l'accueil, message effacé à la prochaine ouverture.
    el('fermer-chercher-cap').click();
    transitionEcrans.terminer(ui.doc);
    attendre(el('ecran-chercher').hidden && touchable(ui, el('ouvrir-chercher')), 'accueil pas revenu');
    el('ouvrir-chercher').click();
    attendre(el('message-chercher').hidden, 'ancien message encore là');
  });

  await testAsync('Écran Chercher (09/11/2026, FICTIF) : To-do = l’écran des tâches ; Documents = l’œil (visionneuse) ; Média = le Lecteur (musique), une fois chacun, jamais en double ; la barre : Entrée = recherche de Cap dans les tâches, résultats, barre vidée', async c => {
    const nombre = TACHES.length;
    try {
      const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
      brancherAccueil(c, ui);
      const el = id => ui.parId(id);
      const touches = { oeil: 0, lecteur: 0 };
      el('ouvrir-oeil').addEventListener('click', () => { touches.oeil++; });
      el('ouvrir-lecteur').addEventListener('click', () => { touches.lecteur++; });
      el('ouvrir-chercher').click();
      el('chercher-documents').click();
      attendreEgal(touches, { oeil: 1, lecteur: 0 }, 'Documents ne touche pas l’œil (une fois)');
      el('chercher-media').click();
      attendreEgal(touches, { oeil: 1, lecteur: 1 }, 'Média ne touche pas le Lecteur (une fois)');
      el('chercher-photo').click();
      attendreEgal(touches, { oeil: 1, lecteur: 1 }, 'Photo a touché quelque chose');
      // To-do : l'écran des tâches, Chercher fermé.
      el('chercher-todo').click();
      transitionEcrans.terminer(ui.doc);
      attendre(!el('ecran-complet').hidden && !el('zone-recherche').hidden && el('ecran-chercher').hidden && !ui.doc.documentElement.classList.contains('ecran-cap-ouvert'), 'To-do : écran des tâches pas ouvert proprement');
      el('fermer-chercher').click();
      transitionEcrans.terminer(ui.doc);
      // 09/11/2026 (règle du retour) : les tâches reviennent à Chercher (avant : à l'accueil), puis Chercher à l'accueil.
      attendre(el('ecran-complet').hidden && !el('ecran-chercher').hidden, 'les tâches ne reviennent pas à Chercher');
      el('fermer-chercher-cap').click();
      transitionEcrans.terminer(ui.doc);
      attendre(el('ecran-complet').hidden && touchable(ui, el('ouvrir-chercher')), 'retour à l’accueil depuis les tâches');
      // La barre : une tâche FICTIVE retrouvée par la recherche de Cap.
      c.TACHES.push({ ...TACHES_FICTIVES[0], id: 'FICTIF-chercher', intitule: 'Racheter des piles FICTIF chercher', fait: false, abandonnee_le: '' }); // tâches de la page essayée
      el('ouvrir-chercher').click();
      transitionEcrans.terminer(ui.doc);
      const champ = el('chercher-champ');
      champ.value = 'piles FICTIF';
      champ.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
      transitionEcrans.terminer(ui.doc);
      attendre(!el('ecran-complet').hidden && el('ecran-chercher').hidden, 'Entrée : écran des tâches pas ouvert');
      attendreEgal(el('saisie-recherche').value, 'piles FICTIF', 'texte pas passé à la recherche de Cap');
      attendre(!el('resultats-recherche').hidden && [...el('resultats-recherche').querySelectorAll('.resultat-recherche')].some(b => b.textContent.includes('Racheter des piles FICTIF chercher')), 'résultat pas montré');
      attendreEgal(champ.value, '', 'barre de Chercher pas vidée');
      // Une autre touche que Entrée : rien ne part.
      el('fermer-chercher').click();
      el('ouvrir-chercher').click();
      champ.value = 'x';
      champ.dispatchEvent(new KeyboardEvent('keydown', { key: 'a', bubbles: true }));
      attendre(!el('ecran-chercher').hidden && el('ecran-complet').hidden, 'une lettre a lancé la recherche');
      el('fermer-chercher-cap').click();
      attendreEgal(champ.value, '', '« Fermer » ne vide pas la barre');
    } finally { TACHES.slice(nombre).forEach(x => abandonner(x.id)); }
  });

  await testAsync('Écran Chercher (09/11/2026) : geste de HAUT EN BAS = Chercher se ferme en douceur (son « Fermer ») ; geste sur la barre : rien ; le geste vers l’eau reste pour l’accueil seul ; animations réduites : tout d’un coup', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    let retours = 0;
    const { module } = brancherAccueil(c, ui);
    void module;
    ui.parId('aller-eau').addEventListener('click', () => { retours++; });
    const temps = { t: 0 };
    brancherGesteRetour(c, ui, temps);
    const el = id => ui.parId(id);
    el('ouvrir-chercher').click();
    transitionEcrans.terminer(ui.doc);
    // Sur la barre (champ) : jamais de fermeture.
    glisserRetour(ui, temps, el('chercher-champ'), [200, 400, 200, 800]);
    attendre(!el('ecran-chercher').hidden, 'geste parti de la barre a fermé Chercher');
    glisserRetour(ui, temps, el('ecran-chercher'), [200, 150, 200, 600]);
    attendre(el('ecran-chercher').classList.contains('geste-retour-sortie'), 'pas de sortie douce');
    await attendreQue(() => el('ecran-chercher').hidden, 'Chercher pas fermé par le geste');
    attendreEgal(retours, 0, 'le geste sur Chercher a ramené à l’eau');
    transitionEcrans.terminer(ui.doc);
    attendre(touchable(ui, el('ouvrir-chercher')), 'accueil pas revenu');
    // Animations réduites : Chercher et To-do d'un coup.
    ui.cadre.contentWindow.matchMedia = q => ({ matches: /reduce/.test(q), addEventListener() {}, removeEventListener() {} });
    el('ouvrir-chercher').click();
    attendre(!ui.doc.querySelector('.ecran-part, .ecran-entree, .ecran-entree-directe') && affiche(ui, el('ecran-chercher')), 'Chercher : transition malgré les animations réduites');
    el('chercher-todo').click();
    attendre(!ui.doc.querySelector('.ecran-part, .ecran-entree, .ecran-entree-directe') && affiche(ui, el('ecran-complet')) && !affiche(ui, el('ecran-chercher')), 'To-do : transition malgré les animations réduites');
  });

  // Faux tableur bâti comme le vrai (avec une ligne RETIRER, jamais lue).
  const TABLEUR_FICTIF_CHERCHER = [
    ...TABLEUR_FICTIF_1,
    ['Navigation', '', 'Écran cible', 'la loupe fictive', 'NAV-01', 'RETIRER 09/11/2026 : FICTIF, jamais lu']
  ];
  await testAsync('Commande vocale NAV-01 / NAV-13 (09/11/2026, faux tableur FICTIF avec RETIRER) : « ouvre chercher » depuis l’accueil, Autre, Réglages, l’écran Micro et l’écran des tâches = l’écran Chercher, un seul écran ouvert ; « mes tâches » = l’écran des tâches ; ligne RETIRER jamais lue', async c => {
    const cle = commandesVocales.CLE_COPIE;
    const avantCopie = localStorage.getItem(cle);
    const lignes = commandesVocales.analyser(TABLEUR_FICTIF_CHERCHER).lignes;
    localStorage.setItem(cle, JSON.stringify({ lu_le: new Date(0).toISOString(), compte: {}, lignes }));
    const nombre = TACHES.length;
    try {
      attendre(!lignes.some(l => l.formulation === 'la loupe fictive'), 'ligne RETIRER lue');
      const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
      brancherAccueil(c, ui);
      const temps = { t: 0 };
      const g = brancherGesteRetour(c, ui, temps);
      commandesNavigation.brancher(ui.doc, { geste: () => g });
      const el = id => ui.parId(id);
      const dicter = phrase => {
        Object.assign(ui.dictee, { disponible: () => true, enCours: () => false, arreter() {}, demarrer(r) { r.surFinal(phrase); if (r.surFin) r.surFin(); } });
        parlerAuGrosMicro(el('microphone')); // 09/11/2026 : deux touchers
        return el('statut').textContent;
      };
      const seulChercher = () => ['ecran-autre', 'ecran-reglages', 'ecran-micro'].every(id => el(id).hidden) && !el('ecran-chercher').hidden && el('ecran-complet').hidden;
      for (const depart of ['', 'ouvrir-autre', 'ouvrir-reglages-cap', 'tâches']) { // 09/11/2026 : sans l'écran Micro (retiré)
        if (depart === 'tâches') { el('ouvrir-chercher').click(); el('chercher-todo').click(); } else if (depart) el(depart).click();
        transitionEcrans.terminer(ui.doc);
        // 09/11/2026 : plus d'écran Micro : la phrase est dite au gros micro (avant : el('ouvrir-micro').click()).
        if (depart && depart !== 'ouvrir-micro') { /* l'écran de départ est remplacé par l'écran Micro, comme au doigt */ }
        transitionEcrans.terminer(ui.doc);
        attendreEgal(dicter('ouvre chercher'), 'J’ouvre Chercher.', `réponse (départ ${depart || 'accueil'})`);
        transitionEcrans.terminer(ui.doc);
        attendre(seulChercher(), `pas l’écran Chercher seul (départ ${depart || 'accueil'})`);
        el('fermer-chercher-cap').click();
        transitionEcrans.terminer(ui.doc);
      }
      // Depuis l'écran des tâches, sans passer par l'écran Micro : la commande ferme d'abord les tâches.
      el('ouvrir-chercher').click();
      el('chercher-todo').click();
      transitionEcrans.terminer(ui.doc);
      attendreEgal(commandesVocales.reconnaitre('ouvre chercher', lignes, {}).code, 'NAV-01', 'NAV-01 reconnu');
      el('fermer-chercher').click(); // l'écran Micro s'ouvre depuis l'accueil
      transitionEcrans.terminer(ui.doc);
      // 09/11/2026 : plus d'écran Micro (avant : el('ouvrir-micro').click()).
      transitionEcrans.terminer(ui.doc);
      attendreEgal(dicter('ouvre mes tâches'), 'J’ouvre tes tâches.', 'mes tâches');
      transitionEcrans.terminer(ui.doc);
      attendre(!el('ecran-complet').hidden && el('ecran-chercher').hidden && el('ecran-micro').hidden, 'tâches pas ouvertes seules');
      attendre(!commandesVocales.reconnaitre('ouvre la loupe fictive', lignes, {}).code, 'formulation RETIRER reconnue');
      attendreEgal(TACHES.length, nombre, 'une commande a créé une tâche');
    } finally {
      TACHES.slice(nombre).forEach(x => abandonner(x.id));
      if (avantCopie === null) localStorage.removeItem(cle); else localStorage.setItem(cle, avantCopie);
      for (const code of Object.keys(commandesNavigation.PAS_PRET).concat(['NAV-01', 'NAV-02', 'NAV-03', 'NAV-04', 'NAV-07', 'NAV-08', 'NAV-09', 'NAV-10', 'NAV-11', 'NAV-13', 'NAV-21', 'NAV-22', 'NAV-24'])) commandesVocales.brancherAction(code, undefined);
    }
  });

  await testAsync('Commande vocale NAV-01 (09/11/2026) : appelée directement depuis l’écran des tâches et depuis Autre (sans écran Micro) : un seul écran ouvert, l’écran Chercher', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    brancherAccueil(c, ui);
    const nav = commandesNavigation.brancher(ui.doc, { geste: () => null });
    const el = id => ui.parId(id);
    try {
      el('ouvrir-chercher').click();
      el('chercher-todo').click();
      transitionEcrans.terminer(ui.doc);
      attendreEgal(nav.actions['NAV-01'](), 'J’ouvre Chercher.', 'depuis les tâches');
      transitionEcrans.terminer(ui.doc);
      attendre(el('ecran-complet').hidden && !el('ecran-chercher').hidden && !ui.doc.body.classList.contains('vue-complete'), 'tâches pas fermées, ou Chercher pas ouvert');
      el('ouvrir-autre').click();
      transitionEcrans.terminer(ui.doc);
      attendreEgal(nav.actions['NAV-01'](), 'J’ouvre Chercher.', 'depuis Autre');
      attendre(el('ecran-autre').hidden && !el('ecran-chercher').hidden, 'Autre pas remplacé par Chercher');
      attendreEgal(nav.actions['NAV-07'](), 'Retour à l’accueil.', 'accueil');
      transitionEcrans.terminer(ui.doc);
      attendre(el('ecran-chercher').hidden && touchable(ui, el('ouvrir-chercher')), 'NAV-07 ne ferme pas Chercher');
    } finally {
      for (const code of Object.keys(commandesNavigation.PAS_PRET).concat(['NAV-01', 'NAV-02', 'NAV-03', 'NAV-04', 'NAV-07', 'NAV-08', 'NAV-09', 'NAV-10', 'NAV-11', 'NAV-13', 'NAV-21', 'NAV-22', 'NAV-24'])) commandesVocales.brancherAction(code, undefined);
    }
  });

  // ----- 09/11/2026 : étape 1 après l'essai c58 (« mes tâches », « Fermer » de Chercher, « Fermer » de la visionneuse) -----
  // Faux tableur bâti comme le VRAI pour la navigation : verbe d'ouverture COMMUN, « Écran cible » par code (NAV-13 :
  // mêmes six cibles que le vrai), une ligne RETIRER jamais lue. Aucune ligne de noms.
  const TABLEUR_FICTIF_TACHES = [
    TABLEUR_FICTIF_0[0],
    ['Ouvrir un écran de l’application', 'Navigation', 'Verbe d’ouverture', 'ouvre', 'COMMUN', ''],
    ['Ouvrir un écran de l’application', 'Navigation', 'Verbe d’ouverture', 'montre-moi', 'COMMUN', ''],
    ['Ouvrir un écran de l’application', 'Navigation', 'Écran cible', 'l’agenda', 'NAV-05', ''],
    ['Ouvrir un écran de l’application', 'Navigation', 'Écran cible', 'la liste des choses à faire', 'NAV-13', ''],
    ['Ouvrir un écran de l’application', 'Navigation', 'Écran cible', 'ma liste à faire', 'NAV-13', ''],
    ['Ouvrir un écran de l’application', 'Navigation', 'Écran cible', 'ma to-do', 'NAV-13', ''],
    ['Ouvrir un écran de l’application', 'Navigation', 'Écran cible', 'ma to-do liste', 'NAV-13', ''],
    ['Ouvrir un écran de l’application', 'Navigation', 'Écran cible', 'mes tâches', 'NAV-13', ''],
    ['Ouvrir un écran de l’application', 'Navigation', 'Écran cible', 'mes choses à faire', 'NAV-13', ''],
    ['Ouvrir un écran de l’application', 'Navigation', 'Écran cible', 'mon pense-bête fictif', 'NAV-13', 'RETIRER 09/11/2026 : FICTIF, jamais lu'],
    ['Fermer', '', 'Verbe de fermeture', 'ferme', 'NAV-09', ''],
    ['Fermer', '', 'Mot-clé', 'ça', 'NAV-09', '']
  ];

  await testAsync('Voix (09/11/2026, ce que Max a vécu sur c58, faux tableur bâti comme le vrai) : « mes tâches » SEUL au micro du milieu ouvre l’écran des tâches (avant : rangé dans « À trier ») ; « ma to-do », « la to-do », « les tâches », « ouvre mes tâches » aussi ; « liste de tâches » (absent du tableur) et une vraie phrase restent dans « À trier »', async c => {
    const cle = commandesVocales.CLE_COPIE;
    const avantCopie = localStorage.getItem(cle);
    const lignes = commandesVocales.analyser(TABLEUR_FICTIF_TACHES).lignes;
    localStorage.setItem(cle, JSON.stringify({ lu_le: new Date(0).toISOString(), compte: {}, lignes }));
    const nombre = TACHES.length;
    try {
      attendre(!lignes.some(l => l.formulation === 'mon pense-bete fictif' || l.formulation === 'mon pense-bête fictif'), 'ligne RETIRER lue');
      const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
      brancherAccueil(c, ui);
      commandesNavigation.brancher(ui.doc, { geste: () => null });
      const el = id => ui.parId(id);
      const dicter = phrase => {
        Object.assign(ui.dictee, { disponible: () => true, enCours: () => false, arreter() {}, demarrer(r) { r.surFinal(phrase); if (r.surFin) r.surFin(); } });
        parlerAuGrosMicro(el('microphone')); // 09/11/2026 : deux touchers
        return el('statut').textContent;
      };
      for (const phrase of ['mes tâches', 'Mes tâches.', 'ma to-do', 'la to-do', 'les tâches', 'mes choses à faire', 'ouvre mes tâches', 'montre-moi ma liste à faire']) {
        // 09/11/2026 : plus d'écran Micro (avant : el('ouvrir-micro').click()).
        transitionEcrans.terminer(ui.doc);
        attendreEgal(dicter(phrase), 'J’ouvre tes tâches.', `« ${phrase} »`);
        transitionEcrans.terminer(ui.doc);
        attendre(!el('ecran-complet').hidden && el('ecran-micro').hidden, `« ${phrase} » : écran des tâches pas ouvert`);
        attendreEgal(TACHES.length, nombre, `« ${phrase} » rangé dans « À trier »`);
        el('fermer-chercher').click();
        transitionEcrans.terminer(ui.doc);
      }
      // Pas dans le tableur, ou une vraie phrase : « À trier », comme avant (le code ne devine pas).
      // « liste de tâches » : absent du tableur (aucun code) ; au micro, le module des listes vocales le prend pour une
      // liste nommée « tâches » (« Je note… ») : vérifié ici sans le dicter (la session de liste resterait ouverte).
      attendre(!commandesVocales.deciderMicro('liste de tâches', { lignes, contexte: {} })?.code, '« liste de tâches » reconnu comme une commande');
      for (const phrase of ['mes tâches de demain FICTIF', 'mon pense-bête fictif']) {
        // 09/11/2026 : plus d'écran Micro (avant : el('ouvrir-micro').click()).
        transitionEcrans.terminer(ui.doc);
        const dit = dicter(phrase);
        attendre(TACHES.slice(nombre).some(x => x.intitule.toLowerCase().includes(phrase.toLowerCase().split(' ')[0]) && x.categorie === 'À trier'), `« ${phrase} » pas rangé dans « À trier » (Cap : ${dit})`);
        attendre(el('ecran-complet').hidden, `« ${phrase} » a ouvert l’écran des tâches`);
        el('fermer-micro').click();
        transitionEcrans.terminer(ui.doc);
      }
    } finally {
      TACHES.slice(nombre).forEach(x => abandonner(x.id));
      if (avantCopie === null) localStorage.removeItem(cle); else localStorage.setItem(cle, avantCopie);
      for (const code of Object.keys(commandesNavigation.PAS_PRET).concat(['NAV-01', 'NAV-02', 'NAV-03', 'NAV-04', 'NAV-07', 'NAV-08', 'NAV-09', 'NAV-10', 'NAV-11', 'NAV-13', 'NAV-21', 'NAV-22', 'NAV-24'])) commandesVocales.brancherAction(code, undefined);
    }
  });

  await testAsync('Visionneuse (09/11/2026, FICTIF) : gros « Fermer la visionneuse » du bas caché ; le « Fermer » de la page de Zencoder (en haut à droite) ferme la visionneuse de Cap (mémoire libérée, retour aux vignettes) ; « ferme » à la voix aussi ; petit micro toujours en haut à droite', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const v = fausseVisionneuse();
    const adresses = fausseAdresses();
    // Fausse page de Zencoder : seulement son bouton « Fermer » (il vide ses documents, comme le vrai).
    const page = ui.doc.implementation.createHTMLDocument('FICTIF');
    const haut = page.createElement('button');
    haut.id = 'bouton-fermer';
    let videeParZencoder = 0;
    haut.addEventListener('click', () => { videeParZencoder++; });
    page.body.append(haut);
    const compte = { appeler: async () => ({ blob: async () => new Blob(['document FICTIF']) }), seConnecter() {} };
    const vis = visionneuseCap0().brancher(ui.doc, { compte, visionneuse: v.charger, urls: adresses, stockage: c.localStorage,
      vignette: async () => new Blob(['vignette FICTIVE']), pageZencoder: () => page });
    brancherAccueil(c, ui); // pose le petit micro de tous les écrans dans la fenêtre du dessus
    const el = id => ui.parId(id);
    attendre(el('fermer-visionneuse').hidden, '« Fermer la visionneuse » du bas affiché');
    // Un seul document : la visionneuse s'ouvre ; « Fermer » du haut = visionneuse fermée, mémoire libérée.
    await vis.ouvrir([{ id: 'seul' }]);
    attendre(el('visionneuse-cap').open && v.appels.length === 1, 'pas ouvert');
    await pause();
    attendre(touchable(ui, el('petit-micro')), 'petit micro pas touchable'); // 09/11/2026 : le petit micro de tous les écrans
    haut.click();
    attendre(videeParZencoder === 1 && !el('visionneuse-cap').open, '« Fermer » du haut ne ferme pas la visionneuse');
    attendre(adresses.liberees.length >= adresses.faites.length, 'mémoire pas libérée');
    // Plusieurs documents : vignettes, puis un document ; « Fermer » du haut ramène aux vignettes (branché une seule fois).
    await vis.ouvrir([{ id: 'a' }, { id: 'b' }]);
    el('grille-vignettes').querySelector('.vignette').click();
    await attendreQue(() => el('visionneuse-cap').open && v.appels.filter(x => x[0] === 'montrer').length >= 2, 'document pas ouvert');
    haut.click();
    attendre(!el('visionneuse-cap').open && el('vignettes-cap').open, 'pas revenu aux vignettes');
    // « ferme » à la voix : même bouton caché.
    el('grille-vignettes').querySelector('.vignette').click();
    await attendreQue(() => el('visionneuse-cap').open, 'document pas rouvert');
    attendreEgal(vis.fermerParVoix(), 'Je ferme le document : voici les vignettes.', 'voix');
    attendre(!el('visionneuse-cap').open && el('vignettes-cap').open, 'la voix ne ferme pas le document');
  });

  // ----- 09/11/2026 : PETIT MICRO de TOUS les écrans (accord de Max), FICTIF -----
  const seTouchent = (a, b) => a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom;
  // Tout ce qu'on peut toucher dans « zone » (sauf le petit micro et la note) : rien ne doit être sous le micro.
  function sousLePetitMicro(ui, zone) {
    const m = ui.parId('petit-micro').getBoundingClientRect();
    return [...zone.querySelectorAll('button, input, select, textarea, a[href], [role="switch"]')]
      .filter(x => x.id !== 'petit-micro' && x.id !== 'indicateur-musique' && x.getClientRects().length > 0 && !x.closest('[hidden]'))
      .filter(x => { const r = x.getBoundingClientRect(); return r.width > 0 && r.height > 0 && seTouchent(r, m); })
      .map(x => x.id || x.className || x.tagName);
  }

  await testAsync('Petit micro partout (09/11/2026) : UN seul, en haut à droite, immobile, icône seule, touchable, sur l’accueil, Autre, Réglages, l’écran Micro, Chercher, l’écran des tâches et l’écran d’eau ; il ne cache AUCUN bouton ; anciens micros de la visionneuse et des vignettes cachés', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    brancherAccueil(c, ui);
    const el = id => ui.parId(id);
    const m = el('petit-micro');
    attendreEgal(ui.doc.querySelectorAll('#petit-micro').length, 1, 'un seul petit micro');
    attendre(el('micro-visionneuse').hidden && el('micro-vignettes').hidden, 'anciens micros encore affichés');
    attendre(!m.textContent.trim() && m.getAttribute('aria-label') && m.querySelector('svg'), 'micro avec un mot, ou sans nom');
    attendreEgal(ui.cadre.contentWindow.getComputedStyle(m).position, 'fixed', 'micro qui bouge');
    const place = () => { const r = m.getBoundingClientRect(); return [Math.round(r.top), Math.round(r.right), Math.round(r.width), Math.round(r.height)]; };
    attendreEgal(place(), [12, 400, 52, 52], 'place ou taille du micro');
    const ecrans = [
      ['accueil', () => {}],
      ['Autre', () => el('ouvrir-autre').click()],
      ['Réglages', () => el('ouvrir-reglages-cap').click()],
      ['Micro', () => el('microphone').click()], // 09/11/2026 : premier toucher du gros micro (« + » et l'icône apparaissent)
      ['Chercher', () => el('ouvrir-chercher').click()],
      ['tâches', () => el('chercher-todo').click()]
    ];
    for (const [nom, ouvrir] of ecrans) {
      ouvrir();
      transitionEcrans.terminer(ui.doc);
      await pause();
      attendre(touchable(ui, m), `micro pas touchable (${nom})`);
      attendreEgal(place(), [12, 400, 52, 52], `micro qui a bougé (${nom})`);
      attendreEgal(sousLePetitMicro(ui, ui.doc.body), [], `bouton sous le micro (${nom})`);
    }
    el('fermer-chercher').click();
    transitionEcrans.terminer(ui.doc);
    // Écran d'eau (premier écran, au-dessus de tout) : le micro reste au-dessus.
    el('ecran-eau').hidden = false;
    attendre(touchable(ui, m), 'micro caché par l’écran d’eau');
    el('ecran-eau').hidden = true;
  });

  await testAsync('Petit micro partout (09/11/2026) : posé dans la fenêtre ouverte du dessus (chaque fenêtre de Cap), touchable, même place, rien dessous ; revient sur la page à la fermeture ; dans une fenêtre de choix, il ne monte pas du sable', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    brancherAccueil(c, ui);
    const el = id => ui.parId(id);
    const m = el('petit-micro');
    const fenetres = [...ui.doc.querySelectorAll('dialog')].map(d => d.id).filter(Boolean);
    attendre(fenetres.length >= 20, 'trop peu de fenêtres essayées');
    for (const id of fenetres) {
      const d = el(id);
      d.showModal();
      await pause();
      attendre(d.contains(m), `micro pas posé dans « ${id} »`);
      attendre(touchable(ui, m), `micro pas touchable dans « ${id} »`);
      const r = m.getBoundingClientRect();
      attendre(Math.round(r.top) === 12 && Math.round(r.right) === 400, `micro qui a bougé dans « ${id} » : ${JSON.stringify(r)}`);
      attendreEgal(sousLePetitMicro(ui, d), [], `bouton sous le micro dans « ${id} »`);
      d.close();
      await pause();
      attendre(!d.contains(m), `micro resté dans « ${id} » fermée`);
    }
    attendre(m.parentNode === ui.doc.body, 'micro pas revenu sur la page');
    // Deux fenêtres l'une sur l'autre : celle du dessus.
    el('clavier').showModal();
    el('aide').showModal();
    await pause();
    attendre(el('aide').contains(m), 'micro pas dans la fenêtre du dessus');
    el('aide').close();
    await pause();
    attendre(el('clavier').contains(m), 'micro pas revenu dans la fenêtre d’en dessous');
    el('clavier').close();
    // Fenêtre de choix en train de sortir du sable : pas d'animation sur le micro.
    const choix = el('choix-voix');
    choix.classList.add('fenetre-choix', 'choix-entree');
    choix.showModal();
    await pause();
    const style = ui.cadre.contentWindow.getComputedStyle(m);
    attendre(style.animationName === 'none' && style.opacity === '1', `le micro monte du sable avec la fenêtre : ${style.animationName} ${style.opacity}`);
    choix.close();
    choix.classList.remove('choix-entree');
  });

  await testAsync('Petit micro partout (09/11/2026) : la note de musique à sa GAUCHE, même taille, même ligne, sans se toucher ; tous deux sous l’alerte Google quand elle est affichée ; l’écran des tâches garde son « Fermer » libre', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    brancherAccueil(c, ui);
    const el = id => ui.parId(id);
    const m = el('petit-micro');
    const note = el('indicateur-musique');
    note.hidden = false;
    const r = () => [m.getBoundingClientRect(), note.getBoundingClientRect()];
    let [rm, rn] = r();
    attendre(Math.abs(rm.top - rn.top) < 1 && Math.abs(rm.width - rn.width) < 1 && Math.abs(rm.height - rn.height) < 1, `pas même ligne ou même taille : ${JSON.stringify([rm, rn])}`);
    attendre(rn.right <= rm.left - 6 && !seTouchent(rm, rn), 'la note n’est pas à gauche du micro');
    // Écran des tâches : « Fermer » libre, même avec la note.
    el('ouvrir-chercher').click();
    el('chercher-todo').click();
    transitionEcrans.terminer(ui.doc);
    for (const b of [el('fermer-chercher')]) attendre(!seTouchent(b.getBoundingClientRect(), rm) && !seTouchent(b.getBoundingClientRect(), rn) && touchable(ui, b), '« Fermer » des tâches sous le micro ou la note');
    // Alerte Google : les deux descendent sous l'alerte, toujours sur la même ligne.
    el('texte-alerte-google').textContent = 'Connexion à Google à refaire (FICTIF).';
    el('alerte-google').hidden = false;
    await pause();
    [rm, rn] = r();
    const ra = el('alerte-google').getBoundingClientRect();
    attendre(rm.top >= ra.bottom && Math.abs(rm.top - rn.top) < 1, `micro ou note pas sous l’alerte : ${JSON.stringify([ra, rm, rn])}`);
    attendre(touchable(ui, m) && touchable(ui, el('redonner-acces-google')), 'micro ou bouton Google caché');
    const rf = el('fermer-chercher').getBoundingClientRect();
    attendre(!seTouchent(rf, rm) && !seTouchent(rf, rn) && touchable(ui, el('fermer-chercher')), `« Fermer » des tâches sous le micro ou la note, avec l’alerte : ${JSON.stringify([rf, rm, rn])}`);
    attendreEgal(sousLePetitMicro(ui, ui.doc.body), [], 'bouton sous le micro avec l’alerte');
    el('alerte-google').hidden = true;
    note.hidden = true;
  });

  await testAsync('Visionneuse (09/11/2026) : le « Fermer » de la page de Zencoder passe JUSTE SOUS le petit micro (même bord droit), par une retouche de Cap', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    brancherAccueil(c, ui);
    // Bouton à la place du vrai (page de Zencoder : tout en haut à droite, 4 % de la largeur).
    const b = ui.doc.createElement('button');
    b.id = 'bouton-fermer';
    b.textContent = 'Fermer';
    b.style.cssText = 'position: absolute; top: 16px; right: 16px; padding: 8px 16px;';
    ui.doc.body.append(b);
    const m = ui.parId('petit-micro').getBoundingClientRect();
    attendre(seTouchent(b.getBoundingClientRect(), m), 'le bouton d’essai ne serait pas sous le micro (essai mal fait)');
    visionneuseCap0().retoucherVisionneuse(ui.doc);
    const r = b.getBoundingClientRect();
    attendre(!seTouchent(r, m) && r.top >= m.bottom && r.top - m.bottom <= 16 && Math.abs(r.right - m.right) < 1, `« Fermer » pas juste sous le micro : ${JSON.stringify([m, r])}`);
    b.remove();
  });

  await testAsync('Petit micro partout (09/11/2026, faux tableur avec RETIRER) : appui simple = une phrase par le même chemin que le micro du milieu (commandes d’abord, sinon « À trier ») ; appui long 2 s = conversation, surbrillance ; un toucher l’arrête', async c => {
    const cle = commandesVocales.CLE_COPIE;
    const avantCopie = localStorage.getItem(cle);
    localStorage.setItem(cle, JSON.stringify({ lu_le: new Date(0).toISOString(), compte: {}, lignes: commandesVocales.analyser(TABLEUR_FICTIF_1).lignes }));
    const nombre = TACHES.length;
    try {
      const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
      brancherAccueil(c, ui);
      commandesNavigation.brancher(ui.doc, { geste: () => null });
      const el = id => ui.parId(id);
      const m = el('petit-micro');
      const dicter = phrase => { Object.assign(ui.dictee, { disponible: () => true, enCours: () => false, arreter() {}, demarrer(r) { r.surFinal(phrase); if (r.surFin) r.surFin(); } }); m.click(); return el('statut').textContent; };
      attendreEgal(dicter('ouvre l’écran autre'), 'J’ouvre Autre.', 'commande au petit micro');
      transitionEcrans.terminer(ui.doc);
      attendre(!el('ecran-autre').hidden, 'Autre pas ouvert');
      dicter('acheter des piles FICTIF petit micro');
      attendre(TACHES.slice(nombre).some(x => x.intitule === 'acheter des piles FICTIF petit micro' && x.categorie === 'À trier'), 'pas rangé dans À trier');
      attendre(commandesVocales.analyser(TABLEUR_FICTIF_1).lignes.every(l => !/^RETIRER/.test(l.remarque || '')), 'ligne RETIRER lue');
      // Appui long : conversation en surbrillance ; un toucher l'arrête.
      Object.assign(ui.dictee, { disponible: () => true, enCours: () => false, arreter() {}, demarrer() {} });
      m.dispatchEvent(new Event('pointerdown'));
      const appui = [...c.delais.entries()].find(([, d]) => d.delai === 2000);
      attendre(appui, 'pas d’appui long de 2 s prévu');
      c.delais.delete(appui[0]);
      appui[1].rappel();
      m.dispatchEvent(new Event('pointerup'));
      m.click(); // le clic qui suit l'appui long n'arrête pas
      await pause();
      attendre(el('microphone').classList.contains('live') && m.getAttribute('aria-pressed') === 'true', 'conversation pas lancée en surbrillance');
      m.click();
      await pause();
      attendre(!el('microphone').classList.contains('live') && m.getAttribute('aria-pressed') === 'false', 'conversation pas arrêtée');
    } finally {
      TACHES.slice(nombre).forEach(x => abandonner(x.id));
      if (avantCopie === null) localStorage.removeItem(cle); else localStorage.setItem(cle, avantCopie);
      for (const code of Object.keys(commandesNavigation.PAS_PRET).concat(['NAV-01', 'NAV-02', 'NAV-03', 'NAV-04', 'NAV-07', 'NAV-08', 'NAV-09', 'NAV-10', 'NAV-11', 'NAV-13', 'NAV-21', 'NAV-22', 'NAV-24'])) commandesVocales.brancherAction(code, undefined);
    }
  });

  // ----- 09/11/2026 : BULLE sous le petit micro et interrupteur « Sous-titres » (accord de Max), FICTIF -----
  async function interfaceBulle(c, essai) {
    const cle = commandesVocales.CLE_COPIE;
    const avantCopie = localStorage.getItem(cle);
    const avantSousTitres = localStorage.getItem('cap_sous_titres_v1');
    localStorage.removeItem('cap_sous_titres_v1');
    localStorage.setItem(cle, JSON.stringify({ lu_le: new Date(0).toISOString(), compte: {}, lignes: commandesVocales.analyser(TABLEUR_FICTIF_1).lignes }));
    const nombre = TACHES.length;
    try {
      const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
      brancherAccueil(c, ui);
      commandesNavigation.brancher(ui.doc, { geste: () => null });
      const el = id => ui.parId(id);
      const dicter = phrase => { Object.assign(ui.dictee, { disponible: () => true, enCours: () => false, arreter() {}, demarrer(r) { if (phrase) r.surFinal(phrase); if (r.surFin) r.surFin(); } }); el('petit-micro').click(); };
      const bulle = () => (el('bulle-micro').hidden ? '' : el('bulle-micro').textContent);
      const effacer = () => { const d = [...c.delais.entries()].find(([, x]) => x.delai === 4500); attendre(d, 'pas d’effacement prévu (4,5 s)'); c.delais.delete(d[0]); d[1].rappel(); };
      await essai({ ui, el, dicter, bulle, effacer, nombre });
    } finally {
      TACHES.slice(nombre).forEach(x => abandonner(x.id));
      if (avantCopie === null) localStorage.removeItem(cle); else localStorage.setItem(cle, avantCopie);
      if (avantSousTitres === null) localStorage.removeItem('cap_sous_titres_v1'); else localStorage.setItem('cap_sous_titres_v1', avantSousTitres);
      for (const code of Object.keys(commandesNavigation.PAS_PRET).concat(['NAV-01', 'NAV-02', 'NAV-03', 'NAV-04', 'NAV-07', 'NAV-08', 'NAV-09', 'NAV-10', 'NAV-11', 'NAV-13', 'NAV-21', 'NAV-22', 'NAV-24'])) commandesVocales.brancherAction(code, undefined);
    }
  }

  await testAsync('Bulle (09/11/2026, faux tableur avec RETIRER) : SANS sous-titres (par défaut) : erreurs et échecs TOUJOURS dans la bulle (rien entendu, phrase pas complète, « pas encore prêt »), confirmations JAMAIS ; effacée après 4,5 s', async c => {
    await interfaceBulle(c, async ({ el, dicter, bulle, effacer, nombre }) => {
      attendreEgal(el('bouton-sous-titres').getAttribute('aria-checked'), 'false', 'sous-titres pas éteints par défaut');
      dicter('');
      attendreEgal(bulle(), 'Je n’ai rien entendu, réessaie.'.replace('’', "'"), 'rien entendu');
      attendre(el('bulle-micro').classList.contains('bulle-erreur'), 'pas marquée erreur');
      effacer();
      attendreEgal(bulle(), '', 'bulle pas effacée');
      dicter('ouvre');
      attendreEgal(bulle(), commandesVocales.PAS_UNE_IA, 'phrase incomplète');
      effacer();
      dicter('ouvre l’agenda');
      attendreEgal(bulle(), 'Agenda : pas encore prêt.', '« pas encore prêt »');
      effacer();
      // Confirmations : rien.
      dicter('ouvre l’écran autre');
      attendreEgal(bulle(), '', 'confirmation de commande sans sous-titres');
      dicter('acheter du pain FICTIF bulle');
      attendre(TACHES.slice(nombre).some(x => x.intitule === 'acheter du pain FICTIF bulle'), 'phrase pas rangée');
      attendreEgal(bulle(), '', 'confirmation « À trier » sans sous-titres');
    });
  });

  await testAsync('Bulle (09/11/2026, FICTIF) : interrupteur « Sous-titres » dans Réglages (même allure que clair / sombre, gardé sur le téléphone) ; AVEC sous-titres : « J’ouvre Autre. » et « Ajoutée dans À trier » dans la bulle ; erreurs toujours', async c => {
    await interfaceBulle(c, async ({ ui, el, dicter, bulle, effacer }) => {
      el('ouvrir-autre').click();
      el('ouvrir-reglages-cap').click();
      transitionEcrans.terminer(ui.doc);
      const b = el('bouton-sous-titres');
      b.scrollIntoView({ block: 'center' }); // Réglages défile : l'interrupteur est sous « Eau »
      attendre(touchable(ui, b) && b.getAttribute('role') === 'switch' && el('libelle-sous-titres').textContent === 'Sous-titres', 'interrupteur absent ou pas touchable');
      // Même allure que l'interrupteur clair / sombre (taille et curseur).
      el('fermer-reglages').click();
      el('ouvrir-autre').click();
      transitionEcrans.terminer(ui.doc);
      const theme = el('bouton-theme-cap').getBoundingClientRect();
      el('ouvrir-reglages-cap').click();
      transitionEcrans.terminer(ui.doc);
      const st = b.getBoundingClientRect();
      attendre(Math.abs(st.width - theme.width) < 1.5 && Math.abs(st.height - theme.height) < 1.5, `pas la même taille que clair / sombre : ${JSON.stringify([theme, st])}`);
      b.click();
      attendre(b.getAttribute('aria-checked') === 'true' && localStorage.getItem('cap_sous_titres_v1') === 'oui', 'sous-titres pas allumés ou pas gardés');
      dicter('ouvre l’écran autre');
      attendreEgal(bulle(), 'J’ouvre Autre.', 'confirmation de commande');
      attendre(!el('bulle-micro').classList.contains('bulle-erreur'), 'confirmation marquée erreur');
      effacer();
      dicter('acheter du lait FICTIF bulle');
      attendre(/^Ajoutée dans À trier : « acheter du lait FICTIF bulle »/.test(bulle()), `confirmation « À trier » : ${bulle()}`);
      effacer();
      dicter('');
      attendre(/rien entendu/.test(bulle()), 'erreur pas montrée avec les sous-titres');
      effacer();
      b.click();
      attendre(b.getAttribute('aria-checked') === 'false' && localStorage.getItem('cap_sous_titres_v1') === 'non', 'sous-titres pas éteints');
    });
  });

  await testAsync('Bulle (09/11/2026, FICTIF) : dans la visionneuse, « Je n’ai rien entendu » est VISIBLE (dans la fenêtre du dessus, sous le « Fermer » déplacé, rien ne la cache) ; elle ne capte aucun toucher ; sous l’alerte Google, elle descend', async c => {
    await interfaceBulle(c, async ({ ui, el, dicter, bulle, effacer }) => {
      const fen = el('visionneuse-cap');
      fen.showModal();
      await pause();
      dicter('');
      await pause();
      attendre(/rien entendu/.test(bulle()) && fen.contains(el('bulle-micro')) && affiche(ui, el('bulle-micro')), 'bulle pas visible dans la visionneuse');
      const rb = el('bulle-micro').getBoundingClientRect();
      const rm = el('petit-micro').getBoundingClientRect();
      attendre(rb.top >= rm.bottom && rb.top >= 120 && Math.abs(rb.right - rm.right) < 1 && rb.bottom <= 900, `bulle mal placée : ${JSON.stringify([rm, rb])}`);
      attendreEgal(ui.cadre.contentWindow.getComputedStyle(el('bulle-micro')).pointerEvents, 'none', 'la bulle capte le doigt');
      // Rien ne la recouvre : au centre de la bulle, on touche ce qui est dessous (la visionneuse), jamais une autre fenêtre.
      const dessous = ui.doc.elementFromPoint(rb.left + rb.width / 2, rb.top + rb.height / 2);
      attendre(dessous && fen.contains(dessous), 'autre chose par-dessus la bulle');
      effacer();
      fen.close();
      await pause();
      attendre(el('bulle-micro').parentNode === ui.doc.body, 'bulle pas revenue sur la page');
      el('texte-alerte-google').textContent = 'Connexion à Google à refaire (FICTIF).';
      el('alerte-google').hidden = false;
      await pause();
      dicter('');
      const ra = el('alerte-google').getBoundingClientRect();
      const rb2 = el('bulle-micro').getBoundingClientRect();
      attendre(rb2.top >= ra.bottom && rb2.top >= el('petit-micro').getBoundingClientRect().bottom, 'bulle pas sous l’alerte et le micro');
      effacer();
      el('alerte-google').hidden = true;
    });
  });

  // ----- 09/11/2026 : GROS MICRO de l'accueil, « + » et nouvelle icône, nouvel ordre (accord de Max, étape 2), FICTIF -----
  async function accueilGrosMicro(c, essai, { reduit = false } = {}) {
    const cle = commandesVocales.CLE_COPIE;
    const avantCopie = localStorage.getItem(cle);
    localStorage.setItem(cle, JSON.stringify({ lu_le: new Date(0).toISOString(), compte: {}, lignes: commandesVocales.analyser(TABLEUR_FICTIF_1).lignes }));
    const nombre = TACHES.length;
    try {
      const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
      if (reduit) ui.cadre.contentWindow.matchMedia = q => ({ matches: /reduce/.test(q), addEventListener() {}, removeEventListener() {} });
      brancherAccueil(c, ui);
      commandesNavigation.brancher(ui.doc, { geste: () => null });
      const el = id => ui.parId(id);
      const ecoutes = [];
      const phrase = texte => Object.assign(ui.dictee, { disponible: () => true, enCours: () => false, arreter() {}, demarrer(r) { ecoutes.push(texte); if (texte) r.surFinal(texte); if (r.surFin) r.surFin(); } });
      const outils = () => !el('micro-ajouter').hidden && !el('micro-ecrire').hidden;
      await essai({ ui, el, phrase, ecoutes, outils, nombre });
    } finally {
      TACHES.slice(nombre).forEach(x => abandonner(x.id));
      if (avantCopie === null) localStorage.removeItem(cle); else localStorage.setItem(cle, avantCopie);
      for (const code of Object.keys(commandesNavigation.PAS_PRET).concat(['NAV-01', 'NAV-02', 'NAV-03', 'NAV-04', 'NAV-07', 'NAV-08', 'NAV-09', 'NAV-10', 'NAV-11', 'NAV-13', 'NAV-21', 'NAV-22', 'NAV-24'])) commandesVocales.brancherAction(code, undefined);
    }
  }

  await testAsync('Gros micro (09/11/2026) : accueil = Chercher EN HAUT, gros micro AU MILIEU, Autre EN BAS ; « + » et l’icône cachés au départ ; écran Micro et « continu » jamais montrés ; tout est touchable', async c => {
    await accueilGrosMicro(c, async ({ ui, el, outils }) => {
      const nav = el('accueil-boutons');
      attendreEgal([...nav.querySelectorAll('button')].filter(b => !b.hidden).map(b => b.id), ['ouvrir-chercher', 'microphone', 'ouvrir-autre'], 'boutons visibles de l’accueil');
      const r = ['ouvrir-chercher', 'microphone', 'ouvrir-autre'].map(id => el(id).getBoundingClientRect());
      attendre(r[0].bottom <= r[1].top && r[1].bottom <= r[2].top, 'pas Chercher, micro, Autre de haut en bas');
      attendre(Math.abs((r[1].left + r[1].right) / 2 - 206) < 2, 'gros micro pas centré');
      attendre(!outils() && el('micro-ajouter').hidden && el('micro-ecrire').hidden, '« + » ou l’icône visibles au départ');
      attendre(el('ouvrir-micro').hidden && el('micro-continu').hidden && el('ecran-micro').hidden, 'écran Micro ou « continu » encore là');
      for (const id of ['ouvrir-chercher', 'microphone', 'ouvrir-autre']) attendre(touchable(ui, el(id)), `${id} pas touchable`);
    });
  });

  await testAsync('Gros micro (09/11/2026, faux tableur avec RETIRER) : PREMIER toucher = n’écoute PAS, « + » à gauche et l’icône à droite apparaissent (même rangée, plus petits) ; DEUXIÈME toucher = une phrase ; deux touchers rapides = une phrase ; le petit micro écoute tout de suite', async c => {
    await accueilGrosMicro(c, async ({ ui, el, phrase, ecoutes, outils }) => {
      phrase('ouvre l’écran autre');
      el('microphone').click();
      attendreEgal(ecoutes.length, 0, 'le premier toucher écoute');
      attendre(outils(), '« + » et l’icône pas apparus');
      const [rp, rm, ri] = ['micro-ajouter', 'microphone', 'micro-ecrire'].map(id => el(id).getBoundingClientRect());
      attendre(rp.right <= rm.left && rm.right <= ri.left, 'pas « + » à gauche et l’icône à droite');
      const centre = x => x.top + x.height / 2;
      attendre(Math.abs(centre(rp) - centre(rm)) < 2 && Math.abs(centre(ri) - centre(rm)) < 2, 'pas sur la même rangée');
      attendre(rp.width < rm.width && Math.abs(rp.width - ri.width) < 1, '« + » et l’icône pas identiques et plus petits');
      attendre(Math.abs((rm.left + rm.right) / 2 - 206) < 2, 'le gros micro a bougé');
      for (const id of ['micro-ajouter', 'microphone', 'micro-ecrire']) attendre(touchable(ui, el(id)), `${id} pas touchable`);
      attendreEgal(sousLePetitMicro(ui, ui.doc.body), [], 'un bouton sous le petit micro');
      // Deuxième toucher : une phrase (commande d'abord).
      el('microphone').click();
      attendreEgal(ecoutes, ['ouvre l’écran autre'], 'le deuxième toucher n’écoute pas');
      attendreEgal(el('statut').textContent, 'J’ouvre Autre.', 'commande');
      transitionEcrans.terminer(ui.doc);
      await pause();
      attendre(!outils(), '« + » et l’icône restés en quittant l’accueil');
      el('fermer-autre').click();
      transitionEcrans.terminer(ui.doc);
      // Deux touchers rapides : une phrase.
      phrase('acheter du riz FICTIF gros micro');
      el('microphone').click(); el('microphone').click();
      attendreEgal(ecoutes.length, 2, 'deux touchers rapides n’écoutent pas une fois');
      attendre(TACHES.some(x => x.intitule === 'acheter du riz FICTIF gros micro' && x.categorie === 'À trier'), 'phrase pas rangée');
      // Le petit micro : un seul toucher suffit.
      phrase('acheter du thé FICTIF petit micro');
      el('petit-micro').click();
      attendreEgal(ecoutes.length, 3, 'le petit micro n’écoute pas tout de suite');
    });
  });

  await testAsync('Gros micro (09/11/2026, FICTIF) : « + » ouvre « Ajouter une tâche », l’icône ouvre la MÊME fenêtre que l’ancienne icône clavier ; les toucher les fait partir ; quitter l’accueil aussi ; AUCUNE minuterie ne les efface', async c => {
    await accueilGrosMicro(c, async ({ ui, el, outils }) => {
      el('microphone').click();
      attendre(outils(), 'pas apparus');
      // Aucune minuterie : toutes les minuteries prévues se déclenchent, ils restent.
      for (const [id, d] of [...c.delais.entries()]) { c.delais.delete(id); try { d.rappel(); } catch (e) { /* rien */ } }
      attendre(outils(), 'effacés par une minuterie');
      const clavierAvant = [];
      el('ouvrir-clavier').addEventListener('click', () => clavierAvant.push('clavier'));
      el('micro-ecrire').click();
      attendreEgal(clavierAvant, ['clavier'], 'l’icône n’ouvre pas la fenêtre « Écrire une demande »');
      attendre(el('micro-ecrire').getAttribute('aria-controls') === el('micro-clavier').getAttribute('aria-controls'), 'pas la même fenêtre que l’icône clavier');
      attendre(!outils(), 'toucher l’icône ne les fait pas partir');
      if (el('clavier').open) el('clavier').close();
      el('microphone').click();
      const ajouts = [];
      el('ajouter').addEventListener('click', () => ajouts.push('+'));
      el('micro-ajouter').click();
      attendreEgal(ajouts, ['+'], '« + » n’ouvre pas « Ajouter une tâche »');
      attendre(!outils(), 'toucher « + » ne les fait pas partir');
      for (const d of ui.doc.querySelectorAll('dialog[open]')) d.close();
      // Quitter l'accueil : Chercher, puis l'eau.
      el('microphone').click();
      el('ouvrir-chercher').click();
      await pause();
      attendre(!outils(), 'restés en ouvrant Chercher');
      el('fermer-chercher-cap').click();
      transitionEcrans.terminer(ui.doc);
      attendre(!outils(), 'revenus tout seuls');
    });
  });

  await testAsync('Gros micro (09/11/2026, FICTIF) : APPUI LONG 2 s = écoute continue, SURBRILLANCE, « + » et l’icône apparaissent en même temps ; le clic qui suit ne l’arrête pas ; un toucher l’arrête ; déjà en écoute (petit micro) : un toucher l’arrête et les montre', async c => {
    await accueilGrosMicro(c, async ({ ui, el, outils }) => {
      Object.assign(ui.dictee, { disponible: () => true, enCours: () => false, arreter() {}, demarrer() {} });
      const m = el('microphone');
      m.style.transition = 'none'; // la couleur se mesure sans le fondu de 0,9 s
      const fond = () => ui.cadre.contentWindow.getComputedStyle(m).backgroundColor;
      const repos = fond();
      m.dispatchEvent(new Event('pointerdown'));
      const appui = [...c.delais.entries()].find(([, d]) => d.delai === 2000);
      attendre(appui, 'pas d’appui long de 2 s prévu');
      c.delais.delete(appui[0]);
      appui[1].rappel();
      m.dispatchEvent(new Event('pointerup'));
      m.click();
      await pause();
      attendre(m.classList.contains('live') && outils() && el('petit-micro').getAttribute('aria-pressed') === 'true', 'conversation, « + » / icône ou petit micro pas allumés');
      attendre(fond() !== repos, 'pas de surbrillance');
      m.click();
      await pause();
      attendre(!m.classList.contains('live'), 'un toucher n’arrête pas la conversation');
      // Écoute lancée par le petit micro, « + » et l'icône partis : un toucher du gros micro l'arrête et les montre.
      el('ouvrir-chercher').click();
      await pause();
      el('fermer-chercher-cap').click();
      transitionEcrans.terminer(ui.doc);
      attendre(!outils(), 'pas partis');
      let arrets = 0;
      Object.assign(ui.dictee, { enCours: () => true, arreter() { arrets++; }, demarrer() {} });
      el('petit-micro').click(); // en cours : le petit micro arrête (comme avant)
      m.setAttribute('aria-pressed', 'true');
      m.click();
      attendre(outils() && arrets >= 1, 'pas montrés, ou écoute pas arrêtée');
      m.setAttribute('aria-pressed', 'false');
    });
  });

  await testAsync('Gros micro (09/11/2026, faux tableur avec RETIRER) : « ouvre le micro » (NAV-22) depuis Autre = retour à l’accueil, « + » et l’icône montrés, sans écouter ; animations réduites : ils apparaissent d’un coup', async c => {
    await accueilGrosMicro(c, async ({ ui, el, outils }) => {
      el('ouvrir-autre').click();
      transitionEcrans.terminer(ui.doc);
      Object.assign(ui.dictee, { disponible: () => true, enCours: () => false, arreter() {}, demarrer(r) { r.surFinal('ouvre le micro'); if (r.surFin) r.surFin(); } });
      el('petit-micro').click();
      attendreEgal(el('statut').textContent, 'Voici le micro.', 'réponse');
      transitionEcrans.terminer(ui.doc);
      attendre(el('ecran-autre').hidden && outils() && el('microphone').getAttribute('aria-pressed') === 'false' && el('ecran-micro').hidden, 'pas l’accueil avec « + » et l’icône, ou écoute lancée');
    }, {});
    await accueilGrosMicro(c, async ({ ui, el, outils }) => {
      el('microphone').click();
      attendre(outils(), 'pas apparus');
      // Le navigateur d'essai ne simule pas le réglage d'Android : on vérifie la règle du style.
      attendre(/prefers-reduced-motion: reduce\) \{ #accueil-boutons \.outil-apparait \{ animation: none; \}/.test(SOURCE_STYLE), 'pas de règle « animations réduites » pour « + » et l’icône');
    }, { reduit: true });
  });

  // ----- 09/11/2026 : RÈGLE DU RETOUR (pile des écrans) et commandes sur l'écran d'eau (accord de Max, étape 3), FICTIF -----
  async function interfaceRetour(c, essai) {
    const cle = commandesVocales.CLE_COPIE;
    const avantCopie = localStorage.getItem(cle);
    localStorage.setItem(cle, JSON.stringify({ lu_le: new Date(0).toISOString(), compte: {}, lignes: commandesVocales.analyser(TABLEUR_FICTIF_1).lignes }));
    const nombre = TACHES.length;
    try {
      const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
      const { module } = brancherAccueil(c, ui);
      const temps = { t: 0 };
      const g = brancherGesteRetour(c, ui, temps);
      const eau = { entrees: 0, entrerDansCap() { this.entrees++; ui.doc.documentElement.classList.remove('eau-ouverte'); ui.parId('ecran-eau').hidden = true; } };
      commandesNavigation.brancher(ui.doc, { geste: () => g, eau: () => eau });
      const el = id => ui.parId(id);
      const dire = phrase => { Object.assign(ui.dictee, { disponible: () => true, enCours: () => false, arreter() {}, demarrer(r) { r.surFinal(phrase); if (r.surFin) r.surFin(); } }); el('petit-micro').click(); transitionEcrans.terminer(ui.doc); return el('statut').textContent; };
      const fin = () => transitionEcrans.terminer(ui.doc);
      const visible = () => ['ecran-autre', 'ecran-reglages', 'ecran-chercher'].filter(id => !el(id).hidden).concat(el('ecran-complet').hidden ? [] : ['taches']);
      await essai({ ui, el, module, temps, g, eau, dire, fin, visible, nombre });
      attendreEgal(TACHES.length, nombre, 'une commande a créé une tâche');
    } finally {
      TACHES.slice(nombre).forEach(x => abandonner(x.id));
      if (avantCopie === null) localStorage.removeItem(cle); else localStorage.setItem(cle, avantCopie);
      for (const code of Object.keys(commandesNavigation.PAS_PRET).concat(['NAV-01', 'NAV-02', 'NAV-03', 'NAV-04', 'NAV-07', 'NAV-08', 'NAV-09', 'NAV-10', 'NAV-11', 'NAV-13', 'NAV-21', 'NAV-22', 'NAV-24'])) commandesVocales.brancherAction(code, undefined);
    }
  }

  await testAsync('Retour (09/11/2026) : Chercher → To-do → « Fermer » = Chercher, puis l’accueil ; Autre → Réglages → « Fermer » = Autre, puis l’accueil ; Chercher → Autre (voix) → « Fermer » = Chercher ; rouvrir un écran déjà dans la pile la raccourcit', async c => {
    await interfaceRetour(c, async ({ el, module, dire, fin, visible }) => {
      el('ouvrir-chercher').click(); fin();
      el('chercher-todo').click(); fin();
      attendreEgal(visible(), ['taches'], 'To-do');
      el('fermer-chercher').click(); fin();
      attendreEgal(visible(), ['ecran-chercher'], 'Fermer des tâches = Chercher');
      el('fermer-chercher-cap').click(); fin();
      attendreEgal([visible(), module.pile()], [[], []], 'Chercher = accueil, pile vide');
      el('ouvrir-autre').click(); fin();
      el('ouvrir-reglages-cap').click(); fin();
      attendreEgal(module.pile(), ['accueil', 'ecran-autre'], 'pile Autre → Réglages');
      el('fermer-reglages').click(); fin();
      attendreEgal(visible(), ['ecran-autre'], 'Réglages = Autre');
      el('fermer-autre').click(); fin();
      attendreEgal(visible(), [], 'Autre = accueil');
      el('ouvrir-chercher').click(); fin();
      attendreEgal(dire('ouvre l’écran autre'), 'J’ouvre Autre.', 'voix');
      el('fermer-autre').click(); fin();
      attendreEgal(visible(), ['ecran-chercher'], 'Autre ouvert depuis Chercher = Chercher');
      // Boucle : Chercher → Autre → Chercher : la pile se raccourcit.
      el('ouvrir-autre').click(); fin();
      el('ouvrir-chercher').click(); fin();
      attendreEgal(module.pile(), ['accueil'], 'pile pas raccourcie');
      el('fermer-chercher-cap').click(); fin();
      attendreEgal(visible(), [], 'pas revenu à l’accueil');
    });
  });

  await testAsync('Retour (09/11/2026, faux tableur avec RETIRER) : le geste de haut en bas, « ferme » à la voix et le glissement des tâches suivent la même règle ; une fenêtre posée par-dessus (aide) ne change rien', async c => {
    await interfaceRetour(c, async ({ ui, el, temps, dire, fin, visible }) => {
      el('ouvrir-autre').click(); fin();
      el('ouvrir-reglages-cap').click(); fin();
      glisserRetour(ui, temps, el('ecran-reglages'), NET);
      await attendreQue(() => el('ecran-reglages').hidden, 'geste : Réglages pas fermé');
      fin();
      attendreEgal(visible(), ['ecran-autre'], 'geste : pas revenu à Autre');
      el('ouvrir-reglages-cap').click(); fin();
      attendreEgal(dire('ferme ça'), 'Je ferme.', 'voix');
      await attendreQue(() => el('ecran-reglages').hidden, 'voix : Réglages pas fermé');
      fin();
      attendreEgal(visible(), ['ecran-autre'], 'voix : pas revenu à Autre');
      el('fermer-autre').click(); fin();
      // Tâches ouvertes depuis Chercher : le glissement vers le bas revient à Chercher.
      el('ouvrir-chercher').click(); fin();
      el('chercher-todo').click(); fin();
      el('ecran-complet').scrollTop = 0;
      const glisse = (type, y) => { const e = new Event(type, { bubbles: true }); Object.defineProperties(e, { touches: { value: type === 'touchend' ? [] : [{ clientX: 200, clientY: y }] }, changedTouches: { value: [{ clientX: 200, clientY: y }] } }); el('titre-vue').dispatchEvent(e); };
      glisse('touchstart', 300); glisse('touchend', 500);
      fin();
      attendreEgal(visible(), ['ecran-chercher'], 'glissement des tâches : pas revenu à Chercher');
      // Fenêtre par-dessus : la fermer laisse Chercher.
      el('aide').showModal(); el('aide').close();
      attendreEgal(visible(), ['ecran-chercher'], 'la fenêtre a changé l’écran');
      el('fermer-chercher-cap').click(); fin();
    });
  });

  await testAsync('Retour (09/11/2026, faux tableur avec RETIRER) : exceptions : « reviens à l’accueil » et « l’eau seule » à la voix VIDENT la pile ; une page rechargée (retour de Google) part de l’accueil, pile vide', async c => {
    await interfaceRetour(c, async ({ el, module, dire, fin, visible }) => {
      el('ouvrir-chercher').click(); fin();
      el('ouvrir-autre').click(); fin();
      el('ouvrir-reglages-cap').click(); fin();
      attendreEgal(module.pile(), ['accueil', 'ecran-chercher', 'ecran-autre'], 'pile');
      attendreEgal(dire('reviens à l’accueil'), 'Retour à l’accueil.', 'accueil');
      attendreEgal([visible(), module.pile()], [[], []], '« accueil » : pas l’accueil, ou pile pas vide');
      el('ouvrir-chercher').click(); fin();
      el('ouvrir-autre').click(); fin();
      dire('remets-moi l’eau seule');
      attendreEgal([visible(), module.pile()], [[], []], '« eau » : écrans ou pile pas vidés');
    });
    await interfaceRetour(c, async ({ module, visible }) => {
      attendreEgal([visible(), module.pile()], [[], []], 'page neuve : pas l’accueil ou pile pas vide');
    });
  });

  await testAsync('Écran d’eau (09/11/2026, défaut vu par Max sur c60, faux tableur avec RETIRER) : sur l’eau, « ouvre l’écran autre » et « reviens à l’accueil » font d’abord ENTRER dans Cap (avant : l’écran changeait sous l’eau, rien ne se voyait) ; « l’eau seule » n’en sort pas', async c => {
    await interfaceRetour(c, async ({ ui, el, eau, dire, visible }) => {
      const surEau = () => { ui.doc.documentElement.classList.add('eau-ouverte'); el('ecran-eau').hidden = false; };
      surEau();
      attendre(touchable(ui, el('petit-micro')), 'petit micro pas touchable sur l’eau');
      attendreEgal(dire('ouvre l’écran autre'), 'J’ouvre Autre.', 'réponse');
      attendre(eau.entrees === 1 && el('ecran-eau').hidden && !ui.doc.documentElement.classList.contains('eau-ouverte'), 'pas entré dans Cap');
      attendreEgal(visible(), ['ecran-autre'], 'Autre pas ouvert');
      el('fermer-autre').click();
      transitionEcrans.terminer(ui.doc);
      surEau();
      attendreEgal(dire('reviens à l’accueil'), 'Retour à l’accueil.', 'accueil');
      attendre(eau.entrees === 2 && el('ecran-eau').hidden, '« accueil » : pas entré dans Cap');
      surEau();
      dire('remets-moi l’eau seule');
      attendreEgal(eau.entrees, 2, '« l’eau seule » fait sortir de l’eau');
      ui.doc.documentElement.classList.remove('eau-ouverte'); el('ecran-eau').hidden = true;
    });
  });

  // ----- 09/11/2026 : mission A, ALLURE des fenêtres « + » et crayon (maquette de saisie de Zencoder), FICTIF -----
  await testAsync('Fenêtres de saisie (09/11/2026, mission A) : « + » et le crayon ouvrent leurs fenêtres SANS cadre ni fond (l’eau se voit, l’écran d’avant s’efface) ; champs simples (un trait en bas) ; boutons identiques un peu transparents ; titres lus mais cachés à l’œil ; toucher à côté ferme toujours ; petit micro intact', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    brancherAccueil(c, ui);
    const el = id => ui.parId(id);
    const vue = ui.cadre.contentWindow;
    ui.doc.querySelector('.ecran').style.transition = 'none'; // le fondu se mesure à la fin
    const alpha = couleur => { const m = /rgba?\(([^)]+)\)/.exec(couleur); const v = m ? m[1].split(',').map(Number) : []; return v.length === 4 ? v[3] : 1; };
    for (const [outil, id, titre] of [['micro-ajouter', 'ajout-tache', 'titre-ajout'], ['micro-ecrire', 'clavier', 'titre-clavier']]) {
      el('microphone').click();
      el(outil).click();
      await pause();
      const d = el(id);
      attendre(d.open, `${id} pas ouverte`);
      const s = vue.getComputedStyle(d);
      attendre(alpha(s.backgroundColor) === 0 && s.borderTopWidth === '0px' && s.boxShadow === 'none', `${id} : cadre ou fond encore là (${s.backgroundColor}, ${s.borderTopWidth})`);
      attendre(alpha(vue.getComputedStyle(d, '::backdrop').backgroundColor) === 0, `${id} : voile sombre derrière`);
      attendreEgal(vue.getComputedStyle(ui.doc.querySelector('.ecran')).opacity, '0', `${id} : l’écran d’avant ne s’efface pas`);
      const t2 = el(titre);
      attendre(t2.textContent.trim() && t2.getBoundingClientRect().width <= 1, `${id} : titre absent ou visible`);
      const champs = [...d.querySelectorAll('input[type="text"], textarea')];
      attendre(champs.length >= 1 && champs.every(x => { const cs = vue.getComputedStyle(x); return cs.borderTopWidth === '0px' && parseFloat(cs.borderBottomWidth) >= 2 && alpha(cs.backgroundColor) === 0; }), `${id} : champs pas « simples »`);
      // 09/11/2026 : + le bouton « phrase à apprendre » (il suit le micro dans la fenêtre, avec son allure à lui).
      const boutons = [...d.querySelectorAll('button')].filter(b => b.id !== 'petit-micro' && b.id !== 'indicateur-musique' && b.id !== 'bouton-apprendre' && b.getClientRects().length && !b.closest('[hidden]'));
      attendre(boutons.length >= 2, `${id} : trop peu de boutons`);
      const fonds = new Set(boutons.map(b => vue.getComputedStyle(b).backgroundColor));
      attendre(boutons.every(b => vue.getComputedStyle(b).borderTopLeftRadius === '22px' && parseFloat(vue.getComputedStyle(b).minHeight) >= 56), `${id} : boutons pas identiques ou trop petits`);
      attendre([...fonds].every(f => alpha(f) > 0.5 && alpha(f) < 1), `${id} : boutons pas « un peu transparents » (${[...fonds].join(' ; ')})`);
      // Le petit micro garde son allure à lui (rond, 52 px), posé dans la fenêtre.
      await pause();
      const m = el('petit-micro').getBoundingClientRect();
      attendre(d.contains(el('petit-micro')) && Math.round(m.width) === 52 && touchable(ui, el('petit-micro')), `${id} : petit micro abîmé`);
      // Toucher à côté (sous la fenêtre) : elle se ferme, comme avant.
      const r = d.getBoundingClientRect();
      d.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: 200, clientY: Math.min(899, r.bottom + 10) }));
      if (r.bottom + 10 < 900) attendre(!d.open, `${id} : toucher à côté ne ferme plus`);
      else d.close();
      await pause();
      attendreEgal(vue.getComputedStyle(ui.doc.querySelector('.ecran')).opacity, '1', `${id} : l’écran d’avant ne revient pas`);
    }
    attendre(/Cap_saisie_essai_v1_2026_11_08/.test(SOURCE_STYLE), 'origine (maquette de Zencoder) pas notée');
  });

  // ----- 09/11/2026 : POUCE et CROIX ROUGE à côté du petit micro (accord de Max, étape 4), FICTIF -----
  await testAsync('Signe (09/11/2026, faux tableur avec RETIRER) : POUCE = compris et fait (« ouvre l’écran autre », phrase rangée) ; CROIX = rien entendu, phrase incomplète, « pas encore prêt » ; même SANS sous-titres ; jamais de texte ; effacé ensuite', async c => {
    await interfaceBulle(c, async ({ el, dicter, nombre }) => {
      const s = el('signe-micro');
      const sorte = () => (s.hidden ? '' : (s.classList.contains('signe-pouce-visible') ? 'pouce' : (s.classList.contains('signe-croix-visible') ? 'croix' : '?')));
      const effacerSigne = d => { const x = [...c.delais.entries()].find(([, y]) => y.delai === d); attendre(x, `pas d’effacement du signe prévu (${d} ms)`); c.delais.delete(x[0]); x[1].rappel(); };
      attendreEgal(el('bouton-sous-titres').getAttribute('aria-checked'), 'false', 'sous-titres allumés');
      dicter('ouvre l’écran autre');
      attendreEgal([sorte(), s.getAttribute('aria-label')], ['pouce', 'Compris'], 'commande faite');
      attendreEgal(s.textContent.trim(), '', 'le signe dit quelque chose');
      effacerSigne(3000) /* 09/11/2026 : pouce 3 s (avant : 1800) */;
      attendreEgal(sorte(), '', 'pouce pas effacé');
      dicter('acheter du sel FICTIF signe');
      attendre(TACHES.slice(nombre).some(x => x.intitule === 'acheter du sel FICTIF signe'), 'phrase pas rangée');
      attendreEgal(sorte(), 'pouce', 'phrase rangée');
      dicter('');
      attendreEgal([sorte(), s.getAttribute('aria-label')], ['croix', 'Pas compris ou pas fait'], 'rien entendu');
      effacerSigne(2600);
      dicter('ouvre');
      attendreEgal(sorte(), 'croix', 'phrase incomplète');
      dicter('ouvre l’agenda');
      attendreEgal(sorte(), 'croix', '« pas encore prêt »');
    });
  });

  await testAsync('Signe (09/11/2026, FICTIF) : fenêtre de GROS CHOIX ouverte (Cap hésite) : ni pouce ni croix ; croix ROUGE, pouce vert ; à GAUCHE du petit micro, même ligne, plus à gauche quand la note joue ; dans la visionneuse aussi, rien ne le cache', async c => {
    await interfaceBulle(c, async ({ ui, el, dicter }) => {
      const s = el('signe-micro');
      const vue = ui.cadre.contentWindow;
      // Gros choix ouverts : aucun signe.
      el('choix-voix').showModal();
      await pause();
      dicter('ouvre l’écran autre');
      attendre(s.hidden, 'un signe malgré la fenêtre de choix');
      el('choix-voix').close();
      await pause();
      // Couleurs et place.
      dicter('');
      attendre(!s.hidden, 'pas de croix');
      attendreEgal(vue.getComputedStyle(s.querySelector('.signe-croix')).color, 'rgb(198, 40, 40)', 'croix pas rouge');
      let rs = s.getBoundingClientRect();
      let rm = el('petit-micro').getBoundingClientRect();
      attendre(rs.right <= rm.left && Math.abs(rs.top - rm.top) < 1 && !seTouchent(rs, rm), `signe pas à gauche du micro : ${JSON.stringify([rs, rm])}`);
      attendreEgal(vue.getComputedStyle(s).pointerEvents, 'none', 'le signe capte le doigt');
      el('indicateur-musique').hidden = false;
      const rn = el('indicateur-musique').getBoundingClientRect();
      rs = s.getBoundingClientRect();
      attendre(!seTouchent(rs, rn) && rs.right <= rn.left, `le signe cache la note : ${JSON.stringify([rs, rn])}`);
      el('indicateur-musique').hidden = true;
      dicter('ouvre l’écran autre');
      attendreEgal(vue.getComputedStyle(s.querySelector('.signe-pouce')).color, 'rgb(31, 110, 74)', 'pouce pas vert');
      transitionEcrans.terminer(ui.doc);
      // Visionneuse : le signe la suit, visible.
      el('visionneuse-cap').showModal();
      await pause();
      dicter('');
      await pause();
      rs = s.getBoundingClientRect();
      rm = el('petit-micro').getBoundingClientRect();
      attendre(el('visionneuse-cap').contains(s) && affiche(ui, s) && rs.right <= rm.left && !seTouchent(rs, rm), 'signe pas visible dans la visionneuse');
      el('visionneuse-cap').close();
      await pause();
      attendre(s.parentNode === ui.doc.body, 'signe pas revenu sur la page');
      attendre(/prefers-reduced-motion: reduce\) \{ #signe-micro\.signe-pouce-visible, #signe-micro\.signe-croix-visible \{ animation: none; \} \}/.test(SOURCE_STYLE), 'pas de règle « animations réduites »');
    });
  });

  // ----- 09/11/2026 : mission C, 5e icône « À trier » dans Chercher (accord de Max), FICTIF -----
  await testAsync('À trier (09/11/2026, mission C) : 5e icône dans Chercher, même allure, centrée sous les 4 autres, rien ne se chevauche ; elle ouvre « À trier » avec la DERNIÈRE phrase EN HAUT et surlignée ; « Fermer » revient à Chercher ; par la tuile, l’ordre d’avant ne change pas', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    brancherAccueil(c, ui);
    const el = id => ui.parId(id);
    const vue = ui.cadre.contentWindow;
    c.TACHES.splice(0, c.TACHES.length,
      { ...TACHES_FICTIVES[0], id: 'FICTIF-at-1', intitule: 'première phrase FICTIF', categorie: 'À trier', fait: false, abandonnee_le: '', parente: '' },
      { ...TACHES_FICTIVES[0], id: 'FICTIF-autre', intitule: 'tâche rangée FICTIF', categorie: 'Quotidien', fait: false, abandonnee_le: '', parente: '' },
      { ...TACHES_FICTIVES[0], id: 'FICTIF-at-2', intitule: 'deuxième phrase FICTIF', categorie: 'À trier', fait: false, abandonnee_le: '', parente: '' },
      { ...TACHES_FICTIVES[0], id: 'FICTIF-at-3', intitule: 'dernière phrase FICTIF', categorie: 'À trier', fait: false, abandonnee_le: '', parente: '' });
    el('ouvrir-chercher').click();
    transitionEcrans.terminer(ui.doc);
    const icones = ['chercher-todo', 'chercher-documents', 'chercher-media', 'chercher-photo', 'chercher-a-trier'].map(el);
    attendre(icones.every(b => b.classList.contains('bouton-autre') && b.querySelector('svg') && !b.textContent.replace(b.querySelector('.visuellement-cache').textContent, '').trim()), 'icône pas comme les autres, ou texte visible');
    attendreEgal(el('chercher-a-trier').querySelector('.visuellement-cache').textContent, 'À trier', 'nom lu par le téléphone');
    const r = icones.map(b => b.getBoundingClientRect());
    attendre(Math.abs(r[4].width - r[0].width) < 1 && r[4].top >= r[2].bottom && Math.abs((r[4].left + r[4].right) / 2 - 206) < 2, `5e icône pas centrée dessous, ou pas la même taille : ${JSON.stringify(r[4])}`);
    attendreEgal(vue.getComputedStyle(icones[4]).backgroundColor, vue.getComputedStyle(icones[0]).backgroundColor, 'pas la même allure');
    const tous = [...icones, el('chercher-champ')];
    for (const b of tous) attendre(touchable(ui, b), `${b.id} pas touchable`);
    for (let i = 0; i < tous.length; i++) for (let j = i + 1; j < tous.length; j++) attendre(!seCroisent(tous[i].getBoundingClientRect(), tous[j].getBoundingClientRect()), `${tous[i].id} chevauche ${tous[j].id}`);
    attendreEgal(sousLePetitMicro(ui, ui.doc.body), [], 'un bouton sous le petit micro');
    // Toucher « À trier ».
    el('chercher-a-trier').click();
    transitionEcrans.terminer(ui.doc);
    attendre(!el('ecran-complet').hidden && el('ecran-chercher').hidden, 'écran des tâches pas ouvert');
    attendreEgal(el('titre-vue').textContent, 'À trier', 'pas la liste « À trier »');
    const lignes = () => [...el('liste-taches').querySelectorAll('li.tache')].map(l => l.querySelector('.texte-tache').textContent.split('\n')[0]);
    const ordre = lignes();
    attendre(/dernière phrase FICTIF/.test(ordre[0]) && /deuxième/.test(ordre[1]) && /première/.test(ordre[2]) && ordre.length === 3, `pas la dernière en haut : ${JSON.stringify(ordre)}`);
    const premiere = el('liste-taches').querySelector('li.tache');
    attendre(premiere.classList.contains('derniere-ajoutee') && premiere.classList.contains('surbrillance-recherche'), 'dernière phrase pas surlignée');
    attendreEgal(el('liste-taches').querySelectorAll('.derniere-ajoutee').length, 1, 'plusieurs phrases marquées');
    // « Fermer » : retour à Chercher (règle du retour).
    el('fermer-chercher').click();
    transitionEcrans.terminer(ui.doc);
    attendre(el('ecran-complet').hidden && !el('ecran-chercher').hidden, '« Fermer » ne revient pas à Chercher');
    // Par To-do puis la tuile « À trier » : l'ordre d'avant (ordre d'ajout), sans marque.
    el('chercher-todo').click();
    transitionEcrans.terminer(ui.doc);
    const tuile = [...el('tuiles').querySelectorAll('button')].find(b => /^À trier/.test(b.textContent.trim()));
    attendre(tuile, 'tuile « À trier » introuvable');
    tuile.click();
    const ordre2 = lignes();
    attendre(/première/.test(ordre2[0]) && /dernière/.test(ordre2[2]), `ordre de la tuile changé : ${JSON.stringify(ordre2)}`);
    attendreEgal(el('liste-taches').querySelectorAll('.derniere-ajoutee').length, 0, 'marque hors de la vue de l’icône');
  });

  // ----- 09/11/2026 : mission D, FENÊTRE DE GROS CHOIX quand Cap hésite entre des commandes (accord de Max), FICTIF -----
  const TABLEUR_FICTIF_CHOIX = [
    ...TABLEUR_FICTIF_0,
    ['Ouvrir Réglages', '', 'Mot-clé', 'les réglages fictifs', 'NAV-03', ''],
    ['Navigation', '', 'Écran cible', 'les options fictives', 'NAV-02', ''],
    ['Navigation', '', 'Écran cible', 'les options fictives', 'NAV-03', ''],
    ['Navigation', '', 'Écran cible', 'le coin fictif', 'NAV-02', 'RETIRER 09/11/2026 : FICTIF, jamais lu']
  ];
  async function interfaceChoix(c, essai, { garderApprises = false } = {}) {
    const cle = commandesVocales.CLE_COPIE;
    const avantCopie = localStorage.getItem(cle);
    const lignes = commandesVocales.analyser(TABLEUR_FICTIF_CHOIX).lignes;
    localStorage.setItem(cle, JSON.stringify({ lu_le: new Date(0).toISOString(), compte: {}, lignes }));
    // 09/11/2026 (petit tableur) : les phrases apprises comptent pour le micro : chaque essai part d'une liste vide
    // (un choix fait dans un essai ne doit pas trancher l'hésitation de l'essai suivant).
    // 09/11/2026 (séance 2) : + les clés de « Commandes vocales (Cap) » (copie et tampon).
    const clesApprises = ['cap_phrases_a_apprendre_v1', 'cap_phrases_apprises_copie_v1', 'cap_phrases_tampon_v1', 'cap_tableur_cap_copie_v1', 'cap_tableur_cap_tampon_v1'];
    const avantApprises = clesApprises.map(k => localStorage.getItem(k));
    clesApprises.forEach(k => localStorage.removeItem(k));
    const nombre = TACHES.length;
    try {
      const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
      ui.cadre.contentWindow.matchMedia = q => ({ matches: /reduce/.test(q), addEventListener() {}, removeEventListener() {} }); // fermetures d'un coup
      brancherAccueil(c, ui);
      commandesNavigation.brancher(ui.doc, { geste: () => null });
      const el = id => ui.parId(id);
      // 09/11/2026 (petit tableur) : sauf pour la machine « phrase à apprendre », chaque phrase dictée part d'une liste
      // apprise vide (sinon le choix fait juste avant tranche déjà l'hésitation : c'est voulu dans Cap, pas dans ces essais).
      const dicter = phrase => { if (!garderApprises) clesApprises.forEach(k => localStorage.removeItem(k)); Object.assign(ui.dictee, { disponible: () => true, enCours: () => false, arreter() {}, demarrer(r) { r.surFinal(phrase); if (r.surFin) r.surFin(); } }); el('petit-micro').click(); transitionEcrans.terminer(ui.doc); return el('statut').textContent; };
      const signe = () => (el('signe-micro').hidden ? '' : (el('signe-micro').classList.contains('signe-pouce-visible') ? 'pouce' : 'croix'));
      const lignesChoix = () => [...el('liste-choix-commande').querySelectorAll('.ligne-choix-commande')].map(b => [b.querySelector('.numero-morceau').textContent, b.querySelector('.nom-morceau').textContent]);
      await essai({ ui, el, dicter, signe, lignesChoix, lignes, nombre });
    } finally {
      TACHES.slice(nombre).forEach(x => abandonner(x.id));
      if (avantCopie === null) localStorage.removeItem(cle); else localStorage.setItem(cle, avantCopie);
      clesApprises.forEach((k, i) => { if (avantApprises[i] === null) localStorage.removeItem(k); else localStorage.setItem(k, avantApprises[i]); });
      for (const code of Object.keys(commandesNavigation.PAS_PRET).concat(['NAV-01', 'NAV-02', 'NAV-03', 'NAV-04', 'NAV-07', 'NAV-08', 'NAV-09', 'NAV-10', 'NAV-11', 'NAV-13', 'NAV-21', 'NAV-22', 'NAV-24'])) commandesVocales.brancherAction(code, undefined);
    }
  }

  await testAsync('Gros choix des commandes (09/11/2026, faux tableur avec RETIRER) : Cap hésite → fenêtre de gros choix numérotés (une ligne chacun) + « Aucun de ces choix », ni pouce ni croix ; dire « deux » fait la 2e commande, puis le POUCE ; rien de nouveau dans « À trier »', async c => {
    await interfaceChoix(c, async ({ ui, el, dicter, signe, lignesChoix, lignes, nombre }) => {
      attendre(!lignes.some(l => /coin fictif/.test(l.formulation)), 'ligne RETIRER lue');
      const dit = dicter('ouvre les options fictives');
      attendre(el('choix-commande').open && /touche ou dis le bon numéro/.test(dit), `fenêtre pas ouverte : ${dit}`);
      attendreEgal(lignesChoix(), [['1', 'Ouvrir Autre'], ['2', 'Ouvrir Réglages']], 'choix numérotés');
      attendreEgal(el('aucun-choix-commande').textContent, 'Aucun de ces choix', 'case « Aucun »');
      attendreEgal(signe(), '', 'un signe pendant la fenêtre');
      // Une ligne chacun, grandes cases, même allure que les autres fenêtres de choix sur l'eau.
      const vue = ui.cadre.contentWindow;
      for (const b of el('liste-choix-commande').querySelectorAll('.ligne-choix-commande')) {
        attendreEgal(vue.getComputedStyle(b.querySelector('.nom-morceau')).whiteSpace, 'nowrap', 'nom sur plusieurs lignes');
        attendre(b.getBoundingClientRect().height >= 56 && touchable(ui, b), 'case trop petite ou pas touchable');
      }
      attendre(el('choix-commande').classList.contains('fenetre-choix') && vue.getComputedStyle(el('choix-commande')).backgroundColor === 'rgba(0, 0, 0, 0)', 'pas le style des fenêtres de choix (eau dessous)');
      attendreEgal(vue.getComputedStyle(el('liste-choix-commande').querySelector('.ligne-morceau')).backgroundColor, vue.getComputedStyle(el('liste-choix-voix').querySelector('.ligne-morceau') || el('liste-choix-commande').querySelector('.ligne-morceau')).backgroundColor, 'cases pas comme les autres');
      // « deux » à la voix.
      attendreEgal(dicter('deux'), 'J’ouvre Réglages.', 'numéro dit');
      attendre(!el('choix-commande').open && !el('ecran-reglages').hidden, 'Réglages pas ouvert, ou fenêtre restée');
      attendreEgal(signe(), 'pouce', 'pas de pouce après le choix');
      attendreEgal(TACHES.length, nombre, '« deux » rangé dans « À trier »');
    });
  });

  await testAsync('Gros choix des commandes (09/11/2026, FICTIF) : toucher la case 1 fait la commande 1 (pouce) ; « le numéro deux » marche aussi ; « Aucun de ces choix » (toucher ou « aucun ») ferme sans rien faire ni signe ; une autre phrase ferme la fenêtre et suit son chemin', async c => {
    await interfaceChoix(c, async ({ el, dicter, signe, nombre }) => {
      dicter('ouvre les options fictives');
      el('liste-choix-commande').querySelector('.ligne-choix-commande').click();
      attendre(!el('choix-commande').open && !el('ecran-autre').hidden, 'toucher la case 1 n’ouvre pas Autre');
      attendreEgal(signe(), 'pouce', 'pas de pouce');
      el('fermer-autre').click();
      dicter('ouvre les options fictives');
      attendreEgal(dicter('le numéro deux'), 'J’ouvre Réglages.', '« le numéro deux »');
      el('fermer-reglages').click();
      // « Aucun de ces choix » au toucher.
      dicter('ouvre les options fictives');
      el('signe-micro').hidden = true;
      el('aucun-choix-commande').click();
      attendre(!el('choix-commande').open && el('ecran-autre').hidden && el('ecran-reglages').hidden && signe() === '', '« Aucun » a fait quelque chose');
      // « aucun » à la voix.
      dicter('ouvre les options fictives');
      dicter('aucun');
      attendre(!el('choix-commande').open && el('ecran-autre').hidden && el('ecran-reglages').hidden, '« aucun » a fait quelque chose');
      // Une autre phrase : la fenêtre s'en va, la phrase va dans « À trier ».
      dicter('ouvre les options fictives');
      dicter('acheter du pain FICTIF choix');
      attendre(!el('choix-commande').open && TACHES.slice(nombre).some(x => x.intitule === 'acheter du pain FICTIF choix' && x.categorie === 'À trier'), 'autre phrase pas traitée normalement');
      // Un numéro trop grand : pas de choix, la fenêtre se ferme.
      dicter('ouvre les options fictives');
      dicter('cinq');
      attendre(!el('choix-commande').open && el('ecran-autre').hidden && el('ecran-reglages').hidden, '« cinq » a choisi quelque chose');
    });
  });

  // ----- 09/11/2026 : défaut 1 (eau sous les fenêtres « + » et crayon), FICTIF -----
  await testAsync('Défaut 1 (09/11/2026) : l’écran change de taille (clavier du téléphone) : les vagues sont GARDÉES (plus de remise à plat) ; dans les fenêtres « + » et crayon, l’eau suit le doigt ; fenêtre fermée : l’eau arrêtée repart', async c => {
    // 1. Vagues gardées au changement de taille.
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const toile = ui.doc.createElement('canvas');
    toile.style.cssText = 'position:fixed;left:0;top:0;width:412px;height:900px';
    ui.doc.body.append(toile);
    const couche = ecranEau.creerCouche(toile, { raf: () => 1, caf: () => {}, fenetre: ui.cadre.contentWindow });
    couche.demarrer();
    couche.perturber(0.5, 0.5, 60, 4);
    const energie = e => e.buf1.reduce((s, v) => s + Math.abs(v), 0);
    const avant = energie(couche.exporterEtat());
    attendre(avant > 0, 'pas de vague pour l’essai');
    toile.style.height = '500px'; // le clavier s'ouvre
    couche.dimensionner();
    const pendant = couche.exporterEtat();
    attendre(pendant.lignes !== 0 && energie(pendant) > avant * 0.2, `vagues remises à plat à l’ouverture du clavier (${energie(pendant)} contre ${avant})`);
    toile.style.height = '900px'; // le clavier se ferme
    couche.dimensionner();
    attendre(energie(couche.exporterEtat()) > avant * 0.2, 'vagues remises à plat à la fermeture du clavier');
    toile.remove();
    // 2. L'eau suit le doigt dans les deux fenêtres de saisie (pas dans une fenêtre ordinaire).
    const ui2 = preparerInterface(c, { largeur: 412, hauteur: 900 });
    brancherAccueil(c, ui2);
    const vue = ui2.cadre.contentWindow;
    const eau = ecranEau.eauAccueil(ui2.doc, { raf: () => 1, caf: () => {} });
    eau.demarrer();
    for (const id of ['ajout-tache', 'clavier']) {
      const d = ui2.parId(id);
      d.showModal();
      const n = eau.etat().touchers;
      d.dispatchEvent(new vue.PointerEvent('pointerdown', { bubbles: true, pointerId: 5, clientX: 200, clientY: 400, buttons: 1 }));
      attendre(eau.etat().touchers > n, `l’eau ne suit pas le doigt dans « ${id} »`);
      d.close();
    }
    const aide = ui2.parId('aide');
    aide.showModal();
    const n2 = eau.etat().touchers;
    aide.dispatchEvent(new vue.PointerEvent('pointerdown', { bubbles: true, pointerId: 6, clientX: 200, clientY: 400, buttons: 1 }));
    attendreEgal(eau.etat().touchers, n2, 'l’eau bouge sous une fenêtre ordinaire');
    aide.close();
    eau.arreter();
    // 3. Filet : l'eau d'accueil arrêtée repart quand une fenêtre (pas plein écran) se ferme.
    const ui3 = preparerInterface(c, { largeur: 412, hauteur: 900 });
    let actif = false, demarrages = 0;
    const fond = { demarrer() { actif = true; demarrages++; }, arreter() { actif = false; }, etat: () => ({ active: actif }) };
    brancherAccueil(c, ui3, { eau: { fond, changerCouleurs() {}, eauActive: () => true } });
    actif = false;
    const d3 = ui3.parId('ajout-tache');
    d3.showModal();
    await pause();
    d3.close();
    await pause();
    attendre(actif && demarrages >= 1, 'l’eau arrêtée ne repart pas à la fermeture');
  });

  // ----- 09/11/2026 : défaut 3 (« deux » au petit micro dans la fenêtre de choix = « je n'ai rien entendu »), FICTIF -----
  await testAsync('Défaut 3 (09/11/2026, faux tableur avec RETIRER) : comme Android pour un mot court (mot provisoire, puis « pas trouvé ») : « deux » choisit la 2e commande (pouce) ; « de » et « d’eux » aussi ; hors fenêtre, la phrase provisoire compte ; sans aucun mot : « rien entendu » comme avant', async c => {
    await interfaceChoix(c, async ({ ui, el, dicter, signe, nombre }) => {
      // Faux micro « à la manière d'Android » : le mot arrive en provisoire, puis l'erreur « pas trouvé », puis la fin.
      const motCourt = mot => {
        Object.assign(ui.dictee, { disponible: () => true, enCours: () => false, arreter() {}, demarrer(r) { if (mot) r.surProvisoire(mot); r.surErreur('no-speech'); if (r.surFin) r.surFin(); } });
        el('petit-micro').click();
        transitionEcrans.terminer(ui.doc);
        return el('statut').textContent;
      };
      for (const [mot, attendu] of [['deux', 'ecran-reglages'], ['de', 'ecran-reglages'], ['d’eux', 'ecran-reglages'], ['un', 'ecran-autre']]) {
        dicter('ouvre les options fictives');
        attendre(el('choix-commande').open, 'fenêtre pas ouverte');
        motCourt(mot);
        attendre(!el('choix-commande').open && !el(attendu).hidden, `« ${mot} » (mot court) n’a pas choisi ${attendu}`);
        attendreEgal(signe(), 'pouce', `pas de pouce pour « ${mot} »`);
        el(attendu === 'ecran-autre' ? 'fermer-autre' : 'fermer-reglages').click();
        transitionEcrans.terminer(ui.doc);
      }
      // Hors fenêtre : la phrase provisoire suit son chemin (ici « À trier »).
      motCourt('acheter du riz FICTIF provisoire');
      attendre(TACHES.slice(nombre).some(x => x.intitule === 'acheter du riz FICTIF provisoire'), 'phrase provisoire perdue');
      // Aucun mot : « rien entendu », croix.
      attendre(/rien entendu/.test(motCourt('')), '« rien entendu » perdu');
      attendreEgal(signe(), 'croix', 'pas de croix');
    });
  });

  // ----- 09/11/2026 : défaut 4 (« document suivant » visionneuse fermée), FICTIF -----
  await testAsync('Défaut 4 (09/11/2026, FICTIF) : visionneuse FERMÉE : « document suivant » ouvre le document d’après le dernier ouvert (dans la visionneuse) ; au bout de la liste ou sans document ouvert avant : Cap le DIT (« Il n’y a pas de document suivant »), et rien ne s’ouvre', async c => {
    try {
      const { el, v, vis, dire, liste } = visionneuse3c(c, 3);
      // Aucun document ouvert avant.
      attendre(/^Il n’y a pas de document suivant/.test(vis.documentVoisin(1)), 'sans document ouvert : pas dit clairement');
      attendre(!el('visionneuse-cap').open, 'quelque chose s’est ouvert');
      // Vignettes, toucher le 1er, puis tout fermer.
      await vis.ouvrir(liste);
      el('grille-vignettes').querySelector('.vignette').click();
      await attendreQue(() => v.appels.filter(x => x[0] === 'montrer').length === 1, '1er document pas ouvert');
      el('fermer-visionneuse').click();
      el('fermer-vignettes').click();
      await attendreQue(() => !el('vignettes-cap').open && !el('visionneuse-cap').open, 'pas tout fermé');
      // « le suivant » (la voix) : le 2e s'ouvre dans la visionneuse.
      attendreEgal(vis.documentVoisin(1), 'J’ouvre le document suivant.', 'suivant');
      await attendreQue(() => el('visionneuse-cap').open && v.appels.filter(x => x[0] === 'montrer').length === 2, '2e document pas ouvert');
      el('fermer-visionneuse').click();
      attendreEgal(vis.documentVoisin(1), 'J’ouvre le document suivant.', 'suivant encore');
      await attendreQue(() => v.appels.filter(x => x[0] === 'montrer').length === 3, '3e document pas ouvert');
      el('fermer-visionneuse').click();
      attendreEgal(vis.documentVoisin(1), 'Il n’y a pas de document suivant.', 'au bout de la liste');
      attendre(!el('visionneuse-cap').open, 'quelque chose s’est ouvert au bout');
      attendreEgal(vis.documentVoisin(-1), 'J’ouvre le document précédent.', 'précédent');
      void dire;
    } finally { debrancherVision(); }
  });

  // ----- 09/11/2026 : partie C, ÉCRANS DITS SEULS (accord de Max), faux tableur bâti comme le vrai, FICTIF -----
  const ECRANS_SEULS = [
    // [phrase dite seule, code, formulation « Écran cible », réponse attendue, prêt ?]
    ['les réglages', 'NAV-03', 'les réglages', 'J’ouvre Réglages.', true],
    ['les paramètres', 'NAV-03', 'les paramètres', 'J’ouvre Réglages.', true],
    ['le scanner', 'NAV-04', 'le scanner', 'J’ouvre le scanner.', true],
    ['l’agenda', 'NAV-05', 'l’agenda', 'Agenda : pas encore prêt.', false],
    ['mon calendrier', 'NAV-05', 'mon calendrier', 'Agenda : pas encore prêt.', false],
    ['mes notes', 'NAV-06', 'mes notes', 'Notes : pas encore prêt.', false],
    ['l’accueil', 'NAV-07', 'l’accueil', 'Retour à l’accueil.', true],
    ['la liste de courses', 'NAV-12', 'la liste de courses', 'La liste de courses : pas encore prêt.', false],
    ['mes tâches', 'NAV-13', 'mes tâches', 'J’ouvre tes tâches.', true],
    ['mon échéancier', 'NAV-14', 'mon échéancier', 'L’échéancier : pas encore prêt.', false],
    ['le journal de bord', 'NAV-15', 'le journal de bord', 'Le journal de bord : pas encore prêt.', false],
    ['le dictionnaire', 'NAV-16', 'le dictionnaire', 'Le dictionnaire des personnes : pas encore prêt.', false],
    ['ma biographie', 'NAV-17', 'ma biographie', 'La biographie : pas encore prêt.', false],
    ['mes archives', 'NAV-18', 'mes archives', 'Les archives : pas encore prêt.', false],
    ['mes mails', 'NAV-19', 'mes mails', 'Les mails : pas encore prêt.', false],
    ['mes contacts', 'NAV-20', 'mes contacts', 'Le répertoire : pas encore prêt.', false],
    ['l’aide', 'NAV-21', 'l’aide', 'J’ouvre l’aide.', true],
    ['mon profil', 'NAV-23', 'mon profil', 'Le profil : pas encore prêt.', false]
  ];
  const TABLEUR_FICTIF_ECRANS = [
    TABLEUR_FICTIF_0[0],
    ['Ouvrir un écran de l’application', 'Navigation', 'Verbe d’ouverture', 'ouvre', 'COMMUN', ''],
    ['Ouvrir un écran de l’application', 'Navigation', 'Verbe d’ouverture', 'montre-moi', 'COMMUN', ''],
    ...ECRANS_SEULS.map(([, code, formulation]) => ['Ouvrir un écran de l’application', 'Navigation', 'Écran cible', formulation, code, '']),
    ['Ouvrir Autre', '', 'Mot-clé', 'autre', 'NAV-02', ''],
    ['Ouvrir un écran de l’application', 'Navigation', 'Écran cible', 'le carnet fictif', 'NAV-06', 'RETIRER 09/11/2026 : FICTIF, jamais lu']
  ];
  async function interfaceEcrans(c, essai) {
    const cle = commandesVocales.CLE_COPIE;
    const avantCopie = localStorage.getItem(cle);
    const lignes = commandesVocales.analyser(TABLEUR_FICTIF_ECRANS).lignes;
    localStorage.setItem(cle, JSON.stringify({ lu_le: new Date(0).toISOString(), compte: {}, lignes }));
    const nombre = TACHES.length;
    try {
      const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
      brancherAccueil(c, ui);
      commandesNavigation.brancher(ui.doc, { geste: () => null });
      const el = id => ui.parId(id);
      const dicter = phrase => { Object.assign(ui.dictee, { disponible: () => true, enCours: () => false, arreter() {}, demarrer(r) { r.surFinal(phrase); if (r.surFin) r.surFin(); } }); el('petit-micro').click(); transitionEcrans.terminer(ui.doc); return el('statut').textContent; };
      const signe = () => (el('signe-micro').hidden ? '' : (el('signe-micro').classList.contains('signe-pouce-visible') ? 'pouce' : 'croix'));
      await essai({ ui, el, dicter, signe, lignes, nombre });
    } finally {
      TACHES.slice(nombre).forEach(x => abandonner(x.id));
      if (avantCopie === null) localStorage.removeItem(cle); else localStorage.setItem(cle, avantCopie);
      for (const code of Object.keys(commandesNavigation.PAS_PRET).concat(['NAV-01', 'NAV-02', 'NAV-03', 'NAV-04', 'NAV-07', 'NAV-08', 'NAV-09', 'NAV-10', 'NAV-11', 'NAV-13', 'NAV-21', 'NAV-22', 'NAV-24'])) commandesVocales.brancherAction(code, undefined);
    }
  }
  // Un test par écran, qui reproduit ce que Max dit.
  for (const [phrase, code, , reponse, pret] of ECRANS_SEULS) {
    await testAsync(`Écran dit seul (09/11/2026, faux tableur avec RETIRER) : « ${phrase} » (${code}) → « ${reponse} »${pret ? '' : ' et la croix'} ; rien dans « À trier »`, async c => {
      await interfaceEcrans(c, async ({ el, dicter, signe, nombre }) => {
        attendreEgal(dicter(phrase), reponse, 'réponse');
        attendreEgal(TACHES.length, nombre, 'phrase rangée dans « À trier »');
        if (!pret) attendreEgal(signe(), 'croix', 'pas de croix pour un écran pas encore prêt');
        else attendreEgal(signe(), 'pouce', 'pas de pouce');
        for (const d of el('petit-micro').ownerDocument.querySelectorAll('dialog[open]')) d.close();
      });
    });
  }
  await testAsync('Écrans dits seuls (09/11/2026, faux tableur avec RETIRER) : rien de cassé : avec un verbe (« ouvre mes notes », « montre-moi les réglages ») ça marche toujours ; un MOT-CLÉ seul (« autre »), une phrase plus longue (« mes notes de cours FICTIF ») et une ligne RETIRER (« le carnet fictif ») vont dans « À trier »', async c => {
    await interfaceEcrans(c, async ({ el, dicter, lignes, nombre }) => {
      attendreEgal(dicter('ouvre mes notes'), 'Notes : pas encore prêt.', 'avec verbe');
      attendreEgal(dicter('montre-moi les réglages'), 'J’ouvre Réglages.', 'avec verbe');
      el('fermer-reglages').click();
      attendre(!lignes.some(l => /carnet fictif/.test(l.formulation)), 'ligne RETIRER lue');
      for (const phrase of ['autre', 'mes notes de cours FICTIF', 'le carnet fictif']) {
        dicter(phrase);
        attendre(TACHES.slice(nombre).some(x => x.intitule === phrase && x.categorie === 'À trier'), `« ${phrase} » pas rangé dans « À trier »`);
      }
    });
  });

  // ----- 09/11/2026 : défauts vus par Max sur c67 (faux tableur bâti comme le vrai, FICTIF) -----
  const TABLEUR_FICTIF_C67 = [
    TABLEUR_FICTIF_0[0],
    ['Ouvrir un écran de l’application', 'Navigation', 'Verbe d’ouverture', 'ouvre', 'COMMUN', ''],
    ['Ouvrir un écran de l’application', 'Navigation', 'Écran cible', 'mes notes', 'NAV-06', ''],
    ['Lire les notes', '', 'Variante de transcription', 'les notes', 'NAV-06', ''], // comme le vrai : « les notes » ET « mes notes »
    ['Document suivant', '', 'Verbe de passage au suivant', 'passe', 'VIS-04', ''],
    ['Document suivant', '', 'Mot-clé', 'le document suivant', 'VIS-04', ''],
    ['Document suivant', '', 'Mot-clé', 'le suivant', 'VIS-04', ''],
    ['Document suivant', '', 'Expression complète', 'ouvre le document suivant', 'VIS-04', ''],
    ['Morceau suivant', '', 'Verbe de passage au suivant', 'passe', 'MUS-12', ''],
    ['Morceau suivant', '', 'Mot-clé', 'le morceau suivant', 'MUS-12', ''],
    ['Morceau suivant', '', 'Mot-clé', 'le suivant', 'MUS-12', ''],
    ['Morceau suivant', '', 'Mot-clé', 'la piste fictive suivante', 'MUS-12', 'RETIRER 09/11/2026 : FICTIF, jamais lu']
  ];
  test('Défauts 1, 4 et 6 (09/11/2026, faux tableur bâti comme le vrai, avec RETIRER) : « mes notes de cours » n’est PLUS une commande (le verbe et le mot-clé ne peuvent pas être le même bout de phrase) ; « document suivant » et « morceau suivant » SANS « le » sont reconnus ; « suivant » seul ne déclenche rien', () => {
    const lignes = commandesVocales.analyser(TABLEUR_FICTIF_C67).lignes;
    const r = (p, ouvert = '') => commandesVocales.reconnaitre(p, lignes, { ouvert });
    attendreEgal(r('mes notes de cours FICTIF').statut === 'reconnu', false, '« mes notes de cours » reconnu (défaut 1)');
    attendreEgal([r('mes notes').code, r('ouvre mes notes').code], ['NAV-06', 'NAV-06'], '« mes notes » cassé');
    attendreEgal([r('document suivant').code, r('le document suivant').code, r('ouvre le document suivant').code], ['VIS-04', 'VIS-04', 'VIS-04'], 'document suivant');
    attendreEgal([r('morceau suivant').code, r('le morceau suivant').code, r('passe au morceau suivant').code], ['MUS-12', 'MUS-12', 'MUS-12'], 'morceau suivant');
    attendreEgal(r('le suivant', 'lecteur').code, 'MUS-12', '« le suivant » avec le lecteur');
    attendre(r('suivant').statut !== 'reconnu' && r('passe le rendez-vous suivant FICTIF').code !== 'VIS-04', '« suivant » seul ou au milieu d’une phrase déclenche une commande');
    attendre(!lignes.some(l => /piste fictive/.test(l.formulation)) && r('piste fictive suivante').statut !== 'reconnu', 'ligne RETIRER lue');
  });

  await testAsync('Défaut 6 (09/11/2026, FICTIF) : « document suivant » dit au micro, visionneuse FERMÉE et rien ouvert avant : Cap DIT « Il n’y a pas de document suivant » (croix), rien n’est rangé dans « À trier » ni dans une autre catégorie', async c => {
    try {
      const v3 = visionneuse3c(c, 3);
      const lignes = commandesVocales.analyser(TABLEUR_FICTIF_C67).lignes;
      const d = commandesVocales.deciderMicro('document suivant', { lignes, contexte: { ouvert: '' } });
      attendre(d && d.code === 'VIS-04' && /^Il n’y a pas de document suivant/.test(d.message), `réponse : ${JSON.stringify(d)}`);
      void v3;
    } finally { debrancherVision(); }
  });

  await testAsync('Défaut 2 (09/11/2026, FICTIF) : fenêtre de gros choix ouverte, Android ne transmet RIEN (« deux » perdu) : Cap dit comment répondre (« Dis « numéro deux », ou touche la case. »), la fenêtre reste ; « le numéro deux » choisit bien', async c => {
    await interfaceChoix(c, async ({ ui, el, dicter }) => {
      dicter('ouvre les options fictives');
      attendre(el('choix-commande').open, 'fenêtre pas ouverte');
      Object.assign(ui.dictee, { disponible: () => true, enCours: () => false, arreter() {}, demarrer(r) { r.surErreur('no-speech'); if (r.surFin) r.surFin(); } });
      el('petit-micro').click();
      attendre(/Dis « numéro deux », ou touche la case/.test(el('statut').textContent) && /numéro deux/.test(el('bulle-micro').textContent), 'pas d’aide pour répondre');
      attendre(el('choix-commande').open, 'la fenêtre s’est fermée');
      attendreEgal(dicter('le numéro deux'), 'J’ouvre Réglages.', '« le numéro deux »');
    });
  });

  await testAsync('Défaut 3 (09/11/2026, FICTIF) : fenêtre du « + » : le geste de haut en bas parti du CHAMP de l’intitulé ou d’une liste à choisir la ferme ; parti de la note (plusieurs lignes) : non ; texte tapé : Cap demande « garder / jeter » (rien de perdu)', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    brancherAccueil(c, ui);
    const temps = { t: 0 };
    brancherGesteRetour(c, ui, temps);
    const el = id => ui.parId(id);
    const d = el('ajout-tache');
    for (const depart of ['intitule', 'priorite']) {
      d.showModal();
      d.scrollTop = 0;
      glisserRetour(ui, temps, el(depart), NET);
      await attendreQue(() => !d.open, `pas fermée depuis « ${depart} »`);
    }
    d.showModal();
    glisserRetour(ui, temps, el('note'), NET);
    await attendreMs(550);
    attendre(d.open, 'fermée depuis la note (plusieurs lignes)');
    // Texte tapé : la question « garder / jeter » (règle zéro perte), pas une fermeture.
    el('intitule').value = 'acheter du pain FICTIF geste';
    el('intitule').dispatchEvent(new Event('input', { bubbles: true }));
    glisserRetour(ui, temps, el('intitule'), NET);
    await attendreMs(550);
    attendre(d.open && d.querySelector('.question-fermeture'), 'texte tapé : pas de question « garder / jeter »');
    el('intitule').value = '';
    d.close();
  });

  await testAsync('Défaut 5 (09/11/2026, FICTIF) : la fenêtre de gros choix ouverte PAR-DESSUS « Musique » reçoit le petit micro (et la bulle, et le signe) : il est touchable ; à sa fermeture, il revient dans « Musique »', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    brancherAccueil(c, ui);
    const el = id => ui.parId(id);
    el('musique-relations').showModal();
    await pause();
    attendre(el('musique-relations').contains(el('petit-micro')), 'micro pas dans « Musique »');
    el('liste-choix-commande').replaceChildren();
    choixSurEau.ouvrir(el('choix-commande'));
    await pause();
    for (const id of ['petit-micro', 'bulle-micro', 'signe-micro']) attendre(el('choix-commande').contains(el(id)), `${id} pas dans la fenêtre de choix (du dessus)`);
    el('choix-commande').classList.remove('choix-entree');
    attendre(touchable(ui, el('petit-micro')), 'micro pas touchable dans la fenêtre de choix');
    el('choix-commande').close();
    await pause();
    attendre(el('musique-relations').contains(el('petit-micro')), 'micro pas revenu dans « Musique »');
    el('musique-relations').close();
  });

  // ----- 09/11/2026 : partie 2 A, MENU de recherche (« Tout » par défaut) et propositions dans Chercher (accord de Max), FICTIF -----
  await testAsync('Recherche partout (09/11/2026, FICTIF) : barre de Chercher = même menu, « Tout » par défaut ; propositions DÈS LA PREMIÈRE LETTRE (tâche, rendez-vous, personne), 6 au plus, chacune dit ce qu’elle est ; les toucher mène directement au résultat ; les trois barres disent « Chercher »', async c => {
    c.localStorage.setItem('cap_google_rendezvous_v1', JSON.stringify({ rendezvous: [{ titre: 'Pelote FICTIVE répétition', lieu: 'Salle FICTIVE', description: '', date: '2030-01-10', heure: '14:32' }] }));
    c.TACHES.push({ ...TACHES_FICTIVES[0], id: 'FICTIF-pelote', intitule: 'Pelote FICTIVE à rendre', categorie: 'À trier', fait: false, abandonnee_le: '', parente: '' });
    const contact = annuaire.creerContact({ prenom: 'Pelote', nom: 'FICTIVE' });
    try {
      const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
      brancherAccueil(c, ui);
      const el = id => ui.parId(id);
      for (const id of ['chercher-champ', 'saisie-recherche', 'recherche-contacts']) attendreEgal(el(id).getAttribute('placeholder'), 'Chercher', `texte de la barre ${id}`);
      attendreEgal([...el('chercher-source').options].map(o => o.textContent), [...el('source-recherche').options].map(o => o.textContent), 'pas le même menu');
      attendreEgal(el('chercher-source').value, 'tout', '« Tout » pas par défaut');
      el('ouvrir-chercher').click();
      transitionEcrans.terminer(ui.doc);
      const champ = el('chercher-champ');
      const taper = texte => { champ.value = texte; champ.dispatchEvent(new Event('input', { bubbles: true })); return [...el('propositions-chercher').querySelectorAll('.proposition-chercher')].map(b => b.textContent); };
      const une = taper('p');
      attendre(!el('propositions-chercher').hidden && une.length >= 1 && une.length <= 6, `pas de proposition dès la 1re lettre : ${JSON.stringify(une)}`);
      const props = taper('pelote');
      attendre(props.some(x => /^Tâche · Pelote FICTIVE à rendre/.test(x)) && props.some(x => /^Rendez-vous · /.test(x) && /Pelote FICTIVE/.test(x)) && props.some(x => /^Personne · Pelote/.test(x)), `tâche, rendez-vous ou personne manquant : ${JSON.stringify(props)}`);
      for (const b of el('propositions-chercher').querySelectorAll('.proposition-chercher')) attendre(touchable(ui, b), 'proposition pas touchable');
      // Restreindre : « Personnes ».
      el('chercher-source').value = 'personnes';
      el('chercher-source').dispatchEvent(new Event('change'));
      attendre(taper('pelote').every(x => /^Personne · /.test(x)), '« Personnes » montre autre chose');
      // Toucher la personne : sa fiche.
      [...el('propositions-chercher').querySelectorAll('.proposition-chercher')][0].click();
      // La fiche des personnes (fiche_contact.js) est branchée sur la page de test elle-même (une seule page dans Cap).
      attendre(ui.doc.querySelector('dialog[open]') || document.querySelector('#annuaire[open]'), 'fiche de la personne pas ouverte');
      for (const d of [...ui.doc.querySelectorAll('dialog[open]'), ...document.querySelectorAll('#annuaire[open]')]) d.close();
      // Toucher la tâche : l'écran des tâches, la tâche surlignée ; « Fermer » revient à Chercher.
      el('chercher-source').value = 'tout';
      el('chercher-source').dispatchEvent(new Event('change'));
      taper('pelote');
      [...el('propositions-chercher').querySelectorAll('.proposition-chercher')].find(b => /^Tâche/.test(b.textContent)).click();
      transitionEcrans.terminer(ui.doc);
      attendre(!el('ecran-complet').hidden && el('liste-taches').querySelector('.surbrillance-recherche'), 'tâche pas ouverte ni surlignée');
      el('fermer-chercher').click();
      transitionEcrans.terminer(ui.doc);
      attendre(!el('ecran-chercher').hidden, '« Fermer » ne revient pas à Chercher');
      // Rien tapé : pas de proposition.
      attendreEgal(taper('').length, 0, 'propositions sans texte');
      attendre(el('propositions-chercher').hidden, 'liste vide pas cachée');
    } finally { annuaire.supprimerContact(contact.id); }
  });

  await testAsync('Recherche partout (09/11/2026, FICTIF) : barre de l’écran des tâches : « Tout » cherche tâches, rendez-vous ET personnes (chacun dit ce qu’il est) ; « Personnes » seulement les personnes ; « Rien trouvé nulle part »', async c => {
    c.TACHES.push({ ...TACHES_FICTIVES[0], id: 'FICTIF-bobine', intitule: 'Bobine FICTIVE à coudre', categorie: 'À trier', fait: false, abandonnee_le: '', parente: '' });
    const contact = annuaire.creerContact({ prenom: 'Bobine', nom: 'FICTIVE' });
    try {
      const ui = preparerInterface(c);
      const champ = ui.parId('saisie-recherche');
      const liste = ui.parId('resultats-recherche');
      const chercher = texte => { champ.value = texte; champ.dispatchEvent(new Event('input')); return [...liste.querySelectorAll('.resultat-recherche')].map(b => b.textContent); };
      attendreEgal(ui.parId('source-recherche').value, 'tout', 'pas « Tout »');
      const tout = chercher('bobine');
      attendre(tout.some(x => /^Tâche · Bobine FICTIVE/.test(x)) && tout.some(x => /^Personne · Bobine/.test(x)), `« Tout » incomplet : ${JSON.stringify(tout)}`);
      ui.parId('source-recherche').value = 'personnes';
      ui.parId('source-recherche').dispatchEvent(new Event('change'));
      attendre(chercher('bobine').every(x => /^Personne · /.test(x)), '« Personnes » montre autre chose');
      ui.parId('source-recherche').value = 'tout';
      chercher('zzz introuvable FICTIF');
      attendreEgal(liste.textContent.trim(), 'Rien trouvé nulle part', 'message');
    } finally { annuaire.supprimerContact(contact.id); }
  });

  // ----- 09/11/2026 : proposition B, « morceau suivant » sans musique en cours (accord de Max), FAUX Drive FICTIF -----
  await testAsync('Morceau suivant sans musique (09/11/2026, FAUX Drive FICTIF) : rien joué depuis l’ouverture : Cap le DIT (croix) ; après une musique ARRÊTÉE : le morceau d’après se lance EN ARRIÈRE-PLAN (note, lecteur fermé) ; au bout de la liste : dit', async c => {
    try {
      const { el, appels, tele, dire } = await musiqueALancer(c);
      attendreEgal(tele.suivant(), 'Il n’y a pas de morceau suivant : aucune musique n’a été lancée.', 'rien joué');
      attendreEgal(appels.length, 0, 'un morceau lancé sans musique avant');
      // Un morceau joué (sa liste : les morceaux du même dossier), puis arrêté.
      await dire('mets-moi trois');
      await attendreQue(() => appels.length >= 1, 'morceau pas lancé');
      const premier = appels[appels.length - 1][1];
      tele.arreter();
      await attendreMs(450); // le fondu du son (300 ms) se termine : la musique est vraiment arrêtée
      attendre(!tele.etat().actif, 'musique pas arrêtée');
      // Le morceau d'après « Trois » est « Énorme », exprès trop gros (70 Mo) : Cap le dit et ne le charge pas.
      attendreEgal(tele.suivant(), 'Je mets le morceau suivant : « Énorme FICTIF ».', 'suivant (trop gros)');
      await attendreQue(() => /trop gros/.test(el('etat-lecteur-mp3').textContent), 'trop gros pas dit');
      const n = appels.filter(x => x[0] === 'jouer').length;
      const reponse = tele.suivant(); // le suivant encore : un morceau normal
      attendre(/^Je mets le morceau suivant : « .+ »\.$/.test(reponse), `réponse : ${reponse}`);
      await attendreQue(() => appels.filter(x => x[0] === 'jouer').length === n + 1, `morceau suivant pas lancé : ${JSON.stringify(appels)} ${JSON.stringify(tele.etat())} ${el('etat-lecteur-mp3').textContent}`);
      attendre(appels[appels.length - 1][1] !== premier, 'le même morceau relancé');
      attendre(tele.etat().arrierePlan && !el('lecteur-mp3-relations').open && !el('indicateur-musique').hidden, 'pas en arrière-plan (ou lecteur ouvert)');
      // Au bout de la liste (sans musique en cours) : dit, rien ne se lance.
      for (let i = 0; i < 8; i++) {
        if (tele.etat().actif) { tele.arreter(); await attendreMs(450); }
        if (!/^Je mets/.test(tele.suivant())) break;
        await attendreMs(300);
      }
      if (tele.etat().actif) { tele.arreter(); await attendreMs(450); }
      attendreEgal(tele.suivant(), 'C’est le dernier morceau de la liste.', 'bout de la liste');
    } finally { debrancherMusiqueTout(); }
  });

  // ----- 09/11/2026 : MACHINE « PHRASE À APPRENDRE » (accord de Max), phrases FICTIVES, faux tableur avec RETIRER -----
  const fauxStockage = () => { const m = new Map(); return { getItem: k => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)), removeItem: k => m.delete(k) }; };
  test('Phrases à apprendre (09/11/2026, FICTIF) : UNE liste : ajout (phrase, commande, date, origine) ; même phrase + même commande = « deja », rien d’ajouté ; autre commande = « conflit », rien changé ; garder la nouvelle ; « Retirer » ; « Copier tout » aux colonnes du tableur', () => {
    const s = fauxStockage();
    const maintenant = Date.UTC(2030, 0, 10, 9, 0, 0);
    attendreEgal(phrasesApprendre.ajouter(s, { phrase: 'ouvre la boîte fictive', code: 'NAV-03', commande: 'Ouvrir Réglages', origine: 'bouton' }, maintenant).statut, 'ajoutee', 'ajout');
    attendreEgal(phrasesApprendre.ajouter(s, { phrase: 'Ouvre la BOÎTE fictive !', code: 'NAV-03', commande: 'Ouvrir Réglages', origine: 'bouton' }, maintenant).statut, 'deja', 'doublon (même phrase pliée)');
    const conflit = phrasesApprendre.ajouter(s, { phrase: 'ouvre la boîte fictive', code: 'NAV-02', commande: 'Ouvrir Autre', origine: 'hesitation' }, maintenant);
    attendre(conflit.statut === 'conflit' && conflit.existante.code === 'NAV-03', 'conflit pas vu');
    attendreEgal(phrasesApprendre.lire(s).length, 1, 'doublon ajouté');
    phrasesApprendre.garderNouvelle(s, { phrase: 'ouvre la boîte fictive', code: 'NAV-02', commande: 'Ouvrir Autre', origine: 'hesitation' }, maintenant);
    attendreEgal(phrasesApprendre.lire(s).map(e => [e.code, e.origine]), [['NAV-02', 'hésitation']], 'nouvelle pas gardée');
    phrasesApprendre.ajouter(s, { phrase: 'range le grenier fictif', code: '', origine: 'bouton' }, maintenant);
    const lignes = phrasesApprendre.texteACopier(phrasesApprendre.lire(s)).split('\n').map(l => l.split('\t'));
    attendreEgal(lignes[0].slice(0, 5), ['À traiter à la main', '', 'Expression seule (Cap)', 'range le grenier fictif', ''], 'copie « aucune commande »');
    attendreEgal(lignes[1].slice(0, 5), ['Ouvrir Autre', '', 'Expression seule (Cap)', 'ouvre la boîte fictive', 'NAV-02'], 'copie');
    attendre(/^Ajoutée par Cap le \d\d\/\d\d\/\d{4} \(hésitation\)$/.test(lignes[1][5]), `remarque : ${lignes[1][5]}`);
    attendreEgal(phrasesApprendre.retirer(s, 0), 1, 'retirer');
    attendreEgal(phrasesApprendre.ajouter(s, { phrase: '   ', code: 'NAV-02' }).statut, 'vide', 'phrase vide');
  });

  test('Phrases à apprendre (09/11/2026, faux tableur avec RETIRER) : le CODE propose les commandes les plus proches (mots en commun), les familles (Navigation…), jamais une ligne RETIRER', () => {
    const lignes = commandesVocales.analyser(TABLEUR_FICTIF_CHOIX).lignes;
    const p = commandesVocales.proches('montre les options fictives stp', lignes, 5).map(x => x.code);
    attendre(p.includes('NAV-02') && p.includes('NAV-03') && p.length <= 5, `proches : ${JSON.stringify(p)}`);
    attendreEgal(commandesVocales.proches('zzz qqq', lignes, 5), [], 'rien de proche');
    const fs = commandesVocales.familles(lignes);
    attendre(fs.some(f => f.nom === 'Navigation' && f.codes.some(c => c.code === 'NAV-03')), 'famille Navigation');
    attendre(!commandesVocales.codesConnus(lignes).some(c => c.termes.some(x => /coin fictif/.test(x.terme || ''))), 'ligne RETIRER lue');
  });

  await testAsync('Phrases à apprendre (09/11/2026, FICTIF) : la machine ne parle à personne : son fichier n’a aucun appel réseau ni IA', async () => {
    const src = SOURCE_PHRASES_APPRENDRE_TEST;
    for (const mot of ['fetch(', 'XMLHttpRequest', 'sendBeacon', 'cerveau', 'anthropic', 'claude', 'googleapis', 'sheets']) attendre(!src.toLowerCase().includes(mot.toLowerCase()), `phrases_apprendre.js contient « ${mot} »`);
  });

  await testAsync('Rang dans un choix (09/11/2026, bloc c74, faux tableur avec RETIRER) : fenêtre de gros choix : « la deuxième » fait la 2e commande, « le premier » la 1re ; « le troisième » sur 2 choix : rien de fait', async c => {
    await interfaceChoix(c, async ({ el, dicter, signe }) => {
      dicter('ouvre les options fictives');
      attendre(el('choix-commande').open, 'fenêtre pas ouverte');
      attendreEgal(dicter('la deuxième'), 'J’ouvre Réglages.', 'la deuxième');
      attendreEgal(signe(), 'pouce', 'signe');
      dicter('ouvre les options fictives');
      attendreEgal(dicter('le premier'), 'J’ouvre Autre.', 'le premier');
    });
  });

  async function interfaceApprendre(c, essai) {
    const avant = localStorage.getItem('cap_phrases_a_apprendre_v1');
    localStorage.removeItem('cap_phrases_a_apprendre_v1');
    try {
      await interfaceChoix(c, async x => {
        const { ui, el } = x;
        // Faux micro : la prochaine écoute rend « phrase » (ou rien).
        const prochaine = phrase => Object.assign(ui.dictee, { disponible: () => true, enCours: () => false, arreter() {}, demarrer(r) { if (phrase) r.surFinal(phrase); else r.surErreur('no-speech'); if (r.surFin) r.surFin(); } });
        const cases = () => [...el('liste-choix-commande').querySelectorAll('.nom-morceau')].map(n => n.textContent);
        const toucher = texte => { const b = [...el('liste-choix-commande').querySelectorAll('.ligne-choix-commande')].find(x2 => x2.querySelector('.nom-morceau').textContent === texte); attendre(b, `case « ${texte} » absente : ${JSON.stringify(cases())}`); b.click(); };
        const question = () => (el('question-choix-commande').hidden ? '' : el('question-choix-commande').textContent);
        const liste = () => JSON.parse(localStorage.getItem('cap_phrases_a_apprendre_v1') || '[]');
        const ecouter = () => { const d = [...c.delais.entries()].find(([, y]) => y.delai === 400); attendre(d, 'pas d’écoute prévue (0,4 s)'); c.delais.delete(d[0]); d[1].rappel(); };
        await essai({ ...x, prochaine, cases, toucher, question, liste, ecouter });
      }, { garderApprises: true });
    } finally {
      if (avant === null) localStorage.removeItem('cap_phrases_a_apprendre_v1'); else localStorage.setItem('cap_phrases_a_apprendre_v1', avant);
    }
  }

  await testAsync('Phrases à apprendre (09/11/2026, FICTIF, faux tableur avec RETIRER) : ordre refusé → bouton → « Reprendre ? » / redire → « J’ai compris : … » (Oui) → commandes proches + « Autres commandes » (famille) → « c’est bien ça ? » (« numéro un » à la voix) → rangée : pouce, nombre 1 ; doublon : dit ; autre commande : laquelle garder', async c => {
    await interfaceApprendre(c, async ({ ui, el, dicter, signe, prochaine, cases, toucher, question, liste, ecouter }) => {
      attendre(el('compte-apprendre').hidden && /0 en attente/.test(el('bouton-apprendre').getAttribute('aria-label')), 'nombre au départ');
      dicter('ouvre la boîte fictive'); // pas une commande : rangée dans « À trier », et gardée comme phrase refusée
      el('signe-micro').hidden = true; // le pouce de ce rangement ne compte pas pour la suite
      el('bouton-apprendre').click();
      attendre(el('choix-commande').open && question() === 'Reprendre « ouvre la boîte fictive » ?', `pas « Reprendre ? » : ${question()}`);
      // 09/11/2026 (décision de Max après c72) : + « Écrire ». Avant : attendreEgal(cases(), ['Oui', 'Redire'], 'cases');
      attendreEgal(cases(), ['Oui', 'Redire', 'Écrire'], 'cases');
      // 09/11/2026 (bloc c74) : « le troisième » = la 3e case (« Écrire »), puis « Annuler » ramène à « Reprendre ? ».
      dicter('le troisième');
      attendre(!el('saisie-apprendre').hidden && el('saisie-apprendre').value === 'ouvre la boîte fictive', '« le troisième » n’a pas choisi « Écrire »');
      el('aucun-choix-commande').click();
      el('bouton-apprendre').click();
      attendreEgal(question(), 'Reprendre « ouvre la boîte fictive » ?', 'question après Annuler');
      // Redire (le mot de la case, à la voix) : la phrase redite.
      prochaine('redire');
      el('petit-micro').click(); // « redire » à la voix choisit la case
      attendreEgal(question(), 'Redis la phrase…', 'pendant l’écoute');
      prochaine('montre les options fictives');
      ecouter(); // l'écoute de la machine (après 0,4 s)
      attendreEgal(question(), 'J’ai compris : « montre les options fictives »', 'confirmation 1');
      attendreEgal(cases(), ['Oui', 'Redire', 'Écrire'], 'cases de la confirmation 1');
      toucher('Oui');
      attendre(/« montre les options fictives » : quelle commande \?/.test(question()), `quiz : ${question()}`);
      const cs = cases();
      attendre(cs.includes('Ouvrir Autre') && cs.includes('Ouvrir Réglages') && cs[cs.length - 2] === 'Autres commandes' && cs[cs.length - 1] === 'Aucune ne convient', `cases du quiz : ${JSON.stringify(cs)}`);
      attendreEgal(signe(), '', 'un signe pendant le quiz');
      toucher('Autres commandes');
      attendre(cases().includes('Navigation') && cases().includes('Retour'), 'familles');
      toucher('Navigation');
      toucher('Ouvrir Réglages');
      attendreEgal(question(), '« montre les options fictives » → Ouvrir Réglages : c’est bien ça ?', 'confirmation 2');
      attendreEgal(cases(), ['Oui', 'Changer'], 'cases de la confirmation 2');
      attendreEgal(dicter('numéro un'), el('statut').textContent, '');
      attendre(!el('choix-commande').open, 'fenêtre pas fermée après le rangement');
      attendreEgal(liste().map(e => [e.phrase, e.code, e.origine]), [['montre les options fictives', 'NAV-03', 'bouton']], 'liste');
      attendre(!el('compte-apprendre').hidden && el('compte-apprendre').textContent === '1', 'nombre pas monté');
      attendreEgal(signe(), 'pouce', 'pas de pouce');
      // Doublon (même phrase, même commande) : dit, pas ajouté.
      el('bouton-apprendre').click();
      toucher('Redire'); prochaine('montre les options fictives'); ecouter();
      toucher('Oui'); toucher('Autres commandes'); toucher('Navigation'); toucher('Ouvrir Réglages'); toucher('Oui');
      attendre(/déjà dans la liste/.test(el('bulle-micro').textContent) && liste().length === 1, 'doublon pas dit, ou ajouté');
      // Même phrase, autre commande : laquelle garder ? → la nouvelle.
      el('bouton-apprendre').click();
      toucher('Redire'); prochaine('montre les options fictives'); ecouter();
      toucher('Oui'); toucher('Autres commandes'); toucher('Navigation'); toucher('Ouvrir Autre'); toucher('Oui');
      attendreEgal(question(), 'Déjà notée avec « Ouvrir Réglages ». Laquelle garder ?', 'question du conflit');
      toucher('Ouvrir Autre');
      attendreEgal(liste().map(e => e.code), ['NAV-02'], 'nouvelle pas gardée');
      void ui;
    });
  });

  await testAsync('Phrases à apprendre (09/11/2026, décisions de Max après c72, FICTIF) : « Reprendre ? » → « Écrire » : champ DÉJÀ REMPLI avec la phrase refusée, une seule confirmation ; Réglages > « Modifier » : la phrase garde ses mots, reçoit la nouvelle commande ; dans le tampon du petit tableur : l’ancienne « remplacée le … », la nouvelle ajoutée ; rien effacé', async c => {
    // 09/11/2026 (séance 2) : les changements vont dans le tampon de « Commandes vocales (Cap) » (avant : cap_phrases_tampon_v1, ses champs « ligne » et « etat »).
    const avantTampon = localStorage.getItem('cap_tableur_cap_tampon_v1');
    localStorage.removeItem('cap_tableur_cap_tampon_v1');
    try {
      await interfaceApprendre(c, async ({ ui, el, dicter, cases, toucher, question, liste }) => {
        dicter('ouvre la boîte fictive');
        el('bouton-apprendre').click();
        attendreEgal(question(), 'Reprendre « ouvre la boîte fictive » ?', 'question');
        toucher('Écrire');
        attendre(!el('saisie-apprendre').hidden && el('saisie-apprendre').value === 'ouvre la boîte fictive', `champ pas rempli : « ${el('saisie-apprendre').value} »`);
        el('saisie-apprendre').value = 'ouvre la boite fictive corrigée';
        toucher('Valider');
        attendreEgal(question(), 'J’ai compris : « ouvre la boite fictive corrigée »', 'confirmation');
        toucher('Oui');
        toucher('Autres commandes'); toucher('Navigation');
        toucher('Ouvrir Réglages');
        toucher('Oui');
        attendreEgal(liste().map(e => [e.phrase, e.code]), [['ouvre la boite fictive corrigée', 'NAV-03']], 'rangée');
        const ancienId = liste()[0].id;
        // Réglages > « Modifier ».
        el('ouvrir-autre').click(); el('ouvrir-reglages-cap').click();
        transitionEcrans.terminer(ui.doc);
        el('ouvrir-phrases-apprendre').click();
        const modifier = el('liste-phrases-apprendre').querySelector('.modifier-phrase-apprendre');
        attendre(modifier && modifier.textContent === 'Modifier' && modifier.nextElementSibling.textContent === 'Retirer', '« Modifier » pas à côté de « Retirer »');
        modifier.click();
        attendreEgal(question(), '« ouvre la boite fictive corrigée » : quelle commande ?', 'question de Modifier');
        toucher('Autres commandes'); toucher('Navigation');
        toucher('Ouvrir Autre');
        toucher('Oui');
        attendre(!el('choix-commande').open, 'fenêtre pas fermée');
        attendreEgal(liste().map(e => [e.phrase, e.code, e.origine]), [['ouvre la boite fictive corrigée', 'NAV-02', 'bouton']], 'pas modifiée');
        const tampon = JSON.parse(localStorage.getItem('cap_tableur_cap_tampon_v1'));
        const fin = tampon.slice(-2);
        attendre(fin[0].type === 'etat' && fin[0].id === ancienId && /^remplacée le /.test(fin[0].texte) && fin[1].type === 'ajout' && fin[1].code === 'NAV-02' && fin[1].phrase === 'ouvre la boite fictive corrigée', `tampon : ${JSON.stringify(fin)}`);
        attendre(/Phrases à apprendre \(1\)/.test(el('ouvrir-phrases-apprendre').textContent), 'nombre changé');
      });
    } finally { if (avantTampon === null) localStorage.removeItem('cap_tableur_cap_tampon_v1'); else localStorage.setItem('cap_tableur_cap_tampon_v1', avantTampon); }
  });

  await testAsync('Phrases à apprendre (09/11/2026, FICTIF) : rien entendu → « Redire » / « Écrire » (corriger au clavier) ; « Aucune ne convient » gardée sans commande ; « Annuler » ne garde rien ; le choix fait dans la fenêtre d’HÉSITATION va dans la MÊME liste', async c => {
    await interfaceApprendre(c, async ({ el, dicter, prochaine, cases, toucher, question, liste, ecouter }) => {
      prochaine('');
      el('bouton-apprendre').click();
      attendreEgal(question(), 'Redis la phrase…', 'écoute');
      ecouter();
      attendreEgal(question(), 'Je n’ai rien entendu.', 'rien entendu');
      toucher('Écrire');
      attendre(!el('saisie-apprendre').hidden, 'pas de champ pour écrire');
      el('saisie-apprendre').value = 'range le grenier fictif';
      toucher('Valider');
      attendreEgal(question(), 'J’ai compris : « range le grenier fictif »', 'phrase écrite');
      attendre(el('saisie-apprendre').hidden, 'champ resté');
      toucher('Oui');
      toucher('Aucune ne convient');
      attendreEgal(question(), '« range le grenier fictif » → aucune commande : c’est bien ça ?', 'confirmation sans commande');
      toucher('Oui');
      attendreEgal(liste().map(e => [e.phrase, e.code]), [['range le grenier fictif', '']], 'gardée sans commande');
      // Annuler (pendant l'écoute) : rien de gardé, l'écoute prévue ne démarre pas.
      prochaine('lave la vaisselle fictive');
      el('bouton-apprendre').click();
      attendreEgal(el('aucun-choix-commande').textContent, 'Annuler', 'bouton du bas pendant la machine');
      el('aucun-choix-commande').click();
      attendre(![...c.delais.values()].some(y => y.delai === 400), 'écoute encore prévue après « Annuler »');
      attendre(!el('choix-commande').open && liste().length === 1, '« Annuler » a gardé quelque chose');
      attendreEgal(el('aucun-choix-commande').textContent, 'Aucun de ces choix', 'libellé pas remis');
      // Fenêtre d'hésitation : le choix va dans la même liste (origine « hésitation »).
      dicter('ouvre les options fictives');
      attendre(el('choix-commande').open && question() === '', 'fenêtre d’hésitation (sans question)');
      dicter('deux');
      attendreEgal(liste().map(e => [e.phrase, e.code, e.origine]), [['ouvre les options fictives', 'NAV-03', 'hésitation'], ['range le grenier fictif', '', 'bouton']], 'choix d’hésitation pas rangé');
      attendreEgal(el('compte-apprendre').textContent, '2', 'nombre');
      void cases;
    });
  });

  await testAsync('L’ORDRE GAGNE (09/11/2026, décision de Max, bloc c75, faux tableur FICTIF) : fenêtre de gros choix : une case commence par un nombre (« Deux … ») : « deux » dit seul choisit la 2e CASE ; le titre dit EN ENTIER choisit la case « Deux … »', async c => {
    await interfaceApprendre(c, async ({ el, dicter, cases, toucher, question }) => {
      const lignes = commandesVocales.analyser([...TABLEUR_FICTIF_CHOIX, ['Deux écrans FICTIFS', '', 'Mot-clé', 'les écrans fictifs', 'NAV-05', '']]).lignes;
      localStorage.setItem(commandesVocales.CLE_COPIE, JSON.stringify({ lu_le: new Date(0).toISOString(), compte: {}, lignes }));
      dicter('montre les écrans fictifs');
      el('bouton-apprendre').click();
      attendreEgal(question(), 'Reprendre « montre les écrans fictifs » ?', 'question');
      toucher('Oui');
      const liste = cases();
      const i = liste.indexOf('Deux écrans FICTIFS');
      attendre(i >= 0 && i !== 1 && liste.length >= 3, `case « Deux … » absente ou déjà 2e : ${JSON.stringify(liste)}`);
      dicter('deux');
      attendreEgal(question(), `« montre les écrans fictifs » → ${liste[1]} : c’est bien ça ?`, '« deux » n’a pas pris la 2e case');
      dicter('changer');
      attendreEgal(cases(), liste, 'pas revenu aux commandes');
      dicter('deux écrans fictifs');
      attendreEgal(question(), '« montre les écrans fictifs » → Deux écrans FICTIFS : c’est bien ça ?', 'titre dit en entier pas choisi');
    });
  });

  await testAsync('Phrases à apprendre (09/11/2026, FICTIF) : Réglages > « Phrases à apprendre (N) » : la liste (phrase → commande, date, origine), « Retirer » par ligne, « Copier tout » (presse-papiers, rien d’envoyé)', async c => {
    const avant = localStorage.getItem('cap_phrases_a_apprendre_v1');
    try {
      localStorage.removeItem('cap_phrases_a_apprendre_v1');
      phrasesApprendre.ajouter(localStorage, { phrase: 'ouvre la boîte fictive', code: 'NAV-03', commande: 'Ouvrir Réglages', origine: 'bouton' });
      phrasesApprendre.ajouter(localStorage, { phrase: 'range le grenier fictif', code: '', origine: 'hesitation' });
      const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
      brancherAccueil(c, ui);
      const el = id => ui.parId(id);
      let copie = null;
      c.navigator.clipboard = { writeText: async texte => { copie = texte; } }; // faux presse-papiers (le navigateur du banc de test)
      el('ouvrir-autre').click(); el('ouvrir-reglages-cap').click();
      transitionEcrans.terminer(ui.doc);
      attendreEgal(el('ouvrir-phrases-apprendre').textContent, 'Phrases à apprendre (2)', 'bouton de Réglages');
      el('ouvrir-phrases-apprendre').click();
      const lignes = () => [...el('liste-phrases-apprendre').querySelectorAll('.texte-phrase-apprendre')].map(x => x.textContent);
      attendre(lignes().length === 2 && /« range le grenier fictif » → aucune commande · \d\d\/\d\d\/\d{4} · hésitation/.test(lignes()[0]) && /« ouvre la boîte fictive » → Ouvrir Réglages/.test(lignes()[1]), `lignes : ${JSON.stringify(lignes())}`);
      el('copier-phrases-apprendre').click();
      await attendreQue(() => copie !== null || /Copié|pas marché/.test(el('etat-copie-apprendre').textContent), 'rien copié');
      attendre(copie !== null, `rien copié : ${el('etat-copie-apprendre').textContent}`);
      attendre(copie.split('\n').length === 2 && copie.includes('ouvre la boîte fictive\tNAV-03'), `copie : ${copie}`);
      attendre(/Copié/.test(el('etat-copie-apprendre').textContent), 'copie pas dite');
      el('liste-phrases-apprendre').querySelector('.retirer-phrase-apprendre').click();
      attendre(lignes().length === 1 && el('ouvrir-phrases-apprendre').textContent === 'Phrases à apprendre (1)' && el('compte-apprendre').textContent === '1', 'retirer');
    } finally { if (avant === null) localStorage.removeItem('cap_phrases_a_apprendre_v1'); else localStorage.setItem('cap_phrases_a_apprendre_v1', avant); }
  });

  // ----- 09/11/2026 : PETIT TABLEUR « Phrases apprises » (accord de Max, 3 étapes), FAUX Google, données FICTIVES -----
  // Faux Google : un Drive et des tableurs en mémoire. Toute suppression, tout effacement, tout accès au tableur principal
  // fait échouer le test. « panne » : la prochaine requête échoue (pas de réseau) ; « perdue » : Google écrit, mais la
  // réponse se perd en route.
  function fauxGooglePetitTableur() {
    const g = { fichiers: new Map(), appels: [], panne: 0, perdue: false, numero: 0 };
    const reponse = corps => ({ ok: true, status: 200, json: async () => corps });
    g.appeler = async (url, options = {}) => {
      const methode = (options.method || 'GET').toUpperCase();
      const u = new URL(url);
      g.appels.push([methode, u.href]);
      if (methode === 'DELETE' || /:clear|batchClear|deleteDimension|deleteSheet|\/trash|"trashed":true/i.test(u.href + (options.body || ''))) throw new Error(`SUPPRESSION INTERDITE : ${methode} ${u.href}`);
      if (/FICTIF_PRINCIPAL/.test(u.href)) throw new Error('le tableur principal a été touché');
      if (g.panne > 0) { g.panne--; throw new Error('Pas de réseau (FICTIF)'); }
      const corps = options.body ? JSON.parse(options.body) : null;
      const chemin = decodeURIComponent(u.pathname);
      let m;
      if (u.hostname === 'www.googleapis.com' && (m = chemin.match(/^\/drive\/v3\/files\/([^/]+)$/))) {
        const f = g.fichiers.get(m[1]);
        if (!f) { const e = new Error('404'); e.statut = 404; throw e; }
        if (methode === 'PATCH') { f.appProperties = { ...f.appProperties, ...corps.appProperties }; return reponse({ id: f.id }); }
        return reponse({ id: f.id, trashed: Boolean(f.trashed) });
      }
      if (u.hostname === 'www.googleapis.com' && chemin === '/drive/v3/files') {
        const q = u.searchParams.get('q');
        const k = q.match(/key='([^']+)' and value='([^']+)'/);
        return reponse({ files: [...g.fichiers.values()].filter(f => !f.trashed && k && f.appProperties[k[1]] === k[2]).map(f => ({ id: f.id })) });
      }
      if (u.hostname === 'sheets.googleapis.com' && chemin === '/v4/spreadsheets' && methode === 'POST') {
        const id = `FICTIF_petit_tableur_${++g.numero}_abcdef`;
        g.fichiers.set(id, { id, nom: corps.properties.title, onglet: corps.sheets[0].properties.title, parents: corps.parents || null, appProperties: {}, lignes: [] });
        return reponse({ spreadsheetId: id });
      }
      if (u.hostname === 'sheets.googleapis.com' && (m = chemin.match(/^\/v4\/spreadsheets\/([^/]+)\/values\/'Phrases'!(.+?)(:append)?$/))) {
        const f = g.fichiers.get(m[1]);
        if (!f) { const e = new Error('404'); e.statut = 404; throw e; }
        const plageCellules = m[2];
        if (m[3]) { f.lignes.push(...corps.values.map(l => l.slice())); if (g.perdue) { g.perdue = false; throw new Error('Réponse perdue (FICTIF)'); } return reponse({}); }
        if (methode === 'PUT') {
          const c = plageCellules.match(/^([A-G])(\d+)/);
          const col = c[1].charCodeAt(0) - 65; const rang = Number(c[2]) - 1;
          corps.values.forEach((l, i) => { while (f.lignes.length <= rang + i) f.lignes.push([]); l.forEach((v, j) => { f.lignes[rang + i][col + j] = v; }); });
          return reponse({});
        }
        if (plageCellules === 'G:G') return reponse({ values: f.lignes.map(l => [l[6] || '']) });
        if (plageCellules === 'A2:G') return reponse({ values: f.lignes.slice(1) });
      }
      throw new Error(`requête inattendue : ${methode} ${u.href}`);
    };
    return g;
  }
  const fauxStockagePT = () => { const m = new Map(); return { getItem: k => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)), removeItem: k => m.delete(k) }; };

  await testAsync('Petit tableur (09/11/2026, FAUX Google, FICTIF) : étape 1 : hors connexion et sans réseau les phrases ATTENDENT dans le tampon (rien perdu) ; puis Cap CRÉE « Phrases apprises » (racine du Drive, marque invisible, titres), écrit les lignes, vide le tampon ; « Retirer » MARQUE « retirée le … » sans rien effacer ; commande changée : « remplacée le … » ; jamais de doublon ; renommé ou nouvel appareil : retrouvé par sa MARQUE, jamais un 2e tableur', async () => {
    const g = fauxGooglePetitTableur();
    const s = fauxStockagePT();
    let connecte = false;
    const tp = tableurPhrases.creer({ appeler: g.appeler, stockage: s, connecte: () => connecte, maintenant: () => Date.UTC(2030, 0, 10, 10) });
    const p1 = { id: 'P-fictif-1', phrase: 'fais voir la boîte fictive', code: 'NAV-03', commande: 'Ouvrir Réglages', origine: 'bouton', quand: '2030-01-10T10:00:00.000Z' };
    const p2 = { id: 'P-fictif-2', phrase: 'range le grenier fictif', code: '', commande: 'Aucune ne convient', origine: 'hésitation', quand: '2030-01-10T10:00:00.000Z' };
    tp.noterAjout(p1); tp.noterAjout(p2, { etat: '' });
    // Pas connecté : rien n'est demandé à Google, tout attend.
    attendreEgal((await tp.envoyer()).attente, 2, 'hors connexion');
    attendreEgal(g.appels.length, 0, 'Google appelé sans connexion');
    // Connecté mais pas de réseau : rien de perdu.
    connecte = true; g.panne = 1;
    const r1 = await tp.envoyer();
    attendre(r1.attente === 2 && r1.erreur, `panne : ${JSON.stringify(r1)}`);
    attendreEgal(tp.enAttente(), 2, 'tampon vidé malgré la panne');
    // Le réseau revient : création, marque, titres, deux lignes.
    const r2 = await tp.envoyer();
    attendre(r2.attente === 0 && r2.envoyees === 2, `envoi : ${JSON.stringify(r2)}`);
    attendreEgal(g.fichiers.size, 1, 'nombre de tableurs');
    const f = [...g.fichiers.values()][0];
    attendre(f.nom === 'Phrases apprises' && f.onglet === 'Phrases' && f.parents === null, `tableur : ${JSON.stringify([f.nom, f.onglet, f.parents])}`);
    attendreEgal(f.appProperties, { cap_role: 'phrases_apprises' }, 'marque invisible');
    attendreEgal(f.lignes[0], ['Phrase', 'Code', 'Commande', 'Date', 'Origine', 'État', 'Identifiant'], 'titres');
    attendreEgal(f.lignes.slice(1).map(l => [l[0], l[1], l[2], l[3], l[4], l[6]]), [['fais voir la boîte fictive', 'NAV-03', 'Ouvrir Réglages', '10/01/2030', 'bouton', 'P-fictif-1'], ['range le grenier fictif', '', 'Aucune ne convient', '10/01/2030', 'hésitation', 'P-fictif-2']], 'lignes');
    attendreEgal(tp.adresse(), `https://docs.google.com/spreadsheets/d/${f.id}/edit`, 'adresse pour « Ouvrir le tableur »');
    // « Retirer » : la ligne reste, marquée.
    tp.noterRetrait('P-fictif-2');
    await tp.envoyer();
    attendreEgal(f.lignes.length, 3, 'une ligne effacée ou ajoutée');
    attendreEgal(f.lignes[2][5], 'retirée le 10/01/2030', 'pas marquée retirée');
    attendreEgal(f.lignes[2][0], 'range le grenier fictif', 'phrase retirée effacée');
    // Commande changée : l'ancienne « remplacée », la nouvelle ajoutée.
    tp.noterRemplacement('P-fictif-1');
    tp.noterAjout({ ...p1, id: 'P-fictif-3', code: 'NAV-02', commande: 'Ouvrir Autre' });
    await tp.envoyer();
    attendre(f.lignes.length === 4 && f.lignes[1][5] === 'remplacée le 10/01/2030' && f.lignes[3][1] === 'NAV-02', `remplacement : ${JSON.stringify(f.lignes)}`);
    // Réponse perdue : Google a écrit, Cap ne le sait pas : la fois suivante, pas de doublon.
    tp.noterAjout({ ...p1, id: 'P-fictif-4', phrase: 'montre le coffre fictif' });
    g.perdue = true;
    attendreEgal((await tp.envoyer()).attente, 1, 'réponse perdue : doit rester en attente');
    await tp.envoyer();
    attendreEgal(f.lignes.filter(l => l[6] === 'P-fictif-4').length, 1, 'doublon après réponse perdue');
    attendreEgal(tp.enAttente(), 0, 'tampon pas vide');
    // Max renomme le tableur, puis un NOUVEL appareil (rien en mémoire) : retrouvé par la marque, pas recréé.
    f.nom = 'Mes phrases FICTIVES renommées';
    const s2 = fauxStockagePT();
    const tp2 = tableurPhrases.creer({ appeler: g.appeler, stockage: s2, connecte: () => true });
    attendreEgal((await tp2.trouverOuCreer()).id, f.id, 'pas retrouvé par la marque');
    attendreEgal(g.fichiers.size, 1, 'un 2e tableur créé');
    // Étape 2 : lecture du petit tableur, copie sur le téléphone.
    const lu = await tp2.lireEtGarder();
    attendre(lu.lu && lu.nombre === 4, `lecture : ${JSON.stringify(lu)}`);
    attendreEgal(tp2.copie().map(l => [l.code, l.etat]), [['NAV-03', 'remplacée le 10/01/2030'], ['', 'retirée le 10/01/2030'], ['NAV-02', ''], ['NAV-03', '']], 'copie');
    attendre(!g.appels.some(([m]) => m === 'DELETE'), 'DELETE envoyé');
  });

  test('Petit tableur (09/11/2026) : son fichier n’efface rien, ne touche pas au tableur principal, n’appelle ni l’IA ni fetch directement (tout passe par la connexion Google)', () => {
    const src = SOURCE_TABLEUR_PHRASES_TEST;
    for (const mot of ['DELETE', ':clear', 'batchClear', 'deleteDimension', 'trash(', '"trashed":true', 'commandesVocales', 'googlePicker', 'NOM_TABLEUR', 'fetch(', 'XMLHttpRequest', 'cerveau', 'anthropic', 'claude', 'primary', 'innerHTML'])
      attendre(!src.includes(mot), `tableur_phrases.js contient « ${mot} »`);
    attendre(src.includes("appProperties has { key='${MARQUE.cle}' and value='${MARQUE.valeur}' }"), 'recherche par la marque absente');
  });

  test('Petit tableur (09/11/2026, faux tableur avec RETIRER) : étape 2 : les phrases apprises (téléphone ET copie du petit tableur) sont reconnues DITES EN ENTIER, même sans réseau ; « Aucune ne convient », « retirée », « remplacée », retrait en attente et code inconnu : ignorés ; LE PRINCIPAL GAGNE', () => {
    const s = fauxStockagePT();
    s.setItem(commandesVocales.CLE_COPIE, JSON.stringify({ lignes: commandesVocales.analyser(TABLEUR_FICTIF_CHOIX).lignes }));
    const principal = commandesVocales.copie(s).lignes;
    attendreEgal(commandesVocales.reconnaitre('fais voir la boîte fictive', principal).statut, 'rien', 'phrase déjà connue du faux tableur');
    s.setItem('cap_phrases_a_apprendre_v1', JSON.stringify([
      { id: 'P-a', phrase: 'fais voir la boîte fictive', code: 'NAV-03', commande: 'Ouvrir Réglages', origine: 'bouton', quand: '2030-01-10T10:00:00Z' },
      { id: 'P-b', phrase: 'range le grenier fictif', code: '', commande: 'Aucune ne convient', origine: 'bouton', quand: '2030-01-10T10:00:00Z' },
      { id: 'P-c', phrase: 'ouvre autre', code: 'NAV-03', commande: 'Ouvrir Réglages', origine: 'bouton', quand: '2030-01-10T10:00:00Z' },
      { id: 'P-d', phrase: 'lance la fusée fictive', code: 'XYZ-99', commande: 'Inconnue FICTIVE', origine: 'bouton', quand: '2030-01-10T10:00:00Z' },
      { id: 'P-e', phrase: 'montre le placard fictif', code: 'NAV-02', commande: 'Ouvrir Autre', origine: 'bouton', quand: '2030-01-10T10:00:00Z' }]));
    s.setItem('cap_phrases_apprises_copie_v1', JSON.stringify({ lignes: [
      { phrase: 'affiche le tiroir fictif', code: 'NAV-02', commande: 'Ouvrir Autre', etat: '', id: 'P-f' },
      { phrase: 'sors le carton fictif', code: 'NAV-02', commande: 'Ouvrir Autre', etat: 'retirée le 10/01/2030', id: 'P-g' },
      { phrase: 'déballe le sac fictif', code: 'NAV-02', commande: 'Ouvrir Autre', etat: 'remplacée le 10/01/2030', id: 'P-h' }] }));
    s.setItem('cap_phrases_tampon_v1', JSON.stringify([{ type: 'etat', id: 'P-e', etat: 'retirée le 10/01/2030' }]));
    const lignes = commandesVocales.lignesMicro(s);
    attendre(commandesVocales.lignesMicro(s) === lignes, 'copie fusionnée recalculée sans changement');
    const r = phrase => commandesVocales.reconnaitre(phrase, lignes);
    attendre(r('fais voir la boîte fictive').statut === 'reconnu' && r('fais voir la boîte fictive').code === 'NAV-03', `phrase du téléphone : ${JSON.stringify(r('fais voir la boîte fictive'))}`);
    attendre(r('Fais voir la boîte fictive !').code === 'NAV-03', 'majuscules et ponctuation');
    attendre(r('affiche le tiroir fictif').code === 'NAV-02', 'phrase de la copie du petit tableur (sans réseau)');
    attendre(r('fais voir la boîte fictive et le grenier fictif').code !== 'NAV-03', 'reconnue sans être dite en entier');
    attendreEgal(r('range le grenier fictif').statut, 'rien', '« Aucune ne convient » reconnue');
    attendreEgal(r('sors le carton fictif').statut, 'rien', 'ligne « retirée » reconnue');
    attendreEgal(r('déballe le sac fictif').statut, 'rien', 'ligne « remplacée » reconnue');
    attendreEgal(r('montre le placard fictif').statut, 'rien', 'retrait en attente reconnu');
    attendreEgal(r('lance la fusée fictive').statut, 'rien', 'code inconnu du principal reconnu');
    attendreEgal(commandesVocales.reconnaitre('ouvre autre', principal).code, 'NAV-02', 'phrase pas nette dans le principal');
    attendreEgal(r('ouvre autre').code, 'NAV-02', 'le principal ne gagne pas');
    // Le principal HÉSITE (fenêtre de gros choix) : le choix appris de Max tranche.
    attendreEgal(commandesVocales.reconnaitre('les options fictives', principal).statut, 'ambigu', 'le faux tableur n’hésite plus');
    const s2 = fauxStockagePT();
    s2.setItem(commandesVocales.CLE_COPIE, s.getItem(commandesVocales.CLE_COPIE));
    s2.setItem('cap_phrases_a_apprendre_v1', JSON.stringify([{ id: 'P-i', phrase: 'les options fictives', code: 'NAV-03', commande: 'Ouvrir Réglages', origine: 'hésitation', quand: '2030-01-10T10:00:00Z' }]));
    attendreEgal(commandesVocales.reconnaitre('les options fictives', commandesVocales.lignesMicro(s2)).code, 'NAV-03', 'le choix de l’hésitation ne tranche pas');
    attendre(commandesVocales.dejaDansPrincipal('ouvre autre', principal) && !commandesVocales.dejaDansPrincipal('les options fictives', principal) && !commandesVocales.dejaDansPrincipal('fais voir la boîte fictive', principal), 'dejaDansPrincipal');
  });

  await testAsync('Petit tableur (09/11/2026, FICTIF) : étape 3 : Réglages : « Ouvrir le tableur » (seulement quand Cap le connaît : lien hors de Cap) et le nombre de changements qui attendent ; « Retirer » met « retirée le … » en attente (rien effacé dans le tableur)', async c => {
    // 09/11/2026 (séance 2) : les changements vont dans le tampon de « Commandes vocales (Cap) » (avant : cap_phrases_tampon_v1, ses champs « ligne » et « etat »).
    const cles = ['cap_phrases_a_apprendre_v1', 'cap_tableur_cap_tampon_v1', 'cap_phrases_tableur_id_v1', 'cap_phrases_tableur_reprise_v1', 'cap_tableur_cap_reprise_v1'];
    const avant = cles.map(k => localStorage.getItem(k));
    try {
      for (const k of cles) localStorage.removeItem(k);
      localStorage.setItem('cap_phrases_tableur_reprise_v1', 'FICTIF');
      const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
      brancherAccueil(c, ui);
      const el = id => ui.parId(id);
      el('ouvrir-autre').click(); el('ouvrir-reglages-cap').click();
      transitionEcrans.terminer(ui.doc);
      el('ouvrir-phrases-apprendre').click();
      attendre(el('ouvrir-tableur-phrases').hidden, '« Ouvrir le tableur » montré sans tableur connu');
      attendreEgal(el('tampon-phrases-apprendre').textContent, 'Toutes les phrases sont écrites dans le tableur « Commandes vocales (Cap) ».', 'tampon vide');
      // Une phrase rangée et une retirée : deux changements attendent (pas de connexion Google dans le banc de test).
      phrasesApprendre.ajouter(localStorage, { phrase: 'ouvre la boîte fictive', code: 'NAV-03', commande: 'Ouvrir Réglages', origine: 'bouton' });
      tableurCap.noterAjout(phrasesApprendre.lire(localStorage)[0]);
      localStorage.setItem('cap_phrases_tableur_id_v1', 'FICTIF_petit_tableur_0123456789');
      el('ouvrir-phrases-apprendre').click(); el('ouvrir-phrases-apprendre').click(); // refermer, rouvrir : relu
      await attendreMs(50);
      const lien = el('ouvrir-tableur-phrases');
      attendre(!lien.hidden && lien.href === 'https://docs.google.com/spreadsheets/d/FICTIF_petit_tableur_0123456789/edit' && lien.target === '_blank' && /noopener/.test(lien.rel), `lien : ${lien.hidden} ${lien.href}`);
      lien.scrollIntoView({ block: 'center' });
      attendre(touchable(ui, lien), '« Ouvrir le tableur » pas touchable');
      el('liste-phrases-apprendre').querySelector('.retirer-phrase-apprendre').click();
      await attendreMs(50);
      const tampon = JSON.parse(localStorage.getItem('cap_tableur_cap_tampon_v1'));
      attendre(tampon.length === 2 && tampon[1].type === 'etat' && /^retirée le \d\d\/\d\d\/\d{4}$/.test(tampon[1].texte) && tampon[1].id === tampon[0].id, `tampon : ${JSON.stringify(tampon)}`);
      attendreEgal(el('tampon-phrases-apprendre').textContent, '2 changements attendent d’être écrits dans le tableur (réseau ou connexion Google).', 'nombre en attente');
    } finally { cles.forEach((k, i) => { if (avant[i] === null) localStorage.removeItem(k); else localStorage.setItem(k, avant[i]); }); }
  });

  // ----- 09/11/2026 (décision de Max, séance 2) : les DEUX tableurs, FAUX Google, données FICTIVES -----
  function fauxGoogleTableurCap() {
    const TITRES = ['Ce que je veux', 'Commande', 'Bloc', 'Formulation', 'Code commande', 'Remarque (FICTIVE, datée)'];
    const ID = 'FICTIF_tableur_cap_seance2_abcdef';
    const MODELE = 'FICTIF_PRINCIPAL_modele_0123456789';
    const g = { lignes: [TITRES.slice()], appels: [], panne: 0, perdue: false, TITRES, ID };
    const csv = lignes => lignes.map(l => l.map(x => (/[",\n]/.test(String(x)) ? `"${String(x).replace(/"/g, '""')}"` : String(x))).join(',')).join('\n');
    const reponse = corps => ({ ok: true, status: 200, json: async () => corps, text: async () => corps });
    const pannes = () => { if (g.panne > 0) { g.panne--; throw new Error('Pas de réseau (FICTIF)'); } };
    g.lire = async url => {
      const u = new URL(url); g.appels.push(['GET', u.href]); pannes();
      const chemin = decodeURIComponent(u.pathname);
      if (chemin === '/drive/v3/files') return reponse({ files: /commandes_vocales_cap/.test(u.searchParams.get('q')) ? [{ id: ID }] : [{ id: MODELE }] });
      if (chemin === `/drive/v3/files/${ID}`) return reponse({ id: ID, trashed: false });
      if (chemin === `/drive/v3/files/${ID}/export`) return reponse(csv(g.lignes));
      throw new Error(`lecture inattendue ${u.href}`);
    };
    g.ecrire = async (url, options) => {
      const u = new URL(url); g.appels.push([options.method, u.href]);
      if (u.href.includes(MODELE)) throw new Error('le tableur modèle a été écrit');
      if (/DELETE/.test(options.method) || /:clear|batchClear|batchUpdate/.test(u.href)) throw new Error('SUPPRESSION INTERDITE');
      pannes();
      const corps = JSON.parse(options.body); const chemin = decodeURIComponent(u.pathname);
      let m;
      if (chemin === `/drive/v3/files/${ID}`) return reponse({});
      if ((m = chemin.match(/\/values\/'Commandes'!A:F:append$/))) { g.lignes.push(...corps.values.map(l => l.slice())); if (g.perdue) { g.perdue = false; throw new Error('Réponse perdue (FICTIF)'); } return reponse({}); }
      if ((m = chemin.match(/\/values\/'Commandes'!F(\d+)$/)) && options.method === 'PUT') { g.lignes[Number(m[1]) - 1][5] = corps.values[0][0]; return reponse({}); }
      throw new Error(`écriture inattendue ${options.method} ${u.href}`);
    };
    return g;
  }

  await testAsync('Tableur de Cap, séance 2 (09/11/2026, FAUX Google FICTIF) : les phrases vont dans « Commandes vocales (Cap) » aux colonnes du modèle (Expression seule (Cap), remarque datée + [identifiant]) ; sans connexion ou sans réseau : elles ATTENDENT ; « retirée », « remplacée », « choisie par Max » s’AJOUTENT à la remarque (rien d’effacé) ; reprise de « Phrases apprises » marquée « reprise le … » ; jamais de doublon ; copie pour reconnaître sans réseau', async () => {
    const g = fauxGoogleTableurCap();
    const m = new Map(); const s = { getItem: k => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)), removeItem: k => m.delete(k) };
    s.setItem(tableurCap.CLE_ID, g.ID); s.setItem('cap_tableur_cap_marque_v1', g.ID);
    let connecte = false;
    const tc = tableurCap.creer({ lire: g.lire, ecrire: g.ecrire, stockage: s, connecte: () => connecte, lireCsv: commandesVocales.lireCsv, maintenant: () => Date.UTC(2030, 0, 10, 10) });
    const p1 = { id: 'P-fictif-a', phrase: 'fais voir la boîte fictive', code: 'NAV-03', commande: 'Ouvrir Réglages', origine: 'bouton', quand: '2030-01-10T10:00:00.000Z' };
    const p2 = { id: 'P-fictif-b', phrase: 'range le grenier fictif', code: '', commande: 'Aucune ne convient', origine: 'hésitation', quand: '2030-01-10T10:00:00.000Z' };
    tc.noterAjout(p1); tc.noterAjout(p2);
    tc.noterReprise({ id: 'P-fictif-r', phrase: 'montre le coffre fictif', code: 'NAV-02', commande: 'Ouvrir Autre', etat: 'remplacée le 01/01/2030' });
    attendreEgal((await tc.envoyer()).attente, 3, 'hors connexion');
    attendreEgal(g.appels.length, 0, 'Google appelé sans connexion');
    connecte = true; g.panne = 1;
    attendreEgal((await tc.envoyer()).attente, 3, 'pas de réseau : perdu');
    const r = await tc.envoyer();
    attendre(r.attente === 0 && r.envoyees === 3, `envoi : ${JSON.stringify(r)}`);
    attendreEgal(g.lignes.length, 4, 'lignes');
    attendreEgal(g.lignes[1], ['Ouvrir Réglages', 'Ouvrir Réglages', 'Expression seule (Cap)', 'fais voir la boîte fictive', 'NAV-03', 'Ajoutée par Cap le 10/01/2030 (bouton) [P-fictif-a]'], 'ligne 1');
    attendreEgal(g.lignes[2].slice(0, 5), ['À traiter à la main', 'Aucune ne convient', 'Expression seule (Cap)', 'range le grenier fictif', ''], 'ligne 2 (aucune ne convient)');
    attendreEgal(g.lignes[3][5], 'Reprise le 10/01/2030 de « Phrases apprises » ; état d’origine : remplacée le 01/01/2030 [P-fictif-r]', 'reprise');
    // Marques ajoutées, jamais effacées.
    tc.noterRetrait('P-fictif-b'); tc.noterChoix('P-fictif-a'); tc.noterRemplacement('P-fictif-a');
    await tc.envoyer();
    attendreEgal(g.lignes.length, 4, 'une ligne effacée ou ajoutée');
    attendreEgal(g.lignes[1][5], 'Ajoutée par Cap le 10/01/2030 (bouton) [P-fictif-a] ; choisie par Max le 10/01/2030 ; remplacée le 10/01/2030', 'marques');
    attendre(/\[P-fictif-b\] ; retirée le 10\/01\/2030$/.test(g.lignes[2][5]), `retrait : ${g.lignes[2][5]}`);
    attendreEgal(g.lignes[2][3], 'range le grenier fictif', 'phrase retirée effacée');
    // Un état avant l'ajout de sa ligne (ordre du tampon) : l'état passe après l'ajout.
    tc.noterChoix('P-fictif-c');
    tc.noterAjout({ ...p1, id: 'P-fictif-c', phrase: 'affiche le tiroir fictif' });
    await tc.envoyer();
    attendre(/\[P-fictif-c\] ; choisie par Max le /.test(g.lignes[4][5]), `état avant l’ajout perdu : ${g.lignes[4][5]}`);
    // Réponse perdue : pas de doublon.
    tc.noterAjout({ ...p1, id: 'P-fictif-d', phrase: 'sors le carton fictif' });
    g.perdue = true;
    attendreEgal((await tc.envoyer()).attente, 1, 'réponse perdue : doit rester en attente');
    await tc.envoyer();
    attendreEgal(g.lignes.filter(l => /\[P-fictif-d\]/.test(l[5])).length, 1, 'doublon');
    // Copie pour reconnaître sans réseau.
    const lu = await tc.lireEtGarder();
    attendre(lu.lu && lu.nombre === 5, `lecture : ${JSON.stringify(lu)}`);
    attendreEgal(tc.copie().map(l => [l.id, l.code, l.ecartee, l.choisie]), [['P-fictif-a', 'NAV-03', true, true], ['P-fictif-b', '', true, false], ['P-fictif-r', 'NAV-02', true, false], ['P-fictif-c', 'NAV-03', false, true], ['P-fictif-d', 'NAV-03', false, false]], 'copie');
    attendre(!g.appels.some(([meth]) => meth === 'DELETE'), 'DELETE envoyé');
  });

  test('Les deux tableurs (09/11/2026, séance 2, faux tableur avec RETIRER) : phrase apprise DITE EN ENTIER ; même commande, ou principal muet, ou principal qui hésite avec elle : faite directement ; commandes différentes : fenêtre de choix (deux cases), sauf si Max l’a déjà « choisie » ; « Aucune ne convient », « retirée », « remplacée » et retraits en attente : écartés', () => {
    const lignes = commandesVocales.analyser(TABLEUR_FICTIF_CHOIX).lignes;
    const faits = [];
    for (const code of ['NAV-02', 'NAV-03', 'NAV-09']) commandesVocales.brancherAction(code, r => { faits.push(r.code); return `Fait FICTIF ${r.code}.`; });
    try {
      const decide = (phrase, apprises) => commandesVocales.deciderMicro(phrase, { lignes, apprises: apprises.map(a => ({ cle: commandesVocales.trouverApprise ? phrasesApprendre.plier(a.phrase) : '', ...a })) });
      attendreEgal(commandesVocales.reconnaitre('ouvre autre', lignes).code, 'NAV-02', 'le faux tableur a changé');
      // Principal muet : la phrase apprise est faite.
      attendreEgal(decide('fais voir la boîte fictive', [{ phrase: 'fais voir la boîte fictive', code: 'NAV-03' }]).code, 'NAV-03', 'principal muet');
      // Même commande : directement.
      attendreEgal(decide('ouvre autre', [{ phrase: 'ouvre autre', code: 'NAV-02' }]).statut, 'fait', 'même commande');
      // Commandes différentes : fenêtre de choix, deux cases.
      const d = decide('ouvre autre', [{ phrase: 'ouvre autre', code: 'NAV-03', commande: 'Ouvrir Réglages' }]);
      attendre(d.statut === 'ambigu' && d.deuxTableurs && JSON.stringify(d.codes) === '["NAV-02","NAV-03"]' && d.options.length === 2, `pas de fenêtre : ${JSON.stringify(d)}`);
      // Déjà choisie par Max : directement.
      attendreEgal(decide('ouvre autre', [{ phrase: 'ouvre autre', code: 'NAV-03', choisie: true }]).code, 'NAV-03', 'choix retenu ignoré');
      // Le principal hésite : la commande apprise en fait partie : directement ; sinon : fenêtre avec toutes.
      attendreEgal(commandesVocales.reconnaitre('les options fictives', lignes).statut, 'ambigu', 'le faux tableur n’hésite plus');
      attendreEgal(decide('les options fictives', [{ phrase: 'les options fictives', code: 'NAV-03' }]).code, 'NAV-03', 'hésitation + phrase apprise');
      const d3 = decide('les options fictives', [{ phrase: 'les options fictives', code: 'NAV-09' }]);
      attendre(d3.statut === 'ambigu' && d3.codes.length === 3 && d3.codes.includes('NAV-09'), `hésitation + autre commande : ${JSON.stringify(d3.codes)}`);
      // Pas dite en entier : la phrase apprise ne compte pas.
      attendreEgal(decide('ouvre autre et le reste fictif', [{ phrase: 'ouvre autre', code: 'NAV-03' }]).code, 'NAV-02', 'comptée sans être dite en entier');
      // Les sources et ce qui est écarté.
      const m = new Map(); const s = { getItem: k => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)) };
      s.setItem('cap_phrases_a_apprendre_v1', JSON.stringify([{ id: 'P-t1', phrase: 'ouvre la porte fictive', code: 'NAV-03' }, { id: 'P-t2', phrase: 'range le grenier fictif', code: '' }]));
      s.setItem('cap_tableur_cap_copie_v1', JSON.stringify({ lignes: [{ id: 'P-c1', phrase: 'affiche le tiroir fictif', code: 'NAV-02', ecartee: false, choisie: false },
        { id: 'P-c2', phrase: 'sors le carton fictif', code: 'NAV-02', ecartee: true }, { id: 'P-c3', phrase: 'déballe le sac fictif', code: 'NAV-02', ecartee: false }] }));
      s.setItem('cap_phrases_apprises_copie_v1', JSON.stringify({ lignes: [{ id: 'P-o1', phrase: 'vide le panier fictif', code: 'NAV-02', etat: 'remplacée le 01/01/2030' }, { id: 'P-o2', phrase: 'lave la tasse fictive', code: 'NAV-02', etat: '' }] }));
      s.setItem('cap_tableur_cap_tampon_v1', JSON.stringify([{ type: 'etat', id: 'P-c3', texte: 'retirée le 10/01/2030' }, { type: 'etat', id: 'P-c1', texte: 'choisie par Max le 10/01/2030' }]));
      const liste = commandesVocales.apprisesDeuxTableurs(s);
      attendreEgal(liste.map(a => [a.phrase, a.code, a.choisie]), [['ouvre la porte fictive', 'NAV-03', false], ['affiche le tiroir fictif', 'NAV-02', true], ['lave la tasse fictive', 'NAV-02', false]], 'phrases gardées');
    } finally { for (const code of ['NAV-02', 'NAV-03', 'NAV-09']) commandesVocales.brancherAction(code, undefined); }
  });

  await testAsync('Les deux tableurs (09/11/2026, séance 2, faux tableur FICTIF) : la phrase est dans les deux avec des commandes différentes : FENÊTRE de choix (deux cases + « Aucun de ces choix ») ; « la deuxième » la fait et le choix est RETENU (« choisie par Max », daté) : la fois suivante, directement ; choisir l’autre : l’ancienne « remplacée », la nouvelle ajoutée', async c => {
    await interfaceChoix(c, async ({ el, dicter, lignesChoix }) => {
      const liste = () => JSON.parse(localStorage.getItem('cap_phrases_a_apprendre_v1') || '[]');
      const tampon = () => JSON.parse(localStorage.getItem('cap_tableur_cap_tampon_v1') || '[]');
      localStorage.setItem('cap_phrases_a_apprendre_v1', JSON.stringify([{ id: 'P-deux', phrase: 'ouvre autre', code: 'NAV-03', commande: 'Ouvrir Réglages', origine: 'bouton', quand: '2030-01-10T10:00:00Z' }]));
      dicter('ouvre autre');
      attendre(el('choix-commande').open, 'pas de fenêtre de choix');
      attendreEgal(lignesChoix(), [['1', 'Ouvrir Autre'], ['2', 'Ouvrir Réglages']], 'cases');
      attendreEgal(el('aucun-choix-commande').textContent, 'Aucun de ces choix', 'case « Aucun »');
      attendreEgal(dicter('la deuxième'), 'J’ouvre Réglages.', 'choix');
      attendre(liste()[0].choisie === true, 'pas retenu sur le téléphone');
      attendre(tampon().some(o => o.type === 'etat' && o.id === 'P-deux' && /^choisie par Max le \d\d\/\d\d\/\d{4}$/.test(o.texte)), `pas retenu dans le tableur : ${JSON.stringify(tampon())}`);
      attendreEgal(dicter('ouvre autre'), 'J’ouvre Réglages.', 'redemandé alors que retenu');
      attendre(!el('choix-commande').open, 'fenêtre rouverte');
      // Une autre phrase, choix de la PREMIÈRE case (celle du tableur de Max) : l'apprise est remplacée.
      localStorage.setItem('cap_phrases_a_apprendre_v1', JSON.stringify([{ id: 'P-trois', phrase: 'ouvre autre', code: 'NAV-03', commande: 'Ouvrir Réglages', origine: 'bouton', quand: '2030-01-10T10:00:00Z' }]));
      localStorage.removeItem('cap_tableur_cap_tampon_v1');
      dicter('ouvre autre');
      attendreEgal(dicter('le premier'), 'J’ouvre Autre.', 'premier choix');
      const l = liste();
      attendre(l.length === 1 && l[0].code === 'NAV-02' && l[0].choisie && l[0].id !== 'P-trois', `liste : ${JSON.stringify(l)}`);
      attendre(tampon().some(o => o.type === 'etat' && o.id === 'P-trois' && /^remplacée le /.test(o.texte)) && tampon().some(o => o.type === 'ajout' && o.code === 'NAV-02' && /choisie par Max le /.test(o.remarque)), `tampon : ${JSON.stringify(tampon())}`);
      // « Aucun de ces choix » : rien de retenu.
      localStorage.setItem('cap_phrases_a_apprendre_v1', JSON.stringify([{ id: 'P-quatre', phrase: 'ouvre autre', code: 'NAV-03', commande: 'Ouvrir Réglages', origine: 'bouton', quand: '2030-01-10T10:00:00Z' }]));
      localStorage.removeItem('cap_tableur_cap_tampon_v1');
      dicter('ouvre autre');
      dicter('aucun');
      attendre(!liste()[0].choisie && !tampon().length, '« Aucun » a retenu quelque chose');
    }, { garderApprises: true });
  });

  await testAsync('Reprise de « Phrases apprises » (09/11/2026, séance 2, FICTIF) : une seule fois, quand le tableur de Cap est prêt : chaque ligne du petit tableur (même identifiant, « reprise le … », état d’origine gardé) + les phrases du téléphone qui n’y étaient pas ; le petit tableur n’est ni écrit ni créé', async c => {
    const cles = ['cap_phrases_a_apprendre_v1', 'cap_tableur_cap_tampon_v1', 'cap_tableur_cap_reprise_v1', 'cap_phrases_apprises_copie_v1', 'cap_phrases_tableur_id_v1', 'cap_phrases_tampon_v1'];
    const avant = cles.map(k => localStorage.getItem(k));
    const avantFonctions = { t: tableurCap.trouverOuCreer, e: tableurCap.envoyer, l: tableurPhrases.lireSansToucher, n: tableurPhrases.noterAjout };
    const touchesPetit = [];
    try {
      for (const k of cles) localStorage.removeItem(k);
      localStorage.setItem('cap_phrases_a_apprendre_v1', JSON.stringify([{ id: 'P-tel', phrase: 'ouvre la porte fictive', code: 'NAV-03', commande: 'Ouvrir Réglages', origine: 'bouton', quand: '2030-01-10T10:00:00Z' },
        { id: 'P-p1', phrase: 'affiche le tiroir fictif', code: 'NAV-02', commande: 'Ouvrir Autre', origine: 'bouton', quand: '2030-01-09T10:00:00Z' }]));
      localStorage.setItem('cap_phrases_apprises_copie_v1', JSON.stringify({ lignes: [{ id: 'P-p1', phrase: 'affiche le tiroir fictif', code: 'NAV-02', commande: 'Ouvrir Autre', etat: '' },
        { id: 'P-p2', phrase: 'vide le panier fictif', code: 'NAV-02', commande: 'Ouvrir Autre', etat: 'remplacée le 01/01/2030' }] }));
      tableurCap.trouverOuCreer = async () => ({ id: 'FICTIF_tableur_cap_0123456789', cree: false });
      tableurCap.envoyer = async () => ({ envoyees: 0, attente: 1, raison: 'pas_connecte' });
      tableurPhrases.lireSansToucher = async () => ({ lu: false });
      tableurPhrases.noterAjout = (...x) => { touchesPetit.push(x); return 0; };
      preparerInterface(c, { largeur: 412, hauteur: 900 });
      await attendreQue(() => localStorage.getItem('cap_tableur_cap_reprise_v1'), 'reprise pas faite');
      const t = JSON.parse(localStorage.getItem('cap_tableur_cap_tampon_v1'));
      attendreEgal(t.map(o => [o.type, o.id]), [['ajout', 'P-p1'], ['ajout', 'P-p2'], ['ajout', 'P-tel']], 'tampon de reprise');
      attendre(/^Reprise le \d\d\/\d\d\/\d{4} de « Phrases apprises »$/.test(t[0].remarque) && /état d’origine : remplacée le 01\/01\/2030$/.test(t[1].remarque) && /^Ajoutée par Cap le /.test(t[2].remarque), `remarques : ${JSON.stringify(t.map(o => o.remarque))}`);
      attendreEgal(touchesPetit.length, 0, 'le petit tableur a reçu une phrase');
      attendreEgal(localStorage.getItem('cap_phrases_tampon_v1'), null, 'le petit tableur a reçu un changement');
      // Une seule fois.
      preparerInterface(c, { largeur: 412, hauteur: 900 });
      await attendreMs(100);
      attendreEgal(JSON.parse(localStorage.getItem('cap_tableur_cap_tampon_v1')).length, 3, 'reprise refaite');
    } finally {
      tableurCap.trouverOuCreer = avantFonctions.t; tableurCap.envoyer = avantFonctions.e; tableurPhrases.lireSansToucher = avantFonctions.l; tableurPhrases.noterAjout = avantFonctions.n;
      cles.forEach((k, i) => { if (avant[i] === null) localStorage.removeItem(k); else localStorage.setItem(k, avant[i]); });
    }
  });

  await testAsync('Bouton « phrase à apprendre » (09/11/2026) : à GAUCHE du petit micro, même ligne, sur tous les écrans et dans chaque fenêtre (il suit le micro), touchable ; il ne cache ni le micro, ni la note, ni un bouton ; sous l’alerte Google', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    brancherAccueil(c, ui);
    const el = id => ui.parId(id);
    const b = el('bouton-apprendre');
    const verifier = (ou, zone) => {
      const rb = b.getBoundingClientRect();
      const rm = el('petit-micro').getBoundingClientRect();
      attendre(touchable(ui, b), `bouton pas touchable (${ou})`);
      attendre(rb.right <= rm.left - 4 && Math.abs((rb.top + rb.bottom) / 2 - (rm.top + rm.bottom) / 2) < 2, `pas à gauche du micro sur la même ligne (${ou}) : ${JSON.stringify([rb, rm])}`);
      const autres = [...zone.querySelectorAll('button, input, select, textarea, a[href]')]
        .filter(x => !['bouton-apprendre', 'petit-micro', 'indicateur-musique'].includes(x.id) && x.getClientRects().length && !x.closest('[hidden]'))
        .filter(x => { const r = x.getBoundingClientRect(); return r.width > 0 && r.height > 0 && seTouchent(r, rb); });
      attendreEgal(autres.map(x => x.id || x.className), [], `un bouton sous le bouton « apprendre » (${ou})`);
    };
    for (const [nom, ouvrir] of [['accueil', () => {}], ['Autre', () => el('ouvrir-autre').click()], ['Réglages', () => el('ouvrir-reglages-cap').click()], ['Chercher', () => el('ouvrir-chercher').click()], ['tâches', () => el('chercher-todo').click()]]) {
      ouvrir(); transitionEcrans.terminer(ui.doc); await pause();
      verifier(nom, ui.doc.body);
    }
    el('fermer-chercher').click(); transitionEcrans.terminer(ui.doc);
    for (const id of [...ui.doc.querySelectorAll('dialog')].map(d => d.id).filter(Boolean)) {
      const d = el(id); d.showModal(); await pause();
      attendre(d.contains(b), `bouton pas posé dans « ${id} »`);
      verifier(id, d);
      d.close(); await pause();
    }
    // La note de musique à gauche du bouton, sans se toucher.
    el('indicateur-musique').hidden = false;
    attendre(!seTouchent(el('indicateur-musique').getBoundingClientRect(), b.getBoundingClientRect()) && el('indicateur-musique').getBoundingClientRect().right <= b.getBoundingClientRect().left, 'la note touche le bouton');
    el('indicateur-musique').hidden = true;
    // Sous l'alerte Google.
    el('texte-alerte-google').textContent = 'Connexion à Google à refaire (FICTIF).';
    el('alerte-google').hidden = false;
    await pause();
    attendre(b.getBoundingClientRect().top >= el('alerte-google').getBoundingClientRect().bottom && touchable(ui, b), 'bouton pas sous l’alerte');
    el('alerte-google').hidden = true;
  });

  test('Search Console : les deux balises de vérification de Google sont dans la page (l’ancienne gardée), chacune une seule fois', () => {
    const modele = new DOMParser().parseFromString(SOURCE_HTML, 'text/html');
    const balises = modele.head.querySelectorAll('meta[name="google-site-verification"]');
    attendreEgal([...balises].map(b => b.getAttribute('content')), ['AzyYjPSR5WClNkEoHd0ifUIHLoeJ7rCRnEpyGaejhlA', 'FiiCjzO--6k0nz9-Xh2ZRQdaG0qqb0xvZoieMuwydt0'], 'balises');
  });

  test('Panneau rouge (lot 1) : aucun champ « mot de passe » ni « adresse mail », pas de « Se connecter à Google », clés masquées', () => {
    const modele = new DOMParser().parseFromString(SOURCE_HTML, 'text/html');
    attendreEgal(modele.querySelectorAll('input[type="password"], input[type="email"]').length, 0, 'champ de connexion');
    attendre(!/Se connecter à Google/.test(SOURCE_HTML), 'ancien bouton');
    attendreEgal(modele.getElementById('connexion-google').textContent, 'Autoriser Cap (agenda et Drive)', 'bouton renommé');
    for (const id of ['cle-picker', 'cle-ia']) attendre(modele.getElementById(id).classList.contains('champ-masque'), `${id} pas masqué`);
    attendre(/\.champ-masque \{ -webkit-text-security: disc;/.test(SOURCE_STYLE), 'masquage absent');
    attendreEgal(modele.getElementById('adresse-compte-relations').getAttribute('inputmode'), 'email', 'clavier');
  });

  await testAsync('Rond d’attente : remis même si la lecture échoue', async () => {
    const bouton = document.createElement('button');
    bouton.textContent = 'Compter FICTIF';
    await attendreRejet(() => attenteLecture.pendant(bouton, async () => { throw new Error('panne FICTIVE'); }), 'panne FICTIVE');
    attendreEgal([bouton.textContent, bouton.disabled, bouton.hasAttribute('aria-busy')], ['Compter FICTIF', false, false], 'bouton pas remis');
  });

  test('Sélecteur : le rôle « relations » rattache le choix à Cap (numéro du projet) ; les autres dossiers gardent leur réglage', () => {
    attendre(/if \(role === 'relations'\) constructeur = constructeur\.setAppId\(numeroProjet\(\)\);/.test(SOURCE_GOOGLE_PICKER), 'numéro du projet pour « relations »');
    attendreEgal((SOURCE_GOOGLE_PICKER.match(/setAppId\(/g) || []).length, 2, 'setAppId ailleurs');
    attendre(/relations: 'cap_dossier_relations_v1'/.test(SOURCE_GOOGLE_PICKER), 'rôle « relations »');
  });

  await testAsync('Relations (FAUX Drive) : si Google ne fait pas un Google Doc du « Journal de bord », Cap s’arrête (rien d’autre créé, rien supprimé)', async c => {
    const drive = fauxDriveRelations(c);
    const repondre = c.repondre;
    c.repondre = async r => {
      const reponse = await repondre(r);
      if (r.url.pathname.startsWith('/upload/')) return reponseGoogle({ id: 'fictif-texte', mimeType: 'text/plain' });
      return reponse;
    };
    const { module } = creationIsolee(c, '2026-11-06T21:50:00Z');
    await attendreRejet(async () => module.lancer(await module.preparer(dictionnaireCreationFictif(), 'appcap-fictif'), { appCap: 'appcap-fictif' }), 'pas été converti');
    attendreEgal(drive.fichiers.map(x => x.name), ['Relations', 'r_Jean Fictif', 'Journal de bord'], 'création après l’arrêt');
    attendre(c.requetes.every(r => ['GET', 'POST'].includes(r.methode)), 'méthode non permise');
  });

  // Étape 4 : essai sur UNE personne (toujours sur le FAUX Drive dans les tests).
  function dictionnaireEssaiFictif() {
    return [['Prénom', 'Nom', 'Type', 'Note pour IA'],
      ['Jean', 'Fictif', 'Personne', 'note FICTIVE jamais lue'],
      ['Jean-Baptiste-FICTIF (Jibé)', 'Essai-FICTIF', 'Personne', ''],
      ['Paul', 'Modèle-FICTIF', 'Personne', ''], ['paul', 'modele-fictif', 'Personne', ''],
      ['Séverine-FICTIF', '', 'Personne', '']];
  }

  await testAsync('Relations (étape 4, FAUX Drive) : essai sur UNE personne choisie : écran (ce qui sera créé, question), puis « Oui, crée ce dossier » = 5 éléments au plus, un seul dossier de personne', async c => {
    const ui = preparerInterface(c);
    const drive = fauxDriveRelations(c);
    const { module, lignes } = creationIsolee(c);
    const el = id => ui.parId(id);
    let lectures = 0;
    module.brancherEssai(ui.doc, { lire: async () => { lectures++; return dictionnaireEssaiFictif(); }, appCap: async () => ({ id: 'appcap-fictif' }) });
    el('essai-relations').click();
    await attendreQue(() => el('choix-essai-relations').children.length > 0, `choix absents : ${el('resume-essai-relations').textContent}`);
    // Les homonymes et la fiche incomplète ne sont pas proposés ; le prénom avec parenthèse donne le diminutif.
    attendreEgal([...el('choix-essai-relations').children].map(b => b.textContent), ['r_Jean Fictif', 'r_Jibé Essai-FICTIF'], 'personnes proposées');
    attendreEgal(drive.creations, 0, 'création avant le choix');
    [...el('choix-essai-relations').children][1].click();
    attendre(el('verification-relations').open, 'écran de vérification fermé');
    attendreEgal(el('relations-nombre').textContent, 'Ce qui sera créé (un seul dossier d’essai) :', 'titre');
    attendreEgal([...el('relations-liste').children].map(li => li.textContent),
      ['App Cap › Relations › r_Jibé Essai-FICTIF', 'r_Jibé Essai-FICTIF › Journal de bord', 'r_Jibé Essai-FICTIF › Reçus', 'r_Jibé Essai-FICTIF › Envoyés'], 'ce qui sera créé');
    attendre(!el('relations-question').hidden && el('relations-confirmer').hidden, 'question absente ou bouton visible trop tôt');
    attendreEgal(el('relations-question-texte').textContent, 'As-tu déjà créé toi-même un dossier r_ pour l’une de ces personnes ?', 'question');
    el('relations-non-jamais').click();
    attendreEgal(el('relations-creer').textContent, 'Oui, crée ce dossier', 'bouton');
    attendreEgal(drive.creations, 0, 'création avant « Oui, crée ce dossier »');
    // Le travail est lancé par le clic ; on attend sa fin en regardant l'état affiché.
    el('relations-creer').click();
    el('relations-creer').click();
    await attendreQue(() => /Terminé/.test(el('relations-etat').textContent), `état : ${el('relations-etat').textContent}`);
    attendreEgal(drive.noms(), ['Envoyés', 'Journal de bord', 'Relations', 'Reçus', 'r_Jibé Essai-FICTIF'], 'éléments créés');
    attendreEgal(drive.creations, 5, 'plus de 5 éléments');
    attendreEgal(lignes.length, 5, 'lignes du Journal Général');
    attendreEgal(lectures, 1, 'Dictionnaire relu');
    // Second essai sur une AUTRE personne : refusé, rien créé (jamais plus d'un dossier de personne).
    el('essai-relations').click();
    await attendreQue(() => el('choix-essai-relations').children.length > 0, 'choix absents au second essai');
    [...el('choix-essai-relations').children].find(b => b.textContent === 'r_Jean Fictif').click();
    attendre(/existe déjà pour une autre personne/.test(el('resume-essai-relations').textContent), `second essai : ${el('resume-essai-relations').textContent}`);
    // Même personne une seconde fois : rien de recréé.
    [...el('choix-essai-relations').children].find(b => b.textContent === 'r_Jibé Essai-FICTIF').click();
    attendre(/existe déjà/.test(el('relations-nombre').textContent), 'dossier existant non signalé');
    el('relations-non-jamais').click();
    el('relations-creer').click();
    await attendreQue(() => /Terminé : 0 élément/.test(el('relations-etat').textContent), `état : ${el('relations-etat').textContent}`);
    attendreEgal(drive.creations, 5, 'doublon au second passage');
    el('relations-fermer').click();
    attendre(c.requetes.every(r => ['GET', 'POST'].includes(r.methode) && r.url.hostname === 'www.googleapis.com'), 'adresse ou méthode non permise');
  });

  await testAsync('Relations (étape 4, FAUX Drive) : plafond de l’essai, « Oui j’ai déjà créé » = rien, App Cap ou Dictionnaire absents = rien', async c => {
    const drive = fauxDriveRelations(c);
    const { module } = creationIsolee(c);
    const plan = await module.preparer(dictionnaireEssaiFictif(), 'appcap-fictif');
    // Un plan d'essai trafiqué avec deux personnes : refusé avant toute création.
    const triche = { ...module.planEssai(plan, 2), aFaire: plan.aFaire };
    await attendreRejet(() => module.lancer(triche, { appCap: 'appcap-fictif' }), 'une seule personne');
    attendreEgal(drive.creations, 0, 'création malgré deux personnes');
    await attendreRejet(async () => module.planEssai(plan, 4), 'ne peut pas servir');
    // Écran : « Oui » à la question = rien créé.
    const ui = preparerInterface(c);
    fauxDriveRelations(c);
    module.ecran(ui.doc, module.planEssai(plan, 2), { appCap: 'appcap-fictif' });
    ui.parId('relations-oui-deja').click();
    ui.parId('relations-creer').click();
    await new Promise(r => setTimeout(r, 50));
    attendre(c.requetes.every(r => r.methode === 'GET'), 'création malgré « Oui, j’ai déjà créé »');
    // App Cap pas choisi, Dictionnaire pas choisi : message, aucune requête.
    const avant = c.requetes.length;
    module.brancherEssai(ui.doc, { lire: async () => dictionnaireEssaiFictif(), appCap: async () => null });
    ui.parId('essai-relations').click();
    await attendreQue(() => /App Cap/.test(ui.parId('resume-essai-relations').textContent), 'message sans App Cap');
    attendreEgal(c.requetes.length, avant, 'requête sans App Cap');
  });

  // Étape 5 : toutes les personnes, en une fois, à la demande (FAUX Drive, faux Dictionnaire).
  function dictionnaireTousFictif() {
    return [['Prénom', 'Nom', 'Type', 'Note pour IA'],
      ['Jean-Baptiste-FICTIF (Jibé)', 'Essai-FICTIF', 'Personne', ''],
      ['Jean', 'Fictif', 'Personne', 'note FICTIVE jamais lue'],
      ['Jeanne', 'Exemple-FICTIF', 'Personne', ''],
      ['Paul', 'Modèle-FICTIF', 'Personne', ''], ['paul', 'modele-fictif', 'Personne', ''],
      ['Séverine-FICTIF', '', 'Personne', ''],
      ['Marc', 'Essai-FICTIF', '', ''],
      ['Cabinet FICTIF', '', 'Organisme', ''],
      ['Zoé-FICTIF (Zézé)', 'Lefèvre-FICTIF', 'Personne', '']];
  }

  await testAsync('Relations (étape 5, FAUX Drive) : toutes les personnes en une fois : liste, nombre, dossier d’essai écarté, mis de côté comptés, question, « Oui, crée ces N dossiers », premières entrées datées', async c => {
    const ui = preparerInterface(c);
    const drive = fauxDriveRelations(c);
    const { module, lignes } = creationIsolee(c, '2026-11-06T22:10:00Z');
    const el = id => ui.parId(id);
    // D'abord l'essai (étape 4) sur la première fiche, comme dans la réalité.
    const essai = await module.preparer(dictionnaireTousFictif(), 'appcap-fictif');
    await module.lancer(module.planEssai(essai, 2), { appCap: 'appcap-fictif' });
    attendreEgal(drive.creations, 5, 'essai');
    const journalEssai = drive.fichiers.find(x => x.name === 'Journal de bord');
    const texteEssai = journalEssai.contenu;
    module.brancherTous(ui.doc, { lire: async () => dictionnaireTousFictif(), appCap: async () => ({ id: 'appcap-fictif' }) });
    el('tous-relations').click();
    await attendreQue(() => el('verification-relations').open, `écran fermé : ${el('resume-tous-relations').textContent}`);
    attendreEgal(drive.creations, 5, 'création avant toute réponse');
    attendre(/^3 dossier\(s\) « r_ » à créer/.test(el('relations-nombre').textContent) && /1 déjà fait\(s\), écarté\(s\)/.test(el('relations-nombre').textContent), `nombre : ${el('relations-nombre').textContent}`);
    attendreEgal([...el('relations-liste').children].map(li => li.textContent), ['r_Jean Fictif', 'r_Jeanne Exemple-FICTIF', 'r_Zézé Lefèvre-FICTIF'], 'liste complète');
    // Mis de côté, avec leur nombre, en très gros ; deux choix.
    attendre(!el('relations-arret').hidden && el('relations-question').hidden, 'arrêt non montré');
    attendreEgal(el('relations-mis-de-cote').textContent, 'Mis de côté : 1 homonyme(s) (2 fiche(s)), 1 fiche(s) incomplète(s), 1 fiche(s) sans type, 0 changement(s) de nom possible(s).', 'mis de côté');
    attendre(parseFloat(ui.cadre.contentWindow.getComputedStyle(el('relations-mis-de-cote')).fontSize) >= 20, 'pas en très gros');
    el('relations-sans-probleme').click();
    attendreEgal(el('relations-question-texte').textContent, 'As-tu déjà créé toi-même un dossier r_ pour l’une de ces personnes ?', 'question');
    el('relations-non-jamais').click();
    attendreEgal(el('relations-creer').textContent, 'Oui, crée ces 3 dossiers', 'dernier bouton');
    attendreEgal(drive.creations, 5, 'création avant le dernier bouton');
    el('relations-creer').click();
    el('relations-creer').click();
    await attendreQue(() => /Terminé/.test(el('relations-etat').textContent), `état : ${el('relations-etat').textContent}`, 120);
    attendreEgal(drive.creations, 5 + 12, '4 éléments par personne, une seule fois');
    attendreEgal(drive.fichiers.filter(x => x.name.startsWith('r_')).map(x => x.name).sort(),
      ['r_Jean Fictif', 'r_Jeanne Exemple-FICTIF', 'r_Jibé Essai-FICTIF', 'r_Zézé Lefèvre-FICTIF'], 'dossiers de personnes');
    attendreEgal(drive.fichiers.filter(x => x.name === 'Relations').length, 1, 'un seul « Relations »');
    attendreEgal(journalEssai.contenu, texteEssai, 'Journal de bord de l’essai réécrit');
    const journauxNeufs = drive.fichiers.filter(x => x.name === 'Journal de bord' && x !== journalEssai);
    attendreEgal(journauxNeufs.map(x => x.contenu).sort(), ['06/11/2026, 23:10 : création du dossier Relations de Jean Fictif',
      '06/11/2026, 23:10 : création du dossier Relations de Jeanne Exemple-FICTIF', '06/11/2026, 23:10 : création du dossier Relations de Zézé Lefèvre-FICTIF'], 'premières entrées datées');
    attendreEgal(lignes.length, 17, 'une ligne de Journal Général par création');
    // Plus tard : nouvel appui, rien de nouveau dans le Dictionnaire → rien à créer.
    el('relations-fermer').click();
    el('tous-relations').click();
    await attendreQue(() => /^0 dossier/.test(el('relations-nombre').textContent), 'second passage');
    attendreEgal(drive.creations, 17, 'doublon au second passage');
    attendre(c.requetes.every(r => ['GET', 'POST'].includes(r.methode) && r.url.hostname === 'www.googleapis.com'), 'adresse ou méthode non permise');
  });

  await testAsync('Relations (étape 5, FAUX Drive) : coupure au milieu de toutes les personnes, puis reprise sans doublon ; « Oui, j’ai déjà créé » = rien', async c => {
    const drive = fauxDriveRelations(c, { coupureApres: 7 });
    const { module } = creationIsolee(c, '2026-11-06T22:10:00Z');
    const propre = dictionnaireTousFictif().filter((l, i) => i === 0 || [3, 4, 10].includes(i + 1));
    await attendreRejet(async () => module.lancer(await module.preparer(propre, 'appcap-fictif'), { appCap: 'appcap-fictif' }), 'coupure FICTIVE');
    attendreEgal(drive.creations, 7, 'avant la coupure');
    drive.coupureApres = Infinity;
    const reprise = await module.preparer(propre, 'appcap-fictif');
    attendreEgal([reprise.aFaire.length, reprise.deja.length], [1, 2], 'reprise : une personne à faire, deux déjà commencées');
    await module.lancer(reprise, { appCap: 'appcap-fictif' });
    attendreEgal(drive.noms(), ['Envoyés', 'Envoyés', 'Envoyés', 'Journal de bord', 'Journal de bord', 'Journal de bord', 'Relations', 'Reçus', 'Reçus', 'Reçus',
      'r_Jean Fictif', 'r_Jeanne Exemple-FICTIF', 'r_Zézé Lefèvre-FICTIF'], 'arborescence après reprise (sans doublon)');
    attendre(drive.fichiers.filter(x => x.name === 'Journal de bord').every(x => /^06\/11\/2026, 23:10 : création du dossier Relations de /.test(x.contenu)), 'première entrée manquante');
    // « Oui, j'ai déjà créé un dossier r_ » : rien n'est créé.
    const ui = preparerInterface(c);
    fauxDriveRelations(c);
    const depuis = c.requetes.length;
    module.ecran(ui.doc, await module.preparer(dictionnaireTousFictif(), 'appcap-fictif2'), { appCap: 'appcap-fictif2' });
    ui.parId('relations-sans-probleme').click();
    ui.parId('relations-oui-deja').click();
    ui.parId('relations-creer').click();
    await new Promise(r => setTimeout(r, 50));
    attendre(c.requetes.length > depuis && c.requetes.slice(depuis).every(r => r.methode === 'GET'), 'création malgré « Oui, j’ai déjà créé »');
  });

  test('Relations (étapes 3 et 4) : seul le bouton d’essai lance la création (jamais au démarrage ni dans les tests) ; le module ne supprime, ne renomme, ne déplace rien', () => {
    for (const nom of ['SOURCE_APP', 'SOURCE_RELATIONS']) {
      attendre(!/relationsCreation/.test({ SOURCE_APP, SOURCE_RELATIONS }[nom]), `${nom} appelle déjà la création`);
    }
    const apres = SOURCE_RELATIONS_CREATION.split('\n})();')[1] || '';
    attendreEgal((apres.match(/relationsCreation\.\w+/g) || []), ['relationsCreation.brancherEssai', 'relationsCreation.brancherTous', 'relationsCreation.brancherReparation', 'relationsCreation.brancherVisibilite'], 'point de départ autre que les quatre boutons');
    attendre(/!\(typeof window !== 'undefined' && window\.CAP_TESTS\)/.test(apres), 'le bouton d’essai serait branché dans les tests');
    attendre(!/lancer\(/.test(apres), 'création lancée au démarrage');
    attendreEgal((SOURCE_RELATIONS_CREATION.match(/'PATCH'/g) || []).length, 1, 'un seul remplacement de contenu (la réparation)');
    attendre(/\$\{envoi\}\/\$\{encodeURIComponent\(entree\.id\)\}\?uploadType=media/.test(SOURCE_RELATIONS_CREATION), 'remplacement par une autre adresse');
    for (const interdit of ["'DELETE'", "'PUT'", 'trashed: true', 'removeParents', 'addParents', 'innerHTML', 'localStorage', 'cerveau', 'docs.googleapis']) {
      attendre(!SOURCE_RELATIONS_CREATION.includes(interdit), `relations_creation.js contient « ${interdit} »`);
    }
  });

  // ---------- 06/11/2026 : écran d'ouverture « eau » (étape 1 de l'intégration du travail de Zencoder) ----------
  function horlogeEau() {
    const appels = [];
    let numero = 1;
    return { appels, raf: f => { appels.push(f); return numero++; }, caf: () => {} };
  }
  function pointeur(cible, type, x, y) {
    cible.dispatchEvent(new PointerEvent(type, { bubbles: true, pointerId: 7, clientX: x, clientY: y, isPrimary: true }));
  }
  function glisserSurEau(ui) {
    const r = ui.parId('ecran-eau').getBoundingClientRect();
    const surface = ui.parId('surface-eau');
    pointeur(surface, 'pointerdown', r.left + r.width / 2, r.top + r.height * 0.9);
    pointeur(surface, 'pointermove', r.left + r.width / 2, r.top + r.height * 0.5);
    pointeur(surface, 'pointerup', r.left + r.width / 2, r.top + r.height * 0.1);
  }
  // Une vidéo qui « marche » sans vrai fichier : l'erreur de chargement est arrêtée avant d'arriver à la vidéo.
  function videoQuiMarche(ui) {
    const video = ui.parId('video-galet');
    ui.parId('ecran-eau').addEventListener('error', e => e.stopPropagation(), true);
    video.play = () => Promise.resolve();
    video.pause = () => {};
    return video;
  }
  async function attendreQue(condition, message, essais = 60) {
    for (let i = 0; i < essais && !condition(); i++) await new Promise(r => setTimeout(r, 50));
    attendre(condition(), message);
  }

  // Attente en temps RÉEL (07/11/2026) : le lecteur de PDF (pdf.js) travaille à part, en temps réel, alors que
  // les attentes ci-dessus avancent en temps simulé ; une petite demande au serveur des tests suspend le
  // temps simulé pendant qu'elle se fait.
  async function attendreReel(condition, message, essais = 400) {
    for (let i = 0; i < essais && !condition(); i++) {
      try { await window.attenteReelle(i); } catch (erreur) { /* rien */ }
      await new Promise(r => setTimeout(r, 20));
    }
    attendre(condition(), message);
  }

  await testAsync('Écran d’eau : montré au démarrage, une seule fois par ouverture (pas après un rechargement), sans planter si le stockage refuse', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const h = horlogeEau();
    const memoire = new Map();
    const stockage = { getItem: k => memoire.get(k) ?? null, setItem: (k, v) => memoire.set(k, v) };
    let ecran = ecranEau.auDemarrage(ui.doc, { stockage, raf: h.raf, caf: h.caf, reglages: { fond: 'aucun', dureeSortieMs: 0 } });
    attendre(ecran.etat().visible && ecran.etat().animation, 'eau absente au démarrage');
    attendreEgal(memoire.get(ecranEau.CLE_VUE), 'oui', 'marque de la session');
    ecran.entrerDansCap();
    // Rechargement de la page pendant la même ouverture : pas d'eau.
    ui.parId('ecran-eau').hidden = true;
    ecran = ecranEau.auDemarrage(ui.doc, { stockage, raf: h.raf, caf: h.caf, reglages: { fond: 'aucun', dureeSortieMs: 0 } });
    attendre(!ecran.etat().visible, 'eau remontrée après un rechargement');
    // Stockage refusé (navigation privée) : l'eau s'affiche quand même, sans erreur.
    const refuse = { getItem: () => { throw new Error('refusé'); }, setItem: () => { throw new Error('refusé'); } };
    ecran = ecranEau.auDemarrage(ui.doc, { stockage: refuse, raf: h.raf, caf: h.caf, reglages: { fond: 'aucun', dureeSortieMs: 0 } });
    attendre(ecran.etat().visible, 'eau absente quand le stockage refuse');
  });

  await testAsync('Écran d’eau : REPLI, vidéo introuvable → l’eau seule et « Entrer dans Cap » tout de suite ; fonds « image » et « rien »', async c => {
    let ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    let h = horlogeEau();
    let ecran = ecranEau.monter(ui.parId('ecran-eau'), { raf: h.raf, caf: h.caf, reglages: { fond: 'video', dureeSortieMs: 0, video: 'eau/fichier-absent-FICTIF.mp4' } });
    ecran.afficher();
    await attendreQue(() => ecran.etat().panne, 'panne de la vidéo non détectée');
    attendre(ecran.etat().boutons && ui.parId('video-galet').hidden, 'pas de repli après la panne');
    glisserSurEau(ui);
    attendre(ecran.etat().boutons, 'boutons perdus après un glissement');
    glisserSurEau(ui);
    attendre(!ecran.etat().visible && !ecran.etat().animation, 'entrée dans Cap impossible après la panne');
    // Lecture refusée par le téléphone (play rejeté) : repli aussi.
    ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    h = horlogeEau();
    const video = videoQuiMarche(ui);
    ecran = ecranEau.monter(ui.parId('ecran-eau'), { raf: h.raf, caf: h.caf, reglages: { fond: 'video', dureeSortieMs: 0, video: 'eau/FICTIF.mp4' } });
    video.play = () => Promise.reject(new Error('lecture refusée FICTIVE'));
    ecran.afficher();
    attendre(!ecran.etat().boutons && !ui.parId('consigne-eau'), 'boutons avant la vidéo, ou texte de consigne encore là');
    ecran.demarrerVideo();
    await attendreQue(() => ecran.etat().panne && ecran.etat().boutons, 'pas de repli quand la lecture est refusée');
    // Fond « rien » : boutons tout de suite, pas de vidéo. Fond « image » : l'image est utilisée.
    ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    ecran = ecranEau.monter(ui.parId('ecran-eau'), { raf: h.raf, caf: h.caf, reglages: { fond: 'aucun', dureeSortieMs: 0 } });
    ecran.afficher();
    attendre(ecran.etat().boutons && ui.parId('video-galet').hidden && ui.parId('image-galet').hidden, 'fond « rien »');
    ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    ecran = ecranEau.monter(ui.parId('ecran-eau'), { raf: h.raf, caf: h.caf, reglages: { fond: 'image', dureeSortieMs: 0, image: 'eau/image-FICTIVE.png' } });
    ecran.afficher();
    attendre(!ui.parId('image-galet').hidden || ui.parId('image-galet').getAttribute('src') === 'eau/image-FICTIVE.png', 'fond « image » non utilisé');
    attendre(ecran.etat().boutons && ui.parId('video-galet').hidden, 'fond « image » : boutons absents');
  });

  await testAsync('Écran d’eau : glissement vers le haut = vidéo du galet, JAMAIS les tuiles ; puis « Entrer dans Cap » et les boutons de Cap répondent', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const h = horlogeEau();
    const video = videoQuiMarche(ui);
    const ecran = ecranEau.monter(ui.parId('ecran-eau'), { raf: h.raf, caf: h.caf, reglages: { fond: 'video', dureeSortieMs: 0, video: 'eau/FICTIF.mp4' } });
    ecran.afficher();
    // Pendant l'eau, c'est elle qui est touchée (Cap est dessous).
    const centre = el => { const r = el.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; };
    attendre(ui.parId('ecran-eau').contains(ui.doc.elementFromPoint(...centre(ui.parId('ouvrir-autre')))), 'Cap touchable sous l’eau');
    attendre(!ui.doc.querySelector('.ecran').contains(ui.parId('ecran-eau')), 'eau placée dans l’écran des tuiles');
    // Le glissement vers le haut sur l'eau lance la vidéo ; les tuiles restent fermées (doigt et souris).
    glisser(ui, ui.parId('surface-eau'), 200, 820, 200, 80);
    glisserSurEau(ui);
    attendreEgal(ecran.etat().video, 'lecture', 'vidéo non lancée');
    attendre(ui.parId('ecran-complet').hidden, 'les tuiles se sont ouvertes sous l’eau');
    video.dispatchEvent(new Event('ended'));
    attendre(ecran.etat().boutons, 'boutons absents à la fin de la vidéo');
    // « Revenir aux vagues » est touchable (rien ne le recouvre) ; un second glissement fait entrer.
    attendreEgal(ui.doc.elementFromPoint(...centre(ui.parId('bouton-revenir-vagues'))), ui.parId('bouton-revenir-vagues'), 'bouton « Revenir aux vagues » recouvert');
    glisserSurEau(ui);
    attendre(!ecran.etat().visible && !ecran.etat().animation, 'eau encore là, ou animation pas arrêtée');
    attendre(!ui.doc.documentElement.classList.contains('eau-ouverte'), 'défilement de Cap encore bloqué');
    // CONTRE LA PANNE DE TOUCHER : après l'entrée, les boutons de Cap reçoivent bien le toucher.
    // Étape A (07/11/2026) : les 3 boutons de l'accueil (sous l'eau, qui ne capte aucun toucher).
    for (const id of ['ouvrir-chercher', 'microphone', 'ouvrir-autre']) /* 09/11/2026 : nouvel ordre, gros micro */ { // 08/11/2026 (étape 2) : le micro de l'accueil est « ouvrir-micro » (avant : « microphone », déplacé dans l'écran Micro)
      const touche = ui.doc.elementFromPoint(...centre(ui.parId(id)));
      attendre(touche === ui.parId(id) || ui.parId(id).contains(touche), `bouton de Cap recouvert après l’entrée : ${id}`);
    }
    let ouvert = false;
    ui.parId('ouvrir-autre').addEventListener('click', () => { ouvert = true; }, { once: true });
    const [x, y] = centre(ui.parId('ouvrir-autre'));
    ui.doc.elementFromPoint(x, y).click();
    attendre(ouvert, 'le bouton de Cap ne répond pas après « Entrer dans Cap »');
    // Le glissement vers le haut de Cap ouvre toujours les tuiles (inchangé).
    glisser(ui, ui.doc.querySelector('.ecran'), 200, 700, 200, 300);
    attendre(!ui.parId('ecran-complet').hidden, 'glissement des tuiles cassé');
  });

  await testAsync('Écran d’eau (lot c20) : sans vidéo, le glissement fait monter Cap « de sous le sable » en environ 1 s, puis les boutons répondent ; fond pâle unique', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const h = horlogeEau();
    attendreEgal(ecranEau.REGLAGES.fond, 'aucun', 'fond par défaut (lot c20)');
    const ecran = ecranEau.monter(ui.parId('ecran-eau'), { raf: h.raf, caf: h.caf, animationsReduites: false, reglages: { dureeSortieMs: 150 } });
    ecran.afficher();
    attendre(ui.parId('bouton-revenir-vagues').hidden && !ui.parId('bouton-entrer-cap'), 'bouton « Entrer dans Cap » encore là, ou « Revenir aux vagues » sans vidéo');
    attendre(!ui.parId('consigne-eau'), 'texte de consigne encore là');
    glisserSurEau(ui);
    // Pendant l'entrée : l'eau bouge encore, ne retient aucun toucher, et Cap monte.
    attendre(ecran.etat().entree && ecran.etat().animation && ecran.etat().visible, 'entrée non commencée, ou eau arrêtée trop tôt');
    attendre(ui.doc.documentElement.classList.contains('cap-monte'), 'Cap ne monte pas');
    attendreEgal(ui.cadre.contentWindow.getComputedStyle(ui.parId('ecran-eau')).pointerEvents, 'none', 'l’eau retient les touchers pendant l’entrée');
    attendre(ui.parId('ecran-complet').hidden, 'le glissement a ouvert les tuiles');
    await attendreQue(() => !ecran.etat().visible, 'eau toujours là après l’entrée');
    attendre(!ecran.etat().animation && !ui.doc.documentElement.classList.contains('cap-monte'), 'animation pas finie');
    const centre = el => { const r = el.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; };
    const toucheAutre = ui.doc.elementFromPoint(...centre(ui.parId('ouvrir-autre')));
    attendre(toucheAutre === ui.parId('ouvrir-autre') || ui.parId('ouvrir-autre').contains(toucheAutre), 'bouton « Autre » recouvert après l’entrée');
    // Un second passage par l'eau : le glissement refait la même entrée.
    ecran.afficher();
    glisserSurEau(ui);
    attendre(ecran.etat().entree, 'second glissement sans entrée');
    await attendreQue(() => !ecran.etat().visible, 'seconde entrée non finie');
    // Animations réduites (réglage du téléphone) : entrée immédiate.
    const ecranReduit = ecranEau.monter(ui.parId('ecran-eau'), { raf: h.raf, caf: h.caf, animationsReduites: true });
    ecranReduit.afficher();
    ecranReduit.entrerDansCap();
    attendre(!ecranReduit.etat().visible, 'entrée pas immédiate avec les animations réduites');
    // Teinte de fond de Cap inchangée ; étape A : sur l'accueil, fond du thème (sombre par défaut, comme
    // Zencoder ; mode clair = l'ancien fond pâle).
    const fond = ui.cadre.contentWindow.getComputedStyle(ui.doc.documentElement).getPropertyValue('--fond').trim().toLowerCase();
    attendreEgal(fond, '#eaf1f4', 'teinte de fond');
    attendreEgal(ui.cadre.contentWindow.getComputedStyle(ui.doc.body).backgroundColor, 'rgb(10, 12, 12)', 'fond de l’accueil (sombre)');
    ui.doc.documentElement.classList.add('theme-cap-clair');
    attendreEgal(ui.cadre.contentWindow.getComputedStyle(ui.doc.body).backgroundColor, 'rgb(217, 228, 226)', 'fond de l’accueil (clair, #d9e4e2 depuis le 08/11/2026)');
    ui.doc.documentElement.classList.remove('theme-cap-clair');
  });

  await testAsync('Eau sur l’accueil (lot c20) : CHAQUE bouton visible de l’accueil répond (Scanner compris) et l’eau bouge au toucher ; arrêtée pendant l’ouverture et en arrière-plan', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const h = horlogeEau();
    const memoire = new Map([[ecranEau.CLE_VUE, 'oui']]);
    const stockage = { getItem: k => memoire.get(k) ?? null, setItem: (k, v) => memoire.set(k, v) };
    const ecran = ecranEau.auDemarrage(ui.doc, { stockage, raf: h.raf, caf: h.caf, reglages: { fond: 'aucun', dureeSortieMs: 0 } });
    attendre(!ecran.etat().visible && ecran.fond.etat().active, 'eau de l’accueil absente');
    const fenetre = ui.cadre.contentWindow;
    attendreEgal(fenetre.getComputedStyle(ui.parId('eau-accueil')).pointerEvents, 'none', 'l’eau de l’accueil capte les touchers');
    // Lot c22 : EXACTEMENT la même eau qu'à l'ouverture (tous les réglages, pas seulement l'opacité).
    const ouverture = ecranEau.monter(ui.parId('ecran-eau'), { raf: h.raf, caf: h.caf, reglages: { fond: 'aucun', dureeSortieMs: 0 } });
    attendreEgal(ecran.fond.etat().reglagesEau, ouverture.etat().reglagesEau, 'eau de l’accueil différente de l’ouverture');
    attendreEgal(ecran.fond.etat().reglagesEau.cellules, ecranEau.EAU.cellules, 'finesse réduite sur l’accueil');
    // Lisibilité (option A) : contraste calculé dans le PIRE cas, l'eau la plus foncée sous la carte.
    const rgb = t => (t.match(/[0-9.]+/g) || []).map(Number);
    const lum = c => { const v = c.slice(0, 3).map(x => x / 255).map(x => (x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4)); return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]; };
    const contraste = (a, b) => { const [l1, l2] = [lum(a), lum(b)].sort((x, y) => y - x); return (l1 + 0.05) / (l2 + 0.05); };
    const melange = (dessus, alpha, dessous) => dessous.map((c, i) => c * (1 - alpha) + dessus[i] * alpha);
    // Étape A : accueil sombre par défaut (eau sombre de Zencoder sur fond sombre) ; la date et l'alerte sont
    // AU-DESSUS de l'eau, les boutons dessous.
    ecran.changerCouleurs(accueilCap.EAU_SOMBRE.map(c => [...c]));
    const clair = rgb(fenetre.getComputedStyle(ui.doc.body).backgroundColor);
    const pireEau = accueilCap.EAU_SOMBRE[1].map(c => Math.max(0, c - 22));
    const opaciteEau = Number(fenetre.getComputedStyle(ui.parId('eau-accueil')).opacity);
    let eauVue = melange(pireEau, opaciteEau, clair);
    let pire = 99;
    const verifierTextes = racine => {
      for (const el of [racine, ...racine.querySelectorAll('*')]) {
        if (!el.childNodes || ![...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) continue;
        if (el.closest('[hidden], dialog')) continue;
        // Les entrées d'une liste déroulante s'affichent dans une fenêtre du téléphone, jamais sur l'eau.
        if (el.closest('select, option, datalist')) continue;
        // Fond réellement vu derrière ce texte : les fonds transparents empilés jusqu'à l'eau.
        const couches = [];
        for (let x = el; x && x !== ui.doc.body; x = x.parentElement) couches.push(rgb(fenetre.getComputedStyle(x).backgroundColor));
        let fondVu = eauVue;
        for (const c of couches.reverse()) if (c.length >= 3) fondVu = melange(c, c.length === 4 ? c[3] : 1, fondVu);
        const ratio = contraste(rgb(fenetre.getComputedStyle(el).color), fondVu);
        pire = Math.min(pire, ratio);
        attendre(ratio >= 8, `texte pas assez lisible (${ratio.toFixed(1)}:1) : ${el.id || el.className || el.tagName} « ${el.textContent.trim().slice(0, 25)} »`);
      }
    };
    for (const sel of ['#alerte-google', '.bouton-scanner', '.barre-recherche', '#date']) {
      const el = ui.doc.querySelector(sel);
      if (el) verifierTextes(el);
    }
    // 08/11/2026 : MODE CLAIR sur l'accueil (fond #d9e4e2, eau de Zencoder à 60 %), même pire cas, même exigence.
    ui.doc.documentElement.classList.add('theme-cap-clair');
    ecran.changerCouleurs(accueilCap.EAU_CLAIRE.map(c => [...c]));
    {
      const fondClair = rgb(fenetre.getComputedStyle(ui.doc.body).backgroundColor);
      const opaciteClaire = Number(fenetre.getComputedStyle(ui.parId('eau-accueil')).opacity);
      attendreEgal([fondClair, opaciteClaire], [[217, 228, 226], 0.6], 'réglages du mode clair');
      eauVue = melange(accueilCap.EAU_CLAIRE[1].map(c => Math.max(0, c - 22)), opaciteClaire, fondClair);
      for (const sel of ['#alerte-google', '#date']) verifierTextes(ui.doc.querySelector(sel));
    }
    ui.doc.documentElement.classList.remove('theme-cap-clair');
    ecran.changerCouleurs(accueilCap.EAU_SOMBRE.map(c => [...c]));
    eauVue = melange(pireEau, opaciteEau, clair);
    ui.parId('basculer-vue').click();
    // L'écran des tâches garde son allure claire (accueil_cap.js remet l'eau claire) : eau pâle derrière.
    ecran.changerCouleurs(null);
    {
      const fondHex = fenetre.getComputedStyle(ui.doc.documentElement).getPropertyValue('--fond').trim();
      const pale = [1, 3, 5].map(i => parseInt(fondHex.slice(i, i + 2), 16));
      eauVue = melange(pale.map((c, i) => Math.round(c * 0.8 + [120, 150, 165][i] * 0.2) - 22), opaciteEau, pale);
    }
    attendre(ui.doc.querySelectorAll('.tuile').length > 0, 'aucune tuile à vérifier');
    for (const tuile of ui.doc.querySelectorAll('.tuile')) {
      verifierTextes(tuile);
      attendre(/rgba?\([^)]*0\.6\)/.test(fenetre.getComputedStyle(tuile).backgroundColor), `tuile pas semi-transparente : ${fenetre.getComputedStyle(tuile).backgroundColor}`);
    }
    ui.parId('basculer-vue').click();
    attendre(pire >= 8 && pire < 99, `contraste minimal : ${pire}`);
    // Chaque bouton visible de l'accueil (les deux vues : accueil et tuiles) reçoit le toucher.
    const centre = el => { const r = el.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; };
    const visibles = () => [...ui.doc.querySelectorAll('.ecran button')].filter(b => {
      if (b.closest('[hidden], dialog, [inert]') || b.classList.contains('visuellement-cache')) return false;
      const r = b.getBoundingClientRect();
      const [x, y] = centre(b);
      if (!(r.width > 0 && r.height > 0 && x >= 0 && y >= 0 && x < fenetre.innerWidth && y < fenetre.innerHeight)) return false;
      // Un bouton coupé par une zone qui défile (il faut faire défiler pour l'atteindre) n'est pas touchable au doigt.
      for (let parent = b.parentElement; parent; parent = parent.parentElement) {
        const st = fenetre.getComputedStyle(parent);
        if (!/(auto|scroll|hidden)/.test(`${st.overflowX} ${st.overflowY}`)) continue;
        const z = parent.getBoundingClientRect();
        if (x < z.left || x > z.right || y < z.top || y > z.bottom) return false;
      }
      return true;
    });
    for (const vue of ['accueil', 'tuiles']) {
      if (vue === 'tuiles') ui.parId('basculer-vue').click();
      const boutons = visibles();
      attendre(boutons.length >= (vue === 'accueil' ? 2 : 1), `pas assez de boutons visibles (${vue}) : ${boutons.length}`);
      if (vue === 'accueil') attendre(['ouvrir-chercher', 'microphone', 'ouvrir-autre'].every( /* 09/11/2026 */id => boutons.includes(ui.parId(id))), 'boutons de l’accueil absents des boutons testés');
      for (const b of boutons) {
        const touche = ui.doc.elementFromPoint(...centre(b));
        attendre(touche === b || b.contains(touche), `bouton recouvert (${vue}) : ${b.id || b.className || b.textContent.trim().slice(0, 30)} par ${touche ? (touche.id || touche.className || touche.tagName) : 'rien'}`);
        attendre(touche !== ui.parId('eau-accueil'), 'l’eau a reçu un toucher');
      }
    }
    ui.parId('basculer-vue').click();
    // Toucher une tuile ou un bouton : le bouton fonctionne ET l'eau bouge.
    const avant = ecran.fond.etat().touchers;
    let ouvert = false;
    ui.parId('ouvrir-autre').addEventListener('click', () => { ouvert = true; }, { once: true });
    const [x, y] = centre(ui.parId('ouvrir-autre'));
    const cible = ui.doc.elementFromPoint(x, y);
    cible.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, pointerId: 3, clientX: x, clientY: y, isPrimary: true }));
    cible.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, pointerId: 3, clientX: x, clientY: y, isPrimary: true }));
    cible.click();
    attendre(ouvert, '« Autre » ne répond pas sous l’eau');
    attendre(ecran.fond.etat().touchers > avant, 'l’eau ne bouge pas au toucher');
    // Pendant l'écran d'ouverture : l'eau de l'accueil s'arrête ; elle repart après l'entrée.
    ui.parId('aller-eau').click();
    attendre(ecran.etat().visible && !ecran.fond.etat().active, 'eau de l’accueil pas arrêtée pendant l’ouverture');
    glisserSurEau(ui);
    attendre(!ecran.etat().visible && ecran.fond.etat().active, 'eau de l’accueil pas relancée après l’entrée');
    // Cap en arrière-plan : arrêtée (batterie) ; au retour : relancée.
    ui.visibilite(true);
    attendre(!ecran.fond.etat().active, 'eau pas arrêtée en arrière-plan');
    ui.visibilite(false);
    attendre(ecran.fond.etat().active, 'eau pas relancée au retour');
  });

  await testAsync('Eau sur l’accueil (lot c22) : elle suit le doigt pendant un défilement, sans jamais retenir le geste', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const h = horlogeEau();
    const ecran = ecranEau.auDemarrage(ui.doc, { stockage: { getItem: () => 'oui', setItem: () => {} }, raf: h.raf, caf: h.caf, reglages: { fond: 'aucun', dureeSortieMs: 0 } });
    attendre(ecran.fond.etat().active, 'eau de l’accueil absente');
    ui.parId('basculer-vue').click();
    const zone = ui.parId('ecran-complet');
    const avant = ecran.fond.etat().touchers;
    const mouvement = new Event('touchmove', { bubbles: true, cancelable: true });
    Object.defineProperty(mouvement, 'changedTouches', { value: [{ clientX: 200, clientY: 500 }, { clientX: 210, clientY: 480 }] });
    zone.dispatchEvent(mouvement);
    attendre(ecran.fond.etat().touchers >= avant + 2, 'l’eau ne suit pas le doigt pendant le défilement');
    attendre(!mouvement.defaultPrevented, 'le défilement a été bloqué par l’eau');
  });

  await testAsync('Interrupteur « Eau » (lot c21) : arrêt = aucune eau nulle part, aucune animation, aucun toucher perdu, Cap démarre normalement ; réglage gardé', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const h = horlogeEau();
    const prefs = new Map();
    const preferences = { getItem: k => prefs.get(k) ?? null, setItem: (k, v) => prefs.set(k, String(v)) };
    const session = new Map();
    const stockage = { getItem: k => session.get(k) ?? null, setItem: (k, v) => session.set(k, v) };
    const fenetre = ui.cadre.contentWindow;
    // En marche par défaut : l'eau d'ouverture s'affiche.
    let ecran = ecranEau.auDemarrage(ui.doc, { stockage, preferences, raf: h.raf, caf: h.caf, reglages: { fond: 'aucun', dureeSortieMs: 0 } });
    attendre(ecran.eauActive() && ecran.etat().visible, 'eau absente en marche');
    attendreEgal(ui.parId('interrupteur-eau').getAttribute('aria-checked'), 'true', 'interrupteur en marche');
    glisserSurEau(ui);
    // Arrêt depuis l'accueil (bouton dans « Afficher tout »).
    ui.parId('interrupteur-eau').click();
    attendre(!ecran.eauActive() && !ecran.fond.etat().active, 'eau de l’accueil pas arrêtée');
    attendreEgal(prefs.get(ecranEau.CLE_ACTIVE), 'non', 'réglage non gardé');
    attendreEgal(ui.parId('etat-interrupteur-eau').textContent, 'arrêtée', 'texte de l’interrupteur');
    attendreEgal(fenetre.getComputedStyle(ui.parId('eau-accueil')).display, 'none', 'eau de l’accueil encore visible');
    attendreEgal(fenetre.getComputedStyle(ui.parId('aller-eau')).display, 'none', 'bouton « Eau » encore là à l’arrêt');
    // Nouveau démarrage de Cap avec l'interrupteur sur arrêt : aucune eau, aucune animation, l'accueil tout de suite.
    const ui2 = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const h2 = horlogeEau();
    const ecran2 = ecranEau.auDemarrage(ui2.doc, { stockage: { getItem: () => null, setItem: () => {} }, preferences, raf: h2.raf, caf: h2.caf, reglages: { fond: 'aucun', dureeSortieMs: 0 } });
    const fenetre2 = ui2.cadre.contentWindow;
    attendre(!ecran2.eauActive() && !ecran2.etat().visible && !ecran2.fond.etat().active, 'eau au démarrage malgré l’arrêt');
    attendreEgal(h2.appels.length, 0, 'animation lancée malgré l’arrêt');
    attendreEgal(fenetre2.getComputedStyle(ui2.parId('toile-eau')).display, 'none', 'eau d’ouverture visible malgré l’arrêt');
    attendreEgal(fenetre2.getComputedStyle(ui2.doc.body).backgroundColor, 'rgb(10, 12, 12)', 'fond du thème absent sans eau');
    const centre = el => { const r = el.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; };
    const toucheSansEau = ui2.doc.elementFromPoint(...centre(ui2.parId('ouvrir-autre')));
    attendre(toucheSansEau === ui2.parId('ouvrir-autre') || ui2.parId('ouvrir-autre').contains(toucheSansEau), '« Autre » recouvert sans eau');
    // Remise en marche : l'eau revient tout de suite sur l'accueil, réglage gardé.
    ui2.parId('interrupteur-eau').click();
    attendre(ecran2.eauActive() && ecran2.fond.etat().active, 'eau pas revenue');
    attendreEgal(prefs.get(ecranEau.CLE_ACTIVE), 'oui', 'remise en marche non gardée');
    // Préférences illisibles : l'eau reste en marche, sans erreur.
    const ui3 = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const casse = { getItem: () => { throw new Error('refusé'); }, setItem: () => { throw new Error('refusé'); } };
    const ecran3 = ecranEau.auDemarrage(ui3.doc, { stockage: casse, preferences: casse, raf: h.raf, caf: h.caf, reglages: { fond: 'aucun', dureeSortieMs: 0 } });
    attendre(ecran3.eauActive(), 'eau coupée par des préférences illisibles');
    ecran3.changerEau(false);
    attendre(!ecran3.eauActive(), 'arrêt impossible quand les préférences refusent');
  });

  await testAsync('Barre du bas (lot c21) : Cap envoie à l’application Android la couleur de l’eau en bas, et le fond seul sans eau', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const h = horlogeEau();
    const recues = [];
    ui.cadre.contentWindow.CouleursAndroid = { changer: (haut, bas) => recues.push([haut, bas]) };
    const prefs = new Map();
    const preferences = { getItem: k => prefs.get(k) ?? null, setItem: (k, v) => prefs.set(k, String(v)) };
    const ecran = ecranEau.auDemarrage(ui.doc, { stockage: { getItem: () => 'oui', setItem: () => {} }, preferences, raf: h.raf, caf: h.caf, reglages: { fond: 'aucun', dureeSortieMs: 0 } });
    attendre(recues.length >= 1, 'aucune couleur envoyée au téléphone');
    const [haut, bas] = recues[recues.length - 1];
    attendreEgal(haut, '#eaf1f4', 'bande du haut');
    attendre(/^#[0-9a-f]{6}$/.test(bas) && bas !== haut, `bande du bas sans la couleur de l’eau : ${bas}`);
    // Couleur attendue : le fond et l'eau « profonde » mélangés à l'opacité de l'eau (0,55).
    const attendu = ecranEau.couleursBandes(ui.doc, true).bas;
    attendreEgal(bas, attendu, 'couleur du bas');
    ui.parId('interrupteur-eau').click();
    const dernier = recues[recues.length - 1];
    attendreEgal(dernier, ['#eaf1f4', '#eaf1f4'], 'sans eau : le fond partout');
    // Hors de l'application Android (pas de pont) : aucune erreur.
    delete ui.cadre.contentWindow.CouleursAndroid;
    ecran.changerEau(true);
    attendre(ecran.eauActive(), 'erreur sans application Android');
  });

  await testAsync('Écran d’eau : le petit bouton « Eau » y ramène ; couche d’eau sans toucher ; gestes bloqués seulement sur l’eau ; aucune adresse extérieure', async c => {
    const ui = preparerInterface(c, { largeur: 412, hauteur: 900 });
    const h = horlogeEau();
    const memoire = new Map([[ecranEau.CLE_VUE, 'oui']]);
    const stockage = { getItem: k => memoire.get(k) ?? null, setItem: (k, v) => memoire.set(k, v) };
    const ecran = ecranEau.auDemarrage(ui.doc, { stockage, raf: h.raf, caf: h.caf, reglages: { fond: 'aucun', dureeSortieMs: 0 } });
    attendre(!ecran.etat().visible, 'eau montrée alors qu’elle a déjà été vue');
    ui.parId('aller-eau').click();
    attendre(ecran.etat().visible && ecran.etat().animation, 'le bouton « Eau » ne ramène pas à l’eau');
    const style = el => ui.cadre.contentWindow.getComputedStyle(el);
    attendreEgal(style(ui.parId('toile-eau')).pointerEvents, 'none', 'la couche d’eau capte les touchers');
    attendreEgal(style(ui.parId('ecran-eau')).touchAction, 'none', 'gestes non bloqués sur l’eau');
    attendre(style(ui.doc.body).touchAction !== 'none' && style(ui.doc.querySelector('.ecran')).touchAction !== 'none', 'gestes bloqués dans tout Cap');
    ecran.entrerDansCap();
    attendre(!ecran.etat().visible, 'eau restée');
    const source = SOURCE_ECRAN_EAU;
    attendre(!/https?:\/\//.test(source) && !/indexedDB|fetch\(/.test(source), 'adresse extérieure ou envoi dans l’écran d’eau');
    attendreEgal((source.match(/localStorage/g) || []).length, 1, 'stockage durable autre que la préférence de l’interrupteur');
  });

  await testAsync('Classement étape 1 : Doc et tableur choisis chacun à part, bon type vérifié, rien gardé sinon', async c => {
    function monter(docs, memoire = espaceMemoire()) {
      const fonctions = [];
      const numeros = [];
      const vues = [];
      const fauxGoogle = { picker: {
        Action: { PICKED: 'picked', CANCEL: 'cancel', LOADED: 'loaded' }, ViewId: { DOCS: 'docs' },
        Feature: { MULTISELECT_ENABLED: 'multi' },
        DocsView: class { constructor() { vues.push(this); } setIncludeFolders() { return this; } setMimeTypes(t) { this.types = t; return this; } },
        PickerBuilder: class {
          addView() { return this; } enableFeature(f) { fonctions.push(f); return this; } setOAuthToken() { return this; }
          setAppId(numero) { numeros.push(numero); return this; }
          setDeveloperKey() { return this; } setTitle() { return this; } setCallback(f) { this.rappel = f; return this; }
          build() { const b = this; return { setVisible: () => b.rappel({ action: 'picked', docs }) }; }
        }
      } };
      const piqueur = objetIsole(SOURCE_GOOGLE_PICKER, 'googlePicker', {
        localStorage: memoire, googleConnexion: { connecte: () => true, jeton: () => 'jeton-fictif', appeler: c.fetch },
        googleSheets: c.tableauAgenda, REGLAGES_GOOGLE, google: fauxGoogle,
        clePicker: { presente: () => true, lire: () => 'cle-fictive' }, window: { gapi: { load: (n, o) => o.callback() } }
      });
      return { piqueur, fonctions, numeros, vues, memoire };
    }
    const doc = { id: 'doc-fictif', name: 'Architecture FICTIVE', mimeType: 'application/vnd.google-apps.document' };
    const tableur = { id: 'tableur-fictif', name: 'Classement FICTIF', mimeType: 'application/vnd.google-apps.spreadsheet' };
    const memoire = espaceMemoire();
    // Le Doc d'abord : seul le type Doc est montré, et seul le Doc est gardé.
    const premier = monter([doc], memoire);
    attendreEgal((await premier.piqueur.choisirFichier('architecture')).id, 'doc-fictif', 'Doc gardé');
    attendreEgal(premier.vues[0].types, 'application/vnd.google-apps.document', 'fenêtre limitée aux Docs');
    attendreEgal(premier.fonctions, [], 'sélection multiple encore demandée');
    // Numéro du projet Cap donné à la fenêtre (début public de l'identifiant client), pour drive.file.
    attendreEgal(premier.numeros, [REGLAGES_GOOGLE.id_client.split('-')[0]], 'numéro du projet absent');
    attendre(/^\d+$/.test(premier.numeros[0]), 'numéro du projet mal formé');
    attendreEgal(premier.piqueur.dossierChoisi('tableur_classement'), null, 'tableur choisi sans le demander');
    // Puis le tableur, indépendamment : le Doc déjà choisi reste.
    const second = monter([tableur], memoire);
    attendreEgal((await second.piqueur.choisirFichier('tableur_classement')).id, 'tableur-fictif', 'tableur gardé');
    attendreEgal(second.vues[0].types, 'application/vnd.google-apps.spreadsheet', 'fenêtre limitée aux tableurs');
    attendreEgal(second.piqueur.dossierChoisi('architecture').id, 'doc-fictif', 'Doc perdu en choisissant le tableur');
    await second.piqueur.rangerDansDrive('architecture');
    await second.piqueur.rangerDansDrive('tableur_classement');
    attendreEgal([c.proprietesDrive.cap_fichier_architecture, c.proprietesDrive.cap_fichier_tableur_classement],
      ['doc-fictif', 'tableur-fictif'], 'identifiants rangés dans le Drive');
    attendreEgal((await monter([]).piqueur.retrouverDepuisDrive('tableur_classement')).id, 'tableur-fictif', 'retrouvé par la coque');
    // Mauvais type : refus clair, rien gardé, l'ancien choix intact.
    const mauvais = monter([tableur], memoire);
    await attendreRejet(() => mauvais.piqueur.choisirFichier('architecture'), 'n’est pas un Google Doc');
    attendreEgal(mauvais.piqueur.dossierChoisi('architecture').id, 'doc-fictif', 'ancien Doc remplacé par un mauvais fichier');
    const neuf = monter([doc]);
    await attendreRejet(() => neuf.piqueur.choisirFichier('tableur_classement'), 'n’est pas un tableur');
    attendreEgal(neuf.piqueur.dossierChoisi('tableur_classement'), null, 'mauvais fichier gardé');
    await attendreRejet(() => neuf.piqueur.choisirFichier('documents_personnels'), 'Fichier inconnu');
  });

  // ---------- Journaux de chantier (étape 2) : faux Drive, noms inventés ----------
  function fauxDriveJournaux(c, etat) {
    etat.fichiers ||= [];
    etat.lignes ||= {};
    return async r => {
      if (r.url.hostname === 'www.googleapis.com' && r.url.pathname === '/drive/v3/files' && r.methode === 'GET') {
        const q = r.url.searchParams.get('q');
        const trouve = etat.fichiers.find(f => q.includes(`name='${f.name}'`) && q.includes(`mimeType='${f.mimeType}'`)
          && q.includes(`'${f.parents[0]}' in parents`));
        return reponseGoogle({ files: trouve ? [{ id: trouve.id }] : [] });
      }
      if (r.url.hostname === 'www.googleapis.com' && r.url.pathname === '/drive/v3/files' && r.methode === 'POST') {
        const id = `cree-${etat.fichiers.length + 1}`;
        etat.fichiers.push({ id, ...r.corps });
        return reponseGoogle({ id });
      }
      const ajout = /^\/v4\/spreadsheets\/([^/]+)\/values\/A1:append$/.exec(r.url.pathname);
      if (r.url.hostname === 'sheets.googleapis.com' && ajout && r.methode === 'POST') {
        if (etat.panne) return reponseGoogle({ error: { code: 503 } }, 503);
        attendreEgal([r.url.searchParams.get('valueInputOption'), r.url.searchParams.get('insertDataOption')],
          ['RAW', 'INSERT_ROWS'], 'ajout en fin de tableur, texte tel quel');
        (etat.lignes[ajout[1]] ||= []).push(...r.corps.values);
        return reponseGoogle({});
      }
      throw new Error(`Requête inattendue : ${r.methode} ${r.url}`);
    };
  }
  function monterJournaux(c, memoire = c.localStorage, navigateur = c.navigator) {
    const piqueur = objetIsole(SOURCE_GOOGLE_PICKER, 'googlePicker', {
      localStorage: memoire, googleConnexion: c.googleConnexion, googleSheets: c.tableauAgenda,
      REGLAGES_GOOGLE, clePicker: { presente: () => true, lire: () => 'cle-fictive' }, window: c.window
    });
    const module = objetIsole(SOURCE_JOURNAUX, 'journaux', {
      localStorage: memoire, googleConnexion: c.googleConnexion, googlePicker: piqueur, REGLAGES_GOOGLE, navigator: navigateur
    });
    return { piqueur, journaux: module };
  }

  await testAsync('Journaux : dossier « Journaux » et deux Google Sheets créés dans App Cap, noms exacts, une ligne ajoutée', async c => {
    const etat = {};
    c.repondre = fauxDriveJournaux(c, etat);
    const { piqueur, journaux } = monterJournaux(c);
    piqueur.enregistrerDossier('app-cap-fictif', 'App Cap', 'app_cap');
    journaux.ajouter('numerisation', { action: 'Lecture du classement', resultat: 'réussie', details: 'Tableur : lu. ; Doc : lu.' });
    const bilan = await journaux.envoyer();
    attendreEgal(REGLAGES_GOOGLE.journaux, { numerisation: 'Journal Numérisation', general: 'Journal Général' }, 'noms exacts');
    attendreEgal(etat.fichiers.map(f => [f.name, f.mimeType, f.parents[0]]), [
      ['Journaux', 'application/vnd.google-apps.folder', 'app-cap-fictif'],
      ['Journal Numérisation', 'application/vnd.google-apps.spreadsheet', 'cree-1'],
      ['Journal Général', 'application/vnd.google-apps.spreadsheet', 'cree-1']
    ], 'dossier et tableurs créés au bon endroit');
    const numerisation = etat.lignes['cree-2'];
    attendreEgal(numerisation[0], ['Date', 'Heure', 'Action', 'Résultat', 'Détails'], 'en-têtes du Journal Numérisation');
    attendreEgal(numerisation[1].slice(2), ['Lecture du classement', 'réussie', 'Tableur : lu. ; Doc : lu.'], 'ligne ajoutée');
    attendre(/^\d{4}-\d{2}-\d{2}$/.test(numerisation[1][0]) && /^\d{2}:\d{2}:\d{2}$/.test(numerisation[1][1]), 'date ou heure à la seconde');
    const general = etat.lignes['cree-3'];
    attendreEgal(general[0], ['Date', 'Heure', 'Action', 'Résultat', 'Détails', 'Chantier'], 'en-têtes du Journal Général');
    attendreEgal(general.slice(1).map(l => l.slice(2)), [
      ['Création du journal', 'créé', 'Journal Numérisation', 'Numérisation'],
      ['Création du journal', 'créé', 'Journal Général', 'Numérisation']
    ], 'créations notées dans le Journal Général');
    attendreEgal([bilan.restantes, journaux.enAttente()], [0, 0], 'file vidée après réussite');
    attendreEgal([c.proprietesDrive.cap_journal_numerisation, c.proprietesDrive.cap_journal_general, c.proprietesDrive.cap_dossier_journaux],
      ['cree-2', 'cree-3', 'cree-1'], 'identifiants rangés dans le Drive pour la coque');
    // Deuxième ligne : rien n'est recréé, seulement un ajout.
    const avant = etat.fichiers.length;
    journaux.ajouter('general', { action: 'Essai FICTIF', resultat: 'ok', chantier: 'Numérisation' });
    await journaux.envoyer();
    attendreEgal(etat.fichiers.length, avant, 'journal recréé');
    attendreEgal(etat.lignes['cree-3'].at(-1).slice(2), ['Essai FICTIF', 'ok', '', 'Numérisation'], 'ligne ajoutée à la fin');
    attendre(c.requetes.every(r => r.methode === 'GET' || r.methode === 'POST'
      || (r.methode === 'PATCH' && Object.keys(r.corps || {}).join() === 'appProperties')), 'modification ou effacement');
    attendre(c.requetes.every(r => !/:clear|batchClear|:batchUpdate|values\/[^:]*$/.test(r.url.pathname) || r.methode === 'GET'), 'écriture hors ajout');
  });

  await testAsync('Journaux : panne de Google ou hors connexion = lignes gardées sur le téléphone, envoyées ensuite, sans perte ni doublon', async c => {
    preparerConnexion(c);
    const etat = { panne: true };
    c.repondre = fauxDriveJournaux(c, etat);
    const { piqueur, journaux } = monterJournaux(c);
    piqueur.enregistrerDossier('app-cap-fictif', 'App Cap', 'app_cap');
    journaux.ajouter('numerisation', { action: 'Lecture du classement', resultat: 'échouée', details: 'Doc : refusé' });
    await attendreRejet(() => journaux.envoyer(), '503');
    // Attendent : la ligne, les en-têtes des deux journaux et les deux lignes de création.
    attendreEgal(journaux.enAttente(), 5, 'ligne perdue pendant la panne');
    c.navigator.onLine = false;
    journaux.ajouter('numerisation', { action: 'Essai hors connexion FICTIF', resultat: 'gardé' });
    const requetes = c.requetes.length;
    attendreEgal((await journaux.envoyer()).envoyees, 0, 'envoi tenté hors connexion');
    attendreEgal(c.requetes.length, requetes, 'requête hors connexion');
    c.navigator.onLine = true;
    etat.panne = false;
    await journaux.envoyer();
    attendreEgal(journaux.enAttente(), 0, 'file non vidée après le retour');
    attendreEgal(etat.lignes['cree-2'][0], ['Date', 'Heure', 'Action', 'Résultat', 'Détails'], 'en-têtes perdus après la panne');
    const lignes = etat.lignes['cree-2'].slice(1).map(l => l[2]);
    attendreEgal(lignes, ['Lecture du classement', 'Essai hors connexion FICTIF'], 'lignes envoyées une seule fois, dans l’ordre');
    attendreEgal(etat.lignes['cree-3'][0], ['Date', 'Heure', 'Action', 'Résultat', 'Détails', 'Chantier'], 'en-têtes du Journal Général perdus');
    attendreEgal(etat.fichiers.filter(f => f.name === 'Journal Numérisation').length, 1, 'journal créé deux fois après la panne');
  });

  await testAsync('Journaux : coque sans App Cap = relit les tableurs rangés dans le Drive ; sinon rien de créé, lignes gardées', async c => {
    const etat = {};
    c.repondre = fauxDriveJournaux(c, etat);
    // Coque toute neuve, rien de rangé : aucune création, la ligne attend.
    const neuve = monterJournaux(c, espaceMemoire());
    neuve.journaux.ajouter('numerisation', { action: 'Essai FICTIF', resultat: 'gardé' });
    await attendreRejet(() => neuve.journaux.envoyer(), 'App Cap');
    attendreEgal([etat.fichiers.length, neuve.journaux.enAttente()], [0, 1], 'création sans App Cap ou ligne perdue');
    // Chrome a créé les journaux et rangé leurs identifiants : la coque les retrouve et ajoute seulement.
    const chrome = monterJournaux(c);
    chrome.piqueur.enregistrerDossier('app-cap-fictif', 'App Cap', 'app_cap');
    chrome.journaux.ajouter('general', { action: 'Essai Chrome FICTIF', resultat: 'ok', chantier: 'Numérisation' });
    await chrome.journaux.envoyer();
    const crees = etat.fichiers.length;
    await neuve.journaux.envoyer();
    attendreEgal([etat.fichiers.length, neuve.journaux.enAttente()], [crees, 0], 'coque : recréation ou ligne non envoyée');
    attendreEgal(etat.lignes['cree-2'].at(-1).slice(2, 4), ['Essai FICTIF', 'gardé'], 'ligne de la coque dans le bon journal');
  });

  await testAsync('Journaux : texte gardé tel quel (jamais une formule), action obligatoire, journal inconnu refusé', async c => {
    const etat = {};
    c.repondre = fauxDriveJournaux(c, etat);
    const { piqueur, journaux } = monterJournaux(c);
    piqueur.enregistrerDossier('app-cap-fictif', 'App Cap', 'app_cap');
    journaux.ajouter('numerisation', { action: '=SOMME(A1:A9) FICTIF', resultat: '+1', details: 'ligne\nsur  deux' });
    await journaux.envoyer();
    attendreEgal(etat.lignes['cree-2'][1].slice(2), ['=SOMME(A1:A9) FICTIF', '+1', 'ligne sur deux'], 'texte modifié');
    let message = '';
    try { journaux.ajouter('numerisation', { action: '  ' }); } catch (erreur) { message = erreur.message; }
    attendre(message.includes('action'), 'ligne sans action acceptée');
    message = '';
    try { journaux.ajouter('inconnu', { action: 'x' }); } catch (erreur) { message = erreur.message; }
    attendre(message.includes('inconnu'), 'journal inconnu accepté');
  });

  await testAsync('Google Agenda : Drive injoignable, aucun second agenda créé dans le doute', async c => {
    c.tableauAgenda.trouverOuCreer = async () => { throw new Error('Drive injoignable FICTIF'); };
    c.repondre = async r => { throw new Error(`Requête inattendue : ${r.url}`); };
    await attendreRejet(() => c.agenda().trouverOuCreer(), 'Drive injoignable FICTIF');
    attendreEgal(c.requetes.filter(r => r.methode === 'POST').length, 0, 'agenda créé malgré le doute');
  });

  await testAsync('Google Agenda : vraie connexion, sans identifiant gardé, jamais déconnecté par un 403', async c => {
    preparerConnexion(c);
    let deconnexions = 0;
    c.window.addEventListener('cap-google-deconnecte', () => deconnexions++);
    c.repondre = async r => {
      if (r.url.pathname.includes('calendarList')) return reponseGoogle({ error: { code: 403 } }, 403);
      if (r.methode === 'POST' && r.url.pathname === '/calendar/v3/calendars') return reponseGoogle({ id: 'agenda-coque-fictif' });
      if (r.methode === 'POST' && r.url.pathname === '/calendar/v3/calendars/agenda-coque-fictif/events') return reponseGoogle({});
      throw new Error(`Requête inattendue : ${r.url}`);
    };
    attendreEgal(await c.agenda().trouverOuCreer(), 'agenda-coque-fictif', 'agenda créé avec la vraie connexion');
    attendreEgal(deconnexions, 0, 'déconnexion pendant l’ouverture de l’agenda');
    attendre(c.googleConnexion.connecte(), 'jeton retiré pendant l’ouverture de l’agenda');
    attendre(c.requetes.every(r => !r.url.pathname.includes('calendarList')), 'liste des agendas lue sans droit');
    attendreEgal(c.proprietesDrive.cap_agenda_id, 'agenda-coque-fictif', 'identifiant rangé dans le Drive');
  });

  await testAsync('Google Agenda : formats d’heures en description', async c => {
    let cree = false;
    const descriptions = ['14h30 – FICTIF', '14h – FICTIF', '14:30 – FICTIF', '9h05 – FICTIF',
      '25h30 – FICTIF', '14h99 – FICTIF', '14h300 – FICTIF', 'FICTIF à 14h'];
    c.repondre = async r => {
      if (r.methode === 'POST' && r.url.pathname === '/calendar/v3/calendars') {
        cree = true;
        return reponseGoogle({ id: 'agenda-secondaire-fictif' });
      }
      if (r.methode === 'POST' && r.url.pathname.endsWith('/events')) return reponseGoogle({});
      if (r.methode === 'GET' && r.url.pathname.endsWith('/events')) {
        return reponseGoogle({ items: descriptions.map(description => ({
          summary: 'Heure FICTIF', start: { date: '2030-01-11' }, description
        })) });
      }
      throw new Error('Requête inattendue FICTIF');
    };
    const rendezVous = await c.agenda().prochainsRendezVous(8);
    attendre(cree, 'agenda secondaire non créé');
    attendreEgal(rendezVous.map(rendezVous => rendezVous.heure),
      ['14:30', '14:00', '14:30', '09:05', '', '', '', ''], 'formats exacts et heures invalides');
  });

  function preparerFicheRendezVous(c, changements = {}) {
    const evenement = {
      id: 'rdv-fictif', etag: '"version-fictive"', summary: 'Consultation FICTIF',
      location: '12 rue Fictive',
      description: 'Préparation FICTIF\nTéléphone : 01 00 00 00 00\nMail : cabinet.fictif@example.com',
      start: { dateTime: '2030-01-10T09:15:00Z' },
      end: { dateTime: '2030-01-10T10:00:00Z' },
      reminders: { useDefault: false, overrides: [{ method: 'popup', minutes: 60 }, { method: 'email', minutes: 10 }] },
      ...changements
    };
    c.agendaModifiable = 'agenda-fictif';
    c.localStorage.setItem('cap_google_agenda_v1', c.agendaModifiable);
    // Identifiant déjà rangé dans le Drive : les tests de fiche ne voient que les appels à l'agenda.
    c.localStorage.setItem('cap_google_agenda_drive_v1', c.agendaModifiable);
    c.repondre = async r => {
      const base = `/calendar/v3/calendars/${encodeURIComponent(c.agendaModifiable)}`;
      if (r.methode === 'GET' && r.url.pathname === base) {
        return reponseGoogle({ id: c.agendaModifiable, summary: REGLAGES_GOOGLE.nom_agenda, primary: false });
      }
      if (r.methode === 'GET' && r.url.pathname === `${base}/events`) return reponseGoogle({ items: [evenement] });
      if (r.methode === 'GET' && r.url.pathname === `${base}/events/${evenement.id}`) return reponseGoogle(evenement);
      if (r.methode === 'PATCH' && r.url.pathname === `${base}/events/${evenement.id}`) {
        const resultat = { ...evenement, ...r.corps };
        for (const champ of ['start', 'end']) {
          if (r.corps[champ]?.dateTime) resultat[champ] = { ...r.corps[champ],
            dateTime: r.corps[champ].dateTime + (r.corps[champ].dateTime.startsWith('2030-07-') ? '+02:00' : '+01:00') };
        }
        return reponseGoogle(resultat);
      }
      throw new Error(`Requête de fiche inattendue : ${r.methode} ${r.url}`);
    };
    return evenement;
  }

  function ancienRendezVous(evenement) {
    return Object.fromEntries(['summary', 'location', 'description', 'start', 'end', 'reminders']
      .map(champ => [champ, evenement[champ] ?? null]));
  }

  await testAsync('Google Agenda fiche : description canonique aller-retour sans perte', async c => {
    const agenda = c.agenda();
    const informations = { heure_journee: '09:05', notes: 'Notes FICTIF <b>libres</b>\nDeuxième ligne\n',
      telephone: '01 00 00 00 00', mail: 'contact.fictif@example.com' };
    const texte = '09h05 – Notes FICTIF <b>libres</b>\nDeuxième ligne\n\nTéléphone : 01 00 00 00 00\nMail : contact.fictif@example.com';
    attendreEgal(agenda.ecrireDescription(informations), texte, 'description canonique');
    attendreEgal(agenda.lireDescription(texte), informations, 'champs extraits');
    attendreEgal(agenda.ecrireDescription(agenda.lireDescription(texte)), texte, 'second aller-retour');
    attendreEgal(c.requetes.length, 0, 'conversion locale');
  });

  for (const libelle of ['Téléphone', 'TELEPHONE', 'tÉlÉpHoNe']) {
    await testAsync(`Google Agenda fiche : extraction accent et casse ${libelle}`, async c => {
      attendreEgal(c.agenda().lireDescription(`Notes FICTIF\n${libelle} : 01 00 00 00 00\nmAiL : fictif@example.com`),
        { heure_journee: '', notes: 'Notes FICTIF', telephone: '01 00 00 00 00', mail: 'fictif@example.com' }, 'coordonnées extraites');
    });
  }

  await testAsync('Google Agenda fiche : notes libres et anciennes coordonnées doublonnées conservées', async c => {
    const agenda = c.agenda();
    const notes = 'Texte FICTIF à 14h\nTéléphone : ancien FICTIF\nMail : ancien.fictif@example.com\n\nTéléphone :\nMail :\nFin <b>FICTIF</b>';
    const texte = `${notes}\nTéléphone : 01 00 00 00 00\nMail : nouveau.fictif@example.com`;
    const informations = agenda.lireDescription(texte);
    attendreEgal(informations, { heure_journee: '', notes, telephone: '01 00 00 00 00', mail: 'nouveau.fictif@example.com' }, 'doublons gardés dans les notes');
    attendreEgal(agenda.ecrireDescription(informations), texte, 'texte complet conservé');
    attendreEgal(agenda.lireDescription('Notes FICTIF\n  espaces conservés  '),
      { heure_journee: '', notes: 'Notes FICTIF\n  espaces conservés  ', telephone: '', mail: '' }, 'notes libres intactes');
  });

  await testAsync('Google Agenda fiche : heure de journée entière extraite et réécrite', async c => {
    const agenda = c.agenda();
    for (const texte of ['9h05 – Notes FICTIF', '09:05 — Notes FICTIF', '9h05 - Notes FICTIF']) {
      const informations = agenda.lireDescription(texte);
      attendreEgal(informations, { heure_journee: '09:05', notes: 'Notes FICTIF', telephone: '', mail: '' }, 'heure et notes');
      attendreEgal(agenda.ecrireDescription(informations), '09h05 – Notes FICTIF', 'heure canonique');
    }
    attendreEgal(agenda.lireDescription('14h – Notes FICTIF').heure_journee, '14:00', 'heure sans minutes');
    attendreEgal(agenda.lireDescription('25h30 – Notes FICTIF').notes, '25h30 – Notes FICTIF', 'heure invalide conservée');
  });

  await testAsync('Google Agenda fiche : prochains rendez-vous enrichis et cache identique', async c => {
    const evenement = preparerFicheRendezVous(c);
    const agenda = c.agenda();
    const attendu = { id: evenement.id, titre: evenement.summary, date: '2030-01-10', heure: '10:15', heure_fin: '11:00',
      journee_entiere: false, lieu: evenement.location, notes: 'Préparation FICTIF', telephone: '01 00 00 00 00',
      mail: 'cabinet.fictif@example.com', rappels: [60], description: evenement.description };
    attendreEgal(await agenda.prochainsRendezVous(), [attendu], 'tous les champs de la fiche');
    attendreEgal(agenda.lireCache(), [attendu], 'lecture du cache enrichi');
    const cache = c.localStorage.getItem('cap_google_rendezvous_v1');
    attendreEgal(JSON.parse(cache).rendezvous, [attendu], 'cache persistant');
    c.googleConnexion.connecte = () => false;
    const nombre = c.requetes.length;
    attendreEgal(await agenda.prochainsRendezVous(), [attendu], 'secours hors connexion enrichi');
    attendreEgal(c.requetes.length, nombre, 'aucune requête déconnectée');
    attendreEgal(c.localStorage.getItem('cap_google_rendezvous_v1'), cache, 'cache non réécrit');
  });

  await testAsync('Google Agenda fiche : PATCH limité après identité, GET événement et historique complet', async c => {
    const evenement = preparerFicheRendezVous(c);
    const operations = [];
    const enregistrer = c.localStorage.setItem;
    c.localStorage.setItem = (cle, valeur) => {
      if (cle === 'cap_rdv_historique_v1') operations.push('historique');
      return enregistrer(cle, valeur);
    };
    const repondre = c.repondre;
    c.repondre = async r => {
      operations.push(`${r.methode} ${r.url.pathname}`);
      if (r.methode === 'PATCH') {
        const historique = JSON.parse(c.localStorage.getItem('cap_rdv_historique_v1'));
        attendreEgal(historique[0].ancien, ancienRendezVous(evenement), 'sauvegarde déjà écrite avant PATCH');
        attendreEgal(r.corps, { summary: 'Nouveau titre FICTIF' }, 'uniquement le champ demandé');
        attendreEgal(r.options.headers['If-Match'], evenement.etag, 'version concurrente protégée');
      }
      return repondre(r);
    };
    const avant = Date.now();
    const agenda = c.agenda();
    const resultat = await agenda.modifierRendezVous(evenement.id, { titre: 'Nouveau titre FICTIF' });
    attendreEgal(operations[0], 'GET /calendar/v3/calendars/agenda-fictif', 'identité agenda avant événement');
    attendreEgal(operations.filter(operation => operation !== 'GET /calendar/v3/calendars/agenda-fictif'),
      ['GET /calendar/v3/calendars/agenda-fictif/events/rdv-fictif', 'historique',
        'PATCH /calendar/v3/calendars/agenda-fictif/events/rdv-fictif'], 'GET événement puis sauvegarde puis PATCH');
    const historique = agenda.lireHistorique();
    attendreEgal(historique.length, 1, 'une ancienne version');
    attendreEgal(historique[0].id, evenement.id, 'identifiant sauvegardé');
    attendre(Date.parse(historique[0].enregistre_le) >= avant && Date.parse(historique[0].enregistre_le) <= Date.now(), 'date réelle de sauvegarde');
    attendreEgal(historique[0].ancien, ancienRendezVous(evenement), 'tous les champs anciens');
    attendreEgal(resultat, { id: evenement.id, titre: 'Nouveau titre FICTIF', date: '2030-01-10', heure: '10:15', heure_fin: '11:00',
      journee_entiere: false, lieu: evenement.location, notes: 'Préparation FICTIF', telephone: '01 00 00 00 00',
      mail: 'cabinet.fictif@example.com', rappels: [60], description: evenement.description }, 'objet de retour enrichi');
    attendreEgal(agenda.lireCache(), [resultat], 'fiche modifiée mise en cache');
    attendre(c.requetes.every(r => !r.url.pathname.includes('/calendars/primary') && r.methode !== 'DELETE'), 'jamais primary ni DELETE');
  });

  await testAsync('Google Agenda fiche : agenda découvert par trouverOuCreer utilisé pour le PATCH', async c => {
    const evenement = preparerFicheRendezVous(c);
    c.localStorage.setItem('cap_google_agenda_v1', 'primary');
    c.agendaModifiable = 'agenda-decouvert-fictif';
    c.localStorage.removeItem('cap_google_agenda_drive_v1');
    c.proprietesDrive.cap_agenda_id = c.agendaModifiable;
    await c.agenda().modifierRendezVous(evenement.id, { lieu: 'Autre lieu FICTIF' });
    attendreEgal(c.localStorage.getItem('cap_google_agenda_v1'), c.agendaModifiable, 'identifiant découvert mémorisé');
    attendreEgal(c.requetes.filter(r => r.methode === 'PATCH').map(r => r.url.pathname),
      ['/calendar/v3/calendars/agenda-decouvert-fictif/events/rdv-fictif'], 'PATCH seulement sur l’agenda trouvé');
    attendre(c.requetes.every(r => !r.url.pathname.includes('/calendars/primary') && r.methode !== 'DELETE'), 'principal et suppression interdits');
  });

  await testAsync('Google Agenda fiche : historique limité à 100, plus récent en premier', async c => {
    const evenement = preparerFicheRendezVous(c);
    const precedents = Array.from({ length: 100 }, (_, i) => ({ id: `ancien-fictif-${i}`, enregistre_le: '2029-01-01T00:00:00Z', ancien: {} }));
    c.localStorage.setItem('cap_rdv_historique_v1', JSON.stringify(precedents));
    const agenda = c.agenda();
    await agenda.modifierRendezVous(evenement.id, { lieu: 'Lieu modifié FICTIF' });
    const historique = agenda.lireHistorique();
    attendreEgal(historique.length, 100, 'plafond de versions');
    attendreEgal(historique[0].ancien, ancienRendezVous(evenement), 'nouvelle sauvegarde première');
    attendreEgal(historique[0].id, evenement.id, 'nouvelle sauvegarde identifiée');
    attendreEgal(historique.slice(1), precedents.slice(0, 99), 'ordre ancien conservé, plus ancien écarté');
  });

  for (const panne of ['écriture refusée', 'JSON illisible', 'objet au lieu de liste']) {
    await testAsync(`Google Agenda fiche : historique ${panne} bloque le PATCH`, async c => {
      const evenement = preparerFicheRendezVous(c);
      const brut = panne === 'JSON illisible' ? '{illisible FICTIF' : panne === 'objet au lieu de liste' ? '{}' : '[]';
      c.localStorage.setItem('cap_rdv_historique_v1', brut);
      const cache = JSON.stringify({ rendezvous: [{ id: evenement.id, titre: 'Cache FICTIF', date: '2030-01-10' }] });
      c.localStorage.setItem('cap_google_rendezvous_v1', cache);
      const enregistrer = c.localStorage.setItem;
      if (panne === 'écriture refusée') c.localStorage.setItem = (cle, valeur) => {
        if (cle === 'cap_rdv_historique_v1') throw new Error('Quota FICTIF');
        return enregistrer(cle, valeur);
      };
      await attendreRejet(() => c.agenda().modifierRendezVous(evenement.id, { titre: 'Refusé FICTIF' }),
        'Impossible de sauvegarder l’ancienne version sur ce téléphone. Le rendez-vous n’a pas été modifié.');
      attendre(c.requetes.some(r => r.methode === 'GET' && r.url.pathname.endsWith('/events/rdv-fictif')), 'ancienne version relue');
      attendre(!c.requetes.some(r => r.methode === 'PATCH'), 'aucun PATCH sans sauvegarde');
      attendreEgal(c.localStorage.getItem('cap_rdv_historique_v1'), brut, 'historique original intact');
      attendreEgal(c.localStorage.getItem('cap_google_rendezvous_v1'), cache, 'cache intact');
    });
  }

  for (const identite of [{ summary: 'Autre agenda FICTIF', primary: false },
    { summary: REGLAGES_GOOGLE.nom_agenda, primary: true }]) {
    await testAsync(`Google Agenda fiche : identité agenda refusée ${identite.primary ? 'principal' : 'mauvais nom'}`, async c => {
      const evenement = preparerFicheRendezVous(c);
      c.repondre = async r => {
        attendreEgal(r.methode, 'GET', 'lecture seulement');
        attendreEgal(r.url.pathname, '/calendar/v3/calendars/agenda-fictif', 'aucun accès événement avant identité');
        return reponseGoogle({ id: c.agendaModifiable, ...identite });
      };
      await attendreRejet(() => c.agenda().modifierRendezVous(evenement.id, { titre: 'Refusé FICTIF' }), 'FICTIF');
      attendre(c.requetes.length > 0 && c.requetes.every(r => !r.url.pathname.includes('/events')), 'refus avant GET événement');
      attendreEgal(c.localStorage.getItem('cap_rdv_historique_v1'), null, 'aucun historique créé');
    });
  }

  await testAsync('Google Agenda fiche : PATCH horaire Europe Paris, description et rappels popup', async c => {
    const evenement = preparerFicheRendezVous(c);
    const changements = { titre: 'Titre modifié FICTIF', date: '2030-07-12', heure: '14:30', heure_fin: '15:45',
      lieu: 'Studio FICTIF', notes: 'Nouvelles notes FICTIF\nDeuxième ligne', telephone: '02 00 00 00 00',
      mail: 'nouveau.fictif@example.com', rappels: [0, 60, 1440, 10080, 40320] };
    const description = 'Nouvelles notes FICTIF\nDeuxième ligne\nTéléphone : 02 00 00 00 00\nMail : nouveau.fictif@example.com';
    const resultat = await c.agenda().modifierRendezVous(evenement.id, changements);
    attendreEgal(c.requetes.find(r => r.methode === 'PATCH').corps, {
      summary: changements.titre, location: changements.lieu, description,
      start: { dateTime: '2030-07-12T14:30:00', timeZone: 'Europe/Paris' },
      end: { dateTime: '2030-07-12T15:45:00', timeZone: 'Europe/Paris' },
      reminders: { useDefault: false, overrides: changements.rappels.map(minutes => ({ method: 'popup', minutes })) }
    }, 'corps exact sans champs supplémentaires');
    attendreEgal(resultat, { id: evenement.id, titre: changements.titre, date: changements.date, heure: changements.heure,
      heure_fin: changements.heure_fin, journee_entiere: false, lieu: changements.lieu, notes: changements.notes,
      telephone: changements.telephone, mail: changements.mail, rappels: changements.rappels, description }, 'retour complet après PATCH');
  });

  await testAsync('Google Agenda fiche : suppression des coordonnées et des rappels sans DELETE', async c => {
    const evenement = preparerFicheRendezVous(c);
    const resultat = await c.agenda().modifierRendezVous(evenement.id, { telephone: '', mail: '', rappels: [] });
    attendreEgal(c.requetes.find(r => r.methode === 'PATCH').corps,
      { description: 'Préparation FICTIF', reminders: { useDefault: false, overrides: [] } }, 'vidage limité aux champs');
    attendreEgal([resultat.telephone, resultat.mail, resultat.rappels], ['', '', []], 'coordonnées et rappels vides');
  });

  await testAsync('Google Agenda fiche : heure seule de journée entière ne change aucune date', async c => {
    const evenement = preparerFicheRendezVous(c, { start: { date: '2030-01-10' }, end: { date: '2030-01-13' },
      description: '09h05 – Notes FICTIF\nTéléphone : 01 00 00 00 00\nMail : fictif@example.com' });
    const resultat = await c.agenda().modifierRendezVous(evenement.id, { heure: '14:30' });
    const description = '14h30 – Notes FICTIF\nTéléphone : 01 00 00 00 00\nMail : fictif@example.com';
    attendreEgal(c.requetes.find(r => r.methode === 'PATCH').corps, { description }, 'uniquement la description');
    attendreEgal(resultat, { id: evenement.id, titre: evenement.summary, date: '2030-01-10', heure: '14:30', heure_fin: '',
      journee_entiere: true, lieu: evenement.location, notes: 'Notes FICTIF', telephone: '01 00 00 00 00',
      mail: 'fictif@example.com', rappels: [60], description }, 'journée entière toujours entière');
  });

  await testAsync('Google Agenda fiche : déplacement journée entière préserve durée multijour', async c => {
    const evenement = preparerFicheRendezVous(c, { start: { date: '2030-01-10' }, end: { date: '2030-01-13' },
      description: '09h05 – Notes FICTIF' });
    const resultat = await c.agenda().modifierRendezVous(evenement.id, { date: '2030-03-30' });
    attendreEgal(c.requetes.find(r => r.methode === 'PATCH').corps,
      { start: { date: '2030-03-30' }, end: { date: '2030-04-02' } }, 'trois jours civils, fin exclusive');
    attendreEgal([resultat.date, resultat.heure, resultat.journee_entiere], ['2030-03-30', '09:05', true], 'horaire descriptif conservé');
  });

  for (const etat of ['hors ligne', 'déconnecté']) {
    await testAsync(`Google Agenda fiche : ${etat} refuse sans requête`, async c => {
      preparerFicheRendezVous(c);
      if (etat === 'hors ligne') c.navigator.onLine = false;
      else c.googleConnexion.connecte = () => false;
      await attendreRejet(() => c.agenda().modifierRendezVous('rdv-fictif', { titre: 'Refusé FICTIF' }), 'connecté à Google');
      attendreEgal(c.requetes.length, 0, 'aucune requête');
      attendreEgal(c.localStorage.getItem('cap_rdv_historique_v1'), null, 'aucune sauvegarde inutile');
    });
  }

  const nouveauRdv = { titre: 'test notification FICTIF', date: '2030-01-10', heure: '11:45', heure_fin: '12:45',
    lieu: '', telephone: '', mail: '', notes: '', rappels: [10] };

  await testAsync('Google Agenda création : POST sur l’agenda FICTIF avec rappel popup', async c => {
    preparerFicheRendezVous(c);
    const repondre = c.repondre;
    let envoye = null;
    c.repondre = async r => {
      if (r.methode === 'POST') {
        attendreEgal(r.url.pathname, '/calendar/v3/calendars/agenda-fictif/events', 'agenda FICTIF seulement');
        envoye = r.corps;
        return reponseGoogle({ id: 'nouveau-fictif', ...r.corps,
          start: { dateTime: '2030-01-10T11:45:00+01:00' }, end: { dateTime: '2030-01-10T12:45:00+01:00' } });
      }
      return repondre(r);
    };
    const resultat = await c.agenda().creerRendezVous(nouveauRdv);
    attendre(envoye, 'aucun POST');
    attendreEgal(envoye.summary, 'test notification FICTIF', 'titre envoyé');
    attendreEgal(envoye.start, { dateTime: '2030-01-10T11:45:00', timeZone: 'Europe/Paris' }, 'début');
    attendreEgal(envoye.end, { dateTime: '2030-01-10T12:45:00', timeZone: 'Europe/Paris' }, 'fin');
    attendreEgal(envoye.reminders, { useDefault: false, overrides: [{ method: 'popup', minutes: 10 }] }, 'rappel');
    attendreEgal([resultat.id, resultat.date, resultat.heure, resultat.rappels], ['nouveau-fictif', '2030-01-10', '11:45', [10]], 'résultat');
    attendre(c.agenda().lireCache().some(rdv => rdv.id === 'nouveau-fictif'), 'cache mis à jour');
    attendre(c.requetes.every(r => !['DELETE', 'PATCH', 'PUT'].includes(r.methode)), 'aucune autre écriture');
  });

  for (const etat of ['hors ligne', 'déconnecté', 'principal', 'fin avant début']) {
    await testAsync(`Google Agenda création : refus ${etat} sans POST`, async c => {
      preparerFicheRendezVous(c);
      let champs = nouveauRdv;
      if (etat === 'hors ligne') c.navigator.onLine = false;
      if (etat === 'déconnecté') c.googleConnexion.connecte = () => false;
      if (etat === 'fin avant début') champs = { ...nouveauRdv, heure_fin: '11:00' };
      if (etat === 'principal') {
        c.repondre = async r => {
          attendreEgal(r.methode, 'GET', 'lecture seulement');
          return reponseGoogle({ id: c.agendaModifiable, summary: REGLAGES_GOOGLE.nom_agenda, primary: true });
        };
      }
      await attendreRejet(() => c.agenda().creerRendezVous(champs), '');
      attendre(c.requetes.every(r => r.methode !== 'POST'), 'aucun POST');
    });
  }

  test('Compréhension : la phrase de Max donne un rendez-vous à 11h45 aujourd’hui', () => {
    const maintenant = new Date(2026, 9, 29, 10, 0);
    const rdv = comprendreDemande.rendezVous('Ajoute-moi un rendez-vous à 11h45 aujourd\'hui, intitulé test notification, avec un rappel dix minutes avant', maintenant);
    attendreEgal([rdv.titre, rdv.date, rdv.heure, rdv.heure_fin, rdv.rappels], ['test notification', '2026-10-29', '11:45', '12:45', [10]], 'brouillon');
  });

  test('Compréhension : dates, heures, rappels et refus', () => {
    const maintenant = new Date(2026, 9, 29, 10, 0);
    const cas = [
      ['rendez-vous demain à midi chez le garagiste FICTIF', '2026-10-30', '12:00', []],
      ['rdv le 12 novembre à 9 heures et demie, rappel une demi-heure avant', '2026-11-12', '09:30', [30]],
      ['rendez-vous lundi 14h garage FICTIF avec un rappel la veille', '2026-11-02', '14:00', [1440]],
      ['rendez-vous le 3/02 à 8h05', '2027-02-03', '08:05', []]
    ];
    for (const [phrase, date, heure, rappels] of cas) {
      const rdv = comprendreDemande.rendezVous(phrase, maintenant);
      attendreEgal([rdv.date, rdv.heure, rdv.rappels], [date, heure, rappels], phrase);
    }
    attendreEgal(comprendreDemande.rendezVous('acheter du pain FICTIF', maintenant), null, 'pas de rendez-vous');
    attendreEgal(comprendreDemande.rendezVous('reporte le rendez-vous à demain', maintenant), null, 'report exclu');
    attendreEgal(comprendreDemande.report('Reporte ça à demain'), { cible: 'tache' }, 'report tâche');
    attendreEgal(comprendreDemande.report('décale le rendez-vous à demain'), { cible: 'rendez-vous' }, 'report rdv');
    attendreEgal(comprendreDemande.report('reporte à après-demain'), null, 'après-demain non géré');
  });

  const modificationsRdvInvalides = [
    ['titre vide', { titre: '' }, 'titre'], ['titre blanc', { titre: '   ' }, 'titre'],
    ['date impossible', { date: '2030-02-30' }, 'date'], ['date mois invalide', { date: '2030-13-01' }, 'date'],
    ['date format court', { date: '2030-1-01' }, 'date'], ['date vide', { date: '' }, 'date'],
    ['mail invalide', { mail: 'adresse-fictive' }, 'mail'],
    ['mail multiligne', { mail: 'fictif@example.com\nCopie : autre.fictif@example.com' }, 'mail'],
    ['téléphone multiligne', { telephone: '01 00 00 00 00\nMail : fictif@example.com' }, 'ligne'],
    ['heure invalide', { heure: '24:00' }, 'heure'], ['minutes invalides', { heure: '12:60' }, 'heure'],
    ['heure format court', { heure: '9:05' }, 'heure'], ['fin invalide', { heure_fin: '25:00' }, 'heure'],
    ['rappels négatifs', { rappels: [-1] }, 'rappels'], ['rappels au-delà limite', { rappels: [40321] }, 'rappels'],
    ['rappels décimaux', { rappels: [0.5] }, 'rappels'], ['rappels texte', { rappels: ['60'] }, 'rappels'],
    ['rappels pas liste', { rappels: 60 }, 'rappels'], ['six rappels', { rappels: [0, 1, 2, 3, 4, 5] }, 'rappels'],
    ['champ interdit', { summary: 'FICTIF' }, 'autorisée'], ['titre non texte', { titre: 42 }, 'invalide']
  ];
  for (const [nom, changements, message] of modificationsRdvInvalides) {
    await testAsync(`Google Agenda fiche : validation ${nom} sans requête`, async c => {
      preparerFicheRendezVous(c);
      await attendreRejet(() => c.agenda().modifierRendezVous('rdv-fictif', changements), message);
      attendreEgal(c.requetes.length, 0, 'validation avant tout accès Google');
      attendreEgal(c.localStorage.getItem('cap_rdv_historique_v1'), null, 'aucune sauvegarde de modification invalide');
    });
  }

  for (const changements of [{ heure: '' }, { heure_fin: '' }, { heure: '11:00', heure_fin: '11:00' },
    { heure: '12:00', heure_fin: '11:00' }]) {
    await testAsync(`Google Agenda fiche : plage horaire incohérente ${JSON.stringify(changements)}`, async c => {
      preparerFicheRendezVous(c);
      await attendreRejet(() => c.agenda().modifierRendezVous('rdv-fictif', changements), 'heure');
      attendre(c.requetes.every(r => r.methode === 'GET'), 'aucune écriture avec plage invalide');
      attendreEgal(c.localStorage.getItem('cap_rdv_historique_v1'), null, 'pas de sauvegarde inutile');
    });
  }

  await testAsync('Google Agenda fiche : heure de fin interdite pour une journée entière', async c => {
    preparerFicheRendezVous(c, { start: { date: '2030-01-10' }, end: { date: '2030-01-11' } });
    await attendreRejet(() => c.agenda().modifierRendezVous('rdv-fictif', { heure_fin: '15:00' }), 'journée entière');
    attendre(c.requetes.every(r => r.methode === 'GET'), 'aucun PATCH');
    attendreEgal(c.localStorage.getItem('cap_rdv_historique_v1'), null, 'historique inchangé');
  });

  for (const statut of [412, 500]) {
    await testAsync(`Google Agenda fiche : erreur PATCH ${statut} garde ancienne version et cache intact`, async c => {
      const evenement = preparerFicheRendezVous(c);
      const agenda = c.agenda();
      await agenda.prochainsRendezVous();
      const cache = c.localStorage.getItem('cap_google_rendezvous_v1');
      const repondre = c.repondre;
      c.repondre = async r => r.methode === 'PATCH' ? reponseGoogle({ erreur: 'Échec FICTIF' }, statut) : repondre(r);
      await attendreRejet(() => agenda.modifierRendezVous(evenement.id, { titre: 'Échec FICTIF' }), String(statut));
      attendreEgal(agenda.lireHistorique().length, 1, 'ancienne version toujours disponible');
      attendreEgal(agenda.lireHistorique()[0].ancien, ancienRendezVous(evenement), 'sauvegarde complète après erreur');
      attendreEgal(c.localStorage.getItem('cap_google_rendezvous_v1'), cache, 'cache strictement inchangé');
      attendreEgal(c.requetes.filter(r => r.methode === 'PATCH').length, 1, 'pas de répétition de modification');
    });
  }

  await testAsync('Google et service worker : aucune interception ni cache hors origine', async c => {
    const rappels = new Map();
    const origine = location.origin;
    const fauxSelf = { registration: { scope: `${origine}/src/` }, location: { origin: origine },
      addEventListener: (nom, rappel) => rappels.set(nom, rappel) };
    let cachesOuverts = 0;
    objetIsole(SOURCE_SERVICE_WORKER, 'undefined', { self: fauxSelf,
      caches: { open: async () => { cachesOuverts++; throw new Error('Cache inattendu'); } }, fetch: c.fetch });
    const intercepter = rappels.get('fetch');
    attendre(typeof intercepter === 'function', 'gestionnaire fetch absent');
    let interceptions = 0;
    for (const url of ['https://www.googleapis.com/calendar/v3/calendars',
      'https://sheets.googleapis.com/v4/spreadsheets', `${origine}/hors-precache-fictif`]) {
      intercepter({ request: new Request(url), respondWith: () => interceptions++ });
    }
    intercepter({ request: new Request(`${origine}/src/app.js`, { method: 'POST', body: 'FICTIF' }), respondWith: () => interceptions++ });
    attendreEgal(interceptions, 0, 'requêtes Google ou non précachées ignorées');
    attendreEgal(cachesOuverts, 0, 'cache non ouvert');
    attendreEgal(c.requetes.length, 0, 'aucun fetch du service worker');
  });

  async function viderMicrotaches() {
    for (let i = 0; i < 40; i++) await Promise.resolve();
  }

  function preparerConnexion(c, duree = 3600000) {
    c.localStorage.setItem('cap_google_deja_connecte_v1', 'oui');
    c.localStorage.setItem('cap_google_jeton_v1', JSON.stringify({
      jeton: 'jeton-fictif', expiration: c.maintenant + duree
    }));
    c.googleConnexion = c.connexion();
  }

  function interfaceIsolee(c, { largeur = 1024, hauteur = 768, avant = () => {} } = {}) {
    const cadre = document.createElement('iframe');
    cadre.style.cssText = `position:fixed;left:0;top:0;width:${largeur}px;height:${hauteur}px;border:0;`;
    document.body.append(cadre);
    c.cadres.push(cadre);
    const doc = cadre.contentDocument;
    const modele = new DOMParser().parseFromString(SOURCE_HTML, 'text/html');
    modele.querySelectorAll('script').forEach(script => script.remove());
    doc.documentElement.lang = 'fr';
    doc.body.replaceChildren(...Array.from(modele.body.childNodes, noeud => doc.importNode(noeud, true)));
    const style = doc.createElement('style');
    style.textContent = SOURCE_STYLE;
    doc.head.append(style);
    const vibrations = [];
    c.navigator.vibrate = duree => { vibrations.push(duree); return true; };
    let cache = false;
    Object.defineProperty(doc, 'hidden', { configurable: true, get: () => cache });
    const dicteeSimulee = { disponible: () => false, enCours: () => false };
    const ui = {
      doc, cadre, vibrations, dictee: dicteeSimulee,
      parId: id => doc.getElementById(id),
      visibilite(masque) {
        cache = masque;
        doc.dispatchEvent(new Event('visibilitychange'));
      },
      actualiser: () => c.window.dispatchEvent(new Event('cap-google-etat'))
    };
    avant(ui);
    const agendaSimule = { prochainsRendezVous: async () => [], lireCache: () => c.agenda().lireCache() };
    const etapesIsolees = JSON.parse(JSON.stringify(ETAPES_PAR_DEFAUT));
    ui.listesChoix = objetIsole(SOURCE_LISTES_CHOIX, 'listesChoix', {
      localStorage: c.localStorage, window: c.window, TACHES: c.TACHES, ETAPES_PAR_DEFAUT: etapesIsolees, dateDuJour
    });
    ui.choixDates = objetIsole(SOURCE_CHOIX_DATES, 'choixDates', {
      document: doc, Date: c.Date, comprendreDemande, dictee: ui.dictee
    });
    ui.fermetureFenetres = objetIsole(SOURCE_FERMETURE_FENETRES, 'fermetureFenetres', {
      document: doc, setTimeout: c.setTimeout, clearTimeout: c.clearTimeout, CSS, Event
    });
    ui.fenetresListes = objetIsole(SOURCE_FENETRES_LISTES, 'fenetresListes', {
      document: doc, listesChoix: ui.listesChoix, setTimeout: c.setTimeout, clearTimeout: c.clearTimeout,
      fermetureFenetres: ui.fermetureFenetres
    });
    ui.etapesParDefaut = etapesIsolees;
    ui.journalActions = objetIsole(SOURCE_JOURNAL_ACTIONS, 'journalActions', { localStorage: c.localStorage, googleSheets: undefined });
    ui.classer = (id, categorie, sousCategorie) => {
      const tache = c.TACHES.find(item => item.id === id);
      const ancienne = { categorie: tache.categorie, sous_categorie: tache.sous_categorie };
      tache.categorie = categorie;
      tache.sous_categorie = sousCategorie;
      return ancienne;
    };
    ui.tuiles = objetIsole(SOURCE_TUILES, 'tuiles', { document: doc, navigator: c.navigator, setTimeout, clearTimeout });
    ui.modeTrier = objetIsole(SOURCE_MODE_TRIER, 'modeTrier', {
      document: doc, TACHES: c.TACHES, listesChoix: ui.listesChoix, classer: ui.classer, dictee: ui.dictee,
      journalActions: ui.journalActions, setTimeout: c.setTimeout, clearTimeout: c.clearTimeout
    });
    ui.sauvegardes = [];
    ui.sauvegardeDrive = {
      etat: () => ({ derniere: '', dossier: '', nombre: 0 }),
      sauvegarder: async () => { ui.sauvegardes.push(1); return { nom: 'Cap – FICTIF – sauvegarde', nombre: 1, enTrop: 0 }; },
      verifierAutomatique: async () => null, aFaire: () => false
    };
    objetIsole(SOURCE_APP, 'undefined', {
      document: doc, window: c.window, navigator: c.navigator, Date: c.Date,
      setInterval: c.setInterval, setTimeout: c.setTimeout, clearTimeout: c.clearTimeout,
      googleConnexion: c.googleConnexion, synchronisation: c.synchronisation,
      recherche,
      ficheRendezVous: objetIsole(SOURCE_FICHE_RDV, 'ficheRendezVous', {
        document: doc, navigator: c.navigator, googleConnexion: c.googleConnexion, googleAgenda: agendaSimule
      }),
      journalActions: ui.journalActions,
      tuiles: ui.tuiles, modeTrier: ui.modeTrier, sauvegardeDrive: ui.sauvegardeDrive, REGLAGES_GOOGLE,
      googleAgenda: agendaSimule,
      TACHES: c.TACHES, INFO_CHARGEMENT: '', ETAPES_PAR_DEFAUT: etapesIsolees,
      listesChoix: ui.listesChoix, choixDates: ui.choixDates, fenetresListes: ui.fenetresListes, fermetureFenetres: ui.fermetureFenetres,
      avancementTache: () => ({ faites: 0, total: 0 }), avancementSousCategorie: () => 0,
      joursRestants, dateDuJour, ajouterEtape, abandonner, remettre, cocher,
      reporterADemain, changerEcheance, creerAvecEtapesParDefaut, creerTache, traiterDemande, composerTexte,
      preferencesClavier, PHRASES_CLAVIER, dictee: dicteeSimulee
    });
    return ui;
  }

  function preparerInterface(c, options) {
    c.googleConnexion = c.connexion();
    c.synchronisation = c.sync(fauxSheetsSync(c, c.TACHES));
    return interfaceIsolee(c, options);
  }

  function glisser(ui, cible, x, y, finX, finY) {
    for (const [type, touches, changedTouches] of [
      ['touchstart', [{ clientX: x, clientY: y }], []],
      ['touchend', [], [{ clientX: finX, clientY: finY }]]
    ]) {
      const evenement = new Event(type, { bubbles: true });
      Object.defineProperties(evenement, { touches: { value: touches }, changedTouches: { value: changedTouches } });
      cible.dispatchEvent(evenement);
    }
  }

  for (const code of ['interaction_required', 'login_required', 'consent_required', 'account_selection_required']) {
    await testAsync(`Google silencieux : ${code} demande un geste et affiche l’alerte`, async c => {
      c.localStorage.setItem('cap_google_deja_connecte_v1', 'oui');
      const connexion = c.connexion();
      attendre(connexion.tenterSilencieux(true), 'tentative silencieuse absente');
      const etat = c.redirections[0].searchParams.get('state');
      attendreEgal(c.localStorage.getItem('cap_google_etat_silencieux_v1'), etat, 'marqueur lié au state');
      c.location.hash = `#error=${code}&state=${etat}`;
      const ui = preparerInterface(c);
      attendre(c.googleConnexion.besoinGeste(), 'accord non demandé');
      attendreEgal(c.localStorage.getItem('cap_google_besoin_geste_v1'), 'oui', 'geste persistant');
      attendre(!ui.parId('alerte-google').hidden, 'alerte cachée');
      attendre(ui.parId('texte-alerte-google').textContent.includes('Google demande ton accord'), 'message d’accord absent');
      attendreEgal(c.localStorage.getItem('cap_google_etat_silencieux_v1'), null, 'marqueur consommé');
      attendreEgal(c.redirections.length, 1, 'aucune boucle silencieuse');
      c.maintenant += 700000;
      attendre(!c.googleConnexion.tenterSilencieux(true), 'nouvelle tentative malgré le geste requis');
      const recharge = c.connexion();
      attendre(recharge.besoinGeste(), 'geste perdu au rechargement');
    });
  }

  await testAsync('Google silencieux : access_denied reste un refus sans boucle', async c => {
    c.localStorage.setItem('cap_google_deja_connecte_v1', 'oui');
    c.connexion().seConnecter({ silencieux: true });
    const etat = c.redirections[0].searchParams.get('state');
    c.location.hash = `#error=access_denied&state=${etat}`;
    const ui = preparerInterface(c);
    attendre(!c.googleConnexion.connecte(), 'refus accepté');
    attendre(!c.googleConnexion.besoinGeste(), 'refus confondu avec interaction requise');
    attendre(c.googleConnexion.message().includes('pas été autorisée'), 'message de refus absent');
    attendre(!ui.parId('alerte-google').hidden, 'refus non affiché');
    attendre(!c.googleConnexion.tenterSilencieux(true), 'boucle après refus');
    attendreEgal(c.localStorage.getItem('cap_google_jeton_v1'), null, 'jeton après refus');
  });

  await testAsync('Google silencieux : marqueur seul et mauvais state ne contournent pas la sécurité', async c => {
    c.localStorage.setItem('cap_google_etat_v1', 'attendu-fictif');
    c.localStorage.setItem('cap_google_etat_silencieux_v1', 'intrus-fictif');
    c.location.hash = '#error=interaction_required&state=intrus-fictif';
    const ui = preparerInterface(c);
    attendre(c.googleConnexion.message().includes('sécurité'), 'mauvais state accepté');
    attendre(!c.googleConnexion.besoinGeste(), 'erreur de sécurité transformée en demande d’accord');
    attendre(!c.googleConnexion.connecte(), 'connexion acceptée');
    attendre(!ui.parId('alerte-google').hidden, 'erreur non affichée');
    attendreEgal(c.location.hash, '', 'fragment nettoyé');
    attendreEgal(c.redirections.length, 0, 'aucune redirection après erreur');
  });

  await testAsync('Google silencieux : erreur interactive non liée au marqueur reste un refus', async c => {
    c.localStorage.setItem('cap_google_etat_v1', 'attendu-fictif');
    c.localStorage.setItem('cap_google_etat_silencieux_v1', 'autre-fictif');
    c.location.hash = '#error=consent_required&state=attendu-fictif';
    const connexion = c.connexion();
    attendre(!connexion.besoinGeste(), 'marqueur sans rapport accepté');
    attendre(connexion.message().includes('pas été autorisée'), 'refus absent');
  });

  await testAsync('Google silencieux : throttle dix minutes, prompt none et horodatage', async c => {
    c.localStorage.setItem('cap_google_deja_connecte_v1', 'oui');
    const connexion = c.connexion();
    attendre(connexion.tenterSilencieux(true), 'première tentative absente');
    attendreEgal(c.redirections[0].searchParams.get('prompt'), 'none', 'prompt silencieux');
    attendreEgal(Number(c.localStorage.getItem('cap_google_silencieux_v1')), c.maintenant, 'date de tentative');
    attendre(!connexion.tenterSilencieux(true), 'tentative immédiate répétée');
    c.maintenant += 600000;
    attendre(!connexion.tenterSilencieux(true), 'tentative à dix minutes exactement');
    c.maintenant++;
    attendre(connexion.tenterSilencieux(true), 'pas de reprise après dix minutes');
    attendreEgal(c.redirections.length, 2, 'nombre de redirections');
    attendre(c.redirections[0].searchParams.get('state') !== c.redirections[1].searchParams.get('state'), 'state réutilisé');
  });

  for (const cas of ['jamais connecté', 'hors ligne', 'jeton supérieur à cinq minutes', 'conditions refusées']) {
    await testAsync(`Google silencieux : aucune tentative si ${cas}`, async c => {
      if (cas !== 'jamais connecté') c.localStorage.setItem('cap_google_deja_connecte_v1', 'oui');
      if (cas === 'hors ligne') c.navigator.onLine = false;
      if (cas === 'jeton supérieur à cinq minutes') preparerConnexion(c, 300001);
      const connexion = c.connexion();
      attendre(!connexion.tenterSilencieux(cas !== 'conditions refusées'), 'tentative indésirable');
      attendreEgal(c.redirections.length, 0, 'redirection indésirable');
      attendreEgal(c.localStorage.getItem('cap_google_silencieux_v1'), null, 'throttle consommé sans tentative');
    });
  }

  for (const cas of ['dialogue', 'dictée', 'texte', 'page cachée']) {
    await testAsync(`Interface Google : aucune reconnexion silencieuse pendant ${cas}`, async c => {
      c.localStorage.setItem('cap_google_deja_connecte_v1', 'oui');
      const ui = preparerInterface(c, { avant(ui) {
        if (cas === 'dialogue') ui.parId('clavier').showModal();
        if (cas === 'dictée') ui.dictee.enCours = () => true;
        if (cas === 'texte') ui.parId('saisie-demande').value = 'Demande FICTIF en cours';
        if (cas === 'page cachée') ui.visibilite(true);
      } });
      attendreEgal(c.redirections.length, 0, 'redirection au démarrage');
      if (cas !== 'page cachée') ui.visibilite(false);
      attendreEgal(c.redirections.length, 0, 'redirection au retour visible');
      if (cas === 'dialogue') ui.parId('clavier').close();
      if (cas === 'dictée') ui.dictee.enCours = () => false;
      if (cas === 'texte') ui.parId('saisie-demande').value = '';
      ui.visibilite(false);
      attendreEgal(c.redirections.length, 1, 'reprise une fois l’interface libre');
      attendreEgal(c.redirections[0].searchParams.get('prompt'), 'none', 'reprise silencieuse');
    });
  }

  await testAsync('Interface Google : expiration, nombre en attente et une seule vibration', async c => {
    preparerConnexion(c, 120000);
    c.localStorage.setItem('cap_google_silencieux_v1', String(c.maintenant));
    const sheets = fauxSheetsSync(c, c.TACHES);
    c.synchronisation = c.sync(sheets);
    const ui = interfaceIsolee(c);
    await viderMicrotaches();
    attendre(ui.parId('alerte-google').hidden, 'alerte avant expiration');
    c.navigator.onLine = false;
    c.synchronisation.signaler(c.TACHES.slice(0, 2).map(t => t.id));
    const expiration = c.googleConnexion.expiration();
    attendreEgal(expiration, c.maintenant + 120000, 'expiration exposée');
    const minuterie = Array.from(c.delais.values()).find(delai => delai.delai === 60001);
    attendre(minuterie, 'minuteur d’expiration absent');
    c.maintenant = expiration - 59999;
    minuterie.rappel();
    attendre(!ui.parId('alerte-google').hidden, 'alerte après expiration');
    attendre(ui.parId('texte-alerte-google').textContent.includes('2 tâches attendent'), 'mauvais nombre dans l’alerte');
    attendre(ui.parId('texte-etat-google').textContent.includes('2 en attente'), 'nombre hors ligne absent');
    ui.actualiser();
    ui.visibilite(false);
    attendreEgal(ui.vibrations, [200], 'vibration répétée');
    attendreEgal(lireFileGoogle(c).length, 2, 'file perdue à l’expiration');
    ui.parId('redonner-acces-google').click();
    attendreEgal(c.redirections.length, 1, 'bouton sans redirection');
    attendre(!c.redirections[0].searchParams.has('prompt'), 'bouton encore silencieux');
    attendreEgal(c.localStorage.getItem('cap_google_etat_silencieux_v1'), null, 'marqueur silencieux après clic');
  });

  await testAsync('Interface Google : retour OAuth valide démarre et envoie automatiquement la file', async c => {
    c.localStorage.setItem('cap_google_etat_v1', 'retour-fictif');
    c.localStorage.setItem('cap_google_etat_silencieux_v1', 'retour-fictif');
    c.localStorage.setItem('cap_google_besoin_geste_v1', 'oui');
    c.localStorage.setItem('cap_google_file_v1', JSON.stringify([c.TACHES[0].id]));
    c.location.hash = '#access_token=jeton-fictif&expires_in=3600&token_type=Bearer&state=retour-fictif';
    c.googleConnexion = c.connexion();
    const sheets = fauxSheetsSync(c, c.TACHES);
    c.synchronisation = c.sync(sheets);
    const ui = interfaceIsolee(c);
    attendre(ui.parId('synchroniser-maintenant').disabled, 'bouton actif pendant le démarrage');
    await viderMicrotaches();
    attendreEgal(sheets.envois.flat().map(t => t.id), [c.TACHES[0].id], 'file non envoyée par le démarrage de l’app');
    attendreEgal(lireFileGoogle(c), [], 'file non acquittée');
    attendre(!c.googleConnexion.besoinGeste(), 'geste non réinitialisé');
    attendre(ui.parId('alerte-google').hidden, 'alerte après retour valide');
    attendreEgal(c.redirections.length, 0, 'redirection supplémentaire');
    attendreEgal(c.localStorage.getItem('cap_google_etat_silencieux_v1'), null, 'marqueur non consommé');
  });

  await testAsync('Interface Google : 403 retire le jeton, affiche l’alerte et garde la file', async c => {
    preparerConnexion(c);
    const sheets = fauxSheetsSync(c, c.TACHES);
    c.synchronisation = c.sync(sheets);
    const ui = interfaceIsolee(c);
    await viderMicrotaches();
    c.navigator.onLine = false;
    c.synchronisation.signaler([c.TACHES[0].id, c.TACHES[1].id]);
    c.navigator.onLine = true;
    c.repondre = async () => reponseGoogle({}, 403);
    sheets.ecrireTaches = async () => c.googleConnexion.appeler('https://sheets.googleapis.com/v4/spreadsheets/tableau-fictif');
    let evenements = 0;
    c.window.addEventListener('cap-google-deconnecte', () => evenements++);
    ui.parId('basculer-vue').click();
    ui.parId('synchroniser-maintenant').click();
    // La raison du refus est lue dans la réponse de Google avant de décider : une attente de plus.
    for (let essai = 0; essai < 50 && evenements < 1; essai++) await new Promise(resoudre => setTimeout(resoudre, 10));
    await viderMicrotaches();
    attendreEgal(evenements, 1, 'événement de déconnexion absent');
    attendreEgal(c.localStorage.getItem('cap_google_jeton_v1'), null, 'jeton non retiré');
    attendreEgal(lireFileGoogle(c), c.TACHES.slice(0, 2).map(t => t.id), 'file modifiée après 403');
    attendre(!ui.parId('alerte-google').hidden, 'alerte absente');
    attendre(ui.parId('texte-alerte-google').textContent.includes('403'), 'raison 403 absente');
    attendre(ui.parId('texte-alerte-google').textContent.includes('2 tâches attendent'), 'nombre incorrect');
    attendre(!c.synchronisation.informations().pret, 'sync encore prête après déconnexion');
    attendreEgal(c.localStorage.getItem('cap_google_dernier_envoi_v1'), null, 'succès inventé après 403');
    attendreEgal(ui.vibrations, [200], 'vibration de déconnexion');
  });

  await testAsync('Interface Google : synchronisation manuelle, verrou, heure du dernier succès', async c => {
    preparerConnexion(c);
    const sheets = fauxSheetsSync(c, c.TACHES);
    c.synchronisation = c.sync(sheets);
    const ui = interfaceIsolee(c);
    await viderMicrotaches();
    attendreEgal(c.synchronisation.informations(), {
      nombre: 0, pret: true, enCours: false, dernierEnvoi: 0, erreur: '', illisibles: 0
    }, 'informations au repos');
    c.navigator.onLine = false;
    c.synchronisation.signaler([c.TACHES[0].id]);
    c.navigator.onLine = true;
    let terminer;
    sheets.ecrireTaches = taches => new Promise(resolve => {
      terminer = () => resolve(taches.map(t => t.id));
    });
    ui.parId('basculer-vue').click();
    const bouton = ui.parId('synchroniser-maintenant');
    bouton.click();
    attendre(c.synchronisation.informations().enCours, 'verrou absent');
    attendre(bouton.disabled && bouton.textContent === 'Envoi…', 'bouton non désactivé');
    await viderMicrotaches();
    attendre(typeof terminer === 'function', 'envoi non lancé');
    attendreEgal(c.localStorage.getItem('cap_google_dernier_envoi_v1'), null, 'succès avant réponse');
    c.maintenant += 45000;
    terminer();
    await viderMicrotaches();
    attendreEgal(Number(c.localStorage.getItem('cap_google_dernier_envoi_v1')), c.maintenant, 'heure de succès non sauvegardée');
    attendreEgal(c.synchronisation.informations().dernierEnvoi, c.maintenant, 'heure non exposée');
    const heure = new Intl.DateTimeFormat('fr-FR', { hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).format(new Date(c.maintenant));
    attendreEgal(ui.parId('dernier-envoi').textContent, `Dernier envoi réussi : ${heure}`, 'heure affichée');
    attendre(!bouton.disabled, 'bouton bloqué après succès');
    attendreEgal(ui.parId('texte-etat-google').textContent, 'Tout est envoyé', 'état final');
  });

  await testAsync('Google sync : reprise périodique à soixante secondes, sans réseau hors ligne', async c => {
    preparerConnexion(c);
    const sheets = fauxSheetsSync(c, c.TACHES);
    const sync = c.sync(sheets);
    await sync.demarrer();
    c.navigator.onLine = false;
    sync.signaler([c.TACHES[0].id]);
    const rappels = c.intervalles.filter(intervalle => intervalle.delai === 60000);
    attendreEgal(rappels.length, 1, 'intervalle de reprise');
    rappels[0].rappel();
    await viderMicrotaches();
    attendreEgal(sheets.envois.length, 0, 'envoi hors ligne');
    c.navigator.onLine = true;
    rappels[0].rappel();
    await viderMicrotaches();
    attendreEgal(sheets.envois.flat().map(t => t.id), [c.TACHES[0].id], 'reprise périodique absente');
    attendreEgal(lireFileGoogle(c), [], 'file non acquittée');
  });

  await testAsync('Interface Google : reprise de la file au retour visible seulement', async c => {
    preparerConnexion(c);
    const sheets = fauxSheetsSync(c, c.TACHES);
    c.synchronisation = c.sync(sheets);
    const ui = interfaceIsolee(c);
    await viderMicrotaches();
    c.navigator.onLine = false;
    c.synchronisation.signaler([c.TACHES[0].id]);
    c.navigator.onLine = true;
    ui.visibilite(true);
    await viderMicrotaches();
    attendreEgal(sheets.envois.length, 0, 'reprise lors du masquage');
    ui.visibilite(false);
    await viderMicrotaches();
    attendreEgal(sheets.envois.flat().map(t => t.id), [c.TACHES[0].id], 'reprise au retour visible absente');
    attendreEgal(lireFileGoogle(c), [], 'file non acquittée');
  });

  await testAsync('Interface Google : première connexion, alerte vide et aucun renouvellement par minuteur', async c => {
    const ui = preparerInterface(c);
    attendre(ui.parId('alerte-google').hidden, 'alerte avant toute connexion');
    attendre(!ui.parId('connexion-google').hidden, 'première connexion indisponible');
    c.googleConnexion.deconnecter();
    ui.actualiser();
    attendre(!ui.parId('alerte-google').hidden, 'alerte sans jeton absente');
    attendre(ui.parId('texte-alerte-google').textContent.includes('Rien n’est perdu.'), 'message pour file vide absent');
    attendre(ui.parId('connexion-google').hidden, 'première connexion encore affichée');
    attendre(ui.parId('synchroniser-maintenant').hidden, 'envoi proposé sans accès');
    const surveillance = c.intervalles.find(intervalle => intervalle.delai === 30000);
    attendre(surveillance, 'surveillance toutes les trente secondes absente');
    c.maintenant += 700000;
    surveillance.rappel();
    surveillance.rappel();
    attendreEgal(c.redirections.length, 0, 'renouvellement déclenché par un minuteur');
    attendreEgal(ui.vibrations, [200], 'vibration répétée avec une file vide');
    attendre(c.connexion().reconnexion(), 'connexion passée oubliée au rechargement');
  });

  await testAsync('Accueil : liste cachée et inerte, horloge et commandes visibles', async c => {
    const ui = preparerInterface(c);
    attendre(ui.parId('ecran-complet').hidden && ui.parId('ecran-complet').inert, 'liste initialement accessible');
    attendre(!ui.parId('accueil').hidden, 'accueil caché');
    attendreEgal(ui.parId('basculer-vue').getAttribute('aria-expanded'), 'false', 'état du bouton');
    for (const cible of [ui.doc.querySelector('header.horloge'), ui.doc.querySelector('footer.dictee'), ui.parId('microphone')]) { // 09/11/2026 : le gros micro est de retour sur l'accueil // 08/11/2026 (étape 2) : le micro de l'accueil est « ouvrir-micro » (avant : « microphone », déplacé dans l'écran Micro)
      const rectangle = cible.getBoundingClientRect();
      attendre(rectangle.width > 0 && rectangle.height > 0, 'horloge ou commandes invisibles');
      attendre(rectangle.top >= 0 && rectangle.bottom <= ui.cadre.clientHeight + 1, 'horloge ou commandes hors écran');
    }
    attendre(ui.parId('date').textContent.length > 0, 'date vide');
    attendre(!ui.parId('heure'), 'heure encore affichée');
    // Étape A : accueil = 3 boutons en colonne (Micro, Chercher, Autre) ; la barre de recherche est dans « Chercher ».
    // 09/11/2026 (étape 2) : Chercher en haut, gros micro au milieu, Autre en bas. Avant : Micro, Chercher, Autre.
    const colonne = ['ouvrir-chercher', 'microphone', 'ouvrir-autre'].map(id => ui.parId(id).getBoundingClientRect());
    attendre(colonne.every(r => r.width >= 48 && r.height >= 48 && r.top >= 0 && r.bottom <= ui.cadre.clientHeight + 1), 'boutons de l’accueil hors écran ou trop petits');
    attendre(colonne[0].bottom <= colonne[1].top && colonne[1].bottom <= colonne[2].top, 'boutons de l’accueil pas en colonne (Chercher, micro, Autre)');
    attendre(ui.parId('zone-recherche').hidden && ui.parId('zone-recherche').getBoundingClientRect().height === 0, 'barre de recherche encore sur l’accueil');
    attendre(ui.doc.querySelector('.choix-source').contains(ui.parId('source-recherche')), 'menu hors de la barre');
    ui.parId('basculer-vue').click();
    const barreChercher = ui.doc.querySelector('.barre-recherche').getBoundingClientRect();
    attendre(!ui.parId('zone-recherche').hidden && barreChercher.height > 0 && barreChercher.bottom <= ui.cadre.clientHeight + 1, 'barre de recherche absente de « Chercher »');
    attendre(!ui.parId('ecran-complet').hidden && !ui.parId('ecran-complet').inert, 'vue complète non ouverte');
    attendre(ui.parId('accueil').hidden, 'accueil encore visible');
    attendreEgal(ui.parId('basculer-vue').getAttribute('aria-expanded'), 'true', 'état ouvert');
    ui.parId('basculer-vue').click();
    attendre(ui.parId('ecran-complet').hidden, 'retour accueil impossible');
  });

  await testAsync('Accueil : gestes haut, bas en haut et liste déjà défilée', async c => {
    const ui = preparerInterface(c);
    const ecran = ui.parId('ecran-complet');
    glisser(ui, ui.parId('accueil'), 100, 300, 100, 180);
    attendre(!ecran.hidden, 'geste haut sans ouverture');
    attendre(ecran.scrollHeight > ecran.clientHeight, 'liste non défilable pour le test');
    ecran.scrollTop = 80;
    glisser(ui, ecran, 100, 180, 100, 300);
    attendre(!ecran.hidden, 'geste bas ferme une liste défilée');
    ecran.scrollTop = 0;
    glisser(ui, ecran, 100, 180, 100, 300);
    attendre(ecran.hidden, 'geste bas en haut sans retour accueil');
  });

  await testAsync('Accueil : gestes horizontaux, courts et sur boutons ignorés', async c => {
    const ui = preparerInterface(c);
    const ecran = ui.parId('ecran-complet');
    glisser(ui, ui.parId('accueil'), 100, 300, 250, 220);
    attendre(ecran.hidden, 'geste horizontal ouvre la liste');
    glisser(ui, ui.parId('accueil'), 100, 300, 100, 250);
    attendre(ecran.hidden, 'geste trop court ouvre la liste');
    glisser(ui, ui.parId('basculer-vue'), 100, 300, 100, 180);
    attendre(ecran.hidden, 'geste sur bouton ouvre la liste');
    ui.parId('clavier').showModal();
    glisser(ui, ui.parId('accueil'), 100, 300, 100, 180);
    attendre(ecran.hidden, 'geste pendant dialogue ouvre la liste');
    ui.parId('clavier').close();
  });

  for (const [largeur, hauteur] of [[1024, 768], [360, 560]]) {
    await testAsync(`Présentation : tailles calculées et aucun débordement à ${largeur} × ${hauteur}`, async c => {
      const ui = preparerInterface(c, { largeur, hauteur });
      const style = noeud => ui.cadre.contentWindow.getComputedStyle(noeud);
      attendreEgal(parseFloat(style(ui.parId('date')).fontSize), 18.5, 'taille de la date modifiée');
      attendreEgal(style(ui.doc.querySelector('header.horloge')).textAlign, 'center', 'date non centrée');
      ui.parId('basculer-vue').click();
      const intitule = ui.doc.querySelector('#liste-taches .intitule');
      attendreEgal(parseFloat(style(intitule).fontSize), 18.7, 'taille de la liste');
      attendre(parseFloat(style(intitule).fontSize) > 17, 'liste non agrandie');
      attendre(ui.doc.documentElement.scrollWidth <= largeur, 'débordement horizontal du document');
      attendre(ui.doc.body.scrollWidth <= largeur, 'débordement horizontal du corps');
      const liste = ui.parId('ecran-complet');
      attendre(liste.scrollWidth <= liste.clientWidth, 'débordement horizontal de la liste');
      c.localStorage.setItem('cap_google_deja_connecte_v1', 'oui');
      c.googleConnexion.deconnecter();
      c.localStorage.setItem('cap_google_file_v1', JSON.stringify(c.TACHES.map(t => t.id)));
      ui.actualiser();
      const alerte = ui.parId('alerte-google');
      attendre(!alerte.hidden, 'alerte non affichée pour contrôle de largeur');
      attendre(alerte.scrollWidth <= alerte.clientWidth, 'débordement de l’alerte');
      for (const cible of [alerte, ui.doc.querySelector('footer.dictee')]) {
        const rectangle = cible.getBoundingClientRect();
        attendre(rectangle.left >= 0 && rectangle.right <= largeur + 1, 'élément hors largeur disponible');
      }
    });
  }

  test('Recherche : normalisation des accents et de la casse', () => {
    attendreEgal(recherche.normaliser('Été À ÇÔTÉ e\u0301'), 'ete a cote e', 'normalisation');
    attendreEgal(recherche.normaliser(null), '', 'champ absent');
  });

  test('Recherche : tous les champs des tâches, faites incluses et abandonnées exclues', () => {
    const liste = [
      { intitule: 'FICTIF Café', categorie: 'Maison', sous_categorie: 'Étage', note: 'Réparer', fait: true },
      { intitule: 'FICTIF Café abandonné', abandonnee_le: '2030-01-01' }
    ];
    for (const texte of ['CAFE', 'maison', 'etage', 'reparer']) {
      attendreEgal(recherche.chercherTaches(liste, texte), [liste[0]], texte);
    }
    attendreEgal(recherche.chercherTaches(liste, ' '), [], 'requête vide');
    attendreEgal(recherche.chercherTaches(liste, 'absent'), [], 'absent');
  });

  test('Recherche : rendez-vous par titre, lieu et description sans mutation', () => {
    const liste = [{ titre: 'FICTIF Répétition', lieu: 'Théâtre', description: 'Éclairage', date: '2030-01-01', heure: '14:32' }];
    const avant = JSON.stringify(liste);
    for (const texte of ['repetition', 'THEATRE', 'eclairage']) {
      attendreEgal(recherche.chercherRendezVous(liste, texte), liste, texte);
    }
    attendreEgal(recherche.chercherRendezVous(liste, ''), [], 'vide');
    attendreEgal(JSON.stringify(liste), avant, 'données modifiées');
  });

  test('Journal : trente entrées, ordre et intitulé exact', () => {
    const memoire = espaceMemoire();
    const journal = objetIsole(SOURCE_JOURNAL_ACTIONS, 'journalActions', { localStorage: memoire });
    for (let i = 0; i < 35; i++) journal.noter('ajout', `FICTIF ${i} <b>Été</b>  `);
    const entrees = journal.lire();
    attendreEgal(entrees.length, 30, 'limite');
    attendreEgal(entrees[0].texte, 'FICTIF 34 <b>Été</b>  ', 'plus récente');
    attendreEgal(entrees[29].texte, 'FICTIF 5 <b>Été</b>  ', 'plus ancienne');
    attendre(entrees.every(entree => Number.isFinite(Date.parse(entree.heure))), 'heure ISO');
    attendreEgal(Object.keys(entrees[0]), ['heure', 'type', 'texte'], 'structure');
  });

  test('Journal : JSON cassé et structures invalides', () => {
    const memoire = espaceMemoire();
    const journal = objetIsole(SOURCE_JOURNAL_ACTIONS, 'journalActions', { localStorage: memoire });
    for (const brut of ['{cassé', 'null', '{}', '[null,{},42]']) {
      memoire.setItem('cap_journal_actions_v1', brut);
      attendreEgal(journal.lire(), [], 'lecture robuste');
      journal.noter('ajout', 'FICTIF après corruption');
      attendreEgal(journal.lire().length, 1, 'écriture après corruption');
    }
  });

  test('Journal : stockage refusé en lecture et écriture sans erreur', () => {
    const journal = objetIsole(SOURCE_JOURNAL_ACTIONS, 'journalActions', {
      localStorage: { getItem() { throw new Error('refus'); }, setItem() { throw new Error('refus'); } }
    });
    attendreEgal(journal.lire(), [], 'lecture refusée');
    journal.noter('ajout', 'FICTIF refus');
  });

  test('Journal : toutes les actions réussies et aucune après échec', () => {
    localStorage.removeItem('cap_journal_actions_v1');
    const texte = '  FICTIF <b>Été</b> exact  ';
    const tache = creerTache({ intitule: texte });
    cocher(tache.id, true);
    cocher(tache.id, false);
    abandonner(tache.id);
    remettre(tache.id);
    attendreEgal(journalActions.lire().map(entree => entree.type),
      ['remise', 'abandon', 'remise à faire', 'fait', 'ajout'], 'actions');
    attendre(journalActions.lire().every(entree => entree.texte === texte), 'intitulé reformulé');
    const avant = JSON.stringify(journalActions.lire());
    const original = stockage.enregistrer;
    stockage.enregistrer = () => { throw new Error('FICTIF refus'); };
    try {
      attendreErreur(() => creerTache({ intitule: 'FICTIF échec' }), 'refus');
      attendreErreur(() => cocher(tache.id, true), 'refus');
      attendreErreur(() => abandonner(tache.id), 'refus');
    } finally {
      stockage.enregistrer = original;
    }
    attendreEgal(JSON.stringify(journalActions.lire()), avant, 'action échouée journalisée');
  });

  test('Journal : ajout clavier libre et dictée par la porte commune', () => {
    localStorage.removeItem('cap_journal_actions_v1');
    for (const source of ['micro', 'clavier', 'saisie']) {
      traiterDemande({ texte: `FICTIF journal ${source}`, source });
      attendreEgal(journalActions.lire()[0].texte, `FICTIF journal ${source}`, source);
    }
    attendreEgal(journalActions.lire().length, 3, 'doublon journal');
  });

  test('Dernières actions : affichage immédiat après ajout et coche', () => {
    localStorage.removeItem('cap_journal_actions_v1');
    document.getElementById('ajouter').click();
    document.getElementById('intitule').value = 'FICTIF journal interface';
    document.getElementById('formulaire-ajout').requestSubmit();
    const zone = document.getElementById('dernieres-actions');
    attendre(!zone.hidden, 'zone cachée après ajout');
    attendre(zone.textContent.includes('Ajouté : FICTIF journal interface'), 'ajout absent');
    const tache = TACHES.find(tache => tache.intitule === 'FICTIF journal interface');
    const caseTache = document.getElementById(`tache-${tache.id}`);
    caseTache.checked = true;
    caseTache.dispatchEvent(new Event('change'));
    attendre(document.getElementById('liste-actions').firstElementChild.textContent.includes('Fait : FICTIF journal interface'), 'coche absente');
    attendre(!document.getElementById('liste-taches').querySelector(`[data-tache="${tache.id}"]`), 'tâche cochée encore dans la liste');
  });

  function tacheInterface(intitule, cochee = false) {
    document.getElementById('ajouter').click();
    document.getElementById('intitule').value = intitule;
    document.getElementById('formulaire-ajout').requestSubmit();
    const tache = TACHES.find(tache => tache.intitule === intitule);
    attendre(tache, 'tâche de test non créée');
    if (cochee) {
      const caseTache = document.getElementById(`tache-${tache.id}`);
      caseTache.checked = true;
      caseTache.dispatchEvent(new Event('change'));
    }
    return tache;
  }

  test('Terminées : ligne repliée en bas, compteur, décocher remet la tâche dans sa catégorie', () => {
    const bouton = document.getElementById('basculer-terminees');
    const liste = document.getElementById('liste-terminees');
    const tache = tacheInterface('FICTIF terminée interface', true);
    const nombre = TACHES.filter(t => t.fait && !t.abandonnee_le && (!t.parente || !TACHES.some(p => p.id === t.parente && !p.abandonnee_le))).length;
    attendre(!bouton.hidden, 'ligne Terminées cachée');
    attendreEgal(bouton.textContent, `Terminées (${nombre})`, 'compteur');
    attendre(liste.hidden, 'liste ouverte par défaut');
    attendreEgal(bouton.getAttribute('aria-expanded'), 'false', 'aria fermé');
    bouton.click();
    attendre(!liste.hidden, 'liste non ouverte');
    const caseTache = document.getElementById(`tache-${tache.id}`);
    attendre(liste.contains(caseTache) && caseTache.checked, 'tâche absente des terminées');
    caseTache.checked = false;
    caseTache.dispatchEvent(new Event('change'));
    attendre(!tache.fait, 'tâche encore cochée');
    attendre(document.getElementById(`tache-${tache.id}`).closest('.categorie'), 'tâche pas revenue dans sa catégorie');
    attendreEgal(bouton.textContent, `Terminées (${nombre - 1})`, 'compteur après décoche');
    bouton.click();
    attendre(liste.hidden, 'liste non refermée');
    attendre(TACHES.includes(tache), 'tâche perdue');
  });

  function listesIsolees(taches = [], etapes = { Roman: ['Relire'] }, memoire = espaceMemoire(), fenetre = new EventTarget()) {
    let evenements = 0;
    fenetre.addEventListener('cap-listes-changees', () => { evenements += 1; });
    const instance = objetIsole(SOURCE_LISTES_CHOIX, 'listesChoix', {
      localStorage: memoire, window: fenetre, TACHES: taches, ETAPES_PAR_DEFAUT: etapes, dateDuJour: () => '2026-10-29'
    });
    return { instance, memoire, etapes, fenetre, evenements: () => evenements };
  }

  function annuaireIsolee(memoire = espaceMemoire(), fenetre = new EventTarget()) {
    let evenements = 0;
    fenetre.addEventListener('cap-annuaire-changee', () => { evenements += 1; });
    const instance = objetIsole(SOURCE_ANNUAIRE, 'annuaire', { localStorage: memoire, window: fenetre });
    return { instance, memoire, fenetre, evenements: () => evenements };
  }

  const boutonTexte = (racine, texte) => Array.from(racine.querySelectorAll('button')).find(bouton => bouton.textContent === texte);
  const texteJour = date => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;

  function remettreListesPage(etapesAvant) {
    document.querySelectorAll('dialog[open]').forEach(dialogue => dialogue.close());
    if (etapesAvant) {
      for (const nom of Object.keys(ETAPES_PAR_DEFAUT)) if (!(nom in etapesAvant)) delete ETAPES_PAR_DEFAUT[nom];
    }
    localStorage.removeItem('cap_listes_v1');
    localStorage.removeItem('cap_listes_a_envoyer_v1');
    listesChoix.recharger();
  }

  test('Listes : À trier en tête, plus utilisées ensuite, couleurs et sous-catégories', () => {
    const taches = [
      { categorie: 'Musique', sous_categorie: 'Guitare' }, { categorie: 'Jardin', sous_categorie: '' },
      { categorie: 'Jardin', sous_categorie: '' }, { categorie: 'Écriture', sous_categorie: '', abandonnee_le: '2026-01-01' }
    ];
    const l = listesIsolees(taches);
    attendreEgal(l.instance.categories(), ['À trier', 'Jardin', 'Musique', 'Écriture', 'Quotidien'], 'ordre');
    attendreEgal(l.instance.couleur('À trier'), '#6f6f6f', 'gris pour À trier');
    const couleurs = l.instance.categories().map(nom => l.instance.couleur(nom));
    attendreEgal(new Set(couleurs).size, couleurs.length, 'une couleur par catégorie');
    attendre(couleurs.every(couleur => /^#[0-9a-f]{6}$/i.test(couleur)), 'couleurs valides');
    attendreEgal(l.instance.categories('Musique'), ['Guitare'], 'sous-catégorie reprise des tâches');
    attendreEgal(l.instance.modeles(), ['Roman'], 'modèles de départ');
    attendre(!l.instance.aEnvoyer(), 'rien à envoyer au départ');
    attendreEgal(l.instance.ajouterCategorie('  Voyage   lointain '), 'Voyage lointain', 'nom nettoyé');
    attendre(l.instance.categories().includes('Voyage lointain') && l.instance.aEnvoyer() && l.evenements() > 0, 'ajout signalé');
    attendreEgal(l.instance.ajouterCategorie('musique'), 'Musique', 'pas de doublon');
    attendreEgal(l.instance.categories().filter(nom => nom === 'Musique').length, 1, 'Musique unique');
    l.instance.ajouterCategorie('Basse', 'Musique');
    attendreEgal(l.instance.categories('Musique'), ['Guitare', 'Basse'], 'sous-catégorie ajoutée');
    attendreEgal(l.instance.ajouterCategorie('x'.repeat(80)).length, 60, '60 caractères au plus');
    attendreErreur(() => l.instance.ajouterCategorie('   '), 'Indique un nom');
    attendreErreur(() => l.instance.ajouterCategorie('Solo', 'Inconnue'), 'introuvable');
    const relue = listesIsolees(taches, { Roman: ['Relire'] }, l.memoire);
    attendreEgal(relue.instance.categories('Musique'), ['Guitare', 'Basse'], 'relu après redémarrage');
  });

  test('Listes : retirer n’efface rien, remettre, modèles ajoutés et retirés', () => {
    const l = listesIsolees([{ categorie: 'Jardin', sous_categorie: '' }]);
    attendreEgal(l.instance.retirer('categorie', ['Jardin']), ['Jardin'], 'retrait');
    attendre(!l.instance.categories().includes('Jardin'), 'Jardin encore proposé');
    attendreEgal(l.instance.categoriesRetirees(), [{ nom: 'Jardin', retiree_le: '2026-10-29' }], 'retirée avec la date');
    attendre(l.instance.exporter().categories.some(categorie => categorie.nom === 'Jardin'), 'Jardin effacé');
    attendreEgal(l.instance.remettre('categorie', ['Jardin']), ['Jardin'], 'remise');
    attendre(l.instance.categories().includes('Jardin'), 'Jardin pas revenu');
    attendreEgal(l.instance.ajouterModele('Concert', ['Répéter', '', '  Jouer  ']), 'Concert', 'modèle ajouté');
    attendreEgal(l.etapes.Concert, ['Répéter', 'Jouer'], 'étapes enregistrées pour la création');
    attendreErreur(() => l.instance.ajouterModele('concert', ['A']), 'existe déjà');
    attendreErreur(() => l.instance.ajouterModele('Vide', ['  ']), 'au moins une étape');
    attendreErreur(() => l.instance.ajouterModele('Long', Array.from({ length: 21 }, (_, i) => `É${i}`)), 'Vingt étapes');
    l.instance.retirer('modele', ['Roman']);
    attendreEgal(l.instance.modeles(), ['Concert'], 'Roman retiré du menu');
    attendreEgal(l.etapes.Roman, ['Relire'], 'Roman gardé');
    attendreEgal(l.instance.exporter().modeles.find(modele => modele.nom === 'Roman').retiree_le, '2026-10-29', 'date de retrait');
    attendreEgal(l.instance.ajouterModele('roman', ['Relire', 'Envoyer']), 'Roman', 'modèle remis par un nouvel ajout');
    attendreEgal(l.instance.etapes('Roman'), ['Relire', 'Envoyer'], 'nouvelles étapes');
    attendreEgal(l.instance.modeles(), ['Roman', 'Concert'], 'ordre conservé');
  });

  test('Listes : fusion avec le tableau, la modification la plus récente gagne', () => {
    const l = listesIsolees([]);
    l.instance.retirer('categorie', ['Musique']);
    l.instance.marquerEnvoye();
    l.instance.fusionner({
      modeles: [
        { nom: 'Roman', etapes: ['A', 'B'], retiree_le: '', modifie_le: '2099-01-01T00:00:00.000Z' },
        { nom: 'Album', etapes: ['Mixer'], retiree_le: '', modifie_le: '' }
      ],
      categories: [
        { nom: 'musique', parente: '', couleur: '#123456', retiree_le: '', modifie_le: '2000-01-01T00:00:00.000Z' },
        { nom: 'Sport', parente: '', couleur: '', retiree_le: '', modifie_le: '' },
        { nom: 'Course', parente: 'Sport', couleur: '', retiree_le: '', modifie_le: '' }
      ]
    });
    attendreEgal(l.instance.etapes('Roman'), ['A', 'B'], 'version distante plus récente');
    attendreEgal(l.etapes.Album, ['Mixer'], 'modèle distant ajouté');
    attendre(!l.instance.categories().includes('Musique'), 'retrait local plus récent perdu');
    attendreEgal(l.instance.couleur('Musique'), '#123456', 'couleur du tableau');
    attendre(/^#[0-9a-f]{6}$/i.test(l.instance.couleur('Sport')), 'couleur donnée à Sport');
    attendreEgal(l.instance.categories('Sport'), ['Course'], 'sous-catégorie distante');
    attendre(!l.instance.aEnvoyer(), 'la fusion seule ne demande pas d’envoi');
  });

  test('Compréhension : ce week-end, semaine prochaine et jours pour les dates', () => {
    const jeudi = new Date(2026, 9, 29, 12);
    attendreEgal(comprendreDemande.date('ce week-end', jeudi), '2026-10-31', 'week-end depuis jeudi');
    attendreEgal(comprendreDemande.date('ce week-end', new Date(2026, 9, 31, 12)), '2026-10-31', 'samedi');
    attendreEgal(comprendreDemande.date('ce weekend', new Date(2026, 10, 1, 12)), '2026-11-01', 'dimanche');
    attendreEgal(comprendreDemande.date('semaine prochaine', jeudi), '2026-11-02', 'lundi suivant');
    attendreEgal(comprendreDemande.date('la semaine prochaine', new Date(2026, 10, 2, 12)), '2026-11-09', 'depuis un lundi');
    attendreEgal(comprendreDemande.date('Vendredi', jeudi), '2026-10-30', 'vendredi');
    attendreEgal(comprendreDemande.date('le 12 novembre', jeudi), '2026-11-12', 'date en toutes lettres');
    attendreEgal(comprendreDemande.date('blabla', jeudi), '', 'rien inventé');
    attendreEgal(choixDates.dateRapide("aujourd'hui", jeudi), '2026-10-29', 'bouton Aujourd’hui');
  });

  test('Dates : toutes les façons de dire une date par rapport à aujourd’hui', () => {
    const jeudi = new Date(2026, 9, 29, 9);
    const cas = [
      ['dans deux semaines', '2026-11-12'], ['vendredi dans deux semaines', '2026-11-13'],
      ['dans 2 semaines, vendredi', '2026-11-13'], ['dans un mois', '2026-11-29'],
      ['le premier lundi du mois prochain', '2026-11-02'], ['le dernier vendredi du mois prochain', '2026-11-27'],
      ['après-demain', '2026-10-31'], ['dans trois jours', '2026-11-01'], ['lundi en huit', '2026-11-09'],
      ['mardi en quinze', '2026-11-17'], ['la semaine prochaine, mercredi', '2026-11-04'],
      ['mercredi de la semaine prochaine', '2026-11-04'], ['fin du mois', '2026-10-31'],
      ['fin du mois prochain', '2026-11-30'], ['dans une quinzaine', '2026-11-12'], ['dans un an', '2027-10-29'],
      ['le premier mardi de décembre', '2026-12-01'], ['le 3 février', '2027-02-03'],
      ['le quinze novembre', '2026-11-15'], ['ce jeudi', '2026-10-29'], ['mardi prochain', '2026-11-03']
    ];
    for (const [phrase, attendu] of cas) {
      const resultat = comprendreDates.trouver(phrase, jeudi);
      attendreEgal([resultat.date, resultat.choix], [attendu, []], phrase);
    }
    attendreEgal(comprendreDates.trouver('dans un mois', new Date(2027, 0, 31, 9)).date, '2027-02-28', 'fin de mois raccourcie');
    attendreEgal(comprendreDates.trouver('jeudi', jeudi).choix, ['2026-10-29', '2026-11-05'], 'jeudi un jeudi : question');
    attendreEgal(comprendreDates.trouver('vendredi prochain', jeudi).choix, ['2026-10-30', '2026-11-06'], 'vendredi prochain : question');
    attendreEgal(comprendreDates.trouver('dans 8 jours', jeudi).choix, ['2026-11-05', '2026-11-06'], 'huit jours : question');
    attendreEgal(comprendreDates.trouver('le 15', jeudi).date, '', 'le 15 seul ignoré dans une phrase');
    attendreEgal(comprendreDates.trouver('le 15', jeudi, { seul: true }).date, '2026-11-15', 'le 15 dans Dire la date');
    attendreEgal(comprendreDates.trouver('acheter du pain FICTIF', jeudi), { date: '', choix: [], morceau: '' }, 'rien inventé');
    const rdv = comprendreDemande.rendezVous('rendez-vous jeudi à 10h garage FICTIF', jeudi);
    attendreEgal([rdv.date, rdv.choix_date], ['', ['2026-10-29', '2026-11-05']], 'rendez-vous : date à demander');
  });

  test('Dates : une tâche dictée reçoit son échéance, et Cap demande quand il hésite', () => {
    const avant = TACHES.length;
    const resultat = traiterDemande({ texte: 'Rappeler le garage FICTIF dans deux semaines', source: 'micro' });
    attendreEgal(resultat.type, 'tache', 'type');
    attendreEgal(resultat.tache.intitule, 'Rappeler le garage FICTIF dans deux semaines', 'intitulé intact');
    attendreEgal(resultat.tache.echeance, comprendreDates.trouver('dans deux semaines').date, 'échéance');
    attendreEgal(TACHES.length, avant + 1, 'une tâche ajoutée');
    const hesite = traiterDemande({ texte: 'Arroser les plantes FICTIF dans 8 jours', source: 'micro' });
    attendreEgal([hesite.tache.echeance, hesite.choix_echeance.length], ['', 2], 'hésitation : pas de date devinée');
  });

  test('Ajouter une tâche : dates en menus, boutons rapides, date impossible refusée', () => {
    remettreListesPage();
    document.getElementById('ajouter').click();
    const formulaireTache = document.getElementById('formulaire-ajout');
    attendreEgal(formulaireTache.querySelectorAll('input[type="date"]').length, 0, 'plus de saisie JJ/MM/AAAA');
    const jour = document.getElementById('echeance-jour');
    const mois = document.getElementById('echeance-mois');
    const annee = document.getElementById('echeance-annee');
    const echeance = document.getElementById('echeance');
    attendre(jour && mois && annee, 'trois menus absents');
    attendreEgal(annee.options[1].value, String(new Date().getFullYear()), 'année en cours en premier');
    attendreEgal(mois.options[11].textContent, 'novembre', 'mois en toutes lettres');
    attendreEgal(echeance.value, '', 'vide par défaut');
    const zone = jour.closest('.champ-date');
    attendreEgal(Array.from(zone.querySelectorAll('.boutons-rapides button'), b => b.textContent),
      ['Aujourd’hui', 'Demain', 'Ce week-end', 'Semaine prochaine'], 'quatre boutons rapides');
    const demain = new Date();
    demain.setDate(demain.getDate() + 1);
    boutonTexte(zone, 'Demain').click();
    attendreEgal(echeance.value, texteJour(demain), 'Demain');
    attendreEgal([jour.value, mois.value, annee.value], texteJour(demain).split('-').reverse(), 'menus remplis d’un coup');
    attendreEgal(boutonTexte(zone, 'Demain').getAttribute('aria-pressed'), 'true', 'bouton marqué');
    boutonTexte(zone, 'Ce week-end').click();
    const weekend = new Date(`${echeance.value}T12:00:00`);
    attendre([0, 6].includes(weekend.getDay()) && echeance.value >= texteJour(new Date()), 'week-end incorrect');
    boutonTexte(zone, 'Semaine prochaine').click();
    attendre(new Date(`${echeance.value}T12:00:00`).getDay() === 1 && echeance.value > texteJour(new Date()), 'semaine prochaine incorrecte');
    boutonTexte(zone, 'Effacer').click();
    attendreEgal([echeance.value, jour.value, mois.value, annee.value], ['', '', '', ''], 'effacé');
    mois.value = '03';
    mois.dispatchEvent(new Event('change'));
    attendreEgal([jour.value, annee.value], [String(new Date().getDate()).padStart(2, '0'), String(new Date().getFullYear())], 'jour et année du jour complétés');
    jour.value = '31';
    mois.value = '02';
    jour.dispatchEvent(new Event('change'));
    attendreEgal(echeance.value, '', 'date impossible gardée');
    attendre(jour.validationMessage.includes('n’existe pas'), 'pas de message pour le 31 février');
    document.getElementById('intitule').value = 'FICTIF date impossible';
    const avant = TACHES.length;
    formulaireTache.requestSubmit();
    attendreEgal(TACHES.length, avant, 'tâche créée avec une date impossible');
    jour.value = '28';
    jour.dispatchEvent(new Event('change'));
    attendreEgal(echeance.value, `${annee.value}-02-28`, '28 février');
    attendreEgal(jour.validationMessage, '', 'message retiré');
    boutonTexte(document.getElementById('avant-le-jour').closest('.champ-date'), 'Aujourd’hui').click();
    document.getElementById('intitule').value = 'FICTIF dates menus';
    formulaireTache.requestSubmit();
    const tache = TACHES.find(item => item.intitule === 'FICTIF dates menus');
    attendre(tache, 'tâche non créée');
    attendreEgal([tache.echeance, tache.avant_le], [`${annee.value}-02-28`, texteJour(new Date())], 'dates enregistrées');
    document.getElementById('ajouter').click();
    attendreEgal([echeance.value, jour.value, document.getElementById('avant-le').value], ['', '', ''], 'formulaire remis à zéro');
    remettreListesPage();
  });

  test('Ajouter une tâche : catégories en gros boutons, sous-catégories, ajouter et retirer sans effacer', () => {
    remettreListesPage();
    document.getElementById('ajouter').click();
    document.getElementById('choisir-categorie').click();
    const fenetre = document.getElementById('fenetre-liste');
    attendre(fenetre.open, 'liste des catégories pas ouverte');
    attendreEgal(fenetre.querySelectorAll('input, textarea').length, 0, 'aucun champ texte, donc pas de clavier');
    const premiers = Array.from(fenetre.querySelector('.grille-choix').querySelectorAll('.bouton-choix'), b => b.textContent);
    attendreEgal(premiers[0], 'À trier', 'À trier en premier');
    attendre(['Musique', 'Écriture', 'Quotidien'].every(nom => premiers.includes(nom)), 'catégories prêtes absentes');
    boutonTexte(fenetre, '+ Ajouter').click();
    document.getElementById('nom-nouvel-element').value = 'Jardin FICTIF';
    fenetre.querySelector('form').requestSubmit();
    const jardin = boutonTexte(fenetre, 'Jardin FICTIF');
    attendre(jardin, 'nouvelle catégorie pas devenue un bouton');
    attendre(jardin.style.getPropertyValue('--couleur-choix'), 'nouvelle catégorie sans couleur');
    jardin.click();
    attendreEgal(document.getElementById('titre-fenetre-liste').textContent, 'Jardin FICTIF : sous-catégorie', 'sous-catégories ouvertes');
    boutonTexte(fenetre, '+ Ajouter').click();
    document.getElementById('nom-nouvel-element').value = 'Potager';
    fenetre.querySelector('form').requestSubmit();
    boutonTexte(fenetre, 'Potager').click();
    attendre(!fenetre.open, 'fenêtre restée ouverte après le choix');
    attendreEgal([document.getElementById('categorie').value, document.getElementById('sous-categorie').value], ['Jardin FICTIF', 'Potager'], 'choix enregistré');
    attendreEgal(document.getElementById('texte-categorie').textContent, 'Jardin FICTIF › Potager', 'choix affiché');
    document.getElementById('intitule').value = 'FICTIF catégorie boutons';
    document.getElementById('formulaire-ajout').requestSubmit();
    const tache = TACHES.find(item => item.intitule === 'FICTIF catégorie boutons');
    attendreEgal([tache.categorie, tache.sous_categorie], ['Jardin FICTIF', 'Potager'], 'tâche classée');
    const section = document.getElementById(`tache-${tache.id}`).closest('section.categorie');
    attendreEgal(section.style.getPropertyValue('--couleur-categorie'), listesChoix.couleur('Jardin FICTIF'), 'couleur dans la liste');
    document.getElementById('ajouter').click();
    document.getElementById('choisir-categorie').click();
    boutonTexte(fenetre, 'Modifier').click();
    const retirer = Array.from(fenetre.querySelectorAll('.bouton-retirer'))[0];
    attendre(retirer.hidden, 'Retirer visible sans case cochée');
    const caseJardin = Array.from(fenetre.querySelectorAll('.liste-cases input')).find(c => c.value === 'Jardin FICTIF');
    caseJardin.checked = true;
    caseJardin.dispatchEvent(new Event('change'));
    attendre(!retirer.hidden && retirer.textContent === 'Retirer (1)', 'bouton Retirer (1) absent');
    retirer.click();
    attendre(!listesChoix.categories().includes('Jardin FICTIF'), 'catégorie encore proposée');
    attendre(listesChoix.exporter().categories.find(c => c.nom === 'Jardin FICTIF').retiree_le, 'catégorie effacée au lieu d’être marquée');
    attendre(fenetre.querySelector('.section-retirees').textContent.includes('Jardin FICTIF'), 'pas dans Retirées');
    const bandeau = document.getElementById('annulation-liste');
    attendre(!bandeau.hidden, 'pas de bouton Annuler');
    boutonTexte(bandeau, 'Annuler').click();
    attendre(listesChoix.categories().includes('Jardin FICTIF'), 'Annuler n’a pas remis la catégorie');
    attendre(TACHES.includes(tache) && tache.categorie === 'Jardin FICTIF', 'tâche touchée');
    remettreListesPage();
  });

  test('Étapes par défaut : Ajouter et Modifier la liste depuis le menu', () => {
    const etapesAvant = JSON.parse(JSON.stringify(ETAPES_PAR_DEFAUT));
    remettreListesPage(etapesAvant);
    document.getElementById('ajouter').click();
    const selection = document.getElementById('modele');
    const options = Array.from(selection.options);
    attendreEgal(options.slice(-2).map(o => [o.value, o.textContent]), [['__ajouter', 'Ajouter…'], ['__modifier', 'Modifier la liste…']], 'deux choix en bas');
    selection.value = '__ajouter';
    selection.dispatchEvent(new Event('change'));
    attendreEgal(selection.value, '', 'menu remis à l’ancien choix');
    const fenetre = document.getElementById('fenetre-liste');
    attendre(fenetre.open, 'fenêtre d’ajout pas ouverte');
    document.getElementById('nom-nouvel-element').value = 'Concert FICTIF';
    document.getElementById('etapes-nouveau-modele').value = 'Répéter\n\nJouer';
    fenetre.querySelector('form').requestSubmit();
    attendre(!fenetre.open, 'fenêtre restée ouverte');
    attendreEgal(selection.value, 'Concert FICTIF', 'nouveau modèle choisi');
    attendreEgal(ETAPES_PAR_DEFAUT['Concert FICTIF'], ['Répéter', 'Jouer'], 'étapes enregistrées');
    attendre(listesChoix.aEnvoyer(), 'pas marqué pour le tableau');
    document.getElementById('intitule').value = 'FICTIF concert';
    document.getElementById('formulaire-ajout').requestSubmit();
    const parent = TACHES.find(item => item.intitule === 'FICTIF concert');
    attendreEgal(TACHES.filter(item => item.parente === parent.id).map(item => item.intitule), ['Répéter', 'Jouer'], 'étapes créées');
    document.getElementById('ajouter').click();
    selection.value = '__modifier';
    selection.dispatchEvent(new Event('change'));
    attendre(fenetre.open, 'fenêtre Modifier pas ouverte');
    const retirer = fenetre.querySelector('.bouton-retirer');
    attendre(retirer.hidden, 'Retirer visible d’emblée');
    const caseConcert = Array.from(fenetre.querySelectorAll('.liste-cases input')).find(c => c.value === 'Concert FICTIF');
    caseConcert.checked = true;
    caseConcert.dispatchEvent(new Event('change'));
    attendreEgal(retirer.textContent, 'Retirer (1)', 'compteur');
    fenetre.querySelector('.bouton-retirer').click();
    attendre(!listesChoix.modeles().includes('Concert FICTIF'), 'modèle encore proposé');
    attendre(!Array.from(selection.options).some(o => o.value === 'Concert FICTIF'), 'modèle encore dans le menu');
    attendreEgal(listesChoix.modelesRetires().map(m => m.nom), ['Concert FICTIF'], 'modèle gardé comme retiré');
    boutonTexte(document.getElementById('annulation-liste'), 'Annuler').click();
    attendre(listesChoix.modeles().includes('Concert FICTIF'), 'Annuler sans effet');
    const caseDeNouveau = Array.from(fenetre.querySelectorAll('.liste-cases input')).find(c => c.value === 'Concert FICTIF');
    caseDeNouveau.checked = true;
    caseDeNouveau.dispatchEvent(new Event('change'));
    fenetre.querySelector('.bouton-retirer').click();
    boutonTexte(fenetre.querySelector('.section-retirees'), 'Remettre').click();
    attendre(listesChoix.modeles().includes('Concert FICTIF'), 'Remettre sans effet');
    attendre(Array.from(selection.options).some(o => o.value === 'Concert FICTIF'), 'modèle pas revenu dans le menu');
    remettreListesPage(etapesAvant);
  });

  test('Dates : ligne en toutes lettres sous les menus, vide si la date est vide', () => {
    attendreEgal(choixDates.dateEnLettres('2026-11-02'), 'lundi 2 novembre 2026', 'lundi 2 novembre');
    attendreEgal(choixDates.dateEnLettres('2026-02-31'), '', 'date impossible');
    attendreEgal(choixDates.dateEnLettres(''), '', 'date vide');
    remettreListesPage();
    document.getElementById('ajouter').click();
    const lisible = document.getElementById('echeance-lisible');
    const echeance = document.getElementById('echeance');
    attendreEgal(lisible.textContent, '', 'rien tant que la date est vide');
    const zone = lisible.closest('.champ-date');
    boutonTexte(zone, 'Demain').click();
    attendreEgal(lisible.textContent, choixDates.dateEnLettres(echeance.value), 'bouton rapide');
    const jour = document.getElementById('echeance-jour');
    const mois = document.getElementById('echeance-mois');
    const annee = document.getElementById('echeance-annee');
    jour.value = '02';
    mois.value = '11';
    annee.value = '2026';
    annee.dispatchEvent(new Event('change'));
    attendreEgal(lisible.textContent, 'lundi 2 novembre 2026', 'menus');
    boutonTexte(zone, 'Effacer').click();
    attendreEgal(lisible.textContent, '', 'effacée');
    remettreListesPage();
  });

  test('Dire la date : écoute, relance si rien entendu, texte provisoire et dates dites', () => {
    let rappels = null;
    let demarrages = 0;
    const dicteeSimulee = {
      disponible: () => true,
      enCours: () => false,
      arreter() {},
      demarrer(r) { rappels = r; demarrages += 1; }
    };
    const instance = objetIsole(SOURCE_CHOIX_DATES, 'choixDates', {
      document, Date, comprendreDemande, dictee: dicteeSimulee, setTimeout: f => f()
    });
    const cible = document.createElement('input');
    cible.type = 'hidden';
    cible.id = 'date-essai-dictee';
    const conteneur = document.createElement('div');
    conteneur.dataset.cible = cible.id;
    conteneur.dataset.libelle = 'Essai';
    document.body.append(cible, conteneur);
    try {
      instance.installer(conteneur);
      const dire = boutonTexte(conteneur, 'Dire la date');
      const aide = conteneur.querySelector('.aide-date');
      attendre(!dire.hidden, 'bouton caché');
      dire.click();
      attendreEgal(demarrages, 1, 'écoute lancée');
      attendre(aide.textContent.includes('Je t’écoute'), 'pas de message d’écoute');
      rappels.surErreur('no-speech');
      rappels.surFin();
      attendreEgal(demarrages, 2, 'pas de relance après un silence');
      rappels.surFin();
      attendre(aide.textContent.includes('rien entendu'), 'pas de message après la relance');
      const jeudi = new Date();
      dire.click();
      rappels.surProvisoire('vendredi');
      attendre(aide.textContent.includes('vendredi'), 'texte entendu non affiché');
      rappels.surFin();
      attendreEgal(cible.value, comprendreDemande.date('vendredi', jeudi), 'texte provisoire non utilisé');
      dire.click();
      rappels.surFinal('demain');
      rappels.surFin();
      attendreEgal(cible.value, comprendreDemande.date('demain', new Date()), 'demain');
      dire.click();
      rappels.surFinal('le 15 novembre');
      rappels.surFin();
      attendreEgal(cible.value.slice(5), '11-15', 'le 15 novembre');
      attendre(conteneur.querySelector('.date-lisible').textContent.includes('15 novembre'), 'ligne lisible');
      dire.click();
      rappels.surErreur('not-allowed');
      rappels.surFin();
      attendre(aide.textContent.includes('bloqué'), 'micro bloqué non expliqué');
    } finally {
      cible.remove();
      conteneur.remove();
    }
  });

  test('Petites fenêtres : toucher à côté ferme, question Garder, Jeter et Continuer', () => {
    remettreListesPage();
    for (const id of ['clavier', 'menu-tache', 'ajout-tache']) {
      attendreEgal(document.querySelectorAll(`#${id} [data-fermer]`).length, 0, `bouton retour dans ${id}`);
    }
    const ajout = document.getElementById('ajout-tache');
    const intitule = document.getElementById('intitule');
    document.getElementById('ajouter').click();
    const cadre = ajout.getBoundingClientRect();
    ajout.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: cadre.left + 2, clientY: cadre.top + 2 }));
    attendre(ajout.open, 'fermée en touchant dedans');
    fermetureFenetres.toucheACote(ajout);
    attendre(!ajout.open, 'fenêtre vide pas fermée');
    document.getElementById('ajouter').click();
    intitule.value = 'FICTIF brouillon';
    intitule.dispatchEvent(new Event('input', { bubbles: true }));
    fermetureFenetres.toucheACote(ajout);
    attendre(ajout.open, 'fermée alors que Max avait écrit');
    const question = () => ajout.querySelector('.question-fermeture');
    attendre(question(), 'pas de question');
    attendreEgal(Array.from(question().querySelectorAll('button'), b => b.textContent), ['Garder', 'Jeter', 'Continuer'], 'trois boutons');
    boutonTexte(question(), 'Continuer').click();
    attendre(ajout.open && !question() && intitule.value === 'FICTIF brouillon', 'Continuer');
    fermetureFenetres.toucheACote(ajout);
    boutonTexte(question(), 'Garder').click();
    attendre(!ajout.open, 'Garder n’a pas fermé');
    document.getElementById('ajouter').click();
    attendreEgal(intitule.value, 'FICTIF brouillon', 'texte gardé retrouvé');
    fermetureFenetres.toucheACote(ajout);
    boutonTexte(question(), 'Jeter').click();
    attendre(!ajout.open, 'Jeter n’a pas fermé');
    const bandeau = document.querySelector('.annulation-fenetre');
    attendre(bandeau, 'pas de bouton Annuler après Jeter');
    document.getElementById('ajouter').click();
    attendreEgal(intitule.value, '', 'texte jeté revenu tout seul');
    ajout.close();
    boutonTexte(bandeau, 'Annuler').click();
    attendre(ajout.open, 'Annuler n’a pas rouvert');
    attendreEgal(intitule.value, 'FICTIF brouillon', 'Annuler n’a pas remis le texte');
    attendre(!document.querySelector('.annulation-fenetre'), 'bandeau resté');
    intitule.value = '';
    ajout.close();
    document.getElementById('ajouter').click();
    document.getElementById('choisir-categorie').click();
    const fenetre = document.getElementById('fenetre-liste');
    attendre(!boutonTexte(fenetre, 'Fermer') && !boutonTexte(fenetre, 'Retour'), 'bouton retour encore là');
    boutonTexte(fenetre, '+ Ajouter').click();
    const nom = document.getElementById('nom-nouvel-element');
    nom.value = 'Jardin FICTIF';
    nom.dispatchEvent(new Event('input', { bubbles: true }));
    fermetureFenetres.toucheACote(fenetre);
    boutonTexte(fenetre.querySelector('.question-fermeture'), 'Garder').click();
    attendre(fenetre.open, 'fenêtre d’avant pas revenue');
    attendreEgal(document.getElementById('titre-fenetre-liste').textContent, 'Catégorie', 'retour à la liste des catégories');
    attendre(ajout.open, 'fenêtre principale fermée');
    boutonTexte(fenetre, '+ Ajouter').click();
    attendreEgal(document.getElementById('nom-nouvel-element').value, 'Jardin FICTIF', 'nom gardé');
    document.getElementById('nom-nouvel-element').value = '';
    fermetureFenetres.toucheACote(fenetre);
    attendreEgal(document.getElementById('titre-fenetre-liste').textContent, 'Catégorie', 'vide : retour direct');
    fermetureFenetres.toucheACote(fenetre);
    attendre(!fenetre.open && ajout.open, 'catégories : retour à la fenêtre Ajouter');
    attendre(!listesChoix.categories().includes('Jardin FICTIF'), 'catégorie créée sans le vouloir');
    remettreListesPage();
  });

  test('Annuaire : création, modification avec historique, suppression douce et restauration', () => {
    attendreErreur(() => annuaire.creerContact({}), 'prénom ou un surnom');
    attendreErreur(() => annuaire.creerContact({ prenom: '   ' }), 'prénom ou un surnom');
    attendreErreur(() => annuaire.creerContact({ prenom: 'Mentor FICTIF', telephone: 'abc' }), 'numéro de téléphone');
    attendreErreur(() => annuaire.creerContact({ prenom: 'Mentor FICTIF', telephone: '06 00 00 00' }), 'dix chiffres');
    attendre(annuaire.creerContact({ prenom: 'Mentor FICTIF', telephone: '0600000000' }).telephone === '0600000000', 'numéro français à dix chiffres accepté');
    attendre(annuaire.creerContact({ prenom: 'Mentor FICTIF', telephone: '+1 212 555 0100' }).telephone === '+1 212 555 0100', 'numéro étranger jamais bloqué');
    attendre(annuaire.creerContact({ prenom: 'Mentor FICTIF', telephone: '0033600000000' }).telephone === '0033600000000', 'numéro international avec 00 jamais bloqué');
    attendreErreur(() => annuaire.creerContact({ prenom: 'Mentor FICTIF', mail: 'pas-un-mail' }), 'adresse mail');
    attendreErreur(() => annuaire.creerContact({ prenom: 'Mentor FICTIF', mail2: 'pas-un-mail' }), 'adresse mail');
    attendreErreur(() => annuaire.creerContact({ prenom: 'Mentor FICTIF', telephone2: 'abc' }), 'numéro de téléphone');
    attendreErreur(() => annuaire.creerContact({ prenom: 'Mentor FICTIF', anniversaire: '31-02' }), 'n’existe pas');
    attendreEgal(annuaire.creerContact({ prenom: 'Mentor FICTIF', anniversaire: '2-9' }).anniversaire, '02-09', 'date sans zéro acceptée');
    attendreErreur(() => annuaire.creerContact({ prenom: 'Mentor FICTIF', site_web: 'pas un site' }), 'site web');
    const contact = annuaire.creerContact({
      prenom: '  Mentor  ', nom: '  FICTIF  ', telephone: '06 00 00 00 00', telephone2: '07 00 00 00 00',
      mail: 'mentor.fictif@exemple.test', mail2: 'mentor2.fictif@exemple.test', anniversaire: '29-02', site_web: 'exemple.test'
    });
    attendreEgal(contact.prenom, 'Mentor', 'prénom nettoyé');
    attendreEgal(contact.nom, 'FICTIF', 'nom nettoyé');
    attendre(annuaire.tous().some(item => item.id === contact.id), 'contact listé');
    attendreEgal(contact.historique.length, 1, 'historique de création');
    const modifie = annuaire.modifierContact(contact.id, { telephone: '06 11 11 11 11' });
    attendreEgal(modifie.telephone, '06 11 11 11 11', 'téléphone modifié');
    const entreeHistorique = modifie.historique.find(e => e.champ === 'telephone');
    attendreEgal([entreeHistorique.ancienne, entreeHistorique.nouvelle], ['06 00 00 00 00', '06 11 11 11 11'], 'ancienne valeur gardée');
    const avantModif = modifie.historique.length;
    annuaire.modifierContact(contact.id, { telephone: '06 11 11 11 11' });
    attendreEgal(annuaire.trouver(contact.id).historique.length, avantModif, 'aucun changement : pas de nouvelle ligne');
    annuaire.supprimerContact(contact.id);
    attendre(!annuaire.tous().some(item => item.id === contact.id), 'contact retiré de la liste active');
    attendre(annuaire.supprimes().some(item => item.id === contact.id), 'contact dans les supprimés');
    attendre(!!annuaire.trouver(contact.id).supprime_le, 'date de suppression posée');
    annuaire.restaurerContact(contact.id);
    attendre(annuaire.tous().some(item => item.id === contact.id), 'contact restauré');
    attendreEgal(annuaire.trouver(contact.id).supprime_le, '', 'date de suppression effacée');
    attendreErreur(() => annuaire.trouver('C-introuvable'), 'introuvable');
  });

  test('Annuaire : dates multi-formats, abréviations, années ambiguës et dictée', () => {
    attendreEgal(annuaire.analyserAnniversaire('').valeur, '', 'date vide acceptée');
    attendreEgal(annuaire.analyserAnniversaire('11 01 77').ok, false, 'année à deux chiffres : ambigu');
    attendreEgal(annuaire.analyserAnniversaire('11 01 77').options.map(o => o.valeur).sort(), ['11-01-1977', '11-01-2077'], 'deux options complètes proposées');
    attendreEgal(annuaire.analyserAnniversaire('11 01 1977').valeur, '11-01-1977', 'année à quatre chiffres : pas d’ambiguïté');
    attendreEgal(annuaire.analyserAnniversaire('11 janvier').valeur, '11-01', 'mois en toutes lettres, sans année');
    attendreEgal(annuaire.analyserAnniversaire('11 janv 77').ok, false, 'mois abrégé, année à deux chiffres : toujours les deux options');
    attendreEgal(annuaire.analyserAnniversaire('11 janv. 1977').valeur, '11-01-1977', 'mois abrégé avec point, année à quatre chiffres');
    attendreEgal(annuaire.analyserAnniversaire('11/01/1977').valeur, '11-01-1977', 'séparateur barre oblique');
    attendreEgal(annuaire.analyserAnniversaire('11.01.1977').valeur, '11-01-1977', 'séparateur point');
    attendreEgal(annuaire.analyserAnniversaire('11-01-1977').valeur, '11-01-1977', 'séparateur tiret');
    attendreEgal(annuaire.analyserAnniversaire('onze janvier mille neuf cent soixante-dix-sept').valeur, '11-01-1977', 'dictée en toutes lettres');
    attendreEgal(annuaire.analyserAnniversaire('11 jui').ok, false, 'mois « jui » ambigu entre juin et juillet');
    attendreEgal(annuaire.analyserAnniversaire('11 jui').options.map(o => o.valeur).sort(), ['11-06', '11-07'], 'les deux mois possibles proposés');
    attendreErreur(() => annuaire.analyserAnniversaire('31 février'), 'n’existe pas');
    attendreErreur(() => annuaire.analyserAnniversaire('pas une date'), 'Vérifie');
    attendreEgal(annuaire.anniversaireLisible('11-01-1977'), '11 janvier 1977', 'affichage en toutes lettres avec année');
    attendreEgal(annuaire.anniversaireLisible('11-01'), '11 janvier', 'affichage en toutes lettres sans année');
  });

  test('Annuaire : un seul surnom suffit, plusieurs surnoms séparés par virgule', () => {
    const contact = annuaire.creerContact({ surnoms: 'Pépé FICTIF,  Papi FICTIF ,Pépé FICTIF' });
    attendreEgal(contact.surnoms, 'Pépé FICTIF, Papi FICTIF', 'surnoms nettoyés, doublons gardés en l’état de saisie');
    attendreEgal(annuaire.nomAffichage(contact), 'Pépé FICTIF', 'affichage basé sur le premier surnom sans prénom/nom');
  });

  test('Annuaire : recherche par prénom, nom ou n’importe quel surnom, accents et casse ignorés', () => {
    annuaire.creerContact({ prenom: 'Éléonore', nom: 'FICTIF', surnoms: 'Léo, Nono FICTIF' });
    annuaire.creerContact({ prenom: 'Leonard', nom: 'FICTIF' });
    const prefixe = annuaire.correspondances('leo');
    attendreEgal(prefixe.map(c => c.prenom), ['Éléonore', 'Leonard'], 'préfixe commun trouve les deux');
    const partiel = annuaire.correspondances('eleonor');
    attendreEgal(partiel.map(c => c.prenom), ['Éléonore'], 'recherche partielle sans accent');
    const parAutreSurnom = annuaire.correspondances('nono fictif');
    attendreEgal(parAutreSurnom.map(c => c.prenom), ['Éléonore'], 'trouvé par n’importe quel surnom de la liste');
    attendreEgal(annuaire.correspondances(''), [], 'recherche vide : rien');
    attendreEgal(annuaire.correspondances('zzz-inconnu'), [], 'rien trouvé');
  });

  test('Annuaire : recherche mot par mot, dès la première lettre, dans n’importe quel ordre', () => {
    annuaire.creerContact({ prenom: 'Marius', nom: 'Cousin FICTIF', lien: 'Mon cousin FICTIF' });
    annuaire.creerContact({ prenom: 'JP FICTIF', nom: '', lien: 'Mon voisin FICTIF' });
    attendreEgal(annuaire.correspondances('c').map(c => c.prenom), ['Marius'], 'une seule lettre ne doit pas perdre Marius Cousin');
    attendreEgal(annuaire.correspondances('cou').map(c => c.prenom), ['Marius'], 'début de mot « cou »');
    attendreEgal(annuaire.correspondances('Marius C').map(c => c.prenom), ['Marius'], 'deux mots dans l’ordre');
    attendreEgal(annuaire.correspondances('Cousin Marius').map(c => c.prenom), ['Marius'], 'deux mots dans le désordre');
    attendreEgal(annuaire.correspondances('mon cousin marius').map(c => c.prenom), ['Marius'], 'trois mots : trouve Marius, pas JP');
  });

  test('Annuaire : recherche insensible aux tirets, espaces, apostrophes et accents', () => {
    annuaire.creerContact({ prenom: 'JP FICTIF', surnoms: 'Jean-Pierre FICTIF' });
    annuaire.creerContact({ prenom: 'Andre FICTIF', nom: 'FICTIF' });
    attendreEgal(annuaire.correspondances('jean-pierre').map(c => c.prenom), ['JP FICTIF'], 'avec tiret');
    attendreEgal(annuaire.correspondances('jean pierre').map(c => c.prenom), ['JP FICTIF'], 'avec espace');
    attendreEgal(annuaire.correspondances('JEANPIERRE').map(c => c.prenom), [], 'collé sans séparateur : non trouvé, c’est attendu');
    attendreEgal(annuaire.correspondances('André').map(c => c.prenom), ['Andre FICTIF'], 'avec accent trouve sans accent');
    attendreEgal(annuaire.correspondances('andre').map(c => c.prenom), ['Andre FICTIF'], 'sans accent trouve sans accent');
  });

  test('Commandes annuaire : détection des trois commandes (fiche, appel, mail)', () => {
    attendreEgal(commandesAnnuaire.detecter('montre-moi la fiche de Milo FICTIF'),
      { action: 'fiche', nom: 'Milo FICTIF' }, 'fiche reconnue');
    attendreEgal(commandesAnnuaire.detecter('affiche la fiche d’Éléonore FICTIF'),
      { action: 'fiche', nom: 'Éléonore FICTIF' }, 'fiche avec apostrophe');
    attendreEgal(commandesAnnuaire.detecter('appelle Milo FICTIF'),
      { action: 'appel', nom: 'Milo FICTIF' }, 'appel reconnu');
    attendreEgal(commandesAnnuaire.detecter('mail à Milo FICTIF, dis-lui bonjour'),
      { action: 'mail', nom: 'Milo FICTIF', message: 'dis-lui bonjour' }, 'mail avec message');
    attendreEgal(commandesAnnuaire.detecter('mail a Milo FICTIF'),
      { action: 'mail', nom: 'Milo FICTIF', message: '' }, 'mail sans virgule : pas de message');
    attendreEgal(commandesAnnuaire.detecter('liste pommes'), null, 'pas de collision avec une autre commande');
    attendreEgal(commandesAnnuaire.detecter('appelle'), null, 'appelle sans nom : rien');
    attendreEgal(commandesAnnuaire.detecter(''), null, 'texte vide : rien');
  });

  test('Commandes annuaire : variantes de phrases d’origine (fiche, appel, mail)', () => {
    attendreEgal(commandesAnnuaire.detecter('ouvre la fiche de Milo FICTIF'),
      { action: 'fiche', nom: 'Milo FICTIF' }, 'ouvre la fiche de');
    attendreEgal(commandesAnnuaire.detecter('téléphone à Milo FICTIF'),
      { action: 'appel', nom: 'Milo FICTIF' }, 'téléphone à');
    attendreEgal(commandesAnnuaire.detecter('passe un coup de fil à Milo FICTIF'),
      { action: 'appel', nom: 'Milo FICTIF' }, 'passe un coup de fil à');
    attendreEgal(commandesAnnuaire.detecter('envoie un mail à Milo FICTIF, dis-lui bonjour'),
      { action: 'mail', nom: 'Milo FICTIF', message: 'dis-lui bonjour' }, 'envoie un mail à');
    attendreEgal(commandesAnnuaire.detecter('écris à Milo FICTIF, dis-lui bonjour'),
      { action: 'mail', nom: 'Milo FICTIF', message: 'dis-lui bonjour' }, 'écris à');
  });

  test('Commandes annuaire : résolution via l’annuaire, 0/1/plusieurs correspondances', () => {
    annuaire.creerContact({ prenom: 'Milo', nom: 'FICTIF', telephone: '0600000010', mail: 'milo.fictif@exemple.test' });
    annuaire.creerContact({ prenom: 'Milovan', nom: 'FICTIF', telephone: '0600000011' });
    annuaire.creerContact({ prenom: 'Zoe', nom: 'FICTIF' });
    const aucun = commandesAnnuaire.resoudreContact('Personne FICTIF');
    attendreEgal(aucun, { statut: 'aucun' }, 'aucune correspondance');
    const plusieurs = commandesAnnuaire.resoudreContact('milo');
    attendre(plusieurs.statut === 'plusieurs' && plusieurs.contacts.length === 2, 'deux Milo trouvés');
    const un = commandesAnnuaire.resoudreContact('zoe');
    attendre(un.statut === 'un' && un.contact.prenom === 'Zoe', 'un seul Zoe trouvé');
  });

  test('Commande annuaire UI : mail sans message, jamais « undefined » dans le corps', () => {
    annuaire.creerContact({ prenom: 'Milo', nom: 'FICTIF', mail: 'milo.fictif@exemple.test' });
    const urls = [];
    commandeAnnuaireUI._definirNaviguer(url => urls.push(url));
    commandeAnnuaireUI.traiter({ action: 'mail', nom: 'Milo FICTIF', message: '' });
    document.querySelector('.commande-annuaire-boutons button').click();
    attendreEgal(urls.length, 1, 'une navigation déclenchée');
    attendre(!urls[0].includes('undefined'), 'jamais « undefined » dans le lien mailto');
    attendre(urls[0].includes('body='), 'le paramètre body est toujours présent');
    attendre(urls[0].startsWith('mailto:milo.fictif%40exemple.test?body='), 'lien mailto correct');
  });

  test('Commande annuaire UI : plusieurs correspondances, bouton Annuler ferme sans rien faire', () => {
    annuaire.creerContact({ prenom: 'Milo', nom: 'FICTIF', telephone: '0600000010' });
    annuaire.creerContact({ prenom: 'Milovan', nom: 'FICTIF', telephone: '0600000011' });
    const urls = [];
    commandeAnnuaireUI._definirNaviguer(url => urls.push(url));
    commandeAnnuaireUI.traiter({ action: 'appel', nom: 'Milo' });
    const dialogue = document.getElementById('commande-annuaire');
    attendre(dialogue.open, 'écran de choix ouvert');
    const annuler = Array.from(dialogue.querySelectorAll('button')).find(b => b.textContent === 'Annuler');
    attendre(Boolean(annuler), 'bouton Annuler présent');
    annuler.click();
    attendre(!dialogue.open, 'écran fermé après Annuler');
    attendreEgal(urls.length, 0, 'aucune navigation déclenchée');
  });

  test('Annuaire : fusion sans perte, dernière modification gagne, historiques combinés', () => {
    const m = annuaireIsolee();
    const local = m.instance.creerContact({ prenom: 'Jardinier FICTIF', telephone: '0600000001' });
    m.instance.marquerEnvoye();
    const distantPlusRecent = {
      contacts: [{
        id: local.id, prenom: 'Jardinier FICTIF', nom: '', type: '', role: '', lien: '', surnoms: '', coordonnees: '',
        telephone: '0600000002', mail: '', domaine: '', note_ia: '', anniversaire: '', adresse: '', telephone2: '',
        mail2: '', fonction: '', site_web: '', note: '',
        supprime_le: '', modifie_le: '2999-01-01T00:00:00.000Z',
        historique: [...local.historique, { champ: 'telephone', ancienne: '0600000001', nouvelle: '0600000002', date: '2999-01-01T00:00:00.000Z' }]
      }, {
        id: 'C-distant-nouveau', prenom: 'Voisin FICTIF', nom: '', type: '', role: '', lien: '', surnoms: '', coordonnees: '',
        telephone: '', mail: '', domaine: '', note_ia: '', anniversaire: '', adresse: '', telephone2: '', mail2: '',
        fonction: '', site_web: '', note: '', supprime_le: '', modifie_le: '2999-01-01T00:00:00.000Z', historique: []
      }]
    };
    m.instance.fusionner(distantPlusRecent);
    attendreEgal(m.instance.trouver(local.id).telephone, '0600000002', 'valeur distante plus récente retenue');
    attendreEgal(m.instance.trouver(local.id).historique.length, 2, 'historique fusionné sans doublon');
    attendre(m.instance.tous().some(c => c.id === 'C-distant-nouveau'), 'nouveau contact distant ajouté');
    const distantPlusAncien = {
      contacts: [{
        id: local.id, prenom: 'Jardinier FICTIF', nom: '', type: '', role: '', lien: '', surnoms: '', coordonnees: '',
        telephone: '0000000000', mail: '', domaine: '', note_ia: '', anniversaire: '', adresse: '', telephone2: '',
        mail2: '', fonction: '', site_web: '', note: '', supprime_le: '', modifie_le: '2000-01-01T00:00:00.000Z', historique: []
      }]
    };
    m.instance.fusionner(distantPlusAncien);
    attendreEgal(m.instance.trouver(local.id).telephone, '0600000002', 'valeur locale plus récente gardée, rien d’écrasé');
    attendre(!m.instance.aEnvoyer(), 'fusion ne marque rien à renvoyer');
  });

  test('Annuaire : migration automatique d’un ancien contact (ancien « nom », ancien « surnom » singulier)', () => {
    const m = annuaireIsolee();
    m.memoire.setItem('cap_annuaire_v1', JSON.stringify({
      contacts: [{
        id: 'C-ancien1', nom: 'Dupont FICTIF', surnom: 'Dudu FICTIF', telephone: '0600000000', adresse: '12 rue FICTIF',
        mail: 'dupont.fictif@exemple.test', anniversaire: '01-01', note: 'note ancienne FICTIF',
        supprime_le: '', modifie_le: '2026-01-01T00:00:00.000Z',
        historique: [{ champ: 'créé', ancienne: '', nouvelle: 'Dupont FICTIF', date: '2026-01-01T00:00:00.000Z' },
          { champ: 'surnom', ancienne: '', nouvelle: 'Dudu FICTIF', date: '2026-01-01T00:00:01.000Z' }]
      }]
    }));
    m.instance.recharger();
    const migre = m.instance.trouver('C-ancien1');
    attendreEgal(migre.prenom, '', 'prénom vide après migration, non deviné');
    attendreEgal(migre.nom, 'Dupont FICTIF', 'ancien nom complet recopié dans Nom, rien perdu');
    attendreEgal(migre.surnoms, 'Dudu FICTIF', 'ancien surnom singulier recopié dans surnoms');
    attendreEgal(migre.telephone, '0600000000', 'téléphone conservé');
    attendreEgal(migre.adresse, '12 rue FICTIF', 'adresse conservée');
    attendreEgal(migre.mail, 'dupont.fictif@exemple.test', 'mail conservé');
    attendreEgal(migre.anniversaire, '01-01', 'anniversaire conservé');
    attendreEgal(migre.note, 'note ancienne FICTIF', 'note conservée');
    attendreEgal(migre.historique.length, 2, 'historique entièrement conservé, rien perdu');
    attendreEgal(migre.historique.map(e => e.champ), ['créé', 'surnoms'], 'champ « surnom » re-cadré en « surnoms »');
    attendreEgal(migre.telephone2, '', 'nouveaux champs vides par défaut');
    attendreEgal(migre.type, '', 'nouveaux champs vides par défaut');
  });

  await testAsync('Google Sheets annuaire : onglet absent puis créé, lecture et écriture sans rien effacer', async c => {
    c.localStorage.setItem('cap_google_fichier_v1', 'tableau-fictif');
    let ongletsPresents = ['Tâches'];
    let lignesAnnuaire = [];
    c.repondre = async r => {
      const chemin = decodeURIComponent(r.url.pathname);
      if (r.methode === 'GET' && chemin === '/drive/v3/files/tableau-fictif') return reponseGoogle({ id: 'tableau-fictif', trashed: false });
      if (r.methode === 'GET' && chemin === '/v4/spreadsheets/tableau-fictif') return reponseGoogle({ sheets: ongletsPresents.map(title => ({ properties: { title } })) });
      if (r.methode === 'GET' && chemin.includes('Annuaire')) return reponseGoogle({ values: lignesAnnuaire });
      if (r.methode === 'POST') return reponseGoogle({});
      throw new Error(`Requête inattendue : ${r.url}`);
    };
    const entetesAnnuaireFictif = ['Identifiant', 'Prénom', 'Nom', 'Type', 'Rôle', 'Lien avec Max', 'Appellations et surnoms',
      'Coordonnées', 'Téléphone', 'Mail', 'Domaine', 'Note pour IA', 'Date de naissance / anniversaire', 'Adresse postale',
      'Deuxième téléphone', 'Deuxième mail', 'Fonction / titre', 'Site web', 'Note', 'Supprimé le', 'Modifié le', 'Historique'];
    const sheets = c.sheets();
    await sheets.trouverOuCreer();
    const lecture = await sheets.lireAnnuaire();
    attendreEgal(lecture.manquant, true, 'onglet Annuaire absent au départ');
    attendreEgal(lecture.contacts, [], 'rien à lire');
    const contact = {
      id: 'C-fictif1', prenom: 'Dupont', nom: 'FICTIF', type: '', role: '', lien: '', surnoms: '', coordonnees: '',
      telephone: '0600000000', mail: '', domaine: '', note_ia: '', anniversaire: '', adresse: '', telephone2: '', mail2: '',
      fonction: '', site_web: '', note: '', supprime_le: '', modifie_le: 'x',
      historique: [{ champ: 'créé', ancienne: '', nouvelle: 'Dupont FICTIF', date: 'x' }]
    };
    await sheets.ecrireAnnuaire({ contacts: [contact] });
    const ajoutOnglet = c.requetes.find(r => r.url.pathname.endsWith('tableau-fictif:batchUpdate')).corps.requests;
    attendreEgal(ajoutOnglet.map(a => a.addSheet.properties.title), ['Annuaire'], 'onglet Annuaire ajouté');
    const ecriture = c.requetes.find(r => r.url.pathname.endsWith('/values:batchUpdate')).corps;
    attendreEgal(ecriture.valueInputOption, 'RAW', 'écriture brute');
    attendreEgal(ecriture.data[0].values[0], entetesAnnuaireFictif, 'entêtes écrites');
    attendreEgal(ecriture.data[0].values[1],
      ['C-fictif1', 'Dupont', 'FICTIF', '', '', '', '', '', '0600000000', '', '', '', '', '', '', '', '', '', '', '', 'x', JSON.stringify(contact.historique)],
      'ligne du contact écrite, rien de supprimé');
    ongletsPresents = [...ongletsPresents, 'Annuaire'];
    lignesAnnuaire = ecriture.data[0].values;
    const relue = await sheets.lireAnnuaire();
    attendreEgal(relue.manquant, false, 'onglet maintenant présent');
    attendreEgal(relue.contacts.length, 1, 'un contact relu');
    attendreEgal(relue.contacts[0].historique, contact.historique, 'historique JSON relu sans perte');
    lignesAnnuaire = [['Identifiant', 'Nom'], ['C-fictif1', 'Dupont FICTIF']];
    await attendreRejet(() => sheets.lireAnnuaire(), 'illisibles');
    lignesAnnuaire = [entetesAnnuaireFictif, ['C-fictif1', 'Dupont', 'FICTIF', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'x', 'pas-du-json']];
    await attendreRejet(() => sheets.lireAnnuaire(), 'illisible');
  });

  await testAsync('Google Sheets annuaire : ancien onglet (11 colonnes) lu et migré, rien perdu', async c => {
    c.localStorage.setItem('cap_google_fichier_v1', 'tableau-fictif');
    const historiqueAncien = [{ champ: 'créé', ancienne: '', nouvelle: 'Dupont FICTIF', date: 'x' }];
    const lignesAnnuaireAncien = [
      ['Identifiant', 'Nom', 'Surnom', 'Téléphone', 'Adresse', 'Mail', 'Anniversaire', 'Note', 'Supprimé le', 'Modifié le', 'Historique'],
      ['C-ancien1', 'Dupont FICTIF', 'Dudu FICTIF', '0600000000', '12 rue FICTIF', 'dupont.fictif@exemple.test', '01-01', 'note FICTIF', '', 'x', JSON.stringify(historiqueAncien)]
    ];
    c.repondre = async r => {
      const chemin = decodeURIComponent(r.url.pathname);
      if (r.methode === 'GET' && chemin === '/drive/v3/files/tableau-fictif') return reponseGoogle({ id: 'tableau-fictif', trashed: false });
      if (r.methode === 'GET' && chemin === '/v4/spreadsheets/tableau-fictif') return reponseGoogle({ sheets: [{ properties: { title: 'Annuaire' } }] });
      if (r.methode === 'GET' && chemin.includes('Annuaire')) return reponseGoogle({ values: lignesAnnuaireAncien });
      throw new Error(`Requête inattendue : ${r.url}`);
    };
    const sheets = c.sheets();
    await sheets.trouverOuCreer();
    const lecture = await sheets.lireAnnuaire();
    attendreEgal(lecture.manquant, false, 'onglet présent');
    attendreEgal(lecture.ancien, true, 'ancien format détecté');
    attendreEgal(lecture.contacts.length, 1, 'un contact lu');
    const contact = lecture.contacts[0];
    attendreEgal(contact.nom, 'Dupont FICTIF', 'ancien nom complet recopié, rien perdu');
    attendreEgal(contact.surnoms, 'Dudu FICTIF', 'ancien surnom recopié dans surnoms');
    attendreEgal(contact.telephone, '0600000000', 'téléphone conservé');
    attendreEgal(contact.adresse, '12 rue FICTIF', 'adresse conservée');
    attendreEgal(contact.note, 'note FICTIF', 'note conservée');
    attendreEgal(contact.historique, historiqueAncien, 'historique conservé sans perte');
    attendreEgal(contact.telephone2, '', 'nouveaux champs vides par défaut');
  });

  await testAsync('Synchro annuaire : lit, fusionne, écrit, puis seulement après un changement', async c => {
    const memoire = espaceMemoire();
    const a = annuaireIsolee(memoire, c.window);
    const ecritures = [];
    let echec = false;
    const contactDistant = {
      id: 'C-distant', prenom: 'Distant FICTIF', nom: '', type: '', role: '', lien: '', surnoms: '', coordonnees: '',
      telephone: '', mail: '', domaine: '', note_ia: '', anniversaire: '', adresse: '', telephone2: '', mail2: '',
      fonction: '', site_web: '', note: '', supprime_le: '', modifie_le: 'x', historique: []
    };
    const fauxSheets = {
      trouverOuCreer: async () => ({ id: 'tableau-fictif', cree: false }),
      lireAnnuaire: async () => ({ contacts: [contactDistant] }),
      ecrireAnnuaire: async donnees => {
        if (echec) throw new Error('panne simulée');
        ecritures.push(donnees);
      }
    };
    const synchro = objetIsole(SOURCE_SYNCHRO_ANNUAIRE, 'synchroAnnuaire', {
      googleConnexion: c.googleConnexion, navigator: c.navigator, googleSheets: fauxSheets, annuaire: a.instance,
      localStorage: memoire, window: c.window, setInterval: c.setInterval
    });
    attendreEgal(await synchro.synchroniser(), true, 'première synchronisation');
    attendreEgal(ecritures.length, 1, 'une écriture');
    attendre(ecritures[0].contacts.some(contact => contact.id === 'C-distant') && a.instance.tous().some(c2 => c2.id === 'C-distant'), 'fusion absente');
    attendreEgal(await synchro.synchroniser(), false, 'rien à refaire');
    attendreEgal(ecritures.length, 1, 'pas de réécriture inutile');
    a.instance.creerContact({ prenom: 'Nouveau FICTIF' });
    await synchro.synchroniser();
    attendreEgal(ecritures.length, 2, 'changement envoyé');
    attendre(ecritures[1].contacts.some(contact => contact.prenom === 'Nouveau FICTIF'), 'nouveau contact absent de l’écriture');
    echec = true;
    a.instance.creerContact({ prenom: 'Perdu FICTIF' });
    attendreEgal(await synchro.synchroniser(), false, 'échec signalé sans exception');
    attendre(synchro.erreur().includes('panne simulée'), `erreur rapportée : ${synchro.erreur()}`);
    attendre(a.instance.aEnvoyer(), 'un échec garde la marque « à envoyer »');
  });

  await testAsync('Google Sheets listes : lecture, ancien entête, onglet Catégories ajouté sans rien effacer', async c => {
    c.localStorage.setItem('cap_google_fichier_v1', 'tableau-fictif');
    let ongletsPresents = ['Tâches', 'Étapes par défaut', 'Phrases du clavier'];
    let lignesModeles = [['Modèle', 'Étape'], ['Roman', 'Relire'], ['Roman', 'Corriger'], ['Album', 'Mixer']];
    c.repondre = async r => {
      const chemin = decodeURIComponent(r.url.pathname);
      if (r.methode === 'GET' && chemin === '/drive/v3/files/tableau-fictif') return reponseGoogle({ id: 'tableau-fictif', trashed: false });
      if (r.methode === 'GET' && chemin === '/v4/spreadsheets/tableau-fictif') return reponseGoogle({ sheets: ongletsPresents.map(title => ({ properties: { title } })) });
      if (r.methode === 'GET' && chemin.includes('Étapes par défaut')) return reponseGoogle({ values: lignesModeles });
      if (r.methode === 'GET' && chemin.includes('Catégories')) return reponseGoogle({ values: [] });
      if (r.methode === 'POST') return reponseGoogle({});
      throw new Error(`Requête inattendue : ${r.url}`);
    };
    const sheets = c.sheets();
    await sheets.trouverOuCreer();
    const lecture = await sheets.lireListes();
    attendreEgal(lecture.modeles.map(m => [m.nom, m.etapes]), [['Roman', ['Relire', 'Corriger']], ['Album', ['Mixer']]], 'modèles lus');
    attendreEgal(lecture.manquants, ['Catégories'], 'onglet manquant repéré');
    await sheets.ecrireListes({
      modeles: [{ nom: 'Roman', etapes: ['Relire'], retiree_le: '2026-10-29', modifie_le: 'x' }],
      categories: [{ nom: 'À trier', parente: '', couleur: '#6f6f6f', retiree_le: '', modifie_le: '' }]
    });
    const ajoutOnglet = c.requetes.find(r => r.url.pathname.endsWith('tableau-fictif:batchUpdate')).corps.requests;
    attendreEgal(ajoutOnglet.map(a => a.addSheet.properties.title), ['Catégories'], 'onglet Catégories ajouté');
    const ecriture = c.requetes.find(r => r.url.pathname.endsWith('/values:batchUpdate')).corps;
    attendreEgal(ecriture.valueInputOption, 'RAW', 'écriture brute');
    attendreEgal(ecriture.data[0].values, [['Modèle', 'Étape', 'Retirée le', 'Modifiée le'], ['Roman', 'Relire', '2026-10-29', 'x'], ['', '', '', ''], ['', '', '', '']], 'lignes anciennes recouvertes, aucune suppression');
    attendreEgal(ecriture.data[1].values, [['Catégorie', 'Sous-catégorie de', 'Couleur', 'Retirée le', 'Modifiée le', 'Ordre'], ['À trier', '', '#6f6f6f', '', '', '']], 'catégories écrites');
    ongletsPresents = [...ongletsPresents, 'Catégories'];
    lignesModeles = [['Nom', 'Truc'], ['Roman', 'Relire']];
    const avant = c.requetes.filter(r => r.methode === 'POST').length;
    await attendreRejet(() => sheets.ecrireListes({ modeles: [], categories: [] }), 'illisibles');
    lignesModeles = [['Modèle', 'Étape'], ['Roman', 42]];
    await attendreRejet(() => sheets.ecrireListes({ modeles: [], categories: [] }), 'illisible');
    attendreEgal(c.requetes.filter(r => r.methode === 'POST').length, avant, 'aucune écriture sur un tableau illisible');
  });

  await testAsync('Synchro listes : lit, fusionne, écrit, puis seulement après un changement', async c => {
    const memoire = espaceMemoire();
    const l = listesIsolees([], { Roman: ['Relire'] }, memoire, c.window);
    const ecritures = [];
    let echec = false;
    const fauxSheets = {
      trouverOuCreer: async () => ({ id: 'tableau-fictif', cree: false }),
      lireListes: async () => ({ modeles: [], categories: [{ nom: 'Sport', parente: '', couleur: '', retiree_le: '', modifie_le: '' }] }),
      ecrireListes: async donnees => {
        if (echec) throw new Error('panne simulée');
        ecritures.push(donnees);
      }
    };
    const synchro = objetIsole(SOURCE_SYNCHRO_LISTES, 'synchroListes', {
      googleConnexion: c.googleConnexion, navigator: c.navigator, googleSheets: fauxSheets, listesChoix: l.instance,
      localStorage: memoire, window: c.window, setInterval: c.setInterval, Date: c.Date
    });
    attendreEgal(await synchro.synchroniser(), true, 'première synchronisation');
    attendreEgal(ecritures.length, 1, 'une écriture');
    attendre(ecritures[0].categories.some(cat => cat.nom === 'Sport') && l.instance.categories().includes('Sport'), 'fusion absente');
    attendreEgal(await synchro.synchroniser(), false, 'rien à refaire');
    attendreEgal(ecritures.length, 1, 'pas de réécriture inutile');
    l.instance.ajouterCategorie('Voyage');
    await synchro.synchroniser();
    attendreEgal(ecritures.length, 2, 'changement envoyé');
    attendre(ecritures[1].categories.some(cat => cat.nom === 'Voyage'), 'Voyage absent');
    echec = true;
    l.instance.ajouterCategorie('Cuisine');
    await synchro.synchroniser();
    attendre(l.instance.aEnvoyer(), 'changement perdu après une panne');
    attendre(synchro.erreur().includes('panne simulée'), 'erreur non gardée');
    echec = false;
    attendreEgal(await synchro.synchroniser(), false, 'nouvel essai trop tôt');
    c.maintenant += 61000;
    attendreEgal(await synchro.synchroniser(), true, 'nouvel essai après une minute');
    attendre(ecritures.at(-1).categories.some(cat => cat.nom === 'Cuisine') && !l.instance.aEnvoyer(), 'Cuisine pas envoyée');
    c.navigator.onLine = false;
    l.instance.ajouterCategorie('Hors ligne');
    const nombre = ecritures.length;
    attendreEgal(await synchro.synchroniser(), false, 'hors ligne');
    attendreEgal(ecritures.length, nombre, 'aucun envoi hors ligne');
    attendre(l.instance.aEnvoyer(), 'changement hors ligne gardé');
  });

  test('Glisser et report : droite coche, gauche reporte à demain, Annuler remet', () => {
    const tache = tacheInterface('FICTIF glisser interface');
    const glisser = ecart => {
      const ligne = document.getElementById('liste-taches').querySelector(`[data-tache="${tache.id}"]`);
      ligne.getBoundingClientRect = () => ({ width: 300 });
      Object.defineProperty(ligne, 'offsetWidth', { configurable: true, value: 300 });
      const options = { bubbles: true, pointerId: 7, pointerType: 'touch', clientY: 10 };
      ligne.dispatchEvent(new PointerEvent('pointerdown', { ...options, clientX: 150 }));
      ligne.dispatchEvent(new PointerEvent('pointermove', { ...options, clientX: 150 + ecart / 2 }));
      ligne.dispatchEvent(new PointerEvent('pointermove', { ...options, clientX: 150 + ecart }));
      ligne.dispatchEvent(new PointerEvent('pointerup', { ...options, clientX: 150 + ecart }));
    };
    const demain = new Date();
    demain.setDate(demain.getDate() + 1);
    const texteDemain = `${demain.getFullYear()}-${String(demain.getMonth() + 1).padStart(2, '0')}-${String(demain.getDate()).padStart(2, '0')}`;
    const ancienne = tache.echeance;
    glisser(-120);
    attendreEgal(tache.echeance, texteDemain, 'échéance demain');
    attendre(!tache.fait, 'report ne coche pas');
    let annuler = document.querySelector('#statut .annuler-dictee');
    attendre(annuler, 'pas de bouton Annuler après report');
    annuler.click();
    attendreEgal(tache.echeance, ancienne, 'report annulé');
    glisser(40);
    attendre(!tache.fait, 'petit glisser ne coche pas');
    glisser(120);
    attendre(tache.fait, 'glisser à droite ne coche pas');
    annuler = document.querySelector('#statut .annuler-dictee');
    attendre(annuler, 'pas de bouton Annuler après coche');
    annuler.click();
    attendre(!tache.fait, 'coche non annulée');
    attendre(TACHES.includes(tache), 'tâche perdue');
  });

  test('Voix : « Reporte ça à demain » reporte la dernière tâche ouverte', () => {
    const tache = tacheInterface('FICTIF voix interface');
    const nombre = TACHES.length;
    const ancienne = tache.echeance;
    document.querySelector(`[data-tache="${tache.id}"] .options-tache`).click();
    document.getElementById('menu-tache').close();
    document.getElementById('ouvrir-clavier').click();
    document.getElementById('saisie-demande').value = 'Reporte ça à demain';
    document.getElementById('formulaire-demande').requestSubmit();
    const demain = new Date();
    demain.setDate(demain.getDate() + 1);
    attendreEgal(tache.echeance, `${demain.getFullYear()}-${String(demain.getMonth() + 1).padStart(2, '0')}-${String(demain.getDate()).padStart(2, '0')}`, 'tâche ouverte reportée');
    attendreEgal(TACHES.length, nombre, 'aucune tâche créée');
    if (document.getElementById('clavier').open) document.getElementById('clavier').close();
    document.querySelector('#statut .annuler-dictee').click();
    attendreEgal(tache.echeance, ancienne, 'report vocal annulé');
    const proposeRdv = traiterDemande({ texte: 'Ajoute-moi un rendez-vous à 11h45 aujourd\'hui, intitulé test, rappel dix minutes avant', source: 'micro', agenda_disponible: true });
    attendre(proposeRdv.type === 'proposition' && proposeRdv.message.includes('à 11 h 45') && proposeRdv.message.endsWith('c’est bien ça ?'), `rendez-vous redit : ${proposeRdv.message}`);
    attendre(!document.getElementById('fiche-rendez-vous').open, 'la fiche rendez-vous ne s’ouvre pas toute seule');
    const corrige = traiterDemande({ texte: 'Non, à 16h', source: 'micro', agenda_disponible: true });
    attendre(corrige.type === 'proposition' && corrige.message.includes('à 16 h') && !corrige.message.includes('11 h 45'), `correction reformulée : ${corrige.message}`);
    attendreEgal(traiterDemande({ texte: 'Non', source: 'micro', agenda_disponible: true }).message, 'D’accord, je n’inscris rien dans l’agenda.', 'non : rien inscrit');
    attendreEgal(TACHES.length, nombre, 'rendez-vous connecté : aucune tâche');
    const sansHeure = actionsCap.preparerProposition('proposer_rendez_vous', { titre: 'Garagiste FICTIF', date: '2027-01-11', lieu: 'rue FICTIVE' });
    attendreEgal([sansHeure.manque, sansHeure.texte], ['heure', 'À quelle heure ?'], 'heure manquante : une seule question');
    const complete = actionsCap.completerProposition(sansHeure, 'à 15h30');
    attendreEgal(actionsCap.preparerProposition('proposer_rendez_vous', complete).texte,
      'Rendez-vous « Garagiste FICTIF » le lundi 11 janvier 2027 à 15 h 30, rue FICTIVE, c’est bien ça ?', 'jour de la semaine calculé par Cap');
    const deuxDates = actionsCap.preparerProposition('proposer_rendez_vous', { titre: 'FICTIF', heure: '10:00', choix_date: ['2027-01-07', '2027-01-14'] });
    attendre(deuxDates.manque === 'date' && deuxDates.texte.includes(' ou le '), `deux dates possibles : ${deuxDates.texte}`);
    attendreEgal(actionsCap.completerProposition(deuxDates, 'le 14').date, '2027-01-14', 'date choisie');
    attendreEgal([actionsCap.heureDite('midi'), actionsCap.heureDite('9 heures 05'), actionsCap.heureDite('rien')], ['12:00', '09:05', ''], 'heures dites');
    cerveau.proposer({ type: 'action', action: 'proposer_rendez_vous', parametres: { titre: 'FICTIF', date: '2027-01-11', heure: '10:00' } });
    attendreEgal(traiterDemande({ texte: 'annule', source: 'micro' }).message, 'D’accord, je n’inscris rien dans l’agenda.', '« annule » pendant une proposition : rien inscrit');
    attendre(!cerveau.propositionEnAttente(), 'proposition oubliée');
    const horsLigne = traiterDemande({ texte: 'rendez-vous demain à 9h FICTIF', source: 'micro', agenda_disponible: false });
    attendre(horsLigne.type === 'tache' && horsLigne.message.includes('PAS dans l\'agenda'), 'message honnête hors connexion');
    abandonner(horsLigne.tache.id);
    attendreEgal(tache.echeance, ancienne, 'traiterDemande seul ne modifie pas');
  });

  await testAsync('Dernières actions : zone cachée si vide', async c => {
    const ui = preparerInterface(c);
    attendre(ui.parId('dernieres-actions').hidden, 'zone vide visible');
  });

  await testAsync('Dernières actions : cinq lignes, heure, hier et date courte', async c => {
    const aujourdHui = new Date();
    const hier = new Date();
    hier.setDate(hier.getDate() - 1);
    const ancien = new Date();
    ancien.setDate(ancien.getDate() - 3);
    const dates = [aujourdHui, hier, ancien, aujourdHui, aujourdHui, aujourdHui];
    c.localStorage.setItem('cap_journal_actions_v1', JSON.stringify(dates.map((date, index) => ({
      heure: date.toISOString(), type: 'ajout', texte: `FICTIF ${index}`
    }))));
    const ui = preparerInterface(c);
    const lignes = [...ui.parId('liste-actions').children];
    attendreEgal(lignes.length, 5, 'limite affichage');
    attendre(/\d{2}:\d{2} · Ajouté : FICTIF 0/.test(lignes[0].textContent), 'heure locale');
    attendre(lignes[1].textContent.includes('hier'), 'hier absent');
    attendre(lignes[2].textContent.includes(new Intl.DateTimeFormat('fr-FR', { day: '2-digit', month: '2-digit' }).format(ancien)), 'date courte absente');
  });

  await testAsync('Recherche accueil : options futures grisées et inaccessibles', async c => {
    const ui = preparerInterface(c);
    const select = ui.parId('source-recherche');
    // 09/11/2026 (accord de Max, partie 2 A) : menu renommé, « Tout » par défaut. Avant : ['Tâches', 'Rendez-vous',
    // 'Gmail (plus tard)', 'Drive (plus tard)', 'Archives perso (plus tard)', 'Mémoire perso (plus tard)'], Tâches par défaut.
    attendreEgal([...select.options].map(option => option.textContent),
      ['Tout', 'Tâches', 'Rendez-vous', 'Personnes', 'Notes (plus tard)', 'Listes (plus tard)', 'Documents (plus tard)', 'Musique (plus tard)', 'Mails (plus tard)', 'Archives (plus tard)', 'Biographie (plus tard)'], 'options');
    attendreEgal(select.selectedIndex, 0, 'choix initial');
    attendreEgal(select.value, 'tout', '« Tout » pas par défaut');
    attendre([...select.options].slice(4).every(option => option.disabled) && [...select.options].slice(0, 4).every(option => !option.disabled), 'option future accessible');
    const style = ui.cadre.contentWindow.getComputedStyle(select.options[4]);
    attendre(style.color !== ui.cadre.contentWindow.getComputedStyle(select.options[0]).color, 'options non grisées');
    const champ = ui.parId('saisie-recherche');
    attendreEgal([champ.type, champ.getAttribute('enterkeyhint'), champ.autocomplete], ['search', 'search', 'off'], 'champ mobile');
    attendre(Boolean(champ.getAttribute('aria-label')), 'étiquette absente');
  });

  await testAsync('Recherche accueil : résultats à chaque input, vide et message exact', async c => {
    const ui = preparerInterface(c);
    const champ = ui.parId('saisie-recherche');
    const liste = ui.parId('resultats-recherche');
    ui.parId('source-recherche').value = 'taches'; // 09/11/2026 : « Tout » est par défaut ; ce test vise « Tâches » (comme avant)
    attendreEgal(liste.textContent, '', 'texte à vide');
    champ.value = 'FICTIF zz introuvable';
    champ.dispatchEvent(new Event('input'));
    attendreEgal(liste.textContent.trim(), 'Rien trouvé dans Tâches', 'message exact');
    champ.value = c.TACHES[0].intitule;
    champ.dispatchEvent(new Event('input'));
    attendre(liste.querySelector('button'), 'résultat sans validation absent');
    champ.value = '';
    champ.dispatchEvent(new Event('input'));
    attendreEgal(liste.textContent, '', 'effacement');
    ui.parId('source-recherche').value = 'rendez-vous'; // 09/11/2026 : par sa valeur (avant : options[1], l'ordre a changé)
    champ.value = 'introuvable';
    ui.parId('source-recherche').dispatchEvent(new Event('change'));
    attendreEgal(liste.textContent.trim(), 'Rien trouvé dans Rendez-vous', 'changement source');
  });

  await testAsync('Recherche accueil : trente résultats, autres et tâches faites', async c => {
    c.TACHES.splice(0, c.TACHES.length, ...Array.from({ length: 36 }, (_, index) => ({
      ...TACHES_FICTIVES[0], id: `FICTIF-${index}`, intitule: `FICTIF résultat ${index}`, fait: index === 0, abandonnee_le: ''
    })));
    const ui = preparerInterface(c);
    ui.parId('saisie-recherche').value = 'resultat';
    ui.parId('saisie-recherche').dispatchEvent(new Event('input'));
    attendreEgal(ui.parId('resultats-recherche').querySelectorAll('button').length, 30, 'limite');
    attendre(ui.parId('resultats-recherche').textContent.includes('et 6 autres…'), 'compteur');
    attendre(ui.parId('resultats-recherche').querySelector('button').textContent.toLowerCase().includes('fait'), 'statut fait');
  });

  await testAsync('Recherche accueil : toucher tâche ouvre, défile et surligne deux secondes', async c => {
    const ui = preparerInterface(c);
    const champ = ui.parId('saisie-recherche');
    champ.value = c.TACHES[0].intitule;
    champ.dispatchEvent(new Event('input'));
    let defile = false;
    const prototype = ui.cadre.contentWindow.Element.prototype;
    const ancienDefilement = prototype.scrollIntoView;
    prototype.scrollIntoView = function () { if (this.matches('li')) defile = true; };
    try {
      ui.parId('resultats-recherche').querySelector('button').click();
    } finally {
      prototype.scrollIntoView = ancienDefilement;
    }
    const ligne = ui.doc.getElementById(`tache-${c.TACHES[0].id}`).closest('li');
    attendre(!ui.parId('ecran-complet').hidden, 'vue complète fermée');
    attendreEgal(ui.parId('ecran-complet').dataset.vue, 'tout', 'grande liste ouverte');
    attendre(defile, 'pas de défilement');
    attendre(ligne.classList.contains('surbrillance-recherche'), 'surbrillance absente');
    const delai = [...c.delais.values()].find(delai => delai.delai === 2000);
    attendre(delai, 'durée incorrecte');
    delai.rappel();
    attendre(!ligne.classList.contains('surbrillance-recherche'), 'surbrillance persistante');
  });

  await testAsync('Recherche accueil : rendez-vous locaux, date et heure, accès sans réseau', async c => {
    c.localStorage.setItem('cap_google_rendezvous_v1', JSON.stringify({ rendezvous: [
      { titre: 'FICTIF Répétition', lieu: 'Théâtre', description: 'Éclairage', date: '2030-01-10', heure: '14:32' }
    ] }));
    const ui = preparerInterface(c);
    ui.parId('source-recherche').value = 'rendez-vous'; // 09/11/2026 : par sa valeur (avant : selectedIndex = 1, l'ordre a changé)
    ui.parId('saisie-recherche').value = 'theatre';
    ui.parId('saisie-recherche').dispatchEvent(new Event('input'));
    const resultat = ui.parId('resultats-recherche').querySelector('button');
    attendre(resultat && resultat.textContent.includes('14:32') && resultat.textContent.includes('10'), 'date et heure absentes');
    resultat.click();
    attendre(ui.parId('fiche-rendez-vous').open, 'fiche non ouverte');
    attendre(ui.parId('cartes-rdv').textContent.includes('Théâtre'), 'rendez-vous non montré');
    attendreEgal(c.requetes.length, 0, 'recherche déclenche du réseau');
  });

  await testAsync('Recherche accueil : glissements ignorés depuis barre et liste', async c => {
    const ui = preparerInterface(c);
    ui.parId('saisie-recherche').value = 'introuvable';
    ui.parId('saisie-recherche').dispatchEvent(new Event('input'));
    for (const cible of [ui.parId('zone-recherche'), ui.parId('saisie-recherche'), ui.parId('resultats-recherche'), ui.parId('resultats-recherche').firstElementChild]) {
      glisser(ui, cible, 100, 300, 100, 180);
      attendre(ui.parId('ecran-complet').hidden, 'geste ouvre depuis la recherche');
    }
  });

  await testAsync('Recherche accueil : texte bloque reconnexion silencieuse', async c => {
    c.localStorage.setItem('cap_google_deja_connecte_v1', 'oui');
    const ui = preparerInterface(c, { avant(ui) { ui.parId('saisie-recherche').value = 'FICTIF en cours'; } });
    attendreEgal(c.redirections.length, 0, 'redirection pendant recherche');
    ui.visibilite(false);
    attendreEgal(c.redirections.length, 0, 'redirection au retour');
    ui.parId('saisie-recherche').value = '';
    ui.visibilite(false);
    attendreEgal(c.redirections.length, 1, 'reconnexion non rétablie après effacement');
  });

  await testAsync('Recherche accueil : aucun débordement avec résultats à 360 × 560', async c => {
    c.TACHES.splice(0, c.TACHES.length, ...Array.from({ length: 35 }, (_, index) => ({
      ...TACHES_FICTIVES[0], id: `FICTIF-${index}`, intitule: `FICTIF ${'long'.repeat(80)} ${index}`, abandonnee_le: ''
    })));
    const ui = preparerInterface(c, { largeur: 360, hauteur: 560 });
    ui.parId('basculer-vue').click(); // étape A : la recherche est dans « Chercher »
    transitionEcrans.terminer(ui.doc); // 08/11/2026 : mesures prises APRÈS la transition douce (transition_ecrans.js)
    ui.parId('saisie-recherche').value = 'fictif';
    ui.parId('saisie-recherche').dispatchEvent(new Event('input'));
    attendre(ui.doc.documentElement.scrollWidth <= 360 && ui.doc.body.scrollWidth <= 360, 'débordement horizontal');
    attendre(ui.doc.documentElement.scrollHeight <= 560 && ui.doc.body.scrollHeight <= 560, 'débordement vertical');
    const liste = ui.parId('resultats-recherche');
    attendre(liste.scrollHeight > liste.clientHeight && liste.clientHeight > 0, 'résultats non défilables');
    attendre(liste.getBoundingClientRect().bottom <= 560, 'résultats hors écran');
    attendre(liste.getBoundingClientRect().bottom <= ui.doc.querySelector('.barre-recherche').getBoundingClientRect().top, 'résultats pas au-dessus de la barre');
    attendre(liste.getBoundingClientRect().top >= ui.doc.querySelector('header.horloge').getBoundingClientRect().bottom, 'résultats sur la date');
    for (const id of ['ouvrir-clavier', 'ajouter', 'saisie-recherche', 'source-recherche']) {
      const rect = ui.parId(id).getBoundingClientRect();
      attendre(rect.top >= 0 && rect.bottom <= 560 && rect.height >= 48, `${id} hors écran ou trop petit`);
    }
  });

  await testAsync('Google Agenda : copie locale conserve lieu et description pour la recherche', async c => {
    c.localStorage.setItem('cap_google_agenda_v1', 'agenda-fictif');
    c.repondre = async r => reponseGoogle(r.url.pathname.endsWith('/events') ? { items: [
      { summary: 'FICTIF rendez-vous', location: 'Théâtre FICTIF', description: 'Éclairage FICTIF', start: { date: '2030-01-10' } }
    ] } : { id: 'agenda-fictif' });
    const agenda = c.agenda();
    await agenda.prochainsRendezVous();
    attendreEgal(recherche.chercherRendezVous(agenda.lireCache(), 'theatre').length, 1, 'lieu perdu');
    attendreEgal(recherche.chercherRendezVous(agenda.lireCache(), 'eclairage').length, 1, 'description perdue');
  });

  function tachesTuiles(c) {
    const modele = { ...TACHES_FICTIVES[0], parente: '', fait: false, abandonnee_le: '', echeance: '', avant_le: '', sous_categorie: '' };
    c.TACHES.splice(0, c.TACHES.length,
      { ...modele, id: 'FICTIF-T1', intitule: 'FICTIF idée en vrac', categorie: 'À trier' },
      { ...modele, id: 'FICTIF-T2', intitule: 'FICTIF autre idée', categorie: 'À trier' },
      { ...modele, id: 'FICTIF-T3', intitule: 'FICTIF accorder la guitare', categorie: 'Musique', echeance: '2020-01-01' },
      { ...modele, id: 'FICTIF-T4', intitule: 'FICTIF chapitre fini', categorie: 'Écriture', fait: true });
  }

  function dicteeQuiEntend(ui, texte) {
    ui.dictee.disponible = () => true;
    ui.dictee.enCours = () => false;
    ui.dictee.arreter = () => {};
    ui.dictee.demarrer = rappels => { rappels.surFinal(texte); rappels.surFin(); };
  }

  await testAsync('Tuiles : fixes d’abord, À trier en tête, compteurs, Tout, Ajouter et Modifier à la fin', async c => {
    tachesTuiles(c);
    const ui = preparerInterface(c);
    const tuilesAffichees = Array.from(ui.parId('tuiles').querySelectorAll('.tuile'));
    const titres = tuilesAffichees.map(t => t.querySelector('.titre-tuile').textContent);
    attendreEgal(titres.slice(0, 5), ['Dernières actions', 'Prochains rendez-vous', 'Aujourd’hui', 'Annuaire', 'Trier'], 'tuiles fixes');
    attendreEgal(titres[5], 'À trier', 'À trier pas en premier');
    attendreEgal(titres.slice(-3), ['Tout', '+ Ajouter', 'Modifier'], 'tuiles de fin');
    const compteur = titre => tuilesAffichees.find(t => t.querySelector('.titre-tuile').textContent === titre).querySelector('.compteur-tuile')?.textContent;
    attendreEgal(compteur('À trier'), '(2)', 'compteur À trier');
    attendreEgal(compteur('Musique'), '(1)', 'compteur Musique');
    attendreEgal(compteur('Écriture'), '(0)', 'tâche cochée comptée');
    attendreEgal(compteur('Trier'), '(2)', 'compteur Trier');
    attendreEgal(compteur('Aujourd’hui'), '(1)', 'retard compté');
    attendreEgal(compteur('Tout'), '(3)', 'compteur Tout');
    attendre(tuilesAffichees.filter(t => t.classList.contains('tuile-fixe')).every(t => !t.classList.contains('deplacable') && !t.querySelector('.micro-tuile')), 'tuile fixe déplaçable');
    attendre(tuilesAffichees.filter(t => t.classList.contains('tuile-categorie')).every(t => t.querySelector('.micro-tuile')), 'micro absent');
    attendre(!tuilesAffichees[5].classList.contains('deplacable'), 'À trier déplaçable');
    attendreEgal(ui.parId('ecran-complet').dataset.vue, 'tuiles', 'vue de départ');
    attendre(ui.parId('liste-taches').classList.contains('hors-vue'), 'longue liste visible sous les tuiles');
  });

  await testAsync('Tuiles : une catégorie ouvre sa liste, ‹ Tuiles revient, Tout et Aujourd’hui filtrent', async c => {
    tachesTuiles(c);
    const ui = preparerInterface(c);
    ui.parId('basculer-vue').click();
    const ouvrirTuileTitre = titre => Array.from(ui.parId('tuiles').querySelectorAll('.ouvrir-tuile'))
      .find(b => b.querySelector('.titre-tuile').textContent === titre).click();
    ouvrirTuileTitre('Musique');
    attendreEgal(ui.parId('titre-vue').textContent, 'Musique', 'titre');
    attendre(!ui.parId('retour-tuiles').hidden, 'retour caché');
    attendre(ui.parId('tuiles').classList.contains('hors-vue'), 'tuiles encore visibles');
    const intitules = () => Array.from(ui.parId('liste-taches').querySelectorAll('[data-tache]'), n => c.TACHES.find(t => t.id === n.dataset.tache)?.intitule).filter(Boolean);
    attendreEgal(intitules(), ['FICTIF accorder la guitare'], 'filtre catégorie');
    ui.parId('retour-tuiles').click();
    attendreEgal(ui.parId('ecran-complet').dataset.vue, 'tuiles', 'retour aux tuiles');
    ouvrirTuileTitre('Aujourd’hui');
    attendreEgal(intitules(), ['FICTIF accorder la guitare'], 'filtre aujourd’hui');
    ui.parId('retour-tuiles').click();
    ouvrirTuileTitre('Tout');
    attendreEgal(intitules().length, 3, 'grande liste');
    attendre(!ui.parId('basculer-archive').classList.contains('hors-vue'), 'archive absente de Tout');
    ui.parId('basculer-vue').click();
    attendreEgal(ui.parId('ecran-complet').dataset.vue, 'tuiles', 'accueil remet les tuiles');
  });

  await testAsync('Tuiles : le micro d’une tuile range la tâche dictée dans sa catégorie', async c => {
    tachesTuiles(c);
    const ui = preparerInterface(c);
    dicteeQuiEntend(ui, 'FICTIF changer les cordes');
    const pendantOriginal = ui.journalActions.pendant;
    ui.journalActions.pendant = (contexte, action) => {
      ui.journalActions.consigner({ ...contexte, fait: 'FICTIF' });
      return pendantOriginal(contexte, action);
    };
    const tuileMusique = ui.parId('tuiles').querySelector('.tuile[data-categorie="Musique"]');
    tuileMusique.querySelector('.micro-tuile').click();
    const creee = TACHES.find(t => t.intitule === 'FICTIF changer les cordes');
    attendre(creee, 'tâche non créée');
    attendreEgal(creee.categorie, 'Musique', 'catégorie de la tuile');
    attendreEgal(creee.origine, 'dictée', 'origine');
    const ligne = ui.journalActions.lireComplet().find(l => l[3].includes('Musique'));
    attendre(ligne && ligne[1] === 'micro de la tuile Musique' && ligne[2] === 'FICTIF changer les cordes', 'journal incomplet');
  });

  await testAsync('Dictée : le texte exact compris est affiché brièvement à l’écran', async c => {
    tachesTuiles(c);
    const ui = preparerInterface(c);
    dicteeQuiEntend(ui, 'FICTIF liste pommes et pain');
    parlerAuGrosMicro(ui.parId('microphone')); // 09/11/2026 : deux touchers
    attendreEgal(ui.parId('texte-entendu').textContent, 'Entendu : « FICTIF liste pommes et pain »',
      'texte entendu non affiché');
  });

  await testAsync('Dates : micro de tuile, échéance dite, puis question à deux boutons si Cap hésite', async c => {
    tachesTuiles(c);
    const ui = preparerInterface(c);
    const tuile = () => ui.parId('tuiles').querySelector('.tuile[data-categorie="Musique"]');
    dicteeQuiEntend(ui, 'FICTIF accorder la guitare après-demain');
    tuile().querySelector('.micro-tuile').click();
    const avecDate = TACHES.find(t => t.intitule === 'FICTIF accorder la guitare après-demain');
    attendreEgal(avecDate.echeance, comprendreDates.trouver('après-demain').date, 'échéance dite');
    attendre(!ui.parId('question-date').open, 'pas de question si la date est sûre');
    dicteeQuiEntend(ui, 'FICTIF répéter dans 8 jours');
    tuile().querySelector('.micro-tuile').click();
    const hesite = TACHES.find(t => t.intitule === 'FICTIF répéter dans 8 jours');
    attendreEgal(hesite.echeance, '', 'rien deviné');
    const question = ui.parId('question-date');
    attendre(question.open, 'question ouverte');
    const boutons = [...question.querySelectorAll('.choix-date-possible')];
    attendreEgal(boutons.length, 2, 'deux boutons');
    const attendu = comprendreDates.trouver('dans 8 jours').choix[1];
    boutons[1].click();
    attendre(!question.open, 'question fermée');
    attendreEgal(TACHES.find(t => t.id === hesite.id).echeance, attendu, 'date choisie');
  });

  test('Sous-catégories : nommée, contenu proche, sinon À classer, jamais par défaut', () => {
    const modele = { parente: '', abandonnee_le: '', categorie: 'Écriture' };
    const taches = [
      { ...modele, intitule: 'Les jardins suspendus de minuit', sous_categorie: 'Roman' },
      { ...modele, intitule: 'Relire', sous_categorie: 'Roman', parente: 'X' },
      { ...modele, intitule: 'Noter l’idée du train qui ne s’arrête jamais', sous_categorie: 'Scénarios' }
    ];
    const subs = ['Scénarios', 'Roman'];
    const t = texte => sousCategories.trouver(texte, 'Écriture', subs, taches).sous_categorie;
    attendreEgal(t('Relire le chapitre 2 des Jardins suspendus de minuit'), 'Roman', 'contenu proche');
    attendreEgal(t("J'ai une idée de scénario d'horreur"), 'Scénarios', 'nommée au singulier');
    attendreEgal(t('Aide-moi en roman à finir de relire tel chapitre'), 'Roman', 'nommée');
    attendreEgal(t('Penser à acheter des cahiers'), 'À classer', 'pas clair');
    attendreEgal(t('Commencer à écrire mon livre pour enfants'), 'À classer', 'pas de défaut');
    attendreEgal(t('Un roman ou un scénario'), 'À classer', 'deux nommées');
    attendreEgal(t('Relire le train'), 'À classer', 'un seul mot commun ne suffit pas');
    attendreEgal(sousCategories.trouver('Acheter du pain', 'Quotidien', [], taches).sous_categorie, '', 'sans sous-catégorie');
    attendreEgal(sousCategories.trouver('rien', 'Écriture', ['À classer'], taches).sous_categorie, '', 'À classer n’est pas une vraie sous-catégorie');
  });

  await testAsync('Sous-catégories : micro de la tuile Écriture, puis À classer affiché en premier sans pourcentage', async c => {
    tachesTuiles(c);
    const modele = { ...c.TACHES[0], fait: false, categorie: 'Écriture' };
    c.TACHES.push(
      { ...modele, id: 'FICTIF-T5', intitule: 'Les jardins suspendus de minuit', sous_categorie: 'Roman' },
      { ...modele, id: 'FICTIF-T6', intitule: 'Noter l’idée du train', sous_categorie: 'Scénarios' },
      { ...modele, id: 'FICTIF-T7', intitule: 'FICTIF déjà à classer', sous_categorie: 'À classer' },
      { ...modele, id: 'FICTIF-T8', intitule: 'FICTIF ancienne sans sous-catégorie', sous_categorie: '' });
    const ui = preparerInterface(c);
    const micro = () => ui.parId('tuiles').querySelector('.tuile[data-categorie="Écriture"] .micro-tuile');
    const dicter = texte => { dicteeQuiEntend(ui, texte); micro().click(); return TACHES.find(t => t.intitule === texte); };
    attendreEgal(dicter('Relire le chapitre 2 des Jardins suspendus de minuit').sous_categorie, 'Roman', 'Roman');
    attendreEgal(dicter("J'ai une idée de scénario d'horreur").sous_categorie, 'Scénarios', 'Scénarios');
    const cahiers = dicter('Penser à acheter des cahiers');
    attendreEgal(cahiers.sous_categorie, 'À classer', 'À classer');
    attendreEgal(cahiers.categorie, 'Écriture', 'reste dans Écriture');
    attendreEgal(dicter('Réécrire la scène 4').sous_categorie, 'Scénarios', 'indice « scène »');
    attendreEgal(dicter('Revoir le personnage principal').sous_categorie, 'Roman', 'indice « personnage »');
    attendreEgal(dicter('Une scène du chapitre 3').sous_categorie, 'À classer', 'deux indices : À classer');
    attendre(!ui.listesChoix.categories('Écriture').includes('À classer'), 'À classer ne devient pas une sous-catégorie à choisir');
    Array.from(ui.parId('tuiles').querySelectorAll('.ouvrir-tuile')).find(b => b.querySelector('.titre-tuile').textContent === 'Écriture').click();
    const titres = Array.from(ui.parId('liste-taches').querySelectorAll('.sous-categorie h3'), h => h.firstChild.textContent);
    attendreEgal(titres[0], 'À classer', 'À classer en premier');
    attendre(!ui.parId('liste-taches').querySelector('.sous-categorie h3').querySelector('.pourcentage'), 'pas de pourcentage');
    const sections = Array.from(ui.parId('liste-taches').querySelectorAll('.sous-categorie'));
    attendre(sections.length && sections.every(section => section.querySelector('h3')), 'aucune case en vrac sans intitulé');
    attendreEgal(titres.filter(titre => titre === 'À classer').length, 1, 'un seul groupe À classer');
    const aClasser = sections.find(section => section.querySelector('h3').firstChild.textContent === 'À classer');
    attendre(aClasser.textContent.includes('FICTIF ancienne sans sous-catégorie'), 'ancienne tâche sans sous-catégorie sous « À classer »');
  });

  await testAsync('Trier : + Ajouter crée la catégorie et y range la tâche, Modifier la retire sans perte, Annuler la ramène', async c => {
    tachesTuiles(c);
    const ui = preparerInterface(c);
    const trier = ui.parId('mode-trier');
    const liste = ui.parId('fenetre-liste');
    Array.from(ui.parId('tuiles').querySelectorAll('.ouvrir-tuile')).find(b => b.querySelector('.titre-tuile').textContent === 'Trier').click();
    attendre(trier.querySelector('.outils-tri'), 'boutons discrets absents');
    boutonTexte(trier, '+ Ajouter').click();
    attendre(liste.open, 'formulaire de création ouvert');
    liste.querySelector('#nom-nouvel-element').value = 'FICTIF Jardin';
    liste.querySelector('form').requestSubmit();
    attendre(!liste.open, 'formulaire fermé');
    attendreEgal(c.TACHES.find(t => t.id === 'FICTIF-T1').categorie, 'FICTIF Jardin', 'tâche rangée tout de suite');
    attendre(trier.open, 'Trier reste ouvert');
    attendreEgal(trier.querySelector('.tache-a-trier').textContent, 'FICTIF autre idée', 'tâche suivante');
    attendre(Array.from(trier.querySelectorAll('.choix-tri'), b => b.textContent).includes('FICTIF Jardin'), 'nouvelle catégorie proposée');
    boutonTexte(trier, 'Modifier').click();
    attendre(liste.open, 'Modifier ouvert');
    const caseJardin = Array.from(liste.querySelectorAll('input[type="checkbox"]')).find(i => i.value === 'FICTIF Jardin');
    caseJardin.checked = true;
    caseJardin.dispatchEvent(new Event('change'));
    boutonTexte(liste, 'Retirer (1)').click();
    attendre(!ui.listesChoix.categories().includes('FICTIF Jardin'), 'catégorie retirée');
    attendreEgal(c.TACHES.find(t => t.id === 'FICTIF-T1').categorie, 'FICTIF Jardin', 'la tâche ne disparaît pas');
    boutonTexte(ui.parId('annulation-liste'), 'Annuler').click();
    attendre(ui.listesChoix.categories().includes('FICTIF Jardin'), 'Annuler ramène la catégorie');
    liste.close();
    await new Promise(r => setTimeout(r, 0));
    attendre(Array.from(trier.querySelectorAll('.choix-tri'), b => b.textContent).includes('FICTIF Jardin'), 'Trier mis à jour après fermeture');
    trier.close();
  });

  test('Annuler : phrases reconnues, une seule fois, délai de 8 secondes, vibration', () => {
    for (const phrase of ['Annule', 'Annule.', 'annule ça', 'Annuler', 'Cap, annule la dernière action', 'Annule ce que tu viens de faire'])
      attendre(annulation.estDemande(phrase), `reconnue : ${phrase}`);
    for (const phrase of ['Annuler le rendez-vous chez le garagiste', 'Annule ma réunion de lundi', 'Appeler Annie'])
      attendre(!annulation.estDemande(phrase), `pas une annulation : ${phrase}`);
    let defaits = 0;
    let retires = 0;
    annulation.proposer({ annuler: () => { defaits += 1; }, messageApres: 'FICTIF défait', retirer: () => { retires += 1; } });
    attendreEgal(annulation.annulerDerniere(), 'FICTIF défait', 'message');
    attendreEgal(annulation.annulerDerniere(), '', 'une seule fois');
    attendreEgal([defaits, retires], [1, 1], 'défait et bouton retiré');
    const vraiNow = Date.now;
    try {
      annulation.proposer({ annuler: () => { defaits += 1; } });
      const depart = vraiNow();
      Date.now = () => depart + 8001;
      attendreEgal(annulation.annulerDerniere(), '', 'trop tard');
      Date.now = vraiNow;
      annulation.proposer({ annuler: () => { defaits += 1; } });
      annulation.garderPendantEcoute();
      Date.now = () => depart + 12000;
      attendreEgal(annulation.annulerDerniere(), 'C’est annulé.', 'le micro laisse le temps de dire Annule');
    } finally {
      Date.now = vraiNow;
    }
    attendreEgal(defaits, 2, 'rien défait après le délai');
    const vraiVibrer = navigator.vibrate;
    const durees = [];
    try {
      Object.defineProperty(navigator, 'vibrate', { value: duree => { durees.push(duree); return true; }, configurable: true });
      Date.now = () => vraiNow() + 60000;
      abandonner(creerTache({ intitule: 'FICTIF vibration', origine: 'ajout à la main' }).id);
      attendreEgal(durees, [30], 'vibration courte à chaque action');
    } finally {
      Date.now = vraiNow;
      Object.defineProperty(navigator, 'vibrate', { value: vraiVibrer, configurable: true });
    }
  });

  test('Annuler partout : ajout, case cochée, abandon, puis « Annule » au clavier et à la voix', () => {
    const statut = document.getElementById('statut');
    const tache = tacheInterface('FICTIF annuler partout');
    attendre(statut.querySelector('.annuler-dictee'), 'Annuler après ajout au formulaire');
    const nombre = TACHES.length;
    const cocherCase = () => {
      const caseTache = document.getElementById(`tache-${tache.id}`);
      caseTache.checked = !caseTache.checked;
      caseTache.dispatchEvent(new Event('change'));
    };
    cocherCase();
    attendre(tache.fait, 'cochée');
    statut.querySelector('.annuler-dictee').click();
    attendre(!tache.fait, 'Annuler décoche');
    attendre(!statut.querySelector('.annuler-dictee'), 'bouton retiré après usage');
    cocherCase();
    document.getElementById('ouvrir-clavier').click();
    document.getElementById('saisie-demande').value = 'Annule';
    document.getElementById('formulaire-demande').requestSubmit();
    if (document.getElementById('clavier').open) document.getElementById('clavier').close();
    attendre(!tache.fait, '« Annule » au clavier décoche');
    document.querySelector(`[data-tache="${tache.id}"] .options-tache`).click();
    document.getElementById('abandonner-tache').click();
    document.getElementById('confirmer-abandon').click();
    attendre(tache.abandonnee_le, 'abandonnée');
    attendre(statut.querySelector('.annuler-dictee'), 'Annuler après abandon');
    const sauve = { ...dictee };
    try {
      dictee.disponible = () => true;
      dictee.enCours = () => false;
      dictee.demarrer = rappels => { rappels.surFinal('Annule ça'); rappels.surFin?.(); };
      parlerAuGrosMicro(document.getElementById('microphone')); // 09/11/2026 : deux touchers
      attendreEgal(tache.abandonnee_le, '', '« Annule » à la voix remet la tâche');
      parlerAuGrosMicro(document.getElementById('microphone')); // 09/11/2026 : deux touchers
      attendre(/plus rien à annuler/.test(statut.textContent), 'rien à annuler deux fois');
    } finally {
      Object.assign(dictee, sauve);
    }
    attendreEgal(TACHES.length, nombre, 'aucune tâche « Annule » créée, rien effacé');
    abandonner(tache.id);
  });

  await (async () => {
    // 08/11/2026 (étape 3) : la conversation se lance avec le bouton « continu » ; l'appui long du micro ne la lance plus.
    // Avant : « Mode conversation : appui long, écoute continue, « stop », bouton Arrêter » (appui long de 2,1 s).
    // 08/11/2026 : bandeau « Arrêter » retiré (décision de Max) : on vérifie le micro « live » et « continu ».
    const nom = 'Mode conversation : bouton « continu » (l’appui long ne la lance plus), écoute continue, « stop », bouton Arrêter';
    if (nom) { testsRemplaces.push(nom); return; } // 09/11/2026 : « continu » retiré (appui long du gros micro) : remplacé, code gardé
    const sauve = { ...dictee };
    const micro = document.getElementById('microphone');
    const bandeau = document.getElementById('bandeau-live');
    const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
    try {
      const nombre = TACHES.length;
      const phrases = ['Ajoute dans Quotidien : FICTIF live un', 'Ajoute dans Quotidien : FICTIF live deux', 'stop'];
      let ecoutes = 0;
      dictee.disponible = () => true;
      dictee.enCours = () => false;
      dictee.arreter = () => {};
      dictee.demarrer = rappels => {
        ecoutes += 1;
        const phrase = phrases.shift();
        setTimeout(() => { if (phrase) rappels.surFinal(phrase); rappels.surFin(); }, 10);
      };
      micro.dispatchEvent(new Event('pointerdown'));
      await attendreMs(500);
      micro.dispatchEvent(new Event('pointerup'));
      attendre(!micro.classList.contains('live') && ecoutes === 0, 'appui court : pas de mode conversation');
      micro.dispatchEvent(new Event('pointerdown'));
      await pause(2100);
      micro.dispatchEvent(new Event('pointerup'));
      attendre(!micro.classList.contains('live') && ecoutes === 0, 'appui long : la conversation se lance encore (08/11/2026 : bouton « continu »)');
      const continu = document.getElementById('micro-continu');
      continu.click();
      attendre(micro.classList.contains('live') && continu.getAttribute('aria-pressed') === 'true', 'bouton « continu » : mode conversation visible');
      attendre(bandeau.hidden, 'bandeau « Arrêter » affiché (retiré le 08/11/2026, décision de Max)');
      await pause(1200);
      const ajoutees = TACHES.slice(nombre).map(tache => tache.intitule);
      attendreEgal(ajoutees, ['FICTIF live un', 'FICTIF live deux'], 'deux phrases traitées sans rappuyer');
      attendre(!micro.classList.contains('live'), '« stop » arrête le mode conversation');
      attendre(document.getElementById('statut').textContent.includes('Mode conversation arrêté'), 'arrêt annoncé');
      attendreEgal(continu.getAttribute('aria-pressed'), 'false', '« continu » encore actif après « stop »');
      phrases.push();
      continu.click(); // avant le 08/11/2026 : appui long de 2,1 s
      attendre(micro.classList.contains('live') && bandeau.hidden, 'mode relancé (sans bandeau)');
      document.getElementById('arreter-live').click();
      attendre(!micro.classList.contains('live'), 'bouton Arrêter (caché, code gardé)');
      TACHES.slice(nombre).forEach(tache => abandonner(tache.id));
      resultats.push({ nom, ok: true, erreur: '' });
    } catch (erreur) {
      resultats.push({ nom, ok: false, erreur: String(erreur && erreur.message ? erreur.message : erreur) });
    } finally {
      document.getElementById('arreter-live').click();
      Object.assign(dictee, sauve);
    }
  })();

  test('Cerveau préparé : range seulement ce qui est nommé, intitulé mot pour mot, réponse courte', () => {
    const debut = traiterDemande({ texte: 'Ajoute dans Écriture : relire le chapitre 2 FICTIF', source: 'micro' });
    attendreEgal([debut.type, debut.tache.intitule, debut.tache.categorie, debut.tache.sous_categorie, debut.tache.origine],
      ['tache', 'relire le chapitre 2 FICTIF', 'Écriture', 'Roman', 'dictée'], 'catégorie nommée au début, indice « chapitre »');
    attendreEgal(debut.parole, 'C’est noté dans Écriture, Roman.', 'réponse parlée');
    const flou = traiterDemande({ texte: 'Ajoute dans Écriture : acheter un carnet FICTIF', source: 'micro' });
    attendreEgal(flou.tache.sous_categorie, 'À classer', 'rien d’évident : À classer');
    const scenario = traiterDemande({ texte: 'J’ai une idée de scénario d’horreur FICTIF', source: 'micro' });
    attendreEgal([scenario.tache.intitule, scenario.tache.categorie, scenario.tache.sous_categorie],
      ['J’ai une idée de scénario d’horreur FICTIF', 'Écriture', 'Scénarios'], 'sous-catégorie nommée dans la phrase');
    const fin = traiterDemande({ texte: 'Ajoute rappeler Paul FICTIF dans Quotidien Courses', source: 'saisie' });
    attendreEgal([fin.tache.intitule, fin.tache.categorie, fin.tache.sous_categorie, fin.message],
      ['rappeler Paul FICTIF', 'Quotidien', 'Courses', 'Ajoutée dans Quotidien › Courses : « rappeler Paul FICTIF »'], 'désignation à la fin');
    const liste = traiterDemande({ texte: 'Ajoute acheter du pain FICTIF à ma to-do', source: 'saisie' });
    attendreEgal([liste.tache.intitule, liste.tache.categorie, liste.message],
      ['acheter du pain FICTIF', 'À trier', 'Ajoutée dans À trier : « acheter du pain FICTIF »'], 'à ma to-do');
    for (const texte of ['Note de frais FICTIF', 'Penser à acheter des cahiers FICTIF', 'Ajoute du sel FICTIF']) {
      const resultat = traiterDemande({ texte, source: 'saisie' });
      attendreEgal([resultat.tache.intitule, resultat.tache.categorie], [texte, 'À trier'], `rien de nommé : ${texte}`);
    }
    const date = traiterDemande({ texte: 'Ajoute dans Musique : mixer le titre FICTIF dans deux semaines', source: 'micro' });
    const attendue = new Date();
    attendue.setDate(attendue.getDate() + 14);
    attendreEgal([date.tache.categorie, date.tache.echeance],
      ['Musique', `${attendue.getFullYear()}-${String(attendue.getMonth() + 1).padStart(2, '0')}-${String(attendue.getDate()).padStart(2, '0')}`],
      'date dite naturellement');
  });

  test('Cerveau préparé : indices évidents (titre du roman, scène, chapitre), sinon À trier', () => {
    reinitialiser();
    const sous = listesChoix.categories('Écriture');
    attendre(sous.includes('Roman') && sous.includes('Scénarios'), `sous-catégories fictives : ${sous.join(', ')}`);
    const roman = traiterDemande({ texte: 'Relire le chapitre 2 des Jardins suspendus de minuit', source: 'micro' });
    attendreEgal([roman.tache.intitule, roman.tache.categorie, roman.tache.sous_categorie],
      ['Relire le chapitre 2 des Jardins suspendus de minuit', 'Écriture', 'Roman'], 'titre du roman');
    const titre = traiterDemande({ texte: 'Relire les jardins suspendus de minuit FICTIF', source: 'micro' });
    attendreEgal([titre.tache.categorie, titre.tache.sous_categorie], ['Écriture', 'Roman'], 'titre seul');
    const scene = traiterDemande({ texte: 'Réécrire la scène 4', source: 'micro' });
    attendreEgal([scene.tache.intitule, scene.tache.categorie, scene.tache.sous_categorie], ['Réécrire la scène 4', 'Écriture', 'Scénarios'], 'scène');
    const dialogues = traiterDemande({ texte: 'Corriger les dialogues FICTIF', source: 'saisie' });
    attendreEgal(dialogues.tache.sous_categorie, 'Scénarios', 'dialogues au pluriel');
    const deux = traiterDemande({ texte: 'Une scène du chapitre 3 FICTIF', source: 'micro' });
    attendreEgal([deux.tache.categorie, deux.tache.sous_categorie], ['Écriture', 'À classer'], 'deux indices : À classer');
    const rien = traiterDemande({ texte: 'Scener les arbres FICTIF', source: 'micro' });
    attendreEgal(rien.tache.categorie, 'À trier', 'mot voisin ignoré');
  });

  await testAsync('Dernières actions : toucher une ligne ouvre la liste sur la tâche', async c => {
    tachesTuiles(c);
    const tache = c.TACHES.find(item => !item.parente && !item.fait && !item.abandonnee_le);
    c.localStorage.setItem('cap_journal_actions_v1', JSON.stringify([
      { heure: new Date().toISOString(), type: 'ajout', texte: tache.intitule, id: tache.id },
      { heure: new Date().toISOString(), type: 'ajout', texte: 'FICTIF tâche disparue', id: 'FICTIF-absente' }
    ]));
    const ui = preparerInterface(c);
    const lignes = ui.parId('liste-actions').querySelectorAll('li');
    attendreEgal(lignes.length, 2, 'deux lignes');
    attendre(!lignes[1].querySelector('button'), 'tâche introuvable : simple texte');
    const bouton = lignes[0].querySelector('button.lien-action');
    attendre(bouton && bouton.textContent.includes(tache.intitule), 'ligne cliquable');
    bouton.click();
    const ligne = ui.parId('liste-taches').querySelector(`[data-tache="${tache.id}"]`);
    attendre(ligne && ligne.classList.contains('surbrillance-recherche'), 'tâche surlignée dans la liste');
    attendreEgal(ui.doc.activeElement, ligne, 'tâche mise en avant');
    try {
      journalActions.noter('ajout', 'FICTIF avec id', 'FICTIF-id-1');
      const premiere = journalActions.lire()[0];
      attendreEgal([premiere.texte, premiere.id], ['FICTIF avec id', 'FICTIF-id-1'], 'id gardé');
    } finally {
      localStorage.removeItem('cap_journal_actions_v1');
    }
  });

  test('Cerveau préparé : deux catégories citées, une seule question, puis la réponse range la tâche', () => {
    const avant = TACHES.length;
    const texte = 'Idée FICTIF entre musique et écriture';
    const question = traiterDemande({ texte, source: 'micro' });
    attendreEgal(question.type, 'question', 'question posée');
    attendre(/^Je la range dans (Musique|Écriture) ou dans (Musique|Écriture) \?$/.test(question.message)
      && question.message.includes('Musique') && question.message.includes('Écriture'), `question courte : ${question.message}`);
    attendreEgal(TACHES.length, avant, 'rien créé avant la réponse');
    const reponse = traiterDemande({ texte: 'Écriture', source: 'micro' });
    attendreEgal([reponse.tache.intitule, reponse.tache.categorie], [texte, 'Écriture'], 'rangée après la réponse');
    traiterDemande({ texte, source: 'micro' });
    const aTrier = traiterDemande({ texte: 'À trier', source: 'micro' });
    attendreEgal([aTrier.tache.intitule, aTrier.tache.categorie], [texte, 'À trier'], 'réponse « À trier »');
    traiterDemande({ texte, source: 'micro' });
    const autre = traiterDemande({ texte: 'Arroser FICTIF', source: 'micro' });
    attendreEgal([autre.tache.intitule, autre.tache.categorie, cerveau.questionEnAttente()], ['Arroser FICTIF', 'À trier', false],
      'une autre demande fait oublier la question');
  });

  test('Cerveau : frontière des actions, action inconnue refusée, rien de supprimé', () => {
    const avant = TACHES.length;
    attendreErreur(() => actionsCap.executer('supprimer_tout', {}), 'ne sait pas');
    attendreErreur(() => actionsCap.executer('ajouter_tache', { intitule: 'FICTIF', categorie: 'Catégorie inventée FICTIF' }), 'n’existe pas');
    attendreErreur(() => actionsCap.executer('ajouter_tache', { intitule: 'FICTIF', categorie: 'Musique', sous_categorie: 'Inventée FICTIF' }), 'n’existe pas');
    cerveau.enregistrerFournisseur('essai', { nom: 'essai', payant: false, comprendre: () => ({ type: 'action', action: 'supprimer_tout' }) });
    try {
      cerveau.choisirFournisseur('essai');
      const resultat = traiterDemande({ texte: 'FICTIF efface tout', source: 'saisie' });
      attendreEgal([resultat.type, resultat.message], ['question', 'Je n’ai pas compris. Tu peux redire ta demande autrement ?'], 'pas compris');
    } finally {
      cerveau.choisirFournisseur('auto');
    }
    attendreEgal(TACHES.length, avant, 'aucune tâche créée ni retirée');
    attendreEgal(cerveau.fournisseurActif(), 'prepare', 'réponses préparées par défaut');
  });

  await (async () => {
    const nom = 'Cerveau : modèle interchangeable en ligne, limite de 60 échanges et alerte à 50';
    try {
      reinitialiser();
      const cle = 'cap_echanges_ia_v1';
      cerveau.enregistrerFournisseur('essai-en-ligne', {
        nom: 'essai', payant: true,
        comprendre: () => Promise.resolve({ type: 'action', action: 'ajouter_tache',
          parametres: { intitule: 'FICTIF en ligne', categorie: 'Quotidien', sous_categorie: 'Maison' } })
      });
      try {
        cerveau.choisirFournisseur('essai-en-ligne');
        localStorage.setItem(cle, JSON.stringify({ jour: dateDuJour(), nombre: 49 }));
        const enCours = traiterDemande({ texte: 'FICTIF en ligne', source: 'saisie' });
        attendreEgal(enCours.type, 'reflexion', 'réponse attendue');
        const fini = await enCours.suite;
        attendreEgal([fini.tache.intitule, fini.tache.categorie, fini.tache.sous_categorie], ['FICTIF en ligne', 'Quotidien', 'Maison'], 'tâche rangée');
        attendre(fini.message.includes('Attention : 50 échanges'), `alerte à 50 : ${fini.message}`);
        localStorage.setItem(cle, JSON.stringify({ jour: dateDuJour(), nombre: 60 }));
        const limite = traiterDemande({ texte: 'FICTIF limite', source: 'saisie' });
        attendreEgal([limite.type, limite.tache.categorie], ['tache', 'À trier'], 'réponses préparées à la limite');
        attendre(limite.message.includes('J’ai atteint ma limite pour aujourd’hui'), `limite annoncée : ${limite.message}`);
        localStorage.setItem(cle, JSON.stringify({ jour: '2000-01-01', nombre: 60 }));
        attendreEgal([limiteIA.utilises(), limiteIA.peutEchanger()], [0, true], 'nouveau jour');
      } finally {
        cerveau.choisirFournisseur('auto');
        localStorage.removeItem(cle);
      }
      resultats.push({ nom, ok: true, erreur: '' });
    } catch (erreur) {
      resultats.push({ nom, ok: false, erreur: String(erreur && erreur.message ? erreur.message : erreur) });
    }
  })();

  test('Limite IA réglable par Max, alerte avant la limite, dépense du mois', () => {
    try {
      attendreEgal([limiteIA.maximum(), limiteIA.seuilAlerte()], [60, 50], 'réglage par défaut');
      attendreEgal(limiteIA.definirMaximum('100'), 100, 'limite changée');
      attendreEgal([limiteIA.maximum(), limiteIA.seuilAlerte()], [100, 83], 'nouvelle limite et alerte');
      for (const mauvais of ['0', '-3', '2.5', 'beaucoup', '5000']) attendreErreur(() => limiteIA.definirMaximum(mauvais), 'entier');
      attendreEgal(limiteIA.maximum(), 100, 'mauvaise valeur refusée sans rien changer');
      localStorage.setItem('cap_echanges_ia_v1', JSON.stringify({ jour: dateDuJour(), nombre: 99 }));
      const dernier = limiteIA.compter();
      attendreEgal([dernier.nombre, dernier.restants, limiteIA.peutEchanger()], [100, 0, false], 'limite atteinte');
      attendre(dernier.alerte.includes('dernier échange'), `prévenu : ${dernier.alerte}`);
      attendreEgal(limiteIA.depenseDuMois(), 0, 'rien dépensé');
      const euros = limiteIA.ajouterDepense(1000000, 0);
      attendre(Math.abs(euros - 0.92) < 1e-9 && Math.abs(limiteIA.depenseDuMois() - 0.92) < 1e-9, `dépense : ${euros}`);
      localStorage.setItem('cap_depense_ia_v1', JSON.stringify({ mois: '2000-01', euros: 5 }));
      attendreEgal(limiteIA.depenseDuMois(), 0, 'nouveau mois');
      localStorage.removeItem('cap_echanges_ia_v1');
      attendreEgal(limiteIA.plafondMensuel(), 4, 'plafond du mois par défaut : 4 € (crédit de 5 dollars)');
      attendreEgal(limiteIA.definirPlafond('2,50'), 2.5, 'plafond réglé par Max, virgule acceptée');
      for (const mauvais of ['0', '-1', 'cher', '2,555', '5000']) attendreErreur(() => limiteIA.definirPlafond(mauvais), 'euros');
      attendreEgal([limiteIA.plafondMensuel(), limiteIA.maximum()], [2.5, 100], 'mauvais plafond refusé, limite du jour gardée');
      localStorage.setItem('cap_depense_ia_v1', JSON.stringify({ mois: dateDuJour().slice(0, 7), euros: 2.1 }));
      attendre(limiteIA.peutEchanger() && limiteIA.compter().alerte.includes('plafond de 2,50 €'), 'prévenu à 80 % du plafond');
      localStorage.setItem('cap_depense_ia_v1', JSON.stringify({ mois: dateDuJour().slice(0, 7), euros: 2.5 }));
      attendre(!limiteIA.peutEchanger() && limiteIA.raisonArret().includes('plafond de dépense du mois'), 'arrêt net au plafond');
    } finally {
      ['cap_echanges_ia_v1', 'cap_reglages_ia_v1', 'cap_depense_ia_v1'].forEach(nom => localStorage.removeItem(nom));
    }
  });

  test('Clé de l’IA : vérifiée, gardée sur le téléphone, jamais affichée en entier', () => {
    try {
      attendreEgal([cleIA.presente(), cleIA.apercu()], [false, ''], 'pas de clé au départ');
      attendreEgal(cerveau.fournisseurActif(), 'prepare', 'sans clé : réponses préparées');
      for (const mauvaise of ['', 'bonjour', 'sk-ant-court', 'sk-ant-FICTIF avec des espaces dedans 0000']) {
        attendreErreur(() => cleIA.enregistrer(mauvaise), 'Rien n’a été enregistré');
      }
      attendreEgal(cleIA.presente(), false, 'mauvaise clé refusée');
      cleIA.enregistrer('  sk-ant-FICTIF-0000000000000000000000abcd  ');
      attendreEgal([cleIA.lire(), cleIA.apercu()], ['sk-ant-FICTIF-0000000000000000000000abcd', '…abcd'], 'clé gardée, aperçu court');
      attendreEgal(cerveau.fournisseurActif(), 'claude', 'avec clé : Claude');
      cleIA.retirer();
      attendreEgal([cleIA.presente(), cerveau.fournisseurActif()], [false, 'prepare'], 'clé retirée');
    } finally {
      cleIA.retirer();
    }
  });

  await (async () => {
    const nom = 'Claude : consignes BROUILLON jamais envoyées, dialogue, action mot pour mot, clé seulement dans l’en-tête';
    const vraiFetch = window.fetch;
    const CLE_FICTIVE = 'sk-ant-FICTIF-0000000000000000000000wxyz';
    const envois = [];
    let consignes = 'BROUILLON : pas encore validé par Max.\nTu es Cap FICTIF.';
    let reponses = [];
    let lecturesFiche = 0;
    window.fetch = (adresse, options = {}) => {
      if (adresse === REGLAGES_IA.fichier_consignes) {
        lecturesFiche += 1;
        if (consignes === null) return Promise.resolve({ ok: false, status: 404, text: () => Promise.resolve('') });
        return Promise.resolve({ ok: true, status: 200, text: () => Promise.resolve(consignes) });
      }
      if (adresse !== REGLAGES_IA.adresse) return Promise.reject(new Error('Hors de ce test.'));
      envois.push({ adresse, options });
      const suivante = reponses.shift();
      return Promise.resolve({ ok: suivante.statut === 200, status: suivante.statut, json: () => Promise.resolve(suivante.corps) });
    };
    try {
      reinitialiser();
      cleIA.enregistrer(CLE_FICTIVE);
      cerveauClaude.oublier();
      attendreEgal(cerveau.fournisseurActif(), 'claude', 'Claude choisi avec la clé');
      const brouillon = await traiterDemande({ texte: 'Ajoute dans Quotidien : FICTIF brouillon', source: 'saisie' }).suite;
      attendreEgal([brouillon.type, brouillon.tache.categorie, envois.length], ['tache', 'Quotidien', 0], 'brouillon : rien envoyé, réponses préparées');
      attendre(brouillon.message.includes('pas encore validée par Max') && brouillon.message.includes('Réponse préparée'), `prévenu : ${brouillon.message}`);
      attendreEgal(limiteIA.utilises(), 0, 'échange non compté');
      attendre((await cerveauClaude.etatConsignes()).includes('pas encore validé'), 'état des consignes');

      consignes = null;
      cerveauClaude.oublier();
      const sansFiche = await traiterDemande({ texte: 'Ajoute dans Quotidien : FICTIF sans fiche', source: 'saisie' }).suite;
      attendreEgal([sansFiche.type, envois.length], ['tache', 0], 'fiche introuvable : Claude jamais appelé');
      attendre(sansFiche.message.includes('pas pu lire ma fiche'), `prévenu : ${sansFiche.message}`);

      localStorage.removeItem('cap_consignes_v1');
      let changements = 0;
      const surChangement = () => { changements += 1; };
      window.addEventListener('cap-consignes-changees', surChangement);
      consignes = 'Tu es Cap FICTIF.';
      cerveauClaude.oublier();
      attendreEgal(await cerveauClaude.etatConsignes(), 'pret', 'consignes validées');
      const info = cerveauClaude.infoConsignes();
      attendre(info && /^[0-9a-f]{8}$/.test(info.empreinte) && info.lue_le && info.version_du, 'date de lecture et version retenues');
      consignes = 'Tu es Cap FICTIF, version 2.';
      cerveauClaude.oublier();
      await cerveauClaude.precharger();
      attendre(changements === 1 && cerveauClaude.infoConsignes().empreinte !== info.empreinte, 'Max prévenu quand la fiche change');
      cerveauClaude.oublier();
      await cerveauClaude.precharger();
      window.removeEventListener('cap-consignes-changees', surChangement);
      attendreEgal(changements, 1, 'même fiche relue : pas de nouvelle alerte');
      consignes = 'Tu es Cap FICTIF.';
      cerveauClaude.oublier();
      journalIA.effacer();
      reponses.push({ statut: 200, corps: { content: [{ type: 'text', text: 'Salut Max, ça va bien. Et toi ?' }], usage: { input_tokens: 1000, output_tokens: 20 } } });
      const conversation = await traiterDemande({ texte: 'Salut Cap, ça va ?', source: 'micro' }).suite;
      attendreEgal([conversation.type, conversation.message, conversation.parole],
        ['reponse', 'Salut Max, ça va bien. Et toi ?', 'Salut Max, ça va bien. Et toi ?'], 'vraie conversation');
      const envoi = envois[0];
      const corps = JSON.parse(envoi.options.body);
      attendreEgal([envoi.adresse, envoi.options.method, envoi.options.headers['x-api-key'], envoi.options.headers['anthropic-version'],
        envoi.options.headers['anthropic-dangerous-direct-browser-access']],
        [REGLAGES_IA.adresse, 'POST', CLE_FICTIVE, '2023-06-01', 'true'], 'en-têtes');
      attendre(!envoi.options.body.includes(CLE_FICTIVE), 'la clé n’est jamais dans le corps');
      attendreEgal([corps.model, corps.messages.length, corps.messages[0].content], [REGLAGES_IA.modele, 1, 'Salut Cap, ça va ?'], 'message envoyé');
      attendre(/^Nous sommes le \S+ \d{1,2} \S+ \d{4}, il est \d{1,2} h \d{2}\.\nTu es Cap FICTIF\./.test(corps.system) && corps.system.includes('Quotidien'),
        `date et heure, puis consignes et catégories envoyées : ${corps.system.slice(0, 80)}`);
      attendreEgal([corps.tools[0].name, corps.tools[0].input_schema.required], ['ajouter_tache', ['intitule']], 'outils du catalogue');
      attendreEgal(limiteIA.utilises(), 1, 'échange compté');
      attendre(limiteIA.depenseDuMois() > 0, 'dépense comptée');

      reponses.push({ statut: 200, corps: { content: [{ type: 'text', text: 'C’est noté dans Quotidien, Maison.' },
        { type: 'tool_use', name: 'ajouter_tache', input: { intitule: 'arroser les plantes FICTIF', categorie: 'Quotidien', sous_categorie: 'Maison' } }],
        usage: { input_tokens: 1000, output_tokens: 40 } } });
      const action = await traiterDemande({ texte: 'Pense à arroser les plantes FICTIF', source: 'micro' }).suite;
      attendreEgal([action.type, action.tache.intitule, action.tache.categorie, action.tache.sous_categorie, action.parole],
        ['tache', 'arroser les plantes FICTIF', 'Quotidien', 'Maison', 'C’est noté dans Quotidien, Maison.'], 'action exécutée et dite');
      attendreEgal(JSON.parse(envois[1].options.body).messages.length, 3, 'la conversation est retenue');
      const journal = journalIA.lire();
      attendreEgal([journal.length, journal[1].dit, journal[1].repondu, journal[0].dit], [2, 'Salut Cap, ça va ?', 'Salut Max, ça va bien. Et toi ?', 'Pense à arroser les plantes FICTIF'], 'historique de l’IA');
      attendre(journal[0].action.includes('arroser les plantes FICTIF'), `action notée : ${journal[0].action}`);
      attendre(!localStorage.getItem('cap_journal_ia_v1').includes(CLE_FICTIVE), 'la clé n’est jamais dans l’historique');

      let avant = TACHES.length;
      reponses.push({ statut: 200, corps: { content: [{ type: 'tool_use', name: 'ajouter_tache', input: { intitule: 'Acheter du lait FICTIF' } }] } });
      const reformulee = await traiterDemande({ texte: 'Il faudrait du lait FICTIF', source: 'micro' }).suite;
      attendreEgal([reformulee.type, TACHES.length], ['proposition', avant], 'reformulation : proposition, rien créé avant le oui');
      attendre(reformulee.message.startsWith('Je mets « Acheter du lait FICTIF » dans À trier') && reformulee.message.endsWith('ça te va ?')
        && !reformulee.message.includes('répéter'), reformulee.message);
      const envoisProposition = envois.length;
      const oui = traiterDemande({ texte: 'Oui, vas-y', source: 'micro' });
      attendreEgal([oui.type, oui.tache.intitule, TACHES.length, envois.length], ['tache', 'Acheter du lait FICTIF', avant + 1, envoisProposition], 'oui : rangé par Cap, sans nouvel appel');
      attendre(oui.tache.note.includes('Dit par Max : « ') && oui.tache.note.includes('Il faudrait du lait FICTIF'), `mots exacts gardés : ${oui.tache.note}`);
      abandonner(oui.tache.id);
      reponses.push({ statut: 200, corps: { content: [{ type: 'text', text: 'Bonne idée.' },
        { type: 'tool_use', name: 'proposer_rangement', input: { intitule: 'Un homme tombe amoureux FICTIF', categorie: 'Inconnue FICTIF', raison: 'c’est une histoire.' } }] } });
      const idee = await traiterDemande({ texte: 'J’ai une idée, un homme qui tombe amoureux FICTIF', source: 'micro' }).suite;
      attendre(idee.type === 'proposition' && idee.message.includes('À trier') && !idee.message.includes('Bonne idée'), `catégorie inconnue : À trier proposé, Cap formule : ${idee.message}`);
      const nombreAvantNon = TACHES.length;
      const non = traiterDemande({ texte: 'Non merci', source: 'micro' });
      attendreEgal([non.type, non.message, TACHES.length], ['reponse', 'D’accord, je ne range rien.', nombreAvantNon], 'non : rien rangé');
      attendre(JSON.parse(envois[envois.length - 1].options.body).system.includes('Ne demande jamais à Max de répéter ses mots'), 'consigne : jamais répéter');
      avant = TACHES.length;
      reponses.push({ statut: 200, corps: { content: [
        { type: 'tool_use', name: 'ajouter_tache', input: { intitule: 'un FICTIF' } },
        { type: 'tool_use', name: 'ajouter_tache', input: { intitule: 'deux FICTIF' } }] } });
      const plusieurs = await traiterDemande({ texte: 'Ajoute un FICTIF et deux FICTIF', source: 'micro' }).suite;
      attendreEgal([plusieurs.type, TACHES.length], ['reponse', avant], 'plusieurs actions d’un coup refusées');
      reponses.push({ statut: 200, corps: { content: [{ type: 'tool_use', name: 'supprimer_tout', input: { intitule: 'tout FICTIF' } }] } });
      const inconnue = await traiterDemande({ texte: 'Efface tout FICTIF', source: 'micro' }).suite;
      attendreEgal([inconnue.type, TACHES.length], ['question', avant], 'action inconnue refusée');

      reponses.push({ statut: 200, corps: { content: [{ type: 'text', text: 'Le numéro de ton médecin est le 01 23 45 67 89.' }] } });
      const invente = await traiterDemande({ texte: 'Quel est le numéro de mon médecin FICTIF ?', source: 'micro' }).suite;
      attendreEgal([invente.type, invente.message], ['reponse', 'Je ne sais pas : tu ne m’as jamais donné ce numéro.'], 'numéro inconnu : « je ne sais pas », jamais inventé');
      attendre(JSON.parse(envois[envois.length - 1].options.body).system.includes('réponds « Je ne sais pas. »'), 'consigne « je ne sais pas » envoyée à chaque échange');
      reponses.push({ statut: 200, corps: { content: [{ type: 'text', text: 'Je ne sais pas.' }] } });
      const sait = await traiterDemande({ texte: 'Et le numéro de la pharmacie FICTIF ?', source: 'micro' }).suite;
      attendreEgal(sait.message, 'Je ne sais pas.', 'Claude qui dit ne pas savoir : réponse gardée');
      reponses.push({ statut: 200, corps: { content: [{ type: 'text', text: 'C’est le 06 11 22 33 44.' }] } });
      const donne = await traiterDemande({ texte: 'Retiens le 0611223344 pour le garage FICTIF, et redis-le moi', source: 'micro' }).suite;
      attendreEgal(donne.message, 'C’est le 06 11 22 33 44.', 'numéro donné par Max : répété sans souci');
      cerveauClaude.nouvelleConversation();
      reponses.push({ statut: 200, corps: { content: [{ type: 'text', text: 'Bonjour Max.' }] } });
      await traiterDemande({ texte: 'Bonjour FICTIF', source: 'micro' }).suite;
      attendreEgal(JSON.parse(envois[envois.length - 1].options.body).messages.length, 1, 'nouvelle ouverture : l’IA repart de zéro');

      const aFaire = TACHES.filter(tache => !tache.fait && !tache.abandonnee_le).length;
      const empreinteTaches = JSON.stringify(TACHES);
      reponses.push({ statut: 200, corps: { content: [{ type: 'tool_use', id: 'lecture1', name: 'lire_taches', input: { etat: 'a_faire' } }] } });
      reponses.push({ statut: 200, corps: { content: [{ type: 'text', text: `Tu as ${aFaire} tâches à faire.` }] } });
      const envoisLecture = envois.length;
      const compte = await traiterDemande({ texte: 'Combien ai-je de tâches à faire FICTIF ?', source: 'micro' }).suite;
      attendreEgal([compte.type, compte.message, envois.length - envoisLecture], ['reponse', `Tu as ${aFaire} tâches à faire.`, 2], 'lecture : deux appels, réponse dite');
      const second = JSON.parse(envois[envois.length - 1].options.body).messages;
      const resultat = second[second.length - 1].content[0];
      const lu = JSON.parse(resultat.content);
      attendreEgal([resultat.type, resultat.tool_use_id, lu.nombre, lu.taches.length <= 25], ['tool_result', 'lecture1', aFaire, true], 'Cap a lu les tâches et renvoyé le nombre exact');
      attendre(lu.taches.every(tache => Object.keys(tache).join() === 'intitule,categorie,sous_categorie,echeance,fait'), 'strict nécessaire : copie réduite');
      attendreEgal(JSON.stringify(TACHES), empreinteTaches, 'lecture seule : rien modifié');
      attendreEgal(actionsCap.lire('lire_taches', { categorie: 'Inconnue FICTIF' }).erreur, 'La catégorie « Inconnue FICTIF » n’existe pas.', 'catégorie inconnue signalée');
      const rdv = actionsCap.lire('lire_rendez_vous', { du: '2027-01-01', au: '2027-01-31' });
      attendreEgal([rdv.du, rdv.au, typeof rdv.nombre], ['2027-01-01', '2027-01-31', 'number'], 'lecture des rendez-vous');
      attendreEgal(cerveau.proposer({ type: 'action', action: 'lire_taches', parametres: {} }).type, 'question', 'une lecture n’est jamais exécutée comme une action');

      const lecturesAvant = lecturesFiche;
      await cerveauClaude.enregistrerFiche('  Tu es Cap FICTIF, fiche collée sur le téléphone.  ');
      attendreEgal([cerveauClaude.ficheTelephone(), cerveauClaude.origineFiche(), cerveauClaude.infoConsignes().origine],
        ['Tu es Cap FICTIF, fiche collée sur le téléphone.', 'telephone', 'telephone'], 'fiche gardée sur le téléphone');
      reponses.push({ statut: 200, corps: { content: [{ type: 'text', text: 'Bien reçu, Max.' }] } });
      await traiterDemande({ texte: 'Tu as ma fiche FICTIF ?', source: 'micro' }).suite;
      const systemeTelephone = JSON.parse(envois[envois.length - 1].options.body).system;
      attendre(systemeTelephone.includes('fiche collée sur le téléphone') && !systemeTelephone.includes(consignes), 'Claude lit exactement la fiche collée par Max');
      attendreEgal(lecturesFiche, lecturesAvant, 'la fiche publique n’est même pas lue quand Max a collé la sienne');
      let videRefusee = false;
      try { await cerveauClaude.enregistrerFiche('   '); } catch (erreur) { videRefusee = erreur.message.includes('vide'); }
      attendre(videRefusee && cerveauClaude.ficheTelephone().includes('fiche collée'), 'fiche vide refusée, l’ancienne gardée');
      await cerveauClaude.retirerFiche();
      attendreEgal([cerveauClaude.ficheTelephone(), cerveauClaude.origineFiche(), await cerveauClaude.etatConsignes()], ['', 'secours', 'pret'], 'retour à la fiche de secours');

      const utilises = limiteIA.utilises();
      reponses.push({ statut: 401, corps: {} });
      const refusee = await traiterDemande({ texte: 'Ajoute dans Quotidien : FICTIF clé refusée', source: 'saisie' }).suite;
      attendreEgal([refusee.type, refusee.tache.categorie, limiteIA.utilises()], ['tache', 'Quotidien', utilises], 'clé refusée : réponses préparées, non compté');
      attendre(refusee.message.includes('clé n’est plus acceptée') && refusee.message.includes('expiré') && refusee.message.includes('en créer une nouvelle'), refusee.message);
      attendre(!refusee.message.includes(CLE_FICTIVE), 'la clé n’est jamais dans un message d’erreur');

      localStorage.setItem('cap_depense_ia_v1', JSON.stringify({ mois: dateDuJour().slice(0, 7), euros: 10 }));
      const envoisAvant = envois.length;
      const immediat = traiterDemande({ texte: 'Ajoute dans Quotidien : FICTIF plafond', source: 'saisie' });
      const plafond = immediat.suite ? await immediat.suite : immediat;
      attendreEgal([plafond.type, envois.length], ['tache', envoisAvant], 'plafond du mois atteint : Claude n’est plus appelé');
      attendre(plafond.message.includes('plafond de dépense du mois'), plafond.message);
      attendreEgal(cerveauClaude.maintenantParis(new Date('2026-10-30T09:37:00Z')), 'Nous sommes le vendredi 30 octobre 2026, il est 10 h 37.', 'date et heure de Paris');
      resultats.push({ nom, ok: true, erreur: '' });
    } catch (erreur) {
      resultats.push({ nom, ok: false, erreur: String(erreur && erreur.message ? erreur.message : erreur) });
    } finally {
      window.fetch = vraiFetch;
      cleIA.retirer();
      cerveauClaude.oublier();
      ['cap_echanges_ia_v1', 'cap_depense_ia_v1', 'cap_journal_ia_v1', 'cap_consignes_v1', 'cap_fiche_consignes_v1'].forEach(cle => localStorage.removeItem(cle));
    }
  })();

  await testAsync('Réglages du cerveau : clé tapée dans Cap, limite changée, champ vidé', async c => {
    const ui = preparerInterface(c);
    const vraiFetch = window.fetch;
    window.fetch = () => Promise.resolve({ ok: true, status: 200, text: () => Promise.resolve('BROUILLON FICTIF\nTu es Cap.') });
    try {
      ui.parId('ouvrir-reglages-ia').click();
      const fenetre = ui.parId('reglages-ia');
      attendre(fenetre.open, 'fenêtre ouverte');
      ui.parId('cle-ia').value = 'pas une clé';
      ui.parId('formulaire-cle-ia').requestSubmit();
      attendre(!fenetre.querySelector('.erreur').hidden && !cleIA.presente(), 'mauvaise clé refusée et expliquée');
      ui.parId('cle-ia').value = 'sk-ant-FICTIF-0000000000000000000000abcd';
      ui.parId('formulaire-cle-ia').requestSubmit();
      attendreEgal([cleIA.presente(), ui.parId('cle-ia').value], [true, ''], 'clé enregistrée, champ vidé');
      attendre(ui.parId('texte-cerveau').textContent.includes(REGLAGES_IA.nom), 'tuile du cerveau à jour');
      ui.parId('limite-ia').value = '100';
      ui.parId('formulaire-limite-ia').requestSubmit();
      attendreEgal(limiteIA.maximum(), 100, 'limite changée par Max');
      ui.parId('plafond-ia').value = '7,5';
      ui.parId('formulaire-plafond-ia').requestSubmit();
      attendreEgal(limiteIA.plafondMensuel(), 7.5, 'plafond changé par Max');
      ui.parId('texte-fiche-ia').value = 'Tu es Cap FICTIF, fiche collée par Max.';
      ui.parId('formulaire-fiche-ia').requestSubmit();
      await new Promise(resolve => setTimeout(resolve, 20));
      attendreEgal([cerveauClaude.ficheTelephone(), ui.parId('retirer-fiche-ia').hidden], ['Tu es Cap FICTIF, fiche collée par Max.', false], 'fiche collée et gardée sur le téléphone');
      attendre(ui.parId('fiche-ia').textContent.includes('ta fiche, gardée sur ce téléphone'), ui.parId('fiche-ia').textContent);
      ui.parId('retirer-fiche-ia').click();
      await new Promise(resolve => setTimeout(resolve, 20));
      attendreEgal([cerveauClaude.ficheTelephone(), ui.parId('texte-fiche-ia').value, ui.parId('retirer-fiche-ia').hidden], ['', '', true], 'retour à la fiche de secours');
      journalIA.noter({ dit: 'FICTIF bonjour', repondu: 'FICTIF salut' });
      await new Promise(resolve => setTimeout(resolve, 0));
      ui.parId('formulaire-limite-ia').requestSubmit();
      attendre(ui.parId('liste-journal-ia').textContent.includes('FICTIF salut'), 'historique de l’IA visible');
      attendre(/Conversation du \d{2}\/\d{2} à \d{1,2} h \d{2} \(1 échange\)/.test(ui.parId('liste-journal-ia').querySelector('summary').textContent), 'conversation datée');
      journalIA.nouvelleConversation();
      journalIA.noter({ dit: 'FICTIF deuxième ouverture', repondu: 'FICTIF re' });
      const groupes = journalIA.conversations();
      attendreEgal([groupes.length, groupes[0].echanges[0].dit, groupes[1].echanges[0].dit], [2, 'FICTIF deuxième ouverture', 'FICTIF bonjour'], 'une conversation par ouverture, la plus récente d’abord');
      ui.parId('effacer-journal-ia').click();
      attendreEgal([journalIA.lire().length, ui.parId('liste-journal-ia').textContent.includes('FICTIF')], [0, false], 'effacé d’un geste');
      ui.parId('retirer-cle-ia').click();
      attendreEgal(cleIA.presente(), false, 'clé retirée');
      await new Promise(resolve => setTimeout(resolve, 0));
    } finally {
      window.fetch = vraiFetch;
      cleIA.retirer();
      cerveauClaude.oublier();
      ['cap_reglages_ia_v1', 'cap_journal_ia_v1', 'cap_consignes_v1', 'cap_fiche_consignes_v1'].forEach(cle => localStorage.removeItem(cle));
    }
  });

  await testAsync('Mes phrases : ouvrir, ajouter, modifier, retirer et revenir aux phrases d’origine', async c => {
    const ui = preparerInterface(c);
    localStorage.removeItem('cap_phrases_modifiables');
    try {
      ui.parId('ouvrir-reglages-phrases').click();
      const fenetre = ui.parId('reglages-phrases');
      attendre(fenetre.open, 'fenêtre ouverte');
      attendre(!ui.parId('liste-rubriques-phrases-vue').hidden, 'liste des rubriques visible');
      const boutons = Array.from(ui.parId('liste-rubriques-commande').querySelectorAll('button'));
      const boutonCourses = boutons.find(b => b.textContent === 'Liste de courses');
      attendre(Boolean(boutonCourses), 'rubrique Liste de courses présente');
      boutonCourses.click();
      attendre(!ui.parId('detail-rubrique-phrases').hidden, 'détail de la rubrique visible');
      attendreEgal(ui.parId('titre-rubrique-phrases').textContent, 'Liste de courses', 'titre de la rubrique');
      attendreEgal(
        Array.from(ui.parId('liste-phrases-actives').querySelectorAll('li')).map(li => li.firstChild.textContent.trim()),
        ['liste', 'listes'], 'phrases d’origine affichées');
      ui.parId('saisie-phrase').value = 'courses';
      ui.parId('formulaire-phrase').requestSubmit();
      attendreEgal(ui.parId('statut-phrases').textContent, 'Phrase ajoutée.', 'message après ajout');
      attendre(phrasesModifiablesEtat.obtenir().rubriques.liste_courses.phrases
        .some(p => p.texte === 'courses' && p.retiree_le === null), 'nouvelle phrase gardée dans l’état');
      const ligneCourses = Array.from(ui.parId('liste-phrases-actives').querySelectorAll('li'))
        .find(li => li.firstChild.textContent.trim() === 'courses');
      ligneCourses.querySelector('button').click();
      attendreEgal([ui.parId('saisie-phrase').value, ui.parId('bouton-phrase-valider').textContent],
        ['courses', 'Enregistrer'], 'formulaire prérempli pour modifier');
      ui.parId('saisie-phrase').value = 'mes courses';
      ui.parId('formulaire-phrase').requestSubmit();
      attendreEgal(ui.parId('statut-phrases').textContent, 'Phrase modifiée.', 'message après modification');
      const etatApresModif = phrasesModifiablesEtat.obtenir().rubriques.liste_courses.phrases;
      attendre(etatApresModif.some(p => p.texte === 'courses' && p.retiree_le !== null), 'ancienne phrase marquée retirée, jamais effacée');
      attendre(etatApresModif.some(p => p.texte === 'mes courses' && p.retiree_le === null), 'nouvelle phrase active');
      const ligneMesCourses = Array.from(ui.parId('liste-phrases-actives').querySelectorAll('li'))
        .find(li => li.firstChild.textContent.trim() === 'mes courses');
      ligneMesCourses.querySelectorAll('button')[1].click();
      attendreEgal(ui.parId('statut-phrases').textContent, 'Phrase retirée : « mes courses ».', 'message après retrait');
      attendre(phrasesModifiablesEtat.obtenir().rubriques.liste_courses.phrases
        .find(p => p.texte === 'mes courses').retiree_le !== null, 'phrase retirée marquée datée, pas effacée');
      ui.parId('reinitialiser-rubrique-phrases').click();
      attendre(!ui.parId('confirmation-reinit-phrases').hidden, 'confirmation affichée avant réinitialisation');
      ui.parId('annuler-reinit-phrases').click();
      attendre(ui.parId('confirmation-reinit-phrases').hidden, 'confirmation refermée après Annuler');
      attendre(phrasesModifiablesEtat.obtenir().rubriques.liste_courses.phrases
        .find(p => p.texte === 'mes courses').retiree_le !== null, 'Annuler ne restaure rien, phrase toujours retirée');
      ui.parId('reinitialiser-rubrique-phrases').click();
      ui.parId('confirmer-reinit-phrases').click();
      attendre(ui.parId('confirmation-reinit-phrases').hidden, 'confirmation refermée après Confirmer');
      attendreEgal(ui.parId('statut-phrases').textContent, 'Phrases d’origine restaurées.', 'message après réinitialisation');
      attendreEgal(
        Array.from(ui.parId('liste-phrases-actives').querySelectorAll('li')).map(li => li.firstChild.textContent.trim()),
        ['liste', 'listes'], 'retour aux phrases d’origine');
      ui.parId('retour-liste-phrases').click();
      attendre(!ui.parId('liste-rubriques-phrases-vue').hidden && ui.parId('detail-rubrique-phrases').hidden, 'retour à la liste des rubriques');
      fenetre.close();
    } finally {
      localStorage.removeItem('cap_phrases_modifiables');
    }
  });

  test('Voix : silence par défaut, puis Cap dit ce qu’il a fait en français', () => {
    const dits = [];
    const vraiConstructeur = window.SpeechSynthesisUtterance;
    Object.defineProperty(window, 'speechSynthesis', { value: { cancel() {}, speak(enonce) { dits.push([enonce.text, enonce.lang]); } }, configurable: true });
    window.SpeechSynthesisUtterance = function (texte) { this.text = texte; };
    try {
      attendreEgal(voix.dire('FICTIF'), false, 'silencieux par défaut');
      preferencesClavier.definirSilencieux(false);
      document.getElementById('ouvrir-clavier').click();
      document.getElementById('saisie-demande').value = 'Ajoute dans Quotidien : FICTIF parler';
      document.getElementById('formulaire-demande').requestSubmit();
      if (document.getElementById('clavier').open) document.getElementById('clavier').close();
      attendreEgal(dits, [['C’est noté dans Quotidien, À classer.', 'fr-FR']], 'réponse parlée');
      const tache = TACHES.find(item => item.intitule === 'FICTIF parler');
      attendre(tache && document.querySelector('#statut .annuler-dictee'), 'Annuler proposé après l’action du cerveau');
      document.querySelector('#statut .annuler-dictee').click();
      attendre(tache.abandonnee_le, 'Annuler fonctionne, rien d’effacé');
    } finally {
      delete window.speechSynthesis;
      window.SpeechSynthesisUtterance = vraiConstructeur;
      preferencesClavier.definirSilencieux(true);
    }
  });

  await testAsync('Trier : toucher une catégorie, Annuler, puis la voix range la tâche suivante', async c => {
    tachesTuiles(c);
    const ui = preparerInterface(c);
    const fenetre = ui.parId('mode-trier');
    Array.from(ui.parId('tuiles').querySelectorAll('.ouvrir-tuile')).find(b => b.querySelector('.titre-tuile').textContent === 'Trier').click();
    attendre(fenetre.open, 'Trier fermé');
    attendreEgal(fenetre.querySelector('.tache-a-trier').textContent, 'FICTIF idée en vrac', 'première tâche');
    const choix = Array.from(fenetre.querySelectorAll('.choix-tri'), b => b.textContent);
    attendre(!choix.includes('À trier') && choix.includes('Musique'), 'choix de catégories');
    boutonTexte(fenetre, 'Écriture').click();
    attendreEgal(c.TACHES.find(t => t.id === 'FICTIF-T1').categorie, 'Écriture', 'tâche rangée');
    attendreEgal(fenetre.querySelector('.tache-a-trier').textContent, 'FICTIF autre idée', 'tâche suivante');
    boutonTexte(fenetre, 'Annuler').click();
    attendreEgal(c.TACHES.find(t => t.id === 'FICTIF-T1').categorie, 'À trier', 'Annuler');
    attendreEgal(fenetre.querySelector('.tache-a-trier').textContent, 'FICTIF idée en vrac', 'tâche revenue');
    dicteeQuiEntend(ui, 'mets ça dans musique');
    fenetre.querySelector('.micro-tri').click();
    attendreEgal(c.TACHES.find(t => t.id === 'FICTIF-T1').categorie, 'Musique', 'voix');
    attendreEgal(ui.modeTrier.reconnaitre('quotidien'), 'Quotidien', 'reconnaissance');
    attendreEgal(ui.modeTrier.reconnaitre('rien du tout'), '', 'pas d’invention');
    boutonTexte(fenetre, 'Passer').click();
    attendre(fenetre.querySelector('.revoir-passees'), 'revoir les passées');
    attendreEgal(c.TACHES.length, 4, 'aucune tâche effacée');
    ui.fermetureFenetres.toucheACote(fenetre);
    attendre(!fenetre.open, 'toucher à côté ne ferme pas Trier');
  });

  test('Ordre des tuiles : ordonner garde le choix de Max, À trier reste devant', () => {
    const { instance } = listesIsolees([]);
    attendreEgal(instance.categories().slice(0, 4), ['À trier', 'Musique', 'Écriture', 'Quotidien'], 'départ');
    attendre(instance.ordonner(['Quotidien', 'Musique', 'Écriture']), 'aucun changement');
    attendreEgal(instance.categories().slice(0, 4), ['À trier', 'Quotidien', 'Musique', 'Écriture'], 'ordre choisi');
    attendre(!instance.ordonner(['Quotidien', 'Musique', 'Écriture']), 'réécriture inutile');
  });

  test('Classer : change la catégorie de la tâche et de ses étapes, rien n’est effacé', () => {
    const tache = creerTache({ intitule: 'FICTIF à classer', categorie: 'À trier', sous_categorie: '' });
    ajouterEtape(tache.id, 'FICTIF étape');
    const total = TACHES.length;
    const ancienne = classer(tache.id, 'Musique', '');
    attendreEgal(ancienne.categorie, 'À trier', 'ancienne catégorie');
    attendre(TACHES.filter(t => t.id === tache.id || t.parente === tache.id).every(t => t.categorie === 'Musique'), 'étapes non suivies');
    attendreEgal(TACHES.length, total, 'tâche effacée');
  });

  await testAsync('Aide : bouton en haut à droite, gestes listés, fermeture en touchant à côté', async c => {
    const ui = preparerInterface(c);
    ui.parId('basculer-vue').click();
    const bouton = ui.parId('ouvrir-aide');
    const entete = bouton.parentElement.getBoundingClientRect();
    const cadre = bouton.getBoundingClientRect();
    attendre(Math.abs(entete.right - cadre.right) < 2 && cadre.top - entete.top < 20, 'Aide pas en haut à droite');
    bouton.click();
    const aide = ui.parId('aide');
    attendre(aide.open, 'aide fermée');
    attendre(aide.querySelectorAll('.geste-aide').length >= 6, 'gestes manquants');
    attendre(aide.textContent.includes('droite') && aide.textContent.includes('Annuler'), 'contenu incomplet');
    attendreEgal(aide.querySelectorAll('[data-fermer]').length, 0, 'bouton retour présent');
    ui.fermetureFenetres.toucheACote(aide);
    attendre(!aide.open, 'aide pas fermée en touchant à côté');
  });

  test('Journal complet : contexte, heure à la seconde, masquage des secrets', () => {
    const memoire = espaceMemoire();
    const j = objetIsole(SOURCE_JOURNAL_ACTIONS, 'journalActions', { localStorage: memoire, googleSheets: undefined });
    j.pendant({ source: 'micro', entree: 'ajoute FICTIF pain', compris: 'ajouter une tâche' }, () => j.noter('ajout', 'FICTIF pain'));
    j.consigner({ source: 'clavier', entree: 'mon mot de passe est Secret123 et ma carte 4970 1234 5678 9012', compris: 'rien', fait: 'rien' });
    const lignes = j.lireComplet();
    attendreEgal(lignes.length, 2, 'deux lignes');
    attendre(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(lignes[0][0]), 'heure');
    attendreEgal(lignes[0].slice(1), ['micro', 'ajoute FICTIF pain', 'ajouter une tâche', 'ajout de la tâche : FICTIF pain'], 'ligne');
    attendre(!lignes[1][2].includes('Secret123') && !lignes[1][2].includes('9012'), 'secret conservé');
    j.noter('fait', 'FICTIF pain');
    attendreEgal(j.lireComplet()[2][1], 'écran touché', 'source par défaut');
  });

  await testAsync('Journal complet : envoi en ajout à la fin de l’onglet, file vidée seulement après succès', async c => {
    preparerConnexion(c);
    let ongletPresent = false;
    let panne = true;
    c.repondre = async r => {
      const chemin = decodeURIComponent(r.url.pathname);
      if (r.methode === 'GET' && chemin === '/drive/v3/files/tableau-fictif') return reponseGoogle({ id: 'tableau-fictif', trashed: false });
      if (r.methode === 'GET' && chemin === '/v4/spreadsheets/tableau-fictif') return reponseGoogle({ sheets: [{ properties: { title: 'Tâches' } }, ...(ongletPresent ? [{ properties: { title: 'Journal' } }] : [])] });
      if (r.methode === 'POST' && chemin.endsWith(':append')) {
        if (panne) return reponseGoogle({ error: { message: 'panne' } }, 500);
        return reponseGoogle({});
      }
      if (r.methode === 'POST') { ongletPresent = true; return reponseGoogle({}); }
      throw new Error(`Requête inattendue : ${r.url}`);
    };
    c.localStorage.setItem('cap_google_fichier_v1', 'tableau-fictif');
    const sheets = c.sheets();
    const j = objetIsole(SOURCE_JOURNAL_ACTIONS, 'journalActions', {
      localStorage: c.localStorage, googleSheets: sheets, googleConnexion: c.googleConnexion,
      navigator: c.navigator, synchronisation: { informations: () => ({ pret: true }) }, setTimeout: () => 0
    });
    j.consigner({ source: 'micro', entree: 'FICTIF', compris: 'test', fait: 'rien' });
    attendreEgal(await j.envoyer(), false, 'panne non signalée');
    attendreEgal(j.enAttente(), 1, 'ligne perdue après une panne');
    panne = false;
    attendreEgal(await j.envoyer(), true, 'envoi');
    attendreEgal(j.enAttente(), 0, 'file non vidée');
    const ajout = c.requetes.filter(r => decodeURIComponent(r.url.pathname).endsWith(':append')).pop();
    attendre(decodeURIComponent(ajout.url.pathname).includes('Journal'), 'mauvais onglet');
    attendreEgal(ajout.url.searchParams.get('insertDataOption'), 'INSERT_ROWS', 'ajout sans écraser');
    attendreEgal(ajout.corps.values[0].slice(1), ['micro', 'FICTIF', 'test', 'rien'], 'contenu');
    attendre(c.requetes.every(r => !['DELETE'].includes(r.methode) && !r.url.pathname.includes(':clear')), 'effacement');
  });

  await testAsync('Sauvegarde Drive : copie datée dans le dossier, aucune suppression, hebdomadaire après la première', async c => {
    preparerConnexion(c);
    c.localStorage.setItem('cap_google_fichier_v1', 'tableau-fictif');
    c.repondre = async r => {
      const chemin = decodeURIComponent(r.url.pathname);
      if (r.methode === 'GET' && chemin === '/drive/v3/files/tableau-fictif') return reponseGoogle({ id: 'tableau-fictif', trashed: false });
      if (r.methode === 'GET' && chemin === '/drive/v3/files' && r.url.searchParams.get('q').includes('folder')) return reponseGoogle({ files: [] });
      if (r.methode === 'POST' && chemin === '/drive/v3/files') return reponseGoogle({ id: 'dossier-fictif' });
      if (r.methode === 'POST' && chemin === '/drive/v3/files/tableau-fictif/copy') return reponseGoogle({ id: 'copie-fictive', name: r.corps.name });
      if (r.methode === 'GET' && chemin === '/drive/v3/files') return reponseGoogle({ files: Array.from({ length: 6 }, (_, i) => ({ id: `c${i}` })) });
      throw new Error(`Requête inattendue : ${r.url}`);
    };
    const sheets = c.sheets();
    const s = objetIsole(SOURCE_SAUVEGARDE_DRIVE, 'sauvegardeDrive', {
      localStorage: c.localStorage, window: c.window, googleConnexion: c.googleConnexion, googleSheets: sheets,
      REGLAGES_GOOGLE, journalActions: { consigner: () => {} }
    });
    attendre(!s.aFaire(), 'automatique avant la première');
    attendreEgal(await s.verifierAutomatique(), null, 'sauvegarde automatique sans accord');
    const resultat = await s.sauvegarder();
    const copie = c.requetes.find(r => r.url.pathname.endsWith('/copy'));
    attendre(copie.corps.name.includes('sauvegarde du') && copie.corps.name.includes('FICTIF'), 'nom de la copie');
    attendreEgal(copie.corps.parents, ['dossier-fictif'], 'dossier');
    attendreEgal(resultat.enTrop, 1, 'copies en trop');
    attendre(c.requetes.every(r => r.methode !== 'DELETE' && !(r.corps && r.corps.trashed)), 'suppression');
    attendre(!s.aFaire(Date.now()), 'refait aussitôt');
    attendre(s.aFaire(Date.now() + 8 * 24 * 3600 * 1000), 'pas refait après une semaine');
    attendreEgal(s.etat().nombre, 6, 'nombre de copies');
  });

  test('Fichiers vocaux : « liste » reconnu en code pur (ajout, lecture, retrait, zéro perte)', () => {
    attendreEgal(fichiersVocaux.detecterCommande('liste pommes, pain et lait'),
      { type: 'ajouter', fichier: 'liste_courses', produits: ['pommes', 'pain', 'lait'] }, 'ajout reconnu');
    attendreEgal(fichiersVocaux.detecterCommande('liste, lis-moi'), { type: 'lire', fichier: 'liste_courses' }, 'lecture reconnue');
    attendreEgal(fichiersVocaux.detecterCommande('liste, retire pommes'),
      { type: 'retirer', fichier: 'liste_courses', produit: 'pommes' }, 'retrait reconnu');
    attendreEgal(fichiersVocaux.detecterCommande('bloc-notes, note quelque chose'), null, 'pas de collision avec une autre commande');
    const ajout = fichiersVocaux.ajouterElements('', ['Pommes', 'pain']);
    attendreEgal(ajout.ajoutes, ['Pommes', 'pain'], 'deux produits ajoutés');
    attendre(ajout.contenu === '- Pommes\n- pain\n', 'lignes attendues');
    const sansDoublon = fichiersVocaux.ajouterElements(ajout.contenu, ['pommes', 'beurre']);
    attendreEgal(sansDoublon.ajoutes, ['beurre'], 'pas de doublon malgré la casse');
    attendreEgal(sansDoublon.doublons, ['pommes'], 'doublon signalé');
    const retrait = fichiersVocaux.retirerElement(sansDoublon.contenu, 'pain', new Date(2026, 10, 3));
    attendre(retrait.retire && retrait.nom === 'pain', 'retrait reconnu');
    attendre(retrait.contenu.includes('- pain (retiré le 03/11/2026)'), 'ligne marquée, jamais effacée');
    attendreEgal(fichiersVocaux.elementsActifs(retrait.contenu), ['Pommes', 'beurre'], 'retiré absent de la lecture');
  });

  await testAsync('Fichiers vocaux Drive : crée « Fichiers vocaux » et le fichier Liste de courses, ajoute puis retire sans effacer', async () => {
    let texteFichier = '';
    const requetes = [];
    const googleConnexionFictif = {
      appeler: async (adresse, options = {}) => {
        const url = new URL(adresse);
        const chemin = decodeURIComponent(url.pathname);
        requetes.push({ url, methode: options.method || 'GET' });
        if (!options.method || options.method === 'GET') {
          if (chemin === '/drive/v3/files/fichier-liste-courses') {
            if (url.searchParams.get('alt') === 'media') return { text: async () => texteFichier };
            return { json: async () => ({ id: 'fichier-liste-courses', trashed: false }) };
          }
          if (chemin === '/drive/v3/files') {
            return { json: async () => ({ files: [] }) };
          }
          throw new Error(`GET inattendu : ${url}`);
        }
        if (options.method === 'POST' && chemin === '/drive/v3/files') {
          const corps = JSON.parse(options.body);
          if (corps.mimeType === 'application/vnd.google-apps.folder') {
            attendreEgal(corps.parents, ['dossier-app-cap'], 'sous-dossier créé dans App Cap');
            return { json: async () => ({ id: 'dossier-fichiers-vocaux' }) };
          }
          attendreEgal(corps.mimeType, 'text/markdown', 'fichier créé en Markdown');
          return { json: async () => ({ id: 'fichier-liste-courses' }) };
        }
        if (options.method === 'PATCH' && chemin === '/upload/drive/v3/files/fichier-liste-courses') {
          texteFichier = options.body;
          return { json: async () => ({ id: 'fichier-liste-courses' }) };
        }
        throw new Error(`Requête inattendue : ${url}`);
      }
    };
    const drive = objetIsole(SOURCE_FICHIERS_VOCAUX_DRIVE, 'fichiersVocauxDrive', {
      localStorage: espaceMemoire(), googleConnexion: googleConnexionFictif, REGLAGES_GOOGLE,
      googlePicker: { dossierAppCap: () => ({ id: 'dossier-app-cap', nom: 'App Cap' }) }
    });
    const nomFichier = REGLAGES_GOOGLE.fichiers_vocaux.liste_courses;
    const ajout = await drive.modifier('liste_courses', nomFichier,
      contenu => fichiersVocaux.ajouterElements(contenu, ['pommes', 'pain']));
    attendreEgal(ajout.ajoutes, ['pommes', 'pain'], 'produits ajoutés');
    attendre(texteFichier.includes('- pommes') && texteFichier.includes('- pain'), 'contenu écrit dans le fichier');
    const retrait = await drive.modifier('liste_courses', nomFichier,
      contenu => fichiersVocaux.retirerElement(contenu, 'pommes'));
    attendre(retrait.retire, 'retrait reconnu');
    attendre(texteFichier.includes('(retiré le') && texteFichier.includes('- pain') && !/\n- pommes\n/.test(texteFichier),
      'zéro perte : la ligne reste, marquée, jamais effacée');
  });

  await testAsync('Fichiers vocaux : le contrôleur ajoute, lit et retire, et répond honnêtement hors connexion', async () => {
    let contenuActuel = '';
    const drivefictif = {
      modifier: async (cle, nomFichier, transformer) => {
        const resultat = transformer(contenuActuel);
        contenuActuel = resultat.contenu;
        return resultat;
      },
      trouverOuCreerFichier: async () => 'fichier-fictif',
      lireTexte: async () => contenuActuel
    };
    const controleur = objetIsole(SOURCE_FICHIERS_VOCAUX_CONTROLEUR, 'fichiersVocauxControleur', {
      navigator: { onLine: true }, googleConnexion: { connecte: () => true }, REGLAGES_GOOGLE,
      fichiersVocauxDrive: drivefictif, fichiersVocaux, fichiersVocauxEcheancier, fichiersVocauxAFaire,
      fichiersVocauxNotes, journalActions: { consigner: () => {} }
    });
    const ajout = await controleur.traiter({ systeme: 'liste', commande: { type: 'ajouter', fichier: 'liste_courses', produits: ['pommes'] } });
    attendre(ajout.type === 'reponse' && ajout.message.includes('pommes'), 'réponse après ajout');
    const lecture = await controleur.traiter({ systeme: 'liste', commande: { type: 'lire', fichier: 'liste_courses' } });
    attendre(lecture.message.includes('pommes'), 'lecture après ajout');
    const retrait = await controleur.traiter({ systeme: 'liste', commande: { type: 'retirer', fichier: 'liste_courses', produit: 'pommes' } });
    attendre(retrait.message.includes('Retiré'), 'réponse après retrait');
    const relecture = await controleur.traiter({ systeme: 'liste', commande: { type: 'lire', fichier: 'liste_courses' } });
    attendre(relecture.message.includes('vide'), 'retiré absent de la lecture, jamais effacé du fichier');
    attendre(contenuActuel.includes('(retiré le'), 'zéro perte dans le fichier');
    const controleurHorsLigne = objetIsole(SOURCE_FICHIERS_VOCAUX_CONTROLEUR, 'fichiersVocauxControleur', {
      navigator: { onLine: false }, googleConnexion: { connecte: () => true }, REGLAGES_GOOGLE,
      fichiersVocauxDrive: drivefictif, fichiersVocaux, fichiersVocauxEcheancier, fichiersVocauxAFaire,
      fichiersVocauxNotes, journalActions: { consigner: () => {} }
    });
    const horsLigne = await controleurHorsLigne.traiter({ systeme: 'liste', commande: { type: 'ajouter', fichier: 'liste_courses', produits: ['lait'] } });
    attendre(horsLigne.message.toLowerCase().includes('pas de connexion'), 'honnête hors connexion, rien inventé');
  });

  await testAsync('Fichiers vocaux : après "terminé", sessionEnCoursDeFermeture() reste vrai pendant l\'écriture (évite le faux "Je n\'ai rien entendu")', async () => {
    let contenuActuel = '';
    let resoudreEcriture;
    const drivefictif = {
      modifier: async (cle, nomFichier, transformer) => {
        await new Promise(resolve => { resoudreEcriture = resolve; });
        const resultat = transformer(contenuActuel);
        contenuActuel = resultat.contenu;
        return resultat;
      },
      trouverOuCreerFichier: async () => 'fichier-fictif',
      lireTexte: async () => contenuActuel
    };
    const controleur = objetIsole(SOURCE_FICHIERS_VOCAUX_CONTROLEUR, 'fichiersVocauxControleur', {
      navigator: { onLine: true }, googleConnexion: { connecte: () => true }, REGLAGES_GOOGLE,
      fichiersVocauxDrive: drivefictif, fichiersVocaux, fichiersVocauxEcheancier, fichiersVocauxAFaire,
      fichiersVocauxNotes, journalActions: { consigner: () => {} }
    });
    controleur.ouvrirSession('bloc_notes');
    controleur.accumuler('Acheter du lait');
    attendreEgal(controleur.sessionEnCoursDeFermeture(), false, 'pas de fermeture avant que "terminé" soit dit');
    const promesse = controleur.fermerSession();
    attendreEgal(controleur.sessionEnCoursDeFermeture(), true, 'fermeture en cours dès l’appel, avant la fin de l’écriture Drive');
    attendreEgal(controleur.sessionActive(), true, 'session encore active pendant l’écriture : app.js ne doit pas la croire fermée sans vérifier sessionEnCoursDeFermeture()');
    resoudreEcriture();
    const resultat = await promesse;
    attendreEgal(controleur.sessionEnCoursDeFermeture(), false, 'fermeture terminée une fois l’écriture finie');
    attendreEgal(controleur.sessionActive(), false, 'session bien fermée');
    attendre(resultat.message.includes('Acheter du lait'), 'contenu dicté bien enregistré');
  });

  test('Fichiers vocaux : listes génériques (achats, films, livres) sans collision', () => {
    attendreEgal(fichiersVocaux.detecterCommande('achats une perceuse'),
      { type: 'ajouter', fichier: 'choses_a_acheter', produits: ['une perceuse'] }, 'achats reconnu');
    attendreEgal(fichiersVocaux.detecterCommande('films Dune et Oppenheimer'),
      { type: 'ajouter', fichier: 'films_a_voir', produits: ['Dune', 'Oppenheimer'] }, 'films reconnu');
    attendreEgal(fichiersVocaux.detecterCommande('livres, lis-moi'), { type: 'lire', fichier: 'livres_a_lire' }, 'livres lecture');
    attendreEgal(fichiersVocaux.detecterCommande('liste pain'), { type: 'ajouter', fichier: 'liste_courses', produits: ['pain'] }, 'liste toujours reconnue');
  });

  test('Fichiers vocaux : singulier et pluriel, avec ou sans virgule (phrases comme le micro les transcrit)', () => {
    attendreEgal(fichiersVocaux.detecterCommande('film Rambo'),
      { type: 'ajouter', fichier: 'films_a_voir', produits: ['Rambo'] }, 'film singulier sans virgule');
    attendreEgal(fichiersVocaux.detecterCommande('film, Rambo'),
      { type: 'ajouter', fichier: 'films_a_voir', produits: ['Rambo'] }, 'film singulier avec virgule');
    attendreEgal(fichiersVocaux.detecterCommande('films, Rambo'),
      { type: 'ajouter', fichier: 'films_a_voir', produits: ['Rambo'] }, 'films pluriel avec virgule');
    attendreEgal(fichiersVocaux.detecterCommande('livre Dune'),
      { type: 'ajouter', fichier: 'livres_a_lire', produits: ['Dune'] }, 'livre singulier');
    attendreEgal(fichiersVocaux.detecterCommande('livre, Dune'),
      { type: 'ajouter', fichier: 'livres_a_lire', produits: ['Dune'] }, 'livre singulier avec virgule');
    attendreEgal(fichiersVocaux.detecterCommande('achat lait'),
      { type: 'ajouter', fichier: 'choses_a_acheter', produits: ['lait'] }, 'achat singulier');
    attendreEgal(fichiersVocaux.detecterCommande('achat, lait'),
      { type: 'ajouter', fichier: 'choses_a_acheter', produits: ['lait'] }, 'achat singulier avec virgule');
    attendreEgal(fichiersVocaux.detecterCommande('listes pain'),
      { type: 'ajouter', fichier: 'liste_courses', produits: ['pain'] }, 'listes pluriel');
    attendreEgal(fichiersVocaux.detecterCommande('liste, pain'),
      { type: 'ajouter', fichier: 'liste_courses', produits: ['pain'] }, 'liste singulier avec virgule');
    attendreEgal(fichiersVocaux.detecterCommande('film lis-moi'), { type: 'lire', fichier: 'films_a_voir' }, 'film singulier lecture');
    attendreEgal(fichiersVocaux.detecterCommande('livre retiré Dune'),
      { type: 'retirer', fichier: 'livres_a_lire', produit: 'Dune' }, 'livre singulier retrait');
  });

  test('Fichiers vocaux : notes (ouverture, fin, titre automatique, ajout sans effacement)', () => {
    attendreEgal(fichiersVocauxNotes.detecterOuverture('bloc-notes, note'), { fichier: 'bloc_notes' }, 'ouverture bloc-notes');
    attendreEgal(fichiersVocauxNotes.detecterOuverture('brouillon vocal, note'), { fichier: 'brouillon_vocal' }, 'ouverture brouillon vocal');
    attendreEgal(fichiersVocauxNotes.detecterOuverture('liste pommes'), null, 'pas de collision avec les listes');
    attendre(fichiersVocauxNotes.estTerminer('terminé'), 'fin reconnue');
    attendre(fichiersVocauxNotes.estTerminer('Terminé.'), 'fin reconnue avec majuscule et point');
    attendre(!fichiersVocauxNotes.estTerminer('je n’ai pas terminé mon café'), 'pas de faux positif');
    attendreEgal(fichiersVocauxNotes.decouperFin('terminé'), { avant: '', termine: true }, 'decouperFin seul, rien avant');
    attendreEgal(fichiersVocauxNotes.decouperFin('range le lait terminé'),
      { avant: 'range le lait', termine: true }, 'decouperFin dans le même souffle, mot terminé coupé');
    attendreEgal(fichiersVocauxNotes.decouperFin('range le lait, terminé.'),
      { avant: 'range le lait', termine: true }, 'decouperFin avec virgule et point');
    attendreEgal(fichiersVocauxNotes.decouperFin('Terminé'),
      { avant: '', termine: true }, 'decouperFin majuscule seule');
    attendreEgal(fichiersVocauxNotes.decouperFin('je n’ai pas terminé mon café'),
      { avant: 'je n’ai pas terminé mon café', termine: false }, 'decouperFin pas de faux positif au milieu');
    attendreEgal(fichiersVocauxNotes.titreCourt('Penser à appeler le plombier demain matin pour la fuite dans la cuisine.'),
      'Penser à appeler le plombier demain matin pour…', 'titre court');
    const texte = fichiersVocauxNotes.ajouterEntree('', 'Idée', 'Contenu dicté.', new Date(2026, 10, 3, 9, 5));
    attendre(texte.includes('## 03/11/2026 09:05 — Idée') && texte.includes('Contenu dicté.'), 'entrée bien formée');
    const deuxieme = fichiersVocauxNotes.ajouterEntree(texte, 'Autre', 'Deuxième contenu.', new Date(2026, 10, 3, 9, 10));
    attendre(deuxieme.includes('Contenu dicté.') && deuxieme.includes('Deuxième contenu.'), 'ajout sans effacer la première entrée');
  });

  test('Fichiers vocaux : tableau Markdown générique (ajout, lecture, retrait sans effacement)', () => {
    const vide = fichiersVocauxTableau.construireFichier([{ titre: 'À venir', colonnes: ['A', 'B'] }]);
    attendre(vide.includes('# À venir') && vide.includes('| A | B |'), 'fichier vide bien formé');
    const avecLigne = fichiersVocauxTableau.ajouterLigne(vide, 'À venir', ['A', 'B'], ['x', 'y']);
    attendreEgal(fichiersVocauxTableau.lignesDonnees(fichiersVocauxTableau.corpsSection(avecLigne, 'À venir')).length, 1, 'une ligne de données');
    attendreEgal(fichiersVocauxTableau.cellules(fichiersVocauxTableau.lignesDonnees(fichiersVocauxTableau.corpsSection(avecLigne, 'À venir'))[0]), ['x', 'y'], 'cellules lues');
    const avecDeux = fichiersVocauxTableau.ajouterLigne(avecLigne, 'À venir', ['A', 'B'], ['z', 'w']);
    attendreEgal(fichiersVocauxTableau.lignesDonnees(fichiersVocauxTableau.corpsSection(avecDeux, 'À venir')).length, 2, 'ajout sans écraser');
    const sansPremiere = fichiersVocauxTableau.retirerLigneParIndex(fichiersVocauxTableau.corpsSection(avecDeux, 'À venir'), 0);
    attendreEgal(fichiersVocauxTableau.lignesDonnees(sansPremiere).map(l => fichiersVocauxTableau.cellules(l)[0]), ['z'], 'retrait par index');
  });

  test('Fichiers vocaux : Échéancier (ajout avec rappel par défaut, terminer déplace sans effacer, lecture triée)', () => {
    const maintenant = new Date(2026, 10, 3, 10, 0);
    const commande = fichiersVocauxEcheancier.detecterCommande('échéance anniversaire de Léa le 8 mars', maintenant);
    attendre(commande && commande.type === 'ajouter' && commande.element === 'anniversaire de Léa', 'commande reconnue');
    attendreEgal(commande.delaiJours, 30, 'rappel par défaut à 30 jours');
    const sansRappel = fichiersVocauxEcheancier.detecterCommande('échéance contrôle technique le 8 mars, pas de rappel', maintenant);
    attendreEgal(sansRappel.delaiJours, null, 'pas de rappel respecté');
    attendreEgal(fichiersVocauxEcheancier.detecterCommande('échéance, lis-moi'), { type: 'lire' }, 'lecture reconnue');
    const { contenu } = fichiersVocauxEcheancier.ajouter('', commande, maintenant);
    attendre(contenu.includes('anniversaire de Léa'), 'ligne ajoutée dans À venir');
    const resultat = fichiersVocauxEcheancier.terminer(contenu, 'anniversaire de Léa', new Date(2026, 10, 4));
    attendre(resultat.trouve, 'échéance trouvée');
    const corpsAVenir = fichiersVocauxTableau.corpsSection(resultat.contenu, 'À venir');
    attendreEgal(fichiersVocauxTableau.lignesDonnees(corpsAVenir).length, 0, 'plus dans À venir');
    const corpsTerminees = fichiersVocauxTableau.corpsSection(resultat.contenu, 'Terminées');
    attendre(fichiersVocauxTableau.cellules(fichiersVocauxTableau.lignesDonnees(corpsTerminees)[0])[9] === '04/11/2026', 'déplacée dans Terminées avec sa date, zéro perte');
  });

  test('Fichiers vocaux : À faire (ajout, priorité, coche et retrait sans effacement, lecture triée, distinct des tâches FICTIF)', () => {
    const maintenant = new Date(2026, 10, 3, 10, 0);
    const commande = fichiersVocauxAFaire.detecterCommande('à faire appeler le garagiste demain, urgent', maintenant);
    attendre(commande && commande.type === 'ajouter', 'commande reconnue');
    attendreEgal(commande.priorite, 'Haute', 'priorité détectée');
    attendre(commande.tache.toLowerCase().includes('appeler le garagiste'), 'tâche propre, sans la date ni le mot urgent');
    const viaRappelleMoi = fichiersVocauxAFaire.detecterCommande('rappelle-moi de sortir les poubelles', maintenant);
    attendre(viaRappelleMoi && viaRappelleMoi.tache.includes('sortir les poubelles'), 'synonyme « rappelle-moi de » reconnu');
    const { contenu } = fichiersVocauxAFaire.ajouter('', commande, maintenant);
    attendre(contenu.includes('appeler le garagiste'), 'ligne ajoutée');
    const coche = fichiersVocauxAFaire.coche(contenu, commande.tache);
    attendre(coche.trouve, 'tâche cochée sans suppression');
    const corps = fichiersVocauxTableau.corpsSection(coche.contenu, 'Tâches');
    attendreEgal(fichiersVocauxTableau.lignesDonnees(corps).length, 1, 'ligne toujours présente après la coche');
    attendreEgal(fichiersVocauxAFaire.lireActives(coche.contenu).length, 0, 'tâche cochée absente de la lecture');
    const { contenu: contenuDeux } = fichiersVocauxAFaire.ajouter(contenu, viaRappelleMoi, maintenant);
    const retrait = fichiersVocauxAFaire.retirer(contenuDeux, 'sortir les poubelles');
    attendre(retrait.trouve && retrait.contenu.includes('(retirée le'), 'retrait marqué, jamais effacé');
  });

  test('Fichiers vocaux : le routeur du contrôleur distingue listes, échéancier et à faire sans collision', () => {
    attendreEgal(fichiersVocauxControleur.detecterCommande('liste pain').systeme, 'liste', 'liste routée');
    attendreEgal(fichiersVocauxControleur.detecterCommande('échéance anniversaire le 8 mars').systeme, 'echeancier', 'échéancier routé');
    attendreEgal(fichiersVocauxControleur.detecterCommande('à faire appeler le garagiste').systeme, 'a_faire', 'à faire routé');
    attendreEgal(fichiersVocauxControleur.detecterCommande('bonjour Cap'), null, 'phrase libre non capturée');
  });

  const erreursPage = window.erreursPage || [];
  const reussis = resultats.filter(r => r.ok).length;
  document.getElementById('resultat-tests').textContent = JSON.stringify({
    erreurs_page: erreursPage,
    reussis,
    total: resultats.length,
    tests: resultats
  });
})();
"""


MANIFEST = "manifest.webmanifest"
FAVICON = "icones/favicon.png"
ATTENDUS_MANIFEST = {
    "name": "Cap",
    "short_name": "Cap",
    "lang": "fr",
    "start_url": "./",
    "scope": "./",
    "display": "standalone",
    "orientation": "portrait",
    "background_color": "#FDE6C3",
    "theme_color": "#4F87B5",
}
ICONES_MANIFEST = [
    ("icones/icone-192.png", 192, "any"),
    ("icones/icone-512.png", 512, "any"),
    ("icones/icone-maskable-512.png", 512, "maskable"),
]


def attendre(condition, message):
    if not condition:
        raise AssertionError(message)


def lire_texte(nom):
    return (APP / nom).read_text(encoding="utf-8")


def lire_json(nom):
    return json.loads(lire_texte(nom))


def lire_html():
    return lire_texte("index.html")


def attribut(balise, nom):
    trouve = re.search(rf'\b{nom}="([^"]*)"', balise)
    return trouve.group(1) if trouve else None


def normaliser(entree):
    return entree[2:] if entree.startswith("./") else entree


def lire_precache():
    texte = lire_texte("service-worker.js")
    trouve = re.search(r"const\s+FICHIERS_PRECACHE\s*=\s*(\[.*?\])\s*;", texte, re.S)
    attendre(trouve, "FICHIERS_PRECACHE introuvable dans service-worker.js")
    try:
        liste = json.loads(trouve.group(1))
    except ValueError as erreur:
        raise AssertionError(f"FICHIERS_PRECACHE n’est pas un tableau JSON valide : {erreur}")
    attendre(isinstance(liste, list) and all(isinstance(e, str) for e in liste),
             "FICHIERS_PRECACHE doit contenir uniquement des chaînes")
    return liste


def lire_png(chemin):
    attendre(chemin.is_file(), f"fichier introuvable : {chemin.relative_to(APP).as_posix()}")
    with open(chemin, "rb") as fichier:
        entete = fichier.read(24)
    attendre(len(entete) == 24 and entete[:8] == b"\x89PNG\r\n\x1a\n" and entete[12:16] == b"IHDR",
             f"signature PNG invalide : {chemin.name}")
    return struct.unpack(">II", entete[16:24])


def verifier_fichiers_requis():
    requis = ["index.html", "style.css", MANIFEST, "service-worker.js", "installation.js", FAVICON]
    requis += [chemin for chemin, _, _ in ICONES_MANIFEST]
    requis += SOURCES
    manquants = [nom for nom in requis if not (APP / nom).is_file()]
    attendre(not manquants, f"fichiers manquants : {', '.join(manquants)}")


def verifier_manifest():
    manifest = lire_json(MANIFEST)
    for champ, valeur in ATTENDUS_MANIFEST.items():
        attendre(manifest.get(champ) == valeur,
                 f"manifest {champ} attendu {valeur!r}, reçu {manifest.get(champ)!r}")


def verifier_icones_manifest():
    icones = lire_json(MANIFEST).get("icons")
    attendre(isinstance(icones, list) and len(icones) == len(ICONES_MANIFEST),
             f"le manifest doit déclarer exactement {len(ICONES_MANIFEST)} icônes")
    for chemin, taille, usage in ICONES_MANIFEST:
        entree = next((i for i in icones if isinstance(i, dict) and i.get("src") == chemin), None)
        attendre(entree is not None, f"icône absente du manifest : {chemin}")
        attendre(entree.get("sizes") == f"{taille}x{taille}",
                 f"taille déclarée incorrecte pour {chemin} : {entree.get('sizes')!r}")
        attendre(entree.get("purpose", "any") == usage,
                 f"usage déclaré incorrect pour {chemin} : {entree.get('purpose')!r}")


def verifier_png():
    for chemin, taille, _ in ICONES_MANIFEST:
        largeur, hauteur = lire_png(APP / chemin)
        attendre(largeur == taille and hauteur == taille,
                 f"dimensions de {chemin} : {largeur}x{hauteur}, attendu {taille}x{taille}")
    largeur, hauteur = lire_png(APP / FAVICON)
    attendre(largeur == 48 and hauteur == 48, f"dimensions de {FAVICON} : {largeur}x{hauteur}, attendu 48x48")


def verifier_liens_manifest_favicon():
    liens = re.findall(r"<link\b[^>]*>", lire_html(), re.I)
    attendre(any(attribut(l, "rel") == "manifest" and attribut(l, "href") == MANIFEST for l in liens),
             f"lien manifest vers {MANIFEST} absent de index.html")
    attendre(any(attribut(l, "rel") == "icon" and attribut(l, "href") == FAVICON for l in liens),
             f"lien favicon vers {FAVICON} absent de index.html")
    attendre(any(attribut(l, "rel") == "apple-touch-icon"
                 and attribut(l, "href") == "icones/icone-192.png" for l in liens),
             "lien apple-touch-icon absent de index.html")


def verifier_liens_locaux():
    references = re.findall(r'\b(?:href|src)="([^"]*)"', lire_html())
    manquants = []
    for reference in references:
        if reference in ("", "./") or reference.startswith(("http://", "https://", "//", "data:", "mailto:", "#")):
            continue
        cible = reference.split("#", 1)[0].split("?", 1)[0]
        if cible and not (APP / cible).is_file():
            manquants.append(reference)
    attendre(not manquants, f"liens locaux introuvables dans index.html : {', '.join(manquants)}")


def verifier_lecteur_mp3_zencoder():
    # Copie du lecteur de Zencoder (07/11/2026, accord de Max) : identique à l'original
    # (empreinte de C:\Users\revox\Cap_lecteur_mp3_essai\index.html) sauf la seule ligne ajoutée, avec son commentaire daté.
    import hashlib
    texte = (APP / "lecteur_mp3" / "index.html").read_bytes().decode("utf-8").replace("\r\n", "\n")
    ajout = ("  // 07/11/2026 (Claude Code, accord de Max) : SEULE ligne ajoutée au lecteur de Zencoder, pour que Cap puisse lancer un morceau, "
             "l'arrêter et savoir quand il finit. Rien d'autre n'a changé.\n"
             "  window.lecteurMp3Zencoder = { jouerFichier: jouerFichier, arreter: arreter, audio: audio };\n")
    attendre(texte.count(ajout) == 1, "ligne ajoutée absente ou en double")
    attendre(hashlib.sha256(texte.replace(ajout, "").encode("utf-8")).hexdigest()
             == "89f175978e471751f9935882d4c73df3303f02ce9d9f0781ea0a5c1fb79b3c4f", "le lecteur de Zencoder a été modifié ailleurs")


def verifier_visionneuse_zencoder():
    # Copie de la visionneuse de Zencoder (07/11/2026, accords de Max) : identique à l'original
    # (empreintes de C:\Users\revox\Cap_visualiseur_essai) sauf : la ligne de l'eau devant à 35 % et les
    # 3 chemins de pdf.js (celui de Cap, app/pdfjs), chacun avec son commentaire daté.
    # Ni journal ni LISEZ_MOI de Zencoder dans Cap.
    import hashlib
    empreinte = lambda texte: hashlib.sha256(texte.encode("utf-8")).hexdigest()
    lire = lambda chemin: (APP / "visionneuse" / chemin).read_bytes().decode("utf-8").replace("\r\n", "\n")
    ajout = ("  // 07/11/2026 (Claude Code, accord de Max) : ligne ajoutée à la visionneuse de Zencoder, pour corriger l'image invisible : "
             "l'eau devant reprend 35 % d'opacité, comme avant. Seul autre changement (même jour, accord de Max) : les chemins de pdf.js, en haut de la page.\n"
             "  intensiteEauDevant = 0.35 * INTENSITE_EAU_UNIQUE;\n")
    chemins_cap = ("<!-- 07/11/2026 (Claude Code, accord de Max) : pdf.js pris dans Cap (app/pdfjs, même fichier, même empreinte, pas de deuxième copie).\n"
                   "     Anciens chemins : bloc_visualiseur/pdfjs/pdf.worker.min.js et bloc_visualiseur/pdfjs/pdf.min.js. -->\n"
                   "<script src=\"../pdfjs/pdf.worker.min.js\"></script>\n<script src=\"../pdfjs/pdf.min.js\"></script>\n")
    chemins_zencoder = "<script src=\"bloc_visualiseur/pdfjs/pdf.worker.min.js\"></script>\n<script src=\"bloc_visualiseur/pdfjs/pdf.min.js\"></script>\n"
    page = lire("index.html")
    attendre(page.count(ajout) == 1 and page.count(chemins_cap) == 1, "changements datés absents ou en double")
    attendre(page.index(ajout) > page.index("  var intensiteEauDevant = INTENSITE_EAU_UNIQUE;"), "ligne ajoutée au mauvais endroit")
    attendre(empreinte(page.replace(ajout, "").replace(chemins_cap, chemins_zencoder)) == "15961ae16fc5ef126c8824e1cc7c600a558e32e4acd9f08b1a54b627d0f8f209", "page de Zencoder modifiée ailleurs")
    ajout_js = ("  // 07/11/2026 (Claude Code, accord de Max) : pdf.js de Cap, rangé dans app/pdfjs (la visionneuse est dans app/visionneuse).\n"
                "  CHEMIN_PDFJS_WORKER = \"../pdfjs/pdf.worker.min.js\";\n")
    js = lire("bloc_visualiseur/visualiseur.js")
    attendre(js.count(ajout_js) == 1, "chemin du worker de pdf.js absent")
    # 08/11/2026 (accord de Max) : zoom corrigé, 4 ajouts datés (dézoom au quart, pincement ≠ double appui).
    ajouts_zoom = [
        "  // 08/11/2026 (Claude Code, accord de Max) : dézoom jusqu'au quart de la taille d'ouverture (au lieu de la moitié).\n  ZOOM_MIN = 0.25;\n",
        "        // 08/11/2026 (Claude Code, accord de Max) : un pincement commence ; ses doigts levés ne comptent pas comme un double appui.\n        doc.pincementRecent = true;\n",
        "        // 08/11/2026 (Claude Code, accord de Max) : nouveau geste, l'ancien pincement est fini.\n        doc.pincementRecent = false;\n",
        "      // 08/11/2026 (Claude Code, accord de Max) : fin d'un pincement = pas un double appui (sinon saut à 2,5 ou retour à 1 au lâcher).\n"
        "      if (doc.pincementRecent) {\n        if (nbPointeursDoc(doc) === 0) doc.pincementRecent = false;\n        doc.dernierAppuiTemps = 0;\n        return;\n      }\n",
    ]
    for morceau in ajouts_zoom:
        attendre(js.count(morceau) == 1, "ajout du zoom absent ou en double")
        js = js.replace(morceau, "")
    attendre(empreinte(js.replace(ajout_js, "")) == "996f1fdd5d1d13775a74e7277ae6dfb90e69ff03a552478efb08ce71de683a0a", "visualiseur.js modifié ailleurs")
    attendre(empreinte(lire("bloc_visualiseur/visualiseur.css")) == "178b4c4c96457df90f1aeaff29430dfe7c05ea4dadc590e34e6b791bf48e9342", "visualiseur.css modifié")
    restes = sorted(p.relative_to(APP).as_posix() for p in (APP / "visionneuse").rglob("*") if p.is_file())
    attendre(restes == ["visionneuse/bloc_visualiseur/visualiseur.css", "visionneuse/bloc_visualiseur/visualiseur.js", "visionneuse/index.html"],
             f"fichiers en trop dans la copie : {restes}")


def verifier_commandes_vocales_jamais_ia():
    # 08/11/2026 (accord de Max) : le tableur « Commandes vocales » n'est jamais envoyé à l'IA.
    module = (APP / "commandes_vocales.js").read_text(encoding="utf-8")
    for interdit in ("cerveau", "anthropic", "claude", "journalIA", "fetch(", "scanLecture"):
        attendre(interdit.lower() not in module.lower(), f"commandes_vocales.js contient « {interdit} »")
    for fichier in ("cerveau.js", "cerveau_claude.js", "cerveau_prepare.js", "scan_lecture.js", "journal_ia.js", "limite_ia.js"):
        texte = (APP / fichier).read_text(encoding="utf-8")
        attendre("commandesVocales" not in texte and "cap_commandes_vocales" not in texte, f"{fichier} touche aux commandes vocales")


def verifier_version_cache():
    attendre(re.search(r"const\s+VERSION_CACHE\s*=\s*['\"]cap-v132['\"]\s*;", lire_texte("service-worker.js")),
             "VERSION_CACHE doit définir cap-v132")


def verifier_precache_fichiers_existent():
    for entree in lire_precache():
        nom = normaliser(entree)
        if nom in ("", "."):
            continue
        attendre((APP / nom).is_file(), f"fichier précaché introuvable : {entree}")


def verifier_precache_couverture():
    precache = {normaliser(e) for e in lire_precache()}
    requis = ["index.html", "style.css", MANIFEST]
    requis += [p.name for p in APP.glob("*.js")]
    requis += [p.relative_to(APP).as_posix() for p in (APP / "icones").glob("*.png")]
    manquants = sorted(nom for nom in requis if nom not in precache)
    attendre(not manquants, f"absents de FICHIERS_PRECACHE : {', '.join(manquants)}")


def verifier_installation_en_dernier():
    if not (APP / "installation.js").is_file():
        return
    scripts = re.findall(r'<script\b[^>]*\bsrc="([^"]*)"', lire_html())
    attendre([normaliser(script) for script in scripts] == SOURCES + ["installation.js"],
             "les scripts du clavier doivent suivre dictee.js, avant app.js et installation.js")


def verifier_rien_de_prive_publie():
    # Les mots privés (prénoms des proches, phrases de la fiche de Max) sont dans mots_prives.txt, jamais publié.
    racine = APP.parent
    liste = racine / "mots_prives.txt"
    attendre(liste.is_file(), "mots_prives.txt absent : impossible de vérifier qu'aucun prénom de proche n'est publié")
    ignore = subprocess.run(["git", "check-ignore", "-q", str(liste)], cwd=racine)
    attendre(ignore.returncode == 0, "mots_prives.txt doit rester dans .gitignore")
    mots = [ligne.strip() for ligne in liste.read_text(encoding="utf-8").splitlines() if ligne.strip() and not ligne.startswith("#")]
    attendre(mots, "mots_prives.txt est vide")
    sortie = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                            cwd=racine, capture_output=True, check=True).stdout.decode("utf-8")
    fautifs = []
    for nom in filter(None, sortie.split("\0")):
        chemin = racine / nom
        # Images et vidéos : binaires (des octets au hasard peuvent ressembler à un mot court) ; la vidéo du
        # galet n'a aucun bloc de métadonnées (titre, auteur, commentaire), vérifié le 06/11/2026.
        if not chemin.is_file() or chemin.suffix.lower() in {".png", ".ico", ".mp4"}:
            continue
        texte = chemin.read_text(encoding="utf-8", errors="ignore").casefold()
        if any(re.search(rf"(?<!\w){re.escape(mot.casefold())}(?!\w)", texte) for mot in mots):
            fautifs.append(nom)
        if re.search(r"sk-ant-(?!FICTIF)[A-Za-z0-9_-]{20,}", chemin.read_text(encoding="utf-8", errors="ignore")):
            fautifs.append(f"{nom} (clé)")
    attendre(not fautifs, f"donnée privée dans des fichiers publiables : {', '.join(fautifs)}")


TESTS_PWA = [
    ("Publication : aucun prénom de proche, aucune phrase de la fiche, aucune clé", verifier_rien_de_prive_publie),
    ("PWA : fichiers requis présents", verifier_fichiers_requis),
    ("PWA : manifest, champs attendus", verifier_manifest),
    ("PWA : manifest, icônes déclarées", verifier_icones_manifest),
    ("PWA : icônes PNG, dimensions et signature", verifier_png),
    ("PWA : HTML, liens manifest et favicon", verifier_liens_manifest_favicon),
    ("PWA : HTML, liens locaux existants", verifier_liens_locaux),
    ("Lecteur MP3 de Zencoder : copie identique, sauf la seule ligne datée du 07/11/2026", verifier_lecteur_mp3_zencoder),
    ("Visionneuse de Zencoder : copie identique, sauf l’eau devant à 35 % et les 3 chemins de pdf.js (datés du 07/11/2026)", verifier_visionneuse_zencoder),
    ("Commandes vocales (08/11/2026) : le tableur n’est jamais envoyé à l’IA", verifier_commandes_vocales_jamais_ia),
    ("PWA : service-worker, version de cache", verifier_version_cache),
    ("PWA : service-worker, fichiers précachés existants", verifier_precache_fichiers_existent),
    ("PWA : service-worker, couverture de la précache", verifier_precache_couverture),
    ("PWA : installation.js chargé en dernier", verifier_installation_en_dernier),
]


def executer_tests_pwa():
    resultats = []
    for nom, fonction in TESTS_PWA:
        try:
            fonction()
            resultats.append({"nom": nom, "ok": True, "erreur": ""})
        except Exception as erreur:
            resultats.append({"nom": nom, "ok": False, "erreur": str(erreur) or type(erreur).__name__})
    return resultats


def afficher_resultat(test):
    if test["ok"]:
        print(f"OK     {test['nom']}")
    else:
        print(f"ECHEC  {test['nom']} : {test['erreur']}")


def construire_page():
    source_stockage = (APP / "stockage.js").read_text(encoding="utf-8")
    scripts = "\n".join(f'<script src="/src/{nom}"></script>' for nom in SOURCES)
    source_json = json.dumps(source_stockage).replace("</", "<\\/")
    source_dictee = (APP / "dictee.js").read_text(encoding="utf-8")
    source_dictee_json = json.dumps(source_dictee).replace("</", "<\\/")
    sources_google = {
        "SOURCE_GOOGLE_CONNEXION": "google_connexion.js",
        "SOURCE_GOOGLE_SHEETS": "google_sheets.js",
        "SOURCE_GOOGLE_AGENDA": "google_agenda.js",
        "SOURCE_SYNCHRONISATION": "synchronisation.js",
        "SOURCE_SERVICE_WORKER": "service-worker.js",
        "SOURCE_APP": "app.js",
        "SOURCE_JOURNAL_ACTIONS": "journal_actions.js",
        "SOURCE_FICHE_RDV": "fiche_rendezvous.js",
        "SOURCE_LISTES_CHOIX": "listes_choix.js",
        "SOURCE_ANNUAIRE": "annuaire.js",
        "SOURCE_SYNCHRO_ANNUAIRE": "synchro_annuaire.js",
        "SOURCE_CHOIX_DATES": "choix_dates.js",
        "SOURCE_FENETRES_LISTES": "fenetres_listes.js",
        "SOURCE_FERMETURE_FENETRES": "fermeture_fenetres.js",
        "SOURCE_GESTE_RETOUR_TEST": "geste_retour.js",
        "SOURCE_COMMANDES_VISIONNEUSE_TEST": "commandes_visionneuse.js",
        "SOURCE_RELATIONS_MP3_TEST": "relations_mp3.js",
        "SOURCE_CERVEAU_CLAUDE_TEST": "cerveau_claude.js",
        "SOURCE_JOURNAL_IA_TEST": "journal_ia.js",
        "SOURCE_SYNCHRONISATION_TEST": "synchronisation.js",
        "SOURCE_COMMANDES_NAVIGATION_TEST": "commandes_navigation.js",
        "SOURCE_SYNCHRO_LISTES": "synchro_listes.js",
        "SOURCE_SAUVEGARDE_DRIVE": "sauvegarde_drive.js",
        "SOURCE_GOOGLE_PICKER": "google_picker.js",
        "SOURCE_CLASSEMENT": "classement.js",
        "SOURCE_JOURNAUX": "journaux.js",
        "SOURCE_FICHIERS_VOCAUX": "fichiers_vocaux.js",
        "SOURCE_FICHIERS_VOCAUX_DRIVE": "fichiers_vocaux_drive.js",
        "SOURCE_FICHIERS_VOCAUX_CONTROLEUR": "fichiers_vocaux_controleur.js",
        "SOURCE_TUILES": "tuiles.js",
        "SOURCE_MODE_TRIER": "mode_trier.js",
        "SOURCE_ECRAN_EAU": "ecran_eau.js",
        "SOURCE_RELATIONS": "relations.js",
        "SOURCE_RELATIONS_CREATION": "relations_creation.js",
        "SOURCE_GOOGLE_COMPTE_RELATIONS": "google_compte_relations.js",
        "SOURCE_COMMANDES_VOCALES_TEST": "commandes_vocales.js",
        "SOURCE_PHRASES_APPRENDRE_TEST": "phrases_apprendre.js",
        "SOURCE_TABLEUR_PHRASES_TEST": "tableur_phrases.js",
        "SOURCE_RELATIONS_MP3_TEST_C73": "relations_mp3.js",
        "SOURCE_INDEX_C74": "index.html",
        "SOURCE_TABLEUR_CAP_TEST": "tableur_cap.js",
        "SOURCE_COMPTE_RELATIONS_C77": "google_compte_relations.js",
        "SOURCE_RELATIONS_COMPTE": "relations_compte.js",
        "SOURCE_RELATIONS_MP3": "relations_mp3.js",
        "SOURCE_ACCUEIL_CAP": "accueil_cap.js",
        "SOURCE_VISIONNEUSE_CAP": "visionneuse_cap.js",
        "SOURCE_HTML": "index.html",
        "SOURCE_STYLE": "style.css",
    }
    scripts_sources_google = []
    for constante, nom in sources_google.items():
        source_google_json = json.dumps(lire_texte(nom)).replace("</", "<\\/")
        scripts_sources_google.append(f"<script>const {constante} = {source_google_json};</script>")
    scripts_sources_google = "\n".join(scripts_sources_google)
    source_style = (APP / "style.css").read_text(encoding="utf-8")
    corps_index = (APP / "index.html").read_text(encoding="utf-8")
    corps_body = re.search(r"<body>(.*?)</body>", corps_index, re.S).group(1)
    corps_body = re.sub(r"<script\b[^>]*>.*?</script>", "", corps_body, flags=re.S)
    return f"""<!doctype html>
<html lang="fr">
<head><meta charset="utf-8"><title>Tests Cap</title><style>{source_style}</style></head>
<body>
<pre id="resultat-tests"></pre>
<script>
window.erreursPage = [];
window.addEventListener('error', e => window.erreursPage.push(String(e.message)));
window.addEventListener('unhandledrejection', e => window.erreursPage.push(String(e.reason)));
// Seule demande réelle permise : l'attente en temps réel des tests (adresse fixe, réponse vide).
const vraiFetchAttente = window.fetch.bind(window);
window.attenteReelle = n => vraiFetchAttente('/attente-reelle?' + Number(n), {{ cache: 'no-store' }});
window.fetch = async () => {{
  const message = 'Vrai fetch interdit dans les tests';
  window.erreursPage.push(message);
  throw new Error(message);
}};
for (const espace of [localStorage, sessionStorage]) {{
  for (const cle of Object.keys(espace)) {{
    if (cle.startsWith('cap_google_')) espace.removeItem(cle);
  }}
}}
// Écran d'eau : la page de test fait comme s'il avait déjà été vu, et ne démarre aucune eau elle-même
// (des tests isolés le vérifient).
sessionStorage.setItem('cap_eau_vue_v1', 'oui');
window.CAP_TESTS = true;
</script>
{corps_body}
<!-- pdf.js chargé d'avance dans les tests (dans Cap : à la demande, voir relations_compte.js), avec son
     « worker » dans la page, comme la visionneuse de Zencoder : Edge sans fenêtre n'attend pas les
     chargements faits plus tard. -->
<script src="/pdfjs/pdf.worker.min.js"></script>
<script src="/pdfjs/pdf.min.js"></script>
{scripts}
<script>const SOURCE_STOCKAGE = {source_json};</script>
<script>const SOURCE_DICTEE = {source_dictee_json};</script>
{scripts_sources_google}
<script>{TESTS_JS}</script>
</body>
</html>
"""


class Gestionnaire(BaseHTTPRequestHandler):
    def do_GET(self):
        chemin = self.path.split("?", 1)[0]
        if chemin == "/tests.html":
            corps = construire_page().encode("utf-8")
            type_contenu = "text/html; charset=utf-8"
        elif chemin.startswith("/src/") and chemin[5:] in SOURCES:
            corps = (APP / chemin[5:]).read_bytes()
            type_contenu = "text/javascript; charset=utf-8"
        elif chemin == "/attente-reelle":
            # Attente en temps réel des tests (voir attendreReel) : réponse vide.
            corps = b""
            type_contenu = "text/plain; charset=utf-8"
        elif chemin in ("/visionneuse/index.html", "/visionneuse/bloc_visualiseur/visualiseur.js", "/visionneuse/bloc_visualiseur/visualiseur.css"):
            # Copie de la visionneuse de Zencoder (08/11/2026 : test du zoom dans la vraie page).
            corps = (APP / chemin[1:]).read_bytes()
            type_contenu = {"html": "text/html", "js": "text/javascript", "css": "text/css"}[chemin.rsplit(".", 1)[1]] + "; charset=utf-8"
        elif chemin == "/lecteur_mp3/index.html":
            # Copie du lecteur MP3 de Zencoder (chargée dans un cadre).
            corps = (APP / chemin[1:]).read_bytes()
            type_contenu = "text/html; charset=utf-8"
        elif chemin in ("/pdfjs/pdf.min.js", "/pdfjs/pdf.worker.min.js"):
            # pdf.js copié dans Cap (lecteur de PDF), chargé seulement au premier PDF.
            corps = (APP / chemin[1:]).read_bytes()
            type_contenu = "text/javascript; charset=utf-8"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", type_contenu)
        self.send_header("Content-Length", str(len(corps)))
        self.end_headers()
        self.wfile.write(corps)

    def log_message(self, format, *args):
        pass


def executer_tests(port):
    url = f"http://127.0.0.1:{port}/tests.html"
    with tempfile.TemporaryDirectory(dir=APP, ignore_cleanup_errors=True) as profil:
        commande = [
            str(EDGE),
            "--headless",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-background-networking",
            f"--user-data-dir={profil}",
            "--dump-dom",
            # 08/11/2026 : 60000 -> 180000 et délai 120 -> 300 s : les transitions douces (vraies attentes) ont fait
            # dépasser les 60 s de temps simulé ; le DOM était alors lu avant la fin des tests (résultat vide).
            "--virtual-time-budget=180000",
            url,
        ]
        try:
            resultat = subprocess.run(commande, capture_output=True, timeout=300)
        except subprocess.TimeoutExpired:
            return None
        return resultat.stdout.decode("utf-8", errors="replace")


def main():
    resultats_pwa = executer_tests_pwa()
    for test in resultats_pwa:
        afficher_resultat(test)
    if not EDGE.exists():
        print(f"Edge introuvable : {EDGE}")
        return 2
    serveur = ThreadingHTTPServer(("127.0.0.1", 0), Gestionnaire)
    thread = threading.Thread(target=serveur.serve_forever, daemon=True)
    thread.start()
    try:
        sortie = executer_tests(serveur.server_address[1])
    finally:
        serveur.shutdown()
        serveur.server_close()

    if sortie is None:
        print("Délai dépassé lors de l’exécution d’Edge.")
        return 1
    trouve = re.search(r'<pre id="resultat-tests">(.*?)</pre>', sortie, re.S)
    if not trouve:
        print("Résultat des tests introuvable dans le DOM.")
        return 1
    rapport = json.loads(html.unescape(trouve.group(1)))

    for erreur in rapport["erreurs_page"]:
        print(f"ERREUR PAGE : {erreur}")
    for test in rapport["tests"]:
        afficher_resultat(test)
    reussis = rapport["reussis"] + sum(1 for test in resultats_pwa if test["ok"])
    total = rapport["total"] + len(resultats_pwa)
    print(f"{reussis}/{total} tests réussis")

    echec = rapport["erreurs_page"] or reussis != total
    return 1 if echec else 0


if __name__ == "__main__":
    sys.exit(main())
