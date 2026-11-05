# 09 — 改掉团队，只重跑草稿

## 要点
- 有检查点时，每个跑完的节点都是一份快照。`get_state_history` 从新到旧返回。
- `classify → draft` 之后，最新快照里有回复。更早的那份已经写了 `team`，`reply` 仍是空的。
- `update_state(config, {"team": "engineering"}, as_node="classify")` 把这次写入算作 `classify` 刚做的。`next` 变成 `draft`。在 `draft` 重跑之前，旧回复还在。
- `invoke(None, config)` 只跑 `draft`。

## 契约

```text
工单 "Please refund invoice 1042."
  → team 为 billing
  → reply "Billing will process the refund."
history 长度为 2
  最新：上面的结果
  更早：team 为 billing，reply 为 ""
update_state as_node="classify"，把 team 改成 engineering
  → next 是 draft
  → reply 仍是 billing 那句
invoke(None)
  → reply "Engineering will investigate the error."
```

## 骨架

```python
def build_graph():
    g = StateGraph(State)
    g.add_node("classify", classify)
    g.add_node("draft", draft)
    g.add_edge(START, "classify")
    g.add_edge("classify", "draft")
    g.add_edge("draft", END)
    return g.compile(checkpointer=InMemorySaver())
```

## 教学子集
- 历史是这个线程的 superstep，从新到旧。没有 checkpoint id，也没有分叉时间线。
- `as_node` 用该节点的出边决定 `next`。这张图的出边是 `draft`。
