# 10 — Research in a subgraph

## What you learn
- `build_research()` is its own `StateGraph`. `add_node("research", build_research())` runs that compiled graph as one parent node.
- The child **overwrites** `passages` with the policy hit. The parent schema appends that list with `operator.add`, so a ticket note already on the parent stays in front.
- `note` copies the policy sentence into `draft`. The parent `answer` node copies `draft` into `answer`.

## Contract

```text
query "What is the refund window?" and passages []
  → passages: policy "Refunds are allowed within 30 days."
  → draft and answer: that same sentence

passages already holding {"source": "ticket", "text": "Customer asked twice."}
  → ticket note, then the policy hit
```

## Skeleton

```python
def build_research():
    g = StateGraph(ResearchState)
    g.add_node("retrieve", retrieve)
    g.add_node("note", note)
    g.add_edge(START, "retrieve")
    g.add_edge("retrieve", "note")
    g.add_edge("note", END)
    return g.compile()

def build_graph():
    g = StateGraph(State)
    g.add_node("research", build_research())
    g.add_node("answer", answer)
    g.add_edge(START, "research")
    g.add_edge("research", "answer")
    g.add_edge("answer", END)
    return g.compile()
```

## Teaching subset
- The child receives the parent state and returns its full state. The parent merges that dict with the parent reducers.
- Because the child overwrites `passages`, the parent reducer appends the new hit once. A reducer on both sides would duplicate the parent's old rows.
