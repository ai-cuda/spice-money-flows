"""Render an Android layout (from apktool-decoded resources) to a static HTML page.

Usage: python3 -I layout2html.py <apktool_res_dir> <out_dir> <layout_name> [<layout_name> ...]
Writes <out_dir>/<layout_name>.html. Each page loads solver.js (same dir) which positions
ConstraintLayout / RelativeLayout children after the browser measures them.

Approximation, not layoutlib: runtime state (visibility changes, adapters, data binding,
custom view drawing) is not executed. Design-time samples (tools:text, tools:listitem) are used.
"""
import base64
import html
import os
import re
import sys
import xml.etree.ElementTree as ET

ANDROID = "{http://schemas.android.com/apk/res/android}"
APP = "{http://schemas.android.com/apk/res-auto}"
TOOLS = "{http://schemas.android.com/tools}"

RES, OUT = sys.argv[1], sys.argv[2]
LAYOUTS = sys.argv[3:]
SCREEN_W, SCREEN_H = 360, 780
MAX_DEPTH = 40
OVERLAY_RE = re.compile(r'(loading|loader|progress|shimmer|no_?internet|error_?(layout|state|view)|empty_?state|^dialog_|_dialog$|bottomsheet|bottom_sheet)', re.I)

# ---------------------------------------------------------------- resources
def load_values(kind):
    vals = {}
    path = os.path.join(RES, "values", kind + ".xml")
    if not os.path.exists(path):
        return vals
    for el in ET.parse(path).getroot():
        name = el.get("name")
        if name is None:
            continue
        vals[name] = el
    return vals

STRINGS = load_values("strings")
COLORS = load_values("colors")
DIMENS = load_values("dimens")
STYLES = load_values("styles")
INTEGERS = load_values("integers")
BOOLS = load_values("bools")

DRAWABLE_DIRS = ["drawable-xxhdpi", "drawable-xxhdpi-v4", "drawable-xxxhdpi", "drawable-xhdpi", "drawable", "drawable-anydpi",
                 "drawable-hdpi", "drawable-mdpi", "drawable-nodpi", "drawable-v21", "drawable-v23", "drawable-v24",
                 "mipmap-xxhdpi", "mipmap-xxxhdpi", "mipmap-xhdpi", "mipmap-hdpi", "mipmap-anydpi-v26"]
DRAWABLE_DIRS = [d for d in DRAWABLE_DIRS if os.path.isdir(os.path.join(RES, d))] + sorted(
    d for d in os.listdir(RES) if (d.startswith("drawable") or d.startswith("mipmap")) and d not in DRAWABLE_DIRS)

COLOR_DIRS = ["color", "color-v23", "color-v31"]

THEME = {  # ?attr fallbacks (AppCompat / Material light)
    "colorPrimary": "#ff4caf50", "colorPrimaryDark": "#ff388e3c", "colorAccent": "#ff293897",
    "colorOnPrimary": "#ffffffff", "colorSurface": "#ffffffff", "colorOnSurface": "#de000000",
    "android:textColorPrimary": "#de000000", "textColorPrimary": "#de000000",
    "android:textColorSecondary": "#8a000000", "textColorSecondary": "#8a000000",
    "colorControlNormal": "#8a000000", "colorControlActivated": "#ff293897",
    "android:colorBackground": "#ffffffff", "colorBackground": "#ffffffff",
    "selectableItemBackground": None, "selectableItemBackgroundBorderless": None,
    "actionBarSize": "56dip",
}

def text_of(el):
    if el is None:
        return ""
    s = "".join(el.itertext())
    s = s.replace("\\n", "\n").replace("\\'", "'").replace('\\"', '"').replace("\\@", "@").replace("\\?", "?")
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        s = s[1:-1]
    return s

def resolve_ref(v, depth=0):
    """Follow @type/name and ?attr references; return the raw value string or None."""
    if v is None or depth > 10:
        return None
    v = v.strip()
    if v.startswith("?"):
        name = v.split("/")[-1].lstrip("?").replace("attr/", "")
        t = THEME.get(name, THEME.get(name.replace("android:", "")))
        return resolve_ref(t, depth + 1) if t else None
    m = re.match(r"@(?:\+)?(?:android:)?(\w+)/(.+)$", v)
    if not m:
        return v
    typ, name = m.group(1), m.group(2)
    if v.startswith("@android:"):
        return {"color/white": "#ffffffff", "color/black": "#ff000000", "color/transparent": "#00000000",
                "color/darker_gray": "#ffaaaaaa"}.get(f"{typ}/{name}")
    table = {"string": STRINGS, "color": COLORS, "dimen": DIMENS, "integer": INTEGERS, "bool": BOOLS}.get(typ)
    if typ == "color":
        el = COLORS.get(name)
        if el is not None:
            return resolve_ref(text_of(el), depth + 1)
        for d in COLOR_DIRS:
            p = os.path.join(RES, d, name + ".xml")
            if os.path.exists(p):
                return selector_color(p, depth)
        return None
    if table is not None:
        el = table.get(name)
        if el is None:
            return None
        if typ == "string":
            return text_of(el)
        return resolve_ref(text_of(el), depth + 1)
    return v  # drawable / layout / font / style refs returned as-is

def selector_color(path, depth=0):
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return None
    items = root.findall("item")
    pick = None
    for it in items:
        if not any(k.startswith(ANDROID + "state_") for k in it.attrib):
            pick = it
            break
    if pick is None and items:
        pick = items[-1]
    if pick is None:
        return None
    col = resolve_ref(pick.get(ANDROID + "color"), depth + 1)
    alpha = pick.get(ANDROID + "alpha") or pick.get(APP + "alpha")
    if col and alpha:
        try:
            a = float(resolve_ref(alpha) or 1)
            rgba = parse_color(col)
            if rgba:
                r, g, b, aa = rgba
                return "#%02x%02x%02x%02x" % (int(aa * a * 255), r, g, b)
        except ValueError:
            pass
    return col

def parse_color(v):
    if not v:
        return None
    v = v.strip()
    if not v.startswith("#"):
        return None
    h = v[1:]
    if len(h) == 3:
        h = "ff" + "".join(c * 2 for c in h)
    elif len(h) == 4:
        h = "".join(c * 2 for c in h)
    elif len(h) == 6:
        h = "ff" + h
    if len(h) != 8:
        return None
    try:
        a, r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4, 6))
    except ValueError:
        return None
    return r, g, b, a / 255

