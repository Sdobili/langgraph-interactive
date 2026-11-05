# 05 — 重写助手草稿

## 要点
- 消息是 dict：`role`、`content`，以及可选的 `id`。
- `add_messages` 会追加。相同的 `id` 会替换上一条。
- `operator.add` 只会拼接，所以第二条 id 为 `"draft"` 的草稿会和旧草稿并排。本课第三则判题不允许这样。
- `support_model` 是本地函数，只有三句固定回答。它代替聊天模型。不需要 API key。

id `"draft"` 表示这个节点只维护当前这一条回复。重新生成时更新这条消息。需要保留每一轮助手发言的记录不要写 id，第 06 课就是那样。

## 契约

```text
messages: Annotated[list, add_messages]

"Can I get a refund?"
  → "Refunds are allowed within 30 days. Include the order id."

"Send me the invoice."
  → "Invoices are sent to the billing email on the account."

同一句退款问题，外加已有的
{"id": "draft", "content": "Draft not finished."}
  → 这条草稿被替换。列表仍然只有两条消息。
```

用户消息留在前面。其他问题落到 "I can help with refunds or invoices."。

## 骨架

```python
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]

def _latest_user_text(messages: list) -> str:
    for message in reversed(messages):
        if isinstance(message, dict) and message.get("role") == "user":
            return str(message.get("content", ""))
    return ""

def support_model(messages: list) -> dict:
    text = _latest_user_text(messages).lower()
    if "refund" in text:
        content = "Refunds are allowed within 30 days. Include the order id."
    elif "invoice" in text:
        content = "Invoices are sent to the billing email on the account."
    else:
        content = "I can help with refunds or invoices."
    return {"id": "draft", "role": "assistant", "content": content}

def draft_reply(state: State) -> dict:
    return {"messages": [support_model(state["messages"])]}

def build_graph():
    g = StateGraph(State)
    g.add_node("draft_reply", draft_reply)
    g.add_edge(START, "draft_reply")
    g.add_edge("draft_reply", END)
    return g.compile()
```

## 教学子集
- 只用 dict 消息。这里不加载 `BaseMessage`、`RemoveMessage`、`GenericFakeChatModel`。
- `add_messages` 也可以接收单条 dict。本图返回只有一个元素的列表。
- 缺失的 `messages` 通道从 `[]` 开始。
