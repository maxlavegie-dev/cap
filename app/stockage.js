'use strict';

// Ce fichier sera remplacé par la connexion Google Sheets en semaine 2.
const stockage = (() => {
  const cle = 'cap_taches_v1';
  let dernierContenu = null;
  let bloque = false;

  function dateValide(texte, facultative = true) {
    if (texte === '' && facultative) return true;
    if (typeof texte !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(texte)) return false;
    const date = new Date(`${texte}T12:00:00Z`);
    return Number.isFinite(date.getTime()) && date.toISOString().slice(0, 10) === texte;
  }

  function verifier(liste) {
    if (!Array.isArray(liste)) throw new Error('Liste illisible');
    const identifiants = new Map();
    for (const tache of liste) {
      if (!tache || typeof tache !== 'object' || Array.isArray(tache)) throw new Error('Tâche illisible');
      const textes = ['id', 'intitule', 'categorie', 'sous_categorie', 'parente', 'note'];
      if (textes.some(champ => typeof tache[champ] !== 'string') || !tache.id || !tache.intitule.trim()) {
        throw new Error('Champs manquants');
      }
      if (identifiants.has(tache.id)) throw new Error('Identifiant en double');
      identifiants.set(tache.id, tache);
      if (typeof tache.fait !== 'boolean' || typeof tache.fictif !== 'boolean'
        || !['haute', 'normale', 'basse'].includes(tache.priorite)
        || !['ajout à la main', 'dictée', 'fictif'].includes(tache.origine)
        || !dateValide(tache.date_entree, false)
        || ['echeance', 'date_realisation', 'avant_le', 'abandonnee_le'].some(champ => !dateValide(tache[champ]))
        || (tache.fait ? !tache.date_realisation : tache.date_realisation !== '')) {
        throw new Error('Valeurs illisibles');
      }
    }
    for (const tache of liste) {
      if (tache.parente) {
        const parent = identifiants.get(tache.parente);
        if (!parent || parent.parente || parent.id === tache.id
          || parent.categorie !== tache.categorie || parent.sous_categorie !== tache.sous_categorie) {
          throw new Error('Lien de parenté illisible');
        }
      }
    }
  }

  function enregistrer(liste) {
    if (bloque) throw new Error('Sauvegarde indisponible : tes données existantes restent intactes. Recharge la page après avoir vérifié le stockage du navigateur.');
    verifier(liste);
    const contenu = JSON.stringify(liste);
    try {
      if (localStorage.getItem(cle) !== dernierContenu) {
        throw new Error('La liste a changé dans une autre fenêtre. Recharge la page avant de continuer.');
      }
      localStorage.setItem(cle, contenu);
      dernierContenu = contenu;
    } catch (erreur) {
      if (erreur.message.includes('autre fenêtre')) throw erreur;
      throw new Error('Impossible de sauvegarder sur ce téléphone. La modification n’a pas été appliquée. Vérifie l’espace disponible et l’autorisation de stockage.');
    }
  }

  function charger() {
    const fictives = () => TACHES_FICTIVES.map(tache => ({ ...tache }));
    let contenu;
    try {
      contenu = localStorage.getItem(cle);
      dernierContenu = contenu;
    } catch (erreur) {
      bloque = true;
      return { taches: fictives(), message: 'Le stockage du téléphone est inaccessible. Les exemples sont affichés, mais aucune modification ne peut être sauvegardée.' };
    }
    if (contenu !== null) {
      try {
        const liste = JSON.parse(contenu);
        verifier(liste);
        return { taches: liste, message: '' };
      } catch (erreur) {
        try {
          let cleCopie = `${cle}_illisible_${Date.now()}`;
          while (localStorage.getItem(cleCopie) !== null) cleCopie += '_';
          localStorage.setItem(cleCopie, contenu);
        } catch (erreurCopie) {
          bloque = true;
          return { taches: fictives(), message: 'La liste enregistrée est illisible et sa copie de sécurité a échoué. L’original reste intact ; les modifications sont bloquées.' };
        }
        const taches = fictives();
        try {
          enregistrer(taches);
          return { taches, message: 'La liste enregistrée était illisible. Une copie complète a été conservée sur ce téléphone ; les tâches fictives sont affichées.' };
        } catch (erreurSauvegarde) {
          return { taches, message: `La liste illisible a été copiée en sécurité. ${erreurSauvegarde.message}` };
        }
      }
    }
    const taches = fictives();
    try {
      enregistrer(taches);
      return { taches, message: '' };
    } catch (erreur) {
      return { taches, message: erreur.message };
    }
  }

  return { charger, enregistrer, verifier };
})();
