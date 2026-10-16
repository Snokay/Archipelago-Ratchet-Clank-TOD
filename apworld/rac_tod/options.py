from dataclasses import dataclass

from Options import Choice, DeathLink, DefaultOnToggle, PerGameCommonOptions, Range


class StartingPlanet(Choice):
    """Planet you start on. A new game is sent there as soon as Ratchet appears on Kerwan (the Aphelion is parked
    there, so you can always leave). by_difficulty: random planet using Starting Planet Difficulty. The final planets (Igliak,
    Fastoon) can never be a start."""
    display_name = "Starting Planet"
    option_by_difficulty = 0
    option_cobalia = 1
    option_kortog = 2
    option_fastoon = 3
    option_mukow = 5
    option_apogee_space_station = 6
    option_ardolis = 7
    option_rykan_v = 9
    option_sargasso = 10
    option_kreeli_comet = 11
    option_viceron = 12
    option_jasindu = 14
    option_ublik_passage = 15
    option_reepor = 16
    default = 0


class StartingPlanetDifficulty(Range):
    """How far in the story a random starting planet can be (like progression balancing: the higher, the harder).
    0: only the first planets (Cobalia, Kortog). 99: any planet up to Reepor (late game, starting weapons only)."""
    display_name = "Starting Planet Difficulty"
    range_start = 0
    range_end = 99
    default = 25


class DeviceUnlocks(DefaultOnToggle):
    """Devices (Groovitron, Leech Bomb...) are missing from the device vendor until you receive their unlock.
    Once unlocked, you buy them normally (no check). Only applied if there is room left in the item pool;
    otherwise devices are sold as in the normal game."""
    display_name = "Device Unlocks"


class GoldBoltsRequired(Range):
    """Gold Bolts you must find (checked) before Fastoon (final planet, Emperor Tachyon) appears on the galactic map.
    Fastoon also needs every planet received. The goal is to defeat Emperor Tachyon."""
    display_name = "Gold Bolts Required"
    range_start = 0
    range_end = 31
    default = 10


class PlayerLevels(Range):
    """How many of Ratchet's level-ups are checks (each level-up raises max health by one).
    Level-up N needs about N/4 planets in logic. 0 = no level checks."""
    display_name = "Player Levels"
    range_start = 0
    range_end = 50
    default = 20


@dataclass
class ToDOptions(PerGameCommonOptions):
    starting_planet: StartingPlanet
    starting_planet_difficulty: StartingPlanetDifficulty
    device_unlocks: DeviceUnlocks
    gold_bolts_required: GoldBoltsRequired
    player_levels: PlayerLevels
    # Pas encore géré par le client (DeathLink prévu, voir PLAN.md).
    death_link: DeathLink
