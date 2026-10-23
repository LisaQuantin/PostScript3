"""
Crée une police OpenType (.otf) à partir de SVG, avec variantes alternées
automatiquement (effet écriture manuscrite) grâce à la fonctionnalité 'calt'.

Installation :  pip install fonttools

Structure attendue (dossier ../svg_v1) :
    ../svg_v1/1_U0031/variante_001.svg, variante_002.svg, ...   -> variantes de « 1 »
    ../svg_v1/a_U0061/variante_001.svg ... variante_017.svg     -> variantes de « a »
Le nom du sous-dossier se termine par _U suivi du code Unicode en hexadécimal.
Les variantes sont prises dans l'ordre numérique (variante_2 avant variante_10).
"""
import base64
import math
import os
import re
import xml.etree.ElementTree as ET
from collections import defaultdict

from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.fontBuilder import FontBuilder
from fontTools.misc.transform import Transform
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib.path import parse_path
from fontTools.svgLib.path.shapes import PathBuilder


DOSSIER = "../svg_v1"

# --- TAILLE ---
# SVG mis à l'échelle, on a besoin d'une lettre & hauteur de référence
LETTRE_REFERENCE = "a"
HAUTEUR_REFERENCE = 200

# --- PLACEMENT VERTICAL ---
# Modes :
#   "bas"      : le bas du dessin est posé sur la ligne de base (défaut)
#   "haut_x"   : le haut du dessin est à la hauteur des minuscules (p, q, g, y...)
#   "haut_i"   : le haut est à la hauteur du « i » (pour le « j »)
#   "haut_asc" : le haut est à la hauteur des lettres montantes (apostrophe, guillemets)
#   "haut_cap" : le haut est à la hauteur des majuscules
#   "milieu"   : centré verticalement à mi-hauteur des minuscules (tirets, +, =)
#   "sous"     : le bas descend un peu sous la ligne de base (virgule, point-virgule)

ALIGNEMENT = {
    **{c: "haut_x" for c in "gpqyç"},
    "j": "haut_i",
    "Q": "haut_cap",
    **{c: "haut_asc" for c in "'\"`^°*‘’“”«»"},
    **{c: "milieu" for c in "-–—−+=~·•"},
    **{c: "sous" for c in ",;"},
}
SOUS = 0.2                   # profondeur des modes "sous", en fraction de la hauteur des minuscules

MARGE = 25                   # espace de chaque côté des lettres
LARGEUR_ESPACE = 300
NOM_POLICE = "V1"
SORTIE = "V1.otf"
# ---------------------------------------------------------------------------

EM = 1000


def nom_glyphe(code):
    return f"uni{code:04X}" if code <= 0xFFFF else f"u{code:X}"


# --- Lecture des SVG (avec transformations des groupes parents) --------------
_NB = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"


def parse_transform(texte):
    """Analyse un attribut transform SVG (matrix, translate, scale, rotate, skew)."""
    total = Transform()
    for nom, args in re.findall(r"(\w+)\s*\(([^)]*)\)", texte or ""):
        v = [float(x) for x in re.findall(_NB, args)]
        nom = nom.lower()
        if nom == "matrix" and len(v) == 6:
            t = Transform(*v)
        elif nom == "translate":
            t = Transform(1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0)
        elif nom == "scale":
            t = Transform(v[0], 0, 0, v[1] if len(v) > 1 else v[0], 0, 0)
        elif nom == "rotate":
            a = math.radians(v[0])
            c, s = math.cos(a), math.sin(a)
            t = Transform(c, s, -s, c, 0, 0)
            if len(v) == 3:
                t = Transform(1, 0, 0, 1, v[1], v[2]).transform(t).transform(
                    Transform(1, 0, 0, 1, -v[1], -v[2]))
        elif nom == "skewx":
            t = Transform(1, 0, math.tan(math.radians(v[0])), 1, 0, 0)
        elif nom == "skewy":
            t = Transform(1, math.tan(math.radians(v[0])), 0, 1, 0, 0)
        else:
            continue
        total = total.transform(t)   # la transformation suivante s'applique en premier
    return total


def _nombre(txt):
    m = re.match(r"\s*(" + _NB + ")", txt or "")
    return float(m.group(1)) if m else None


