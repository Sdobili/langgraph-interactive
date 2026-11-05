# 04 — Cycles and recursion_limit

## What you learn
- A cycle is a conditional edge that may return a node already visited.
- Return `END` when the loop should stop. Do not keep a normal edge to `END` on that same node.
- `invoke(state, config={"recursion_limit": N})` allows at most **N node executions**.
- One past the limit raises `GraphRecursionError` (import path: `langgraph.errors`).
- The default limit in this subset is **25**, matching LangGraph's default.

`trace` uses the list reducer from lesson 03, so each visit appends the value of `n` **before** it is decremented. `route` then sees the updated `n`.

## Contract

```text
n == 0 → no tick.          {"n": 0, "trace": []}
n == 1 → one tick.         {"n": 0, "trace": [1]}
n == 3 → three ticks.      {"n": 0, "trace": [3, 2, 1]}
n == 3, recursion_limit 3  same success (exactly 3 node executions)
n == 4, recursion_limit 2  GraphRecursionError
    (the third tick would exceed the limit)
```

Routing functions do **not** count as steps. Only `tick` does.

## Skeleton

```python
import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    n: int
    trace: Annotated[list, operator.add]

def tick(state: State) -> dict:
    return {"n": state["n"] - 1, "trace": [state["n"]]}

def route(state: State) -> str:
    if state["n"] > 0:
        return "tick"
    return END

def build_graph():
    g = StateGraph(State)
    g.add_node("tick", tick)
    g.add_conditional_edges(START, route)
    g.add_conditional_edges("tick", route)
    return g.compile()
```

## Teaching subset
- No `path_map` here: the string returned by `route` is the next node, and that string may be `END`.
- Real LangGraph counts supersteps and can count `START` as well. Here, only node-function calls count, so a limit equal to the number of `tick` calls succeeds.
- `recursion_limit` above 1000 is rejected so a bug cannot freeze the browser tab.