def css_color(v):
    rgba = parse_color(resolve_ref(v))
    if not rgba:
        return None
    r, g, b, a = rgba
    return f"rgba({r},{g},{b},{a:.3f})"

def dim(v):
    """Return px float, 'match', 'wrap', or None."""
    v = resolve_ref(v)
    if v is None:
        return None
    v = v.strip()
    if v in ("fill_parent", "match_parent", "-1"):
        return "match"
    if v in ("wrap_content", "-2"):
        return "wrap"
    m = re.match(r"^(-?[\d.]+)\s*(dip|dp|sp|px|pt|in|mm)?$", v)
    if not m:
        return None
    n = float(m.group(1))
    unit = m.group(2) or "px"
    return n * {"dip": 1, "dp": 1, "sp": 1, "px": 1 / 3, "pt": 1.333, "in": 160, "mm": 6.3}[unit]

# ---------------------------------------------------------------- styles
def style_attrs(name, depth=0):
    """Flatten a style (and its parents) into {attr: value}."""
    if not name or depth > 12:
        return {}
    name = name.split("/")[-1]
    el = STYLES.get(name)
    out = {}
    if el is None:
        return out
    parent = el.get("parent")
    if parent:
        out.update(style_attrs(parent, depth + 1))
    elif "." in name:
        out.update(style_attrs(name.rsplit(".", 1)[0], depth + 1))
    for item in el.findall("item"):
        out[item.get("name").replace("android:", "")] = text_of(item)
    return out

# ---------------------------------------------------------------- drawables
_drawable_cache = {}

def find_drawable(name):
    for d in DRAWABLE_DIRS:
        base = os.path.join(RES, d, name)
        for ext in (".xml", ".webp", ".png", ".jpg", ".9.png", ".gif"):
            if os.path.exists(base + ext):
                return base + ext
    return None

def data_uri(path):
    ext = path.rsplit(".", 1)[-1].lower()
    mime = {"png": "image/png", "webp": "image/webp", "jpg": "image/jpeg", "gif": "image/gif", "svg": "image/svg+xml"}[ext]
    with open(path, "rb") as fh:
        return f"data:{mime};base64," + base64.b64encode(fh.read()).decode()

def drawable(ref, tint=None):
    """Return ('img', data_uri) | ('css', {css props}) | None."""
    if not ref:
        return None
    ref = ref.strip()
    if ref.startswith("#") or "/color/" in ref or ref.startswith("@color") or ref.startswith("@android:color"):
        c = css_color(ref)
        return ("css", {"background-color": c}) if c else None
    m = re.match(r"@(?:android:)?(drawable|mipmap)/(.+)$", ref)
    if not m:
        r = resolve_ref(ref)
        if r and r != ref:
            return drawable(r, tint)
        return None
    key = (m.group(2), tint)
    if key in _drawable_cache:
        return _drawable_cache[key]
    path = find_drawable(m.group(2))
    res = None
    if path:
        if path.endswith(".xml"):
            try:
                res = xml_drawable(ET.parse(path).getroot(), tint)
            except ET.ParseError:
                res = None
        else:
            res = ("img", data_uri(path))
    _drawable_cache[key] = res
    return res

