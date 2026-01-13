"""Repo-wide branding renamer.

Replaces old project branding strings in text files only, while skipping data/cache/generated folders.

Usage:
  python scripts/rename_project_branding.py --root .

Notes:
- This is intended for *branding text* (docs/UI strings), not for renaming identifiers.
- It skips binary files by extension allowlist.
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path


DEFAULT_EXTS = {
    ".md",
    ".py",
    ".toml",
    ".yaml",
    ".yml",
    ".txt",
    ".ps1",
    ".bat",
    ".ini",
    ".env",
    "",  # allow files like .env (suffix is '') handled separately
}

SKIP_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "venv",
    "data",
    "exports",
    "reports",
    "node_modules",
    ".git",
    "DataGenie_AI.egg-info",  # generated packaging artifact
}

REPLACEMENTS = [
    ("DataGenie AI", "Autonomous Multi-Agent Business Intelligence System"),
    ("DataGenie 2.0", "Autonomous Multi-Agent Business Intelligence System"),
    ("DataGenie-AI", "autonomous-multi-agent-business-intelligence-system"),
    ("DataGenie Team", "Sabarish-29"),
    ("DATAGENIE 2.0", "AUTONOMOUS MULTI-AGENT BUSINESS INTELLIGENCE SYSTEM"),
    ("datagenie-ai", "autonomous-multi-agent-bi-system"),
    ("sql generator_AI-main", "autonomous-multi-agent-bi-system"),
]

# Regex-based replacements to avoid touching code identifiers like DATAGENIE_* or datagenie_*
REGEX_REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bDataGenie\b"), "Autonomous Multi-Agent Business Intelligence System"),
]


def should_skip_dir(path: Path) -> bool:
    parts = {p for p in path.parts}
    return any(name in parts for name in SKIP_DIR_NAMES)


def is_allowed_file(path: Path) -> bool:
    if path.name in {".env", ".env.example"}:
        return True
    return path.suffix.lower() in DEFAULT_EXTS


def process_file(path: Path) -> bool:
    try:
        original = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Not a UTF-8 text file; skip.
        return False
    except OSError:
        return False

    updated = original
    for old, new in REPLACEMENTS:
        updated = updated.replace(old, new)

    for pattern, repl in REGEX_REPLACEMENTS:
        updated = pattern.sub(repl, updated)

    if updated != original:
        try:
            path.write_text(updated, encoding="utf-8")
            return True
        except OSError:
            return False
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Repo root")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        raise SystemExit(f"Root does not exist: {root}")

    changed = 0
    scanned = 0

    for dirpath, dirnames, filenames in os.walk(root):
        dir_path = Path(dirpath)
        # prune skipped dirs
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES]
        if should_skip_dir(dir_path):
            continue

        for filename in filenames:
            file_path = dir_path / filename
            if not is_allowed_file(file_path):
                continue
            scanned += 1
            if process_file(file_path):
                changed += 1

    print(f"Scanned {scanned} file(s); updated {changed} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
