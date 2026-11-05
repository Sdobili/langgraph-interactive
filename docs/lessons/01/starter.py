"""Lesson 01 — Minimal StateGraph (starter).

Fill in the TODOs so build_graph() returns a compiled graph:

  State:  TypedDict with count: int
  Nodes:  inc  (+1),  double  (*2)
  Edges:  START → inc → double → END

Then: invoke({"count": 3}) must equal {"count": 8}.
"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


# TODO 1: define State as a TypedDict with one field: count: int
class State(TypedDict):
    pass  # replace with: count: int


# TODO 2: return {"count": state["count"] + 1}
def inc(state: State) -> dict:
    pass


# TODO 3: return {"count": state["count"] * 2}
def double(state: State) -> dict:
    pass


def build_graph():
    """Build and compile the linear graph. Must be exported for the grader."""
    # TODO 4: StateGraph(State), add_node("inc", ...), add_node("double", ...),
    #         edges START→inc→double→END, then return g.compile()
    pass
