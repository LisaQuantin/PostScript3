/* 
Ce code crée une police OpenType avec un glyphe représentant la lettre 'A' et l'enregistre dans un fichier TestA.otf
*/

const opentype = require('opentype.js');
const fs = require('fs');

// this .notdef glyph is required.
const notdefGlyph = new opentype.Glyph({
    name: '.notdef',
    advanceWidth: 650,
    path: new opentype.Path()
});


// Créer un chemin pour le glyphe 'A'
// Pour voir le résultat, copier dans un fichier .svg (voir testA.svg) et ouvrir dans un navigateur
// ou dans vsCode avec l'extension "SVG Viewer"
const pathA = new opentype.Path();
// On dessine le contour extérieur du A en un seul trait
pathA.moveTo(100, 0);      // Bas gauche
pathA.lineTo(200, 400);    // Sommet
pathA.lineTo(300, 0);      // Bas droite
pathA.lineTo(250, 0);      // On remonte un peu (jambe droite)
pathA.lineTo(200, 200);    // On va vers l'intérieur (barre)
pathA.lineTo(150, 200);    // On traverse (barre)
pathA.lineTo(100, 0);      // On redescend (jambe gauche)
pathA.lineTo(100, 0);      // On ferme sur le départ
pathA.close();


const glyphA = new opentype.Glyph({
  name: 'A',
  unicode: 65,          // Code Unicode pour 'A'
  path: pathA,
  advanceWidth: 600     // Largeur du caractère
});

// Créer la police
const font = new opentype.Font({
    familyName: 'TestA',
    styleName: 'Regular',
    unitsPerEm: 1000,               // Taille de la "boite" des lettres
    ascender: 800,                  // Hauteur max (des h, b, l, ...)
    descender: -200,                // Descente max (des p, q, y, ...)
    glyphs: [notdefGlyph, glyphA]   // Liste des glyphes de la police
});

// Sauvegarder la police
fs.writeFileSync("TestA.otf", Buffer.from(font.toArrayBuffer()));