"""
Données du monde Ratchet & Clank : Opération Destruction (Tools of Destruction), BCES00052 01.00.

v0.3 (2026-10-15) : planètes aléatoires (objets « planète », départ sur n'importe quelle planète, voyages forcés
interceptés par le patch v0.6), Clank progressif, Ailorobot et Gélanator.
v0.4 (2026-10-15) : tous les gadgets en objets (+ Super-bottes), combats spatiaux rejouables (objets), checks : boulons
d'or (bits), points de compétence (bits), missions (comptées par planète), statues de Tachyon. Logique de base,
volontairement prudente (à affiner en jouant). Adresses : NOTES.md du projet ; contenu : INVENTAIRE.md ; décisions :
PLAN.md (section 10).
"""
from typing import NamedTuple, Optional

GAME = "Ratchet and Clank Tools of Destruction"  # sans « : » (il casse le YAML des joueurs)
BASE_ID = 0x7A0D0000


class Planet(NamedTuple):
    level: int                # numéro du niveau du jeu (table 0x101F03A8 + n * 0x408, set_level, load_level)
    fr: str
    space_combat: int = -1    # combat spatial que le jeu impose avant la 1re visite (load_level), à autoriser aussi


# Numéros du jeu = ordre de l'histoire sans Nundac (qui fait partie d'Apogée) ; 0 = Kerwan (départ du jeu, jamais
# autorisée), 19 = carte galactique. Fastoon (retour, final) = 18 : pas encore géré (objectif futur).
PLANETS: dict[str, Planet] = {
    "Cobalia": Planet(1, "Cobalia"),
    "Kortog": Planet(2, "Kortog"),
    "Fastoon": Planet(3, "Fastoon"),
    "Mukow": Planet(5, "Mukow", 4),
    "Apogee Space Station": Planet(6, "Anneau de Nundac (station Apogée)"),  # nom sur la carte : Nundac
    "Ardolis": Planet(7, "Ardolis"),
    "Rykan V": Planet(9, "Rykan V", 8),
    "Sargasso": Planet(10, "Sargasso"),
    "Kreeli Comet": Planet(11, "Comète Kreeli"),
    "Viceron": Planet(12, "Viceron"),
    "Jasindu": Planet(14, "Jasindu", 13),
    "Ublik Passage": Planet(15, "Passage Ublik"),
    "Reepor": Planet(16, "Reepor"),
    "Igliak": Planet(17, "Igliak"),
}
LEVEL_TO_PLANET = {p.level: name for name, p in PLANETS.items()}


class SpaceCombat(NamedTuple):
    level: int
    fr: str
    planet: str               # planète dont la 1re visite passe par ce combat (autorisé avec elle)


# Combats spatiaux : rejouables par la carte une fois débloqués (validé : Voron visible après la bataille). Objet =
# rendu visible sur la carte pour le refaire ; 1er passage imposé par le jeu en allant sur la planète liée.
SPACE_COMBATS: dict[str, SpaceCombat] = {
    "Voron Asteroid Belt": SpaceCombat(4, "Ceinture de Voron", "Mukow"),
    "Rakar Star Cluster": SpaceCombat(8, "Amas de Rakar", "Rykan V"),
    "Verdigris Black Hole": SpaceCombat(13, "Trou noir de Verdigris", "Jasindu"),
}

