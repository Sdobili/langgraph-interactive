# 09 — Change the team and rerun the draft

## What you learn
- With a checkpointer, each finished node is a snapshot. `get_state_history` returns the newest first.
- After `classify → draft`, the newest snapshot has the reply. The older one has `team` set and `reply` still empty.
- `update_state(config, {"team": "engineering"}, as_node="classify")` pretends `classify` just wrote that team. `next` becomes `draft`. The previous reply is still there until `draft` runs again.
- `invoke(None, config)` runs `draft` only.

## Contract

```text
ticket "Please refund invoice 1042."
  → team billing
  → reply "Billing will process the refund."
history length 2
  newest: that result
  older: team billing, reply ""
update_state as_node="classify" to team engineering
  → next is draft
  → reply is still the billing sentence
invoke(None)
  → reply "Engineering will investigate the error."
```

## Skeleton

```python
def build_graph():
    g = StateGraph(State)
    g.add_node("classify", classify)
    g.add_node("draft", draft)
    g.add_edge(START, "classify")
    g.add_edge("classify", "draft")
    g.add_edge("draft", END)
    return g.compile(checkpointer=InMemorySaver())
```

## Teaching subset
- History is the supersteps of this thread, newest first. There is no checkpoint id and no branch timeline.
- `as_node` chooses `next` from that node's outgoing edge. This graph's edge is `draft`.
