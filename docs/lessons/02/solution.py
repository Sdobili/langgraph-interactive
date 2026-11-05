"""Lesson 02 — Route a support ticket."""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    ticket: str
    team: str


def route(state: State) -> str:
    text = state["ticket"].lower()
    if any(word in text for word in ("refund", "invoice", "charge")):
        return "billing"
    if any(word in text for word in ("error", "crash", "bug")):
        return "engineering"
    return "general"


def assign_billing(state: State) -> dict:
    return {"team": "billing"}


def assign_engineering(state: State) -> dict:
    return {"team": "engineering"}


def assign_general(state: State) -> dict:
    return {"team": "general"}


def build_graph():
    g = StateGraph(State)
    g.add_node("assign_billing", assign_billing)
    g.add_node("assign_engineering", assign_engineering)
    g.add_node("assign_general", assign_general)
    g.add_conditional_edges(
        START,
        route,
        {
            "billing": "assign_billing",
            "engineering": "assign_engineering",
            "general": "assign_general",
        },
    )
    g.add_edge("assign_billing", END)
    g.add_edge("assign_engineering", END)
    g.add_edge("assign_general", END)
    return g.compile()
