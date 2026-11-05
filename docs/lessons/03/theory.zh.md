# 03 — Reducer 合并

## 要点
- 默认情况下，返回的键会**覆盖**该字段。第 01 课就是这样。
- Reducer 把旧值和本次更新**合并**。
- `Annotated[list, operator.add]` 会把列表接起来（`left + right`）。
- 没有 reducer 的字段（这里的 `total`）仍然是覆盖。

Reducer 写在 **schema** 上，不要写进节点里。每个节点只返回自己新增的那一段。

## 契约

```text
State:  log: Annotated[list, operator.add]，total: int
Nodes:  push_a 追加 ["a"] 且 +1；push_b 追加 ["b"] 且 +10
Edges:  START → push_a → push_b → END
invoke({"log": [], "total": 0})
    == {"log": ["a", "b"], "total": 11}
invoke({"log": ["seed"], "total": 5})
    == {"log": ["seed", "a", "b"], "total": 16}
```

输入里必须已经有 `log`。`operator.add` 不能从缺失值开始（`None + ["a"]` 是 Python 错误）。

## 骨架

```python
import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    log: Annotated[list, operator.add]
    total: int

def push_a(state: State) -> dict:
    return {"log": ["a"], "total": state["total"] + 1}

def push_b(state: State) -> dict:
    return {"log": ["b"], "total": state["total"] + 10}

def build_graph():
    g = StateGraph(State)
    g.add_node("push_a", push_a)
    g.add_node("push_b", push_b)
    g.add_edge(START, "push_a")
    g.add_edge("push_a", "push_b")
    g.add_edge("push_b", END)
    return g.compile()
```

## 教学子集
- `Annotated` 元数据里的第一个可调用对象就是 reducer，和 LangGraph 常见写法一致。
- 本页在 `build_graph()` 编译时读取注解。普通 `list` 注解会覆盖，所以 starter 过不了。
- 这里还没有并行 fan-in。两个顺序节点写同一个带 reducer 的键，就是这一课的全部内容。
