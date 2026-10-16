"""
Interface avec le jeu (RPCS3 par PINE) : checks, dons d'objets, vendeurs, messages.

Reprend les prototypes validés en jeu le 2026-10-13/14 (tools/vendor_proto.py, tools/mailbox.py) ;
adresses et pièges : NOTES.md du projet.

Règles :
- Arme gérée (= objet Archipelago de ce monde) : possédée en jeu <=> reçue d'Archipelago. Les autres armes
  ne sont pas touchées.
- Vendeur d'armes ouvert (0x1072260C = 1) : arme dont le check d'achat n'est pas fait = montrée non possédée
  (en vente, même reçue) ; check fait = montrée possédée (plus de rachat). Nouvelle arme dans la liste =
  achat = check. À la fermeture, retour à la règle normale (fiche d'avant remise : expérience, niveau).
- Armure gérée (avec un check de vendeur) : possédée en jeu <=> check fait ; armure portée = la meilleure
  reçue (armure progressive), pendant le menu la meilleure achetée et reçue.
- v0.3 (2026-10-15), planètes aléatoires (patch v0.6) : planètes reçues = visibles sur la carte et autorisées par le
  filtre de set_level (masque en boîte +0x20 ; les autres cachées et bloquées : la carte s'ouvre à la place) ; nouvelle
  partie = téléportation vers la planète de départ (carte ouverte par la commande 4, puis load_level par la commande 2) ;
  arrivée sur une planète = check ; armes des vendeurs en vente dès que leur planète est reçue ; Clank progressif
  (commandes 5 / 6 du patch, propulseur dans le tableau OBJ_).
"""
import struct
import time
from typing import Optional

from .pine import Pine, READ8, WRITE8
from ..data import BASE_HP, ITEMS, LOCATIONS, PLANETS

GAME_ID, GAME_VERSION = "BCES00052", "01.00"

VENDOR_OPEN = 0x1072260C
WEAPONS, WSIZE = 0x101EFB20, 0x14
OWNED_LIST, LIST_LEN = 0x101EFDA4, 0x20
EMPTY = 0xFFFFFFFF
ARMOR_OWNED, ARMOR_COUNT, ARMOR_WORN = 0x101EFF64, 5, 0x101EFF78
HELD = 0x101EFF4C
HERO_PTR = 0x10724C34
SWITCH_REQ = 0xF14
BOLTS, RARITANIUM = 0x101EFF3C, 0x101EFF40
LEVIATHANS = 0x101EFF1C
FOR_SALE = 0x101F5274          # + fiche : octet « en vente » (0 = absent des vendeurs), remis par le jeu au chargement

# Clank (2026-10-14, Kortog) : objet du jeu au tas, retrouvé par son objet de comportement (unique, vtable 0x8519A8,
# pointeur de retour vers Clank en +0x14). Mot d'affichage Clank +0x11C : 0x80 = Clank normal, 0x40 = ailes de
# l'Ailorobot (0x91 normal, 0x51 sur une plateforme de lancement). Remettre 0x80 cache les ailes (validé en jeu).
CLANK_VTABLE, CLANK_MASK, CLANK_WINGS, CLANK_NORMAL = 0x8519A8, 0x11C, 0x40, 0x80
CLANK_WINDOW = (-0x400000, 0x1400000)  # recherche de Clank autour de l'objet de Ratchet (le tas bouge selon la planète)
ROBO_WINGS = 0x1C