# Logique de base, PRUDENTE (jamais fausse, parfois trop stricte) : ce qu'il faut pour les missions, points de
# compétence et statues d'une planète (en plus de la planète et de Clank). Sources : INVENTAIRE.md, wiki, tests.
REGION_NEEDS: dict[str, tuple] = {
    "Cobalia": ("Gelanator",),
    "Kortog": ("Robo-Wings",),
    "Fastoon": (),
    "Mukow": ("Heli-Pods",),
    "Apogee Space Station": (),
    "Ardolis": ("Heli-Pods", "Geo-Laser"),
    "Rykan V": ("Gyro-Cycle",),
    "Sargasso": ("Robo-Wings",),
    "Kreeli Comet": ("Holo-Pirate Disguise", "Geo-Laser"),
    "Viceron": ("Heli-Pods", "Decryptor"),
    "Jasindu": (),
    "Ublik Passage": ("Heli-Pods",),
    "Reepor": ("Heli-Pods", "Geo-Laser"),
    "Igliak": (),
}
# Boulons d'or (wiki « Tools of Destruction gold bolt locations ») : nombre par niveau et gadgets de TOUS les boulons de
# la planète (on ne sait pas encore quel bit est quel boulon : chaque boulon demande l'union, prudent).
GOLD_BOLTS: dict[str, tuple[int, tuple]] = {
    "Cobalia": (1, ("Gelanator",)),
    "Kortog": (2, ("Robo-Wings", "Gelanator")),
    "Voron Asteroid Belt": (1, ()),
    "Mukow": (4, ("Geo-Laser", "Decryptor")),
    "Apogee Space Station": (1, ()),
    "Ardolis": (3, ("Heli-Pods", "Holo-Pirate Disguise")),
    "Rakar Star Cluster": (1, ()),
    "Rykan V": (2, ("Gyro-Cycle",)),
    "Sargasso": (4, ("Robo-Wings",)),
    "Kreeli Comet": (1, ("Holo-Pirate Disguise",)),
    "Viceron": (2, ("Heli-Pods", "Decryptor")),
    "Verdigris Black Hole": (1, ()),
    "Jasindu": (2, ()),
    "Ublik Passage": (2, ("Heli-Pods", "Gyro-Cycle")),
    "Reepor": (2, ("Heli-Pods",)),
    "Igliak": (2, ()),
}
# Missions comptées par planète (n-ième mission terminée sur la planète = check ; liste « terminées » du jeu).
# Nombre = missions de la 1re visite (wiki) MOINS la dernière (elle peut finir par un voyage forcé qu'on intercepte),
# sauf Fastoon (4 validées en jeu) et les combats spatiaux (1).
MISSIONS: dict[str, int] = {
    "Cobalia": 6, "Kortog": 4, "Fastoon": 4, "Mukow": 5, "Apogee Space Station": 4, "Ardolis": 2, "Rykan V": 5,
    "Sargasso": 4, "Kreeli Comet": 2, "Viceron": 2, "Jasindu": 4, "Ublik Passage": 1, "Reepor": 5, "Igliak": 3,
    "Voron Asteroid Belt": 1, "Rakar Star Cluster": 1, "Verdigris Black Hole": 1,
}
# Points de compétence (table du jeu, NOTES.md) : (numéro = bit, niveau, nom anglais). Globaux (44-59) et Fastoon
# final (34) exclus pour l'instant.
SKILL_POINTS: list[tuple[int, str, str]] = [
    # (bit, région, nom tiré de l'identifiant interne SKILLPOINT_<planète>_<nom> du jeu)
    (0, "Cobalia", "Smash"), (1, "Cobalia", "Barrel"), (2, "Cobalia", "Hunter"),
    (3, "Kortog", "Wrench"), (4, "Kortog", "Bridges"), (5, "Kortog", "Beasts"), (6, "Kortog", "Around"),
    (7, "Mukow", "Sick"), (8, "Mukow", "Fire"), (9, "Mukow", "Peep"),
    (10, "Apogee Space Station", "Alphabet"), (11, "Apogee Space Station", "Wrench"),
    (12, "Apogee Space Station", "Dancing"),
    (13, "Ardolis", "Medicine"), (14, "Ardolis", "Strike"), (15, "Ardolis", "Mutant"),
    (16, "Rykan V", "Consumer"), (17, "Rykan V", "Strong"), (18, "Rykan V", "Untouchable"),
    (19, "Sargasso", "Train"), (20, "Sargasso", "Examiner"), (21, "Sargasso", "Extinction"),
    (22, "Kreeli Comet", "Cold"), (23, "Kreeli Comet", "Turrets"), (24, "Kreeli Comet", "Wrench"),
    (25, "Viceron", "Dancing"), (26, "Viceron", "Seared"),
    (27, "Jasindu", "Aim"), (28, "Jasindu", "Fire"), (29, "Ublik Passage", "Salute"), (30, "Reepor", "Catch"),
    (31, "Igliak", "Strafe"), (32, "Igliak", "Boarding"), (33, "Igliak", "Flying"),
    (35, "Voron Asteroid Belt", "Collector"), (36, "Voron Asteroid Belt", "Minesweeper"), (37, "Voron Asteroid Belt", "Roll"),
    (38, "Rakar Star Cluster", "Battleship"), (39, "Rakar Star Cluster", "Pretty"), (40, "Rakar Star Cluster", "Boss"),
    (41, "Verdigris Black Hole", "Marksman"), (42, "Verdigris Black Hole", "Touch"), (43, "Verdigris Black Hole", "Pyoo"),
]
# Prérequis propres à un point de compétence (en plus de sa planète) : wiki des boulons d'or / tests.
SKILL_NEEDS: dict[int, tuple] = {9: ("Geo-Laser",)}  # Mukow « One Heckuva Peephole » : mur au Géo-laser
STATUES = 6  # statues de Tachyon de Mukow (« Trail of Turning Terror »), compteur OBJ n° 15


