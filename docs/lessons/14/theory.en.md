# 14 — Answer from the last three messages

## What you learn
- A reducer can call `add_messages` and then slice. `keep_last_three` is that function.
- The node still appends one assistant message. The schema drops anything older than the last three rows **after** the append.
- The reply reads the latest user text. "refund" gets the 30-day sentence. Anything else asks the customer to ask about a refund.
- A two-message thread is shorter than the window, so both rows stay.

## Contract

```text
messages:
  user "old"
  assistant "Noted."
  user "Can I get a refund?"
  assistant "Checking the policy."
→ the last three are the refund question, "Checking the policy.",
  and "Refunds are allowed within 30 days."

messages: user "Hello"
→ user "Hello", assistant "Ask me about a refund."
```

## Skeleton

```python
def keep_last_three(left, right):
    return add_messages(left, right)[-3:]

class State(TypedDict):
    messages: Annotated[list, keep_last_three]

def build_graph():
    g = StateGraph(State)
    g.add_node("reply", reply)
    g.add_edge(START, "reply")
    g.add_edge("reply", END)
    return g.compile()
```

## Teaching subset
- The window is applied by the reducer, not by a separate trim node.
- `add_messages` still replaces an identical id before the slice. This lesson's rows have no ids.
