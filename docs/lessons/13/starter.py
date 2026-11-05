"""Lesson 13 — Retry the refund charge after a gateway timeout.

The first call for an order raises TimeoutError. The second call
on that same order writes the receipt. RetryPolicy(max_attempts=2)
covers both calls.
"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    order_id: str
    amount: int
    receipt: str


def charge(state: State) -> dict:
    seen = getattr(charge, "seen", None)
    if seen != state["order_id"]:
        charge.calls = 0
        charge.seen = state["order_id"]
    charge.calls += 1
    if charge.calls == 1:
        raise TimeoutError("gateway timeout")
    return {"receipt": f"refund-{state['order_id']}-{state['amount']}"}


def build_graph():
    g = StateGraph(State)
    # TODO: add_node("charge", charge, retry=RetryPolicy(max_attempts=2))
    g.add_node("charge", charge)
    g.add_edge(START, "charge")
    g.add_edge("charge", END)
    return g.compile()
