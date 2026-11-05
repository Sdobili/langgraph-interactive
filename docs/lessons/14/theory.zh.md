# 14 — 只用最后三条消息来回答

## 要点
- Reducer 可以先调用 `add_messages`，再切片。`keep_last_three` 就是这个函数。
- 节点仍然追加一条助手消息。schema 在追加**之后**丢掉最后三行以前的内容。
- 回复读取最近的用户文本。出现 "refund" 就回答 30 天。其他问题请客户改问退款。
- 只有两条消息的线程短于窗口，两行都会留下。

## 契约

```text
messages:
  user "old"
  assistant "Noted."
  user "Can I get a refund?"
  assistant "Checking the policy."
→ 最后三条是退款问题、"Checking the policy."，
  以及 "Refunds are allowed within 30 days."

messages: user "Hello"
→ user "Hello"，assistant "Ask me about a refund."
```

## 骨架

```python
def keep_last_three(left, right):
    return add_messages(left, right)[-3:]

class State(TypedDict):
    messages: Annotated[list, keep_last_three]

def build_graph():
    g = StateGraph(State)
    g.add_node("reply", reply)
    g.add_edge(START, "reply")
    g.add_edge("reply", END)
    return g.compile()
```

## 教学子集
- 窗口由 reducer 执行，不是另一个 trim 节点。
- `add_messages` 仍会在切片前按相同 id 替换。本课的消息没有 id。
