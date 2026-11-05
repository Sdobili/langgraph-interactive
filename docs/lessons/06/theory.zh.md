# 06 — InMemorySaver 检查点

## 要点
- `g.compile(checkpointer=InMemorySaver())` 为每个线程保存最新 state。
- `invoke` 和 `get_state` 都传入 `config={"configurable": {"thread_id": "counter"}}`。
- 同一线程的下一次 `invoke` 会把这次输入**合并**进已保存的 state，然后再次从 `START` 运行。
- 想沿用记忆时传入 `{}`。`count` 没有 reducer，如果再传入 `{"count": 0}`，会在节点运行前把记忆覆盖掉。
- 另一个 `thread_id` 是另一段对话。`get_state(config).values` 只读取该线程，不运行节点。

当前 LangGraph 文档导入的是 `InMemorySaver`。更早的教程写成 `MemorySaver`。在本子集里两个名字是同一个类（`from langgraph.checkpoint.memory import InMemorySaver, MemorySaver`）。

## 契约

同一个已编译的图，线程 `"counter"`：

```text
invoke({"count": 0}, config) → {"count": 1}
invoke({}, config)           → {"count": 2}
invoke({}, config)           → {"count": 3}
get_state(config).values     == {"count": 3}
```

同一张图上的线程 `"other"`：

```text
invoke({"count": 10}, other) → {"count": 11}
get_state(counter).values    == {"count": 3}   # 不受影响
```

`config` 的形状是 `{"configurable": {"thread_id": "<id>"}}`。

## 骨架

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

class State(TypedDict):
    count: int

def increment(state: State) -> dict:
    return {"count": state["count"] + 1}

def build_graph():
    g = StateGraph(State)
    g.add_node("increment", increment)
    g.add_edge(START, "increment")
    g.add_edge("increment", END)
    return g.compile(checkpointer=InMemorySaver())
```

## 教学子集
- 只保留最新快照：没有时间旅行、没有 interrupt、没有 sqlite。
- saver 放在 `build_graph()` 返回的对象里面。每次调用 `build_graph()` 都是一块新的空记忆。
- 没有 `thread_id` 时，`invoke` 不读也不写检查点。
- 真正的 saver 还会保存元数据和检查点历史。这里的 `get` / `put` 每个线程只留一份 dict，足够完成本课契约。
