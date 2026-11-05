# 11 — Quote every line, then total once

## What you learn
- `Send("quote", {"sku", "qty"})` runs `quote` with that dict as its state, not the parent state.
- A list of `Send` runs **in list order**. Real LangGraph may run the same list concurrently; this page does not.
- After the batch, the graph follows `quote → total` once. `total` sees the merged `quotes`.
- `sku-a` is 20 and `sku-b` is 15. An empty item list returns `END` immediately.

## Contract

```text
sku-a × 2 and sku-b × 1
  → quotes 40 then 15
  → amount 55
sku-a × 1 → quotes 20, amount 20
no items → quotes [], amount 0
```

## Skeleton

```python
def fan_out(state: State):
    if not state["items"]:
        return END
    return [
        Send("quote", {"sku": item["sku"], "qty": item["qty"]})
        for item in state["items"]
    ]

def build_graph():
    g = StateGraph(State)
    g.add_node("quote", quote)
    g.add_node("total", total)
    g.add_conditional_edges(START, fan_out)
    g.add_edge("quote", "total")
    g.add_edge("total", END)
    return g.compile()
```

## Teaching subset
- Every `Send` in the list must name the same node.
- `quote` returns a one-element `quotes` list. The parent reducer appends those rows.
