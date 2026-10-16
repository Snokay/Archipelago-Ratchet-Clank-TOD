"""
Construit le pack PopTracker de Tools of Destruction Archipelago (2026-10-16, demande du développeur).

  python tools/make_poptracker.py
Sortie : dist/poptracker/RaC_ToD_AP/ et dist/RaC_ToD_AP_poptracker_<version>.zip (dossier packs de PopTracker).

Tout vient de l'apworld (apworld/rac_tod/data.py) : numéros AP, checks, logique (même règle que create_regions de
__init__.py : planète reçue + besoins du check + Clank pour explorer ; Léviathan k = k planètes ; niveau k = k / 4
planètes ; Fastoon final = toutes les planètes + gadgets + Clank x2). Aucune image du jeu : carte de la galaxie et
icônes générées (Pillow). Option lue dans le slot data : player_levels (checks de niveau visibles).
"""
import hashlib
import importlib.util
import json
import math
import random
import re
import shutil
import sys
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import pt_art  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "apworld" / "rac_tod"
OUT = ROOT / "dist" / "poptracker" / "RaC_ToD_AP"
FONT = "C:/Windows/Fonts/trebucbd.ttf"
MAP_W, MAP_H = 1400, 1000
# Disposition du pack de R&C3 (SomeLazyGamer) ; style du logo et de l'emblème du développeur : métal sombre riveté,
# lumières orange et bleues, motif hexagonal (dessins dans pt_art.py).
BG_IN, BG_OUT, LINE, DISC, TEXT = (22, 30, 44), (8, 10, 16), (255, 140, 30), (120, 210, 250), (255, 240, 220)
BLUE, ORANGE = (40, 170, 255), (255, 130, 20)
LOGO = ROOT / "assets" / "logo.png"


