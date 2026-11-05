"""CLI grader for LangGraph Interactive lessons.

Usage:
  python -m harness.grade 01
  python -m harness.grade 01 --solution
"""

from __future__ import annotations

import argparse
import importlib
import sys
import traceback
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
LESSON_DIRS = {
    "01": "01_minimal_graph",
    "1": "01_minimal_graph",
}


def _banner(title: str) -> None:
    line = "─" * 56
    print(f"\n{line}\n  {title}\n{line}")


def _ok(msg: str) -> None:
    print(f"  ✅  {msg}")


def _fail(msg: str) -> None:
    print(f"  ❌  {msg}")


def _load_module(lesson_dir: Path, use_solution: bool):
    name = "solution" if use_solution else "starter"
    path = lesson_dir / f"{name}.py"
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}")
    # Isolate lesson package so relative imports are not required.
    sys.path.insert(0, str(lesson_dir))
    # Drop cached copy so re-grades pick up edits.
    for key in list(sys.modules):
        if key == name or key.startswith(f"{name}."):
            del sys.modules[key]
    return importlib.import_module(name)


def _check_invoke(graph: Any, inp: dict, expected: dict) -> tuple[bool, Any]:
    got = graph.invoke(inp)
    # Compare only expected keys (extra keys are allowed but reported).
    ok = all(got.get(k) == v for k, v in expected.items())
    return ok, got


def grade_01(mod) -> bool:
    _banner("Lesson 01 — Minimal StateGraph")
    passed = True

    if not hasattr(mod, "build_graph") or not callable(mod.build_graph):
        _fail("build_graph() is missing or not callable — export it from your module.")
        return False
    _ok("build_graph() found")

    try:
        graph = mod.build_graph()
    except Exception as exc:  # noqa: BLE001 — show student errors
        _fail(f"build_graph() raised: {exc.__class__.__name__}: {exc}")
        traceback.print_exc()
        return False

    if graph is None:
        _fail("build_graph() returned None — did you forget return g.compile()?")
        return False
    if not hasattr(graph, "invoke"):
        _fail("build_graph() did not return a compiled graph (no .invoke).")
        return False
    _ok("build_graph() returned a compiled graph")

    cases = [
        ({"count": 3}, {"count": 8}, "(3+1)*2"),
        ({"count": 0}, {"count": 2}, "(0+1)*2"),
        ({"count": 5}, {"count": 12}, "(5+1)*2"),
    ]
    for inp, expected, hint in cases:
        try:
            ok, got = _check_invoke(graph, inp, expected)
        except Exception as exc:  # noqa: BLE001
            _fail(f"invoke({inp!r}) raised: {exc.__class__.__name__}: {exc}")
            traceback.print_exc()
            passed = False
            continue
        if ok:
            _ok(f"invoke({inp!r}) → {got!r}  [{hint}]")
        else:
            _fail(f"invoke({inp!r})")
            print(f"       expected: {expected!r}")
            print(f"       got:      {got!r}")
            print(f"       hint:     START→inc(+1)→double(*2)→END  so {hint} = {expected['count']}")
            passed = False

    return passed


GRADERS: dict[str, Callable[[Any], bool]] = {
    "01": grade_01,
    "1": grade_01,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Grade a LangGraph Interactive lesson")
    parser.add_argument("lesson", help="Lesson id, e.g. 01")
    parser.add_argument(
        "--solution",
        action="store_true",
        help="Grade solution.py instead of starter.py",
    )
    args = parser.parse_args(argv)

    key = args.lesson.strip().lstrip("0") or "0"
    # normalize "01" / "1"
    lookup = args.lesson.strip()
    if lookup not in LESSON_DIRS and key not in LESSON_DIRS:
        print(f"Unknown lesson {args.lesson!r}. Known: {sorted(set(LESSON_DIRS))}")
        return 2

    dirname = LESSON_DIRS.get(lookup) or LESSON_DIRS[key]
    lesson_dir = ROOT / "lessons" / dirname
    which = "solution" if args.solution else "starter"

    print(f"LangGraph Interactive · grading lessons/{dirname}/{which}.py")

    try:
        mod = _load_module(lesson_dir, use_solution=args.solution)
    except Exception as exc:  # noqa: BLE001
        _fail(f"Could not import {which}.py: {exc}")
        traceback.print_exc()
        return 1

    grader = GRADERS.get(lookup) or GRADERS[key]
    ok = grader(mod)

    _banner("Result")
    if ok:
        print("  ✅  PASS — nice work. Move on to the next lesson.")
        return 0
    print("  ❌  FAIL — fix starter.py using the hints above, then re-run.")
    print("       Tip: compare with  python -m harness.grade 01 --solution")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
