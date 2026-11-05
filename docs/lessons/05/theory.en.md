# 05 — Messages and a fake echo model

## What you learn
- Chat state is a list of plain dicts: `{"role", "content"}`, plus optional `"id"`.
- `add_messages` **appends** those dicts. The same `"id"` **replaces** the old one instead of duplicating it.
- `operator.add` only concatenates. It will not update a message in place, so the third grader case fails if you use it.
- The model is a local function. It reads the latest `role: "user"` text and returns one assistant dict. No API key.

The fixed id `"reply"` is deliberate: it is how this lesson shows replacement. A multi-turn transcript usually omits the id (or uses a new one) so each assistant turn appends. Lesson 06 stores memory another way.

## Contract

```text
messages: Annotated[list, add_messages]
node echo returns [fake_model(messages)]

{"messages": [{"role": "user", "content": "hi"}]}
  → user hi, then {"id": "reply", "role": "assistant", "content": "echo: hi"}

{"messages": [{"role": "user", "content": "ping"}]}
  → user ping, then "echo: ping"

input already contains {"id": "reply", "content": "stale"}
  → that reply is replaced by "echo: hi" (still two messages, not three)
```

## Skeleton

```python
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]

def fake_model(messages: list) -> dict:
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
```

## Teaching subset
- Dict messages only. LangChain `BaseMessage`, `RemoveMessage`, and `GenericFakeChatModel` are not loaded in Pyodide here.
- `add_messages` also accepts a single dict, not only a list. This solution returns a one-element list.
- A missing `messages` channel starts as `[]`. `operator.add` does not do that.