def xml_drawable(root, tint=None, depth=0):
    if depth > 6:
        return None
    tag = root.tag
    if tag == "vector":
        svg = vector_to_svg(root, tint)
        return ("img", "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()) if svg else None
    if tag == "animated-vector":
        return drawable(root.get(ANDROID + "drawable"), tint)
    if tag == "shape":
        return ("css", shape_css(root))
    if tag in ("selector", "level-list", "animated-selector"):
        items = root.findall("item")
        pick = next((it for it in items if not any(k.startswith(ANDROID + "state_") for k in it.attrib)), items[-1] if items else None)
        return item_drawable(pick, tint, depth) if pick is not None else None
    if tag == "layer-list":
        layers = [item_drawable(it, tint, depth) for it in root.findall("item")]
        layers = [l for l in layers if l]
        if not layers:
            return None
        # bottom-most shape gives background; a later bitmap/vector becomes the image
        css = next((l[1] for l in layers if l[0] == "css"), None)
        img = next((l for l in reversed(layers) if l[0] == "img"), None)
        if img and css:
            c = dict(css)
            c["background-image"] = f"url('{img[1]}')"
            c["background-repeat"] = "no-repeat"
            c["background-position"] = "center"
            c["background-size"] = "contain"
            return ("css", c)
        return img or ("css", css)
    if tag == "ripple":
        items = [it for it in root.findall("item") if it.get(ANDROID + "id") != "@android:id/mask"]
        if items:
            return item_drawable(items[0], tint, depth)
        return None
    if tag in ("inset", "scale", "clip", "rotate"):
        d = root.get(ANDROID + "drawable")
        if d:
            return drawable(d, tint)
        kids = list(root)
        return xml_drawable(kids[0], tint, depth + 1) if kids else None
    if tag == "bitmap":
        return drawable(root.get(ANDROID + "src"), tint)
    if tag == "color":
        c = css_color(root.get(ANDROID + "color"))
        return ("css", {"background-color": c}) if c else None
    return None

def item_drawable(it, tint, depth):
    d = it.get(ANDROID + "drawable")
    if d:
        return drawable(d, tint)
    c = it.get(ANDROID + "color")
    if c:
        cc = css_color(c)
        return ("css", {"background-color": cc}) if cc else None
    kids = list(it)
    return xml_drawable(kids[0], tint, depth + 1) if kids else None

def shape_css(root):
    css = {}
    shape = root.get(ANDROID + "shape", "rectangle")
    solid = root.find("solid")
    if solid is not None:
        c = css_color(solid.get(ANDROID + "color"))
        if c:
            css["background-color"] = c
    grad = root.find("gradient")
    if grad is not None:
        s = css_color(grad.get(ANDROID + "startColor")) or "transparent"
        m = css_color(grad.get(ANDROID + "centerColor"))
        e = css_color(grad.get(ANDROID + "endColor")) or "transparent"
        ang = float(resolve_ref(grad.get(ANDROID + "angle")) or 0)
        stops = ", ".join(x for x in (s, m, e) if x)
        if grad.get(ANDROID + "type") == "radial":
            css["background-image"] = f"radial-gradient(circle, {stops})"
        else:
            css["background-image"] = f"linear-gradient({90 - ang:.0f}deg, {stops})"
    stroke = root.find("stroke")
    if stroke is not None:
        w = dim(stroke.get(ANDROID + "width")) or 1
        c = css_color(stroke.get(ANDROID + "color")) or "rgba(0,0,0,.2)"
        dash = stroke.get(ANDROID + "dashWidth")
        css["border"] = f"{w if isinstance(w, float) else 1}px {'dashed' if dash else 'solid'} {c}"
    corners = root.find("corners")
    if shape == "oval":
        css["border-radius"] = "50%"
    elif corners is not None:
        r = dim(corners.get(ANDROID + "radius"))
        tl, tr, bl, br = (dim(corners.get(ANDROID + k)) for k in ("topLeftRadius", "topRightRadius", "bottomLeftRadius", "bottomRightRadius"))
        if any(isinstance(x, float) for x in (tl, tr, bl, br)):
            f = lambda x: x if isinstance(x, float) else (r if isinstance(r, float) else 0)
            css["border-radius"] = f"{f(tl)}px {f(tr)}px {f(br)}px {f(bl)}px"
        elif isinstance(r, float):
            css["border-radius"] = f"{r}px"
    return css

def vec_color(v):
    v = resolve_ref(v)
    rgba = parse_color(v)
    if not rgba:
        return None, 1
    r, g, b, a = rgba
    return f"#{r:02x}{g:02x}{b:02x}", a

AAPT = "{http://schemas.android.com/aapt}"
_grad_n = [0]

def gradient_def(g):
    """Android <gradient> element -> (svg def string, id)."""
    _grad_n[0] += 1
    gid = f"g{_grad_n[0]}"
    stops = []
    items = g.findall("item")
    if items:
        for it in items:
            c, a = vec_color(it.get(ANDROID + "color"))
            stops.append(f'<stop offset="{it.get(ANDROID + "offset", "0")}" stop-color="{c or "#000"}" stop-opacity="{a:.3f}"/>')
    else:
        for off, k in (("0", "startColor"), ("0.5", "centerColor"), ("1", "endColor")):
            if g.get(ANDROID + k):
                c, a = vec_color(g.get(ANDROID + k))
                stops.append(f'<stop offset="{off}" stop-color="{c or "#000"}" stop-opacity="{a:.3f}"/>')
    f = lambda k, d="0": g.get(ANDROID + k, d)
    if g.get(ANDROID + "type") == "radial":
        d = (f'<radialGradient id="{gid}" gradientUnits="userSpaceOnUse" cx="{f("centerX")}" cy="{f("centerY")}" '
             f'r="{f("gradientRadius", "1")}">' + "".join(stops) + "</radialGradient>")
    else:
        d = (f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{f("startX")}" y1="{f("startY")}" '
             f'x2="{f("endX")}" y2="{f("endY")}">' + "".join(stops) + "</linearGradient>")
    return d, gid

def paint(el, attr, defs):
    """Resolve a fill/stroke: plain colour, @drawable gradient file, or inline aapt:attr gradient."""
    v = el.get(ANDROID + attr)
    for aa in el.findall(AAPT + "attr"):
        if aa.get("name") == "android:" + attr:
            g = aa.find("gradient")
            if g is not None:
                d, gid = gradient_def(g)
                defs.append(d)
                return f"url(#{gid})", 1.0
    if v and v.startswith("@drawable/"):
        path = find_drawable(v.split("/", 1)[1])
        if path and path.endswith(".xml"):
            try:
                g = ET.parse(path).getroot()
            except ET.ParseError:
                g = None
            if g is not None and g.tag == "gradient":
                d, gid = gradient_def(g)
                defs.append(d)
                return f"url(#{gid})", 1.0
        return None, 1
    return vec_color(v)

def vector_to_svg(root, tint=None):
    vw = resolve_ref(root.get(ANDROID + "viewportWidth")) or "24"
    vh = resolve_ref(root.get(ANDROID + "viewportHeight")) or "24"
    w = dim(root.get(ANDROID + "width")) or float(vw)
    h = dim(root.get(ANDROID + "height")) or float(vh)
    tint_col = None
    t = tint or root.get(ANDROID + "tint")
    if t:
        tint_col = vec_color(t)
    parts, defs = [], []

    def walk(el):
        for ch in el:
            if ch.tag == "group":
                tx = float(ch.get(ANDROID + "translateX", 0) or 0)
                ty = float(ch.get(ANDROID + "translateY", 0) or 0)
                sx = float(ch.get(ANDROID + "scaleX", 1) or 1)
                sy = float(ch.get(ANDROID + "scaleY", 1) or 1)
                rot = float(ch.get(ANDROID + "rotation", 0) or 0)
                px = float(ch.get(ANDROID + "pivotX", 0) or 0)
                py = float(ch.get(ANDROID + "pivotY", 0) or 0)
                tr = f"translate({tx} {ty}) translate({px} {py}) rotate({rot}) scale({sx} {sy}) translate({-px} {-py})"
                parts.append(f'<g transform="{tr}">')
                walk(ch)
                parts.append("</g>")
            elif ch.tag == "path":
                d = ch.get(ANDROID + "pathData")
                if not d:
                    continue
                fill, fa = paint(ch, "fillColor", defs)
                stroke, sa = paint(ch, "strokeColor", defs)
                if tint_col and tint_col[0]:
                    fill = tint_col[0] if fill else None
                    stroke = tint_col[0] if stroke else None
                fa *= float(ch.get(ANDROID + "fillAlpha", 1) or 1)
                sa *= float(ch.get(ANDROID + "strokeAlpha", 1) or 1)
                sw = ch.get(ANDROID + "strokeWidth", "0")
                rule = "evenodd" if ch.get(ANDROID + "fillType") == "evenOdd" else "nonzero"
                cap = ch.get(ANDROID + "strokeLineCap", "butt")
                join = ch.get(ANDROID + "strokeLineJoin", "miter")
                parts.append(f'<path d="{html.escape(d)}" fill="{fill or "none"}" fill-opacity="{fa:.3f}" fill-rule="{rule}" '
                             f'stroke="{stroke or "none"}" stroke-opacity="{sa:.3f}" stroke-width="{sw}" stroke-linecap="{cap}" stroke-linejoin="{join}"/>')
    walk(root)
    alpha = float(root.get(ANDROID + "alpha", 1) or 1)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {vw} {vh}" opacity="{alpha}">'
            + (f"<defs>{''.join(defs)}</defs>" if defs else "") + "".join(parts) + "</svg>")

