'use strict';

const journalActions = (() => {
  const cle = 'cap_journal_actions_v1';
  const cleComplet = 'cap_journal_complet_v1';
  const types = ['ajout', 'fait', 'remise à faire', 'abandon', 'remise', 'échéance', 'classement'];
  const libelles = {
    ajout: 'ajout de la tâche', fait: 'tâche cochée', 'remise à faire': 'tâche remise à faire',
    abandon: 'tâche abandonnée', remise: 'tâche remise', 'échéance': 'échéance changée', classement: 'tâche classée'
  };
  let contexte = null;
  let envoiEnCours = false;

  function lire() {
    try {
      const entrees = JSON.parse(localStorage.getItem(cle));
      if (!Array.isArray(entrees)) return [];
      return entrees.filter(entree => entree && typeof entree.heure === 'string'
        && Number.isFinite(Date.parse(entree.heure)) && types.includes(entree.type)
        && typeof entree.texte === 'string').slice(0, 30)
        .map(({ heure, type, texte }) => ({ heure, type, texte }));
    } catch (erreur) {
      return [];
    }
  }

  function masquer(valeur) {
    return String(valeur ?? '')
      .replace(/\b(mot de passe|code secret|code pin|password)\b(\s*(?:est\s*)?[:=]?\s*)\S+/gi, '$1$2[masqué]')
      .replace(/(?:\d[\s.-]?){12,}/g, '[numéro masqué] ')
      .replace(/\s+/g, ' ')
      .trim()
      .slice(0, 500);
  }

  function lireComplet() {
    try {
      const lignes = JSON.parse(localStorage.getItem(cleComplet));
      return Array.isArray(lignes) ? lignes.filter(ligne => Array.isArray(ligne) && ligne.length === 5) : [];
    } catch (erreur) {
      return [];
    }
  }

  function heureLocale(date) {
    const deux = nombre => String(nombre).padStart(2, '0');
    return `${date.getFullYear()}-${deux(date.getMonth() + 1)}-${deux(date.getDate())} ${deux(date.getHours())}:${deux(date.getMinutes())}:${deux(date.getSeconds())}`;
  }

  function consigner({ source = 'écran', entree = '', compris = '', fait = '' } = {}) {
    try {
      const lignes = lireComplet();
      lignes.push([heureLocale(new Date()), masquer(source), masquer(entree), masquer(compris), masquer(fait)]);
      localStorage.setItem(cleComplet, JSON.stringify(lignes));
    } catch (erreur) {
      return;
    }
    if (typeof setTimeout === 'function') setTimeout(() => { void envoyer(); }, 0);
  }

  function pendant(nouveauContexte, action) {
    const precedent = contexte;
    contexte = nouveauContexte;
    try {
      return action();
    } finally {
      contexte = precedent;
    }
  }

  function noter(type, texte) {
    try {
      if (!types.includes(type) || typeof texte !== 'string') return;
      const entrees = [{ heure: new Date().toISOString(), type, texte }, ...lire()].slice(0, 30);
      localStorage.setItem(cle, JSON.stringify(entrees));
    } catch (erreur) {
      return;
    }
    consigner({
      source: contexte?.source || 'écran touché',
      entree: contexte?.entree || '',
      compris: contexte?.compris || libelles[type],
      fait: `${libelles[type]} : ${texte}`
    });
  }

  function enAttente() {
    return lireComplet().length;
  }

  async function envoyer() {
    if (envoiEnCours || typeof googleSheets === 'undefined' || typeof googleConnexion === 'undefined') return false;
    if (!googleConnexion.connecte() || (typeof navigator !== 'undefined' && navigator.onLine === false)) return false;
    if (typeof synchronisation !== 'undefined' && !synchronisation.informations?.().pret) return false;
    const lignes = lireComplet();
    if (!lignes.length) return true;
    envoiEnCours = true;
    try {
      await googleSheets.ajouterJournal(lignes);
      const restantes = lireComplet().slice(lignes.length);
      localStorage.setItem(cleComplet, JSON.stringify(restantes));
      return true;
    } catch (erreur) {
      return false;
    } finally {
      envoiEnCours = false;
    }
  }

  return { noter, lire, consigner, pendant, masquer, enAttente, envoyer, lireComplet };
})();
