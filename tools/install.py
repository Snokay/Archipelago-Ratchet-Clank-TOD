"""
Installe le monde Tools of Destruction (2026-10-14).

  python tools/install.py [--archipelago-dir D:\\Archipelago] [--rpcs3-dir D:\\rpcs3-...]

- Empaquette apworld/rac_tod/ en rac_tod.apworld dans <Archipelago>/custom_worlds/ (client compris).
- Copie patch/BCES00052_patch.yml dans <RPCS3>/patches/ (à cocher une fois dans « Gérer les patchs »).
"""
import argparse
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_AP_DIR = Path(r"D:\Archipelago")
DEFAULT_RPCS3_DIR = Path(r"D:\rpcs3-v0.0.43-20284-2ba2f75b_win64_msvc")


def build_apworld(out: Path) -> None:
    src = ROOT / "apworld" / "rac_tod"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(src.rglob("*")):
            if f.is_file() and "__pycache__" not in f.parts:
                z.write(f, Path("rac_tod") / f.relative_to(src))
    print(f"apworld : {out}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archipelago-dir", type=Path, default=DEFAULT_AP_DIR)
    ap.add_argument("--rpcs3-dir", type=Path, default=DEFAULT_RPCS3_DIR)
    args = ap.parse_args()
    build_apworld(args.archipelago_dir / "custom_worlds" / "rac_tod.apworld")
    patches = args.rpcs3_dir / "patches"
    if patches.is_dir():
        shutil.copy2(ROOT / "patch" / "BCES00052_patch.yml", patches / "BCES00052_patch.yml")
        print(f"patch : {patches / 'BCES00052_patch.yml'}")
    else:
        print(f"ATTENTION : {patches} introuvable, patch pas copié")


if __name__ == "__main__":
    main()
