"""
Monde Archipelago : Ratchet & Clank Future: Tools of Destruction (PS3, RPCS3), disque EU BCES00052 01.00.

v0.3 (2026-10-15) : planètes aléatoires. Le client (client/) tourne dans le Launcher d'Archipelago et parle au jeu
par le serveur IPC de RPCS3 (PINE, port 28012) ; il faut le patch RPCS3 v0.6 (patch/BCES00052_patch.yml du projet) :
messages, carte galactique ouverte depuis n'importe où, voyages forcés interceptés, Clank retiré / remis.
"""
from typing import Any

from BaseClasses import Item, ItemClassification, Location, Region
from worlds.AutoWorld import WebWorld, World
from worlds.LauncherComponents import Component, components, icon_paths, launch_subprocess, Type

from .data import (ARMOR_COUNT, CLANK_COUNT, DEVICE_POOL, FILLER, FILLERS, GADGET_ITEMS, GAME, ITEMS, LOCATIONS,
                   OBJ_ITEMS, PLANETS, SPACE_COMBATS, WEAPON_ITEMS, FINAL_REGION)
from .options import ToDOptions

CLIENT_VERSION = "0.9.1.0"
FINAL_PLANETS = ("Igliak",)  # jamais au départ (fin du jeu ; Fastoon final = niveau 18, région de l'objectif)


def run_client(*args: Any) -> None:
    from .client.client import launch
    launch_subprocess(launch, name="ToDClient")


components.append(Component("Ratchet & Clank: Tools of Destruction Client", func=run_client,
                            component_type=Type.CLIENT, icon="tod_icon",
                            description="Client for Ratchet & Clank Future: Tools of Destruction (RPCS3)"))
icon_paths["tod_icon"] = f"ap:{__name__}/images/tod_icon.png"


class ToDItem(Item):
    game = GAME


class ToDLocation(Location):
    game = GAME


class ToDWeb(WebWorld):
    theme = "partyTime"


CLASSIFICATION = {"progression": ItemClassification.progression, "useful": ItemClassification.useful,
                  "filler": ItemClassification.filler}


