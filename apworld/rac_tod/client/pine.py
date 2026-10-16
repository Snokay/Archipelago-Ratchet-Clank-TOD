"""
Accès à la mémoire du jeu par le serveur IPC de RPCS3 (protocole PINE), écrit pour ce projet (2026-10-14).

Protocole PINE (public) :
- requête : taille totale du message (u32 petit-boutiste, elle-même comprise), puis une ou plusieurs
  commandes : code (u8) + adresse (u32 petit-boutiste) [+ valeur à écrire, petit-boutiste] ;
- réponse : taille totale (u32), code résultat (u8 : 0 = OK, 0xFF = échec), puis les données lues dans
  l'ordre des commandes ; les commandes d'information (titre, identifiant, version) renvoient une chaîne
  précédée de sa longueur (u32).
RPCS3 : « IPC Server enabled: true » et « IPC Port: 28012 » dans config/ipc.yml. Un seul client à la fois.
Les valeurs lues sont déjà converties (la mémoire de la PS3 est big-endian, RPCS3 renvoie des entiers).
"""
import socket
import struct

# Codes de commande PINE
READ8, READ16, READ32, READ64 = 0x00, 0x01, 0x02, 0x03
WRITE8, WRITE16, WRITE32, WRITE64 = 0x04, 0x05, 0x06, 0x07
TITLE, ID, GAME_VERSION = 0x0B, 0x0C, 0x0E

WIDTH = {READ8: 1, READ16: 2, READ32: 4, READ64: 8, WRITE8: 1, WRITE16: 2, WRITE32: 4, WRITE64: 8}
OK = 0x00
BATCH = 4096  # commandes par message (les lectures groupées vont beaucoup plus vite)


class Pine:
    def __init__(self, port: int = 28012, host: str = "127.0.0.1") -> None:
        self.sock = socket.create_connection((host, port), timeout=5)

    def _exchange(self, commands: bytes) -> bytes:
        """Envoie un message (suite de commandes) et renvoie les données de la réponse."""
        self.sock.sendall(struct.pack("<I", 4 + len(commands)) + commands)
        total = struct.unpack("<I", self._read_exact(4))[0]
        reply = self._read_exact(total - 4)
        if reply[0] != OK:
            raise IOError("PINE : commande refusée")
        return reply[1:]

    def _read_exact(self, n: int) -> bytes:
        data = bytearray()
        while len(data) < n:
            part = self.sock.recv(n - len(data))
            if not part:
                raise IOError("PINE : connexion fermée")
            data += part
        return bytes(data)

    # --- informations sur le jeu ---------------------------------------------------------------------
    def text(self, command: int) -> str:
        data = self._exchange(bytes([command]))
        size = struct.unpack_from("<I", data)[0]
        return data[4:4 + size].decode("utf-8", "replace").rstrip("\x00")

    # --- lecture / écriture ---------------------------------------------------------------------------
    def read(self, addr: int, op: int = READ32) -> int:
        return int.from_bytes(self._exchange(struct.pack("<BI", op, addr))[:WIDTH[op]], "little")

    def write(self, addr: int, value: int, op: int = WRITE32) -> None:
        self._exchange(struct.pack("<BI", op, addr) + int(value).to_bytes(WIDTH[op], "little"))

    def read_many(self, addrs: list[int], op: int = READ64) -> list[int]:
        """Plusieurs lectures du même type, groupées par messages de BATCH commandes."""
        w, values = WIDTH[op], []
        for start in range(0, len(addrs), BATCH):
            chunk = addrs[start:start + BATCH]
            data = self._exchange(b"".join(struct.pack("<BI", op, a) for a in chunk))
            values += [int.from_bytes(data[i * w:(i + 1) * w], "little") for i in range(len(chunk))]
        return values

    def read_block(self, start: int, length: int) -> bytes:
        """Bloc de mémoire brut, dans l'ordre des octets de la PS3 (big-endian), longueur multiple de 8."""
        words = self.read_many(list(range(start, start + length, 8)), READ64)
        return b"".join(v.to_bytes(8, "big") for v in words)
