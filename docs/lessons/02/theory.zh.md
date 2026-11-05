# 02 — 按工单分派

## 要点
- 普通边每次都进入同一个节点。所有工单都进 billing，就是这种边。
- `add_conditional_edges(source, path, path_map)` 读取 state，决定下一节点。
- `path(state)` 返回 `"engineering"` 这样的键。`path_map` 把键变成节点名。
- 分派节点只记下结论。选择本身由条件边完成。

## 契约

```text
billing      工单里出现 refund、invoice、charge
engineering  工单里出现 error、crash、bug
general      其余情况

"Please refund invoice 1042."     → team "billing"
"Login crashes with error 500."   → team "engineering"
"Where is the status page?"       → team "general"
```

`ticket` 保持原样。导出 `build_graph()`，并 `return g.compile()`。

## 骨架

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    ticket: str
    team: str

def route(state: State) -> str:
    text = state["ticket"].lower()
    if any(word in text for word in ("refund", "invoice", "charge")):
        return "billing"
    if any(word in text for word in ("error", "crash", "bug")):
        return "engineering"
    return "general"

def assign_billing(state: State) -> dict:
    return {"team": "billing"}

def assign_engineering(state: State) -> dict:
    return {"team": "engineering"}

def assign_general(state: State) -> dict:
    return {"team": "general"}

def build_graph():
    g = StateGraph(State)
    g.add_node("assign_billing", assign_billing)
    g.add_node("assign_engineering", assign_engineering)
    g.add_node("assign_general", assign_general)
    g.add_conditional_edges(
        START,
        route,
        {
            "billing": "assign_billing",
            "engineering": "assign_engineering",
            "general": "assign_general",
        },
    )
    g.add_edge("assign_billing", END)
    g.add_edge("assign_engineering", END)
    g.add_edge("assign_general", END)
    return g.compile()
```

## 教学子集
- 每一步只去一个节点。返回列表（`Send`、并行扇出）会抛 `TypeError`。
- 一个节点只能有一条普通边，或一组条件边。
- `route` 看到的是源节点更新合并之后的 state。本图从 `START` 路由，此时还没有节点运行。
