# 02 — Route a support ticket

## What you learn
- A normal edge always enters the same node. A desk that always lands in billing is that edge.
- `add_conditional_edges(source, path, path_map)` reads state and picks the next node.
- `path(state)` returns a key such as `"engineering"`. `path_map` turns that key into a node name.
- The assign nodes only record the decision. The router is the conditional edge.

## Contract

```text
billing      ticket mentions refund, invoice, or charge
engineering  ticket mentions error, crash, or bug
general      otherwise

"Please refund invoice 1042."     → team "billing"
"Login crashes with error 500."   → team "engineering"
"Where is the status page?"       → team "general"
```

Leave `ticket` unchanged. Export `build_graph()` and return `g.compile()`.

## Skeleton

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    ticket: str
    team: str

def route(state: State) -> str:
    text = state["ticket"].lower()
    if any(word in text for word in ("refund", "invoice", "charge")):
        return "billing"
    if any(word in text for word in ("error", "crash", "bug")):
        return "engineering"
    return "general"

def assign_billing(state: State) -> dict:
    return {"team": "billing"}

def assign_engineering(state: State) -> dict:
    return {"team": "engineering"}

def assign_general(state: State) -> dict:
    return {"team": "general"}

def build_graph():
    g = StateGraph(State)
    g.add_node("assign_billing", assign_billing)
    g.add_node("assign_engineering", assign_engineering)
    g.add_node("assign_general", assign_general)
    g.add_conditional_edges(
        START,
        route,
        {
            "billing": "assign_billing",
            "engineering": "assign_engineering",
            "general": "assign_general",
        },
    )
    g.add_edge("assign_billing", END)
    g.add_edge("assign_engineering", END)
    g.add_edge("assign_general", END)
    return g.compile()
```

## Teaching subset
- One destination per step. A list return (`Send`, parallel fan-out) raises `TypeError`.
- A node has one normal edge or one conditional edge, not both.
- `route` sees state after the source node’s update. This graph routes from `START`, before any node runs.
