# 05 — Rewrite the assistant draft

## What you learn
- Messages are dicts: `role`, `content`, and an optional `id`.
- `add_messages` appends them. The same `id` replaces the previous message.
- `operator.add` only concatenates, so a second draft with id `"draft"` would sit beside the old one. This lesson’s third case rejects that.
- `support_model` is a local function with three fixed answers. It stands in for a chat model. No API key.

The id `"draft"` means this node owns one current reply. Regenerating the draft updates that message. A transcript that should keep every assistant turn omits the id, which is what lesson 06 does.

## Contract

```text
messages: Annotated[list, add_messages]

"Can I get a refund?"
  → "Refunds are allowed within 30 days. Include the order id."

"Send me the invoice."
  → "Invoices are sent to the billing email on the account."

The same refund question, plus an existing
{"id": "draft", "content": "Draft not finished."}
  → that draft is replaced. The list still has two messages.
```

The user message stays in front. Anything else falls through to "I can help with refunds or invoices."

## Skeleton

```python
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]

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
```

## Teaching subset
- Dict messages only. `BaseMessage`, `RemoveMessage`, and `GenericFakeChatModel` are not loaded.
- `add_messages` also accepts one dict. This graph returns a one-element list.
- A missing `messages` channel starts as `[]`.
