# 13 — 网关超时后再扣一次

## 要点
- `RetryPolicy(max_attempts=2)` 在第一次调用抛错时再调用一次。
- 每个 `order_id` 的 `charge` 会先失败一次，然后返回 `refund-<order_id>-<amount>`。
- 次数记在函数上，订单号变化时清零，所以每个判题用例都有自己的第一次失败。
- 没有这个 policy 时，第一次 `TimeoutError` 会让整次运行失败。

## 契约

```text
订单 1042，金额 40 → receipt "refund-1042-40"
订单 99，金额 15   → receipt "refund-99-15"
```

## 骨架

```python
def build_graph():
    g = StateGraph(State)
    g.add_node("charge", charge, retry=RetryPolicy(max_attempts=2))
    g.add_edge(START, "charge")
    g.add_edge("charge", END)
    return g.compile()
```

## 教学子集
- 每一次尝试都计入 `recursion_limit`。
- 只有异常才会重试。返回了 dict 就算成功，哪怕回执内容不对。
- 没有退避，也没有单独的错误通道。
