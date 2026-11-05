# 03 — Accumulate passages

## What you learn
- A returned key overwrites that field. `draft` is supposed to do that: the writer replaces the retriever’s placeholder.
- A reducer combines the old value with the update. `passages` must keep every hit.
- `Annotated[list, operator.add]` concatenates lists. Put it on the schema. Each node returns only the passages it found.

## Contract

```text
START → retrieve → write → END

retrieve  appends {"source": "faq", "text": query}
          sets draft to "Looking up the policy."
write     appends {"source": "policy", "text": "Refunds are allowed within 30 days."}
          sets draft to that same sentence

query "What is the refund window?" and passages []
  → faq, then policy
  → draft == "Refunds are allowed within 30 days."

passages that already hold a ticket note keep that note in front.
```

`passages` has to be present on the input. `operator.add` does not start from a missing value.

## Skeleton

```python
import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    query: str
    passages: Annotated[list, operator.add]
    draft: str

def retrieve(state: State) -> dict:
    return {
        "passages": [{"source": "faq", "text": state["query"]}],
        "draft": "Looking up the policy.",
    }

def write(state: State) -> dict:
    return {
        "passages": [{"source": "policy", "text": "Refunds are allowed within 30 days."}],
        "draft": "Refunds are allowed within 30 days.",
    }

def build_graph():
    g = StateGraph(State)
    g.add_node("retrieve", retrieve)
    g.add_node("write", write)
    g.add_edge(START, "retrieve")
    g.add_edge("retrieve", "write")
    g.add_edge("write", END)
    return g.compile()
```

## Teaching subset
- The first callable in `Annotated` metadata is the reducer.
- The grader reads those hints when `build_graph()` compiles. A plain `list` drops the faq hit, which is the starter’s failure.
- Two sequential writers are enough. Parallel fan-in is not in this subset.
