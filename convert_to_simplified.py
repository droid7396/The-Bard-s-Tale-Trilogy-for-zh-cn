# -*- coding: utf-8 -*-
"""Convert pmanyeh's Traditional Chinese dictionaries to Simplified Chinese (tw2sp).

Only converts lines/text segments containing CJK ideographs; ASCII (structure,
regex, tags) passes through OpenCC untouched, so file structure is preserved.
"""
import re
import sys
from pathlib import Path
from opencc import OpenCC

REPO = Path(__file__).parent
REPO_OUT = REPO / "simplified_out"
GAME_PLUGINS = REPO.parent / "BepInEx" / "plugins"

CJK = re.compile(r"[\u3400-\u9fff\uf900-\ufaff]")

cc = OpenCC("tw2sp")


def convert_line(line: str) -> str:
    if not CJK.search(line):
        return line
    return cc.convert(line)


def convert_main(src: Path, dst: Path):
    n = 0
    with open(src, encoding="utf-8", newline="") as f, open(dst, "w", encoding="utf-8", newline="") as g:
        for line in f:
            body = line.rstrip("\r\n")
            eol = line[len(body):] or "\r\n"
            out = convert_line(body)
            if out != body:
                n += 1
            g.write(out + eol)
    return n


def convert_combat(src: Path, dst: Path):
    n = 0
    with open(src, encoding="utf-8", newline="") as f, open(dst, "w", encoding="utf-8", newline="") as g:
        for line in f:
            body = line.rstrip("\r\n")
            eol = line[len(body):] or "\r\n"
            if "::ZH::" in body:
                left, right = body.split("::ZH::", 1)
                right_new = cc.convert(right) if CJK.search(right) else right
                out = left + "::ZH::" + right_new
            else:
                out = convert_line(body)
            if out != body:
                n += 1
            g.write(out + eol)
    return n


def charset_diff(trad_file: Path, simp_file: Path):
    def chars(p):
        s = set()
        with open(p, encoding="utf-8") as f:
            for line in f:
                s.update(ch for ch in line if CJK.match(ch))
        return s

    a, b = chars(trad_file), chars(simp_file)
    return b - a


def main():
    REPO_OUT.mkdir(exist_ok=True)
    files_main = ["btr_localization_zh.txt"]
    for name in files_main:
        src = GAME_PLUGINS / name
        dst = REPO_OUT / name
        if not src.exists():
            src = REPO / "ZHLocalizer" / name
        n = convert_main(src, dst)
        print(f"{name}: {n} lines converted")
        diff = charset_diff(src, dst)
        print(f"  charset: trad={len(charset_diff(src, src)) and '' or ''}", end="")
        print(f"new simplified chars not in trad file: {len(diff)}")
        if diff:
            print("  chars:", "".join(sorted(diff)))

    src = GAME_PLUGINS / "combat_translations.txt"
    dst = REPO_OUT / "combat_translations.txt"
    n = convert_combat(src, dst)
    print(f"combat_translations.txt: {n} lines converted")
    diff = charset_diff(src, dst)
    print(f"  new simplified chars: {len(diff)}")
    if diff:
        print("  chars:", "".join(sorted(diff)))

    # reference doc for players (not loaded by plugin)
    src = REPO / "ZHLocalizer" / "riddle_answers.csv"
    if src.exists():
        n = convert_main(src, REPO_OUT / "riddle_answers.csv")
        print(f"riddle_answers.csv (reference doc): {n} lines converted")


if __name__ == "__main__":
    main()
