'use strict';

// 12/11/2026 (accord écrit de Max, marches M3a, M3b, M3c) : les deux boutons des MMS dans « Réglages du Drive ».
// - « Lire mes derniers MMS » : demande l'autorisation SMS d'Android si besoin (Max accepte ou refuse), lit les 20 derniers
//   MMS reçus, les classe (personne / à trier) et affiche des NOMBRES seulement. Rien n'est copié, rien n'est envoyé.
// - « Répétition MMS » : montre ce qui serait créé dans le compte Cap (dossiers VIDES et FICTIFS) et où iraient de faux
//   messages ; rien n'est créé sans « Oui, créer ». Aucun dossier « r_ », aucun vrai MMS.
// Le DOM : textContent seulement.
const mmsEcran = (() => {
  function brancher(doc, { compte, stockage = (typeof localStorage !== 'undefined' ? localStorage : null), fenetre = window } = {}) {
    const el = id => doc.getElementById(id);
    const lire = el('lire-mms');
    const repetition = el('repetition-mms');
    const zone = el('resultat-mms');
    const barre = el('barre-mms');
    const oui = el('oui-mms');
    const non = el('non-mms');
    if (![lire, repetition, zone, barre, oui, non].every(Boolean) || !compte) return null;
    const montrer = (texte, question = false) => {
      zone.hidden = false;
      zone.textContent = texte;
      barre.hidden = !question;
      oui.disabled = false;
      try { zone.scrollIntoView({ block: 'nearest' }); } catch (erreur) {}
    };
    const raison = erreur => String(erreur && erreur.message || 'raison inconnue').slice(0, 220);
    let occupe = false;

    async function lireMms() {
      if (occupe) return '';
      if (!mmsLecture.disponible(fenetre)) { montrer('La lecture des MMS se fait seulement dans l’application Cap du téléphone.'); return ''; }
      occupe = true;
      try {
        if (!mmsLecture.autorise(fenetre)) {
          montrer('Android va te demander l’autorisation de lire tes SMS et MMS. Cap les lit seulement : il n’envoie, n’efface et ne copie rien.');
          if (!(await mmsLecture.demander(fenetre))) { montrer('Autorisation refusée : rien n’a été lu.'); return ''; }
        }
        montrer('Lecture en cours… (rien n’est copié ni envoyé)');
        const { cle, index, personnes, dossiers } = await mmsRangement.preparerIndex(stockage);
        const messages = await mmsLecture.lireRecents(cle, fenetre);
        const t = mmsRangement.texte(mmsRangement.resumer(mmsRangement.classer(messages, index), dossiers)); // c177 : + les dossiers r_ (nombres)
        const avertissement = personnes ? '' : ' (Aucun numéro de relation dans la copie des coordonnées : touche d’abord « Tout synchroniser ».)';
        montrer(t + avertissement);
        return t;
      } catch (erreur) {
        montrer(`${raison(erreur)} Rien n’a été copié ni envoyé.`);
        return '';
      } finally { occupe = false; }
    }

    async function preparerRepetition() {
      if (occupe) return '';
      if (!compte.connecte()) { montrer('Le compte Cap n’est pas connecté : touche « Autoriser la lecture du compte Cap », puis recommence.'); return ''; }
      occupe = true;
      try {
        montrer('Lecture du compte Cap… (rien n’est modifié)');
        const p = await mmsRepetition.preparer(compte);
        const demo = `Avec de faux messages, voici où ils iraient : ${mmsRepetition.demonstration().join(' ; ')}.`;
        if (!p.aCreer.length) { montrer(`Les dossiers de répétition existent déjà dans le compte Cap : rien à créer. ${demo}`); return ''; }
        montrer(`Répétition FICTIVE. Cap va créer, dans le Drive du compte Cap, des dossiers VIDES : ${p.aCreer.join(', ')}. Aucun dossier « r_ », aucun vrai MMS, rien d’effacé. ${demo} Créer ?`, true);
        return 'question';
      } catch (erreur) {
        montrer(`${raison(erreur)} Rien n’a été créé.`);
        return '';
      } finally { occupe = false; }
    }

    async function confirmer() {
      if (occupe || barre.hidden) return '';
      occupe = true;
      oui.disabled = true;
      try {
        montrer('Création en cours… (rien n’est effacé)');
        const r = await mmsRepetition.creer(compte);
        const t = r.dejaLa ? 'Les dossiers de répétition existaient déjà : rien créé.' : `C’est fait, dans le Drive du compte Cap : ${r.cree.map(n => `« ${n} »`).join(', ')}.`;
        montrer(t);
        return t;
      } catch (erreur) {
        const t = `${raison(erreur)} Rien n’a été effacé ; tu peux réessayer : ce qui existe déjà ne sera pas recréé.`;
        montrer(t);
        return t;
      } finally { occupe = false; }
    }

    lire.addEventListener('click', () => { void lireMms(); });
    repetition.addEventListener('click', () => { void preparerRepetition(); });
    oui.addEventListener('click', () => { void confirmer(); });
    non.addEventListener('click', () => { if (!occupe) montrer('Rien n’a été créé.'); });
    return { lireMms, preparerRepetition, confirmer };
  }
  return { brancher };
})();

if (typeof document !== 'undefined' && !(typeof window !== 'undefined' && window.CAP_TESTS)) {
  mmsEcran.instance = mmsEcran.brancher(document, { compte: googleCompteRelations });
}
