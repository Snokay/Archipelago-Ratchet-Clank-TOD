# Ratchet & Clank Future: Tools of Destruction Archipelago — alpha 0.9.1.1

### 📖 [Setup guide / Guide d'installation](SETUP_GUIDE.md) · 🤖 [AI disclosure / Déclaration IA](AI_DISCLOSURE.md) · ⬇️ [Download / Télécharger](../../releases) · 💬 [Discord](https://discord.gg/yqKUMMkWhr)

*(Version française plus bas)*

[Archipelago](https://archipelago.gg) world for **Ratchet & Clank Future: Tools of Destruction** (PS3) on the
**RPCS3** emulator: planets, gadgets, weapons and more are shuffled with the other players of a multiworld.

> **Alpha**: playable, but expect bugs. Please report them on the Discord.

## Features

- **Random planets**: you start on a random planet (or the one you choose) and unlock the others as items.
  You travel from anywhere through the galactic map (no need to reach the Aphelion); story trips to a planet
  you do not have yet are stopped and the map opens instead.
- **About 280 checks**: story missions, skill points, gold bolts, arrival on each planet, weapon and armor
  vendors, Tachyon statues on Mukow, Leviathan souls, the 13 holo-plans, Ratchet's level-ups (`player_levels`, 20 by
  default) and each weapon's level-ups V2 to V5 (`weapon_level_checks`).
- **Progressive weapons** (`progressive_weapons`, off by default): each weapon is shuffled 5 times. The first copy
  gives the weapon, each next one allows one more level. A weapon cannot level up past what you received: its XP
  stops at the next level (full bar) and the level-up check is still sent.
- **Items**: planets and space combats, gadgets (Heli-Pods, Geo-Laser, Gelanator, Robo-Wings, Gyro-Cycle,
  Holo-Pirate Disguise, Decryptor), Super-Boots, **Progressive Clank** (Clank on your back, then the
  Thruster-Pack), weapons, **Progressive Armor**, device unlocks, bolts and Raritanium.
- Weapons sold by vendors stay for sale until you buy them (the purchase is the check), even if you already
  received them.
- Archipelago messages show up **in the game's own message box** (French or English, following the game's
  language).
- **Goal**: defeat Emperor Tachyon on Fastoon. Fastoon (final) appears on the map once you have every planet
  and the number of gold bolts set by `gold_bolts_required`.

## PopTracker

