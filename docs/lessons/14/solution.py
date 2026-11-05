"""Lesson 14 — Keep the last three messages, then answer."""

from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages


def keep_last_three(left, right):
    return add_messages(left, right)[-3:]


class State(TypedDict):
    messages: Annotated[list, keep_last_three]


def reply(state: State) -> dict:
    text = ""
    for message in reversed(state["messages"]):
        if isinstance(message, dict) and message.get("role") == "user":
            text = str(message.get("content", ""))
            break
    if "refund" in text.lower():
        content = "Refunds are allowed within 30 days."
    else:
        content = "Ask me about a refund."
    return {"messages": [{"role": "assistant", "content": content}]}


def build_graph():
    g = StateGraph(State)
    g.add_node("reply", reply)
    g.add_edge(START, "reply")
    g.add_edge("reply", END)
    return g.compile()
