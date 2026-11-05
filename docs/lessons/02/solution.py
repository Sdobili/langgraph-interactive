"""Lesson 02 — Conditional edges (solution)."""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    n: int
    label: str


def route(state: State) -> str:
    if state["n"] > 0:
        return "pos"
    if state["n"] < 0:
        return "neg"
    return "zero"


def positive(state: State) -> dict:
    return {"label": "positive"}


def negative(state: State) -> dict:
    return {"label": "negative"}


def zero(state: State) -> dict:
    return {"label": "zero"}


def build_graph():
    g = StateGraph(State)
    g.add_node("positive", positive)
    g.add_node("negative", negative)
    g.add_node("zero", zero)
    g.add_conditional_edges(
        START,
        route,
        {"pos": "positive", "neg": "negative", "zero": "zero"},
    )
    g.add_edge("positive", END)
    g.add_edge("negative", END)
    g.add_edge("zero", END)
    return g.compile()
