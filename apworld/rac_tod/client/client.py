"""
Client Archipelago de Tools of Destruction (lancé depuis le Launcher d'Archipelago).

- Serveur AP : CommonClient (connexion, objets reçus, checks envoyés).
- Jeu : RPCS3 par PINE (port 28012, « IPC Server enabled » dans config/ipc.yml), voir game.py.
- Objets à usage unique (boulons, Raritanium) et messages : compteur « traités » gardé sur le serveur
  (stockage de données), pour ne rien donner deux fois après une reconnexion.
"""
import asyncio
from typing import Any, Optional

import Utils
from CommonClient import ClientCommandProcessor, CommonContext, get_base_parser, gui_enabled, logger, server_loop
from NetUtils import ClientStatus

from ..data import GAME, ITEMS, LOCATIONS, item_fr
from .game import Game, GameError

TICK = 0.1


class ToDCommands(ClientCommandProcessor):
    def _cmd_game(self) -> None:
        """Affiche l'état de la connexion au jeu (RPCS3)."""
        ctx = self.ctx
        if isinstance(ctx, ToDContext):
            self.output(f"Jeu : {'connecté' if ctx.tod.connected else 'pas connecté'} ; "
                        f"patch des messages : {ctx.tod.patch_ok}")

    def _cmd_bolts(self, value: str = "") -> None:
        """Test : fixe les boulons (/bolts 55000)."""
        self._set(0x101EFF3C, value, "boulons")

    def _cmd_raritanium(self, value: str = "") -> None:
        """Test : fixe le Raritanium (/raritanium 0)."""
        self._set(0x101EFF40, value, "Raritanium")

    def _set(self, addr: int, value: str, what: str) -> None:
        ctx = self.ctx
        if not (isinstance(ctx, ToDContext) and ctx.tod.connected and value.isdigit()):
            self.output("Jeu pas connecté ou valeur invalide")
            return
        ctx.tod.p.write(addr, int(value))
        self.output(f"{what} = {value}")

    def _cmd_ship(self) -> None:
        """Ouvre la carte galactique (secours si tu es bloqué sans vaisseau ; patch v0.6)."""
        ctx = self.ctx
        if isinstance(ctx, ToDContext) and ctx.tod.connected and ctx.tod.in_game():
            self.output("Carte galactique demandée" if ctx.tod.command(4) else "Le patch est occupé, réessaie")
        else:
            self.output("Jeu pas connecté")

    def _cmd_msg(self, *text: str) -> None:
        """Affiche un message en jeu (test du patch RPCS3)."""
        ctx = self.ctx
        if isinstance(ctx, ToDContext) and ctx.tod.connected:
            ctx.tod.message(" ".join(text) or "Test <Archipelago> !")


