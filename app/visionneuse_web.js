'use strict';

// 13/11/2026 (Agent 3, accord de Max) : SITE WEB ou VIDÉO YOUTUBE dans la visionneuse de Cap.
// Module écrit dans C:\Users\revox\Agent3 (hors Projet_Cap), pour que l'Opus l'intègre sans le réécrire
// (voir LIRE_POUR_OPUS.md). Même forme que les autres modules de Cap : un objet unique, des pièces
// remplaçables dans les tests, rien de lancé quand window.CAP_TESTS est vrai.
// Aucun réseau ici (hors la page montrée elle-même), aucune clé, aucun droit Google, rien d'enregistré.
//
// Marche 1 (13/11/2026) : LIRE UNE ADRESSE. Rien n'est ouvert : la fonction dit seulement ce qu'est l'adresse.
//   - vidéo YouTube (youtube.com, m.youtube.com, youtu.be, youtube-nocookie.com ; watch, embed, shorts, live) :
//     son identifiant (11 signes) et son départ éventuel (t= ou start=) ; le cadre utilisera youtube-nocookie.com ;
//   - site web : seulement en https (la coque refuse le http : usesCleartextTraffic=false) ;
//   - tout le reste est refusé avec une phrase simple (jamais l'adresse entière dans le message).
const visionneuseWeb = (() => {
  const LONGUEUR_MAX = 2000;
  const ID_VIDEO = /^[A-Za-z0-9_-]{11}$/;
  const HOTES_YOUTUBE = new Set(['youtube.com', 'www.youtube.com', 'm.youtube.com', 'music.youtube.com',
    'youtu.be', 'www.youtu.be', 'youtube-nocookie.com', 'www.youtube-nocookie.com']);
  const EMBED = 'https://www.youtube-nocookie.com/embed/';
  // 13/11/2026 (chemin 1 de Max) : YouTube refuse d'être montré dans un cadre (VÉRIFIÉ : « X-Frame-Options: SAMEORIGIN ») ;
  // une adresse YouTube qui n'est PAS une vidéo précise (accueil, chaîne, recherche…) s'ouvre donc HORS de Cap, dans
  // l'application YouTube (la coque Android s'en charge ; le retour du téléphone revient à Cap). Adresses YouTube seulement.
  const HOTES_APPLI = new Set(['youtube.com', 'www.youtube.com', 'm.youtube.com', 'music.youtube.com']);

  // Phrases montrées à Max (une par refus).
  const MESSAGES = Object.freeze({
    vide: 'Aucune adresse : colle ou écris l’adresse du site ou de la vidéo.',
    'trop-longue': 'Cette adresse est trop longue pour être ouverte.',
    illisible: 'Je ne reconnais pas cette adresse. Elle doit ressembler à https://exemple.fr ou à un lien YouTube.',
    'pas-https': 'Cap n’ouvre que les adresses sûres, qui commencent par https://.',
    identifiants: 'Cette adresse contient un nom ou un mot de passe : Cap ne l’ouvre pas.',
    'hote-local': 'Cette adresse désigne un appareil du réseau local : Cap ne l’ouvre pas.',
    'youtube-sans-video': 'Ce lien YouTube ne désigne pas une vidéo précise : ouvre la vidéo dans YouTube, copie son lien, puis colle-le ici.',
    // 13/11/2026 (marche 2) : messages du cadre.
    'pas-de-reseau': 'Pas de réseau : les sites et les vidéos se lisent par Internet. Reconnecte le téléphone, puis réessaie.',
    'visionneuse-absente': 'La visionneuse n’est pas disponible ici : rien n’a été ouvert.',
    'ne-repond-pas': 'Le site ne répond pas, ou il refuse d’être montré dans Cap. Rien n’a été modifié.',
    'peut-refuser': 'Si la page reste blanche, ce site refuse d’être montré dans Cap.'
  });

  const refus = code => ({ ok: false, code, message: MESSAGES[code] });

  // « 90 », « 90s », « 1m30s », « 1h2m3s » : un nombre de secondes, ou 0 si illisible.
  function lireDepart(valeur) {
    const v = String(valeur || '').trim().toLowerCase();
    if (!v) return 0;
    if (/^\d+$/.test(v)) return Math.min(Number(v), 86400);
    const m = /^(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$/.exec(v);
    if (!m || (!m[1] && !m[2] && !m[3])) return 0;
    return Math.min((Number(m[1] || 0) * 3600) + (Number(m[2] || 0) * 60) + Number(m[3] || 0), 86400);
  }

  // Identifiant de la vidéo dans une adresse YouTube déjà lue (URL), ou ''.
  function idYoutube(url) {
    const morceaux = url.pathname.split('/').filter(Boolean);
    let id = '';
    if (url.hostname.replace(/^www\./, '') === 'youtu.be') id = morceaux[0] || '';
    else if (morceaux[0] === 'watch') id = url.searchParams.get('v') || '';
    else if (['embed', 'shorts', 'live', 'v'].includes(morceaux[0])) id = morceaux[1] || '';
    return ID_VIDEO.test(id) ? id : '';
  }

  function estHoteLocal(hote) {
    return hote === 'localhost' || hote.endsWith('.localhost') || hote.endsWith('.local')
      || /^\d{1,3}(\.\d{1,3}){3}$/.test(hote) || hote.startsWith('[');
  }

  // texte : ce que Max a collé ou écrit. Rend { ok: true, sorte: 'youtube' | 'site', ... } ou { ok: false, code, message }.
  function analyserAdresse(texte) {
    let brut = String(texte == null ? '' : texte).trim();
    if (!brut) return refus('vide');
    if (brut.length > LONGUEUR_MAX) return refus('trop-longue');
    if (/\s/.test(brut)) return refus('illisible');
    // Sans « https:// » : « youtu.be/… » ou « exemple.fr » sont acceptés tels quels (https ajouté).
    if (!/^[a-z][a-z0-9+.-]*:/i.test(brut)) {
      if (!/^[^/?#]+\.[^/?#]+/.test(brut)) return refus('illisible');
      brut = `https://${brut}`;
    }
    let url;
    try { url = new URL(brut); } catch (erreur) { return refus('illisible'); }
    if (url.protocol !== 'https:') return refus(url.protocol === 'http:' ? 'pas-https' : 'illisible');
    if (url.username || url.password) return refus('identifiants');
    const hote = url.hostname.toLowerCase();
    if (hote && estHoteLocal(hote)) return refus('hote-local'); // avant le contrôle du point : « [::1] » n'en a pas
    if (!hote || !hote.includes('.')) return refus('illisible');
    if (HOTES_YOUTUBE.has(hote)) {
      const id = idYoutube(url);
      if (!id) { // 13/11/2026 : avant, refus('youtube-sans-video')
        const adresseAppli = HOTES_APPLI.has(hote) ? `https://${hote}${url.pathname}${url.search}` : 'https://www.youtube.com/';
        return { ok: true, sorte: 'youtube-appli', adresseAppli };
      }
      const debut = lireDepart(url.searchParams.get('t') || url.searchParams.get('start'));
      const params = new URLSearchParams({ playsinline: '1', rel: '0' });
      if (debut) params.set('start', String(debut));
      return { ok: true, sorte: 'youtube', id, debut, adresseCadre: `${EMBED}${id}?${params}` };
    }
    return { ok: true, sorte: 'site', hote, adresseCadre: url.href };
  }

  // ----- Marche 2 (13/11/2026, accord de Max) : LE CADRE dans la visionneuse -----
  // Un panneau posé dans la fenêtre « visionneuse-cap », sous la barre de Cap (64 px, comme les documents), au-dessus de
  // la page du visualiseur, sous le menu du bouton blanc (z-index 7) et la grille des chantiers (6).
  // Le cadre est LIMITÉ (sandbox) : scripts et formulaires du site oui ; JAMAIS de nouvelle fenêtre (pas de
  // allow-popups), JAMAIS de remplacement de la page de Cap (pas de allow-top-navigation).
  // Un seul site ou une seule vidéo à la fois ; à la fermeture (fermer(), ou fermeture de la visionneuse), le cadre est
  // vidé (about:blank) PUIS retiré de la page : sa mémoire est relâchée.
  // Un site qui refuse d'être montré dans un cadre ne peut pas être reconnu à coup sûr depuis Cap (page d'un autre
  // site) : Cap le dit (« Si la page reste blanche… ») et, sans réponse au bout du délai, « Le site ne répond pas… ».
  const SANDBOX = 'allow-scripts allow-same-origin allow-forms allow-presentation';
  const PERMISSIONS = 'autoplay; encrypted-media; picture-in-picture; fullscreen';
  const STYLE = `
dialog#visionneuse-cap #web-visionneuse { position: absolute; top: var(--haut-cap-web, 64px); left: 0; right: 0; bottom: 0; z-index: 5;
  display: flex; flex-direction: column; background: #000; }
dialog#visionneuse-cap #web-visionneuse[hidden] { display: none; }
dialog#visionneuse-cap #cadre-web-visionneuse { flex: 1 1 auto; width: 100%; min-height: 0; border: 0; background: #fff; }
dialog#visionneuse-cap #web-visionneuse.video #cadre-web-visionneuse { background: #000; }
/* 13/11/2026 (essai de Max sur le Pixel : vidéo rognée à gauche et à droite) : une VIDÉO a un cadre 16:9, le plus grand qui
   tient dans le panneau (toute la largeur en portrait, toute la hauteur si le panneau est plus large que haut), centré, sans
   rognage ; le reste est noir. Les SITES gardent tout le panneau. Avant : le cadre de la vidéo prenait tout le panneau. */
dialog#visionneuse-cap #web-visionneuse.video { container-type: size; justify-content: center; align-items: center; }
dialog#visionneuse-cap #web-visionneuse.video #cadre-web-visionneuse { flex: none; width: min(100cqw, calc(100cqh * 16 / 9)); height: auto; aspect-ratio: 16 / 9; }
dialog#visionneuse-cap #message-web-visionneuse { position: absolute; left: 12px; right: 12px; bottom: max(12px, env(safe-area-inset-bottom));
  margin: 0; padding: 10px 14px; border-radius: 10px; background: rgba(255, 255, 255, 0.94); color: #16201d;
  font: 16px/1.35 sans-serif; overflow-wrap: anywhere; pointer-events: none; }
dialog#visionneuse-cap #message-web-visionneuse[hidden] { display: none; }
dialog#visionneuse-cap #saisie-web-visionneuse { position: absolute; top: var(--haut-cap-web, 64px); left: 12px; right: 12px; z-index: 6;
  margin: 8px 0 0; padding: 14px; box-sizing: border-box; border-radius: 12px; background: rgba(255, 255, 255, 0.97); color: #16201d;
  font: 17px/1.35 sans-serif; display: flex; flex-direction: column; gap: 10px; box-shadow: 0 6px 20px rgba(0, 0, 0, 0.35); }
dialog#visionneuse-cap #saisie-web-visionneuse[hidden] { display: none; }
dialog#visionneuse-cap #champ-web-visionneuse { min-height: 52px; padding: 0 12px; box-sizing: border-box; width: 100%;
  border: 2px solid #16201d; border-radius: 10px; font: 18px/1.2 sans-serif; color: #16201d; background: #fff; }
dialog#visionneuse-cap #erreur-web-visionneuse { margin: 0; color: #8a1c1c; font-weight: 600; overflow-wrap: anywhere; }
dialog#visionneuse-cap #erreur-web-visionneuse[hidden] { display: none; }
dialog#visionneuse-cap .boutons-web-visionneuse { display: flex; gap: 10px; }
dialog#visionneuse-cap .boutons-web-visionneuse button { flex: 1 1 0; min-height: 52px; border: 0; border-radius: 26px;
  font: 600 17px/1 sans-serif; touch-action: manipulation; }
dialog#visionneuse-cap #ouvrir-web-visionneuse { background: #16201d; color: #fff; }
dialog#visionneuse-cap #annuler-web-visionneuse { background: rgba(22, 32, 29, 0.12); color: #16201d; }
`;

  function brancher(doc, {
    fenetre = doc.getElementById('visionneuse-cap'),
    // Ouvre la visionneuse vide si elle est fermée (visionneuseCap.instance.ouvrirVide dans Cap) ; remplaçable.
    ouvrirVisionneuse = () => (typeof visionneuseCap !== 'undefined' && visionneuseCap.instance ? visionneuseCap.instance.ouvrirVide() : null),
    enLigne = () => (typeof navigator === 'undefined' || navigator.onLine !== false),
    // Pose l'adresse dans le cadre (remplacée dans les tests : aucun réseau).
    poserAdresse = (cadre, adresse) => { cadre.src = adresse; },
    delaiReponseMs = 15000, // sans « load » au bout de 15 s : « Le site ne répond pas… »
    dureeConseilMs = 8000, // « Si la page reste blanche… » reste 8 s
    minuteur = (f, ms) => setTimeout(f, ms), annulerMinuteur = id => clearTimeout(id),
    // 13/11/2026 (chemin 1) : ouvre une adresse YouTube HORS de Cap (un lien suivi : la coque l'envoie à l'application YouTube).
    ouvrirAppli = adresse => { const a = doc.createElement('a'); a.href = adresse; a.rel = 'noopener'; doc.body.append(a); a.click(); a.remove(); }
  } = {}) {
    if (!fenetre) return null;
    let panneau = null;
    let message = null;
    let cadre = null;
    let courant = null; // { sorte } du site ou de la vidéo montré, ou null
    let numero = 0;
    let minuteurReponse = null;
    let minuteurConseil = null;

    function fabriquerPanneau() {
      if (panneau) return;
      if (!doc.getElementById('style-web-visionneuse')) {
        const s = doc.createElement('style');
        s.id = 'style-web-visionneuse';
        s.textContent = STYLE;
        (doc.head || doc.documentElement).append(s);
      }
      // Déjà dans la page (second branchement) : réutilisé, jamais en double (mêmes id).
      panneau = doc.getElementById('web-visionneuse');
      message = doc.getElementById('message-web-visionneuse');
      if (panneau && message) return;
      panneau = doc.createElement('div');
      panneau.id = 'web-visionneuse';
      panneau.hidden = true;
      message = doc.createElement('p');
      message.id = 'message-web-visionneuse';
      message.setAttribute('role', 'status');
      message.hidden = true;
      panneau.append(message);
      fenetre.append(panneau);
    }
    function dire(texte) {
      if (!message) return;
      message.textContent = texte || '';
      message.hidden = !texte;
    }
    function arreterMinuteurs() {
      if (minuteurReponse !== null) annulerMinuteur(minuteurReponse);
      if (minuteurConseil !== null) annulerMinuteur(minuteurConseil);
      minuteurReponse = null;
      minuteurConseil = null;
    }
    function retirerCadre() {
      if (!cadre) return;
      try { cadre.src = 'about:blank'; } catch (e) { /* rien */ }
      cadre.remove();
      cadre = null;
    }

    // Ferme le site ou la vidéo (la visionneuse reste ouverte). Vrai si quelque chose était montré.
    function fermer() {
      numero++;
      arreterMinuteurs();
      const etait = Boolean(courant || (panneau && !panneau.hidden));
      retirerCadre();
      courant = null;
      if (panneau) { panneau.hidden = true; panneau.classList.remove('video'); }
      dire('');
      return etait;
    }

    // texte : l'adresse collée ou écrite. Rend { ok, sorte?, message? } ; jamais l'adresse dans un message.
    function ouvrir(texte) {
      const r = analyserAdresse(texte);
      if (!r.ok) return { ok: false, code: r.code, message: r.message };
      if (r.sorte === 'youtube-appli') { // 13/11/2026 (chemin 1) : rien dans la visionneuse ; l'application YouTube s'ouvre
        if (!enLigne()) return { ok: false, code: 'pas-de-reseau', message: MESSAGES['pas-de-reseau'] };
        ouvrirAppli(r.adresseAppli);
        return { ok: true, sorte: 'youtube-appli' };
      }
      if (!fenetre.open) {
        try { ouvrirVisionneuse(); } catch (e) { /* vérifié juste dessous */ }
        if (!fenetre.open) return { ok: false, code: 'visionneuse-absente', message: MESSAGES['visionneuse-absente'] };
      }
      fermer();
      fabriquerPanneau();
      const n = numero;
      panneau.hidden = false;
      panneau.classList.toggle('video', r.sorte === 'youtube');
      courant = { sorte: r.sorte };
      if (!enLigne()) { dire(MESSAGES['pas-de-reseau']); return { ok: false, code: 'pas-de-reseau', message: MESSAGES['pas-de-reseau'] }; }
      cadre = doc.createElement('iframe');
      cadre.id = 'cadre-web-visionneuse';
      cadre.title = r.sorte === 'youtube' ? 'Vidéo YouTube' : 'Site web';
      cadre.setAttribute('sandbox', SANDBOX);
      cadre.setAttribute('allow', PERMISSIONS);
      cadre.setAttribute('allowfullscreen', '');
      cadre.setAttribute('referrerpolicy', 'strict-origin-when-cross-origin'); // YouTube refuse une vidéo intégrée sans origine
      cadre.setAttribute('loading', 'eager');
      cadre.addEventListener('load', () => {
        if (n !== numero || !cadre) return;
        if (minuteurReponse !== null) { annulerMinuteur(minuteurReponse); minuteurReponse = null; }
        if (r.sorte === 'site') {
          dire(MESSAGES['peut-refuser']);
          minuteurConseil = minuteur(() => { minuteurConseil = null; if (n === numero) dire(''); }, dureeConseilMs);
        } else dire('');
      });
      panneau.insertBefore(cadre, message);
      dire(r.sorte === 'youtube' ? 'Chargement de la vidéo…' : 'Chargement du site…');
      minuteurReponse = minuteur(() => { minuteurReponse = null; if (n === numero) dire(MESSAGES['ne-repond-pas']); }, delaiReponseMs);
      poserAdresse(cadre, r.adresseCadre);
      return { ok: true, sorte: r.sorte };
    }

    // ----- Marche 3 (13/11/2026, accord de Max) : « Site ou vidéo » dans le menu du bouton blanc -----
    // Un bouton du menu (#menu-visionneuse, posé par Cap) ouvre un petit formulaire par-dessus la visionneuse : un champ
    // pour coller l'adresse, « Ouvrir » et « Annuler ». L'adresse passe par analyserAdresse (marche 1) puis ouvrir
    // (marche 2) : seulement https ; un refus s'affiche en une phrase simple, jamais l'adresse. Rien n'est gardé : le champ
    // est vidé à « Annuler », après une ouverture réussie et à la fermeture de la visionneuse.
    let saisie = null;
    let champ = null;
    let erreur = null;
    const noeud = (balise, id, texte) => { const n = doc.createElement(balise); if (id) n.id = id; if (texte !== undefined) n.textContent = texte; return n; };
    function fabriquerSaisie() {
      if (saisie) return;
      fabriquerPanneau(); // le style commun
      saisie = doc.getElementById('saisie-web-visionneuse');
      if (saisie) { champ = doc.getElementById('champ-web-visionneuse'); erreur = doc.getElementById('erreur-web-visionneuse'); return; }
      saisie = noeud('form', 'saisie-web-visionneuse');
      saisie.hidden = true;
      saisie.noValidate = true;
      saisie.setAttribute('role', 'dialog');
      saisie.setAttribute('aria-label', 'Site ou vidéo');
      const etiquette = noeud('label', 'etiquette-web-visionneuse', 'Adresse du site ou de la vidéo YouTube');
      etiquette.htmlFor = 'champ-web-visionneuse';
      champ = noeud('input', 'champ-web-visionneuse');
      champ.type = 'text'; // pas « url » : aucune bulle d'erreur du navigateur, Cap dit lui-même ce qui ne va pas
      champ.setAttribute('inputmode', 'url');
      champ.setAttribute('autocomplete', 'off');
      champ.setAttribute('autocapitalize', 'off');
      champ.setAttribute('spellcheck', 'false');
      champ.maxLength = LONGUEUR_MAX;
      champ.placeholder = 'https://…';
      erreur = noeud('p', 'erreur-web-visionneuse');
      erreur.setAttribute('role', 'alert');
      erreur.hidden = true;
      const boutons = noeud('div');
      boutons.className = 'boutons-web-visionneuse';
      const ouvrirB = noeud('button', 'ouvrir-web-visionneuse', 'Ouvrir');
      ouvrirB.type = 'submit';
      const annulerB = noeud('button', 'annuler-web-visionneuse', 'Annuler');
      annulerB.type = 'button';
      boutons.append(ouvrirB, annulerB);
      saisie.append(etiquette, champ, erreur, boutons);
      saisie.addEventListener('submit', e => { e.preventDefault(); validerSaisie(); });
      annulerB.addEventListener('click', () => cacherSaisie());
      champ.addEventListener('input', () => { erreur.hidden = true; erreur.textContent = ''; });
      fenetre.append(saisie);
    }
    function montrerSaisie() {
      if (!fenetre.open) return false;
      fabriquerSaisie();
      champ.value = '';
      erreur.hidden = true;
      erreur.textContent = '';
      saisie.hidden = false;
      try { champ.focus({ preventScroll: true }); } catch (e) { /* rien */ }
      return true;
    }
    function cacherSaisie() {
      if (!saisie) return false;
      const etait = !saisie.hidden;
      saisie.hidden = true;
      champ.value = '';
      erreur.hidden = true;
      erreur.textContent = '';
      return etait;
    }
    function validerSaisie() {
      if (!saisie || saisie.hidden) return null;
      const r = ouvrir(champ.value);
      if (r.ok) { cacherSaisie(); return r; }
      if (r.code === 'pas-de-reseau') { cacherSaisie(); return r; } // le message est déjà dans le panneau
      erreur.textContent = r.message; // une phrase de MESSAGES : jamais l'adresse
      erreur.hidden = false;
      return r;
    }
    function brancherMenu() {
      const menu = doc.getElementById('menu-visionneuse');
      if (!menu || doc.getElementById('menu-web-visionneuse')) return null;
      const b = noeud('button', 'menu-web-visionneuse', 'Site ou vidéo');
      b.type = 'button';
      // Après « Ouvrir un chantier » s'il est là, sinon après « Ajouter un fichier », sinon à la fin.
      const apres = doc.getElementById('menu-chantiers-visionneuse') || doc.getElementById('menu-ajouter-visionneuse');
      if (apres && apres.parentNode === menu) apres.after(b); else menu.append(b);
      b.addEventListener('click', () => { montrerSaisie(); });
      return b;
    }
    brancherMenu();

    // La visionneuse se ferme (bouton, voix, retour du téléphone) : le cadre est vidé et retiré, le champ vidé.
    // 13/11/2026 (marche 4) : + surveillance de l'attribut « open » : l'événement « close » peut arriver en retard (après
    // une réouverture : il est alors ignoré) ou pas du tout (constaté dans Edge sans fenêtre) ; l'attribut, lui, change
    // tout de suite. Avant : seulement fenetre.addEventListener('close', …).
    const surFermeture = () => { if (!fenetre.open) { fermer(); cacherSaisie(); } };
    fenetre.addEventListener('close', surFermeture);
    if (typeof MutationObserver !== 'undefined') new MutationObserver(surFermeture).observe(fenetre, { attributes: true, attributeFilter: ['open'] });

    // ----- Marche 4 (13/11/2026, accord de Max) : LE RETOUR -----
    // « Fermer » (menu, haut de la page, voix) et le retour du téléphone appellent retour() AVANT de fermer la visionneuse
    // (une ligne à ajouter dans visionneuse_cap.js par l'Opus : voir LIRE_POUR_OPUS.md). Un retour ferme UNE chose,
    // la plus haute : d'abord le formulaire « Site ou vidéo », puis le site ou la vidéo ; la visionneuse reste ouverte.
    // Vrai si quelque chose a été fermé ici (Cap ne ferme alors rien d'autre) ; faux sinon (Cap continue comme avant).
    function retour() {
      if (cacherSaisie()) return true;
      return fermer();
    }

    return { ouvrir, fermer, retour, ouvert: () => Boolean(courant), sorte: () => (courant ? courant.sorte : ''),
      brancherMenu, montrerSaisie, cacherSaisie, validerSaisie, saisieOuverte: () => Boolean(saisie && !saisie.hidden) };
  }

  return { MESSAGES, SANDBOX, PERMISSIONS, analyserAdresse, lireDepart, brancher };
})();

// Dans Cap (pas dans les tests) : branché sur la fenêtre de la visionneuse, si elle existe.
if (typeof document !== 'undefined' && !(typeof window !== 'undefined' && window.CAP_TESTS)) {
  visionneuseWeb.instance = visionneuseWeb.brancher(document);
}
