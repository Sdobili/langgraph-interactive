"""Lesson 07 — Tool loop for an order question.

assistant may ask for lookup_order or lookup_policy.
tools runs that call, then assistant writes the final sentence.
"""

from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages


class State(TypedDict):
    messages: Annotated[list, add_messages]


def _latest_user_text(messages: list) -> str:
    for message in reversed(messages):
        if isinstance(message, dict) and message.get("role") == "user":
            return str(message.get("content", ""))
    return ""


def assistant(state: State) -> dict:
    messages = state["messages"]
    last = messages[-1]
    if last.get("role") == "tool":
        if last.get("name") == "lookup_order":
            content = last["content"] + " The refund can proceed."
        else:
            content = last["content"]
        return {"messages": [{"role": "assistant", "content": content}]}
    text = _latest_user_text(messages)
    lowered = text.lower()
    if "1042" in text:
        call = {"name": "lookup_order", "args": {"order_id": "1042"}}
    elif "window" in lowered or "policy" in lowered:
        call = {"name": "lookup_policy", "args": {}}
    else:
        return {
            "messages": [
                {
                    "role": "assistant",
                    "content": "I can look up an order or the refund policy.",
                }
            ]
        }
    return {"messages": [{"role": "assistant", "tool_calls": [call]}]}


def route(state: State) -> str:
    last = state["messages"][-1]
    if last.get("role") == "assistant" and last.get("tool_calls"):
        return "tools"
    return END


def tools(state: State) -> dict:
    call = state["messages"][-1]["tool_calls"][0]
    if call["name"] == "lookup_order":
        order_id = call["args"]["order_id"]
        content = (
            f"Order {order_id} is paid."
            if order_id == "1042"
            else f"Order {order_id} was not found."
        )
    elif call["name"] == "lookup_policy":
        content = "Refunds are allowed within 30 days."
    else:
        content = f"Unknown tool {call['name']}."
    return {"messages": [{"role": "tool", "name": call["name"], "content": content}]}


def build_graph():
    g = StateGraph(State)
    g.add_node("assistant", assistant)
    g.add_node("tools", tools)
    # TODO: assistant conditionally goes to tools, and tools returns to assistant.
    g.add_edge(START, "assistant")
    g.add_edge("assistant", END)
    return g.compile()
