# 03 — 累积检索片段

## 要点
- 返回的键会覆盖该字段。`draft` 就该这样：撰写节点换掉检索节点的占位句。
- Reducer 把旧值和本次更新合并。`passages` 必须留下每一次命中。
- `Annotated[list, operator.add]` 拼接列表。写在 schema 上。每个节点只返回自己找到的片段。

## 契约

```text
START → retrieve → write → END

retrieve  追加 {"source": "faq", "text": query}
          把 draft 设为 "Looking up the policy."
write     追加 {"source": "policy", "text": "Refunds are allowed within 30 days."}
          把 draft 设为同一句话

query 为 "What is the refund window?" 且 passages 为 []
  → 先 faq，再 policy
  → draft == "Refunds are allowed within 30 days."

如果 passages 里已经有一条工单笔记，它留在最前面。
```

输入里必须已经有 `passages`。`operator.add` 不能从缺失值开始。

## 骨架

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

## 教学子集
- `Annotated` 元数据里的第一个可调用对象就是 reducer。
- 判题在 `build_graph()` 编译时读取这些注解。普通 `list` 会丢掉 faq 命中，这就是 starter 的失败原因。
- 两个顺序节点就够了。本子集没有并行 fan-in。