class ItemDef(NamedTuple):
    id: int
    kind: str          # "weapon", "armor", "bolts", "raritanium", "device_unlock", "gadget", "obj", "planet", "clank"
    value: int         # fiche (arme, gadget, dispositif), index OBJ_, niveau du jeu (planète), nombre (boulons...)
    classification: str  # "progression", "useful", "filler"
    fr: str


# Les noms d'Archipelago sont en anglais (vus par tous les joueurs) ; « fr » = nom affiché en jeu.
ITEMS: dict[str, ItemDef] = {
    # Armes (value = fiche ; possédée en jeu <=> reçue). 0x03 et 0x07 sont données par l'histoire, les autres vendues.
    "Shock Ravager": ItemDef(BASE_ID + 0x03, "weapon", 0x03, "useful", "Ravageur assommant"),
    "Tornado Launcher": ItemDef(BASE_ID + 0x04, "weapon", 0x04, "useful", "Lance-tornade"),
    "Buzz Blades": ItemDef(BASE_ID + 0x05, "weapon", 0x05, "useful", "Discozigzag"),
    "Predator Launcher": ItemDef(BASE_ID + 0x06, "weapon", 0x06, "useful", "Lance-prédateurs"),
    "Alpha Disruptor": ItemDef(BASE_ID + 0x07, "weapon", 0x07, "useful", "Alpha-dérangeur"),
    "Pyro Blaster": ItemDef(BASE_ID + 0x08, "weapon", 0x08, "useful", "Pyro-foudroyeur"),
    "Plasma Beasts": ItemDef(BASE_ID + 0x09, "weapon", 0x09, "useful", "Monstres plasma"),
    "Shard Reaper": ItemDef(BASE_ID + 0x0A, "weapon", 0x0A, "useful", "Picapique"),
    "Negotiator": ItemDef(BASE_ID + 0x0B, "weapon", 0x0B, "useful", "Négociateur"),
    "Nano-Swarmers": ItemDef(BASE_ID + 0x0C, "weapon", 0x0C, "useful", "Nuée de nanos"),
    "Mag-Net Launcher": ItemDef(BASE_ID + 0x0D, "weapon", 0x0D, "useful", "Magnéto-filet"),
    "Razor Claws": ItemDef(BASE_ID + 0x0E, "weapon", 0x0E, "useful", "Griffeurs rasoir"),
    "Progressive Armor": ItemDef(BASE_ID + 0x100, "armor", 1, "useful", "Armure progressive"),
    "Bolts": ItemDef(BASE_ID + 0x200, "bolts", 10000, "filler", "10 000 boulons"),
    "Raritanium": ItemDef(BASE_ID + 0x201, "raritanium", 100, "filler", "100 Raritanium"),
    # Déblocages des dispositifs (option device_unlocks) : value = fiche ; le client met l'octet « en vente »
    # (0x101F5274 + fiche) à 0 tant que l'objet n'est pas reçu, à 1 ensuite (achat normal, sans check).
    "Mr. Zurkon Unlock": ItemDef(BASE_ID + 0x310, "device_unlock", 0x10, "useful", "Déblocage : M. Zurkon"),
    "Confuzzler Gas Unlock": ItemDef(BASE_ID + 0x311, "device_unlock", 0x11, "useful", "Déblocage : Gaz Confuzzlor"),
    "Death Springs Unlock": ItemDef(BASE_ID + 0x312, "device_unlock", 0x12, "useful", "Déblocage : Jets mortels"),
    "Groovitron Unlock": ItemDef(BASE_ID + 0x313, "device_unlock", 0x13, "useful", "Déblocage : Groovitron"),
    "Leech Bomb Unlock": ItemDef(BASE_ID + 0x314, "device_unlock", 0x14, "useful", "Déblocage : Bombe sangsue"),
    "Mega Leech Bomb Unlock": ItemDef(BASE_ID + 0x315, "device_unlock", 0x15, "useful", "Déblocage : Méga-bombe sangsue"),
    "Transmorpher Unlock": ItemDef(BASE_ID + 0x316, "device_unlock", 0x16, "useful", "Déblocage : Transmorphère"),
    "Visi-Copter Unlock": ItemDef(BASE_ID + 0x317, "device_unlock", 0x17, "useful", "Déblocage : Visi-coptère"),
    # Gadgets (value = fiche de la table des objets, possédé = octet +0x10 ; toutes validées dans le menu Gadgets).
    "Heli-Pods": ItemDef(BASE_ID + 0x418, "gadget", 0x18, "progression", "Héli-capsules"),
    "Geo-Laser": ItemDef(BASE_ID + 0x41A, "gadget", 0x1A, "progression", "Géo-laser"),
    "Gelanator": ItemDef(BASE_ID + 0x41B, "gadget", 0x1B, "progression", "Gélanator"),
    "Robo-Wings": ItemDef(BASE_ID + 0x41C, "gadget", 0x1C, "progression", "Ailorobot"),
    "Gyro-Cycle": ItemDef(BASE_ID + 0x41D, "gadget", 0x1D, "progression", "Gyro-Cycle"),
    "Holo-Pirate Disguise": ItemDef(BASE_ID + 0x41E, "gadget", 0x1E, "progression", "Déguisement holopirate"),
    "Decryptor": ItemDef(BASE_ID + 0x41F, "gadget", 0x1F, "progression", "Décrypteur"),
    # Objets OBJ_ (value = index : possédé = 0x101EFE24 + 4 * i et sa copie 0x101EFE80 + 4 * i).
    "Charge Boots": ItemDef(BASE_ID + 0x705, "obj", 5, "useful", "Super-bottes"),
    # Clank progressif : 1 = Clank sur le dos (Hélico-pack), 2 = Propulseur. Patch v0.6 (commandes 5 / 6) +
    # tableau OBJ_. L'hydro-pack reste donné d'office (pas encore bloquable).
    "Progressive Clank": ItemDef(BASE_ID + 0x500, "clank", 1, "progression", "Clank progressif"),
}
for _name, _p in PLANETS.items():
    ITEMS[_name] = ItemDef(BASE_ID + 0x600 + _p.level, "planet", _p.level, "progression", f"Planète : {_p.fr}")