# ---------------------------------------------------------------- fonts
FONT_FILES = {}
for f in os.listdir(os.path.join(RES, "font")):
    if f.endswith(".ttf") or f.endswith(".otf"):
        FONT_FILES[f.rsplit(".", 1)[0]] = os.path.join(RES, "font", f)
USED_FONTS = set()

def font_css(ref):
    if not ref:
        return None
    name = ref.split("/")[-1]
    if name in FONT_FILES:
        USED_FONTS.add(name)
        return f"'f_{name}', Roboto, sans-serif"
    low = name.lower()
    fam = "Mulish" if "mul" in low else "Manrope" if "manrope" in low else "Roboto"
    weight_name = "bold" if "bold" in low else None
    return f"'{fam}', sans-serif"

def weight_from_font(ref):
    if not ref:
        return None
    n = ref.lower()
    for k, w in (("extra_bold", 800), ("extrabold", 800), ("semi_bold", 600), ("semibold", 600), ("bold", 700), ("medium", 500), ("light", 300)):
        if k in n:
            return w
    return None

# ---------------------------------------------------------------- layout tree
def load_layout(name):
    for d in ("layout", "layout-v26", "layout-v31"):
        p = os.path.join(RES, d, name + ".xml")
        if os.path.exists(p):
            try:
                return ET.parse(p).getroot()
            except ET.ParseError:
                return None
    return None

def short(tag):
    return tag.split(".")[-1]

CONTAINERS_LINEAR = {"LinearLayout", "LinearLayoutCompat", "TableLayout", "TableRow", "RadioGroup", "TextInputLayout"}
CONTAINERS_FRAME = {"FrameLayout", "CoordinatorLayout", "MaterialCardView", "CardView", "AppBarLayout", "CollapsingToolbarLayout",
                    "Toolbar", "SwipeRefreshLayout", "ShimmerFrameLayout", "DrawerLayout", "MotionLayout_", "FragmentContainerView"}
SCROLLS = {"ScrollView", "NestedScrollView", "HorizontalScrollView"}

def attr(el, name, ns=ANDROID):
    return el.get(ns + name)

def any_attr(el, name):
    return el.get(ANDROID + name) or el.get(APP + name)

class Ctx:
    def __init__(self):
        self.ids = {}
        self.n = 0
    def node_id(self, el):
        self.n += 1
        return f"n{self.n}"

def id_name(v):
    if not v:
        return None
    return v.split("/")[-1]

def box_css(el, st, extra_bg=True):
    """Margins, padding, background, size hints, alpha, elevation."""
    css = {}
    data = {}
    g = lambda k: el.get(ANDROID + k) if el.get(ANDROID + k) is not None else st.get(k)
    w, h = dim(g("layout_width")), dim(g("layout_height"))
    data["w"] = "match" if w == "match" else "wrap" if w in ("wrap", None) else ("zero" if w == 0 else f"{w}")
    data["h"] = "match" if h == "match" else "wrap" if h in ("wrap", None) else ("zero" if h == 0 else f"{h}")
    m_all = dim(g("layout_margin"))
    mh, mv = dim(g("layout_marginHorizontal")), dim(g("layout_marginVertical"))
    def pick(*ks, base=None):
        for k in ks:
            v = dim(g(k))
            if isinstance(v, float):
                return v
        return base if isinstance(base, float) else 0.0
    ml = pick("layout_marginStart", "layout_marginLeft", base=mh if isinstance(mh, float) else m_all)
    mr = pick("layout_marginEnd", "layout_marginRight", base=mh if isinstance(mh, float) else m_all)
    mt = pick("layout_marginTop", base=mv if isinstance(mv, float) else m_all)
    mb = pick("layout_marginBottom", base=mv if isinstance(mv, float) else m_all)
    data["m"] = f"{ml},{mt},{mr},{mb}"
    p_all = dim(g("padding"))
    ph, pv = dim(g("paddingHorizontal")), dim(g("paddingVertical"))
    def pp(*ks, base=None):
        for k in ks:
            v = dim(g(k))
            if isinstance(v, float):
                return v
        return base if isinstance(base, float) else 0.0
    pl = pp("paddingStart", "paddingLeft", base=ph if isinstance(ph, float) else p_all)
    pr = pp("paddingEnd", "paddingRight", base=ph if isinstance(ph, float) else p_all)
    pt = pp("paddingTop", base=pv if isinstance(pv, float) else p_all)
    pb = pp("paddingBottom", base=pv if isinstance(pv, float) else p_all)
    if any((pl, pr, pt, pb)):
        css["padding"] = f"{pt}px {pr}px {pb}px {pl}px"
    if extra_bg:
        bg = g("background")
        tint = el.get(ANDROID + "backgroundTint") or el.get(APP + "backgroundTint") or st.get("backgroundTint")
        if bg:
            d = drawable(bg)
            if d and d[0] == "css":
                css.update(d[1])
            elif d and d[0] == "img":
                css["background-image"] = f"url('{d[1]}')"
                css["background-size"] = "100% 100%"
        if tint:
            c = css_color(tint)
            if c:
                if "background-color" in css or not bg:
                    css["background-color"] = c
                else:
                    css["background-color"] = c
        cbg = el.get(APP + "cardBackgroundColor") or st.get("cardBackgroundColor")
        if cbg:
            c = css_color(cbg)
            if c:
                css["background-color"] = c
    for k in ("minHeight", "minWidth"):
        v = dim(g(k))
        if isinstance(v, float) and v > 0:
            css["min-height" if k == "minHeight" else "min-width"] = f"{v}px"
    a = g("alpha")
    if a:
        try:
            css["opacity"] = str(float(a))
        except ValueError:
            pass
    el_v = dim(g("elevation")) or dim(el.get(APP + "cardElevation") or st.get("cardElevation"))
    if isinstance(el_v, float) and el_v > 0:
        css["box-shadow"] = f"0 {min(el_v, 12) / 2:.1f}px {min(el_v, 12) * 1.2:.1f}px rgba(0,0,0,.14)"
    cr = dim(el.get(APP + "cardCornerRadius") or st.get("cardCornerRadius"))
    if isinstance(cr, float):
        css["border-radius"] = f"{cr}px"
        css["overflow"] = "hidden"
    lg = g("layout_gravity")
    if lg:
        data["lg"] = lg
    wt = g("layout_weight")
    if wt:
        data["weight"] = wt
    return css, data

