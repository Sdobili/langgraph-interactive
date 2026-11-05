"""Lesson 05 — Messages and a fake echo model (starter).

The node already returns one assistant dict with id "reply".
Without add_messages, that dict replaces the whole list, so the user turn disappears.

The third case also needs id replacement: a stale message with id "reply"
must be overwritten, not appended. operator.add will not do that.
"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    # TODO: messages: Annotated[list, add_messages]
    # from langgraph.graph.message import add_messages
    messages: list


def fake_model(messages: list) -> dict:
    """Scripted echo. No network and no API key."""
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
