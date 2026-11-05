"""Lesson 06 — InMemorySaver checkpoint (solution)."""

from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    count: int


def increment(state: State) -> dict:
    return {"count": state["count"] + 1}


def build_graph():
    g = StateGraph(State)
    g.add_node("increment", increment)
    g.add_edge(START, "increment")
    g.add_edge("increment", END)
    return g.compile(checkpointer=InMemorySaver())
