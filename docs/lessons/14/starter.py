"""Lesson 14 — Keep the last three messages, then answer.

The reducer must run add_messages and then keep only the last three.
A short thread stays intact.
"""

from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages


class State(TypedDict):
    # TODO: Annotated[list, keep_last_three]
    messages: Annotated[list, add_messages]


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