CONSTRAINT_KEYS = ["layout_constraintLeft_toLeftOf", "layout_constraintLeft_toRightOf", "layout_constraintRight_toRightOf",
                   "layout_constraintRight_toLeftOf", "layout_constraintStart_toStartOf", "layout_constraintStart_toEndOf",
                   "layout_constraintEnd_toEndOf", "layout_constraintEnd_toStartOf", "layout_constraintTop_toTopOf",
                   "layout_constraintTop_toBottomOf", "layout_constraintBottom_toBottomOf", "layout_constraintBottom_toTopOf",
                   "layout_constraintBaseline_toBaselineOf", "layout_constraintHorizontal_bias", "layout_constraintVertical_bias",
                   "layout_constraintDimensionRatio", "layout_constraintWidth_percent", "layout_constraintHeight_percent",
                   "layout_constraintGuide_percent", "layout_constraintGuide_begin", "layout_constraintGuide_end",
                   "layout_constraintCircle"]
RELATIVE_KEYS = ["layout_toEndOf", "layout_toRightOf", "layout_toStartOf", "layout_toLeftOf", "layout_below", "layout_above",
                 "layout_alignParentStart", "layout_alignParentLeft", "layout_alignParentEnd", "layout_alignParentRight",
                 "layout_alignParentTop", "layout_alignParentBottom", "layout_centerInParent", "layout_centerHorizontal",
                 "layout_centerVertical", "layout_alignTop", "layout_alignBottom", "layout_alignStart", "layout_alignLeft",
                 "layout_alignEnd", "layout_alignRight", "layout_alignBaseline"]

def layout_data(el):
    d = {}
    for k in CONSTRAINT_KEYS:
        v = el.get(APP + k)
        if v is not None:
            d[k] = id_name(v) if v.startswith("@") else v
    for k in RELATIVE_KEYS:
        v = el.get(ANDROID + k)
        if v is not None:
            d[k] = id_name(v) if v.startswith("@") else v
    gm = {}
    for k in ("layout_goneMarginTop", "layout_goneMarginStart", "layout_goneMarginBottom", "layout_goneMarginEnd"):
        v = el.get(APP + k)
        if v:
            gm[k] = dim(v)
    orient = el.get(ANDROID + "orientation")
    if short(el.tag) == "Guideline":
        d["guide"] = orient or "horizontal"
    return d

def esc(s):
    return html.escape(s or "", quote=True)

def attrs_str(d):
    return " ".join(f'data-{k.replace("layout_", "").replace("_", "-").lower()}="{esc(str(v))}"' for k, v in d.items() if v is not None)

def style_str(css):
    return ";".join(f"{k}:{v}" for k, v in css.items() if v)

def text_props(el, st, default_size=14.0, default_color="rgba(0,0,0,.87)"):
    g = lambda k: el.get(ANDROID + k) or el.get(APP + k) or st.get(k)
    ta = g("textAppearance")
    if ta and ta.startswith("@style"):
        tas = style_attrs(ta)
        st = {**tas, **st}
        g = lambda k: el.get(ANDROID + k) or el.get(APP + k) or st.get(k)
    css = {}
    size = dim(g("textSize"))
    css["font-size"] = f"{size if isinstance(size, float) else default_size}px"
    col = css_color(g("textColor")) or default_color
    css["color"] = col
    ff = g("fontFamily")
    fam = font_css(ff) if ff and ff.startswith("@font") else None
    if fam:
        css["font-family"] = fam
    elif ff and "medium" in ff:
        css["font-weight"] = "500"
    w = weight_from_font(ff)
    cls_low = short(el.tag).lower()
    if not w and not ff:
        for k, ww in (("robotobold", 700), ("robotomedium", 500), ("robotolight", 300), ("robotoregular", 400)):
            if k in cls_low:
                w = ww
    tfw = g("textFontWeight")
    if tfw:
        try:
            w = int(float(tfw))
        except ValueError:
            pass
    ts = g("textStyle") or ""
    if "bold" in ts and not w:
        w = 700
    if w:
        css["font-weight"] = str(w)
    if "italic" in ts:
        css["font-style"] = "italic"
    grav = g("gravity") or ""
    if "center_horizontal" in grav or grav.strip() == "center" or "center|" in grav or "|center" in grav and "vertical" not in grav:
        css["text-align"] = "center"
    elif "end" in grav or "right" in grav:
        css["text-align"] = "right"
    ls = g("letterSpacing")
    if ls:
        try:
            css["letter-spacing"] = f"{float(ls)}em"
        except ValueError:
            pass
    lsm = g("lineSpacingMultiplier")
    if lsm:
        try:
            css["line-height"] = f"{float(lsm) * 1.17:.2f}"
        except ValueError:
            pass
    caps = g("textAllCaps")
    if caps == "true":
        css["text-transform"] = "uppercase"
    ml = g("maxLines") or ("1" if g("singleLine") == "true" else None)
    if ml:
        try:
            n = int(float(resolve_ref(ml) or ml))
            if n == 1:
                css.update({"white-space": "nowrap", "overflow": "hidden", "text-overflow": "ellipsis"})
            else:
                css.update({"display": "-webkit-box", "-webkit-line-clamp": str(n), "-webkit-box-orient": "vertical", "overflow": "hidden"})
        except ValueError:
            pass
    return css, grav

FMT_RE = re.compile(r"%(\d+\$)?[-#+ 0,(]*\d*(\.\d+)?[sdfx]")

def clean_text(r):
    r = r.replace("\\n", "\n").replace("\\'", "'").replace('\\"', '"')
    return FMT_RE.sub("•••", r)

