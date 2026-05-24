#!/usr/bin/env python3

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
BUILD = ROOT / "build"


def main() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)
    if BUILD.exists():
        shutil.rmtree(BUILD)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        str(ROOT / "tetris.spec"),
    ]
    print("[build]", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=ROOT)

    built = DIST / ("tetris.exe" if sys.platform.startswith("win") else "tetris")
    if built.exists():
        print(f"[build] output: {built}")
    else:
        print("[build] build finished but output was not found.")
        sys.exit(1)


if __name__ == "__main__":
    main()
