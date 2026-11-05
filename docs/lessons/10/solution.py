"""Lesson 10 — Research subgraph, then answer from its draft."""

import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph


class ResearchState(TypedDict):
    query: str
    passages: list
    draft: str


class State(TypedDict):
    query: str
    passages: Annotated[list, operator.add]
    draft: str
    answer: str


def retrieve(state: ResearchState) -> dict:
    return {
        "passages": [
            {"source": "policy", "text": "Refunds are allowed within 30 days."}
        ]
    }


def note(state: ResearchState) -> dict:
    text = state["passages"][-1]["text"]
    return {"draft": text}


def build_research():
    g = StateGraph(ResearchState)
    g.add_node("retrieve", retrieve)
    g.add_node("note", note)
    g.add_edge(START, "retrieve")
    g.add_edge("retrieve", "note")
    g.add_edge("note", END)
    return g.compile()


def answer(state: State) -> dict:
    return {"answer": state["draft"]}


def build_graph():
    g = StateGraph(State)
    g.add_node("research", build_research())
    g.add_node("answer", answer)
    g.add_edge(START, "research")
    g.add_edge("research", "answer")
    g.add_edge("answer", END)
    return g.compile()
