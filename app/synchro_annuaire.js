'use strict';

const synchroAnnuaire = (() => {
  let fait = false;
  let enCours = null;
  let dernierEchec = 0;
  let derniereErreur = '';

  function synchroniser() {
    if (enCours) return enCours;
    if (!googleConnexion.connecte() || !navigator.onLine) return Promise.resolve(false);
    if (fait && !annuaire.aEnvoyer()) return Promise.resolve(false);
    if (dernierEchec && Date.now() - dernierEchec < 60000) return Promise.resolve(false);
    enCours = (async () => {
      try {
        await googleSheets.trouverOuCreer();
        const distant = await googleSheets.lireAnnuaire();
        annuaire.fusionner(distant);
        annuaire.marquerEnvoye();
        await googleSheets.ecrireAnnuaire(annuaire.exporter());
        fait = true;
        dernierEchec = 0;
        derniereErreur = '';
        return true;
      } catch (erreur) {
        try { localStorage.setItem('cap_annuaire_a_envoyer_v1', '1'); } catch (e) {}
        dernierEchec = Date.now();
        derniereErreur = erreur instanceof Error ? erreur.message : 'Synchronisation de l’annuaire interrompue.';
        return false;
      }
    })().finally(() => { enCours = null; });
    return enCours;
  }

  function erreur() { return derniereErreur; }

  window.addEventListener('cap-google-etat', () => { void synchroniser(); });
  window.addEventListener('cap-annuaire-changee', () => { if (annuaire.aEnvoyer()) void synchroniser(); });
  window.addEventListener('online', () => { void synchroniser(); });
  setInterval(() => { if (!fait || annuaire.aEnvoyer()) void synchroniser(); }, 60000);
  return { synchroniser, erreur };
})();
