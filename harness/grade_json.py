"""Structured grader used by the web UI (and CLI --json if wired)."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import traceback
from pathlib import Path
from types import ModuleType
from typing import Any


def _load_from_source(source: str, module_name: str = "student_submission") -> ModuleType:
    """Write source to a temp file and import it as a fresh module."""
    td = tempfile.mkdtemp(prefix="lgi_")
    path = Path(td) / f"{module_name}.py"
    path.write_text(source, encoding="utf-8")
    # Drop any previous copy so re-grades pick up new code.
    for key in list(sys.modules):
        if key == module_name or key.startswith(f"{module_name}."):
            del sys.modules[key]
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _check_invoke(graph: Any, inp: dict, expected: dict) -> tuple[bool, Any]:
    got = graph.invoke(inp)
    ok = all(got.get(k) == v for k, v in expected.items())
    return ok, got


def grade_01_source(source: str) -> dict:
    """Grade lesson-01 source string. Returns {ok: bool, lines: list[str]}."""
    lines: list[str] = []
    lines.append("Lesson 01 — Minimal StateGraph")

    try:
        mod = _load_from_source(source)
    except Exception as exc:  # noqa: BLE001
        lines.append(f"❌ Could not import submission: {exc.__class__.__name__}: {exc}")
        tb = traceback.format_exc(limit=5)
        for row in tb.strip().splitlines()[-8:]:
            lines.append(f"   {row}")
        return {"ok": False, "lines": lines}

    if not hasattr(mod, "build_graph") or not callable(mod.build_graph):
        lines.append("❌ build_graph() is missing or not callable — export it from your module.")
        return {"ok": False, "lines": lines}
    lines.append("✅ build_graph() found")

    try:
        graph = mod.build_graph()
    except Exception as exc:  # noqa: BLE001
        lines.append(f"❌ build_graph() raised: {exc.__class__.__name__}: {exc}")
        return {"ok": False, "lines": lines}

    if graph is None:
        lines.append("❌ build_graph() returned None — did you forget return g.compile()?")
        return {"ok": False, "lines": lines}
    if not hasattr(graph, "invoke"):
        lines.append("❌ build_graph() did not return a compiled graph (no .invoke).")
        return {"ok": False, "lines": lines}
    lines.append("✅ build_graph() returned a compiled graph")

    passed = True
    cases = [
        ({"count": 3}, {"count": 8}, "(3+1)*2"),
        ({"count": 0}, {"count": 2}, "(0+1)*2"),
        ({"count": 5}, {"count": 12}, "(5+1)*2"),
    ]
    for inp, expected, hint in cases:
        try:
            ok, got = _check_invoke(graph, inp, expected)
        except Exception as exc:  # noqa: BLE001
            lines.append(f"❌ invoke({inp!r}) raised: {exc.__class__.__name__}: {exc}")
            passed = False
            continue
        if ok:
            lines.append(f"✅ invoke({inp!r}) → {got!r}  [{hint}]")
        else:
            lines.append(f"❌ invoke({inp!r})")
            lines.append(f"   expected: {expected!r}")
            lines.append(f"   got:      {got!r}")
            lines.append(
                f"   hint: START→inc(+1)→double(*2)→END  so {hint} = {expected['count']}"
            )
            passed = False

    if passed:
        lines.append("✅ PASS — nice work.")
    else:
        lines.append("❌ FAIL — fix the TODOs using the hints above.")
    return {"ok": passed, "lines": lines}
