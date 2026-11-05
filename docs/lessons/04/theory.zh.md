# 04 — 循环与递归上限

## 要点
- 循环就是一条条件边，它可能回到已经走过的节点。
- 该停的时候返回 `END`。同一个节点上不要再留一条普通边指向 `END`。
- `invoke(state, config={"recursion_limit": N})` 最多执行 **N 次节点函数**。
- 再多一步就抛 `GraphRecursionError`（导入路径：`langgraph.errors`）。
- 本子集的默认上限是 **25**，与 LangGraph 默认值一致。

`trace` 使用第 03 课的列表 reducer，所以每次访问都会追加**递减之前**的 `n`。随后 `route` 看到的是更新后的 `n`。

## 契约

```text
n == 0 → 不进入 tick。     {"n": 0, "trace": []}
n == 1 → 一次 tick。       {"n": 0, "trace": [1]}
n == 3 → 三次 tick。       {"n": 0, "trace": [3, 2, 1]}
n == 3 且 recursion_limit 3  同样成功（正好 3 次节点执行）
n == 4 且 recursion_limit 2  GraphRecursionError
    （第三次 tick 会超过上限）
```

路由函数**不算**步数。只有 `tick` 算。

## 骨架

```python
import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    n: int
    trace: Annotated[list, operator.add]

def tick(state: State) -> dict:
    return {"n": state["n"] - 1, "trace": [state["n"]]}

def route(state: State) -> str:
    if state["n"] > 0:
        return "tick"
    return END

def build_graph():
    g = StateGraph(State)
    g.add_node("tick", tick)
    g.add_conditional_edges(START, route)
    g.add_conditional_edges("tick", route)
    return g.compile()
```

## 教学子集
- 这里不用 `path_map`：`route` 返回的字符串就是下一节点，也可以是 `END`。
- 真正的 LangGraph 按 superstep 计数，并且可能把 `START` 也算进去。这里只计算节点函数调用，所以上限刚好等于 `tick` 次数时可以通过。
- `recursion_limit` 超过 1000 会被拒绝，避免错误循环把浏览器标签页卡死。
