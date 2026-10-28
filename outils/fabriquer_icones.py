import base64
import pathlib
import struct
import subprocess
import tempfile
import zlib

RACINE = pathlib.Path(__file__).resolve().parent.parent
EDGE = pathlib.Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
SOURCE = RACINE / "icone" / "icone_cap_essai1.png"
DESTINATION = RACINE / "app" / "icones"


def bloc_png(type_bloc, contenu):
    return (struct.pack(">I", len(contenu)) + type_bloc + contenu
            + struct.pack(">I", zlib.crc32(type_bloc + contenu) & 0xFFFFFFFF))


def recadrer_png(source, destination, taille):
    donnees = source.read_bytes()
    if donnees[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Capture PNG attendue")
    position = 8
    compresse = bytearray()
    while position < len(donnees):
        longueur = struct.unpack(">I", donnees[position:position + 4])[0]
        type_bloc = donnees[position + 4:position + 8]
        contenu = donnees[position + 8:position + 8 + longueur]
        if type_bloc == b"IHDR":
            entete = contenu
        elif type_bloc == b"IDAT":
            compresse.extend(contenu)
        position += longueur + 12
    largeur, hauteur, profondeur, couleur, compression, filtre, entrelacement = struct.unpack(">IIBBBBB", entete)
    if (profondeur != 8 or couleur not in (2, 6) or compression != 0
            or filtre != 0 or entrelacement != 0 or min(largeur, hauteur) < taille):
        raise ValueError("Format de capture PNG inattendu")
    canaux = 4 if couleur == 6 else 3
    pas = largeur * canaux
    brut = zlib.decompress(compresse)
    precedente = bytearray(pas)
    sortie = bytearray()
    for y in range(taille):
        debut = y * (pas + 1)
        filtrage = brut[debut]
        ligne = bytearray(brut[debut + 1:debut + 1 + pas])
        for x in range(pas):
            gauche = ligne[x - canaux] if x >= canaux else 0
            haut = precedente[x]
            coin = precedente[x - canaux] if x >= canaux else 0
            if filtrage == 0:
                prediction = 0
            elif filtrage == 1:
                prediction = gauche
            elif filtrage == 2:
                prediction = haut
            elif filtrage == 3:
                prediction = (gauche + haut) // 2
            elif filtrage == 4:
                p = gauche + haut - coin
                distances = (abs(p - gauche), abs(p - haut), abs(p - coin))
                prediction = (gauche, haut, coin)[distances.index(min(distances))]
            else:
                raise ValueError("Filtre PNG inconnu")
            ligne[x] = (ligne[x] + prediction) & 255
        sortie.append(0)
        sortie.extend(ligne[:taille * canaux])
        precedente = ligne
    entete = struct.pack(">IIBBBBB", taille, taille, profondeur, couleur, 0, 0, 0)
    destination.write_bytes(b"\x89PNG\r\n\x1a\n" + bloc_png(b"IHDR", entete)
                            + bloc_png(b"IDAT", zlib.compress(sortie, 9))
                            + bloc_png(b"IEND", b""))


def main():
    if not EDGE.exists():
        raise FileNotFoundError(f"Edge introuvable : {EDGE}")
    DESTINATION.mkdir(parents=True, exist_ok=True)
    image = base64.b64encode(SOURCE.read_bytes()).decode("ascii")
    variantes = [("icone-192.png", 192, False), ("icone-512.png", 512, False),
                 ("icone-maskable-512.png", 512, True), ("favicon.png", 48, False)]
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as dossier:
        temporaire = pathlib.Path(dossier)
        for nom, taille, maskable in variantes:
            origine, cote = (208, 608) if maskable else (130, 764)
            facteur = taille / cote
            rayon = "0" if maskable else "25%"
            page = temporaire / "icone.html"
            page.write_text(f'''<!doctype html><html><head><meta charset="utf-8">
<style>html,body{{margin:0;padding:0;overflow:hidden;background:transparent}}
.icone{{position:absolute;left:0;top:0;width:{taille}px;height:{taille}px;
overflow:hidden;border-radius:{rayon}}}
img{{position:absolute;width:{1024 * facteur}px;height:{1024 * facteur}px;
left:{-origine * facteur}px;top:{-origine * facteur}px;max-width:none}}</style>
</head><body><div class="icone"><img src="data:image/png;base64,{image}"></div></body></html>''', encoding="utf-8")
            capture = temporaire / "capture.png"
            capture.unlink(missing_ok=True)
            resultat = subprocess.run([
                str(EDGE), "--headless", "--disable-gpu", "--no-first-run",
                "--no-default-browser-check", "--hide-scrollbars",
                "--force-device-scale-factor=1", "--default-background-color=00000000",
                "--window-size=1024,1024", "--virtual-time-budget=1500",
                f"--user-data-dir={temporaire / 'profil'}",
                f"--screenshot={capture}", page.as_uri()
            ], capture_output=True, timeout=120)
            if resultat.returncode != 0 or not capture.exists():
                raise RuntimeError(resultat.stderr.decode("utf-8", errors="replace"))
            recadrer_png(capture, DESTINATION / nom, taille)
            print(f"{nom} : {taille} x {taille}")


if __name__ == "__main__":
    main()
