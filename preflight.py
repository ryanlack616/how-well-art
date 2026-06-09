#!/usr/bin/env python3
"""
preflight.py — release gate for how-well.art (GitHub Pages, CNAME how-well.art).

Deploy mechanism: this repo IS the site. `git push origin main` publishes.
There is no FTP step. Untracked files ship ONLY if staged. So the encoding
gate belongs here, before commit/push — the kiln before the fire.

The recurring corruption is the Windows/PowerShell deploy path writing UTF-8
text through a CP437 / Latin-1 / BOM round-trip. Three families have appeared:

  1. U+FFFD replacement chars      — bytes that could not decode at all
  2. CP437 mojibake (Gamma-family) — UTF-8 em/en-dash/lozenge read as CP437:
        "\u0393\u00c7\u00f6" -> em-dash, "\u0393\u00c7\u00f4" -> en-dash,
        "\u0393\u00f9\u00e8" -> lozenge (the box-drawing \u2502 lead byte 0xC2
        also shows up as the box char \u252c in the degree sign "\u252c\u00b0")
  3. Stray 0xC2 lead byte         — "\u252c\u00b0C" instead of "\u00b0C"

Detection is on the DECODED text, by signature character, because those code
points have no legitimate use on an English ceramics/poetry site. Deliberate
references to the replacement char in prose must use the &#xFFFD; HTML entity
(not the literal), so this scan stays meaningful.

Also flags a UTF-8 BOM at file start (the other half of the same pipeline bug).

Exit 0 = clean, safe to ship. Exit 1 = corruption found, do not push.
"""
from __future__ import annotations

import glob
import sys

# Unconditional signature code points. Any occurrence on this site is corruption.
SIGNATURES = {
    "\uFFFD": "U+FFFD replacement char (undecodable bytes)",
    "\u0393": "U+0393 GREEK CAPITAL GAMMA (CP437 mojibake lead)",
}
BOM = "\ufeff"

# U+252C is genuine box-drawing when it sits inside a run of box-drawing chars
# (legitimate ASCII-art diagrams). It is corruption only when adjacent to a
# non-box char, e.g. the degree-sign bug "\u252c\u00b0C". So it is checked in
# context rather than listed unconditionally above.
BOX_BLOCK = range(0x2500, 0x2580)


def _is_box(ch: str | None) -> bool:
    return ch is not None and ord(ch) in BOX_BLOCK


def scan_file(path: str) -> list[tuple[int, int, str, str]]:
    hits: list[tuple[int, int, str, str]] = []
    raw = open(path, "rb").read()
    if raw.startswith(b"\xef\xbb\xbf"):
        hits.append((1, 1, "<BOM>", "UTF-8 BOM at file start"))
    text = raw.decode("utf-8", errors="replace")
    for lineno, line in enumerate(text.splitlines(), 1):
        for col, ch in enumerate(line, 1):
            if ch in SIGNATURES:
                snippet = line[max(0, col - 16): col + 16].strip()
                hits.append((lineno, col, snippet, SIGNATURES[ch]))
            elif ch == "\u252C":
                prev = line[col - 2] if col >= 2 else None
                nxt = line[col] if col < len(line) else None
                if not (_is_box(prev) or _is_box(nxt)):
                    snippet = line[max(0, col - 16): col + 16].strip()
                    hits.append((lineno, col, snippet,
                                 "U+252C box-drawing outside diagram "
                                 "(CP437 0xC2 mis-decode, e.g. degree sign)"))
            elif ch == BOM and lineno > 1:
                hits.append((lineno, col, line.strip()[:32], "stray BOM/ZWNBSP"))
    return hits


def main(argv: list[str]) -> int:
    targets = argv[1:] or sorted(glob.glob("*.html"))
    total = 0
    for path in targets:
        try:
            hits = scan_file(path)
        except FileNotFoundError:
            print(f"  ?? {path}: not found")
            continue
        if hits:
            print(f"FAIL {path}: {len(hits)} corrupted code point(s)")
            for lineno, col, snippet, why in hits[:40]:
                print(f"     {lineno}:{col}  {why}\n            ...{snippet}...")
            if len(hits) > 40:
                print(f"     ... and {len(hits) - 40} more")
            total += len(hits)
        else:
            print(f"ok   {path}")
    print()
    if total:
        print(f"PREFLIGHT FAILED: {total} corrupted code point(s). Do not push.")
        return 1
    print(f"PREFLIGHT CLEAN: {len(targets)} file(s), no corruption. Safe to ship.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
