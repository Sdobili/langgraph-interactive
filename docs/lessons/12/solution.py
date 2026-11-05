"""Lesson 12 — Remember a customer note across threads."""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.store.memory import InMemoryStore


class State(TypedDict):
    customer_id: str
    note: str
    saved: str


def remember(state: State, store: InMemoryStore) -> dict:
    namespace = ("customers", state["customer_id"])
    if state.get("note"):
        store.put(namespace, "profile", {"note": state["note"]})
        saved = state["note"]
    else:
        item = store.get(namespace, "profile")
        saved = "" if item is None else item.value["note"]
    return {"saved": saved}


def build_graph():
    g = StateGraph(State)
    g.add_node("remember", remember)
    g.add_edge(START, "remember")
    g.add_edge("remember", END)
    return g.compile(store=InMemoryStore())
