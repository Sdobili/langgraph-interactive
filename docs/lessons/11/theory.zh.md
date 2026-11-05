# 11 — 逐项报价，再汇总一次

## 要点
- `Send("quote", {"sku", "qty"})` 让 `quote` 看到的是这份 dict，不是父状态。
- `Send` 列表按**列表顺序**执行。真正的 LangGraph 可能并发跑同一份列表；这一页不会。
- 这一批跑完后，图沿 `quote → total` 只走一次。`total` 看到合并后的 `quotes`。
- `sku-a` 单价 20，`sku-b` 单价 15。没有明细时直接返回 `END`。

## 契约

```text
sku-a × 2 且 sku-b × 1
  → quotes 先 40 再 15
  → amount 55
sku-a × 1 → quotes 20，amount 20
没有明细 → quotes []，amount 0
```

## 骨架

```python
def fan_out(state: State):
    if not state["items"]:
        return END
    return [
        Send("quote", {"sku": item["sku"], "qty": item["qty"]})
        for item in state["items"]
    ]

def build_graph():
    g = StateGraph(State)
    g.add_node("quote", quote)
    g.add_node("total", total)
    g.add_conditional_edges(START, fan_out)
    g.add_edge("quote", "total")
    g.add_edge("total", END)
    return g.compile()
```

## 教学子集
- 同一步里的每个 `Send` 必须指向同一个节点。
- `quote` 返回只有一行的 `quotes`。父 reducer 把这些行接起来。