def load_data():
    spec = importlib.util.spec_from_file_location("tod_data", SRC / "data.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["tod_data"] = mod
    spec.loader.exec_module(mod)
    return mod


D = load_data()
PLANETS, COMBATS, ITEMS, LOCATIONS = D.PLANETS, D.SPACE_COMBATS, D.ITEMS, D.LOCATIONS
FINAL, GALAXY = D.FINAL_REGION, "Galaxy"
# Cartes de niveau du jeu (wiki) par région ; Rykan V et Sargasso n'en ont pas (galaxie seulement).
LEVEL_MAPS = {
    "Cobalia": ["Gelatonium_plant"], "Kortog": ["Stratus_City"], "Fastoon": ["Lombax_ruins_1", "Lombax_ruins_2"],
    "Mukow": ["Imperial_Fight_Festival"], "Apogee Space Station": ["Apogee_Space_Station", "Nundac_Asteroid_Ring"],
    "Ardolis": ["Pirate_base"], "Kreeli Comet": ["Kreeli_Comet"], "Viceron": ["Zordoom_Prison"],
    "Jasindu": ["Kerchu_City_1", "Kerchu_City_2"], "Ublik Passage": ["Slags_fleet"], "Reepor": ["Cragmite_ruins"],
    "Igliak": ["Meridian_City"], FINAL: ["Lombax_ruins_2"],
}
GROUPS = [("mission", "Missions"), ("gold_bolt", "Gold Bolts"), ("skill", "Skill Points"), ("holoplan", "Holo-Plan"),
          ("statue", "Tachyon Statues"), ("vendor_weapon", "Vendors"), ("vendor_armor", "Vendors"), ("arrival", "Arrival"),
          ("level", "Ratchet Levels"), ("leviathan", "Leviathans"), ("weapon_level", "Weapon Levels")]
WEAPON_LEVELS = "Weapon Levels"  # région du tracker : une sous-location par arme (V2 à V5)
GADGETS = [n for n, d in ITEMS.items() if d.kind == "gadget"]


def code(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def color_of(name: str) -> tuple:
    h = hashlib.md5(name.encode()).digest()
    return (80 + h[0] % 150, 80 + h[1] % 150, 80 + h[2] % 150)


def font(size):
    return ImageFont.truetype(FONT, size)


# --- icônes ------------------------------------------------------------------------------------------
def sphere(size, rgb):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = img.load()
    r = size / 2 - 2
    for y in range(size):
        for x in range(size):
            dx, dy = (x - size / 2 + 0.5) / r, (y - size / 2 + 0.5) / r
            d2 = dx * dx + dy * dy
            if d2 <= 1:
                z = math.sqrt(1 - d2)
                light = max(0.0, (-dx * 0.5 - dy * 0.6 + z * 0.65))
                k = 0.25 + 0.95 * light
                px[x, y] = tuple(min(255, int(c * k)) for c in rgb) + (255,)
    return img


def badge(name, rgb, size=64):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((2, 2, size - 3, size - 3), 10, fill=BG_OUT + (255,), outline=rgb + (255,), width=3)
    d.rounded_rectangle((6, 6, size - 7, size - 7), 7, outline=rgb + (90,), width=1)
    words = [w for w in re.split(r"[\s\-.]+", name.replace("Unlock", "")) if w]
    initials = "".join(w[0] for w in words[:3]).upper()
    f = font(26 if len(initials) < 3 else 20)
    w, h = d.textbbox((0, 0), initials, font=f)[2:]
    d.text(((size - w) / 2, (size - h) / 2 - 3), initials, font=f, fill=(255, 255, 255, 255))
    return img


def off(img):
    g = img.convert("LA").convert("RGBA")
    a = img.getchannel("A").point(lambda v: v * 0.45)
    g.putalpha(a)
    return g


ICON_PX = 128  # icônes générées en 128 px (PopTracker les réduit : plus nettes)


def item_icon(name, kind):
    if kind == "planet":
        return pt_art.planet_icon(name, ICON_PX)
    return pt_art.item_icon(name, kind, ICON_PX)


# --- carte de la galaxie ----------------------------------------------------------------------------------
ORBITS = [0.30, 0.55, 0.80]   # rayons relatifs des 3 orbites
CENTER = (MAP_W * 0.46, MAP_H * 0.52)
TILT = -0.45


def orbit_point(k, ang):
    rx, ry = ORBITS[k] * MAP_W * 0.55, ORBITS[k] * MAP_H * 0.42
    x, y = math.cos(ang) * rx, math.sin(ang) * ry
    c, s_ = math.cos(TILT), math.sin(TILT)
    return int(CENTER[0] + x * c - y * s_), int(CENTER[1] + x * s_ + y * c)


def galaxy_positions():
    """Corps célestes dans l'ordre de l'histoire, sur 3 orbites (début au centre, fin dehors)."""
    bodies = [(p.level, n) for n, p in PLANETS.items()] + [(c.level, n) for n, c in COMBATS.items()] + [(18, FINAL)]
    bodies.sort()
    per = [5, 6, len(bodies) - 11]
    pos, i = {}, 0
    for k, count in enumerate(per):
        for j in range(count):
            ang = 2.4 + k * 0.7 + j * 2 * math.pi / count
            pos[bodies[i][1]] = orbit_point(k, ang)
            i += 1
    pos[GALAXY] = (MAP_W - 150, 80)
    return pos


def body_size(n):
    return 34 if n in COMBATS else 74 if n == FINAL else 54


def label_lines(n):
    for a, b in ((" (Final)", "|(Final)"), (" Asteroid Belt", "|Asteroid Belt"), (" Star Cluster", "|Star Cluster"),
                 (" Black Hole", "|Black Hole"), (" Space Station", "|Station")):
        n = n.replace(a, b)
    return n.split("|")


def plate(d, x, y, lines, f, accent=ORANGE):
    """Plaque de nom (métal sombre, bord orange, voyant bleu), centrée en x, bas en y."""
    w = max(d.textbbox((0, 0), l, font=f)[2] for l in lines) + 26
    h = 26 * len(lines) + 10
    x0, y0 = x - w / 2, y - h
    d.rounded_rectangle((x0, y0, x0 + w, y), 6, fill=(20, 22, 28, 235), outline=accent + (255,), width=2)
    d.line((x0 + 8, y - 3, x0 + w - 8, y - 3), fill=BLUE + (200,), width=2)
    ty = y0 + 4
    for l in lines:
        lw = d.textbbox((0, 0), l, font=f)[2]
        d.text((x - lw / 2, ty), l, font=f, fill=TEXT)
        ty += 26


PANEL_W, SLOT_W, SLOT_H, COLS = 560, 89, 70, 6
PANEL_ICON, PIN = 50, 20  # icône des cases du panneau ; point de check (petit, à droite de l'icône)
PANEL_GROUPS = ["Gold Bolts", "Holo-Plan", "Skill Points", "Weapon Levels"]


def panel_slots():
    """(groupe, région) -> centre de la case du panneau ; régions dans l'ordre de l'histoire."""
    order = sorted({d.region for d in LOCATIONS.values() if d.region not in ("Menu",)},
                   key=lambda n: PLANETS[n].level if n in PLANETS else COMBATS[n].level if n in COMBATS else 18)
    slots, heads, y = {}, [], 10
    for group in PANEL_GROUPS:
        kinds = {k for k, g in GROUPS if g == group}
        if group == WEAPON_LEVELS:  # une case par arme
            regions = [n for n, d in ITEMS.items() if d.kind == "weapon"]
        else:
            regions = [r for r in order if any(d.region == r and d.kind in kinds for d in LOCATIONS.values())]
        heads.append((group, y))
        y += 52
        for i, r in enumerate(regions):
            slots[(group, r)] = (MAP_W + 20 + (i % COLS) * SLOT_W + SLOT_W // 2, y + (i // COLS) * SLOT_H + 26)
        y += ((len(regions) + COLS - 1) // COLS) * SLOT_H + 8
    return slots, heads


def draw_panel(img, slots, heads):
    d = ImageDraw.Draw(img, "RGBA")
    x0 = MAP_W
    d.rectangle((x0, 0, x0 + PANEL_W, MAP_H), fill=(16, 18, 24, 255))
    d.line((x0 + 2, 0, x0 + 2, MAP_H), fill=ORANGE + (255,), width=4)
    d.line((x0 + 8, 0, x0 + 8, MAP_H), fill=BLUE + (160,), width=2)
    for title, y in heads:
        d.rounded_rectangle((x0 + 18, y, x0 + PANEL_W - 14, y + 44), 6, fill=(30, 33, 40, 255), outline=ORANGE + (255,), width=2)
        d.line((x0 + 28, y + 40, x0 + PANEL_W - 24, y + 40), fill=BLUE + (220,), width=2)
        f = font(26)
        w = d.textbbox((0, 0), title, font=f)[2]
        d.text((x0 + 18 + (PANEL_W - 32 - w) / 2, y + 7), title, font=f, fill=(255, 170, 60))
    for (group, region), (x, y) in slots.items():
        h = PANEL_ICON // 2
        if group == WEAPON_LEVELS:
            ic = pt_art.item_icon(region, "weapon", PANEL_ICON)
            img.paste(ic, (x - h - 10, y - h - 6), ic)
            continue
        pl = pt_art.planet(region, PANEL_ICON)
        img.paste(pl, (x - h - 10, y - h - 6), pl)
        d = ImageDraw.Draw(img, "RGBA")
        name = region.replace(" Space Station", "").replace(" Passage", "").replace(" Asteroid Belt", "").replace(
            " Star Cluster", "").replace(" Black Hole", "").replace(" Comet", "").replace("Fastoon (Final)", "Final")
        f = font(15)
        w = d.textbbox((0, 0), name, font=f)[2]
        d.text((x - w / 2, y + 20), name, font=f, fill=TEXT)


def draw_map(pos):
    rnd = random.Random(7)
    img = Image.new("RGB", (MAP_W, MAP_H), BG_OUT)
    grad = Image.new("L", (MAP_W, MAP_H), 0)
    gd = ImageDraw.Draw(grad)
    for r in range(900, 0, -10):
        gd.ellipse((CENTER[0] - r * 1.3, CENTER[1] - r, CENTER[0] + r * 1.3, CENTER[1] + r), fill=int(255 * (1 - r / 900)))
    img = Image.composite(Image.new("RGB", (MAP_W, MAP_H), BG_IN), img, grad.filter(ImageFilter.GaussianBlur(40)))
    d = ImageDraw.Draw(img, "RGBA")
    hr = 26  # motif hexagonal du fond
    for row in range(-1, int(MAP_H / (hr * 1.5)) + 2):
        for col in range(-1, int(MAP_W / (hr * 1.75)) + 2):
            cx, cy = col * hr * 1.75 + (row % 2) * hr * 0.87, row * hr * 1.5
            d.polygon([(cx + hr * math.cos(math.pi / 6 + k * math.pi / 3), cy + hr * math.sin(math.pi / 6 + k * math.pi / 3))
                       for k in range(6)], outline=(80, 110, 150, 22))
    for _ in range(400):
        d.point((rnd.randint(0, MAP_W - 1), rnd.randint(0, MAP_H - 1)), fill=(220, 230, 255, rnd.randint(60, 200)))
    glow_layer = Image.new("RGBA", (MAP_W, MAP_H), (0, 0, 0, 0))
    gl = ImageDraw.Draw(glow_layer)
    for k in range(len(ORBITS)):  # orbites : rail métal + lumière orange (intérieur) / bleue (extérieur)
        pts = [orbit_point(k, t / 240 * 2 * math.pi) for t in range(241)]
        col = ORANGE if k != 1 else BLUE
        gl.line(pts, fill=col + (200,), width=10)
        d.line(pts, fill=(70, 74, 82, 255), width=7)
        d.line(pts, fill=(140, 146, 158, 255), width=2)
        for t in range(0, 240, 20):
            x, y = orbit_point(k, t / 240 * 2 * math.pi)
            d.ellipse((x - 4, y - 4, x + 4, y + 4), fill=col + (255,))
    img = Image.alpha_composite(img.convert("RGBA"), glow_layer.filter(ImageFilter.GaussianBlur(9)))
    img = Image.alpha_composite(img, Image.new("RGBA", img.size, (0, 0, 0, 0)))
    sun = Image.new("RGBA", (360, 360), (0, 0, 0, 0))
    ImageDraw.Draw(sun).ellipse((120, 120, 240, 240), fill=(255, 170, 60, 255))
    sun = sun.filter(ImageFilter.GaussianBlur(34))
    img.paste(sun, (int(CENTER[0] - 180), int(CENTER[1] - 180)), sun)
    d = ImageDraw.Draw(img, "RGBA")
    # redessiner les rails par-dessus le halo
    for k in range(len(ORBITS)):
        pts = [orbit_point(k, t / 240 * 2 * math.pi) for t in range(241)]
        d.line(pts, fill=(60, 64, 72, 255), width=6)
        d.line(pts, fill=(150, 156, 168, 255), width=2)
    for n, (x, y) in pos.items():
        if n == GALAXY:
            continue
        size = 66 if n in COMBATS else 110 if n == FINAL else 88
        halo = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
        ImageDraw.Draw(halo).ellipse((size // 2, size // 2, size * 3 // 2, size * 3 // 2),
                                     fill=(ORANGE if n == FINAL else BLUE) + (120,))
        halo = halo.filter(ImageFilter.GaussianBlur(16))
        img.paste(halo, (x - size, y - size), halo)
        pl = pt_art.planet(n, size)
        img.paste(pl, (x - size // 2, y - size // 2), pl)
        d = ImageDraw.Draw(img, "RGBA")
        plate(d, x, y - size // 2 - 2, label_lines(n), font(20 if n not in COMBATS else 17),
              ORANGE if n not in COMBATS else (230, 70, 70))
    d = ImageDraw.Draw(img, "RGBA")
    gx, gy = pos[GALAXY]
    plate(d, gx, gy + 30, ["Galaxy-wide"], font(22), BLUE)
    tf = font(44)
    tw = d.textbbox((0, 0), "POLARIS GALAXY", font=tf)[2]
    x0, y0 = MAP_W - tw - 70, MAP_H - 92
    d.rounded_rectangle((x0, y0, x0 + tw + 40, y0 + 64), 10, fill=(20, 22, 28, 240), outline=ORANGE + (255,), width=3)
    d.line((x0 + 14, y0 + 58, x0 + tw + 26, y0 + 58), fill=BLUE + (220,), width=3)
    d.text((x0 + 20, y0 + 6), "POLARIS GALAXY", font=tf, fill=(255, 170, 60))
    if LOGO.exists():
        logo = Image.open(LOGO).convert("RGBA")
        logo = logo.resize((380, int(380 * logo.height / logo.width)), Image.LANCZOS)
        img.paste(logo, (24, 20), logo)
    full = Image.new("RGBA", (MAP_W + PANEL_W, MAP_H), (0, 0, 0, 255))
    full.paste(img, (0, 0))
    draw_panel(full, *panel_slots())
    return full.convert("RGB")


# --- logique (copie de create_regions) -------------------------------------------------------------------
def region_rules(region):
    if region in PLANETS:
        return [[code(region)]]
    if region in COMBATS:
        return [[code(region)], [code(COMBATS[region].planet)]]
    if region == FINAL:
        return [[code(p) for p in PLANETS] + [code(g) for g in GADGETS] + ["progressive_clank:2"]]
    return [[]]


def loc_rules(d):
    if d.kind == "leviathan":
        return [f"$planets|{d.value}"]
    if d.kind == "level":
        return [f"$planets|{(d.value + 3) // 4}"]
    if d.kind == "weapon_level":
        return [f"{code(d.needs[0])},$planets|{2 * (d.value % 16 - 1)}"]
    extra = [code(n) for n in d.needs]
    if d.kind in ("mission", "skill", "gold_bolt", "statue", "holoplan") and d.region in PLANETS:
        extra.append("progressive_clank")
    rules = []
    for base in region_rules(d.region):
        r = list(dict.fromkeys(base + extra))
        rules.append(",".join(r))
    return [r for r in rules if r] or []


def main():
    version = json.loads((SRC / "archipelago.json").read_text(encoding="utf-8"))["world_version"]
    shutil.rmtree(OUT, ignore_errors=True)
    for sub in ("images/items", "items", "locations", "maps", "layouts", "scripts"):
        (OUT / sub).mkdir(parents=True)

    # objets suivis
    tracked = [n for n, d in ITEMS.items() if d.kind not in ("bolts", "raritanium")]
    item_defs = []
    for n in tracked:
        d = ITEMS[n]
        c = code(n)
        img = item_icon(n, d.kind)
        img.save(OUT / f"images/items/{c}.png")
        off(img).save(OUT / f"images/items/{c}_off.png")
        if d.kind in ("clank", "armor", "weapon"):
            mx = D.CLANK_COUNT if d.kind == "clank" else D.ARMOR_COUNT if d.kind == "armor" else 5
            item_defs.append({"name": n, "type": "consumable", "img": f"images/items/{c}.png",
                              "disabled_img": f"images/items/{c}_off.png", "codes": c, "max_quantity": mx})
        else:
            item_defs.append({"name": n, "type": "toggle", "img": f"images/items/{c}.png",
                              "disabled_img": f"images/items/{c}_off.png", "codes": c})
    item_defs.append({"name": "Player Levels (option)", "type": "consumable", "img": "images/items/progressive_clank.png",
                      "codes": "opt_player_levels", "max_quantity": D.MAX_LEVEL_CHECKS})
    (OUT / "items/items.json").write_text(json.dumps(item_defs, indent=1), encoding="utf-8")

    # cartes : galaxie + cartes de niveau du jeu
    pos = galaxy_positions()
    draw_map(pos).save(OUT / "images/galaxy.png", optimize=True)
    maps = [{"name": "galaxy", "img": "images/galaxy.png", "location_size": 34, "location_border_thickness": 3}]
    for files in LEVEL_MAPS.values():
        for f in files:
            if f not in {m["name"] for m in maps}:
                shutil.copy2(pt_art.WIKI / f"map_{f}.png", OUT / f"images/map_{f}.png")
                maps.append({"name": f, "img": f"images/map_{f}.png", "location_size": 26, "location_border_thickness": 3})
    (OUT / "maps/maps.json").write_text(json.dumps(maps, indent=1), encoding="utf-8")
    # checks : une location par région et par groupe (Missions, Gold Bolts...) ; sur la carte de niveau, les groupes sont
    # rangés en colonne au bord gauche (pas encore à leur vraie place) ; la galaxie montre la région entière (ref).
    groups: dict[str, dict[str, list]] = {}
    for name, d in LOCATIONS.items():
        region = d.region if d.region != "Menu" else GALAXY
        if name.startswith("Skill Point - "):
            region = GALAXY
        group = dict(GROUPS).get(d.kind, "Other")
        if d.kind == "weapon_level":  # « Weapon Levels » / <arme> / V2..V5
            region, group = WEAPON_LEVELS, d.needs[0]
        groups.setdefault(region, {}).setdefault(group, []).append((name, d))
    locs, mapping, galaxy_children = [], {}, []
    slots, _ = panel_slots()
    for region, by_group in groups.items():
        children, refs = [], []
        for gi, (group, entries) in enumerate(by_group.items()):
            sections = []
            for name, d in entries:
                sec_name = name.split(": ", 1)[1] if name.startswith(region + ": ") else name
                sec = {"name": sec_name, "item_count": 1}
                rules = loc_rules(d)
                if rules:
                    sec["access_rules"] = rules
                if d.kind == "level":
                    sec["visibility_rules"] = [f"$level_on|{d.value}"]
                sections.append(sec)
                mapping[d.id] = f"@{region}/{group}/{sec_name}"
                refs.append({"name": sec_name, "ref": f"{region}/{group}/{sec_name}"})
            mls = [{"map": f, "x": 40, "y": 60 + gi * 64} for f in LEVEL_MAPS.get(region, [])]
            key = (WEAPON_LEVELS, group) if region == WEAPON_LEVELS else (group, region)
            if key in slots:
                sx, sy = slots[key]
                mls.append({"map": "galaxy", "x": sx + 26, "y": sy - 16, "size": PIN, "border_thickness": 2})
            children.append({"name": group, "map_locations": mls, "sections": sections})
        if region == WEAPON_LEVELS:  # pas de point sur la galaxie : seulement les cases du panneau
            locs.append({"name": region, "chest_unopened_img": "images/chest.png",
                         "chest_opened_img": "images/chest_open.png", "children": children})
            continue
        x, y = pos[region]
        locs.append({"name": region, "chest_unopened_img": "images/chest.png", "chest_opened_img": "images/chest_open.png",
                     "children": children})
        galaxy_children.append({"name": region, "map_locations": [{"map": "galaxy", "x": x, "y": y}], "sections": refs})
    locs.append({"name": "Polaris", "chest_unopened_img": "images/chest.png", "chest_opened_img": "images/chest_open.png",
                 "children": galaxy_children})
    (OUT / "locations/locations.json").write_text(json.dumps(locs, indent=1), encoding="utf-8")
    chest = pt_art.item_icon("Holo-Plan", "obj", 32)
    chest.save(OUT / "images/chest.png")
    off(chest).save(OUT / "images/chest_open.png")

    # scripts
    lines = ["-- généré par tools/make_poptracker.py", "ITEM_MAPPING = {"]
    lines += [f"  [{ITEMS[n].id}] = {json.dumps(code(n))}," for n in tracked]
    lines += ["}", "LOCATION_MAPPING = {"]
    lines += [f"  [{lid}] = {json.dumps(p)}," for lid, p in sorted(mapping.items())]
    lines += ["}", "PLANET_CODES = {" + ", ".join(json.dumps(code(p)) for p in PLANETS) + "}"]
    (OUT / "scripts/ids.lua").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (OUT / "scripts/logic.lua").write_text(LOGIC_LUA, encoding="utf-8")
    (OUT / "scripts/autotracking.lua").write_text(AUTOTRACKING_LUA, encoding="utf-8")
    (OUT / "scripts/init.lua").write_text(INIT_LUA, encoding="utf-8")

    # disposition : objets à gauche, galaxie à droite
    def rows(names, n=7):
        cs = [code(x) for x in names]
        return [cs[i:i + n] for i in range(0, len(cs), n)]
    planet_names = list(PLANETS) + list(COMBATS)
    weapons = [n for n, d in ITEMS.items() if d.kind == "weapon"]
    devices = [n for n, d in ITEMS.items() if d.kind == "device_unlock"]
    progressive = ["Progressive Clank", "Progressive Armor", "Charge Boots"]

    def grid(names, n):
        return {"type": "itemgrid", "item_margin": "4,3", "h_alignment": "left", "item_size": "56", "rows": rows(names, n)}
    items_grid = {"type": "array", "orientation": "horizontal", "content": [
        {"type": "group", "header": "Weapons", "content": grid(weapons, 6)},
        {"type": "group", "header": "Gadgets", "content": grid(GADGETS, 4)},
        {"type": "group", "header": "Progressive", "content": grid(progressive, 3)},
        {"type": "group", "header": "Devices", "content": grid(devices, 4)}]}
    planets_grid = {"type": "itemgrid", "item_margin": "4,3", "h_alignment": "left", "item_size": "56",
                    "rows": rows(planet_names, 6)}
    bottom = {"type": "dock", "dock": "bottom", "content": [
        {"type": "dock", "dock": "left", "content": [items_grid]},
        {"type": "group", "header": "Planets", "dock": "left", "content": planets_grid}]}
    tabs = {"type": "tabbed", "tabs": [{"title": "Galaxy", "content": {"type": "map", "maps": ["galaxy"]}}] + [
        {"title": region.replace(" Space Station", "").replace(" Passage", ""), "content": {"type": "map", "maps": files}}
        for region, files in LEVEL_MAPS.items()]}
    main_view = {"type": "container", "background": "#0c0e14",
                 "content": {"type": "dock", "dropshadow": True, "content": [bottom, tabs]}}
    broadcast = {"type": "array", "orientation": "vertical", "content": [items_grid, planets_grid]}
    layout = {"tracker_default": main_view, "tracker_horizontal": main_view, "tracker_vertical": main_view,
              "tracker_broadcast": broadcast}
    items_only = {"type": "container", "background": "#0c0e14", "content": {
        "type": "array", "orientation": "vertical", "content": [
            {"type": "group", "header": "Items", "content": items_grid},
            {"type": "group", "header": "Planets", "content": planets_grid}]}}
    (OUT / "var_itemsonly/layouts").mkdir(parents=True)
    (OUT / "var_itemsonly/layouts/tracker.json").write_text(json.dumps(
        {"tracker_default": items_only, "tracker_horizontal": items_only, "tracker_vertical": items_only,
         "tracker_broadcast": broadcast}, indent=1), encoding="utf-8")
    (OUT / "layouts/tracker.json").write_text(json.dumps(layout, indent=1), encoding="utf-8")
    manifest = {"name": "Ratchet & Clank: Tools of Destruction Archipelago",
                "game_name": "Ratchet and Clank Tools of Destruction", "package_uid": "rac_tod_archipelago_snokayy",
                "package_version": version, "platform": "ps3", "author": "Snokayy",
                "min_poptracker_version": "0.25.6", "target_poptracker_version": "0.35.4",
                "variants": {"standard": {"display_name": "Map Tracker", "flags": ["ap"]},
                             "var_itemsonly": {"display_name": "Items Only", "flags": ["ap"]}}}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")

    target = ROOT / "dist" / f"RaC_ToD_AP_poptracker_{version}.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(OUT).as_posix())
    print(f"pack {version} : {len(mapping)} checks, {len(tracked)} objets -> {target}")


INIT_LUA = """-- Ratchet & Clank: Tools of Destruction Archipelago : pack généré par tools/make_poptracker.py
ScriptHost:LoadScript("scripts/ids.lua")
ScriptHost:LoadScript("scripts/logic.lua")
Tracker:AddItems("items/items.json")
Tracker:AddMaps("maps/maps.json")
Tracker:AddLocations("locations/locations.json")
Tracker:AddLayouts("layouts/tracker.json")
if Archipelago then
    ScriptHost:LoadScript("scripts/autotracking.lua")
end
"""

LOGIC_LUA = """-- Règles (mêmes que l'apworld)
function planets(n)
    local count = 0
    for _, c in ipairs(PLANET_CODES) do
        if Tracker:ProviderCountForCode(c) > 0 then count = count + 1 end
    end
    return count >= tonumber(n)
end
-- checks de niveau : les N premiers (option player_levels, 20 par défaut tant que le tracker n'est pas connecté)
function level_on(k)
    local o = Tracker:FindObjectForCode("opt_player_levels")
    local n = 20
    if o and o.AcquiredCount > 0 then n = o.AcquiredCount end
    if LEVELS_ZERO then n = 0 end
    return tonumber(k) <= n
end
"""

AUTOTRACKING_LUA = """-- Suivi automatique Archipelago
local function reset()
    for _, c in pairs(ITEM_MAPPING) do
        local o = Tracker:FindObjectForCode(c)
        if o then
            if o.Type == "consumable" then o.AcquiredCount = 0 else o.Active = false end
        end
    end
    for _, path in pairs(LOCATION_MAPPING) do
        local s = Tracker:FindObjectForCode(path)
        if s then s.AvailableChestCount = s.ChestCount end
    end
end

function on_clear(slot_data)
    Tracker.BulkUpdate = true
    pcall(reset)
    LEVELS_ZERO = false
    if slot_data and slot_data.player_levels ~= nil then
        local n = tonumber(slot_data.player_levels) or 20
        LEVELS_ZERO = (n == 0)
        local o = Tracker:FindObjectForCode("opt_player_levels")
        if o then o.AcquiredCount = n end
    end
    Tracker.BulkUpdate = false
end

function on_item(index, item_id, item_name, player)
    local c = ITEM_MAPPING[item_id]
    if not c then return end
    local o = Tracker:FindObjectForCode(c)
    if not o then return end
    if o.Type == "consumable" then o.AcquiredCount = o.AcquiredCount + 1 else o.Active = true end
end

function on_location(location_id, location_name)
    local path = LOCATION_MAPPING[location_id]
    if not path then return end
    local s = Tracker:FindObjectForCode(path)
    if s then s.AvailableChestCount = 0 end
end

Archipelago:AddClearHandler("clear", on_clear)
Archipelago:AddItemHandler("item", on_item)
Archipelago:AddLocationHandler("location", on_location)
"""

if __name__ == "__main__":
    main()
