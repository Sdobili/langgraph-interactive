"""Pytest wrapper around the lesson-01 contract.

Default: grades starter.py (expected to fail until filled in).
Set LG_INTERACTIVE_MODULE=solution to grade the reference solution.
"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest

LESSON_DIR = Path(__file__).resolve().parent
MODULE_NAME = os.environ.get("LG_INTERACTIVE_MODULE", "starter")


@pytest.fixture(scope="module")
def student_mod():
    sys.path.insert(0, str(LESSON_DIR))
    for key in list(sys.modules):
        if key == MODULE_NAME or key.startswith(f"{MODULE_NAME}."):
            del sys.modules[key]
    return importlib.import_module(MODULE_NAME)


@pytest.fixture(scope="module")
def graph(student_mod):
    assert hasattr(student_mod, "build_graph"), "export build_graph()"
    g = student_mod.build_graph()
    assert g is not None, "build_graph() returned None"
    assert hasattr(g, "invoke"), "build_graph() must return a compiled graph"
    return g


@pytest.mark.parametrize(
    "inp,expected",
    [
        ({"count": 3}, {"count": 8}),
        ({"count": 0}, {"count": 2}),
        ({"count": 5}, {"count": 12}),
    ],
)
def test_invoke(graph, inp, expected):
    got = graph.invoke(inp)
    for k, v in expected.items():
        assert got.get(k) == v, f"invoke({inp!r}): expected {expected!r}, got {got!r}"
