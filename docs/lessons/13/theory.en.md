# 13 — Retry a timed-out charge

## What you learn
- `RetryPolicy(max_attempts=2)` calls the node a second time when the first call raises.
- `charge` fails once per `order_id`, then returns `refund-<order_id>-<amount>`.
- The attempts counter lives on the function and resets when the order id changes, so each case gets its own first failure.
- Without the policy, that first `TimeoutError` fails the run.

## Contract

```text
order 1042, amount 40 → receipt "refund-1042-40"
order 99, amount 15   → receipt "refund-99-15"
```

## Skeleton

```python
def build_graph():
    g = StateGraph(State)
    g.add_node("charge", charge, retry=RetryPolicy(max_attempts=2))
    g.add_edge(START, "charge")
    g.add_edge("charge", END)
    return g.compile()
```

## Teaching subset
- Each attempt counts toward `recursion_limit`.
- Only exceptions are retried. A returned dict is success, even if the receipt is wrong.
- There is no backoff and no separate error channel.
