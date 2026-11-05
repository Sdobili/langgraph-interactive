# 07 — 先查订单，再回答

## 要点
- `assistant` 要么请求一个工具，要么写出最终那一句。
- 条件边把带 `tool_calls` 的消息送到 `tools`，其他助手消息送到 `END`。
- `tools` 追加一条 `role: "tool"` 消息，再走回 `assistant`。
- 1042 的 `lookup_order` 说明订单已付款。`lookup_policy` 说明退款期限是 30 天。订单的最终句子还要加上 "The refund can proceed."。

## 契约

```text
"What is the status of order 1042?"
  → assistant 调用 lookup_order
  → tool "Order 1042 is paid."
  → assistant "Order 1042 is paid. The refund can proceed."

"What is the refund window?"
  → lookup_policy
  → "Refunds are allowed within 30 days."

"Hello"
  → "I can look up an order or the refund policy."
  → 没有 tool 消息
```

## 骨架

```python
def route(state: State) -> str:
    last = state["messages"][-1]
    if last.get("role") == "assistant" and last.get("tool_calls"):
        return "tools"
    return END

def build_graph():
    g = StateGraph(State)
    g.add_node("assistant", assistant)
    g.add_node("tools", tools)
    g.add_edge(START, "assistant")
    g.add_conditional_edges("assistant", route)
    g.add_edge("tools", "assistant")
    return g.compile()
```

## 教学子集
- 每一轮只调用一个工具。工具表是本地 Python，不是模型服务。
- 工具消息是普通 dict：`role`、`name`、`content`。
