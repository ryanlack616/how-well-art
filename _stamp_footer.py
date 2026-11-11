#!/usr/bin/env python3
"""Stamp the "last spoke" footer date on how-well.art.

The footer date is a public receipt of freshness. It is the easiest thing
to forget to update, and a stale receipt is exactly what the reading
room's finding 01 exists to catch. This script makes the date a mechanism
instead of a hand edit.

Usage:
    python _stamp_footer.py           # stamp the last commit date
    python _stamp_footer.py --today   # stamp today's date
    python _stamp_footer.py --check   # exit 1 if the footer is stale

Run it after a content commit, then commit the stamp. Or wire --check into
a pre-push step so a stale receipt blocks the push.
"""

import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "index.html"
PATTERN = re.compile(r"last spoke [A-Z][a-z]+ \d{1,2}, \d{4}")


def _fmt(d: date) -> str:
    return f"{d.strftime('%B')} {d.day}, {d.year}"


def last_commit_date() -> str:
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%ad", "--date=format:%Y-%m-%d"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        )
        y, m, d = (int(x) for x in out.stdout.strip().split("-"))
        return _fmt(date(y, m, d))
    except Exception:
        return _fmt(date.today())


def _parse(s: str) -> date:
    m = re.search(r"([A-Z][a-z]+) (\d{1,2}), (\d{4})", s)
    if not m:
        raise ValueError(s)
    return date(int(m.group(3)), date.strptime(m.group(1), "%B").month, int(m.group(2)))


def stamp(when: str, check: bool = False) -> int:
    if not INDEX.exists():
        print(f"no index.html at {INDEX}", file=sys.stderr)
        return 1
    text = INDEX.read_text(encoding="utf-8")
    m = PATTERN.search(text)
    if not m:
        print("no 'last spoke' line found in index.html", file=sys.stderr)
        return 1
    target = f"last spoke {when}"
    try:
        have, want = _parse(m.group(0)), _parse(target)
    except ValueError:
        print(f"unparseable date: {m.group(0)}", file=sys.stderr)
        return 1
    if check:
        if have >= want:
            print(f"ok: {m.group(0)} (last commit {when})")
            return 0
        print(f"stale: {m.group(0)} (last commit {when})", file=sys.stderr)
        return 1
    if have >= want:
        print(f"already current: {m.group(0)}")
        return 0
    INDEX.write_text(text.replace(m.group(0), target, 1), encoding="utf-8")
    print(f"stamped: {target}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0] if __doc__ else "Stamp the footer date."
    )
    ap.add_argument("--today", action="store_true",
                    help="use today's date instead of the last commit date")
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if the footer date is stale")
    args = ap.parse_args()
    when = _fmt(date.today()) if args.today else last_commit_date()
    return stamp(when, check=args.check)


if __name__ == "__main__":
    sys.exit(main())
