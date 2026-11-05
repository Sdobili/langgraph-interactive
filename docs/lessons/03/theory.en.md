# 03 — Reducers

## What you learn
- By default a returned key **overwrites** that field. Lesson 01 relies on this.
- A reducer **combines** the old value with the update.
- `Annotated[list, operator.add]` concatenates lists (`left + right`).
- Fields without a reducer, like `total` here, still overwrite.

Put the reducer on the **schema**, not inside the node. Each node should return only its own new items.

## Contract

```text
State:  log: Annotated[list, operator.add], total: int
Nodes:  push_a adds ["a"] and +1; push_b adds ["b"] and +10
Edges:  START → push_a → push_b → END
invoke({"log": [], "total": 0})
    == {"log": ["a", "b"], "total": 11}
invoke({"log": ["seed"], "total": 5})
    == {"log": ["seed", "a", "b"], "total": 16}
```

`log` must already be in the input. `operator.add` cannot start from a missing value (`None + ["a"]` is a Python error).

## Skeleton

```python
import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    log: Annotated[list, operator.add]
    total: int

def push_a(state: State) -> dict:
    return {"log": ["a"], "total": state["total"] + 1}

def push_b(state: State) -> dict:
    return {"log": ["b"], "total": state["total"] + 10}

def build_graph():
    g = StateGraph(State)
    g.add_node("push_a", push_a)
    g.add_node("push_b", push_b)
    g.add_edge(START, "push_a")
    g.add_edge("push_a", "push_b")
    g.add_edge("push_b", END)
    return g.compile()
```

## Teaching subset
- The first callable in `Annotated` metadata is the reducer. That matches the usual LangGraph pattern.
- This page reads annotations when `build_graph()` compiles. A plain `list` annotation overwrites, which is why the starter fails.
- There is no parallel fan-in yet. Two sequential nodes writing the same reduced key is the whole lesson.
