# 02 — 条件边与路由

## 要点
- 普通边永远只指向一个下一节点。
- `add_conditional_edges(source, path, path_map)` 根据 state 选择下一节点。
- `path(state)` 返回一个键；`path_map` 把键映射成节点名（或 `END`）。
- 不传 `path_map` 时，返回的字符串本身就是下一节点。第 04 课会这样用。
- 分支节点仍是普通函数，特殊的只有路由器。

## 契约

```text
State:   {"n": int, "label": str}
path:    n > 0 → "pos"，n < 0 → "neg"，否则 → "zero"
map:     pos → positive，neg → negative，zero → zero
invoke({"n": 4, "label": ""})   == {"n": 4, "label": "positive"}
invoke({"n": -3, "label": ""})  == {"n": -3, "label": "negative"}
invoke({"n": 0, "label": ""})   == {"n": 0, "label": "zero"}
```

导出 `build_graph()`，并 `return g.compile()`。

## 骨架

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    n: int
    label: str

def route(state: State) -> str:
    if state["n"] > 0:
        return "pos"
    if state["n"] < 0:
        return "neg"
    return "zero"

def positive(state: State) -> dict:
    return {"label": "positive"}

def negative(state: State) -> dict:
    return {"label": "negative"}

def zero(state: State) -> dict:
    return {"label": "zero"}

def build_graph():
    g = StateGraph(State)
    g.add_node("positive", positive)
    g.add_node("negative", negative)
    g.add_node("zero", zero)
    g.add_conditional_edges(
        START,
        route,
        {"pos": "positive", "neg": "negative", "zero": "zero"},
    )
    g.add_edge("positive", END)
    g.add_edge("negative", END)
    g.add_edge("zero", END)
    return g.compile()
```

## 教学子集
- 每一步只去一个节点。返回列表（`Send` / 并行扇出）会抛 `TypeError`。
- 一个节点只能有一条普通边，或一组条件边，不能两者都有。
- 路径函数看到的是该节点更新合并之后的 state。本课从 `START` 路由，此时还没有任何节点运行。
