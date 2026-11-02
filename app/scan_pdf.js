'use strict';

// Assemble des pages JPEG en un seul fichier PDF. Sans DOM, sans ressource externe.
const scanPdf = (() => {
  const largeur_page = 595;
  const encodeur = new TextEncoder();

  function assembler(pages) {
    if (!Array.isArray(pages) || !pages.length) throw new Error('Aucune page à mettre dans le PDF.');
    const morceaux = [];
    const positions = [];
    let longueur = 0;
    const ecrire = contenu => {
      const octets = typeof contenu === 'string' ? encodeur.encode(contenu) : contenu;
      morceaux.push(octets);
      longueur += octets.length;
    };
    const objet = (numero, contenu) => {
      positions[numero] = longueur;
      ecrire(`${numero} 0 obj\n`);
      ecrire(contenu);
      ecrire('\nendobj\n');
    };

    const nombre = pages.length;
    const numeroPage = i => 3 + i * 3;
    ecrire('%PDF-1.4\n%\xE2\xE3\xCF\xD3\n');
    objet(1, '<< /Type /Catalog /Pages 2 0 R >>');
    objet(2, `<< /Type /Pages /Count ${nombre} /Kids [${pages.map((_, i) => `${numeroPage(i)} 0 R`).join(' ')}] >>`);

    pages.forEach((page, i) => {
      const jpeg = page.jpeg;
      if (!(jpeg instanceof Uint8Array) || jpeg.length < 4 || jpeg[0] !== 0xFF || jpeg[1] !== 0xD8) {
        throw new Error(`La page ${i + 1} n’est pas une image JPEG valide.`);
      }
      if (!(page.largeur > 0) || !(page.hauteur > 0)) throw new Error(`La page ${i + 1} n’a pas de dimensions.`);
      const hauteurPage = Math.max(1, Math.round(largeur_page * page.hauteur / page.largeur));
      const n = numeroPage(i);
      const flux = `q ${largeur_page} 0 0 ${hauteurPage} 0 0 cm /Im0 Do Q`;
      objet(n, `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${largeur_page} ${hauteurPage}] `
        + `/Resources << /XObject << /Im0 ${n + 1} 0 R >> >> /Contents ${n + 2} 0 R >>`);
      positions[n + 1] = longueur;
      ecrire(`${n + 1} 0 obj\n<< /Type /XObject /Subtype /Image /Width ${page.largeur} /Height ${page.hauteur} `
        + `/ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ${jpeg.length} >>\nstream\n`);
      ecrire(jpeg);
      ecrire('\nendstream\nendobj\n');
      objet(n + 2, `<< /Length ${flux.length} >>\nstream\n${flux}\nendstream`);
    });

    const total = 3 + nombre * 3;
    const debutTable = longueur;
    let table = `xref\n0 ${total}\n0000000000 65535 f \n`;
    for (let numero = 1; numero < total; numero++) {
      table += `${String(positions[numero]).padStart(10, '0')} 00000 n \n`;
    }
    ecrire(table);
    ecrire(`trailer\n<< /Size ${total} /Root 1 0 R >>\nstartxref\n${debutTable}\n%%EOF\n`);

    const sortie = new Uint8Array(longueur);
    let decalage = 0;
    for (const m of morceaux) { sortie.set(m, decalage); decalage += m.length; }
    return sortie;
  }

  return { assembler };
})();