A [PopTracker](https://github.com/black-sliver/PopTracker) pack is attached to each release
(`RaC_ToD_AP_poptracker_<version>.zip`): drop the zip into PopTracker's `packs` folder, open **Ratchet & Clank:
Tools of Destruction Archipelago** (Map Tracker or Items Only), click **AP** and enter the room address and your
slot. Galaxy map with every planet, a panel for gold bolts, holo-plans, skill points and weapon levels, the game's
level maps, and what is in logic. On level maps the check groups are not at their exact place yet.

## Requirements

- RPCS3 (tested on 0.0.43) and **your own** copy of the game: **EU disc BCES00052, version 01.00, without
  game update** (the game is multilingual).
- [Archipelago 0.6](https://github.com/ArchipelagoMW/Archipelago/releases) or newer.

Install: see the **[setup guide](SETUP_GUIDE.md)** (apworld, RPCS3 patch, IPC server, client).

## Known limitations (alpha)

- Not shuffled yet: Hydro-Pack, Swingshot, Grind/Gravity Boots, O2 Mask (the game gives them as
  usual). Skill points that need challenge mode, holoplans or the Groovitron are not included.
- DeathLink is not implemented yet.
- RPCS3 accepts only one IPC client at a time: close other tools that read the game's memory.

## Credits and license

- Code: Snokayy, MIT license (see [LICENSE](LICENSE)). No game file is distributed: the client talks to RPCS3
  through its IPC server (PINE protocol) and the RPCS3 patch contains only our own code.
- PopTracker pack: item icons, planet pictures and level maps come from the game, through the
  [Ratchet & Clank Wiki](https://ratchetandclank.fandom.com) (Fandom); the galaxy map and frames are generated.
- **AI disclosure**: this project was developed with the help of an AI assistant (Claude, Anthropic); details in [AI_DISCLOSURE.md](AI_DISCLOSURE.md). The logo,
  emblem and client icon are AI-generated images.
- Ratchet & Clank is a trademark of Sony Interactive Entertainment; this fan project is not affiliated with Sony
  or Insomniac Games.

---

# Version française

Monde [Archipelago](https://archipelago.gg) pour **Ratchet & Clank : Opération Destruction** (PS3) sur
l'émulateur **RPCS3** : planètes, gadgets, armes et plus sont mélangés avec les autres joueurs d'un multiworld.

> **Alpha** : jouable, mais il reste des bugs. Signalez-les sur le Discord.

## Contenu

- **Planètes aléatoires** : départ sur une planète au hasard (ou celle de votre choix), les autres arrivent
  comme objets. Voyage depuis n'importe où par la carte galactique ; les voyages de l'histoire vers une planète
  pas encore reçue sont arrêtés et la carte s'ouvre à la place.
- **Environ 280 checks** : missions, points de compétence, boulons d'or, arrivée sur chaque planète, vendeurs
  d'armes et d'armures, statues de Tachyon sur Mukow, âmes de Léviathan, les 13 holoplans, niveaux de Ratchet
  (`player_levels`, 20 par défaut) et niveaux V2 à V5 de chaque arme (`weapon_level_checks`).
- **Armes progressives** (`progressive_weapons`, désactivé par défaut) : chaque arme est mélangée 5 fois. La 1re
  copie donne l'arme, chaque suivante autorise un niveau de plus. L'XP s'arrête au niveau suivant (barre pleine)
  et le check de niveau part quand même.
- **Objets** : planètes et combats spatiaux, gadgets (Héli-capsules, Géo-laser, Gélanator, Ailorobot,
  Gyro-Cycle, Déguisement holopirate, Décrypteur), Super-bottes, **Clank progressif** (Clank sur le dos, puis le
  propulseur), armes, **armure progressive**, déblocages de dispositifs, boulons et Raritanium.
- Les armes des vendeurs restent en vente jusqu'à l'achat (l'achat = le check), même déjà reçues.
- Les messages d'Archipelago s'affichent **dans la boîte de messages du jeu** (en français si le jeu est en
  français, sinon en anglais).
- **Objectif** : battre l'empereur Tachyon sur Fastoon. Fastoon (final) apparaît sur la carte quand vous avez
  toutes les planètes et le nombre de boulons d'or réglé par `gold_bolts_required`.

## PopTracker

Un pack [PopTracker](https://github.com/black-sliver/PopTracker) est joint à chaque release : mettez le zip dans
le dossier `packs` de PopTracker, ouvrez le pack (Map Tracker ou Items Only), cliquez sur **AP** et entrez l'adresse
de la room et votre slot. Sur les cartes de niveau, les groupes de checks ne sont pas encore à leur place exacte.

## Prérequis

- RPCS3 (testé en 0.0.43) et **votre propre** copie du jeu : **disque EU BCES00052, version 01.00, sans mise à
  jour** (le jeu est multilingue).
- [Archipelago 0.6](https://github.com/ArchipelagoMW/Archipelago/releases) ou plus récent.

Installation : voir le **[guide d'installation](SETUP_GUIDE.md)**.

## Limites connues (alpha)

- Pas encore mélangés : hydro-pack, Swingueur, glisso-bottes / bottes gravité, masque O2 (le jeu les
  donne normalement). Points de compétence du mode défi, des holoplans ou du Groovitron absents.
- DeathLink pas encore géré.
- RPCS3 n'accepte qu'un client IPC à la fois : fermez les autres outils qui lisent la mémoire du jeu.

## Crédits et licence

- Code : Snokayy, licence MIT ([LICENSE](LICENSE)). Aucun fichier du jeu n'est distribué avec le mod.
- Pack PopTracker : icônes, images des planètes et cartes de niveau du jeu, via le
  [Ratchet & Clank Wiki](https://ratchetandclank.fandom.com) (Fandom) ; carte de la galaxie et cadres générés.
- **Déclaration IA** : projet développé avec l'aide d'une IA (Claude, Anthropic), détails dans [AI_DISCLOSURE.md](AI_DISCLOSURE.md) Le logo, l'emblème et l'icône
  du client sont des images générées par IA.
- Ratchet & Clank est une marque de Sony Interactive Entertainment ; projet de fan sans lien avec Sony ni
  Insomniac Games.
