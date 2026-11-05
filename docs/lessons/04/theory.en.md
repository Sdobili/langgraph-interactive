# 04 — Drain a lookup queue

## What you learn
- A cycle is a conditional edge that can return the node you just ran.
- `route` returns `"fetch"` while `remaining` still has keys, and `END` when the queue is empty.
- Do not also add a normal edge from `fetch` to `END`. One outgoing choice per node.
- `invoke(state, config={"recursion_limit": N})` allows N executions of `fetch`. The next one raises `GraphRecursionError` (`langgraph.errors`).
- The default limit here is 25.

`evidence` uses the list reducer from lesson 03, so each lookup is kept. `route` sees the queue after `fetch` pops it.

## Contract

```text
query: "Can I refund order 1042?"

remaining []                         → no lookup
remaining ["order"]                  → evidence for order, queue empty
remaining ["order", "policy"]        → order, then policy
remaining ["order", "policy", "account"], recursion_limit 3
                                     → all three records
remaining [order, policy, account, shipment], recursion_limit 2
                                     → GraphRecursionError
```

Records:

```text
order     Order 1042 is paid.
policy    Refunds are allowed within 30 days.
account   The account email is billing@example.com.
shipment  Shipment has not left the warehouse.
```

Each evidence item is `{"tool": "lookup", "key": key, "text": record}`. Routing does not count as a step.

## Skeleton

```python
import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END

RECORDS = {
    "order": "Order 1042 is paid.",
    "policy": "Refunds are allowed within 30 days.",
    "account": "The account email is billing@example.com.",
    "shipment": "Shipment has not left the warehouse.",
}

class State(TypedDict):
    query: str
    evidence: Annotated[list, operator.add]
    remaining: list

def fetch(state: State) -> dict:
    queue = list(state["remaining"])
    if not queue:
        return {}
    key = queue.pop(0)
    return {
        "remaining": queue,
        "evidence": [{"tool": "lookup", "key": key, "text": RECORDS[key]}],
    }

def route(state: State) -> str:
    if state["remaining"]:
        return "fetch"
    return END

def build_graph():
    g = StateGraph(State)
    g.add_node("fetch", fetch)
    g.add_conditional_edges(START, route)
    g.add_conditional_edges("fetch", route)
    return g.compile()
```

## Teaching subset
- No `path_map`: the string from `route` is the next node, including `END`.
- Real LangGraph counts supersteps and may count `START`. Here only `fetch` counts, so a limit equal to the queue length succeeds.
- `recursion_limit` above 1000 is rejected.
