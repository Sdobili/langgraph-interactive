"""Lesson 04 — Cycles and recursion_limit (starter).

tick should repeat while n > 0, then stop at END.
This starter runs tick once and always stops, so n=3 never finishes
and a tight recursion_limit never fires.

invoke({"n": 3, "trace": []}) == {"n": 0, "trace": [3, 2, 1]}
invoke({"n": 4, "trace": []}, config={"recursion_limit": 2}) raises GraphRecursionError
"""

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
    # TODO: conditional edges from START and from "tick" via route,
    # so the graph can loop back to tick or stop at END.
    g.add_edge(START, "tick")
    g.add_edge("tick", END)
    return g.compile()