def get_text(el, st, kind="text"):
    for ns, k in ((ANDROID, "text"), (TOOLS, "text")):
        v = el.get(ns + k)
        if v:
            r = resolve_ref(v) if v.startswith("@") else v
            if r:
                return clean_text(r)
    v = st.get("text")
    if v:
        return resolve_ref(v) if v.startswith("@") else v
    return ""

def compound_drawables(el):
    out = {}
    for side, keys in (("start", ("drawableStart", "drawableLeft")), ("end", ("drawableEnd", "drawableRight")),
                       ("top", ("drawableTop",)), ("bottom", ("drawableBottom",))):
        for k in keys:
            v = el.get(ANDROID + k) or el.get(APP + k.replace("drawable", "drawable") + "Compat")
            if v:
                tint = el.get(ANDROID + "drawableTint") or el.get(APP + "drawableTint")
                d = drawable(v, tint)
                if d and d[0] == "img":
                    out[side] = d[1]
                break
    return out

def render(el, ctx, depth=0, parent_kind=None, override=None):
    """Return HTML for element el."""
    if depth > MAX_DEPTH:
        return ""
    tag = el.tag
    s = short(tag)
    if tag in ("layout",):
        kids = [k for k in el if k.tag not in ("data",)]
        return "".join(render(k, ctx, depth, parent_kind, override) for k in kids)
    if s in ("requestFocus", "data", "ViewStub", "Space_", "tag"):
        return ""
    if s == "include":
        lname = (el.get("layout") or "").split("/")[-1]
        sub = load_layout(lname)
        if sub is None:
            return f'<div class="ph" data-w="match" data-h="wrap">include {esc(lname)}</div>'
        if el.get(ANDROID + "visibility") == "gone":
            return ""
        if OVERLAY_RE.search(lname) or OVERLAY_RE.search(id_name(el.get(ANDROID + "id")) or ""):
            return ""
        ov = {k: v for k, v in el.attrib.items() if k != "layout"}
        if sub.tag == "merge":
            return "".join(render(k, ctx, depth + 1, parent_kind) for k in sub)
        if sub.tag == "layout":
            kids = [k for k in sub if k.tag != "data"]
            if not kids:
                return ""
            sub = kids[0]
        return render(sub, ctx, depth + 1, parent_kind, override=ov)
    if s == "merge":
        return "".join(render(k, ctx, depth + 1, parent_kind) for k in el)

    if override:
        el = ET.Element(el.tag, {**el.attrib, **{k: v for k, v in override.items() if k.startswith(ANDROID + "layout_") or k in (ANDROID + "id", ANDROID + "visibility")} | {k: v for k, v in override.items() if k.startswith(APP + "layout_")}})
        el.extend(list(ET.fromstring(ET.tostring(ET.Element("x"))) ) if False else [])
        src = override.get("__children__")
    vis = el.get(ANDROID + "visibility")
    st = {}
    style_ref = el.get("style")
    if style_ref:
        st = style_attrs(style_ref)
    css, data = box_css(el, st)
    data.update(layout_data(el))
    nid = id_name(el.get(ANDROID + "id"))
    cls = ["v"]
    if vis == "gone":
        cls.append("gone")
    elif vis == "invisible":
        css["visibility"] = "hidden"
    kind = "leaf"
    inner = ""
    children = list(el) if not override else list(el)
    # re-attach children dropped by override copy
    if override is not None:
        children = list(override.get("__src__", []))

    is_container = len(children) > 0 or s.endswith("Layout") or s in CONTAINERS_FRAME or s in SCROLLS
    lname = s
    if s in ("ConstraintLayout", "MotionLayout") or s.endswith("ConstraintLayout"):
        kind = "constraint"
    elif s in ("RelativeLayout", "PercentRelativeLayout"):
        kind = "relative"
    elif s in CONTAINERS_LINEAR or (el.get(ANDROID + "orientation") and is_container and s not in ("Guideline",) and "Layout" in s):
        kind = "linear"
        ori = el.get(ANDROID + "orientation") or st.get("orientation") or ("vertical" if s in ("TextInputLayout", "TableLayout", "RadioGroup") else "horizontal")
        data["ori"] = "v" if ori == "vertical" else "h"
        grav = el.get(ANDROID + "gravity") or ""
        data["gravity"] = grav
    elif s in SCROLLS:
        kind = "scroll"
        if s == "HorizontalScrollView":
            data["ori"] = "h"
    elif s in CONTAINERS_FRAME or (is_container and children and s.endswith("Layout")) or (children and s not in ("Guideline",)):
        kind = "frame"
    html_children = ""
    if kind != "leaf":
        html_children = "".join(render(k, ctx, depth + 1, kind) for k in children)
        if s == "TextInputLayout":
            hint = el.get(ANDROID + "hint") or el.get(APP + "hint")
            if hint:
                html_children = f'<div class="til-hint" data-w="wrap" data-h="wrap">{esc(resolve_ref(hint))}</div>' + html_children
        inner = html_children
    else:
        inner, extra_css, kind = leaf(el, s, st, css, data)
        css.update(extra_css)
    if s == "Guideline":
        kind = "guide"
        cls.append("gone")
    data["kind"] = kind
    if nid:
        data["id"] = nid
    data["cls"] = s
    return f'<div class="{" ".join(cls)} k-{kind}" {attrs_str(data)} style="{esc(style_str(css))}">{inner}</div>'