for _name, _c in SPACE_COMBATS.items():
    ITEMS[_name] = ItemDef(BASE_ID + 0x600 + _c.level, "planet", _c.level, "useful", f"Combat spatial : {_c.fr}")

WEAPON_ITEMS = [n for n, d in ITEMS.items() if d.kind == "weapon"]
DEVICE_POOL = [n for n, d in ITEMS.items() if d.kind == "device_unlock"]
GADGET_ITEMS = [n for n, d in ITEMS.items() if d.kind == "gadget"]
OBJ_ITEMS = [n for n, d in ITEMS.items() if d.kind == "obj"]
CLANK_COUNT = 2
ARMOR_COUNT = 3   # Blackstar, Hélios, Terraflux (Trillium = mode Défi seulement)
FILLERS = ("Bolts", "Raritanium")
FILLER = "Bolts"


class LocDef(NamedTuple):
    id: int
    kind: str          # "vendor_weapon", "vendor_armor", "leviathan", "gold_bolt", "arrival", "skill", "mission", "statue", "level", "holoplan"
    value: int         # fiche, numéro d'armure, k-ième Léviathan / mission / statue, bit (boulon d'or, point), niveau
    region: str        # planète, combat spatial ou "Menu" (partout)
    needs: tuple = ()  # objets nécessaires en plus de la région (logique de base, à ajuster en jouant)
    level: int = -1    # niveau du jeu (boulons d'or, missions)


def _level(region: str) -> int:
    return PLANETS[region].level if region in PLANETS else SPACE_COMBATS[region].level