# Planètes (2026-10-15) : table des niveaux (fiche n : +0 visible sur la carte, +1 visitée), état des niveaux G
# (+0x50 = objet carte galactique ouverte), objet de comportement de Ratchet = [HERO_PTR] - 0x102C (classe 0x211,
# +0x21B0 = poignée de Clank, 0 sans Clank ; chaque objet du jeu a sa poignée en +0x64).
LEVELS, LEVEL_STRIDE, FINAL_LEVEL = 0x101F03A8, 0x408, 18
LEVEL_STATE = 0x101AFCE0
RATCHET_OFS, RATCHET_CLASS, CLANK_HANDLE = 0x102C, 0x211, 0x21B0
OBJ, OBJ2, OBJ_THRUSTER, OBJ_STATUES = 0x101EFE24, 0x101EFE80, 1, 15   # objets OBJ_ du joueur (+ 4 * i), 2 copies
HOLOPLANS = 0x101F8214                                # holoplan de la planète n = bit n (validé sur Kortog)
GOLD_BOLTS, SKILLS = 0x101F0394, 0x101F8230           # boulon d'or k du niveau n = bit k de [GOLD_BOLTS + n * 0x408] ;
#                                                       point de compétence i = bit i du u64 big-endian en SKILLS
MISSIONS_DONE, MISSIONS_STRIDE = 0x10200618, 0x7C     # missions terminées du niveau n (compte en +0x78)
FIND_TACHYON = 0x27E                                  # Fastoon final : mission « Find Tachyon » terminée = combat final
#                                                       lancé (validé le 2026-10-16 ; liste terminées : fiches de 12 octets,
#                                                       +0 numéro ; la mort de Tachyon ne termine aucune mission)
TACHYON_DEAD = ((0x101F5058, 0x00400000), (0x101F820C, 0x20))  # bits allumés à la mort de Tachyon (2026-10-16, en jeu)
GOLD_BOLT_LOCS = {d.id for d in LOCATIONS.values() if d.kind == "gold_bolt"}
SCAN_EVERY = 0.5
PACK, PACK_FLAG = 0x101EFF5C, 0x101EFF58              # pack de Clank équipé (0 hélico, 1 propulseur, 2 hydro)
HOOK2 = 0x8C0000                                      # 1re instruction du crochet de set_level (patch >= v0.4)

MAILBOX = 0x7F000000           # patch RPCS3 : +4 compteur d'images, +0x10 demande, +0x14 durée, +0x18 argument,
#                                +0x20 masque des niveaux autorisés, +0x100 texte. Demandes : 1 message, 2 load_level,
#                                4 ouvrir la carte, 5 retirer Clank, 6 remettre Clank.
CMD_LOAD_LEVEL, CMD_MAP, CMD_CLANK_OFF, CMD_CLANK_ON = 2, 4, 5, 6
COLOR_ON, COLOR_OFF = "", ""

V02_WEAPONS = [0x03, 0x04, 0x09]  # armes gérées par les seeds v0.2 (sans « managed_weapons » dans le slot data)
LEVEL_OF_PLANET = {name: p.level for name, p in PLANETS.items()}
LEVEL_OF_ITEM = {name: d.value for name, d in ITEMS.items() if d.kind == "planet"}  # planètes + combats spatiaux
SPACE_LEVELS = {d.value for d in ITEMS.values() if d.kind == "planet"} - set(LEVEL_OF_PLANET.values())
SCANNED = [d for d in LOCATIONS.values() if d.kind in ("gold_bolt", "skill", "mission", "statue", "level", "holoplan")]
SPACE_COMBAT = {p.level: p.space_combat for p in PLANETS.values() if p.space_combat >= 0}
WEAPON_PLANET = {d.value: d.region for d in LOCATIONS.values() if d.kind == "vendor_weapon"}
ARRIVAL_LOC = {d.value: d.id for d in LOCATIONS.values() if d.kind == "arrival"}
VENDOR_WEAPON_LOC = {d.value: d.id for d in LOCATIONS.values() if d.kind == "vendor_weapon"}
VENDOR_ARMOR_LOC = {d.value: d.id for d in LOCATIONS.values() if d.kind == "vendor_armor"}


class GameError(Exception):
    pass