class ToDContext(CommonContext):
    game = GAME
    items_handling = 0b111
    command_processor = ToDCommands

    def __init__(self, server_address: Optional[str], password: Optional[str]) -> None:
        super().__init__(server_address, password)
        self.tod = Game(logger.info)
        self.processed: Optional[int] = None  # objets reçus déjà traités (None = pas encore lu sur le serveur)
        self.goal_sent = False
        self.goal_seen_open = False  # des checks restaient à faire pendant cette session
        self.game_task: Optional[asyncio.Task] = None

    @property
    def store_key(self) -> str:
        return f"rac_tod_{self.team}_{self.slot}_processed"

    def make_gui(self):
        ui = super().make_gui()
        ui.base_title = "Tools of Destruction Client v0.4 | Archipelago"
        return ui

    async def server_auth(self, password_requested: bool = False) -> None:
        if password_requested and not self.password:
            await super().server_auth(password_requested)
        await self.get_username()
        await self.send_connect()

    def on_package(self, cmd: str, args: dict[str, Any]) -> None:
        super().on_package(cmd, args)
        if cmd == "Connected":
            self.processed = None
            self.goal_sent = False
            self.goal_seen_open = False
            self.tod.configure(args.get("slot_data", {}))
            Utils.async_start(self.send_msgs([
                {"cmd": "Get", "keys": [self.store_key]},
                {"cmd": "LocationScouts", "locations": sorted(self.server_locations), "create_as_hint": 0},
            ]))
        elif cmd == "Retrieved" and self.store_key in args.get("keys", {}):
            self.processed = args["keys"][self.store_key] or 0
            logger.info(f"Objets déjà traités : {self.processed}")

    def save_processed(self) -> None:
        Utils.async_start(self.send_msgs([{"cmd": "Set", "key": self.store_key, "default": 0, "want_reply": False,
                                           "operations": [{"operation": "replace", "value": self.processed}]}]))

    def item_name(self, item: int, player: int) -> str:
        return self.item_names.lookup_in_slot(item, player)

    def received_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for it in self.items_received:
            name = self.item_names.lookup_in_slot(it.item, self.slot)
            counts[name] = counts.get(name, 0) + 1
        return counts

    def process_new_items(self) -> None:
        """Boulons / Raritanium et messages des objets reçus, un par un, dans l'ordre."""
        if self.processed is None:
            return
        changed = False
        while self.processed < len(self.items_received):
            it = self.items_received[self.processed]
            name = self.item_names.lookup_in_slot(it.item, self.slot)
            d = ITEMS.get(name)
            if d and d.kind in ("bolts", "raritanium") and not self.tod.give_filler(name):
                break  # pas en jeu ou vendeur ouvert : on réessaie au prochain tour
            if d and d.kind in ("bolts", "raritanium"):
                logger.info(f"don : {d.fr}")
            if it.player == self.slot:
                self.tod.message(f"Tu as trouvé <{item_fr(name)}> !")
            else:
                self.tod.message(f"Tu as reçu <{item_fr(name)}> de {self.player_names.get(it.player, '?')} !")
            self.processed += 1
            changed = True
        if changed:
            self.save_processed()

    def announce_sent(self, locs: set[int]) -> None:
        for loc in locs:
            info = self.locations_info.get(loc)
            if info is None or info.player == self.slot:
                continue  # notre propre objet : annoncé à la réception
            name = self.item_name(info.item, info.player)
            self.tod.message(f"Envoyé : <{name}> pour {self.player_names.get(info.player, '?')}")


async def game_loop(ctx: ToDContext) -> None:
    while not ctx.exit_event.is_set():
        try:
            if not ctx.tod.connected:
                try:
                    ctx.tod.connect()
                    logger.info("Connecté au jeu (RPCS3).")
                except GameError as e:
                    logger.error(str(e))
                    await asyncio.sleep(10)
                    continue
                except OSError:
                    await asyncio.sleep(3)
                    continue
            if ctx.slot is None or ctx.processed is None:
                await asyncio.sleep(0.5)
                continue
            checked = set(ctx.checked_locations)
            new = ctx.tod.tick(ctx.received_counts(), checked)
            new &= ctx.server_locations
            if new:
                await ctx.send_msgs([{"cmd": "LocationChecks", "locations": sorted(new)}])
                ctx.announce_sent(new)
            ctx.process_new_items()
            ctx.tod.message_tick()
            tachyon = ctx.tod.cfg.get("goal") == "tachyon"
            if not ctx.goal_sent and (ctx.tod.goal_done if tachyon
                                      else ctx.server_locations and ctx.server_locations <= checked):
                await ctx.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}])
                ctx.goal_sent = True
                if ctx.goal_seen_open:  # message seulement si l'objectif vient d'être atteint (pas à la reconnexion)
                    ctx.tod.message("<Tachyon vaincu !> Objectif atteint." if tachyon
                                    else "<Tous les checks faits !> Objectif atteint.", 6.0)
                logger.info("Objectif atteint !")
            elif not ctx.goal_sent:
                ctx.goal_seen_open = True
        except (OSError, IOError) as e:
            logger.info(f"Connexion au jeu perdue ({e}), nouvel essai…")
            ctx.tod.drop()
            await asyncio.sleep(3)
            continue
        await asyncio.sleep(TICK)


def launch(*args: str) -> None:
    async def main(parsed) -> None:
        ctx = ToDContext(parsed.connect, parsed.password)
        ctx.server_task = asyncio.create_task(server_loop(ctx), name="server loop")
        if gui_enabled:
            ctx.run_gui()
        ctx.run_cli()
        ctx.game_task = asyncio.create_task(game_loop(ctx), name="game loop")
        await ctx.exit_event.wait()
        ctx.server_address = None
        await ctx.shutdown()
        if ctx.game_task:
            await asyncio.wait([ctx.game_task], timeout=2)

    Utils.init_logging("ToDClient", exception_logger="Client")
    parser = get_base_parser(description="Tools of Destruction Client")
    parsed, _ = parser.parse_known_args(args)
    import colorama
    colorama.just_fix_windows_console()
    asyncio.run(main(parsed))
    colorama.deinit()
