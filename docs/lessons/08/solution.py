"""Lesson 08 — Pause before the refund is sent."""

from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages


class State(TypedDict):
    messages: Annotated[list, add_messages]
    approved: bool


def draft(state: State) -> dict:
    return {
        "messages": [
            {
                "id": "draft",
                "role": "assistant",
                "content": "Refund order 1042 for the paid amount.",
            }
        ]
    }


def send(state: State) -> dict:
    if state.get("approved"):
        content = "Sent the refund confirmation."
    else:
        content = "Held for review."
    return {"messages": [{"role": "system", "content": content}]}


def build_graph():
    g = StateGraph(State)
    g.add_node("draft", draft)
    g.add_node("send", send)
    g.add_edge(START, "draft")
    g.add_edge("draft", "send")
    g.add_edge("send", END)
    return g.compile(checkpointer=InMemorySaver(), interrupt_before=["send"])
