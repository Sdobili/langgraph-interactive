"""Tiny LangGraph subset for Lesson 01 — no third-party deps.

Enough for: StateGraph, START, END, add_node, add_edge, compile, invoke.
Linear graphs only (one outgoing edge per node). Default merge = dict.update.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

START = "__start__"
END = "__end__"

__all__ = ["START", "END", "StateGraph", "CompiledGraph", "install_as_langgraph"]


class CompiledGraph:
    def __init__(
        self,
        nodes: Dict[str, Callable],
        edges: Dict[str, str],
        entry: str,
    ) -> None:
        self.nodes = nodes
        self.edges = edges
        self.entry = entry

    def invoke(self, state: dict, config: Any = None) -> dict:
        current = dict(state)
        node: Optional[str] = self.entry
        steps = 0
        while node is not None and node != END:
            if steps > 1000:
                raise RuntimeError("graph exceeded step limit (possible cycle)")
            if node not in self.nodes:
                raise KeyError(f"unknown node: {node!r}")
            update = self.nodes[node](current)
            if update:
                current.update(update)
            node = self.edges.get(node, END)
            steps += 1
        return current


class StateGraph:
    def __init__(self, state_schema: Any = None) -> None:
        self.state_schema = state_schema
        self._nodes: Dict[str, Callable] = {}
        self._edges: Dict[str, str] = {}
        self._entry: Optional[str] = None

    def add_node(self, name: str, action: Callable) -> "StateGraph":
        if name in (START, END):
            raise ValueError(f"reserved node name: {name}")
        self._nodes[name] = action
        return self

    def add_edge(self, source: str, target: str) -> "StateGraph":
        if source == START:
            self._entry = target
        else:
            self._edges[source] = target
        return self

    def compile(self) -> CompiledGraph:
        if self._entry is None:
            raise ValueError("missing edge from START")
        missing = [
            n for n in list(self._edges.keys()) + [self._entry]
            if n not in self._nodes and n != END
        ]
        # also targets that aren't END
        for tgt in self._edges.values():
            if tgt != END and tgt not in self._nodes:
                missing.append(tgt)
        missing = sorted(set(missing))
        if missing:
            raise ValueError(f"edges reference unknown nodes: {missing}")
        return CompiledGraph(dict(self._nodes), dict(self._edges), self._entry)


def install_as_langgraph() -> None:
    """Register this module as langgraph.graph so student imports work."""
    import sys
    import types

    pkg = types.ModuleType("langgraph")
    pkg.__path__ = []  # mark as package
    graph = sys.modules[__name__]
    pkg.graph = graph
    sys.modules["langgraph"] = pkg
    sys.modules["langgraph.graph"] = graph
