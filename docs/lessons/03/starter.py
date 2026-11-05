"""Lesson 03 — Reducers (starter).

log should concatenate across nodes. total still overwrites.
The schema below has no reducer, so the second node replaces log.

invoke({"log": [], "total": 0}) must equal {"log": ["a", "b"], "total": 11}.
"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    # TODO: log: Annotated[list, operator.add]
    log: list
    total: int


def push_a(state: State) -> dict:
    return {"log": ["a"], "total": state["total"] + 1}


def push_b(state: State) -> dict:
    return {"log": ["b"], "total": state["total"] + 10}


def build_graph():
    g = StateGraph(State)
    g.add_node("push_a", push_a)
    g.add_node("push_b", push_b)
    g.add_edge(START, "push_a")
    g.add_edge("push_a", "push_b")
    g.add_edge("push_b", END)
    return g.compile()