def leaf(el, s, st, css, data):
    g = lambda k: el.get(ANDROID + k) or el.get(APP + k) or st.get(k)
    low = s.lower()
    extra = {}
    if s == "View" or s == "Space" or s == "Divider" or s == "MaterialDivider":
        return "", extra, "leaf"
    if "imageview" in low or s in ("ImageView", "ImageButton", "AppCompatImageButton", "CircleImageView", "ShapeableImageView", "RoundedImageView") or "image" in low and "text" not in low:
        src = g("src") or g("srcCompat") or el.get(TOOLS + "src") or el.get(TOOLS + "srcCompat")
        tint = g("tint") or el.get(APP + "tint")
        d = drawable(src, tint) if src else None
        fit = {"centerCrop": "cover", "fitXY": "fill", "center": "none", "fitCenter": "contain", "centerInside": "contain"}.get(g("scaleType") or "", "contain")
        if d and d[0] == "img":
            return f'<img src="{d[1]}" alt="" style="object-fit:{fit}">', extra, "img"
        if d and d[0] == "css":
            extra.update(d[1])
            return "", extra, "leaf"
        return "", extra, "img"
    if "lottie" in low:
        return '<span class="ph-in">animation</span>', {"border": "1px dashed #b8bfd6", "border-radius": "50%"}, "ph"
    if "webview" in low:
        return '<span class="ph-in">web content (loaded at runtime)</span>', {"background": "#f1f3f8"}, "ph"
    if s in ("RecyclerView", "ListView", "GridView", "ViewPager", "ViewPager2", "ExpandableListView", "ShimmerRecyclerView"):
        li = el.get(TOOLS + "listitem")
        if li:
            sub = load_layout(li.split("/")[-1])
            if sub is not None:
                c = Ctx()
                items = "".join(render(sub, c, 1, "linear") for _ in range(3))
                return items, {}, "list"
        return '<span class="ph-in">list · filled at runtime</span>', {"background": "repeating-linear-gradient(0deg,#f4f5f9 0 44px,#fff 44px 52px)"}, "ph"
    if s in ("TabLayout",):
        return '<span class="ph-in">tabs</span>', {"border-bottom": "1px solid #e3e6ef"}, "ph"
    if s in ("ProgressBar", "CircularProgressIndicator", "LinearProgressIndicator", "ContentLoadingProgressBar"):
        if "horizontal" in (el.get("style") or "").lower() or s == "LinearProgressIndicator":
            return "", {"background": "#e3e6ef", "height": "4px", "border-radius": "2px"}, "leaf"
        return '<span class="spin"></span>', {}, "ph"
    if "otp" in low or "pinview" in low or "pinentry" in low:
        n = int(float(el.get(APP + "itemCount") or el.get(APP + "pinLength") or 6))
        ih = dim(el.get(APP + "itemHeight")) or 48
        iw = dim(el.get(APP + "itemWidth")) or ih
        rad = dim(el.get(APP + "itemRadius")) or 8
        sp = dim(el.get(APP + "itemSpacing")) or 8
        lc = css_color(el.get(APP + "lineColor")) or "rgba(0,0,0,.25)"
        boxes = "".join(f'<i style="width:{iw}px;height:{ih}px;border-radius:{rad}px;border:1px solid {lc}"></i>' for _ in range(n))
        return f'<span class="otp" style="gap:{sp}px">{boxes}</span>', {}, "otp"
    if "checkbox" in low or "radiobutton" in low or "switch" in low:
        tcss, grav = text_props(el, st)
        txt = get_text(el, st)
        box = '<i class="cb"></i>' if "switch" not in low else '<i class="sw"></i>'
        box = '<i class="rb"></i>' if "radio" in low else box
        return f'<span class="chk">{box}<span style="{esc(style_str(tcss))}">{esc(txt)}</span></span>', {}, "text"
    is_button = "button" in low and "image" not in low
    is_edit = "edittext" in low or "autocomplete" in low or s in ("TextInputEditText",)
    if is_button or is_edit or "textview" in low or "text" in low or "chip" in low or s in ("TextView", "Chip", "CheckedTextView"):
        default_color = "rgba(0,0,0,.87)"
        tcss, grav = text_props(el, st, default_color=default_color)
        txt = get_text(el, st)
        hint = el.get(ANDROID + "hint") or el.get(TOOLS + "hint")
        if is_edit and not txt and hint:
            txt = resolve_ref(hint) if hint.startswith("@") else hint
            hc = css_color(el.get(ANDROID + "textColorHint")) or "rgba(0,0,0,.38)"
            tcss["color"] = hc
        if is_button:
            if el.get(ANDROID + "textAllCaps") != "false" and st.get("textAllCaps") != "false" and "Material" not in s and s in ("Button",):
                tcss["text-transform"] = "uppercase"
            if "text-align" not in tcss:
                tcss["text-align"] = "center"
            if not el.get(ANDROID + "background") and not st.get("background") and "background-color" not in css:
                tint = css_color(el.get(ANDROID + "backgroundTint") or el.get(APP + "backgroundTint"))
                extra["background-color"] = tint or css_color(THEME["colorPrimary"])
                extra.setdefault("border-radius", "4px")
                if "color" not in tcss or el.get(ANDROID + "textColor") is None:
                    tcss["color"] = "#fff"
            if "padding" not in css:
                extra["padding"] = "8px 16px"
        if is_edit and not el.get(ANDROID + "background") and "background-color" not in css:
            extra["border-bottom"] = "1px solid rgba(0,0,0,.35)"
            if "padding" not in css:
                extra["padding"] = "8px 4px"
        cds = compound_drawables(el)
        pad = dim(el.get(ANDROID + "drawablePadding")) or 6
        def img(u, side):
            return f'<img class="cd cd-{side}" src="{u}" alt="" style="margin-{"right" if side == "start" else "left" if side == "end" else "bottom" if side == "top" else "top"}:{pad}px">'
        body = esc(txt).replace("\n", "<br>")
        if "<" in txt and ">" in txt and re.search(r"</?(b|font|br|u|i|strong)\b", txt, re.I):
            body = re.sub(r"<(?!/?(b|br|u|i|strong)\b)[^>]+>", "", txt, flags=re.I).replace("\n", "<br>")
        center_v = "center" in grav and "horizontal" not in grav or "center_vertical" in grav
        flex_dir = "column" if ("top" in cds or "bottom" in cds) else "row"
        jc = "center" if tcss.get("text-align") == "center" else "flex-end" if tcss.get("text-align") == "right" else "flex-start"
        content = (img(cds["top"], "top") if "top" in cds else "") + (img(cds["start"], "start") if "start" in cds else "") + \
                  f'<span class="t" style="{esc(style_str(tcss))}">{body}</span>' + \
                  (img(cds["end"], "end") if "end" in cds else "") + (img(cds["bottom"], "bottom") if "bottom" in cds else "")
        extra.update({"display": "flex", "flex-direction": flex_dir, "align-items": "center" if (center_v or is_button or flex_dir == "row") else "flex-start",
                      "justify-content": jc if flex_dir == "row" else "center"})
        if tcss.get("font-size"):
            extra["font-size"] = tcss["font-size"]
        return content, extra, "text"
    if ("input" in low and "layout" not in low) or "floatinglabel" in low:
        lab = el.get(APP + "dsInputLabel") or el.get(APP + "inputLabel") or el.get(ANDROID + "hint") or el.get(APP + "hint")
        hint = el.get(APP + "dsInputHint") or el.get(APP + "inputHint") or el.get(ANDROID + "hint")
        lab = clean_text(resolve_ref(lab) or "") if lab else ""
        hint = clean_text(resolve_ref(hint) or "") if hint else ""
        cds = compound_drawables(el)
        icon = f'<img class="cd" src="{cds["start"]}" alt="">' if "start" in cds else ""
        body = (f'<span class="fl-lab">{esc(lab)}</span>' if lab and lab != hint else "") + f'<span class="fl-row">{icon}<span class="fl-hint">{esc(hint or lab)}</span></span>'
        return body, {"border": "1px solid #c9cedb", "border-radius": "10px", "padding": "8px 14px", "background": "#fff", "display": "flex", "flex-direction": "column", "justify-content": "center", "min-height": "56px"}, "text"
    # unknown custom view
    return f'<span class="ph-in">{esc(s)}</span>', {"border": "1px dashed #c3c8da", "border-radius": "6px"}, "ph"

