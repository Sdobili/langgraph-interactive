# 10 — 用子图做检索

## 要点
- `build_research()` 是一张自己的 `StateGraph`。`add_node("research", build_research())` 把它当成父图里的一个节点来跑。
- 子图**覆盖** `passages`，只留下政策片段。父图的 schema 用 `operator.add` 把这份列表接上去，所以父图里原有的工单笔记还在前面。
- `note` 把政策句子写进 `draft`。父图的 `answer` 再把 `draft` 抄到 `answer`。

## 契约

```text
query 为 "What is the refund window?" 且 passages 为 []
  → passages：policy "Refunds are allowed within 30 days."
  → draft 和 answer 都是这句话

passages 里已经有 {"source": "ticket", "text": "Customer asked twice."}
  → 先是工单笔记，再是政策片段
```

## 骨架

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

## 教学子集
- 子图收到父状态，返回自己的完整状态。父图用父 reducer 合并这份 dict。
- 子图覆盖 `passages`，父 reducer 就只会把新片段追加一次。两边都用 reducer 时，父图里的旧行会被追加两遍。
