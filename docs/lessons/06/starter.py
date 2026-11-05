"""Lesson 06 — InMemorySaver checkpoint (starter).

Each invoke on thread "counter" should add 1 to the saved count.
Passing {} continues from memory. A different thread_id starts clean.

This starter compiles with no checkpointer, so the second invoke
sees an empty input and returns 1 again.
"""

from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    count: int


def increment(state: State) -> dict:
    return {"count": state.get("count", 0) + 1}


def build_graph():
    g = StateGraph(State)
    g.add_node("increment", increment)
    g.add_edge(START, "increment")
    g.add_edge("increment", END)
    # TODO: return g.compile(checkpointer=InMemorySaver())
    return g.compile()
