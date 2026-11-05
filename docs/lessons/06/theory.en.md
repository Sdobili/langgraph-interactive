# 06 — Keep a support thread

## What you learn
- `g.compile(checkpointer=InMemorySaver())` stores the latest state for each thread.
- Pass `config={"configurable": {"thread_id": "acct-1042"}}` to `invoke` and `get_state`.
- The next `invoke` merges its input onto that snapshot, then runs from `START` again.
- `messages` uses `add_messages`, so the new user turn is appended. `reply` does not set an id, so each assistant turn is kept.
- Another `thread_id` is a different customer. `get_state(config).values` reads one thread and does not run the graph.

Current docs import `InMemorySaver`. Older tutorials say `MemorySaver`. Both names are the same class here.

## Contract

Thread `"acct-1042"`:

```text
user  "Can I get a refund?"
asst  "Refunds are allowed within 30 days. What is the order id?"

user  "The order id is 1042."
asst  "Order 1042 is eligible. I have queued the refund."

get_state → those four messages
```

Thread `"walk-in"` on the same compiled graph:

```text
user  "Hello"
asst  "I can help with refunds. Include the order id."

get_state("acct-1042") is still the four-message refund thread.
```

Later turns pass only the new user message. The transcript stays on `messages`.

## Skeleton

```python
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver

class State(TypedDict):
    messages: Annotated[list, add_messages]

def reply(state: State) -> dict:
    text = str(state["messages"][-1].get("content", "")).lower()
    if "refund" in text:
        content = "Refunds are allowed within 30 days. What is the order id?"
    elif "order" in text:
        content = "Order 1042 is eligible. I have queued the refund."
    else:
        content = "I can help with refunds. Include the order id."
    return {"messages": [{"role": "assistant", "content": content}]}

def build_graph():
    g = StateGraph(State)
    g.add_node("reply", reply)
    g.add_edge(START, "reply")
    g.add_edge("reply", END)
    return g.compile(checkpointer=InMemorySaver())
```

## Teaching subset
- Latest snapshot only. No time travel, interrupts, or sqlite.
- Each `build_graph()` call has its own empty saver.
- Without a `thread_id`, `invoke` does not read or write a checkpoint.
- A field with no reducer is overwritten by the next input. That is why this thread stores history on `messages`, not on a replaced string.