# patch render to keep children of included roots
_orig_render = render
def render(el, ctx, depth=0, parent_kind=None, override=None):  # noqa: F811
    if override is not None:
        override = dict(override)
        override["__src__"] = list(el)
    return _orig_render(el, ctx, depth, parent_kind, override)

# ---------------------------------------------------------------- page
PAGE_CSS = """
*{box-sizing:border-box;margin:0}
html,body{background:#e9ebf1}
#screen{width:%dpx;min-height:%dpx;background:#fff;position:relative;overflow:hidden;font-family:Roboto,'f_roboto_regular',sans-serif;font-size:14px;line-height:1.25;color:rgba(0,0,0,.87)}
.v{position:relative;min-width:0}
.gone{display:none!important}
.k-linear{display:flex}
.k-frame{display:grid}
.k-frame>.v{grid-area:1/1}
.k-scroll{display:flex;flex-direction:column}
.k-img>img{width:100%%;height:100%%;display:block}
.k-img{display:block}
.k-list{display:flex;flex-direction:column}
.t{min-width:0;overflow-wrap:anywhere}
.cd{flex:none;max-width:28px;max-height:28px}
.ph{display:flex;align-items:center;justify-content:center;min-height:24px}
.ph-in{font:500 10px/1.2 monospace;color:#8a91a8;padding:4px;text-align:center}
.otp{display:flex;justify-content:center;width:100%%}
.otp i{display:block;flex:0 1 auto;min-width:0;background:#fff}
.chk{display:flex;align-items:center;gap:8px}
.cb{width:18px;height:18px;border:2px solid #6b7290;border-radius:3px;flex:none}
.rb{width:18px;height:18px;border:2px solid #6b7290;border-radius:50%%;flex:none}
.sw{width:34px;height:14px;border-radius:7px;background:#c6cad6;flex:none}
.spin{width:36px;height:36px;border-radius:50%%;border:4px solid #dfe3f0;border-top-color:#293897;display:block}
.fl-lab{font-size:11px;color:#6b7290;margin-bottom:2px}.fl-row{display:flex;align-items:center;gap:8px}.fl-hint{font-size:15px;color:#9aa0b4}
.til-hint{font-size:12px;color:rgba(0,0,0,.55);padding:0 4px 2px}
"""

def font_faces():
    out = []
    for name in sorted(USED_FONTS | {"roboto_regular", "roboto_medium", "roboto_bold"}):
        if name in FONT_FILES:
            out.append(f"@font-face{{font-family:'f_{name}';src:url('fonts/{name}.ttf')}}")
    # map Roboto family weights to bundled files
    out.append("@font-face{font-family:Roboto;src:url('fonts/roboto_regular.ttf');font-weight:400}")
    out.append("@font-face{font-family:Roboto;src:url('fonts/roboto_medium.ttf');font-weight:500}")
    out.append("@font-face{font-family:Roboto;src:url('fonts/roboto_bold.ttf');font-weight:700 900}")
    out.append("@font-face{font-family:Manrope;src:url('fonts/manrope_regular.ttf');font-weight:400}")
    out.append("@font-face{font-family:Manrope;src:url('fonts/manrope_medium.ttf');font-weight:500}")
    out.append("@font-face{font-family:Manrope;src:url('fonts/manrope_semi_bold.ttf');font-weight:600}")
    out.append("@font-face{font-family:Manrope;src:url('fonts/manrope_bold.ttf');font-weight:700}")
    out.append("@font-face{font-family:Manrope;src:url('fonts/manrope_extra_bold.ttf');font-weight:800 900}")
    return "\n".join(out)

def main():
    os.makedirs(OUT, exist_ok=True)
    fdir = os.path.join(OUT, "fonts")
    os.makedirs(fdir, exist_ok=True)
    for name, p in FONT_FILES.items():
        dst = os.path.join(fdir, name + ".ttf")
        if not os.path.exists(dst):
            with open(p, "rb") as a, open(dst, "wb") as b:
                b.write(a.read())
    ok = 0
    for lname in LAYOUTS:
        root = load_layout(lname)
        if root is None:
            print(f"MISSING {lname}")
            continue
        if root.tag == "layout":
            kids = [k for k in root if k.tag != "data"]
            root = kids[0] if kids else root
        try:
            body = render(root, Ctx(), 0, "screen")
        except Exception as e:  # keep the batch going
            print(f"FAIL {lname}: {e!r}")
            continue
        page = (f"<!doctype html><html><head><meta charset='utf-8'><title>{esc(lname)}</title><style>{font_faces()}{PAGE_CSS % (SCREEN_W, SCREEN_H)}</style></head>"
                f"<body><div id='screen' data-kind='frame' class='k-frame' data-w='{SCREEN_W}' data-h='match'>{body}</div>"
                f"<script src='solver.js'></script></body></html>")
        with open(os.path.join(OUT, lname + ".html"), "w") as fh:
            fh.write(page)
        ok += 1
    print(f"rendered {ok}/{len(LAYOUTS)}")

if __name__ == "__main__":
    main()
