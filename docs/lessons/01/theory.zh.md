# 01 — 最小状态图

## 要点
- **StateGraph**：在共享 state（`TypedDict`）上跑的有向图。
- **节点**：`(state) -> 部分更新`；本课字段直接覆盖即可。
- **边**：`START → inc → double → END`，`compile()` 后 `invoke`。
- 校验：`{"count": 3}` → 先 +1 再 ×2 → `{"count": 8}`。

## 契约

```text
State:  {"count": int}
Nodes:  inc(count+1), double(count*2)
Edges:  START → inc → double → END
invoke({"count": 3})  ==  {"count": 8}
invoke({"count": 0})  ==  {"count": 2}
```

## 骨架

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    count: int

def inc(state: State) -> State:
    return {"count": state["count"] + 1}

def double(state: State) -> State:
    return {"count": state["count"] * 2}

def build_graph():
    g = StateGraph(State)
    g.add_node("inc", inc)
    g.add_node("double", double)
    g.add_edge(START, "inc")
    g.add_edge("inc", "double")
    g.add_edge("double", END)
    return g.compile()
```
