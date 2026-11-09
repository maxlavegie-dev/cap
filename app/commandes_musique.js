'use strict';

// 08/11/2026 (accord de Max, étape 2a du codage des commandes vocales) : COMMANDER LA MUSIQUE au micro du milieu.
// La musique joue en arrière-plan (la note ronde) pendant que Max parle dans l'écran Micro. Chaque commande passe par la
// télécommande du lecteur (relations_mp3.js), qui touche les mêmes boutons que le doigt.
// Règles de Max : « arrête » / « stop » seuls = la dictée (jamais la musique : il faut un mot comme « la musique ») ;
// « tais-toi » / « silence » = couper le son ; « un autre » = morceau suivant ; « recommence » = au début ;
// « volume au maximum / à fond » = jusqu'au bout ; « mets à zéro » = couper le son ; « masque le player » arrête la
// musique s'il est affiché (déjà caché en arrière-plan : rien n'est arrêté).
// 08/11/2026 (étape 2b) : lancer un morceau (titre, personne, album, hasard) et « Choisir » ajoutés plus bas.
// Avant : « Lancer un morceau (par titre, personne, album, hasard) et « Choisir » : étape 2b, pas ici. »
// Rien n'est envoyé à l'IA.
const commandesMusique = (() => {
  function brancher({ commandes = (typeof commandesVocales !== 'undefined' ? commandesVocales : null),
    lecteur = () => (typeof relationsMp3 !== 'undefined' ? relationsMp3.instance : null) } = {}) {
    if (!commandes) return null;
    const avec = fonction => (r, contexte) => {
      const t = lecteur();
      if (!t) return 'Le lecteur de musique n’est pas disponible ici.';
      return fonction(t, r, contexte);
    };
    const mots = r => (r.mots || []).join(' ');
    const actions = {
      'MUS-05': avec(t => t.pause()),
      'MUS-06': avec(t => t.reprendre()),
      'MUS-07': avec(t => t.arreter()),
      'MUS-08': avec((t, r) => t.plusFort(/(maximum|max|a fond|au bout|fond)/.test(mots(r)))),
      'MUS-09': avec(t => t.moinsFort()),
      'MUS-10': avec(t => t.couper()),
      'MUS-11': avec(t => t.remettre()),
      'MUS-12': avec(t => t.suivant()),
      'MUS-13': avec(t => t.precedent()),
      'MUS-14': avec(t => t.rejouer()),
      'MUS-15': avec(t => t.debut()),
      'MUS-16': avec(t => t.arrierePlan()),
      'MUS-17': avec(t => t.afficher()),
      // 09/11/2026 (décision de Max, bloc c74) : rien ne joue : le lecteur s'allume avec la playlist par défaut ; une musique
      // joue déjà : le lecteur seulement (rien n'est relancé). Avant : 'MUS-19': avec(t => t.afficher()),
      'MUS-19': avec(t => ((t.etat && t.etat().actif) || typeof t.lancerPlaylist !== 'function' ? t.afficher()
        : { message: 'Je mets la musique…', parler: false, suite: t.lancerPlaylist() })),
      'MUS-20': avec(t => t.masquer()),
      'MUS-21': avec((t, r) => (r.valeurs && Number.isFinite(r.valeurs.nombre) ? t.volume(r.valeurs.nombre) : 'Je n’ai pas compris le chiffre du volume.')),
      'MUS-22': avec(t => t.titre()),
      // « avance / recule de [DURÉE] » (déplacement) ou « à [DURÉE] » (position précise) : le mot « de » ou « à » décide.
      'MUS-23': avec((t, r) => {
        const d = r.valeurs && r.valeurs.duree;
        if (!Number.isFinite(d)) return 'Je n’ai pas compris la durée.';
        const m = mots(r);
        const absolu = /(^| )a( |$)/.test(m) && !/(^| )de( |$)/.test(m);
        const recul = /(recul|arriere|retour|revien|rembobin)/.test(m);
        return t.deplacer(absolu ? d : (recul ? -d : d), absolu);
      })
    };
    // ----- 08/11/2026 (accord de Max, étape 2b) : LANCER la musique (titre, personne, album, hasard) et « Choisir » -----
    // La recherche se fait dans le code (relations_mp3.js), jamais par l'IA ; la réponse arrive après (« suite »).
    const chercher = demande => avec(t => (typeof t.lancerVoix === 'function'
      ? { message: 'Je cherche la musique…', parler: false, suite: t.lancerVoix(demande) }
      : 'Le lecteur de musique n’est pas disponible ici.'));
    const v = r => r.valeurs || {};
    actions['MUS-01'] = (r, c) => chercher({ titre: v(r).titre, prenom: v(r).prenom })(r, c);
    actions['MUS-02'] = (r, c) => chercher({ prenom: v(r).prenom, tout: true })(r, c);
    actions['MUS-03'] = (r, c) => chercher({ album: v(r).titre || v(r).dossier, prenom: v(r).prenom })(r, c);
    actions['MUS-04'] = (r, c) => chercher({ auHasard: true, prenom: v(r).prenom })(r, c);
    actions['MUS-18'] = avec(t => (typeof t.choisirFichier === 'function' ? t.choisirFichier() : 'Le lecteur de musique n’est pas disponible ici.'));
    for (const [code, action] of Object.entries(actions)) commandes.brancherAction(code, action);
    return { actions };
  }
  return { brancher };
})();

if (typeof document !== 'undefined' && !(typeof window !== 'undefined' && window.CAP_TESTS)) {
  commandesMusique.instance = commandesMusique.brancher();
}
