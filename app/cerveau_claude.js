'use strict';

// Fournisseur « Claude Haiku » : payant, utilisé seulement si Max a tapé sa clé dans Cap
// ET si le document de consignes est validé (pas de mot BROUILLON sur sa première ligne).
// Il ne reçoit que la phrase de Max, les noms des catégories fictives et les derniers échanges de la conversation.
// La fiche de consignes est lue à chaque ouverture de Cap, en tâche de fond : sans elle, l'IA n'est jamais appelée.
const cerveauClaude = (() => {
  const cleFiche = 'cap_consignes_v1';
  const cleFicheTelephone = 'cap_fiche_consignes_v1';
  let origine = '';
  let consignes = null;
  let erreurConsignes = '';
  let chargement = null;
  let historique = [];

  function empreinte(texte) {
    let valeur = 5381;
    for (let i = 0; i < texte.length; i += 1) valeur = ((valeur * 33) ^ texte.charCodeAt(i)) >>> 0;
    return valeur.toString(16).padStart(8, '0');
  }

  // { empreinte, lue_le, version_du } : quand la fiche a été lue, et depuis quand elle n'a pas changé.
  function infoConsignes() {
    try {
      const info = JSON.parse(localStorage.getItem(cleFiche));
      return info && typeof info.empreinte === 'string' ? info : null;
    } catch (erreur) {
      return null;
    }
  }

  function retenirLecture(texte) {
    const avant = infoConsignes();
    const nouvelle = empreinte(texte);
    const maintenant = new Date().toISOString();
    const changee = Boolean(avant && avant.empreinte !== nouvelle);
    const info = { empreinte: nouvelle, lue_le: maintenant, version_du: avant && !changee ? avant.version_du : maintenant, origine };
    try {
      localStorage.setItem(cleFiche, JSON.stringify(info));
    } catch (erreur) {
      // Rien de grave : la fiche reste chargée pour cette ouverture.
    }
    if (changee && typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('cap-consignes-changees', { detail: info }));
  }

  // La fiche de Max est collée une seule fois dans Cap et reste sur ce téléphone, comme la clé.
  // Elle n'est jamais publiée : le projet public ne contient qu'une fiche de secours neutre.
  function ficheTelephone() {
    try {
      return String(localStorage.getItem(cleFicheTelephone) || '').trim();
    } catch (erreur) {
      return '';
    }
  }

  function enregistrerFiche(valeur) {
    const texte = String(valeur ?? '').replace(/\r\n?/g, '\n').trim();
    if (!texte) throw new Error('La fiche est vide : rien n’a été enregistré.');
    if (texte.length > REGLAGES_IA.fiche_maximum_caracteres) {
      throw new Error(`La fiche est trop longue (${REGLAGES_IA.fiche_maximum_caracteres} caractères au plus) : rien n’a été enregistré.`);
    }
    try {
      localStorage.setItem(cleFicheTelephone, texte);
    } catch (erreur) {
      throw new Error('La fiche n’a pas pu être enregistrée sur ce téléphone.');
    }
    return relire();
  }

  function retirerFiche() {
    try {
      localStorage.removeItem(cleFicheTelephone);
    } catch (erreur) {
    }
    return relire();
  }

  function relire() {
    consignes = null;
    erreurConsignes = '';
    chargement = null;
    return precharger();
  }

  function origineFiche() {
    return ficheTelephone() ? 'telephone' : 'secours';
  }

  async function lireFiche() {
    let texte = ficheTelephone();
    if (texte) {
      origine = 'telephone';
      validerFiche(texte);
      return;
    }
    try {
      const reponse = await fetch(REGLAGES_IA.fichier_consignes, { cache: 'no-cache' });
      if (!reponse.ok) throw new Error('illisible');
      texte = String(await reponse.text()).trim();
    } catch (erreur) {
      // Une copie déjà lue à cette ouverture reste valable (réseau coupé entre-temps).
      if (!consignes) erreurConsignes = 'Je n’ai pas pu lire ma fiche de consignes.';
      return;
    }
    if (ficheTelephone()) return;
    origine = 'secours';
    validerFiche(texte);
  }

  function validerFiche(texte) {
    const premiereLigne = texte.split('\n', 1)[0];
    if (!texte || premiereLigne.toLocaleUpperCase('fr').includes(REGLAGES_IA.marqueur_brouillon)) {
      consignes = null;
      erreurConsignes = 'Ma fiche de consignes n’est pas encore validée par Max.';
      return;
    }
    consignes = texte;
    erreurConsignes = '';
    retenirLecture(texte);
  }

  function precharger() {
    if (!chargement) chargement = lireFiche().finally(() => { chargement = null; });
    return chargement;
  }

  async function chargerConsignes() {
    if (!consignes) {
      await Promise.race([precharger(), new Promise(resolve => setTimeout(resolve, REGLAGES_IA.attente_consignes_ms))]);
    }
    if (!consignes) throw new Error(erreurConsignes || 'Ma fiche de consignes n’est pas encore chargée.');
    return consignes;
  }

  async function etatConsignes() {
    try {
      await chargerConsignes();
      return 'pret';
    } catch (erreur) {
      return erreur.message;
    }
  }

  // « Nous sommes le vendredi 30 octobre 2026, il est 10 h 37. », à l'heure de Paris.
  function maintenantParis(date = new Date()) {
    const jour = new Intl.DateTimeFormat('fr-FR', { timeZone: 'Europe/Paris', weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }).format(date);
    const parties = Object.fromEntries(new Intl.DateTimeFormat('fr-FR', { timeZone: 'Europe/Paris', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' })
      .formatToParts(date).map(partie => [partie.type, partie.value]));
    return `Nous sommes le ${jour}, il est ${Number(parties.hour)} h ${parties.minute}.`;
  }

  function outils(contexte) {
    return actionsCap.CATALOGUE.filter(action => contexte.actions.includes(action.nom)).map(action => ({
      name: action.nom,
      description: action.description,
      input_schema: {
        type: 'object',
        properties: Object.fromEntries(Object.entries(action.parametres).map(([nom, description]) => [nom, { type: 'string', description }])),
        required: action.obligatoires || []
      }
    }));
  }

  function systeme(texteConsignes, contexte) {
    const categories = contexte.categories.map(({ nom, sous_categories: sous }) => (sous.length ? `${nom} (${sous.join(', ')})` : nom));
    return [
      maintenantParis(),
      texteConsignes,
      `Catégories de Cap : ${categories.join(' ; ')}. « ${contexte.a_trier} » si aucune ne convient clairement.`,
      'Pour agir, utilise un outil ; recopie l’intitulé de Max mot pour mot. Une seule action par réponse.',
      'Tu ne connais aucun numéro, adresse ou coordonnée que Max ne t’a pas donné dans cette conversation : dans ce cas, réponds « Je ne sais pas. » sans rien inventer.'
    ].join('\n');
  }

  // Garde-fou : un numéro de téléphone que Max n'a jamais dit est forcément inventé.
  function chiffres(texte) {
    return String(texte || '').replace(/\D/g, '');
  }

  function numeroInvente(paroles, texte) {
    const numeros = String(paroles || '').match(/(?:\+\d{1,3}[\s.-]?)?\(?\d(?:[\s.()-]?\d){7,}/g) || [];
    if (!numeros.length) return false;
    const dits = [texte, ...historique.filter(message => message.role === 'user').map(message => message.content)].map(chiffres).join(' ');
    return numeros.some(numero => {
      const seul = chiffres(numero);
      const national = seul.replace(/^33/, '0');
      return !dits.includes(seul) && !dits.includes(national) && !dits.includes(national.replace(/^0/, ''));
    });
  }

  function retenir(texteMax, texteCap, appel = null) {
    const action = appel ? `${appel.name} : ${Object.entries(appel.input || {}).map(([nom, valeur]) => `${nom} = ${valeur}`).join(', ')}` : '';
    historique.push({ role: 'user', content: texteMax }, { role: 'assistant', content: `${texteCap || ''}${action ? ` [action ${action}]` : ''}`.trim() || '…' });
    historique = historique.slice(-2 * REGLAGES_IA.echanges_retenus);
    journalIA.noter({ dit: texteMax, repondu: texteCap, action });
  }

  // Zéro reformulation : l'intitulé doit se trouver tel quel dans ce que Max a dit (maintenant ou juste avant).
  function motPourMot(intitule, texte) {
    const { plier } = cerveau.texte;
    const cherche = plier(intitule).replace(/ +/g, ' ').trim();
    if (!cherche) return true;
    const dits = [texte, ...historique.filter(message => message.role === 'user').map(message => message.content)];
    return dits.some(dit => plier(dit).replace(/ +/g, ' ').includes(cherche));
  }

  function erreurHttp(statut) {
    if (statut === 401) return 'Ma clé n’est plus acceptée par Claude : elle a sans doute expiré. Il faut en créer une nouvelle et la taper dans les réglages du cerveau.';
    if (statut === 403) return 'Ma clé n’a pas le droit d’utiliser Claude. Vérifie-la dans les réglages du cerveau.';
    if (statut === 429) return 'Claude reçoit trop de demandes en ce moment.';
    if (statut >= 500) return 'Claude ne répond pas en ce moment.';
    return 'Claude n’a pas compris la demande de Cap.';
  }

  async function comprendre({ texte }, contexte) {
    const cle = cleIA.lire();
    if (!cle) throw new Error('Aucune clé n’est enregistrée.');
    const texteConsignes = await chargerConsignes();
    const controle = typeof AbortController === 'function' ? new AbortController() : null;
    const minuteur = controle ? setTimeout(() => controle.abort(), REGLAGES_IA.delai_ms) : null;
    let reponse;
    try {
      reponse = await fetch(REGLAGES_IA.adresse, {
        method: 'POST',
        headers: {
          'content-type': 'application/json',
          'x-api-key': cle,
          'anthropic-version': REGLAGES_IA.version_api,
          'anthropic-dangerous-direct-browser-access': 'true'
        },
        body: JSON.stringify({
          model: REGLAGES_IA.modele,
          max_tokens: REGLAGES_IA.reponse_max_jetons,
          system: systeme(texteConsignes, contexte),
          tools: outils(contexte),
          messages: [...historique, { role: 'user', content: texte }]
        }),
        signal: controle?.signal
      });
    } catch (erreur) {
      throw new Error('Je n’arrive pas à joindre Claude (pas de réseau ?).');
    } finally {
      clearTimeout(minuteur);
    }
    if (!reponse.ok) throw new Error(erreurHttp(reponse.status));
    const donnees = await reponse.json();
    limiteIA.ajouterDepense(donnees?.usage?.input_tokens, donnees?.usage?.output_tokens);
    const contenu = Array.isArray(donnees?.content) ? donnees.content : [];
    const appels = contenu.filter(bloc => bloc.type === 'tool_use');
    let paroles = contenu.filter(bloc => bloc.type === 'text').map(bloc => String(bloc.text || '').trim()).filter(Boolean).join(' ');
    if (numeroInvente(paroles, texte)) {
      paroles = 'Je ne sais pas : tu ne m’as jamais donné ce numéro.';
      retenir(texte, paroles);
      return { type: 'reponse', texte: paroles };
    }
    if (appels.length > 1) {
      const texteCap = 'Je fais une seule chose à la fois pour l’instant. Redis-moi la première.';
      retenir(texte, texteCap);
      return { type: 'reponse', texte: texteCap };
    }
    if (appels.length === 1 && !motPourMot(appels[0].input?.intitule, texte)) {
      const texteCap = 'Je veux garder tes mots exacts : redis-moi la tâche telle que tu veux l’écrire.';
      retenir(texte, texteCap);
      return { type: 'reponse', texte: texteCap };
    }
    if (appels.length === 1) {
      retenir(texte, paroles, appels[0]);
      return { type: 'action', action: appels[0].name, parametres: appels[0].input || {}, parole: paroles };
    }
    retenir(texte, paroles);
    return paroles ? { type: 'reponse', texte: paroles } : null;
  }

  function oublier() {
    historique = [];
    consignes = null;
    erreurConsignes = '';
  }

  const fournisseur = { nom: REGLAGES_IA.nom, payant: true, pret: () => cleIA.presente(), comprendre };
  cerveau.enregistrerFournisseur('claude', fournisseur);
  return { ...fournisseur, etatConsignes, oublier, precharger, infoConsignes, maintenantParis, ficheTelephone, enregistrerFiche, retirerFiche, origineFiche };
})();
