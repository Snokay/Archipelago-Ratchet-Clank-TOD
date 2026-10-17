# AI disclosure — Ratchet & Clank Future: Tools of Destruction Archipelago

*(Version française plus bas)*

## Was AI used?

Yes. This project was developed with the help of an AI assistant.

## Which tools?

- **Claude** (Anthropic), through **Claude Code**, for code and documentation.
- An AI image generator for the **logo**, the **emblem** and the **client icon** (`assets/logo.png`,
  `assets/emblem.png`, `apworld/rac_tod/images/tod_icon.png`).

## For what, and how much?

- **Code**: most of the code (apworld, client, RPCS3 patch, PopTracker pack scripts) was written by Claude,
  following my instructions and design decisions.
- **Research**: memory addresses and game behaviour were found together during play sessions: I play and
  test in RPCS3, Claude reads the memory through RPCS3's IPC server and analyses the results.
- **Documentation**: README, setup guide and release notes were drafted by Claude and reviewed by me.
- **Images**: logo, emblem and client icon are AI-generated. Item icons, planet pictures and level maps in the
  PopTracker pack come from the game (through the Ratchet & Clank Wiki), not from AI.

## What I do myself

- Design choices: what is shuffled, options, logic, goal, what goes in each version.
- **Testing**: every version is played and tested in the game before release; bugs found by me and by
  players are reported, diagnosed and fixed.
- Review of the changes, releases and support on the Discord.

I am responsible for everything published here, AI-assisted parts included. If something is wrong or unclear,
please open an issue or ask on the [Discord](https://discord.gg/yqKUMMkWhr).

## No code from other worlds

No code was copied from other Archipelago worlds. The PINE client (`pine.py`) is our own implementation of the
public PINE protocol. See the [README](README.md) for credits and the [MIT license](LICENSE).

---

# Déclaration IA

## IA utilisée ?

Oui. Ce projet a été développé avec l'aide d'un assistant IA.

## Quels outils ?

- **Claude** (Anthropic), via **Claude Code**, pour le code et la documentation.
- Un générateur d'images IA pour le **logo**, l'**emblème** et l'**icône du client**.

## Pour quoi, et à quel point ?

- **Code** : la plus grande partie du code (apworld, client, patch RPCS3, scripts du pack PopTracker) a été
  écrite par Claude, selon mes instructions et mes choix.
- **Recherche** : les adresses mémoire et le fonctionnement du jeu ont été trouvés ensemble pendant des
  sessions de jeu : je joue et je teste dans RPCS3, Claude lit la mémoire par le serveur IPC et analyse.
- **Documentation** : README, guide d'installation et notes de version rédigés par Claude et relus par moi.
- **Images** : logo, emblème et icône du client générés par IA. Les icônes, images des planètes et cartes du
  pack PopTracker viennent du jeu (via le Ratchet & Clank Wiki), pas d'une IA.

## Ce que je fais moi-même

- Les choix : ce qui est mélangé, les options, la logique, l'objectif, le contenu de chaque version.
- **Les tests** : chaque version est jouée et testée en jeu avant publication ; les bugs (les miens et ceux
  des joueurs) sont signalés, analysés et corrigés.
- La relecture des changements, les publications et le support sur le Discord.

Je suis responsable de tout ce qui est publié ici, parties faites avec l'IA comprises. Une erreur ou une
question : ouvrez une issue ou passez sur le [Discord](https://discord.gg/yqKUMMkWhr).

## Pas de code d'autres mondes

Aucun code n'a été copié d'autres mondes Archipelago. Le client PINE (`pine.py`) est notre propre
implémentation du protocole PINE public. Crédits dans le [README](README.md), [licence MIT](LICENSE).