def lire_svg(fichier):
    """Retourne (liste de (d, Transform), viewBox = (x, y, largeur, hauteur))."""
    racine = ET.parse(fichier).getroot()
    formes = []

    def parcourir(el, parent_t):
        if not isinstance(el.tag, str):
            return
        tag = el.tag.split("}")[-1].lower()
        if tag in ("defs", "clippath", "mask", "symbol", "metadata", "style"):
            return
        t = parent_t
        if "transform" in el.attrib:
            t = parent_t.transform(parse_transform(el.attrib["transform"]))
        if tag in ("path", "rect", "circle", "ellipse", "line", "polygon", "polyline"):
            pb = PathBuilder()
            try:
                pb.add_path_from_element(el)
            except (TypeError, ValueError):
                pb.paths = []
            for d in pb.paths:
                if d:
                    formes.append((d, t))
        for enfant in el:
            parcourir(enfant, t)

    parcourir(racine, Transform())
    vb = racine.attrib.get("viewBox")
    if vb:
        x, y, w, h = [float(v) for v in re.split(r"[\s,]+", vb.strip())]
    else:
        w = _nombre(racine.attrib.get("width")) or 100.0
        h = _nombre(racine.attrib.get("height")) or 100.0
        x, y = 0.0, 0.0
    return formes, (x, y, w, h)


def dessiner(formes, vb, pen, echelle=1.0, dx=0.0, dy=0.0):
    """Dessine en coordonnées de police (Y vers le haut) : x' = echelle*x + dx,
    y' = -echelle*y + dy, après un éventuel retournement du SVG."""
    x0, y0, w, h = vb
    fx = 1
    fy = 1
    miroir = Transform(fx, 0, 0, fy, (1 - fx) * (x0 + w / 2), (1 - fy) * (y0 + h / 2))
    vue = Transform(echelle, 0, 0, -echelle, dx, dy)
    for d, t in formes:
        parse_path(d, TransformPen(pen, vue.transform(miroir.transform(t))))


def charstring(formes, vb, echelle, largeur, dx, dy):
    pen = T2CharStringPen(largeur, None)
    dessiner(formes, vb, pen, echelle, dx, dy)
    return pen.getCharString()


def bornes(formes, vb):
    """Boîte englobante (xmin, ymin, xmax, ymax) à l'échelle 1, Y vers le haut."""
    bp = BoundsPen(None)
    dessiner(formes, vb, bp)
    return bp.bounds


# 1. Lire les SVG, groupés par code Unicode -----------------------------------
variantes = defaultdict(list)   # code -> [(formes, vb, nom), ...]
motif_dossier = re.compile(r"_U([0-9A-Fa-f]{4,6})$")


def cle_naturelle(nom):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", nom)]


for sous in sorted(os.listdir(DOSSIER), key=cle_naturelle):
    chemin_sous = os.path.join(DOSSIER, sous)
    m = motif_dossier.search(sous)
    if not (os.path.isdir(chemin_sous) and m):
        continue
    code = int(m.group(1), 16)
    fichiers = sorted(
        (f for f in os.listdir(chemin_sous) if f.lower().endswith(".svg")),
        key=cle_naturelle,
    )
    for f in fichiers:
        formes, vb = lire_svg(os.path.join(chemin_sous, f))
        if not formes:
            print(f"Ignoré (aucune forme lisible) : {sous}/{f}")
            continue
        variantes[code].append((formes, vb, f"{sous}/{f}"))

if not variantes:
    raise SystemExit(f"Aucun SVG trouvé dans {DOSSIER} (attendu : sous-dossiers du type 1_U0031)")

# 2. Échelle commune + placement vertical --------------------------------------
bb = {}   # code -> [boîte à l'échelle 1, ...]
for code, liste in variantes.items():
    bb[code] = [bornes(f, vb) for (f, vb, n) in liste]

code_ref = ord(LETTRE_REFERENCE) if LETTRE_REFERENCE else None
hs = [b[3] - b[1] for b in bb[code_ref]]
echelle = HAUTEUR_REFERENCE / (sum(hs) / len(hs))
print(f"Référence « {LETTRE_REFERENCE} » : {sum(hs)/len(hs):.0f} unités SVG -> {HAUTEUR_REFERENCE}")
print(f"Échelle appliquée : {echelle:.4f} unité de police par unité SVG")


def hauteur_moyenne(lettres, defaut):
    hs = [echelle * (b[3] - b[1]) for c in lettres if ord(c) in bb for b in bb[ord(c)] if b]
    return sum(hs) / len(hs) if hs else defaut


XH = hauteur_moyenne("aceonmursvwxz", HAUTEUR_REFERENCE)
ASC = hauteur_moyenne("lhbdk", XH * 1.5)
CAP = hauteur_moyenne("EHTLIFZ", XH * 1.4)
HI = hauteur_moyenne("i", ASC)
print(f"Hauteurs mesurées : minuscules {XH:.0f}, montantes {ASC:.0f}, majuscules {CAP:.0f}")


