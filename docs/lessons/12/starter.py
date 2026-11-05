"""Lesson 12 — Remember a customer note across threads.

A later thread with an empty note must still read customer 1042's profile.
The store is shared by the compiled graph. The checkpointer is not.
"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.store.memory import InMemoryStore


class State(TypedDict):
    customer_id: str
    note: str
    saved: str


def remember(state: State) -> dict:
    # TODO: accept store and put/get ("customers", customer_id) / "profile".
    return {"saved": state.get("note") or ""}


def build_graph():
    g = StateGraph(State)
    g.add_node("remember", remember)
    g.add_edge(START, "remember")
    g.add_edge("remember", END)
    return g.compile(store=InMemoryStore())
