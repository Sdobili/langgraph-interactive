# 08 — 发出去之前先确认

## 要点
- `interrupt_before=["send"]` 在下一步是 `send` 时停下。`draft` 已经写完。
- 检查点把这次暂停留在线程上。`get_state(config).next` 是 `("send",)`。
- `update_state(config, {"approved": True})` 合并决定，`next` 仍停在 `send`。
- `invoke(None, config)` 从 `send` 继续，不会再跑 `draft`。
- `approved` 仍是 false 时，同一次恢复会写下 "Held for review."。

## 契约

```text
线程 apr-1
  invoke 退款请求
    → user + draft，approved 为 false，没有 system 消息
  get_state.next == ("send",)
  update_state 把 approved 设为 true
  invoke(None) → system "Sent the refund confirmation."

线程 apr-hold
  invoke 之后直接 invoke(None)
    → system "Held for review."
```

## 骨架

```python
def send(state: State) -> dict:
    content = (
        "Sent the refund confirmation."
        if state.get("approved")
        else "Held for review."
    )
    return {"messages": [{"role": "system", "content": content}]}

def build_graph():
    g = StateGraph(State)
    g.add_node("draft", draft)
    g.add_node("send", send)
    g.add_edge(START, "draft")
    g.add_edge("draft", "send")
    g.add_edge("send", END)
    return g.compile(
        checkpointer=InMemorySaver(),
        interrupt_before=["send"],
    )
```

## 教学子集
- 暂停写在 `compile` 上，不是在节点里调用 `interrupt()`。
- 恢复用 `invoke(None)`，它接着跑 `next`。传入新的 dict 会从 `START` 重跑。
