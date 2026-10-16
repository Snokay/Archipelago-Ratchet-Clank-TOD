# Setup guide — Ratchet & Clank Future: Tools of Destruction Archipelago

*(Version française plus bas)*

## 1. Check your game

RPCS3 > right-click the game > the serial must be **BCES00052** and the version **01.00**. If a game update is
installed, remove it (right-click > Remove > Remove HDD Game / update data). Other versions are not supported.

## 2. Install the apworld

Download `rac_tod.apworld` from the [latest release](../../releases) and double-click it (or copy it into the
`custom_worlds` folder of your Archipelago install). Restart the Archipelago Launcher.

## 3. Install the RPCS3 patch

1. Copy `BCES00052_patch.yml` from the release into the `patches` folder of RPCS3 (next to `rpcs3.exe`).
2. RPCS3 > **Manage > Game Patches**, find *Ratchet & Clank Future: Tools of Destruction* and tick the
   **Archipelago** patch. Click **Save**.

The patch only adds our code (messages, galactic map from anywhere, story trip filter, Clank). Without it the
client still connects but planets are not protected.

## 4. Enable the IPC server

RPCS3 > **Configuration > IPC** (or create `config/ipc.yml` in the RPCS3 folder) with:

```yaml
IPC Server enabled: true
IPC Port: 28012
```

Restart RPCS3.

## 5. Generate and play

1. Put the example YAML (`Ratchet and Clank Tools of Destruction.yaml` from the release, or Archipelago
   Launcher > **Generate Template Options**) in your `Players` folder, edit it, and generate as usual.
2. Start the game in RPCS3 and start a **new game**.
3. Archipelago Launcher > **Ratchet & Clank: Tools of Destruction Client**, then connect to the room
   (address, slot name).
4. As soon as Ratchet appears on Kerwan, the galactic map opens and you are sent to your starting planet.

Options: starting planet (or random by difficulty), device unlocks, gold bolts required for the final planet,
number of level-up checks.

---

# Guide d'installation (français)

## 1. Vérifier le jeu

RPCS3 > clic droit sur le jeu : numéro **BCES00052**, version **01.00**. Si une mise à jour est installée,
supprimez-la. Les autres versions ne sont pas gérées.

## 2. Installer l'apworld

Téléchargez `rac_tod.apworld` dans la [dernière release](../../releases) et double-cliquez dessus (ou copiez-le
dans le dossier `custom_worlds` d'Archipelago). Relancez le Launcher d'Archipelago.

## 3. Installer le patch RPCS3

1. Copiez `BCES00052_patch.yml` dans le dossier `patches` de RPCS3 (à côté de `rpcs3.exe`).
2. RPCS3 > **Gérer > Patchs de jeu**, trouvez *Ratchet & Clank Future: Tools of Destruction*, cochez le patch
   **Archipelago**, puis **Enregistrer**.

## 4. Activer le serveur IPC

Dans RPCS3 (**Configuration > IPC**) ou dans un fichier `config/ipc.yml` du dossier de RPCS3 :

```yaml
IPC Server enabled: true
IPC Port: 28012
```

Relancez RPCS3.

## 5. Générer et jouer

1. Mettez le YAML d'exemple de la release dans le dossier `Players`, réglez-le, générez comme d'habitude.
2. Lancez le jeu dans RPCS3 et commencez une **nouvelle partie**.
3. Launcher d'Archipelago > **Ratchet & Clank: Tools of Destruction Client**, connectez-vous à la room.
4. Dès que Ratchet apparaît sur Kerwan, la carte galactique s'ouvre et vous partez vers votre planète de départ.
