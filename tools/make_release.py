"""
Prépare les fichiers d'une release dans dist/ (2026-10-16) : rac_tod.apworld, BCES00052_patch.yml, YAML d'exemple.

  python tools/make_release.py
"""
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from install import ROOT, build_apworld  # noqa: E402

YAML = """name: Player{number}
game: Ratchet and Clank Tools of Destruction
Ratchet and Clank Tools of Destruction:
  # by_difficulty, cobalia, kortog, fastoon, mukow, apogee_space_station, ardolis, rykan_v, sargasso,
  # kreeli_comet, viceron, jasindu, ublik_passage, reepor
  starting_planet: by_difficulty
  starting_planet_difficulty: 25   # 0-99 : how far in the story a random start can be
  device_unlocks: true             # devices missing from the vendor until unlocked
  gold_bolts_required: 10          # 0-31 : gold bolts needed before Fastoon (final) appears
  player_levels: 20                # 0-50 : level-ups that are checks
  death_link: false                # not implemented yet
"""


def main() -> None:
    dist = ROOT / "dist"
    shutil.rmtree(dist, ignore_errors=True)
    dist.mkdir()
    build_apworld(dist / "rac_tod.apworld")
    shutil.copy2(ROOT / "patch" / "BCES00052_patch.yml", dist / "BCES00052_patch.yml")
    (dist / "Ratchet and Clank Tools of Destruction.yaml").write_text(YAML, encoding="utf-8")
    print("dist :", ", ".join(sorted(f.name for f in dist.iterdir())))


if __name__ == "__main__":
    main()
