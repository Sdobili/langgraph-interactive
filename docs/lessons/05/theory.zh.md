# 05 — 消息与假模型回声

## 要点
- 对话 state 是普通 dict 列表：`{"role", "content"}`，可以再加 `"id"`。
- `add_messages` 会**追加**这些 dict。相同的 `"id"` 会**替换**旧消息，而不是再追加一条。
- `operator.add` 只会拼接。它不会就地更新一条消息，所以第三则判题用它会失败。
- 模型是本地函数。它读取最近一条 `role: "user"` 的文本，返回一条 assistant dict。不需要 API key。

固定 id `"reply"` 是故意的：这一课用它演示替换。多轮记录通常不写 id（或每次用新 id），这样每轮 assistant 都会追加。第 06 课用另一种方式保存记忆。

## 契约

```text
messages: Annotated[list, add_messages]
节点 echo 返回 [fake_model(messages)]

{"messages": [{"role": "user", "content": "hi"}]}
  → 保留 user hi，再加 {"id": "reply", "role": "assistant", "content": "echo: hi"}

{"messages": [{"role": "user", "content": "ping"}]}
  → user ping，再加 "echo: ping"

输入里已经有 {"id": "reply", "content": "stale"}
  → 这条 reply 被替换成 "echo: hi"（仍然是两条消息，不是三条）
```

## 骨架

```python
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]

def fake_model(messages: list) -> dict:
    text = ""
    for msg in reversed(messages):
        if isinstance(msg, dict) and msg.get("role") == "user":
            text = str(msg.get("content", ""))
            break
    return {"id": "reply", "role": "assistant", "content": "echo: " + text}

def echo(state: State) -> dict:
    return {"messages": [fake_model(state["messages"])]}

def build_graph():
    g = StateGraph(State)
    g.add_node("echo", echo)
    g.add_edge(START, "echo")
    g.add_edge("echo", END)
    return g.compile()
```

## 教学子集
- 只用 dict 消息。LangChain 的 `BaseMessage`、`RemoveMessage`、`GenericFakeChatModel` 没有装进这里的 Pyodide。
- `add_messages` 也可以接收单条 dict，不限于列表。本解答返回只有一个元素的列表。
- 缺失的 `messages` 通道会从 `[]` 开始。`operator.add` 不会这样做。
