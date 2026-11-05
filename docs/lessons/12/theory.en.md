# 12 — A note that outlives the thread

## What you learn
- A checkpointer is per `thread_id`. A store is on the compiled graph and is visible to every thread.
- `compile(store=InMemoryStore())` injects that store when the node is defined as `remember(state, store)`.
- `store.put(("customers", customer_id), "profile", {"note": ...})` writes it.
- `store.get(...).value` reads it back. A missing item is `None`.

## Contract

```text
thread writer, customer 1042, note "Email refunds to ada@example.com"
  → saved is that sentence
thread reader, customer 1042, note ""
  → saved is still that sentence
thread other, customer 88, note ""
  → saved is ""
```

## Skeleton

```python
def remember(state: State, store) -> dict:
    namespace = ("customers", state["customer_id"])
    if state.get("note"):
        store.put(namespace, "profile", {"note": state["note"]})
        saved = state["note"]
    else:
        item = store.get(namespace, "profile")
        saved = "" if item is None else item.value["note"]
    return {"saved": saved}

def build_graph():
    g = StateGraph(State)
    g.add_node("remember", remember)
    g.add_edge(START, "remember")
    g.add_edge("remember", END)
    return g.compile(store=InMemoryStore())
```

## Teaching subset
- `get` returns an item with `.value`, or `None`. There is no search.
- The store lives inside the object `build_graph()` returns. A new `build_graph()` starts empty.
