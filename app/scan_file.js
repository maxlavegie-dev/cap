'use strict';

// File d'attente des scans sur le téléphone (IndexedDB) : un scan est enregistré ici AVANT tout envoi,
// et n'en sort que lorsque Google a confirmé le dépôt. Aucun scan n'est supprimé de cette liste.
const scanFile = (() => {
  const base_defaut = 'cap_scans_v1';
  const magasin = 'scans';

  function ouvrir(nomBase = base_defaut) {
    return new Promise((resolve, reject) => {
      if (typeof indexedDB === 'undefined') {
        reject(new Error('Ce téléphone ne permet pas de garder les scans hors connexion.'));
        return;
      }
      const demande = indexedDB.open(nomBase, 1);
      demande.onupgradeneeded = () => {
        demande.result.createObjectStore(magasin, { keyPath: 'id', autoIncrement: true });
      };
      demande.onsuccess = () => resolve(demande.result);
      demande.onerror = () => reject(demande.error || new Error('Impossible d’ouvrir la file des scans.'));
    });
  }

  function transaction(base, mode, action) {
    return new Promise((resolve, reject) => {
      const tx = base.transaction(magasin, mode);
      let resultat;
      const requete = action(tx.objectStore(magasin));
      if (requete) requete.onsuccess = () => { resultat = requete.result; };
      tx.oncomplete = () => resolve(resultat);
      tx.onerror = () => reject(tx.error);
      tx.onabort = () => reject(tx.error || new Error('Enregistrement du scan annulé.'));
    });
  }

  function creer(nomBase = base_defaut) {
    let ouverte = null;
    const base = () => (ouverte ||= ouvrir(nomBase));

    async function ajouter({ nom, pdf, pages }) {
      if (!nom || !(pdf instanceof Blob) || !pdf.size) throw new Error('Scan vide : rien à enregistrer.');
      const fiche = { nom, pdf, pages: pages || 0, cree: new Date().toISOString(), etat: 'attente', drive_id: '', depose_le: '', erreur: '' };
      return transaction(await base(), 'readwrite', s => s.add(fiche));
    }

    async function lister() {
      const tout = await transaction(await base(), 'readonly', s => s.getAll());
      return (tout || []).sort((a, b) => a.id - b.id);
    }

    async function lire(id) {
      return transaction(await base(), 'readonly', s => s.get(id));
    }

    async function mettreAJour(id, changements) {
      const b = await base();
      return new Promise((resolve, reject) => {
        const tx = b.transaction(magasin, 'readwrite');
        const s = tx.objectStore(magasin);
        const lecture = s.get(id);
        lecture.onsuccess = () => {
          if (!lecture.result) { reject(new Error('Scan introuvable.')); return; }
          s.put({ ...lecture.result, ...changements });
        };
        tx.oncomplete = () => resolve();
        tx.onerror = () => reject(tx.error);
        tx.onabort = () => reject(tx.error || new Error('Mise à jour du scan annulée.'));
      });
    }

    // Google a confirmé le dépôt : le fichier est gardé sous forme de fiche, la copie locale lourde est libérée.
    async function marquerDepose(id, driveId) {
      await mettreAJour(id, { etat: 'depose', drive_id: driveId, depose_le: new Date().toISOString(), erreur: '', pdf: null });
    }

    async function marquerErreur(id, message) {
      await mettreAJour(id, { erreur: String(message || '') });
    }

    async function enAttente() {
      return (await lister()).filter(f => f.etat === 'attente');
    }

    async function fermer() {
      if (ouverte) (await ouverte).close();
      ouverte = null;
    }

    return { ajouter, lister, lire, marquerDepose, marquerErreur, enAttente, fermer };
  }

  return { creer, base_defaut };
})();
