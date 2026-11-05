# 06 — 保住一条客服线程

## 要点
- `g.compile(checkpointer=InMemorySaver())` 为每个线程保存最新 state。
- `invoke` 和 `get_state` 传入 `config={"configurable": {"thread_id": "acct-1042"}}`。
- 下一次 `invoke` 把这次输入合并进快照，然后再次从 `START` 运行。
- `messages` 使用 `add_messages`，新的用户回合会接在后面。`reply` 不写 id，所以每一轮助手回复都会留下。
- 另一个 `thread_id` 是另一位客户。`get_state(config).values` 只读该线程，不运行图。

当前文档导入 `InMemorySaver`。更早的教程写成 `MemorySaver`。在这里两个名字是同一个类。

## 契约

线程 `"acct-1042"`：

```text
user  "Can I get a refund?"
asst  "Refunds are allowed within 30 days. What is the order id?"

user  "The order id is 1042."
asst  "Order 1042 is eligible. I have queued the refund."

get_state → 这四条消息
```

同一张已编译的图上，线程 `"walk-in"`：

```text
user  "Hello"
asst  "I can help with refunds. Include the order id."

get_state("acct-1042") 仍然是那四条退款对话。
```

后续回合只传入新的用户消息。这里记住历史的通道是 `messages`。

## 骨架

```python
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver

class State(TypedDict):
    messages: Annotated[list, add_messages]

def reply(state: State) -> dict:
    text = str(state["messages"][-1].get("content", "")).lower()
    if "refund" in text:
        content = "Refunds are allowed within 30 days. What is the order id?"
    elif "order" in text:
        content = "Order 1042 is eligible. I have queued the refund."
    else:
        content = "I can help with refunds. Include the order id."
    return {"messages": [{"role": "assistant", "content": content}]}

def build_graph():
    g = StateGraph(State)
    g.add_node("reply", reply)
    g.add_edge(START, "reply")
    g.add_edge("reply", END)
    return g.compile(checkpointer=InMemorySaver())
```

## 教学子集
- 只保留最新快照。没有时间旅行、interrupt 或 sqlite。
- 每次 `build_graph()` 都有自己的空 saver。
- 没有 `thread_id` 时，`invoke` 不读也不写检查点。
- 没有 reducer 的字段会被下一次输入覆盖。所以这条线程把历史放在 `messages` 上，而不是放在一个会被替换的字符串上。
