'use strict';

// Fournisseur « Claude Haiku » : payant, utilisé seulement si Max a tapé sa clé dans Cap
// ET si le document de consignes est validé (pas de mot BROUILLON sur sa première ligne).
// Il ne reçoit que la phrase de Max, les noms des catégories fictives et les derniers échanges de la conversation.
const cerveauClaude = (() => {
  let consignes = null;
  let historique = [];

  async function chargerConsignes() {
    if (consignes !== null) return consignes;
    let reponse;
    try {
      reponse = await fetch(REGLAGES_IA.fichier_consignes, { cache: 'no-cache' });
    } catch (erreur) {
      throw new Error('Je n’ai pas pu lire mon document de consignes.');
    }
    if (!reponse.ok) throw new Error('Je n’ai pas pu lire mon document de consignes.');
    const texte = (await reponse.text()).trim();
    const premiereLigne = texte.split('\n', 1)[0];
    if (!texte || premiereLigne.toLocaleUpperCase('fr').includes(REGLAGES_IA.marqueur_brouillon)) {
      throw new Error('Mon document de consignes n’est pas encore validé par Max.');
    }
    consignes = texte;
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
      texteConsignes,
      `Aujourd’hui : ${dateDuJour()}.`,
      `Catégories de Cap : ${categories.join(' ; ')}. « ${contexte.a_trier} » si aucune ne convient clairement.`,
      'Pour agir, utilise un outil ; recopie l’intitulé de Max mot pour mot. Une seule action par réponse.'
    ].join('\n');
  }

  function retenir(texteMax, texteCap) {
    historique.push({ role: 'user', content: texteMax }, { role: 'assistant', content: texteCap || '…' });
    historique = historique.slice(-2 * REGLAGES_IA.echanges_retenus);
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
    if (statut === 401 || statut === 403) return 'Ma clé n’est pas acceptée par Claude. Vérifie-la dans les réglages du cerveau.';
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
    const paroles = contenu.filter(bloc => bloc.type === 'text').map(bloc => String(bloc.text || '').trim()).filter(Boolean).join(' ');
    const appels = contenu.filter(bloc => bloc.type === 'tool_use');
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
      retenir(texte, `${paroles} [action ${appels[0].name} : ${JSON.stringify(appels[0].input || {})}]`.trim());
      return { type: 'action', action: appels[0].name, parametres: appels[0].input || {}, parole: paroles };
    }
    retenir(texte, paroles);
    return paroles ? { type: 'reponse', texte: paroles } : null;
  }

  function oublier() {
    historique = [];
    consignes = null;
  }

  const fournisseur = { nom: REGLAGES_IA.nom, payant: true, pret: () => cleIA.presente(), comprendre };
  cerveau.enregistrerFournisseur('claude', fournisseur);
  return { ...fournisseur, etatConsignes, oublier };
})();
