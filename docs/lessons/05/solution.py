"""Lesson 05 — Messages and a fake echo model (solution)."""

from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages


class State(TypedDict):
    messages: Annotated[list, add_messages]


def fake_model(messages: list) -> dict:
    """Scripted stand-in. Not GenericFakeChatModel and not a network call."""
    text = ""
    for msg in reversed(messages):
        if isinstance(msg, dict) and msg.get("role") == "user":
            text = str(msg.get("content", ""))
            break
    return {"id": "reply", "role": "assistant", "content": "echo: " + text}


def echo(state: State) -> dict:
    return {"messages": [fake_model(state["messages"])]}


def build_graph():
    g = StateGraph(State)
    g.add_node("echo", echo)
    g.add_edge(START, "echo")
    g.add_edge("echo", END)
    return g.compile()
