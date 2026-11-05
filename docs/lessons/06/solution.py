"""Lesson 06 — Keep a support thread."""

from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages


class State(TypedDict):
    messages: Annotated[list, add_messages]


def reply(state: State) -> dict:
    text = str(state["messages"][-1].get("content", "")).lower()
    if "refund" in text:
        content = "Refunds are allowed within 30 days. What is the order id?"
    elif "order" in text:
        content = "Order 1042 is eligible. I have queued the refund."
    else:
        content = "I can help with refunds. Include the order id."
    return {"messages": [{"role": "assistant", "content": content}]}


def build_graph():
    g = StateGraph(State)
    g.add_node("reply", reply)
    g.add_edge(START, "reply")
    g.add_edge("reply", END)
    return g.compile(checkpointer=InMemorySaver())
