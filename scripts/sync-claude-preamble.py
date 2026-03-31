#!/usr/bin/env python3
"""Sync shared CLAUDE.md preamble from canonical source to all subrepos."""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
PREAMBLE = ROOT / "docs" / "shared-claude-preamble.md"
REPOS = ["sidequest-api", "sidequest-ui", "sidequest-daemon", "sidequest-content"]
PATTERN = re.compile(
    r"<!-- SHARED-PREAMBLE-START -->.*?<!-- SHARED-PREAMBLE-END -->",
    re.DOTALL,
)


def main():
    if not PREAMBLE.exists():
        print(f"ERROR: {PREAMBLE} not found", file=sys.stderr)
        sys.exit(1)

    # Extract shared content between markers
    preamble_text = PREAMBLE.read_text()
    match = PATTERN.search(preamble_text)
    if not match:
        print("ERROR: No preamble markers in canonical source", file=sys.stderr)
        sys.exit(1)

    shared = match.group(0)

    for repo in REPOS:
        target = ROOT / repo / "CLAUDE.md"
        if not target.exists():
            print(f"SKIP: {target} not found")
            continue

        content = target.read_text()
        if PATTERN.search(content):
            updated = PATTERN.sub(shared, content)
            if updated != content:
                target.write_text(updated)
                print(f"SYNCED: {repo}/CLAUDE.md")
            else:
                print(f"OK (no changes): {repo}/CLAUDE.md")
        else:
            print(f"SKIP: {repo}/CLAUDE.md has no preamble markers")

    print("Done.")


if __name__ == "__main__":
    main()
