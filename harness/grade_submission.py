"""CLI: grade a Python file as lesson 01, print JSON to stdout.

  python -m harness.grade_submission /path/to/code.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from harness.grade_json import grade_01_source


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print(json.dumps({"ok": False, "lines": ["❌ Usage: grade_submission <file.py>"]}))
        return 2
    path = Path(args[0])
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(json.dumps({"ok": False, "lines": [f"❌ Cannot read {path}: {exc}"]}))
        return 1
    result = grade_01_source(source)
    print(json.dumps(result))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
