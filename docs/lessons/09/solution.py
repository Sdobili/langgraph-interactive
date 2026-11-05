"""Lesson 09 — Rewrite the team, then rerun only the draft."""

from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    ticket: str
    team: str
    reply: str


def classify(state: State) -> dict:
    text = state["ticket"].lower()
    if "refund" in text or "invoice" in text:
        return {"team": "billing"}
    return {"team": "engineering"}


def draft(state: State) -> dict:
    if state["team"] == "billing":
        reply = "Billing will process the refund."
    else:
        reply = "Engineering will investigate the error."
    return {"reply": reply}


def build_graph():
    g = StateGraph(State)
    g.add_node("classify", classify)
    g.add_node("draft", draft)
    g.add_edge(START, "classify")
    g.add_edge("classify", "draft")
    g.add_edge("draft", END)
    return g.compile(checkpointer=InMemorySaver())
