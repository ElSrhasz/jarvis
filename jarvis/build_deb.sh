#!/usr/bin/env python3
"""
Empaqueta JARVIS en un archivo .deb para Linux Mint.

Uso:
    ./build_deb.sh            -> genera dist/jarvis-assistant_1.0.0_all.deb
Requisitos: dpkg-deb (viene incluido en Debian/Ubuntu/Mint).
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

VERSION = "1.0.0"
PKG_NAME = f"jarvis-assistant_{VERSION}_all"

PROJECT_DIR = Path(__file__).resolve().parent          # .../jarvis
PACKAGING_DIR = PROJECT_DIR / "packaging"
BUILD_DIR = PACKAGING_DIR / "build" / PKG_NAME
DIST_DIR = PROJECT_DIR / "dist"

EXCLUDE_DIRS = {"venv", "__pycache__", ".git", "dist", "packaging", "logs"}
EXCLUDE_FILES = {"build_deb.sh", ".env"}  # no forman parte del paquete final


def copy_tree(src: Path, dst: Path):
    """Copiar los fuentes del proyecto al interior del paquete."""
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.name in EXCLUDE_DIRS or item.name in EXCLUDE_FILES:
            continue
        if item.name.endswith(".pyc"):
            continue
        if item.is_dir():
            copy_tree(item, dst / item.name)
        else:
            shutil.copy2(item, dst / item.name)


def main():
    if not shutil.which("dpkg-deb"):
        print("ERROR: dpkg-deb no esta disponible. Instala 'dpkg'.")
        sys.exit(1)

    # Limpieza y creacion del arbol de instalacion
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)

    opt_jarvis = BUILD_DIR / "opt" / "jarvis"
    copy_tree(PROJECT_DIR, opt_jarvis)

    # Enlaces del sistema
    (BUILD_DIR / "usr" / "bin").mkdir(parents=True, exist_ok=True)
    (BUILD_DIR / "usr" / "share" / "applications").mkdir(parents=True, exist_ok=True)
    shutil.copy2(PACKAGING_DIR / "usr" / "bin" / "jarvis",
                 BUILD_DIR / "usr" / "bin" / "jarvis")
    shutil.copy2(PROJECT_DIR / "jarvis.desktop",
                 BUILD_DIR / "usr" / "share" / "applications" / "jarvis.desktop")

    # Metadatos debian/
    shutil.copytree(PACKAGING_DIR / "debian", BUILD_DIR / "DEBIAN")
    for script in ("postinst", "prerm"):
        os.chmod(BUILD_DIR / "DEBIAN" / script, 0o755)
    os.chmod(BUILD_DIR / "usr" / "bin" / "jarvis", 0o755)

    # Construir el .deb
    DIST_DIR.mkdir(exist_ok=True)
    out_deb = DIST_DIR / f"{PKG_NAME}.deb"
    subprocess.run(["dpkg-deb", "--build", "--root-owner-group",
                    str(BUILD_DIR), str(out_deb)], check=True)

    # Verificacion rapida
    subprocess.run(["dpkg-deb", "--info", str(out_deb)], check=True)

    print(f"\nOK: paquete generado -> {out_deb}")
    print("Instalar en Linux Mint con:  sudo apt install ./{}".format(out_deb))


if __name__ == "__main__":
    main()
