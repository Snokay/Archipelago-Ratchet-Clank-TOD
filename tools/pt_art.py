"""
Dessins du pack PopTracker (2026-10-16), dans le style du logo et de l'emblème du développeur : cadres en métal sombre
rivetés, vitre colorée lumineuse à motif hexagonal, pictogramme clair ; planètes dessinées une par une. Tout est généré
(Pillow), aucune image du jeu. Dessin en 256 px puis réduit (anticrénelage).
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

S = 256  # taille de travail
# Images du jeu reprises du wiki Fandom (Ratchet & Clank Wiki) : icônes des menus, planètes, cartes de niveau.
WIKI = Path(__file__).resolve().parent.parent / "poptracker_assets"
WIKI_ICON = {"Progressive Clank": "Heli-Pack", "Progressive Armor": None}


def upscale_silhouette(img, size):
    """Icônes du wiki (64 px, silhouettes claires) : agrandies sans flou (alpha agrandi en bicubique puis contrasté)."""
    big = img.resize((size, size), Image.BICUBIC)
    a = big.getchannel("A").point(lambda v: 0 if v < 70 else 255 if v > 150 else int((v - 70) * 255 / 80))
    rgb = big.convert("RGB").filter(ImageFilter.UnsharpMask(radius=2, percent=120, threshold=2))
    out = rgb.convert("RGBA")
    out.putalpha(a)
    return out


def wiki(prefix, name):
    f = WIKI / f"{prefix}_{name.replace(' ', '_').replace('.', '').replace(chr(39), '')}.png"
    return Image.open(f).convert("RGBA") if f.exists() else None
GLASS = {"weapon": (255, 120, 20), "gadget": (40, 130, 255), "device_unlock": (170, 60, 255), "clank": (255, 190, 20),
         "armor": (230, 40, 40), "obj": (40, 200, 60)}


def _octagon(m, cut):
    return [(m + cut, m), (S - m - cut, m), (S - m, m + cut), (S - m, S - m - cut), (S - m - cut, S - m), (m + cut, S - m),
            (m, S - m - cut), (m, m + cut)]


def _hex_pattern(rgb):
    pat = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(pat)
    r = 11
    for row in range(-1, 16):
        for col in range(-1, 14):
            cx = col * r * 1.75 + (row % 2) * r * 0.87
            cy = row * r * 1.5
            pts = [(cx + r * math.cos(math.pi / 6 + k * math.pi / 3), cy + r * math.sin(math.pi / 6 + k * math.pi / 3))
                   for k in range(6)]
            d.polygon(pts, outline=tuple(min(255, c + 60) for c in rgb) + (45,))
    return pat


def frame(rgb):
    """Cadre métal + vitre colorée (sans pictogramme)."""
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.polygon(_octagon(6, 46), fill=(30, 32, 36, 255))
    d.polygon(_octagon(10, 44), fill=(88, 92, 100, 255))
    metal = Image.new("RGBA", (S, S), (0, 0, 0, 0))  # dégradé du métal (clair en haut à gauche)
    md = ImageDraw.Draw(metal)
    for i in range(S):
        md.line((0, i, S, i), fill=(255, 255, 255, int(70 * (1 - i / S))))
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).polygon(_octagon(10, 44), fill=255)
    img.paste(Image.alpha_composite(img, metal), (0, 0), mask)
    d = ImageDraw.Draw(img)
    d.polygon(_octagon(26, 36), fill=(18, 18, 22, 255))
    # vitre : dégradé radial de la couleur + motif hexagonal + reflet
    glass = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glass)
    for r in range(110, 0, -2):
        k = 0.35 + 0.65 * (1 - r / 110)
        gd.ellipse((S / 2 - r * 1.3, S / 2 - r * 1.3, S / 2 + r * 1.3, S / 2 + r * 1.3),
                   fill=tuple(int(c * k) for c in rgb) + (255,))
    glass = Image.alpha_composite(glass, _hex_pattern(rgb))
    gmask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(gmask).polygon(_octagon(32, 33), fill=255)
    img.paste(glass, (0, 0), gmask)
    d = ImageDraw.Draw(img)
    d.polygon(_octagon(32, 33), outline=tuple(min(255, c + 80) for c in rgb) + (255,), width=3)
    shine = Image.new("RGBA", (S, S), (0, 0, 0, 0))  # reflet mélangé (dessiner un alpha faible ferait un trou)
    ImageDraw.Draw(shine).polygon([(52, 44), (120, 44), (56, 96)], fill=(255, 255, 255, 22))
    img = Image.alpha_composite(img, shine)
    d = ImageDraw.Draw(img)
    # voyants lumineux et rivets
    for x0, y0, x1, y1 in ((112, 12, 144, 20), (112, 236, 144, 244), (12, 112, 20, 144), (236, 112, 244, 144)):
        d.rounded_rectangle((x0, y0, x1, y1), 3, fill=tuple(min(255, c + 90) for c in rgb) + (255,))
    for x, y in ((44, 22), (212, 22), (44, 234), (212, 234), (22, 60), (234, 60), (22, 196), (234, 196)):
        d.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(150, 155, 165, 255), outline=(25, 25, 30, 255))
    return img


def glow(glyph, rgb):
    """Pictogramme clair avec un halo de la couleur de la vitre."""
    a = glyph.getchannel("A")
    halo = Image.new("RGBA", (S, S), tuple(min(255, c + 100) for c in rgb) + (0,))
    halo.putalpha(a.filter(ImageFilter.GaussianBlur(7)).point(lambda v: min(255, v * 2)))
    out = Image.alpha_composite(halo, glyph)
    return out


# --- pictogrammes (couleur claire, sur 256 x 256, zone utile ~ 70-186) -------------------------------------------------
C = (255, 246, 225, 255)


def _new():
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def g_bolt():  # Shock Ravager : éclair
    img, d = _new()
    d.polygon([(140, 62), (92, 136), (124, 136), (108, 196), (166, 112), (132, 112), (152, 62)], fill=C)
    return img


def g_tornado():
    img, d = _new()
    for i, (w, y) in enumerate(((110, 76), (90, 100), (70, 124), (50, 148), (30, 172))):
        x = 128 + (i - 2) * 6
        d.ellipse((x - w / 2, y - 9, x + w / 2, y + 9), outline=C, width=8)
    return img


def g_saw():  # Buzz Blades : lame circulaire
    img, d = _new()
    pts = []
    for k in range(24):
        r = 62 if k % 2 == 0 else 44
        a = k * math.pi / 12
        pts.append((128 + r * math.cos(a), 128 + r * math.sin(a)))
    d.polygon(pts, fill=C)
    d.ellipse((108, 108, 148, 148), fill=(0, 0, 0, 0))
    img2, d2 = _new()
    d2.polygon(pts, fill=C)
    d2.ellipse((110, 110, 146, 146), fill=(0, 0, 0, 0))
    hole = Image.new("L", (S, S), 255)
    ImageDraw.Draw(hole).ellipse((110, 110, 146, 146), fill=0)
    img2.putalpha(ImageChops.multiply(img2.getchannel("A"), hole))
    return img2


def g_missile():  # Predator Launcher
    img, d = _new()
    d.polygon([(70, 186), (150, 106), (170, 126), (90, 206)], fill=C)
    d.polygon([(150, 106), (186, 70), (170, 126)], fill=C)
    d.polygon([(78, 150), (98, 170), (60, 172)], fill=C)
    d.polygon([(106, 178), (86, 158), (84, 196)], fill=C)
    return img


def g_orb():  # Alpha Disruptor
    img, d = _new()
    d.ellipse((98, 98, 158, 158), fill=C)
    for k in range(8):
        a = k * math.pi / 4
        d.line((128 + 42 * math.cos(a), 128 + 42 * math.sin(a), 128 + 66 * math.cos(a), 128 + 66 * math.sin(a)), fill=C, width=10)
    return img


def g_flame():  # Pyro Blaster
    img, d = _new()
    d.polygon([(128, 60), (170, 130), (164, 170), (128, 196), (92, 170), (86, 130), (108, 110), (112, 140)], fill=C)
    d.ellipse((92, 120, 164, 196), fill=C)
    return img


def g_beast():  # Plasma Beasts : patte
    img, d = _new()
    d.ellipse((92, 120, 164, 186), fill=C)
    for x, y in ((80, 96), (110, 76), (146, 76), (176, 96)):
        d.ellipse((x - 16, y - 18, x + 16, y + 18), fill=C)
    return img


def g_shards():  # Shard Reaper
    img, d = _new()
    d.polygon([(128, 56), (150, 128), (128, 200), (106, 128)], fill=C)
    d.polygon([(72, 100), (100, 134), (82, 186), (62, 140)], fill=C)
    d.polygon([(184, 100), (194, 140), (174, 186), (156, 134)], fill=C)
    return img


def g_crosshair():  # Negotiator
    img, d = _new()
    d.ellipse((72, 72, 184, 184), outline=C, width=12)
    d.ellipse((116, 116, 140, 140), fill=C)
    for a, b, c_, e in ((128, 52, 128, 96), (128, 160, 128, 204), (52, 128, 96, 128), (160, 128, 204, 128)):
        d.line((a, b, c_, e), fill=C, width=12)
    return img


def g_swarm():  # Nano-Swarmers
    img, d = _new()
    rnd = random.Random(3)
    for _ in range(16):
        a, r = rnd.uniform(0, 6.3), rnd.uniform(0, 62)
        x, y, s = 128 + r * math.cos(a), 128 + r * math.sin(a), rnd.randint(8, 15)
        d.ellipse((x - s, y - s, x + s, y + s), fill=C)
    return img


def g_net():  # Mag-Net Launcher
    img, d = _new()
    d.ellipse((66, 66, 190, 190), outline=C, width=10)
    for k in range(-2, 3):
        d.line((128 + k * 24 - 50, 80, 128 + k * 24 + 50, 176), fill=C, width=6)
        d.line((128 + k * 24 + 50, 80, 128 + k * 24 - 50, 176), fill=C, width=6)
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).ellipse((60, 60, 196, 196), fill=255)
    img.putalpha(ImageChops.multiply(img.getchannel("A"), m))
    return img


def g_claws():  # Razor Claws
    img, d = _new()
    for k in range(3):
        x = 86 + k * 36
        d.polygon([(x, 196), (x + 14, 196), (x + 48, 62), (x + 30, 76)], fill=C)
    return img


def g_shield():  # armure
    img, d = _new()
    d.polygon([(128, 58), (188, 80), (180, 150), (128, 200), (76, 150), (68, 80)], fill=C)
    d.polygon([(128, 80), (166, 94), (160, 144), (128, 176)], fill=(0, 0, 0, 0))
    a = img.getchannel("A")
    cut = Image.new("L", (S, S), 255)
    ImageDraw.Draw(cut).polygon([(128, 80), (166, 94), (160, 144), (128, 176)], fill=110)
    img.putalpha(ImageChops.multiply(a, cut))
    return img


def g_robot():  # Mr. Zurkon
    img, d = _new()
    d.rounded_rectangle((84, 96, 172, 172), 20, fill=C)
    d.ellipse((100, 118, 124, 142), fill=(0, 0, 0, 0))
    d.line((128, 96, 128, 70), fill=C, width=8)
    d.ellipse((118, 58, 138, 78), fill=C)
    cut = Image.new("L", (S, S), 255)
    ImageDraw.Draw(cut).ellipse((100, 118, 124, 142), fill=0)
    ImageDraw.Draw(cut).ellipse((132, 118, 156, 142), fill=0)
    img.putalpha(ImageChops.multiply(img.getchannel("A"), cut))
    d.polygon([(118, 172), (138, 172), (146, 196), (110, 196)], fill=C)
    return img


def g_cloud():  # Confuzzler Gas
    img, d = _new()
    for x, y, r in ((96, 140, 34), (132, 120, 42), (166, 142, 32), (128, 156, 36)):
        d.ellipse((x - r, y - r, x + r, y + r), fill=C)
    d.text((114, 80), "?", fill=C)
    return img


def g_spring():  # Death Springs
    img, d = _new()
    for k in range(6):
        y = 76 + k * 22
        d.line((84, y, 172, y + 11), fill=C, width=10)
        d.line((172, y + 11, 84, y + 22), fill=C, width=10)
    return img


def g_disco():  # Groovitron
    img, d = _new()
    d.ellipse((76, 84, 180, 188), fill=C)
    d.line((128, 52, 128, 84), fill=C, width=8)
    for k in range(1, 5):
        d.line((76, 84 + k * 21, 180, 84 + k * 21), fill=(0, 0, 0, 0), width=4)
    cut = Image.new("L", (S, S), 255)
    cd = ImageDraw.Draw(cut)
    for k in range(1, 5):
        cd.line((70, 84 + k * 21, 186, 84 + k * 21), fill=0, width=5)
        cd.line((76 + k * 21, 84, 76 + k * 21, 188), fill=0, width=5)
    img.putalpha(ImageChops.multiply(img.getchannel("A"), cut))
    return img


def g_bomb(big=False):  # Leech Bomb / Mega Leech Bomb
    img, d = _new()
    r = 56 if big else 46
    d.ellipse((128 - r, 140 - r, 128 + r, 140 + r), fill=C)
    d.rectangle((116, 140 - r - 16, 140, 140 - r + 6), fill=C)
    d.line((128, 140 - r - 16, 150, 60), fill=C, width=6)
    d.polygon([(150, 50), (160, 64), (146, 68)], fill=C)
    if big:
        d.line((180, 74, 180, 110), fill=C, width=10)
        d.line((162, 92, 198, 92), fill=C, width=10)
    return img


def g_cycle():  # Transmorpher
    img, d = _new()
    d.arc((72, 72, 184, 184), 200, 340, fill=C, width=14)
    d.arc((72, 72, 184, 184), 20, 160, fill=C, width=14)
    d.polygon([(176, 96), (196, 132), (160, 124)], fill=C)
    d.polygon([(80, 160), (60, 124), (96, 132)], fill=C)
    return img


def g_copter():  # Visi-Copter
    img, d = _new()
    d.ellipse((92, 116, 164, 176), fill=C)
    d.line((128, 116, 128, 92), fill=C, width=8)
    d.line((60, 90, 196, 90), fill=C, width=10)
    d.line((164, 146, 200, 140), fill=C, width=8)
    return img


def g_helipods():
    img, d = _new()
    for x in (90, 166):
        d.ellipse((x - 26, 120, x + 26, 172), fill=C)
        d.line((x - 36, 104, x + 36, 104), fill=C, width=8)
        d.line((x, 104, x, 120), fill=C, width=6)
    d.line((90, 146, 166, 146), fill=C, width=8)
    return img


def g_laser():  # Geo-Laser
    img, d = _new()
    d.polygon([(128, 62), (168, 112), (128, 162), (88, 112)], fill=C)
    d.line((128, 162, 128, 204), fill=C, width=10)
    d.line((96, 196, 160, 196), fill=C, width=6)
    return img


def g_gel():  # Gelanator : cube de gel
    img, d = _new()
    d.polygon([(128, 66), (184, 96), (128, 126), (72, 96)], fill=C)
    d.polygon([(72, 104), (124, 132), (124, 194), (72, 164)], fill=(255, 246, 225, 200))
    d.polygon([(184, 104), (132, 132), (132, 194), (184, 164)], fill=(255, 246, 225, 150))
    return img


def g_wings():  # Robo-Wings
    img, d = _new()
    for s_ in (-1, 1):
        for k in range(3):
            d.polygon([(128, 120 + k * 10), (128 + s_ * (66 - k * 10), 74 + k * 26), (128 + s_ * (72 - k * 12), 96 + k * 26),
                       (128, 140 + k * 10)], fill=C)
    d.ellipse((114, 108, 142, 176), fill=C)
    return img


def g_wheel():  # Gyro-Cycle
    img, d = _new()
    d.ellipse((66, 66, 190, 190), outline=C, width=16)
    d.ellipse((112, 112, 144, 144), fill=C)
    for k in range(6):
        a = k * math.pi / 3
        d.line((128, 128, 128 + 56 * math.cos(a), 128 + 56 * math.sin(a)), fill=C, width=7)
    return img


def g_pirate():  # Holo-Pirate Disguise : tête de mort
    img, d = _new()
    d.ellipse((80, 70, 176, 160), fill=C)
    d.rounded_rectangle((100, 140, 156, 180), 8, fill=C)
    cut = Image.new("L", (S, S), 255)
    cd = ImageDraw.Draw(cut)
    cd.ellipse((98, 102, 124, 128), fill=0)
    cd.ellipse((132, 102, 158, 128), fill=0)
    cd.polygon([(128, 132), (120, 146), (136, 146)], fill=0)
    for x in (112, 128, 144):
        cd.line((x, 160, x, 180), fill=0, width=4)
    img.putalpha(ImageChops.multiply(img.getchannel("A"), cut))
    d.line((70, 196, 186, 156), fill=C, width=10)
    d.line((70, 156, 186, 196), fill=C, width=10)
    return img


def g_key():  # Decryptor
    img, d = _new()
    d.ellipse((66, 84, 134, 152), outline=C, width=16)
    d.line((130, 118, 196, 118), fill=C, width=16)
    d.line((176, 118, 176, 146), fill=C, width=12)
    d.line((156, 118, 156, 140), fill=C, width=12)
    return img


def g_boot():  # Charge Boots
    img, d = _new()
    d.polygon([(110, 66), (150, 66), (150, 146), (196, 160), (196, 190), (110, 190)], fill=C)
    for k, y in enumerate((100, 128, 156)):
        d.line((56 + k * 6, y, 96, y), fill=C, width=8)
    return img


def g_clank():  # Progressive Clank : tête de Clank
    img, d = _new()
    d.rounded_rectangle((76, 92, 180, 172), 26, fill=C)
    d.line((128, 92, 128, 64), fill=C, width=8)
    d.ellipse((116, 50, 140, 74), fill=C)
    cut = Image.new("L", (S, S), 255)
    cd = ImageDraw.Draw(cut)
    cd.ellipse((92, 110, 124, 142), fill=0)
    cd.ellipse((132, 110, 164, 142), fill=0)
    img.putalpha(ImageChops.multiply(img.getchannel("A"), cut))
    d.ellipse((102, 120, 114, 132), fill=C)
    d.ellipse((142, 120, 154, 132), fill=C)
    d.rounded_rectangle((104, 172, 152, 200), 6, fill=C)
    return img


GLYPHS = {
    "Shock Ravager": g_bolt, "Tornado Launcher": g_tornado, "Buzz Blades": g_saw, "Predator Launcher": g_missile,
    "Alpha Disruptor": g_orb, "Pyro Blaster": g_flame, "Plasma Beasts": g_beast, "Shard Reaper": g_shards,
    "Negotiator": g_crosshair, "Nano-Swarmers": g_swarm, "Mag-Net Launcher": g_net, "Razor Claws": g_claws,
    "Progressive Armor": g_shield, "Mr. Zurkon Unlock": g_robot, "Confuzzler Gas Unlock": g_cloud,
    "Death Springs Unlock": g_spring, "Groovitron Unlock": g_disco, "Leech Bomb Unlock": g_bomb,
    "Mega Leech Bomb Unlock": lambda: g_bomb(True), "Transmorpher Unlock": g_cycle, "Visi-Copter Unlock": g_copter,
    "Heli-Pods": g_helipods, "Geo-Laser": g_laser, "Gelanator": g_gel, "Robo-Wings": g_wings, "Gyro-Cycle": g_wheel,
    "Holo-Pirate Disguise": g_pirate, "Decryptor": g_key, "Charge Boots": g_boot, "Progressive Clank": g_clank,
}


def item_icon(name, kind, size=64):
    rgb = GLASS.get(kind, (120, 120, 140))
    img = frame(rgb)
    real = wiki("icon", WIKI_ICON.get(name, name.replace(" Unlock", ""))) if WIKI_ICON.get(name, 1) else None
    if name == "Progressive Armor":
        armor = wiki("armor", "Blackstar")
        if armor:
            armor.thumbnail((int(S * 0.62), int(S * 0.62)), Image.LANCZOS)
            img.paste(armor, ((S - armor.width) // 2, (S - armor.height) // 2), armor)
            return img.resize((size, size), Image.LANCZOS)
    if real:  # vraie icône du jeu (silhouette blanche) avec le halo de la vitre
        g = upscale_silhouette(real, int(S * 0.66))
        pad = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        pad.paste(g, ((S - g.width) // 2, (S - g.height) // 2), g)
        img = Image.alpha_composite(img, glow(pad, rgb))
    elif glyph := GLYPHS.get(name):
        g = glyph().resize((int(S * 0.95),) * 2, Image.LANCZOS)
        pad = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        pad.paste(g, ((S - g.width) // 2, (S - g.height) // 2), g)
        img = Image.alpha_composite(img, glow(pad, rgb))
    return img.resize((size, size), Image.LANCZOS)


# --- planètes --------------------------------------------------------------------------------------------------------
# (couleur de base, couleur 2, style, anneau) ; styles : bands, land, clouds, rock, ice, lava, city
PLANET_LOOK = {
    "Cobalia": ((40, 110, 140), (230, 140, 50), "city", False),
    "Kortog": ((110, 170, 230), (240, 245, 255), "clouds", False),
    "Fastoon": ((150, 110, 70), (90, 70, 50), "rock", False),
    "Mukow": ((120, 60, 160), (90, 200, 90), "land", True),
    "Apogee Space Station": ((140, 150, 165), (60, 70, 90), "bands", True),
    "Ardolis": ((40, 120, 200), (230, 210, 140), "land", False),
    "Rykan V": ((100, 130, 110), (200, 210, 200), "clouds", False),
    "Sargasso": ((50, 120, 50), (20, 70, 40), "land", False),
    "Kreeli Comet": ((190, 225, 245), (120, 170, 210), "ice", False),
    "Viceron": ((80, 40, 90), (230, 90, 40), "lava", False),
    "Jasindu": ((40, 140, 110), (30, 90, 160), "land", False),
    "Ublik Passage": ((60, 90, 140), (150, 200, 230), "ice", True),
    "Reepor": ((170, 60, 40), (100, 30, 20), "rock", False),
    "Igliak": ((220, 150, 60), (255, 230, 150), "city", False),
    "Fastoon (Final)": ((200, 80, 40), (90, 30, 20), "lava", True),
    "Voron Asteroid Belt": ((120, 110, 100), (70, 60, 55), "asteroids", False),
    "Rakar Star Cluster": ((255, 230, 150), (150, 200, 255), "stars", False),
    "Verdigris Black Hole": ((10, 10, 15), (60, 220, 160), "hole", False),
}


def _texture(base, c2, style, seed):
    rnd = random.Random(seed)
    tex = Image.new("RGB", (S, S), base)
    d = ImageDraw.Draw(tex)
    if style == "bands":
        for y in range(0, S, 14):
            d.rectangle((0, y, S, y + rnd.randint(4, 10)), fill=c2)
    elif style in ("land", "rock", "lava"):
        for _ in range(28 if style == "land" else 40):
            x, y, r = rnd.randint(0, S), rnd.randint(0, S), rnd.randint(10, 46 if style == "land" else 26)
            d.ellipse((x - r, y - r * 0.7, x + r, y + r * 0.7), fill=c2)
        if style == "lava":
            for _ in range(14):
                x, y = rnd.randint(0, S), rnd.randint(0, S)
                d.line((x, y, x + rnd.randint(-60, 60), y + rnd.randint(-40, 40)), fill=(255, 160, 60), width=3)
    elif style == "clouds":
        for _ in range(22):
            y, x, w = rnd.randint(0, S), rnd.randint(-40, S), rnd.randint(50, 140)
            d.ellipse((x, y - 7, x + w, y + 7), fill=c2)
    elif style == "ice":
        for _ in range(30):
            x, y = rnd.randint(0, S), rnd.randint(0, S)
            d.line((x, y, x + rnd.randint(-50, 50), y + rnd.randint(-50, 50)), fill=c2, width=2)
    elif style == "city":
        for _ in range(140):
            x, y = rnd.randint(0, S), rnd.randint(0, S)
            d.rectangle((x, y, x + 3, y + 3), fill=c2)
        for _ in range(10):
            x, y, r = rnd.randint(0, S), rnd.randint(0, S), rnd.randint(14, 30)
            d.ellipse((x - r, y - r, x + r, y + r), fill=tuple(c // 2 for c in base))
    return tex.filter(ImageFilter.GaussianBlur(1.5))


def planet(name, size=64, ring_glow=True):
    real = wiki("planet", "Fastoon" if name == "Fastoon (Final)" else name)
    if real:
        if name == "Fastoon (Final)":  # même planète, ambiance de fin (rouge)
            r_, g_, b_, a_ = real.split()
            real = Image.merge("RGBA", (r_.point(lambda v: min(255, int(v * 1.25))), g_.point(lambda v: int(v * 0.6)),
                                        b_.point(lambda v: int(v * 0.45)), a_))
        real.thumbnail((size, size), Image.LANCZOS)
        out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        out.paste(real, ((size - real.width) // 2, (size - real.height) // 2), real)
        return out
    base, c2, style, ring = PLANET_LOOK.get(name, ((120, 160, 220), (220, 230, 255), "bands", False))
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    if style == "asteroids":
        rnd = random.Random(5)
        d = ImageDraw.Draw(img)
        for _ in range(9):
            x, y, r = rnd.randint(50, 206), rnd.randint(60, 196), rnd.randint(10, 30)
            pts = [(x + r * rnd.uniform(0.7, 1.1) * math.cos(k * 0.8), y + r * rnd.uniform(0.7, 1.1) * math.sin(k * 0.8))
                   for k in range(8)]
            d.polygon(pts, fill=base + (255,), outline=c2 + (255,))
        return img.resize((size, size), Image.LANCZOS)
    if style == "stars":
        d = ImageDraw.Draw(img)
        rnd = random.Random(9)
        for _ in range(7):
            x, y, r = rnd.randint(60, 196), rnd.randint(60, 196), rnd.randint(8, 22)
            col = rnd.choice([base, c2, (255, 255, 255)])
            d.polygon([(x, y - r * 2), (x + r * 0.4, y - r * 0.4), (x + r * 2, y), (x + r * 0.4, y + r * 0.4), (x, y + r * 2),
                       (x - r * 0.4, y + r * 0.4), (x - r * 2, y), (x - r * 0.4, y - r * 0.4)], fill=col + (255,))
        img = Image.alpha_composite(img.filter(ImageFilter.GaussianBlur(6)), img)
        return img.resize((size, size), Image.LANCZOS)
    if style == "hole":
        d = ImageDraw.Draw(img)
        for k in range(12):
            d.ellipse((20 + k * 2, 92 + k, 236 - k * 2, 164 - k), outline=c2 + (255 - k * 18,), width=3)
        img = img.filter(ImageFilter.GaussianBlur(3))
        d = ImageDraw.Draw(img)
        d.ellipse((84, 84, 172, 172), fill=(0, 0, 0, 255), outline=c2 + (255,), width=4)
        return img.resize((size, size), Image.LANCZOS)
    r = 96
    tex = _texture(base, c2, style, sum(name.encode()))
    sphere = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    sp, tp = sphere.load(), tex.load()
    for y in range(S):
        for x in range(S):
            dx, dy = (x - 128) / r, (y - 128) / r
            d2 = dx * dx + dy * dy
            if d2 <= 1:
                z = math.sqrt(1 - d2)
                u = int(128 + dx / (z + 0.6) * 90) % S  # léger effet de sphère sur la texture
                v = int(128 + dy / (z + 0.6) * 90) % S
                light = max(0.0, -dx * 0.55 - dy * 0.55 + z * 0.75)
                k = 0.18 + 1.0 * light
                rim = max(0.0, 1 - z) ** 3 * 0.8
                col = tp[u, v]
                sp[x, y] = (min(255, int(col[0] * k + 120 * rim)), min(255, int(col[1] * k + 180 * rim)),
                            min(255, int(col[2] * k + 255 * rim)), 255)
    if ring:
        back, front = Image.new("RGBA", (S, S), (0, 0, 0, 0)), Image.new("RGBA", (S, S), (0, 0, 0, 0))
        for layer, (a0, a1) in ((back, (180, 360)), (front, (0, 180))):
            ImageDraw.Draw(layer).arc((8, 96, 248, 160), a0, a1, fill=tuple(min(255, c + 60) for c in c2) + (230,), width=10)
        img = Image.alpha_composite(img, back)
        img = Image.alpha_composite(img, sphere)
        img = Image.alpha_composite(img, front)
    else:
        img = Image.alpha_composite(img, sphere)
    return img.resize((size, size), Image.LANCZOS)


def planet_icon(name, size=64):
    """Planète dans un cadre métal rond (grille Planets)."""
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((4, 4, 252, 252), fill=(30, 32, 36, 255))
    d.ellipse((12, 12, 244, 244), fill=(88, 92, 100, 255))
    d.ellipse((26, 26, 230, 230), fill=(10, 14, 24, 255), outline=(40, 160, 255, 255), width=4)
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        x, y = 128 + 108 * math.cos(a), 128 + 108 * math.sin(a)
        d.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(150, 155, 165, 255), outline=(25, 25, 30, 255))
    p = planet(name, 200)
    img.paste(p, (28, 28), p)
    return img.resize((size, size), Image.LANCZOS)
