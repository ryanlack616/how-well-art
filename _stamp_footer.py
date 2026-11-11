#!/usr/bin/env python3
"""Stamp the footer receipt on how-well.art.

The footer carries two receipts, not one:

    last spoke <date>   — the last time the site's own voice authored content
    maintained <date>   — the last time the site was maintained

They are different claims. Pass 01 found that a single "last spoke" date was
a false receipt when it lagged the content. Pass 02 found the opposite: a
maintenance pass that stamps "last spoke" is a false receipt in the other
direction, because maintenance is not speech. Keeping both dates keeps the
claim honest in both directions.

Usage:
    python _stamp_footer.py                  # set maintained to the last commit date
    python _stamp_footer.py --today          # set maintained to today
    python _stamp_footer.py --spoke "June 13, 2026"
    python _stamp_footer.py --check          # exit 1 if maintained is behind the last commit

Run it after a commit, then commit the stamp. Or wire --check into a
pre-push step so a stale receipt blocks the push.
"""

import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "index.html"

DATE_RE = r"[A-Z][a-z]+ \d{1,2}, \d{4}"
PATTERN = re.compile(
    rf"last spoke (?P<spoke>{DATE_RE})(?: · maintained (?P<maintained>{DATE_RE}))?"
)


def _fmt(d: date) -> str:
    return f"{d.strftime('%B')} {d.day}, {d.year}"


def _parse(s: str) -> date:
    m = re.search(rf"({DATE_RE})", s)
    if not m:
        raise ValueError(s)
    mm = re.match(r"([A-Z][a-z]+) (\d{1,2}), (\d{4})", m.group(1))
    if not mm:
        raise ValueError(s)
    month, day, year = mm.groups()
    return date(int(year), date.strptime(month, "%B").month, int(day))


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


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0] if __doc__ else "Stamp the footer receipt."
    )
    ap.add_argument("--today", action="store_true", help="use today's date")
    ap.add_argument("--spoke", metavar="DATE", help="set the 'last spoke' date")
    ap.add_argument("--check", action="store_true", help="exit 1 if 'maintained' is stale")
    args = ap.parse_args()

    text = INDEX.read_text(encoding="utf-8")
    m = PATTERN.search(text)
    if not m:
        print("no 'last spoke' line found in index.html", file=sys.stderr)
        return 1

    spoke = args.spoke or m.group("spoke")
    maintained = _fmt(date.today()) if args.today else last_commit_date()
    target = f"last spoke {spoke} · maintained {maintained}"

    if args.check:
        try:
            have = _parse(m.group("maintained") or m.group("spoke"))
            want = _parse(maintained)
        except ValueError:
            print(f"unparseable date in: {m.group(0)}", file=sys.stderr)
            return 1
        if have >= want:
            print(f"ok: {m.group(0)}")
            return 0
        print(f"stale: {m.group(0)} (last commit {maintained})", file=sys.stderr)
        return 1

    if m.group(0) == target:
        print(f"already current: {target}")
        return 0
    INDEX.write_text(text.replace(m.group(0), target, 1), encoding="utf-8")
    print(f"stamped: {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
