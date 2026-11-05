"""Lesson 04 — Drain a lookup queue."""

import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph

RECORDS = {
    "order": "Order 1042 is paid.",
    "policy": "Refunds are allowed within 30 days.",
    "account": "The account email is billing@example.com.",
    "shipment": "Shipment has not left the warehouse.",
}


class State(TypedDict):
    query: str
    evidence: Annotated[list, operator.add]
    remaining: list


def fetch(state: State) -> dict:
    queue = list(state["remaining"])
    if not queue:
        return {}
    key = queue.pop(0)
    return {
        "remaining": queue,
        "evidence": [{"tool": "lookup", "key": key, "text": RECORDS[key]}],
    }


def route(state: State) -> str:
    if state["remaining"]:
        return "fetch"
    return END


def build_graph():
    g = StateGraph(State)
    g.add_node("fetch", fetch)
    g.add_conditional_edges(START, route)
    g.add_conditional_edges("fetch", route)
    return g.compile()