class ToDWorld(World):
    """Ratchet and Clank team up again to fight Emperor Tachyon across the Polaris Galaxy."""
    game = GAME
    web = ToDWeb()
    options_dataclass = ToDOptions
    options: ToDOptions
    item_name_to_id = {name: d.id for name, d in ITEMS.items()}
    location_name_to_id = {name: d.id for name, d in LOCATIONS.items()}

    def generate_early(self) -> None:
        levels = {p.level: name for name, p in PLANETS.items()}
        choice = self.options.starting_planet.value
        if choice in levels and levels[choice] not in FINAL_PLANETS:
            self.start_planet = levels[choice]
        else:  # au hasard parmi les k premières planètes de l'histoire, k selon la difficulté (comme le balancing)
            order = [n for n in sorted(PLANETS, key=lambda n: PLANETS[n].level) if n not in FINAL_PLANETS]
            k = 2 + round(self.options.starting_planet_difficulty.value / 99 * (len(order) - 2))
            self.start_planet = self.random.choice(order[:k])
        self.multiworld.push_precollected(self.create_item(self.start_planet))
        self.devices: list[str] = []
        self.weapons: list[str] = list(WEAPON_ITEMS)

    def create_item(self, name: str) -> ToDItem:
        d = ITEMS[name]
        return ToDItem(name, CLASSIFICATION[d.classification], d.id, self.player)

    def create_regions(self) -> None:
        menu = Region("Menu", self.player, self.multiworld)
        self.multiworld.regions.append(menu)
        regions = {"Menu": menu}
        for name in PLANETS:
            r = Region(name, self.player, self.multiworld)
            self.multiworld.regions.append(r)
            regions[name] = r
            menu.connect(r, f"Travel to {name}", lambda state, n=name: state.has(n, self.player))
        for name, c in SPACE_COMBATS.items():  # 1er passage imposé avec la planète liée, puis rejouable avec l'objet
            r = Region(name, self.player, self.multiworld)
            self.multiworld.regions.append(r)
            regions[name] = r
            menu.connect(r, f"Fly to {name}",
                         lambda state, n=name, pl=c.planet: state.has_any((n, pl), self.player))
        # Fastoon final (niveau 18) : le client l'ouvre quand toutes les planètes sont reçues et que Gold Bolts Required
        # boulons d'or sont trouvés (tous accessibles avec la règle ci-dessous) ; points globaux en logique de fin aussi.
        final = Region(FINAL_REGION, self.player, self.multiworld)
        self.multiworld.regions.append(final)
        regions[FINAL_REGION] = final
        menu.connect(final, "Travel to Fastoon (Final)",
                     lambda state: (state.has_all(list(PLANETS) + GADGET_ITEMS, self.player)
                                    and state.has("Progressive Clank", self.player, 2)))
        self.location_count = 0
        for name, d in LOCATIONS.items():
            if d.kind == "level" and d.value > self.options.player_levels.value:
                continue
            self.location_count += 1
            r = regions[d.region]
            loc = ToDLocation(self.player, name, d.id, r)
            # Clank (planer) pour explorer : missions, points, boulons d'or, statues ; pas pour l'arrivée ni les vendeurs
            explore = d.kind in ("mission", "skill", "gold_bolt", "statue", "holoplan") and d.region in PLANETS
            needs = tuple(d.needs) + (("Progressive Clank",) if explore else ())
            if needs:
                loc.access_rule = lambda state, needs=needs: state.has_all(needs, self.player)
            if d.kind == "leviathan":  # ~1 à 3 Léviathans par planète : k-ième = au moins k planètes
                loc.access_rule = lambda state, k=d.value: state.has_from_list(list(PLANETS), self.player, k)
            if d.kind == "level":  # niveau k : environ k / 4 planètes (le départ compte)
                loc.access_rule = lambda state, k=(d.value + 3) // 4: state.has_from_list(list(PLANETS), self.player, k)
            r.locations.append(loc)
        # Objectif : battre Tachyon sur Fastoon final.
        goal = ToDLocation(self.player, "Defeat Emperor Tachyon", None, final)
        goal.place_locked_item(ToDItem("Victory", ItemClassification.progression, None, self.player))
        final.locations.append(goal)

    def create_items(self) -> None:
        names = [n for n in PLANETS if n != self.start_planet] + list(SPACE_COMBATS)
        names += ["Progressive Clank"] * CLANK_COUNT + GADGET_ITEMS + OBJ_ITEMS
        names += ["Progressive Armor"] * ARMOR_COUNT
        room = self.location_count - len(names) - len(self.weapons)
        if room < 0:  # trop d'objets : des armes restent hors du pool (gérées normalement par le jeu)
            self.weapons = self.weapons[:room]
        names += self.weapons
        if self.options.device_unlocks and self.location_count - len(names) >= len(DEVICE_POOL):
            self.devices = list(DEVICE_POOL)
            names += self.devices
        pool = [self.create_item(n) for n in names]
        pool += [self.create_item(self.get_filler_item_name()) for _ in range(self.location_count - len(pool))]
        self.multiworld.itempool += pool

    def set_rules(self) -> None:
        self.multiworld.completion_condition[self.player] = lambda state: state.has("Victory", self.player)

    def get_filler_item_name(self) -> str:
        return self.random.choice(FILLERS)

    def fill_slot_data(self) -> dict[str, Any]:
        return {"client_version": CLIENT_VERSION, "death_link": bool(self.options.death_link.value),
                "start_level": PLANETS[self.start_planet].level,
                "planets": True,                                            # v0.3 : planètes gérées par le client
                "locked_devices": [ITEMS[n].value for n in self.devices],  # dispositifs verrouillés tant que non reçus
                "managed_gadgets": [ITEMS[n].value for n in GADGET_ITEMS],
                "managed_objs": [ITEMS[n].value for n in OBJ_ITEMS],
                "managed_weapons": [ITEMS[n].value for n in self.weapons],
                "clank": True,
                "goal": "tachyon", "gold_bolts_required": self.options.gold_bolts_required.value}
