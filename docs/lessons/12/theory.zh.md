# 12 — 跨线程还在的客户备注

## 要点
- 检查点属于一个 `thread_id`。store 挂在编译后的图上，每个线程都能看见。
- `compile(store=InMemoryStore())` 会在节点写成 `remember(state, store)` 时把 store 传进去。
- `store.put(("customers", customer_id), "profile", {"note": ...})` 写入。
- `store.get(...).value` 读回。没有这条记录时返回 `None`。

## 契约

```text
线程 writer，客户 1042，note "Email refunds to ada@example.com"
  → saved 就是这句话
线程 reader，客户 1042，note ""
  → saved 仍然是这句话
线程 other，客户 88，note ""
  → saved 是 ""
```

## 骨架

```python
def remember(state: State, store) -> dict:
    namespace = ("customers", state["customer_id"])
    if state.get("note"):
        store.put(namespace, "profile", {"note": state["note"]})
        saved = state["note"]
    else:
        item = store.get(namespace, "profile")
        saved = "" if item is None else item.value["note"]
    return {"saved": saved}

def build_graph():
    g = StateGraph(State)
    g.add_node("remember", remember)
    g.add_edge(START, "remember")
    g.add_edge("remember", END)
    return g.compile(store=InMemoryStore())
```

## 教学子集
- `get` 返回带 `.value` 的 item，或者 `None`。没有搜索。
- store 在 `build_graph()` 返回的对象里面。再调用一次 `build_graph()` 就是一块空的 store。
