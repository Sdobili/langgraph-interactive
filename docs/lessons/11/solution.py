"""Lesson 11 — Quote each line item, then sum once."""

import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

PRICES = {"sku-a": 20, "sku-b": 15}


class State(TypedDict):
    items: list
    quotes: Annotated[list, operator.add]
    amount: int


def fan_out(state: State):
    if not state["items"]:
        return END
    return [
        Send("quote", {"sku": item["sku"], "qty": item["qty"]})
        for item in state["items"]
    ]


def quote(state: dict) -> dict:
    amount = PRICES[state["sku"]] * state["qty"]
    return {"quotes": [{"sku": state["sku"], "amount": amount}]}


def total(state: State) -> dict:
    return {"amount": sum(row["amount"] for row in state["quotes"])}


def build_graph():
    g = StateGraph(State)
    g.add_node("quote", quote)
    g.add_node("total", total)
    g.add_conditional_edges(START, fan_out)
    g.add_edge("quote", "total")
    g.add_edge("total", END)
    return g.compile()