LOCATIONS: dict[str, LocDef] = {
    # Armes des vendeurs (achat = check) ; la planète est celle où l'arme est vendue dans le jeu normal : le client
    # la met en vente (octet 0x101F5274 + fiche) dès que la planète est reçue, chez tous les vendeurs.
    "Cobalia: Plasma Beasts (Weapon Vendor)": LocDef(BASE_ID + 0x1000, "vendor_weapon", 0x09, "Cobalia"),
    "Cobalia: Tornado Launcher (Weapon Vendor)": LocDef(BASE_ID + 0x1001, "vendor_weapon", 0x04, "Cobalia"),
    "Kortog: Predator Launcher (Weapon Vendor)": LocDef(BASE_ID + 0x1002, "vendor_weapon", 0x06, "Kortog"),
    "Mukow: Shard Reaper (Weapon Vendor)": LocDef(BASE_ID + 0x1003, "vendor_weapon", 0x0A, "Mukow"),
    "Ardolis: Buzz Blades (Weapon Vendor)": LocDef(BASE_ID + 0x1004, "vendor_weapon", 0x05, "Ardolis"),
    "Ardolis: Nano-Swarmers (Weapon Vendor)": LocDef(BASE_ID + 0x1005, "vendor_weapon", 0x0C, "Ardolis"),
    "Kreeli Comet: Pyro Blaster (Weapon Vendor)": LocDef(BASE_ID + 0x1006, "vendor_weapon", 0x08, "Kreeli Comet"),
    "Viceron: Negotiator (Weapon Vendor)": LocDef(BASE_ID + 0x1007, "vendor_weapon", 0x0B, "Viceron"),
    "Jasindu: Razor Claws (Weapon Vendor)": LocDef(BASE_ID + 0x1008, "vendor_weapon", 0x0E, "Jasindu"),
    "Ublik Passage: Mag-Net Launcher (Weapon Vendor)": LocDef(BASE_ID + 0x1009, "vendor_weapon", 0x0D, "Ublik Passage"),
    # Armures (achat = check, compté seulement vendeur ouvert).
    "Cobalia: Blackstar Armor (Armor Vendor)": LocDef(BASE_ID + 0x1100, "vendor_armor", 1, "Cobalia"),
    "Rykan V: Helios Armor (Armor Vendor)": LocDef(BASE_ID + 0x1101, "vendor_armor", 2, "Rykan V"),
    "Reepor: Terraflux Armor (Armor Vendor)": LocDef(BASE_ID + 0x1102, "vendor_armor", 3, "Reepor"),
    # Léviathans tués au total (0x101EFF1C) : il y en a sur presque toutes les planètes.
    "Leviathan #1": LocDef(BASE_ID + 0x1200, "leviathan", 1, "Menu"),
    "Leviathan #2": LocDef(BASE_ID + 0x1201, "leviathan", 2, "Menu"),
    "Leviathan #3": LocDef(BASE_ID + 0x1202, "leviathan", 3, "Menu"),
    "Leviathan #4": LocDef(BASE_ID + 0x1203, "leviathan", 4, "Menu"),
}
# Boulons d'or : bit k du u32 en 0x101F0394 + niveau * 0x408 (validé Cobalia, Voron, Mukow).
for _region, (_count, _needs) in GOLD_BOLTS.items():
    for _k in range(_count):
        LOCATIONS[f"{_region}: Gold Bolt {_k + 1}"] = LocDef(
            BASE_ID + 0x1300 + _level(_region) * 8 + _k, "gold_bolt", _k, _region, _needs, _level(_region))
