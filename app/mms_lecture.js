'use strict';

// 12/11/2026 (accord écrit de Max, marche M3a) : LECTURE des MMS reçus, par la coque Android (pont MmsAndroid).
// - Seulement dans l'application Cap du téléphone (la coque) ; ailleurs : « pas disponible ».
// - L'autorisation SMS d'Android est demandée seulement quand Max touche le bouton (demander), jamais au démarrage.
// - La coque rend, pour les 20 derniers MMS reçus : identifiant, date, image / vidéo / texte (oui ou non), nombre de
//   destinataires, et le numéro de l'expéditeur. Ce numéro est changé AUSSITÔT en empreinte (index_relations.js, M1) puis
//   oublié : il ne sort jamais d'ici (ni rendu, ni gardé, ni affiché, ni écrit dans un journal, ni envoyé à l'IA).
// - Rien n'est copié, rien n'est envoyé : aucune lecture du Drive, aucun réseau ici. Sans DOM.
const mmsLecture = (() => {
  const pont = fenetre => (fenetre && fenetre.MmsAndroid) || null;

  function disponible(fenetre = window) { return !!pont(fenetre); }

  function autorise(fenetre = window) {
    try { return !!(pont(fenetre) && pont(fenetre).autorise() === true); } catch (erreur) { return false; }
  }

  // Ouvre la question d'Android ; rend true (accepté) ou false (refusé, pas de coque, pas de réponse dans le délai).
  function demander(fenetre = window, delai = 120000) {
    const p = pont(fenetre);
    if (!p) return Promise.resolve(false);
    if (autorise(fenetre)) return Promise.resolve(true);
    return new Promise(resolu => {
      let fini = false;
      const finir = valeur => {
        if (fini) return;
        fini = true;
        clearTimeout(minuteur);
        if (fenetre.__mmsAutorisation === recevoir) fenetre.__mmsAutorisation = null;
        resolu(valeur === true && autorise(fenetre));
      };
      const recevoir = accordee => finir(accordee);
      const minuteur = setTimeout(() => finir(false), delai);
      fenetre.__mmsAutorisation = recevoir;
      try { p.demander(); } catch (erreur) { finir(false); }
    });
  }

  // cle : la clé du téléphone (indexRelations.cleDuTelephone). Rend [{ id, date, image, video, texte, groupe, nombreDestinataires, empreinte }] :
  // AUCUN numéro dedans (empreinte = null si le numéro est masqué, absent ou illisible).
  async function lireRecents(cle, fenetre = window) {
    const p = pont(fenetre);
    if (!p || !autorise(fenetre)) return [];
    let brut = [];
    try { brut = JSON.parse(p.recents()); } catch (erreur) { brut = []; }
    const rendus = [];
    for (const m of Array.isArray(brut) ? brut.slice(0, 20) : []) {
      if (!m || typeof m !== 'object') continue;
      let empreinte = null;
      try { empreinte = await indexRelations.empreinteNumero(m.expediteur, cle); } catch (erreur) { empreinte = null; }
      rendus.push({
        id: String(m.id ?? ''), date: Number(m.date) || 0,
        image: m.image === true, video: m.video === true, texte: m.texte === true,
        groupe: Number(m.destinataires) > 1, nombreDestinataires: Math.max(0, Math.floor(Number(m.destinataires) || 0)), empreinte // c176 : + le nombre (pour l'explication)
      });
    }
    return rendus;
  }

  return Object.freeze({ disponible, autorise, demander, lireRecents });
})();
