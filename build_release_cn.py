# -*- coding: utf-8 -*-
"""Build the Simplified Chinese mod release zip.

Packs the mod framework from the game directory (where the simplified
dictionaries are already deployed) using a whitelist, so player-local
caches (BepInEx/interop, BepInEx/cache) and backup files are excluded.
"""
import os
import zipfile

GAME_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_ZIP = "TheBardsTaleTrilogy_ZH_CN_Mod_v1.0.1.zip"

FILES_TO_PACK = [
    "doorstop_config.ini",
    "winhttp.dll",
    "dotnet",
    "BepInEx/core",
    "BepInEx/plugins/ZHLocalizer.dll",
    "BepInEx/plugins/arialuni_sdf_u2018",
    "BepInEx/plugins/btr_localization_zh.txt",
    "BepInEx/plugins/combat_translations.txt",
]


def main():
    print(f"Building {OUTPUT_ZIP} from {GAME_DIR} ...")
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zipf:
        for item in FILES_TO_PACK:
            item_path = os.path.join(GAME_DIR, item)
            if not os.path.exists(item_path):
                print(f"  WARN: not found, skipped: {item}")
                continue
            if os.path.isfile(item_path):
                print(f"  file: {item}")
                zipf.write(item_path, item)
            else:
                for root, _dirs, files in os.walk(item_path):
                    for file in files:
                        full_path = os.path.join(root, file)
                        zipf.write(full_path, os.path.relpath(full_path, GAME_DIR))
                print(f"  dir:  {item}")
    size = os.path.getsize(OUTPUT_ZIP)
    print(f"Done: {OUTPUT_ZIP} ({size / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    main()