# Fastoon final (niveau 18, région de l'objectif) : son boulon d'or (bit 0, même règle) et son point de compétence (34).
FINAL_REGION = "Fastoon (Final)"
LOCATIONS[f"{FINAL_REGION}: Gold Bolt 1"] = LocDef(BASE_ID + 0x1300 + 18 * 8, "gold_bolt", 0, FINAL_REGION, (), 18)
LOCATIONS[f"{FINAL_REGION}: Skill Point - Hide"] = LocDef(BASE_ID + 0x1500 + 34, "skill", 34, FINAL_REGION)
# Points de compétence globaux (niveau 19 de la table du jeu) : seulement ceux faisables sans mode défi ni holoplans,
# placés en logique de fin de partie (même règle que Fastoon final). Exclus : ARSENAL, GOLDEN, RYNO, WEAPONS (tout
# acheter / améliorer), CHALLENGE, HARDCORE (mode défi), DANCE, CHORUS, HAPPY, DISCO (Groovitron, dispositif verrouillable).
GLOBAL_SKILLS = [(45, "Roflcopter"), (47, "Cheapskate"), (52, "Souls"), (53, "Penguins"), (55, "Items"), (56, "Gadgets")]
for _bit, _name in GLOBAL_SKILLS:
    LOCATIONS[f"Skill Point - {_name}"] = LocDef(BASE_ID + 0x1500 + _bit, "skill", _bit, FINAL_REGION)
# Holoplans du T.E.L.T. IV (2026-10-16, Kortog validé en jeu : 0x101F8214 0 -> 4) : bit (numéro du niveau) du u32 en
# 0x101F8214. Prérequis : wiki « Tools of Destruction holo-plan locations » (INVENTAIRE.md §7).
HOLOPLANS: dict[str, tuple] = {
    "Kortog": ("Robo-Wings",), "Mukow": (), "Apogee Space Station": (), "Ardolis": ("Heli-Pods",),
    "Rykan V": ("Heli-Pods",), "Sargasso": ("Robo-Wings",), "Kreeli Comet": (), "Viceron": (), "Jasindu": (),
    "Ublik Passage": (), "Reepor": (), "Igliak": (), FINAL_REGION: (),
}
for _region, _needs in HOLOPLANS.items():
    _lv = 18 if _region == FINAL_REGION else _level(_region)
    LOCATIONS[f"{_region}: Holo-Plan"] = LocDef(BASE_ID + 0x1A00 + _lv, "holoplan", _lv, _region,
                                                REGION_NEEDS.get(_region, ()) + _needs)
# Arriver sur une planète = check (octet « visitée » +1 de la table des niveaux, mis par le jeu à l'arrivée).
for _name, _p in PLANETS.items():
    LOCATIONS[f"{_name}: Arrival"] = LocDef(BASE_ID + 0x1400 + _p.level, "arrival", _p.level, _name)
# Points de compétence : bit i du u64 en 0x101F8230 (validé : Radin = 47, Démineur = 36).
for _bit, _region, _name in SKILL_POINTS:
    LOCATIONS[f"{_region}: Skill Point - {_name}"] = LocDef(
        BASE_ID + 0x1500 + _bit, "skill", _bit, _region, REGION_NEEDS.get(_region, ()) + SKILL_NEEDS.get(_bit, ()))
# Missions : n-ième mission terminée sur le niveau (compte de la liste « terminées » 0x10200618 + niveau * 0x7C).
for _region, _count in MISSIONS.items():
    for _k in range(1, _count + 1):
        LOCATIONS[f"{_region}: Mission {_k}"] = LocDef(
            BASE_ID + 0x1600 + _level(_region) * 16 + _k, "mission", _k, _region, REGION_NEEDS.get(_region, ()),
            _level(_region))
# Niveaux de Ratchet (2026-10-16) : chaque niveau donne +1 de vie max ([0x10724C34] + 0x75C, f32) ; niveau k = vie max
# >= BASE_HP + k. Combien sont des checks : option Player Levels. Logique : 1 planète de plus tous les 4 niveaux.
BASE_HP, MAX_LEVEL_CHECKS = 10, 50
for _k in range(1, MAX_LEVEL_CHECKS + 1):
    LOCATIONS[f"Ratchet Level {_k + 1}"] = LocDef(BASE_ID + 0x1900 + _k, "level", _k, "Menu")
# Statues de Tachyon de Mukow (compteur OBJ n° 15).
for _k in range(1, STATUES + 1):
    LOCATIONS[f"Mukow: Tachyon Statue {_k}"] = LocDef(BASE_ID + 0x1800 + _k, "statue", _k, "Mukow")

ITEM_BY_ID = {d.id: name for name, d in ITEMS.items()}
LOCATION_BY_ID = {d.id: name for name, d in LOCATIONS.items()}


def item_fr(name: Optional[str]) -> str:
    return ITEMS[name].fr if name in ITEMS else (name or "?")
