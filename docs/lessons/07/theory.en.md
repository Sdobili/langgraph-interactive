# 07 — Look up the order, then answer

## What you learn
- The assistant node either asks for one tool or writes the final sentence.
- A conditional edge sends a `tool_calls` message to `tools` and sends any other assistant message to `END`.
- `tools` appends a `role: "tool"` message. The edge back to `assistant` is the loop.
- `lookup_order` for 1042 says the order is paid. `lookup_policy` says refunds last 30 days. The final order sentence adds "The refund can proceed."

## Contract

```text
"What is the status of order 1042?"
  → assistant tool call lookup_order
  → tool "Order 1042 is paid."
  → assistant "Order 1042 is paid. The refund can proceed."

"What is the refund window?"
  → lookup_policy
  → "Refunds are allowed within 30 days."

"Hello"
  → "I can look up an order or the refund policy."
  → no tool message
```

## Skeleton

```python
def route(state: State) -> str:
    last = state["messages"][-1]
    if last.get("role") == "assistant" and last.get("tool_calls"):
        return "tools"
    return END

def build_graph():
    g = StateGraph(State)
    g.add_node("assistant", assistant)
    g.add_node("tools", tools)
    g.add_edge(START, "assistant")
    g.add_conditional_edges("assistant", route)
    g.add_edge("tools", "assistant")
    return g.compile()
```

## Teaching subset
- One tool call per turn. The tool table is local Python, not a model provider.
- Tool messages are plain dicts: `role`, `name`, `content`.
