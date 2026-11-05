"""Lesson 03 — Accumulate retrieved passages."""

import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    query: str
    passages: Annotated[list, operator.add]
    draft: str


def retrieve(state: State) -> dict:
    return {
        "passages": [{"source": "faq", "text": state["query"]}],
        "draft": "Looking up the policy.",
    }


def write(state: State) -> dict:
    return {
        "passages": [{"source": "policy", "text": "Refunds are allowed within 30 days."}],
        "draft": "Refunds are allowed within 30 days.",
    }


def build_graph():
    g = StateGraph(State)
    g.add_node("retrieve", retrieve)
    g.add_node("write", write)
    g.add_edge(START, "retrieve")
    g.add_edge("retrieve", "write")
    g.add_edge("write", END)
    return g.compile()
