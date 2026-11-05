# 06 — Checkpoint with InMemorySaver

## What you learn
- `g.compile(checkpointer=InMemorySaver())` keeps the latest state for each thread.
- Pass `config={"configurable": {"thread_id": "counter"}}` on `invoke` and on `get_state`.
- The next `invoke` on that thread **merges** its input onto the saved state, then runs from `START` again.
- Pass `{}` when you want the saved state left as it is. `count` has no reducer, so passing `{"count": 0}` again would overwrite the memory before the node runs.
- Another `thread_id` is a separate conversation. `get_state(config).values` reads one thread without running nodes.

Current LangGraph docs import `InMemorySaver`. Older tutorials say `MemorySaver`. In this subset both names are the same class (`from langgraph.checkpoint.memory import InMemorySaver, MemorySaver`).

## Contract

One compiled graph, thread `"counter"`:

```text
invoke({"count": 0}, config) → {"count": 1}
invoke({}, config)           → {"count": 2}
invoke({}, config)           → {"count": 3}
get_state(config).values     == {"count": 3}
```

Thread `"other"` on that same graph:

```text
invoke({"count": 10}, other) → {"count": 11}
get_state(counter).values    == {"count": 3}   # untouched
```

`config` is `{"configurable": {"thread_id": "<id>"}}`.

## Skeleton

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

class State(TypedDict):
    count: int

def increment(state: State) -> dict:
    return {"count": state["count"] + 1}

def build_graph():
    g = StateGraph(State)
    g.add_node("increment", increment)
    g.add_edge(START, "increment")
    g.add_edge("increment", END)
    return g.compile(checkpointer=InMemorySaver())
```

## Teaching subset
- Latest snapshot only: no time travel, no interrupts, no sqlite.
- The saver lives inside the object `build_graph()` returns. Each call to `build_graph()` starts with empty memory.
- Without a `thread_id`, `invoke` does not read or write a checkpoint.
- Real savers also store metadata and a history of checkpoints. Here `get` / `put` keep one dict per thread, which is enough for this contract.