class Game:
    def __init__(self, log):
        self.log = log
        self.p: Optional[Pine] = None
        self.vendor_open = False
        self.seen: list[int] = []
        self.saved: dict[int, bytes] = {}       # fiches des armes retirées par le client (expérience, niveau)
        self.held_before = EMPTY
        self.bought: set[int] = set()           # checks d'achat vus, pas encore confirmés par le serveur
        self.msg_queue: list[tuple[str, float]] = []
        self.msg_until = 0.0
        self.patch_ok: Optional[bool] = None
        self.clank_beh = 0                      # objet de comportement de Clank (0 = à chercher)
        self.clank_retry = 0.0
        self.cfg: dict = {}                     # slot data (planètes, gadgets, armes gérées...)
        self.managed_weapons: set[int] = set(V02_WEAPONS)
        self.hook2: Optional[bool] = None       # crochet de set_level présent (patch >= v0.4)
        self.warp = ("idle", 0.0)               # téléportation de départ : idle / carte / voyage
        self.clank_cmd_time = 0.0
        self.scan_time = 0.0
        self.goal_done = False

    # --- connexion -------------------------------------------------------------------------------
    def connect(self) -> None:
        p = Pine()
        gid, ver = p.text(0xC).strip(), p.text(0xE).strip()
        if gid != GAME_ID or ver != GAME_VERSION:
            raise GameError(f"jeu {gid} {ver} : il faut {GAME_ID} version {GAME_VERSION} (disque EU, sans mise à jour)")
        self.p = p
        self.patch_ok = None

    @property
    def connected(self) -> bool:
        return self.p is not None

    def drop(self) -> None:
        if self.p:
            try:
                self.p.sock.close()
            except OSError:
                pass
        self.p = None
        self.vendor_open = False
        self.clank_beh = 0
        self.hook2 = None
        self.warp = ("idle", 0.0)

    def in_game(self) -> bool:
        return self.p.read(HERO_PTR) != 0

    # --- outils mémoire ---------------------------------------------------------------------------
    def read_list(self) -> list[int]:
        raw = self.p.read_block(OWNED_LIST, 4 * LIST_LEN)
        return [w for w in struct.unpack(f">{LIST_LEN}I", raw) if w != EMPTY]

    def write_list(self, ids: list[int]) -> None:
        for i in range(LIST_LEN):
            self.p.write(OWNED_LIST + 4 * i, ids[i] if i < len(ids) else EMPTY)

    def owned(self, w: int) -> bool:
        return self.p.read(WEAPONS + w * WSIZE + 0x10, READ8) != 0

    def set_owned(self, w: int, on: bool) -> None:
        self.p.write(WEAPONS + w * WSIZE + 0x10, 1 if on else 0, WRITE8)

    def fiche(self, w: int) -> bytes:
        return self.p.read_block(WEAPONS + w * WSIZE, 0x18)[:WSIZE]

    def restore_fiche(self, w: int, data: bytes) -> None:
        ammo = self.p.read(WEAPONS + w * WSIZE + 8)
        for k in range(0, WSIZE, 4):
            self.p.write(WEAPONS + w * WSIZE + k, int.from_bytes(data[k:k + 4], "big"))
        # garder les munitions du jeu si elles sont plus hautes (f32 positifs : comparables en entiers)
        self.p.write(WEAPONS + w * WSIZE + 8, max(ammo, int.from_bytes(data[8:12], "big")))

    def give_weapon(self, w: int, lst: list[int]) -> None:
        if w in self.saved:
            self.restore_fiche(w, self.saved.pop(w))
        self.set_owned(w, True)
        if w not in lst:
            lst.append(w)

    def take_weapon(self, w: int, lst: list[int]) -> None:
        if self.owned(w):
            self.saved[w] = self.fiche(w)
        self.set_owned(w, False)
        if w in lst:
            lst.remove(w)

    # --- boucle -----------------------------------------------------------------------------------
    def configure(self, slot_data: dict) -> None:
        self.cfg = slot_data
        self.managed_weapons = set(slot_data.get("managed_weapons", V02_WEAPONS))

    def tick(self, received: dict[str, int], checked: set[int]) -> set[int]:
        """Un tour (~10 par seconde). Renvoie les locations nouvellement faites."""
        new: set[int] = set()
        if not self.in_game():
            return new
        self.apply_devices(received, self.cfg.get("locked_devices", []))
        self.apply_gadgets(received, self.cfg.get("managed_gadgets", []))
        done = checked | self.bought
        if self.cfg.get("planets"):
            new |= self.planets_tick(received, done)
        if self.cfg.get("clank"):
            self.clank_tick(received.get("Progressive Clank", 0))
        got_weapons = {ITEMS[n].value for n in received if ITEMS.get(n) and ITEMS[n].kind == "weapon"}
        now_open = self.p.read(VENDOR_OPEN) == 1

        if now_open and not self.vendor_open:
            lst = self.read_list()
            self.held_before = self.p.read(HELD)
            for w, loc in VENDOR_WEAPON_LOC.items():
                if loc in done:
                    self.set_owned(w, True)          # verrou : le vendeur la croit possédée
                    if w not in lst:
                        lst.append(w)
                elif w in lst:
                    self.take_weapon(w, lst)         # remise en vente
            self.write_list(lst)
            self.seen = lst
            self.log(f"vendeur ouvert ; liste {[hex(w) for w in lst]}")
        elif now_open or self.vendor_open:
            cur = self.read_list()
            for w in cur:
                if w not in self.seen and w in VENDOR_WEAPON_LOC and VENDOR_WEAPON_LOC[w] not in done:
                    self.log(f"achat : arme {w:#04x} -> check")
                    new.add(VENDOR_WEAPON_LOC[w])
                    self.bought.add(VENDOR_WEAPON_LOC[w])
            self.seen = cur
            if not now_open:
                self.log("vendeur fermé")
                self.apply_weapons(got_weapons, closing=True)
        if not now_open:
            self.apply_weapons(got_weapons)
            self.fix_held(got_weapons)
        self.vendor_open = now_open

        new |= self.armor_tick(received.get("Progressive Armor", 0), done | new, now_open)

        lev = self.p.read(LEVIATHANS)
        for d in LOCATIONS.values():
            if d.kind == "leviathan" and lev >= d.value and d.id not in done:
                new.add(d.id)
        if time.time() - self.scan_time > SCAN_EVERY:
            self.scan_time = time.time()
            new |= self.scan_checks(done | new)
        self.apply_objs(received)
        self.bought |= new
        return new

    # --- checks lus en mémoire (v0.4) ------------------------------------------------------------------
    def scan_checks(self, done: set[int]) -> set[int]:
        todo = [d for d in SCANNED if d.id not in done]
        if not todo:
            return set()
        new: set[int] = set()
        skills = struct.unpack(">Q", self.p.read_block(SKILLS, 8))[0]
        statues = self.p.read(OBJ + 4 * OBJ_STATUES)
        holoplans = self.p.read(HOLOPLANS)
        bolts: dict[int, int] = {}
        missions: dict[int, int] = {}
        hero = self.p.read(HERO_PTR)
        hp_max = struct.unpack(">f", struct.pack(">I", self.p.read(hero + 0x75C)))[0] if hero else 0.0
        if not 1.0 <= hp_max <= 1000.0:  # chargement : pointeur pas encore sur Ratchet
            hp_max = 0.0
        for d in todo:
            if d.kind == "gold_bolt":
                if d.level not in bolts:
                    bolts[d.level] = self.p.read(GOLD_BOLTS + d.level * LEVEL_STRIDE)
                hit = bolts[d.level] >> d.value & 1
            elif d.kind == "skill":
                hit = skills >> d.value & 1
            elif d.kind == "mission":
                if d.level not in missions:
                    missions[d.level] = self.p.read(MISSIONS_DONE + d.level * MISSIONS_STRIDE + 0x78)
                hit = missions[d.level] >= d.value
            elif d.kind == "holoplan":
                hit = holoplans >> d.value & 1
            elif d.kind == "level":
                hit = hp_max >= BASE_HP + d.value
            else:  # statue
                hit = statues >= d.value
            if hit:
                self.log(f"check : {d.kind} {d.region} {d.value}")
                new.add(d.id)
        return new

    def apply_objs(self, received: dict[str, int]) -> None:
        """Objets OBJ_ gérés (Super-bottes...) : possédé (2 copies) <=> reçu ; le jeu les redonne au chargement."""
        for i in self.cfg.get("managed_objs", []):
            want = 1 if any(d.kind == "obj" and d.value == i for n, d in ITEMS.items() if n in received) else 0
            for base in (OBJ, OBJ2):
                if self.p.read(base + 4 * i) != want:
                    self.p.write(base + 4 * i, want)

    # --- planètes (v0.3) ------------------------------------------------------------------------------
    def command(self, cmd: int, arg: int = 0) -> bool:
        """Demande au patch (boîte aux lettres). Faux si une demande est encore en attente."""
        if self.p.read(MAILBOX + 0x10) != 0:
            return False
        self.p.write(MAILBOX + 0x18, arg)
        self.p.write(MAILBOX + 0x10, cmd)
        return True

    def has_hook2(self) -> bool:
        if self.hook2 is None:
            self.hook2 = self.p.read(HOOK2) == 0x3D607F00
            if not self.hook2:
                self.log("patch RPCS3 v0.6 absent : planètes NON protégées (voyages de l'histoire, téléportation)")
        return self.hook2

    def level_byte(self, level: int, k: int) -> int:
        return self.p.read(LEVELS + level * LEVEL_STRIDE + k, READ8)

    def planets_tick(self, received: dict[str, int], done: set[int]) -> set[int]:
        new: set[int] = set()
        got = {LEVEL_OF_ITEM[n] for n in received if n in LEVEL_OF_ITEM}   # planètes + combats spatiaux reçus
        allowed = got | {SPACE_COMBAT[lv] for lv in got if lv in SPACE_COMBAT}
        if self.final_open(got, done):
            got.add(FINAL_LEVEL)
            allowed.add(FINAL_LEVEL)
            base = MISSIONS_DONE + FINAL_LEVEL * MISSIONS_STRIDE
            count = min(self.p.read(base + 0x78), 10)
            if (any(self.p.read(base + 12 * i) == FIND_TACHYON for i in range(count))
                    and all(self.p.read(a) & bit for a, bit in TACHYON_DEAD)):
                self.goal_done = True
        if self.has_hook2():
            mask = sum(1 << lv for lv in allowed)
            if self.p.read(MAILBOX + 0x20) != mask:
                self.p.write(MAILBOX + 0x20, mask)
        # carte : planètes reçues visibles, les autres cachées (l'histoire en allume, ex. l'holo-invitation de Mukow)
        visited = set()
        for lv in list(LEVEL_OF_PLANET.values()) + sorted(SPACE_LEVELS) + [FINAL_LEVEL]:
            want = 1 if lv in got else 0
            raw = self.p.read_block(LEVELS + lv * LEVEL_STRIDE, 8)
            if raw[0] != want:
                self.p.write(LEVELS + lv * LEVEL_STRIDE, want, WRITE8)
            if raw[1]:
                visited.add(lv)
        for lv in visited:
            loc = ARRIVAL_LOC.get(lv)
            if loc is not None and loc not in done:
                self.log(f"arrivée sur le niveau {lv} -> check")
                new.add(loc)
        # armes des vendeurs : en vente dès que leur planète est reçue ; armes gérées sans vendeur : jamais
        for w in self.managed_weapons:
            planet = WEAPON_PLANET.get(w)
            want = 1 if planet in received else 0
            if self.p.read(FOR_SALE + w, READ8) != want:
                self.p.write(FOR_SALE + w, want, WRITE8)
        if not visited & set(LEVEL_OF_PLANET.values()):
            self.start_warp()
        else:
            self.warp = ("idle", 0.0)
        return new

    def final_open(self, got: set[int], done: set[int]) -> bool:
        """Fastoon final : toutes les planètes reçues et assez de boulons d'or trouvés (slot data)."""
        if self.cfg.get("goal") != "tachyon":
            return False
        return (set(LEVEL_OF_PLANET.values()) <= got
                and len(done & GOLD_BOLT_LOCS) >= self.cfg.get("gold_bolts_required", 0))

    def start_warp(self) -> None:
        """Nouvelle partie (aucune planète visitée) : envoyer le joueur sur sa planète de départ."""
        start = self.cfg.get("start_level")
        if start is None or not self.has_hook2():
            return
        state, t = self.warp
        now = time.time()
        if state == "idle":
            if self.p.read(LEVEL_STATE + 0x50) == 0 and self.command(CMD_MAP):
                self.log(f"nouvelle partie : téléportation vers le niveau {start}")
                self.warp = ("carte", now)
        elif state == "carte":
            if self.p.read(LEVEL_STATE + 0x50) != 0 and now - t > 0.6:
                if self.command(CMD_LOAD_LEVEL, start):
                    self.warp = ("voyage", now)
            elif now - t > 15:
                self.warp = ("idle", 0.0)
        elif state == "voyage" and now - t > 60:
            self.warp = ("idle", 0.0)  # pas arrivé : on recommence

    # --- Clank progressif (v0.3) ------------------------------------------------------------------------
    def ratchet(self) -> int:
        hero = self.p.read(HERO_PTR)
        if not hero:
            return 0
        r = hero - RATCHET_OFS
        return r if self.p.read(r + 4) == RATCHET_CLASS else 0

    def clank_tick(self, level: int) -> None:
        r = self.ratchet()
        if r and self.has_hook2() and time.time() - self.clank_cmd_time > 3:
            has = self.p.read(r + CLANK_HANDLE) != 0
            if has and level < 1 and self.command(CMD_CLANK_OFF):
                self.log("Clank pas encore reçu : retiré du dos")
                self.clank_cmd_time = time.time()
            elif not has and level >= 1 and self.command(CMD_CLANK_ON):
                self.log("Clank reçu : remis sur le dos")
                self.clank_cmd_time = time.time()
        want = 1 if level >= 2 else 0           # propulseur (le jeu le redonne à chaque chargement de planète)
        for base in (OBJ, OBJ2):
            if self.p.read(base + 4 * OBJ_THRUSTER) != want:
                self.p.write(base + 4 * OBJ_THRUSTER, want)
        if not want and self.p.read(PACK) == 1:
            self.p.write(PACK, 0)
            self.p.write(PACK_FLAG, 0)

    def apply_weapons(self, got: set[int], closing: bool = False) -> None:
        lst = self.read_list()
        before = list(lst)
        for w in self.managed_weapons:
            has = w in lst and self.owned(w)
            if w in got and (not has or (closing and w in self.saved)):
                self.give_weapon(w, lst)
            elif w not in got and (has or w in lst):
                self.take_weapon(w, lst)
        if lst != before:
            self.write_list(lst)
            self.log(f"armes : {[hex(w) for w in before]} -> {[hex(w) for w in lst]}")

    def apply_devices(self, received: dict[str, int], locked_devices: list[int]) -> None:
        """Dispositifs à débloquer : en vente seulement une fois le déblocage reçu (partout, même avant leur
        planète d'origine). Le jeu remet ses propres valeurs au chargement d'une planète : réécrites ici."""
        unlocked = {ITEMS[n].value for n in received if ITEMS.get(n) and ITEMS[n].kind == "device_unlock"}
        for f in locked_devices:
            want = 1 if f in unlocked else 0
            if self.p.read(FOR_SALE + f, READ8) != want:
                self.p.write(FOR_SALE + f, want, WRITE8)
                self.log(f"dispositif {f:#04x} : {'en vente' if want else 'verrouillé'}")

    def apply_gadgets(self, received: dict[str, int], managed: list[int]) -> None:
        """Gadgets gérés par la seed : possédé en jeu <=> reçu (le jeu les redonne par l'histoire)."""
        got = {ITEMS[n].value for n in received if ITEMS.get(n) and ITEMS[n].kind == "gadget"}
        for g in managed:
            want = g in got
            if self.owned(g) != want:
                self.set_owned(g, want)
                self.log(f"gadget {g:#04x} : {'donné' if want else 'retiré'}")
        if ROBO_WINGS in managed and ROBO_WINGS not in got:
            self.hide_wings()

    def find_clank(self) -> int:
        """Adresse de Clank (0 si introuvable). D'anciens objets Clank restent dans le tas avec la même vtable :
        le bon est celui dont la poignée (+0x64) est celle que garde l'objet de Ratchet (+0x21B0)."""
        r = self.ratchet()
        handle = self.p.read(r + CLANK_HANDLE) if r else 0
        if not handle:
            return 0
        if self.clank_beh and self.p.read(self.clank_beh) == CLANK_VTABLE:
            clank = self.p.read(self.clank_beh + 0x14)
            if self.handle_of(clank) == handle:
                return clank
        self.clank_beh = 0
        if time.time() < self.clank_retry:
            return 0
        v = struct.pack(">I", CLANK_VTABLE)
        lo = max(0x60000000, (r & ~0xFFFFF) + CLANK_WINDOW[0])
        for base in range(lo, min(0x6B500000, lo + CLANK_WINDOW[1]), 0x100000):
            try:
                b = self.p.read_block(base, 0x100000)
            except IOError:
                continue
            o = 0
            while (o := b.find(v, o)) >= 0:
                if o % 0x10 == 0 and o + 0x18 <= len(b):
                    clank = struct.unpack_from(">I", b, o + 0x14)[0]
                    if self.handle_of(clank) == handle:
                        self.clank_beh = base + o
                        return clank
                o += 4
        self.clank_retry = time.time() + 5
        return 0

    def handle_of(self, obj: int) -> int:
        """Poignée d'un objet du jeu (+0x64), 0 si l'adresse n'est pas dans le tas (vieux pointeur)."""
        if not 0x60000000 <= obj < 0x6B500000:
            return 0
        try:
            return self.p.read(obj + 0x64)
        except IOError:
            return 0

    def hide_wings(self) -> None:
        """Sans Ailorobot, les ailes sortent quand même sur les plateformes de lancement : les rentrer."""
        clank = self.find_clank()
        if clank:
            m = self.p.read(clank + CLANK_MASK)
            if m & CLANK_WINGS:
                self.p.write(clank + CLANK_MASK, (m & ~CLANK_WINGS) | CLANK_NORMAL)

    def fix_held(self, got: set[int]) -> None:
        held = self.p.read(HELD)
        if held in self.managed_weapons and held not in got:
            lst = self.read_list()
            to = self.held_before if self.held_before in lst else (lst[0] if lst else EMPTY)
            hero = self.p.read(HERO_PTR)
            if to != EMPTY and hero and self.p.read(hero + SWITCH_REQ) == EMPTY:
                self.p.write(hero + SWITCH_REQ, to)
                self.log(f"arme en main {held:#04x} pas reçue -> {to:#04x}")

    def armor_tick(self, progressive: int, done: set[int], vendor_open: bool) -> set[int]:
        new: set[int] = set()
        a = [self.p.read(ARMOR_OWNED + 4 * i) for i in range(ARMOR_COUNT)]
        allowed = min(progressive, ARMOR_COUNT - 1)
        for i, loc in VENDOR_ARMOR_LOC.items():
            # achat = seulement vendeur ouvert : le jeu marque aussi « possédée » l'armure portée (armure progressive
            # reçue) au chargement d'une planète -> faux check (vu le 2026-10-15, Blackstar sur Kreeli)
            if a[i] and loc not in done and vendor_open:
                self.log(f"achat : armure {i} -> check")
                new.add(loc)
            want = 1 if (loc in done or loc in new) else 0
            if a[i] != want:
                self.p.write(ARMOR_OWNED + 4 * i, want)
        free = [i for i in range(1, ARMOR_COUNT) if i not in VENDOR_ARMOR_LOC and a[i]]  # achetées hors AP
        if vendor_open:
            target = max([0] + [i for i, loc in VENDOR_ARMOR_LOC.items() if (loc in done or loc in new) and i <= allowed] + free)
        else:
            target = max([allowed] + free)
        worn = self.p.read(ARMOR_WORN)
        if worn != target:
            self.p.write(ARMOR_WORN, target)
            self.log(f"armure portée {worn} -> {target}")
        return new

    # --- objets à usage unique ---------------------------------------------------------------------
    def give_filler(self, name: str) -> bool:
        if not self.in_game() or self.vendor_open:
            return False
        d = ITEMS[name]
        addr = BOLTS if d.kind == "bolts" else RARITANIUM
        self.p.write(addr, self.p.read(addr) + d.value)
        return True

    # --- messages (patch RPCS3) ----------------------------------------------------------------------
    def check_patch(self) -> bool:
        a = self.p.read(MAILBOX + 4)
        time.sleep(0.1)
        self.patch_ok = self.p.read(MAILBOX + 4) != a
        return self.patch_ok

    def message(self, text: str, duration: float = 4.0) -> None:
        self.msg_queue.append((text, duration))

    def message_tick(self) -> None:
        if not self.msg_queue or time.time() < self.msg_until or not self.in_game():
            return
        if self.patch_ok is None and not self.check_patch():
            self.log("patch RPCS3 absent ou inactif : pas de messages en jeu")
        if not self.patch_ok or self.p.read(MAILBOX + 0x10) != 0:
            return
        text, dur = self.msg_queue.pop(0)
        raw = text.replace("<", COLOR_ON).replace(">", COLOR_OFF).encode()[:0xEFF] + b"\0"
        for i in range(0, len(raw), 4):
            self.p.write(MAILBOX + 0x100 + i, int.from_bytes(raw[i:i + 4].ljust(4, b"\0"), "big"))
        self.p.write(MAILBOX + 0x14, struct.unpack(">I", struct.pack(">f", dur))[0])
        self.p.write(MAILBOX + 0x10, 1)
        self.msg_until = time.time() + dur + 0.3
