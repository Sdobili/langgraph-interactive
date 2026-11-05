# 02 — Conditional edges

## What you learn
- A normal edge always goes to one next node.
- `add_conditional_edges(source, path, path_map)` chooses the next node from state.
- `path(state)` returns a key. `path_map` maps that key to a node name (or `END`).
- Omit `path_map` and the string you return **is** the next node. Lesson 04 does that.
- Branch nodes are ordinary functions. Only the router is special.

## Contract

```text
State:   {"n": int, "label": str}
path:    n > 0 → "pos", n < 0 → "neg", else → "zero"
map:     pos → positive, neg → negative, zero → zero
invoke({"n": 4, "label": ""})   == {"n": 4, "label": "positive"}
invoke({"n": -3, "label": ""})  == {"n": -3, "label": "negative"}
invoke({"n": 0, "label": ""})   == {"n": 0, "label": "zero"}
```

Export `build_graph()` and return `g.compile()`.

## Skeleton

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    n: int
    label: str

def route(state: State) -> str:
    if state["n"] > 0:
        return "pos"
    if state["n"] < 0:
        return "neg"
    return "zero"

def positive(state: State) -> dict:
    return {"label": "positive"}

def negative(state: State) -> dict:
    return {"label": "negative"}

def zero(state: State) -> dict:
    return {"label": "zero"}

def build_graph():
    g = StateGraph(State)
    g.add_node("positive", positive)
    g.add_node("negative", negative)
    g.add_node("zero", zero)
    g.add_conditional_edges(
        START,
        route,
        {"pos": "positive", "neg": "negative", "zero": "zero"},
    )
    g.add_edge("positive", END)
    g.add_edge("negative", END)
    g.add_edge("zero", END)
    return g.compile()
```

## Teaching subset
- One destination per step. Returning a list (`Send` / parallel fan-out) raises `TypeError`.
- A node has either one normal edge or one conditional edge, not both.
- The path function sees state **after** that node's update is merged. This lesson routes from `START`, before any node runs.
