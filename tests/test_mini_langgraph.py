"""Direct checks for the teaching subset beyond the lesson fixtures."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1] / "docs"
sys.path.insert(0, str(DOCS))

import grade_lib  # noqa: E402
import mini_langgraph as lg  # noqa: E402


class MiniLanggraphTest(unittest.TestCase):
    def test_conditional_edge_sees_the_node_update(self):
        lg.install_as_langgraph()

        def bump(state):
            return {"n": state["n"] + 1}

        def route(state):
            return "big" if state["n"] >= 5 else "small"

        def big(state):
            return {"label": "big"}

        def small(state):
            return {"label": "small"}

        g = lg.StateGraph(dict)
        g.add_node("bump", bump)
        g.add_node("big", big)
        g.add_node("small", small)
        g.add_edge(lg.START, "bump")
        g.add_conditional_edges("bump", route)
        g.add_edge("big", lg.END)
        g.add_edge("small", lg.END)
        self.assertEqual(
            g.compile().invoke({"n": 4, "label": ""}),
            {"n": 5, "label": "big"},
        )

    def test_future_annotations_still_reduce(self):
        src = """
from __future__ import annotations
import operator
from typing import Annotated, TypedDict
from langgraph.graph import END, START, StateGraph

class State(TypedDict):
    log: Annotated[list, operator.add]

def push_a(state: State) -> dict:
    return {"log": ["a"]}

def push_b(state: State) -> dict:
    return {"log": ["b"]}

def build_graph():
    g = StateGraph(State)
    g.add_node("push_a", push_a)
    g.add_node("push_b", push_b)
    g.add_edge(START, "push_a")
    g.add_edge("push_a", "push_b")
    g.add_edge("push_b", END)
    return g.compile()
"""
        result = grade_lib.grade_source(
            src,
            [{"input": {"log": []}, "expected": {"log": ["a", "b"]}}],
        )
        self.assertTrue(result["ok"], "\n".join(result["lines"]))

    def test_recursion_limit_boundary_and_cap(self):
        def tick(state):
            return {"n": state["n"] + 1}

        def route(state):
            return "tick" if state["n"] < 3 else lg.END

        g = lg.StateGraph(dict)
        g.add_node("tick", tick)
        g.add_conditional_edges(lg.START, route)
        g.add_conditional_edges("tick", route)
        app = g.compile()
        self.assertEqual(app.invoke({"n": 0}, {"recursion_limit": 3}), {"n": 3})
        with self.assertRaises(lg.GraphRecursionError):
            app.invoke({"n": 0}, {"recursion_limit": 2})
        with self.assertRaises(ValueError):
            app.invoke({"n": 0}, {"recursion_limit": lg.MAX_RECURSION_LIMIT + 1})

    def test_add_messages_replaces_by_id(self):
        self.assertEqual(
            lg.add_messages(
                [{"role": "user", "content": "hi"}, {"id": "reply", "content": "stale"}],
                {"id": "reply", "content": "echo: hi"},
            ),
            [{"role": "user", "content": "hi"}, {"id": "reply", "content": "echo: hi"}],
        )

    def test_memory_threads_and_overwrite(self):
        lg.install_as_langgraph()
        from langgraph.checkpoint.memory import InMemorySaver, MemorySaver
        from langgraph.errors import GraphRecursionError

        self.assertIs(InMemorySaver, MemorySaver)
        self.assertIs(GraphRecursionError, lg.GraphRecursionError)

        def increment(state):
            return {"count": state["count"] + 1}

        g = lg.StateGraph(dict)
        g.add_node("increment", increment)
        g.add_edge(lg.START, "increment")
        g.add_edge("increment", lg.END)
        app = g.compile(checkpointer=InMemorySaver())
        counter = {"configurable": {"thread_id": "counter"}}
        other = {"configurable": {"thread_id": "other"}}
        self.assertEqual(app.invoke({"count": 0}, counter), {"count": 1})
        self.assertEqual(app.invoke({}, counter), {"count": 2})
        self.assertEqual(app.invoke({"count": 0}, counter), {"count": 1})
        self.assertEqual(app.get_state(other).values, {})

    def test_parallel_and_duplicate_edges_are_rejected(self):
        g = lg.StateGraph(dict)
        g.add_node("a", lambda state: {})
        g.add_edge(lg.START, "a")
        with self.assertRaises(ValueError):
            g.add_edge(lg.START, "a")

        def fanout(state):
            return ["a", "a"]

        g2 = lg.StateGraph(dict)
        g2.add_node("a", lambda state: {})
        g2.add_conditional_edges(lg.START, fanout)
        with self.assertRaises(TypeError):
            g2.compile().invoke({})


if __name__ == "__main__":
    unittest.main()
