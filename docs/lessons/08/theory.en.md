# 08 — Approve before sending

## What you learn
- `interrupt_before=["send"]` stops the run when `send` is the next node. `draft` has already written.
- The checkpointer keeps that pause on the thread. `get_state(config).next` is `("send",)`.
- `update_state(config, {"approved": True})` merges the decision and leaves `next` on `send`.
- `invoke(None, config)` resumes at `send` and does not draft again.
- The same resume with `approved` still false writes "Held for review."

## Contract

```text
thread apr-1
  invoke the refund request
    → user + draft, approved false, no system message
  get_state.next == ("send",)
  update_state approved true
  invoke(None) → system "Sent the refund confirmation."

thread apr-hold
  invoke, then invoke(None) without an update
    → system "Held for review."
```

## Skeleton

```python
def send(state: State) -> dict:
    content = (
        "Sent the refund confirmation."
        if state.get("approved")
        else "Held for review."
    )
    return {"messages": [{"role": "system", "content": content}]}

def build_graph():
    g = StateGraph(State)
    g.add_node("draft", draft)
    g.add_node("send", send)
    g.add_edge(START, "draft")
    g.add_edge("draft", "send")
    g.add_edge("send", END)
    return g.compile(
        checkpointer=InMemorySaver(),
        interrupt_before=["send"],
    )
```

## Teaching subset
- The pause is declared on `compile`, not by calling `interrupt()` inside the node.
- Resume is `invoke(None)`, which continues `next`. A new dict input starts again at `START`.
