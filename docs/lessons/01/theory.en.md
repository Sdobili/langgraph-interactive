# 01 — Minimal StateGraph

## What you learn
- A **StateGraph** is a directed graph over a shared **state** (`TypedDict`).
- Each **node** is a function `(state) -> partial state update`.
- **Edges** wire `START → … → END`. After `compile()`, call `invoke(initial_state)`.
- Default merge: returned keys **overwrite** state fields (no reducer needed for lesson 1).

## Contract

```text
State:  {"count": int}
Nodes:  inc(count+1), double(count*2)
Edges:  START → inc → double → END
invoke({"count": 3})  ==  {"count": 8}
invoke({"count": 0})  ==  {"count": 2}
```

## Skeleton

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    count: int

def inc(state: State) -> State:
    return {"count": state["count"] + 1}

def double(state: State) -> State:
    return {"count": state["count"] * 2}

def build_graph():
    g = StateGraph(State)
    g.add_node("inc", inc)
    g.add_node("double", double)
    g.add_edge(START, "inc")
    g.add_edge("inc", "double")
    g.add_edge("double", END)
    return g.compile()
```
