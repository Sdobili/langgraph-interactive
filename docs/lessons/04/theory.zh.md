# 04 — 把查询队列跑完

## 要点
- 循环就是一条可以回到当前节点的条件边。
- `remaining` 里还有键时，`route` 返回 `"fetch"`；队列空了就返回 `END`。
- 不要再给 `fetch` 加一条指向 `END` 的普通边。每个节点只有一种出边。
- `invoke(state, config={"recursion_limit": N})` 最多执行 N 次 `fetch`。再多一次就抛 `GraphRecursionError`（`langgraph.errors`）。
- 这里的默认上限是 25。

`evidence` 使用第 03 课的列表 reducer，所以每次查询都会留下。`route` 看到的是 `fetch` 弹出之后的队列。

## 契约

```text
query: "Can I refund order 1042?"

remaining []                         → 不查询
remaining ["order"]                  → 只有 order 的证据，队列为空
remaining ["order", "policy"]        → 先 order，再 policy
remaining ["order", "policy", "account"] 且 recursion_limit 为 3
                                     → 三条记录都在
remaining [order, policy, account, shipment] 且 recursion_limit 为 2
                                     → GraphRecursionError
```

记录内容：

```text
order     Order 1042 is paid.
policy    Refunds are allowed within 30 days.
account   The account email is billing@example.com.
shipment  Shipment has not left the warehouse.
```

每条证据是 `{"tool": "lookup", "key": key, "text": record}`。路由不算步数。

## 骨架

```python
import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END

RECORDS = {
    "order": "Order 1042 is paid.",
    "policy": "Refunds are allowed within 30 days.",
    "account": "The account email is billing@example.com.",
    "shipment": "Shipment has not left the warehouse.",
}

class State(TypedDict):
    query: str
    evidence: Annotated[list, operator.add]
    remaining: list

def fetch(state: State) -> dict:
    queue = list(state["remaining"])
    if not queue:
        return {}
    key = queue.pop(0)
    return {
        "remaining": queue,
        "evidence": [{"tool": "lookup", "key": key, "text": RECORDS[key]}],
    }

def route(state: State) -> str:
    if state["remaining"]:
        return "fetch"
    return END

def build_graph():
    g = StateGraph(State)
    g.add_node("fetch", fetch)
    g.add_conditional_edges(START, route)
    g.add_conditional_edges("fetch", route)
    return g.compile()
```

## 教学子集
- 不用 `path_map`：`route` 返回的字符串就是下一节点，也可以是 `END`。
- 真正的 LangGraph 按 superstep 计数，并且可能把 `START` 算进去。这里只计算 `fetch`，所以上限等于队列长度时可以通过。
- `recursion_limit` 超过 1000 会被拒绝。
