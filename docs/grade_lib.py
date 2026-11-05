"""Grade student source against JSON cases. Shared by Pyodide and local smoke tests.

A case is either one call::

    {"input": {...}, "expected": {...}}
    {"input": {...}, "config": {...}, "raises": "GraphRecursionError"}

or a sequence that reuses one compiled graph (checkpoints)::

    {"steps": [ ...same call objects..., {"get_state": {...}, "expected": {...}} ]}
"""

from __future__ import annotations

import importlib
import json
import traceback
import types
from typing import Any


def grade_source(src: str, cases: list) -> dict:
    import mini_langgraph

    importlib.reload(mini_langgraph)
    mini_langgraph.install_as_langgraph()

    result: dict[str, Any] = {"ok": False, "lines": [], "error": None}
    module = types.ModuleType("student")
    import sys

    sys.modules["student"] = module
    ns = module.__dict__
    try:
        try:
            exec(compile(src, "<student>", "exec"), ns, ns)
        except Exception as exc:
            result["lines"].append(f"❌ exec error: {type(exc).__name__}: {exc}")
            result["error"] = traceback.format_exc()
            return result

        if "build_graph" not in ns or not callable(ns["build_graph"]):
            result["lines"].append("❌ build_graph() not defined")
            return result

        lines: list[str] = []
        all_ok = True
        for case in cases:
            try:
                graph = ns["build_graph"]()
            except Exception as exc:
                all_ok = False
                lines.append(f"❌ build_graph() raised: {type(exc).__name__}: {exc}")
                break
            if graph is None:
                all_ok = False
                lines.append("❌ returned None — did you forget return g.compile()?")
                break
            if not hasattr(graph, "invoke"):
                all_ok = False
                lines.append("❌ compiled object has no invoke()")
                break
            steps = case["steps"] if isinstance(case, dict) and "steps" in case else [case]
            for step in steps:
                ok, line = _run_step(graph, step)
                lines.append(line)
                if not ok:
                    all_ok = False
        result["lines"] = lines
        result["ok"] = bool(all_ok and lines)
        header = "✅ PASS — all cases matched" if result["ok"] else "❌ FAIL — see cases below"
        result["lines"].insert(0, header)
        return result
    finally:
        sys.modules.pop("student", None)


def _run_step(graph: Any, step: dict) -> tuple[bool, str]:
    if "get_state" in step:
        return _run_get_state(graph, step)
    if "input" not in step:
        return False, "❌ grader case needs input, get_state, or steps"
    config = step.get("config")
    label = _invoke_label(step)
    raises = step.get("raises")
    try:
        out = graph.invoke(step["input"], config)
    except Exception as exc:
        if raises and type(exc).__name__ == raises:
            return True, f"✅ {label} raised {raises}: {exc}"
        return False, f"❌ {label} raised {type(exc).__name__}: {exc}"
    if raises:
        return False, f"❌ {label} → {_dump(out)}  (expected {raises})"
    if "expected" not in step:
        return False, f"❌ {label} is missing an expected value"
    if out == step["expected"]:
        return True, f"✅ {label} → {_dump(out)}"
    return (
        False,
        f"❌ {label} → {_dump(out)}  (expected {_dump(step['expected'])})",
    )


def _run_get_state(graph: Any, step: dict) -> tuple[bool, str]:
    config = step["get_state"]
    label = f"get_state({_dump(config)})"
    if not hasattr(graph, "get_state"):
        return False, f"❌ {label} — compiled graph has no get_state()"
    try:
        snap = graph.get_state(config)
        got = snap.values
    except Exception as exc:
        return False, f"❌ {label} raised {type(exc).__name__}: {exc}"
    expected = step.get("expected")
    if got == expected:
        return True, f"✅ {label} → {_dump(got)}"
    return False, f"❌ {label} → {_dump(got)}  (expected {_dump(expected)})"


def _invoke_label(step: dict) -> str:
    rendered = f"invoke({_dump(step.get('input'))}"
    if "config" in step:
        rendered += f", config={_dump(step['config'])}"
    return rendered + ")"


def _dump(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False)
    except TypeError:
        return repr(obj)
