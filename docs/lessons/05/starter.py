"""Lesson 05 — Rewrite the assistant draft.

support_model reads the latest user message and returns one assistant
message with id "draft". A later run with the same id replaces that draft.

Refunds and invoices have fixed answers. Anything else asks for one of those.
The messages channel has to use add_messages, or the user turn is dropped.
"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    # TODO: messages: Annotated[list, add_messages]
    # from langgraph.graph.message import add_messages
    messages: list


def _latest_user_text(messages: list) -> str:
    for message in reversed(messages):
        if isinstance(message, dict) and message.get("role") == "user":
            return str(message.get("content", ""))
    return ""


def support_model(messages: list) -> dict:
    text = _latest_user_text(messages).lower()
    if "refund" in text:
        content = "Refunds are allowed within 30 days. Include the order id."
    elif "invoice" in text:
        content = "Invoices are sent to the billing email on the account."
    else:
        content = "I can help with refunds or invoices."
    return {"id": "draft", "role": "assistant", "content": content}


def draft_reply(state: State) -> dict:
    return {"messages": [support_model(state["messages"])]}


def build_graph():
    g = StateGraph(State)
    g.add_node("draft_reply", draft_reply)
    g.add_edge(START, "draft_reply")
    g.add_edge("draft_reply", END)
    return g.compile()
