'use strict';

// 10/11/2026 (accord de Max, séance 3) : LE SEUL ENDROIT qui décide ce qu'est un fichier : « musique », « vidéo », PDF,
// image, ou autre. Le comptage (relations_compte.js), l'essai de visibilité (relations_creation.js) et la musique
// (relations_mp3.js) passent tous par ici. Pour ajouter un format plus tard (par exemple le MKV, après un essai sur le
// Pixel), on l'ajoute seulement dans les listes ci-dessous.
// Formats décidés par Max (10/11/2026) : musique = MP3, FLAC, M4A, WAV, OGG, OPUS ; vidéo = MP4, WEBM.
// 12/11/2026 (c149, décision de Max, ligne 73) : + MKV (vidéo). Avant : « Pas de MKV. »
// L'extension du nom passe d'abord ; sans extension connue, le type donné par Google Drive (mimeType).
// Avant : seul le MP3 était reconnu (relations_compte.js et relations_creation.js, chacun le sien).
const typesFichiers = (() => {
  const DOSSIER = 'application/vnd.google-apps.folder';
  const MUSIQUE = Object.freeze({ mp3: 'MP3', flac: 'FLAC', m4a: 'M4A', wav: 'WAV', ogg: 'OGG', oga: 'OGG', opus: 'OPUS' });
  const VIDEO = Object.freeze({ mp4: 'MP4', webm: 'WEBM', mkv: 'MKV' }); // c149 : + mkv
  const TYPES_MUSIQUE = Object.freeze({ 'audio/mpeg': 'MP3', 'audio/mp3': 'MP3', 'audio/flac': 'FLAC', 'audio/x-flac': 'FLAC',
    'audio/mp4': 'M4A', 'audio/x-m4a': 'M4A', 'audio/m4a': 'M4A', 'audio/wav': 'WAV', 'audio/x-wav': 'WAV', 'audio/wave': 'WAV',
    'audio/vnd.wave': 'WAV', 'audio/ogg': 'OGG', 'audio/opus': 'OPUS' });
  const TYPES_VIDEO = Object.freeze({ 'video/mp4': 'MP4', 'video/webm': 'WEBM', 'video/x-matroska': 'MKV' }); // c149 : + MKV
  const extension = nom => { const x = /\.([a-z0-9]{1,5})$/i.exec(String(nom || '').trim()); return x ? x[1].toLowerCase() : ''; };

  // { sorte, format } : sorte = 'dossier', 'musique', 'video', 'pdf', 'images' ou 'autres' ; format = « MP3 », « FLAC »…
  function analyser(fichier) {
    const type = String((fichier && fichier.mimeType) || '').toLowerCase();
    if (type === DOSSIER) return { sorte: 'dossier', format: '' };
    const ext = extension(fichier && fichier.name);
    if (MUSIQUE[ext]) return { sorte: 'musique', format: MUSIQUE[ext] };
    if (VIDEO[ext]) return { sorte: 'video', format: VIDEO[ext] };
    if (ext === 'pdf') return { sorte: 'pdf', format: 'PDF' };
    if (/^(jpe?g|png|gif|webp|heic)$/.test(ext)) return { sorte: 'images', format: ext.toUpperCase() };
    // Extension inconnue ou absente : le type donné par Drive (c149 : un MKV, « video/x-matroska », est une vidéo ; avant : « autre »).
    if (TYPES_MUSIQUE[type]) return { sorte: 'musique', format: TYPES_MUSIQUE[type] };
    if (TYPES_VIDEO[type]) return { sorte: 'video', format: TYPES_VIDEO[type] };
    if (type === 'application/pdf') return { sorte: 'pdf', format: 'PDF' };
    if (type.startsWith('image/')) return { sorte: 'images', format: type.slice(6).toUpperCase() };
    return { sorte: 'autres', format: '' };
  }
  const sorte = fichier => analyser(fichier).sorte;
  // Nom d'un morceau sans son extension de musique (« 01 Un.flac » → « 01 Un »).
  const sansExtensionMusique = nom => String(nom || '').replace(/\.([a-z0-9]{1,5})$/i, (tout, ext) => (MUSIQUE[ext.toLowerCase()] ? '' : tout)).trim();
  // 10/11/2026 (séance 4 du lecteur) : nom d'une vidéo sans son extension (« Film.mp4 » → « Film »).
  const sansExtensionVideo = nom => String(nom || '').replace(/\.([a-z0-9]{1,5})$/i, (tout, ext) => (VIDEO[ext.toLowerCase()] ? '' : tout)).trim();

  return { DOSSIER, MUSIQUE, VIDEO, analyser, sorte, sansExtensionMusique, sansExtensionVideo };
})();
