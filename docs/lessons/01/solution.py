"""Lesson 01 — Minimal StateGraph (solution)."""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    count: int


def inc(state: State) -> dict:
    return {"count": state["count"] + 1}


def double(state: State) -> dict:
    return {"count": state["count"] * 2}


def build_graph():
    g = StateGraph(State)
    g.add_node("inc", inc)
    g.add_node("double", double)
    g.add_edge(START, "inc")
    g.add_edge("inc", "double")
    g.add_edge("double", END)
    return g.compile()