def position(code, b):
    """Retourne (dx, dy) pour une boîte b donnée, selon le mode d'alignement."""
    x1, y1, x2, y2 = b
    mode = ALIGNEMENT.get(chr(code), "bas")
    if mode == "haut_x":
        dy = XH - echelle * y2
    elif mode == "haut_i":
        dy = HI - echelle * y2
    elif mode == "haut_asc":
        dy = ASC - echelle * y2
    elif mode == "haut_cap":
        dy = CAP - echelle * y2
    elif mode == "milieu":
        dy = XH / 2 - echelle * (y1 + y2) / 2
    elif mode == "sous":
        dy = -SOUS * XH - echelle * y1
    else:  # "bas"
        dy = -echelle * y1
    return MARGE - echelle * x1, dy


prets = defaultdict(list)   # code -> [(formes, vb, largeur, dx, dy, lsb), ...]
y_min, y_max = 0.0, 0.0
for code, liste in variantes.items():
    for (formes, vb, nom), b in zip(liste, bb[code]):
        if b is None:
            print(f"Ignoré (vide) : {nom}")
            continue
        dx, dy = position(code, b)
        largeur = round(echelle * (b[2] - b[0]) + 2 * MARGE)
        y_max = max(y_max, echelle * b[3] + dy)
        y_min = min(y_min, echelle * b[1] + dy)
        prets[code].append((formes, vb, largeur, dx, dy, MARGE))
variantes = prets
print(f"Étendue verticale : de {y_min:.0f} à {y_max:.0f}")

# 3. Construire les glyphes ----------------------------------------------------
K = max(len(v) for v in variantes.values())          # nombre d'états du cycle
cycle = sorted(c for c, v in variantes.items() if len(v) > 1)

ordre = [".notdef", "space"]
cs = {
    ".notdef": T2CharStringPen(650, None).getCharString(),
    "space": T2CharStringPen(LARGEUR_ESPACE, None).getCharString(),
}
metriques = {".notdef": (650, 0), "space": (LARGEUR_ESPACE, 0)}
cmap = {32: "space"}

for code, liste in sorted(variantes.items()):
    base = nom_glyphe(code)
    formes, vb, larg, dx, dy, lsb = liste[0]
    ordre.append(base)
    cs[base] = charstring(formes, vb, echelle, larg, dx, dy)
    metriques[base] = (larg, lsb)
    cmap[code] = base

    if code in cycle:
        # un glyphe par état : l'état s utilise la variante (s % n)
        for s in range(K):
            formes, vb, larg, dx, dy, lsb = liste[s % len(liste)]
            nom = f"{base}.s{s}"
            ordre.append(nom)
            cs[nom] = charstring(formes, vb, echelle, larg, dx, dy)
            metriques[nom] = (larg, lsb)

# 4. Règles OpenType (calt) ----------------------------------------------------
# Chaque lettre à variantes passe à l'état suivant (s+1) par rapport à la lettre
# précédente : la variante affichée dépend de la position dans le texte.
fea = []
if cycle:
    fea.append("@base = [%s];" % " ".join(nom_glyphe(c) for c in cycle))
    for s in range(K):
        fea.append(
            "@S%d = [%s];" % (s, " ".join(f"{nom_glyphe(c)}.s{s}" for c in cycle))
        )
    fea.append("feature calt {")
    fea.append("  lookup cycle {")
    for s in range(K):
        fea.append(f"    sub @S{s} @base' by @S{(s + 1) % K};")
    fea.append("    sub @base' by @S0;")      # début de mot ou après un autre signe
    fea.append("  } cycle;")
    fea.append("} calt;")

# 5. Assembler la police -------------------------------------------------------
fb = FontBuilder(EM, isTTF=False)
fb.setupGlyphOrder(ordre)
fb.setupCharacterMap(cmap)
fb.setupCFF(NOM_POLICE.replace(" ", "") + "-Regular", {"FullName": NOM_POLICE}, cs, {})
fb.setupHorizontalMetrics(metriques)
ASCENT = max(800, math.ceil(y_max))
DESCENT = max(300, math.ceil(-y_min))
fb.setupHorizontalHeader(ascent=ASCENT, descent=-DESCENT)
fb.setupNameTable({"familyName": NOM_POLICE, "styleName": "Regular"})
fb.setupOS2(sTypoAscender=ASCENT, sTypoDescender=-DESCENT, usWinAscent=ASCENT, usWinDescent=DESCENT)
fb.setupPost()

if fea:
    addOpenTypeFeaturesFromString(fb.font, "\n".join(fea))

fb.save(SORTIE)
print(f"{len(ordre)} glyphes, cycle de {K} états")
print("Police écrite dans :", os.path.abspath(SORTIE))