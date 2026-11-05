"""Lesson 04 — Cycles and recursion_limit (solution)."""

import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    n: int
    trace: Annotated[list, operator.add]


def tick(state: State) -> dict:
    return {"n": state["n"] - 1, "trace": [state["n"]]}


def route(state: State) -> str:
    if state["n"] > 0:
        return "tick"
    return END


def build_graph():
    g = StateGraph(State)
    g.add_node("tick", tick)
    g.add_conditional_edges(START, route)
    g.add_conditional_edges("tick", route)
    return g.compile()
