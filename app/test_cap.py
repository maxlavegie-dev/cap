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
SOURCES = ["donnees_fictives.js", "etapes_par_defaut.js", "stockage.js", "vibration.js", "annulation.js", "taches.js", "listes_choix.js", "annuaire.js", "indices_rangement.js", "sous_categories.js", "reglages_google.js", "google_compte_relations.js", "google_connexion.js", "cle_picker.js", "google_picker.js", "google_sheets.js", "google_agenda.js", "fichiers_vocaux_drive.js", "synchronisation.js", "dictee.js", "phrases_clavier.js", "preferences_clavier.js", "voix.js", "comprendre_dates.js", "comprendre_demande.js", "phrases_modifiables.js", "phrases_modifiables_etat.js", "commandes_annuaire.js", "fichiers_vocaux.js", "fichiers_vocaux_notes.js", "fichiers_vocaux_tableau.js", "fichiers_vocaux_echeancier.js", "fichiers_vocaux_a_faire.js", "reglages_ia.js", "limite_ia.js", "cle_ia.js", "actions_cap.js", "cerveau.js", "cerveau_prepare.js", "journal_ia.js", "cerveau_claude.js", "demandes.js", "recherche.js", "journal_actions.js", "fichiers_vocaux_controleur.js", "fiche_rendezvous.js", "choix_dates.js", "fermeture_fenetres.js", "fenetres_listes.js", "synchro_listes.js", "synchro_annuaire.js", "fiche_contact.js", "commande_annuaire_ui.js", "sauvegarde_drive.js", "scan_image.js", "scan_pdf.js", "scan_documents.js", "scan_file.js", "scan_depot.js", "classement.js", "journaux.js", "scan_lecture.js", "scan_nommage.js", "nommage_scan.js", "mots_courts.js", "emetteur.js", "relations.js", "attente.js", "relations_creation.js", "relations_compte.js", "relations_mp3.js", "scan_ecran.js", "tuiles.js", "mode_trier.js", "app.js", "ecran_eau.js"]

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

  function cliquerMicro() {
    micro().click();
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
      + '<h2 class="c4"><span>02_SANTE</span></h2>'
      + '<p class="c5"><span>Commentaire libre sans puce</span></p>'
      + puces(0, ['Prenom_fictif'])
      + puces(1, ['Remboursements', 'Médecine_du_travail_et_expertises', 'Medecins'])
      + puces(2, ['Cardiologie', 'Dermatologie'])
      + puces(0, ['Autre_fictif (aucun sous-dossier pour l’instant)'])
      + ajout + '</body></html>';
  }
  function fauxTableurClassement() {
    return [
      ['Mot-clé repéré', 'Organisme', 'Chemin de destination', 'Type de document', 'Modèle de titre'],
      ['carte test Prenom_fictif', 'Mairie Fictive', '01_IDENTITE_ET_ETAT_CIVIL / Pieces_identite', 'Carte d’identité', '[date] Carte test Prenom_fictif Nom_fictif'],
      ['mutuelle fictive', 'Mutuelle Fictive', '02_SANTE / Prenom_fictif / Remboursements', 'Relevé', '[date] Releve mutuelle fictive Prenom_fictif'],
      ['ordonnance fictive', 'Cabinet Fictif', '02_SANTE / Prenom_fictif / Medecins / Cardiologie', 'Ordonnance', '[date] Ordonnance cardiologie Prenom_fictif'],
      ['medecine du travail fictive', 'Service Fictif', '02_SANTE / Prenom_fictif / Medecine_du_travail_et_expertises', 'Convocation', '[date] Convocation medecine du travail Prenom_fictif'],
      ['banque fictive', 'Banque Fictive', '04_BANQUE_ET_FINANCES / Prenom_fictif / Comptes_bancaires', 'Relevé', '[date] Releve banque fictive'],
      ['', '', '', '', ''],
      ['ligne incomplète fictive', 'Organisme Fictif', '', 'Courrier', '']
    ];
  }

  await testAsync('Classement étape 1 : Doc lu par niveaux, règles et 00_A_CLASSER écartés, parenthèses retirées', async c => {
    const classementIsole = objetIsole(SOURCE_CLASSEMENT, 'classement', { googleConnexion: c.googleConnexion, googlePicker: {} });
    const arbre = classementIsole.analyserArchitecture(fauxDocArchitecture());
    attendreEgal(arbre.racine.enfants.map(e => e.nom), ['01_IDENTITE_ET_ETAT_CIVIL', '02_SANTE'], 'dossiers principaux');
    attendreEgal(arbre.sections_ignorees, 2, 'règles et 00_A_CLASSER écartés');
    const sante = arbre.racine.enfants[1];
    attendreEgal(sante.enfants.map(e => e.nom), ['Prenom_fictif', 'Autre_fictif'], 'niveau 1 et parenthèse retirée');
    attendreEgal(sante.enfants[0].enfants.map(e => e.nom), ['Remboursements', 'Médecine_du_travail_et_expertises', 'Medecins'], 'niveau 2, accent gardé');
    attendreEgal(sante.enfants[0].enfants[2].enfants.map(e => e.nom), ['Cardiologie', 'Dermatologie'], 'niveau 3');
    attendre(!JSON.stringify(arbre).includes('Règle fictive') && !JSON.stringify(arbre).includes('Dossier_main_fictif'), 'règle ou archive faite main lue comme dossier');
    attendreEgal(arbre.doutes.length, 0, 'doutes inattendus');
  });

  await testAsync('Classement étape 1 : tableur de 5 lignes, chemins vérifiés dans le Doc, nom exact du Doc gardé', async c => {
    const classementIsole = objetIsole(SOURCE_CLASSEMENT, 'classement', { googleConnexion: c.googleConnexion, googlePicker: {} });
    const arbre = classementIsole.analyserArchitecture(fauxDocArchitecture());
    const tableur = classementIsole.analyserTableur(fauxTableurClassement());
    attendreEgal(tableur.lignes.length, 5, 'lignes lues');
    attendreEgal(tableur.ignorees.map(l => l.numero), [8], 'ligne incomplète écartée (ligne 8), ligne vide ignorée');
    attendreEgal(tableur.lignes[2].chemin, ['02_SANTE', 'Prenom_fictif', 'Medecins', 'Cardiologie'], 'chemin coupé sur « / »');
    const v = tableur.lignes.map(l => classementIsole.verifierChemin(l.chemin, arbre));
    attendreEgal(v.map(x => x.ok), [true, true, true, true, false], 'chemins trouvés');
    attendreEgal(v[3].noms[2], 'Médecine_du_travail_et_expertises', 'sans accent dans le tableur, nom exact du Doc');
    attendreEgal([v[4].raison, v[4].niveau], ['absent_du_doc', 0], 'chemin absent du Doc refusé');
    const resume = classementIsole.resumer(tableur, arbre);
    attendreEgal([resume.lignes, resume.lignes_ignorees, resume.dossiers_principaux, resume.chemins_trouves, resume.chemins_absents],
      [5, 1, 2, 4, 1], 'résumé');
    const texte = classementIsole.texteResume(resume);
    attendre(['Prenom_fictif', 'Fictive', 'SANTE', 'carte test'].every(mot => !texte.includes(mot)), 'un nom apparaît dans le résumé');
    // Doublon dans le Doc : deux noms identiques sans accents au même endroit = refus, jamais de choix.
    const double = fauxDocArchitecture('<ul class="lst-kix_autre-0 start"><li><span>prénom_FICTIF</span></li></ul>');
    const arbreDouble = classementIsole.analyserArchitecture(double);
    attendreEgal(arbreDouble.doutes.map(d => d.type), ['double'], 'doublon signalé');
    attendreEgal(classementIsole.verifierChemin(['02_SANTE', 'Prenom_fictif', 'Remboursements'], arbreDouble).raison,
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
      Dictionnaire: { A: ['Prénom', 'Jean'], B: ['Nom', 'Fictif'], C: ['Type', 'Personne'], E: ['Téléphone', '04 00 00 00 01'], G: ['Domaine', 'Santé FICTIVE'] }
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

  await testAsync('Compte Cap (FAUX) : connexion avec lecture seule pour CE compte seulement, identifiant gardé sur le téléphone, retour pris sans gêner la connexion du compte personnel', async c => {
    // Le compte personnel garde exactement ses deux droits limités.
    attendreEgal([...REGLAGES_GOOGLE.autorisations], ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/calendar.app.created'], 'droits du compte personnel');
    attendreEgal([...REGLAGES_GOOGLE.autorisations_relations], ['https://www.googleapis.com/auth/drive.readonly'], 'droit du compte Cap');
    const vierge = compteRelationsIsole(c);
    await attendreRejet(() => vierge.seConnecter(), 'identifiant du compte Cap');
    await attendreRejet(() => vierge.enregistrerAdresse('pas un identifiant'), 'incomplet');
    const { m, url } = connecterCompteFictif(c);
    attendreEgal(url.origin + url.pathname, 'https://accounts.google.com/o/oauth2/v2/auth', 'page de Google');
    attendreEgal(url.searchParams.get('scope'), 'https://www.googleapis.com/auth/drive.readonly', 'droit demandé');
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
    await attendreQue(() => el('page-pdf-relations').textContent === 'PDF 1 sur 2 · Page 1 sur 2', `PDF : ${el('page-pdf-relations').textContent}`, 600);
    attendre(el('pdf-avant-relations').disabled && !el('pdf-apres-relations').disabled, 'boutons du PDF 1');
    attendre(el('lecteur-pdf-relations').open, 'lecteur fermé');
    const canvas = el('canvas-pdf-relations');
    attendre(canvas.width >= 200 && canvas.height === canvas.width, `taille du dessin ${canvas.width} x ${canvas.height}`);
    const noir = (x, y) => { const p = canvas.getContext('2d').getImageData(Math.floor(canvas.width * x), Math.floor(canvas.height * y), 1, 1).data; return p[3] > 200 && p[0] + p[1] + p[2] < 100; };
    attendre(noir(0.25, 0.25) && !noir(0.75, 0.75), 'page 1 mal dessinée');
    attendre(el('pdf-precedente-relations').disabled && !el('pdf-suivante-relations').disabled, 'boutons de page 1');
    el('pdf-suivante-relations').click();
    await attendreQue(() => el('page-pdf-relations').textContent === 'PDF 1 sur 2 · Page 2 sur 2' && noir(0.75, 0.75), 'page 2', 600);
    attendre(!noir(0.25, 0.25), 'page 2 mal dessinée');
    // PDF suivant : le 2e PDF s'ouvre à sa page 1.
    const mediasAvant = c.requetes.filter(q => q.url.searchParams.get('alt') === 'media').length;
    el('pdf-apres-relations').click();
    await attendreQue(() => el('page-pdf-relations').textContent === 'PDF 2 sur 2 · Page 1 sur 2' && noir(0.25, 0.25), `PDF suivant : ${el('page-pdf-relations').textContent}`, 600);
    attendre(!el('pdf-avant-relations').disabled && el('pdf-apres-relations').disabled, 'boutons du PDF 2');
    attendreEgal(c.requetes.filter(q => q.url.searchParams.get('alt') === 'media').length, mediasAvant + 1, 'PDF suivant non lu');
    const ids = c.requetes.filter(q => q.url.searchParams.get('alt') === 'media').map(q => q.url.pathname);
    attendre(ids.at(-1) !== ids.at(-2), 'toujours le même PDF');
    el('pdf-avant-relations').click();
    await attendreQue(() => el('page-pdf-relations').textContent === 'PDF 1 sur 2 · Page 1 sur 2', 'PDF précédent', 600);
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
    const bouton = el('fermer-lecteur-mp3').getBoundingClientRect();
    attendre(bouton.top > 700 && bouton.bottom <= 900 && Math.abs(bouton.left + bouton.width / 2 - 206) < 2, `bouton pas posé en bas du lecteur : ${JSON.stringify(bouton)}`);
    attendreEgal(vue.getComputedStyle(el('fermer-lecteur-mp3')).position, 'absolute', 'bouton hors du lecteur');
    attendre(Number(vue.getComputedStyle(el('fermer-lecteur-mp3')).zIndex) > 0, 'bouton sous le lecteur');
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
    // Bouton posé sur le lecteur, au-dessus de « Arrêter et fermer ».
    attendre(el('reconnecter-lecteur-mp3').getBoundingClientRect().bottom <= el('fermer-lecteur-mp3').getBoundingClientRect().top, 'boutons l’un sur l’autre');
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
    attendreEgal((SOURCE_RELATIONS_MP3.match(/stockage\./g) || []).length, 3, 'autre chose gardé');
    const fin = SOURCE_RELATIONS_MP3.slice(SOURCE_RELATIONS_MP3.lastIndexOf('})();'));
    attendre(/!\(typeof window !== 'undefined' && window\.CAP_TESTS\)/.test(fin), 'branché dans les tests');
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
    attendre(ui.parId('ecran-eau').contains(ui.doc.elementFromPoint(...centre(ui.parId('ouvrir-scanner')))), 'Cap touchable sous l’eau');
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
    for (const id of ['ouvrir-scanner', 'aller-eau']) {
      attendreEgal(ui.doc.elementFromPoint(...centre(ui.parId(id))), ui.parId(id), `bouton de Cap recouvert après l’entrée : ${id}`);
    }
    let ouvert = false;
    ui.parId('ouvrir-scanner').addEventListener('click', () => { ouvert = true; }, { once: true });
    const [x, y] = centre(ui.parId('ouvrir-scanner'));
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
    attendreEgal(ui.doc.elementFromPoint(...centre(ui.parId('ouvrir-scanner'))), ui.parId('ouvrir-scanner'), 'Scanner recouvert après l’entrée');
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
    // Fond pâle unique pour l'accueil et l'eau.
    const fond = ui.cadre.contentWindow.getComputedStyle(ui.doc.documentElement).getPropertyValue('--fond').trim().toLowerCase();
    attendreEgal(fond, '#eaf1f4', 'teinte de fond');
    attendreEgal(ui.cadre.contentWindow.getComputedStyle(ui.doc.body).backgroundColor, 'rgb(234, 241, 244)', 'fond de l’accueil');
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
    const fondHex = fenetre.getComputedStyle(ui.doc.documentElement).getPropertyValue('--fond').trim();
    const clair = [1, 3, 5].map(i => parseInt(fondHex.slice(i, i + 2), 16));
    const pireEau = clair.map((c, i) => Math.round(c * 0.8 + [120, 150, 165][i] * 0.2) - 22);
    const opaciteEau = Number(fenetre.getComputedStyle(ui.parId('eau-accueil')).opacity);
    const eauVue = melange(pireEau, opaciteEau, clair);
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
    ui.parId('basculer-vue').click();
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
      if (vue === 'accueil') attendre(boutons.includes(ui.parId('ouvrir-scanner')), 'Scanner absent des boutons testés');
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
    ui.parId('ouvrir-scanner').addEventListener('click', () => { ouvert = true; }, { once: true });
    const [x, y] = centre(ui.parId('ouvrir-scanner'));
    const cible = ui.doc.elementFromPoint(x, y);
    cible.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, pointerId: 3, clientX: x, clientY: y, isPrimary: true }));
    cible.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, pointerId: 3, clientX: x, clientY: y, isPrimary: true }));
    cible.click();
    attendre(ouvert, 'Scanner ne répond pas avec l’eau derrière');
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
    attendreEgal(fenetre2.getComputedStyle(ui2.doc.body).backgroundColor, 'rgb(234, 241, 244)', 'fond pâle absent sans eau');
    const centre = el => { const r = el.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; };
    attendreEgal(ui2.doc.elementFromPoint(...centre(ui2.parId('ouvrir-scanner'))), ui2.parId('ouvrir-scanner'), 'Scanner recouvert sans eau');
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
      ['rendez-vous demain à midi chez le dentiste FICTIF', '2026-10-30', '12:00', []],
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
    for (const cible of [ui.doc.querySelector('header.horloge'), ui.doc.querySelector('footer.dictee'), ui.parId('microphone')]) {
      const rectangle = cible.getBoundingClientRect();
      attendre(rectangle.width > 0 && rectangle.height > 0, 'horloge ou commandes invisibles');
      attendre(rectangle.top >= 0 && rectangle.bottom <= ui.cadre.clientHeight + 1, 'horloge ou commandes hors écran');
    }
    attendre(ui.parId('date').textContent.length > 0, 'date vide');
    attendre(!ui.parId('heure'), 'heure encore affichée');
    const recherche = ui.parId('zone-recherche').getBoundingClientRect();
    const barre = ui.doc.querySelector('.barre-recherche').getBoundingClientRect();
    attendre(barre.bottom <= ui.doc.querySelector('footer.dictee').getBoundingClientRect().top + 1, 'barre de recherche pas au-dessus des boutons');
    attendre(recherche.top > ui.cadre.clientHeight / 2, 'barre de recherche pas en bas');
    attendre(ui.doc.querySelector('.choix-source').contains(ui.parId('source-recherche')), 'menu hors de la barre');
    ui.parId('basculer-vue').click();
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
    const sansHeure = actionsCap.preparerProposition('proposer_rendez_vous', { titre: 'Dentiste FICTIF', date: '2027-01-11', lieu: 'rue FICTIVE' });
    attendreEgal([sansHeure.manque, sansHeure.texte], ['heure', 'À quelle heure ?'], 'heure manquante : une seule question');
    const complete = actionsCap.completerProposition(sansHeure, 'à 15h30');
    attendreEgal(actionsCap.preparerProposition('proposer_rendez_vous', complete).texte,
      'Rendez-vous « Dentiste FICTIF » le lundi 11 janvier 2027 à 15 h 30, rue FICTIVE, c’est bien ça ?', 'jour de la semaine calculé par Cap');
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
    attendreEgal([...select.options].map(option => option.textContent),
      ['Tâches', 'Rendez-vous', 'Gmail (plus tard)', 'Drive (plus tard)', 'Archives perso (plus tard)', 'Mémoire perso (plus tard)'], 'options');
    attendreEgal(select.selectedIndex, 0, 'choix initial');
    attendre([...select.options].slice(2).every(option => option.disabled), 'option future accessible');
    const style = ui.cadre.contentWindow.getComputedStyle(select.options[2]);
    attendre(style.color !== ui.cadre.contentWindow.getComputedStyle(select.options[0]).color, 'options non grisées');
    const champ = ui.parId('saisie-recherche');
    attendreEgal([champ.type, champ.getAttribute('enterkeyhint'), champ.autocomplete], ['search', 'search', 'off'], 'champ mobile');
    attendre(Boolean(champ.getAttribute('aria-label')), 'étiquette absente');
  });

  await testAsync('Recherche accueil : résultats à chaque input, vide et message exact', async c => {
    const ui = preparerInterface(c);
    const champ = ui.parId('saisie-recherche');
    const liste = ui.parId('resultats-recherche');
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
    ui.parId('source-recherche').value = ui.parId('source-recherche').options[1].value;
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
    ui.parId('source-recherche').selectedIndex = 1;
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
    ui.parId('saisie-recherche').value = 'fictif';
    ui.parId('saisie-recherche').dispatchEvent(new Event('input'));
    attendre(ui.doc.documentElement.scrollWidth <= 360 && ui.doc.body.scrollWidth <= 360, 'débordement horizontal');
    attendre(ui.doc.documentElement.scrollHeight <= 560 && ui.doc.body.scrollHeight <= 560, 'débordement vertical');
    const liste = ui.parId('resultats-recherche');
    attendre(liste.scrollHeight > liste.clientHeight && liste.clientHeight > 0, 'résultats non défilables');
    attendre(liste.getBoundingClientRect().bottom <= 560, 'résultats hors écran');
    attendre(liste.getBoundingClientRect().bottom <= ui.doc.querySelector('.barre-recherche').getBoundingClientRect().top, 'résultats pas au-dessus de la barre');
    attendre(liste.getBoundingClientRect().top >= ui.doc.querySelector('header.horloge').getBoundingClientRect().bottom, 'résultats sur la date');
    for (const id of ['microphone', 'ouvrir-clavier', 'ajouter', 'saisie-recherche', 'source-recherche']) {
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
    ui.parId('microphone').click();
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
    for (const phrase of ['Annuler le rendez-vous chez le dentiste', 'Annule ma réunion de lundi', 'Appeler Annie'])
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
      document.getElementById('microphone').click();
      attendreEgal(tache.abandonnee_le, '', '« Annule » à la voix remet la tâche');
      document.getElementById('microphone').click();
      attendre(/plus rien à annuler/.test(statut.textContent), 'rien à annuler deux fois');
    } finally {
      Object.assign(dictee, sauve);
    }
    attendreEgal(TACHES.length, nombre, 'aucune tâche « Annule » créée, rien effacé');
    abandonner(tache.id);
  });

  await (async () => {
    const nom = 'Mode conversation : appui long, écoute continue, « stop », bouton Arrêter';
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
      await pause(500);
      micro.dispatchEvent(new Event('pointerup'));
      attendre(bandeau.hidden && ecoutes === 0, 'appui court : pas de mode conversation');
      micro.dispatchEvent(new Event('pointerdown'));
      await pause(2100);
      attendre(!bandeau.hidden && micro.classList.contains('live'), 'appui long : mode conversation visible');
      micro.click();
      attendre(!bandeau.hidden, 'le clic qui suit l’appui long n’arrête pas le mode');
      await pause(1200);
      const ajoutees = TACHES.slice(nombre).map(tache => tache.intitule);
      attendreEgal(ajoutees, ['FICTIF live un', 'FICTIF live deux'], 'deux phrases traitées sans rappuyer');
      attendre(bandeau.hidden && !micro.classList.contains('live'), '« stop » arrête le mode conversation');
      attendre(document.getElementById('statut').textContent.includes('Mode conversation arrêté'), 'arrêt annoncé');
      phrases.push();
      micro.dispatchEvent(new Event('pointerdown'));
      await pause(2100);
      attendre(!bandeau.hidden, 'mode relancé');
      document.getElementById('arreter-live').click();
      attendre(bandeau.hidden, 'bouton Arrêter');
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
    const commande = fichiersVocauxAFaire.detecterCommande('à faire appeler le dentiste demain, urgent', maintenant);
    attendre(commande && commande.type === 'ajouter', 'commande reconnue');
    attendreEgal(commande.priorite, 'Haute', 'priorité détectée');
    attendre(commande.tache.toLowerCase().includes('appeler le dentiste'), 'tâche propre, sans la date ni le mot urgent');
    const viaRappelleMoi = fichiersVocauxAFaire.detecterCommande('rappelle-moi de sortir les poubelles', maintenant);
    attendre(viaRappelleMoi && viaRappelleMoi.tache.includes('sortir les poubelles'), 'synonyme « rappelle-moi de » reconnu');
    const { contenu } = fichiersVocauxAFaire.ajouter('', commande, maintenant);
    attendre(contenu.includes('appeler le dentiste'), 'ligne ajoutée');
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
    attendreEgal(fichiersVocauxControleur.detecterCommande('à faire appeler le dentiste').systeme, 'a_faire', 'à faire routé');
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
    # Copie de la visionneuse de Zencoder (07/11/2026, accord de Max) : identique à l'original
    # (empreintes de C:\\Users\\revox\\Cap_visualiseur_essai) sauf la seule ligne ajoutée (eau devant à 35 %), avec son commentaire daté.
    # Ni journal ni LISEZ_MOI de Zencoder dans Cap.
    import hashlib
    empreinte = lambda texte: hashlib.sha256(texte.encode("utf-8")).hexdigest()
    lire = lambda chemin: (APP / "visionneuse" / chemin).read_bytes().decode("utf-8").replace("\r\n", "\n")
    ajout = ("  // 07/11/2026 (Claude Code, accord de Max) : SEULE ligne ajoutée à la visionneuse de Zencoder, pour corriger l'image invisible : "
             "l'eau devant reprend 35 % d'opacité, comme avant. Rien d'autre n'a changé.\n"
             "  intensiteEauDevant = 0.35 * INTENSITE_EAU_UNIQUE;\n")
    page = lire("index.html")
    attendre(page.count(ajout) == 1, "ligne ajoutée absente ou en double")
    attendre(page.index(ajout) > page.index("  var intensiteEauDevant = INTENSITE_EAU_UNIQUE;"), "ligne ajoutée au mauvais endroit")
    attendre(empreinte(page.replace(ajout, "")) == "15961ae16fc5ef126c8824e1cc7c600a558e32e4acd9f08b1a54b627d0f8f209", "page de Zencoder modifiée ailleurs")
    attendre(empreinte(lire("bloc_visualiseur/visualiseur.js")) == "996f1fdd5d1d13775a74e7277ae6dfb90e69ff03a552478efb08ce71de683a0a", "visualiseur.js modifié")
    attendre(empreinte(lire("bloc_visualiseur/visualiseur.css")) == "178b4c4c96457df90f1aeaff29430dfe7c05ea4dadc590e34e6b791bf48e9342", "visualiseur.css modifié")
    restes = sorted(p.relative_to(APP).as_posix() for p in (APP / "visionneuse").rglob("*") if p.is_file())
    attendre(restes == ["visionneuse/bloc_visualiseur/visualiseur.css", "visionneuse/bloc_visualiseur/visualiseur.js", "visionneuse/index.html"],
             f"fichiers en trop dans la copie : {restes}")


def verifier_version_cache():
    attendre(re.search(r"const\s+VERSION_CACHE\s*=\s*['\"]cap-v72['\"]\s*;", lire_texte("service-worker.js")),
             "VERSION_CACHE doit définir cap-v72")


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
    ("Visionneuse de Zencoder : copie identique, sauf la seule ligne datée du 07/11/2026 (eau devant à 35 %)", verifier_visionneuse_zencoder),
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
        "SOURCE_RELATIONS_COMPTE": "relations_compte.js",
        "SOURCE_RELATIONS_MP3": "relations_mp3.js",
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
            "--virtual-time-budget=60000",
            url,
        ]
        try:
            resultat = subprocess.run(commande, capture_output=True, timeout=120)
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
