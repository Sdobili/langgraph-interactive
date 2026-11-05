"""Pure-Python LangGraph subset for the Pages course (lessons 01–14).

No third-party packages. ``install_as_langgraph()`` aliases this module so student
code can keep the real import paths.

Real API vs this teaching subset
--------------------------------
Implemented (same call shape as current LangGraph docs):

- ``StateGraph``, ``START``, ``END``, ``add_node``, ``add_edge``, ``compile``, ``invoke``
- ``add_conditional_edges(source, path, path_map=None)`` — one destination per step
- Reducers: the first *callable* in a field's ``Annotated[...]`` metadata
- ``recursion_limit`` (default 25) and ``langgraph.errors.GraphRecursionError``
- ``langgraph.graph.message.add_messages`` for dict messages (append, or replace by ``id``)
- ``compile(checkpointer=...)``, ``config["configurable"]["thread_id"]``, ``get_state``
- ``interrupt_before``, ``update_state``, ``get_state_history`` (latest-plus-past snapshots)
- ``langgraph.types.Send`` run **in order** (real LangGraph fans these out in parallel)
- ``RetryPolicy`` on ``add_node(..., retry=...)``
- A compiled graph used as a node (subgraph)
- ``langgraph.store.memory.InMemoryStore`` injected when a node takes ``store``
- ``langgraph.checkpoint.memory.InMemorySaver`` (``MemorySaver`` is the same class)

Not implemented (do not expect these to work here):

- Parallel execution, ``Command``, deferred nodes, ``interrupt()`` inside a node
- sqlite/postgres checkpointers, stores with search, pending writes
- LangChain ``BaseMessage`` / ``GenericFakeChatModel`` (lessons use plain dicts
  and a pure-Python fake)
- ``from __future__ import annotations`` is supported only because the grader
  execs student code as the ``student`` module before ``compile()`` reads hints

Other subset rules the lessons rely on:

- Only node-function executions count toward ``recursion_limit``. Routing
  functions do not. The real runtime counts supersteps and may also count START.
- ``recursion_limit`` above 1000 is rejected so a cycle cannot hang the page.
- A node may have one normal edge *or* conditional edges, not both.
- If a node has no outgoing edge, it goes to ``END`` (lesson 01 behavior).
- Checkpoints store every superstep for one thread, but ``get`` still returns
  the latest values only. ``invoke(input, config)`` merges that input and runs
  from ``START``. ``invoke(None, config)`` resumes ``next`` when a snapshot is
  paused (interrupt or ``update_state``); otherwise it reruns from ``START``.
  Pass ``{}`` to continue a finished thread from the start without changing values.
- Channels without a reducer overwrite. ``operator.add`` needs the key to
  already be present (``None + x`` is a Python error). ``add_messages`` treats
  a missing channel as ``[]``.
"""

from __future__ import annotations

import copy
from typing import Any, Callable, Dict, Optional, Tuple

START = "__start__"
END = "__end__"
DEFAULT_RECURSION_LIMIT = 25
MAX_RECURSION_LIMIT = 1000

__all__ = [
    "START",
    "END",
    "DEFAULT_RECURSION_LIMIT",
    "StateGraph",
    "CompiledGraph",
    "StateSnapshot",
    "GraphRecursionError",
    "InMemorySaver",
    "MemorySaver",
    "InMemoryStore",
    "StoreItem",
    "Send",
    "RetryPolicy",
    "add_messages",
    "install_as_langgraph",
]


class GraphRecursionError(RecursionError):
    """Raised when a run exceeds ``recursion_limit`` (``langgraph.errors``)."""


class StateSnapshot:
    """Subset of LangGraph's snapshot: ``.values`` and ``.next``."""

    def __init__(self, values: dict, next: Any = ()) -> None:
        self.values = values
        self.next = tuple(next)


class InMemorySaver:
    """RAM checkpointer. One thread keeps an ordered list of snapshots.

    ``get`` returns the latest values dict. ``history`` returns every snapshot
    (oldest first) as ``{"values", "next"}``. No sqlite and no pending writes.
    """

    def __init__(self) -> None:
        self._history: Dict[str, list] = {}

    def get(self, thread_id: str) -> Optional[dict]:
        latest = self._latest(thread_id)
        if latest is None:
            return None
        return copy.deepcopy(latest["values"])

    def get_snapshot(self, thread_id: str) -> Optional[dict]:
        latest = self._latest(thread_id)
        if latest is None:
            return None
        return copy.deepcopy(latest)

    def history(self, thread_id: str) -> list:
        return copy.deepcopy(self._history.get(thread_id, []))

    def put(self, thread_id: str, state: dict, next: Any = None) -> None:
        snap = {
            "values": copy.deepcopy(state),
            "next": [str(name) for name in (next or [])],
        }
        self._history.setdefault(thread_id, []).append(snap)

    def _latest(self, thread_id: str) -> Optional[dict]:
        hist = self._history.get(thread_id)
        if not hist:
            return None
        return hist[-1]


class StoreItem:
    """Subset of a store item. Lessons read ``.value``."""

    def __init__(self, value: Any, key: str, namespace: Tuple[str, ...]) -> None:
        self.value = value
        self.key = key
        self.namespace = namespace


class InMemoryStore:
    """RAM store shared across threads. ``put`` / ``get`` by namespace and key."""

    def __init__(self) -> None:
        self._data: Dict[Tuple[Tuple[str, ...], str], Any] = {}

    def put(self, namespace: Any, key: str, value: Any) -> None:
        self._data[(tuple(namespace), str(key))] = copy.deepcopy(value)

    def get(self, namespace: Any, key: str) -> Optional[StoreItem]:
        ns = tuple(namespace)
        item_key = str(key)
        if (ns, item_key) not in self._data:
            return None
        return StoreItem(copy.deepcopy(self._data[(ns, item_key)]), item_key, ns)


class Send:
    """Run ``node`` once with ``arg`` as its state. Batches run in list order."""

    def __init__(self, node: str, arg: Any) -> None:
        if not isinstance(node, str):
            raise TypeError("Send node must be a string")
        self.node = node
        self.arg = arg


class RetryPolicy:
    """Retry a node on exception, up to ``max_attempts`` calls (including the first)."""

    def __init__(self, max_attempts: int = 1) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        self.max_attempts = max_attempts


# Older docs and tutorials import MemorySaver. Same object in this subset.
MemorySaver = InMemorySaver


def _message_id(msg: Any) -> Any:
    if isinstance(msg, dict):
        return msg.get("id")
    return getattr(msg, "id", None)


def add_messages(left: Any, right: Any) -> list:
    """Append dict messages, or replace an existing message with the same ``id``.

    Accepts a single message or a list. This is the small slice of
    ``langgraph.graph.message.add_messages`` used by lesson 05: no
    ``RemoveMessage``, no LangChain message classes required.
    """

    if left is None:
        base: list = []
    elif isinstance(left, list):
        base = list(left)
    else:
        raise TypeError(
            "add_messages expected the existing channel to be a list or missing, "
            f"got {type(left).__name__}"
        )
    incoming = list(right) if isinstance(right, list) else [right]
    index: Dict[Any, int] = {}
    for i, msg in enumerate(base):
        mid = _message_id(msg)
        if mid is not None:
            index[mid] = i
    for msg in incoming:
        mid = _message_id(msg)
        if mid is not None and mid in index:
            base[index[mid]] = msg
        else:
            base.append(msg)
            if mid is not None:
                index[mid] = len(base) - 1
    return base


def _is_annotated(hint: Any) -> bool:
    origin = _origin(hint)
    return origin is not None and getattr(origin, "__name__", "") == "Annotated"


def _origin(hint: Any) -> Any:
    from typing import get_origin

    return get_origin(hint)


def _args(hint: Any) -> tuple:
    from typing import get_args

    return get_args(hint)


def _reducers_from_schema(schema: Any) -> Dict[str, Callable]:
    if schema is None:
        return {}
    hints = None
    try:
        from typing import get_type_hints

        hints = get_type_hints(schema, include_extras=True)
    except Exception:
        raw = getattr(schema, "__annotations__", None)
        hints = raw if isinstance(raw, dict) else None
    if not isinstance(hints, dict):
        return {}
    reducers: Dict[str, Callable] = {}
    for name, hint in hints.items():
        if not _is_annotated(hint):
            continue
        for meta in _args(hint)[1:]:
            if callable(meta):
                reducers[name] = meta
                break
    return reducers


def _apply(current: dict, update: Any, reducers: Dict[str, Callable]) -> None:
    if update is None or update == {}:
        return
    if not isinstance(update, dict):
        raise TypeError(
            f"node updates must be a dict or None, got {type(update).__name__}"
        )
    for key, value in update.items():
        reducer = reducers.get(key)
        if reducer is None:
            current[key] = value
        else:
            current[key] = reducer(current.get(key), value)


def _accepts_store(fn: Any) -> bool:
    import inspect

    try:
        parameters = inspect.signature(fn).parameters
    except (TypeError, ValueError):
        return False
    return "store" in parameters


def _clone(state: dict) -> dict:
    try:
        return copy.deepcopy(state)
    except Exception:
        return dict(state)


def _thread_id(config: Any) -> Optional[str]:
    if not isinstance(config, dict):
        return None
    configurable = config.get("configurable")
    if not isinstance(configurable, dict):
        return None
    thread_id = configurable.get("thread_id")
    if thread_id is None:
        return None
    return str(thread_id)


def _recursion_limit(config: Any) -> int:
    limit = DEFAULT_RECURSION_LIMIT
    if isinstance(config, dict) and "recursion_limit" in config:
        limit = int(config["recursion_limit"])
    if limit > MAX_RECURSION_LIMIT:
        raise ValueError(
            f"recursion_limit cannot exceed {MAX_RECURSION_LIMIT} in this teaching subset"
        )
    return limit


class CompiledGraph:
    def __init__(
        self,
        nodes: Dict[str, Callable],
        edges: Dict[str, str],
        entry: Optional[str],
        conditional: Dict[str, Tuple[Callable, Optional[dict]]],
        reducers: Dict[str, Callable],
        checkpointer: Any = None,
        interrupt_before: Any = None,
        retries: Optional[Dict[str, RetryPolicy]] = None,
        store: Any = None,
    ) -> None:
        self.nodes = nodes
        self.edges = edges
        self.entry = entry
        self.conditional = conditional
        self.reducers = reducers
        self.checkpointer = checkpointer
        self.interrupt_before = set(interrupt_before or [])
        self.retries = retries or {}
        self.store = store

    def __call__(self, state: dict) -> dict:
        """Subgraph use: return the full child state. The parent merges it."""
        return self.invoke(state)

    def invoke(self, state: Any = None, config: Any = None) -> dict:
        limit = _recursion_limit(config)
        current, node, skip_interrupt = self._boot(state, config)
        steps = 0
        while node is not None and node != END:
            if isinstance(node, list):
                node, steps = self._run_sends(node, current, limit, steps)
                continue
            if node in self.interrupt_before and node != skip_interrupt:
                self._checkpoint(current, [node], config)
                return current
            skip_interrupt = None
            if node not in self.nodes:
                raise KeyError(f"unknown node: {node!r}")
            update, steps = self._invoke_node(node, current, limit, steps)
            _apply(current, update, self.reducers)
            nxt = self._route(node, current)
            if isinstance(nxt, list):
                node = nxt
                continue
            if nxt == END:
                self._checkpoint(current, [], config)
                return current
            if nxt in self.interrupt_before:
                self._checkpoint(current, [nxt], config)
                return current
            self._checkpoint(current, [nxt], config)
            node = nxt
        self._checkpoint(current, [], config)
        return current

    def get_state(self, config: Any) -> StateSnapshot:
        thread_id = _thread_id(config)
        if self.checkpointer is None or thread_id is None:
            return StateSnapshot({})
        if hasattr(self.checkpointer, "get_snapshot"):
            snap = self.checkpointer.get_snapshot(thread_id)
            if not snap:
                return StateSnapshot({})
            return StateSnapshot(_clone(snap["values"]), snap.get("next") or [])
        saved = self.checkpointer.get(thread_id)
        if not saved:
            return StateSnapshot({})
        return StateSnapshot(_clone(saved))

    def get_state_history(self, config: Any) -> list:
        thread_id = _thread_id(config)
        if (
            self.checkpointer is None
            or thread_id is None
            or not hasattr(self.checkpointer, "history")
        ):
            return []
        snaps = self.checkpointer.history(thread_id)
        return [
            StateSnapshot(_clone(snap["values"]), snap.get("next") or [])
            for snap in reversed(snaps)
        ]

    def update_state(self, config: Any, values: Any = None, as_node: Any = None) -> StateSnapshot:
        if self.checkpointer is None:
            raise ValueError("update_state requires a checkpointer")
        thread_id = _thread_id(config)
        if thread_id is None:
            raise ValueError("update_state requires configurable.thread_id")
        current = self.checkpointer.get(thread_id)
        current = {} if current is None else _clone(current)
        if values:
            _apply(current, values, self.reducers)
        if as_node is not None:
            nxt = self._route(as_node, current)
            if isinstance(nxt, list):
                raise ValueError("update_state as_node cannot route to Send")
            next_nodes = [] if nxt == END else [nxt]
        else:
            snap = (
                self.checkpointer.get_snapshot(thread_id)
                if hasattr(self.checkpointer, "get_snapshot")
                else None
            )
            next_nodes = list(snap["next"]) if snap else []
        self._checkpoint(current, next_nodes, config)
        return StateSnapshot(_clone(current), next_nodes)

    def _initial_state(self, state: Any, config: Any) -> dict:
        if state is None:
            incoming: dict = {}
        elif isinstance(state, dict):
            incoming = state
        else:
            raise TypeError(
                f"invoke() state must be a dict or None, got {type(state).__name__}"
            )
        thread_id = _thread_id(config)
        if self.checkpointer is not None and thread_id is not None:
            prev = self.checkpointer.get(thread_id)
            if prev is not None:
                merged = _clone(prev)
                _apply(merged, incoming, self.reducers)
                return merged
        return _clone(incoming)

    def _save(self, state: dict, config: Any) -> None:
        self._checkpoint(state, [], config)

    def _checkpoint(self, state: dict, next_nodes: list, config: Any) -> None:
        thread_id = _thread_id(config)
        if self.checkpointer is None or thread_id is None:
            return
        self.checkpointer.put(thread_id, state, next_nodes)

    def _boot(self, state: Any, config: Any):
        thread_id = _thread_id(config)
        if state is None and self.checkpointer is not None and thread_id is not None:
            snap = (
                self.checkpointer.get_snapshot(thread_id)
                if hasattr(self.checkpointer, "get_snapshot")
                else None
            )
            if snap and snap.get("next"):
                nxt = snap["next"][0]
                return _clone(snap["values"]), nxt, nxt
        current = self._initial_state(state, config)
        node = self.entry if self.entry is not None else self._route(START, current)
        return current, node, None

    def _invoke_node(self, name: str, state: Any, limit: int, steps: int):
        policy = self.retries.get(name)
        attempts = policy.max_attempts if policy is not None else 1
        last_exc: Optional[BaseException] = None
        for _ in range(attempts):
            steps += 1
            if steps > limit:
                raise GraphRecursionError(
                    f"Recursion limit of {limit} reached without hitting a stop condition."
                )
            try:
                return self._call(self.nodes[name], state), steps
            except GraphRecursionError:
                raise
            except Exception as exc:
                last_exc = exc
        assert last_exc is not None
        raise last_exc

    def _call(self, fn: Any, state: Any) -> Any:
        if isinstance(fn, CompiledGraph):
            return fn.invoke(state)
        if _accepts_store(fn):
            return fn(state, store=self.store)
        return fn(state)

    def _run_sends(self, sends: list, current: dict, limit: int, steps: int):
        if not sends:
            return END, steps
        targets = []
        for send in sends:
            if not isinstance(send, Send):
                raise TypeError(
                    "a conditional path may return one node name or a list of Send; "
                    "parallel name lists are not in this subset"
                )
            if send.node not in self.nodes:
                raise KeyError(f"unknown node: {send.node!r}")
            targets.append(send.node)
            update, steps = self._invoke_node(send.node, send.arg, limit, steps)
            _apply(current, update, self.reducers)
        if len(set(targets)) != 1:
            raise ValueError("Send targets in one step must share one node name")
        target = targets[0]
        if target in self.conditional:
            return self._route(target, current), steps
        return self.edges.get(target, END), steps

    def _route(self, source: str, state: dict) -> Any:
        if source in self.conditional:
            path, path_map = self.conditional[source]
            chosen = path(state)
            if isinstance(chosen, (list, tuple)):
                if all(isinstance(item, Send) for item in chosen):
                    return list(chosen)
                raise TypeError(
                    "a conditional path may return one node name or a list of Send; "
                    "parallel name lists are not in this subset"
                )
            if not isinstance(chosen, str):
                raise TypeError(
                    f"conditional path from {source!r} must return a node name string, "
                    f"got {type(chosen).__name__}"
                )
            if path_map is not None:
                if chosen not in path_map:
                    options = ", ".join(repr(k) for k in path_map)
                    raise ValueError(
                        f"conditional path from {source!r} returned {chosen!r}, "
                        f"expected one of: {options}"
                    )
                chosen = path_map[chosen]
                if not isinstance(chosen, str):
                    raise TypeError("path_map values must be node name strings")
            return chosen
        if source == START:
            raise ValueError("missing edge from START")
        return self.edges.get(source, END)


class StateGraph:
    def __init__(self, state_schema: Any = None) -> None:
        self.state_schema = state_schema
        self._nodes: Dict[str, Callable] = {}
        self._edges: Dict[str, str] = {}
        self._conditional: Dict[str, Tuple[Callable, Optional[dict]]] = {}
        self._retries: Dict[str, RetryPolicy] = {}
        self._entry: Optional[str] = None

    def add_node(self, name: str, action: Callable, retry: Any = None) -> "StateGraph":
        if name in (START, END):
            raise ValueError(f"reserved node name: {name}")
        if not callable(action):
            raise TypeError(f"node {name!r} action must be callable")
        if retry is not None and not isinstance(retry, RetryPolicy):
            raise TypeError("retry must be a RetryPolicy")
        self._nodes[name] = action
        if isinstance(retry, RetryPolicy):
            self._retries[name] = retry
        return self

    def add_edge(self, source: str, target: str) -> "StateGraph":
        self._reject_second_outgoing(source)
        if not isinstance(target, str):
            raise TypeError("edge target must be a node name string")
        if source == START:
            self._entry = target
        else:
            self._edges[source] = target
        return self

    def add_conditional_edges(
        self,
        source: str,
        path: Callable,
        path_map: Any = None,
    ) -> "StateGraph":
        """Route ``source`` through ``path(state) -> name``.

        ``path_map`` is an optional dict, or a list of allowed node names
        (each name maps to itself). Omit it to use the returned string as the
        next node (``END`` is allowed).
        """

        self._reject_second_outgoing(source)
        if not callable(path):
            raise TypeError("path must be callable")
        if isinstance(path_map, list):
            normalized = {name: name for name in path_map}
        elif path_map is None:
            normalized = None
        elif isinstance(path_map, dict):
            normalized = dict(path_map)
        else:
            raise TypeError("path_map must be a dict, a list of node names, or None")
        if normalized is not None:
            for key, target in normalized.items():
                if not isinstance(target, str):
                    raise TypeError(f"path_map[{key!r}] must be a node name string")
        self._conditional[source] = (path, normalized)
        return self

    def compile(
        self,
        checkpointer: Any = None,
        interrupt_before: Any = None,
        store: Any = None,
    ) -> CompiledGraph:
        if self._entry is None and START not in self._conditional:
            raise ValueError("missing edge from START")
        interrupts = list(interrupt_before or [])
        unknown_interrupts = [name for name in interrupts if name not in self._nodes]
        if unknown_interrupts:
            raise ValueError(f"interrupt_before references unknown nodes: {unknown_interrupts}")
        referenced = []
        if self._entry is not None:
            referenced.append(self._entry)
        referenced.extend(self._edges.keys())
        referenced.extend(self._edges.values())
        for source, (_path, path_map) in self._conditional.items():
            if source != START:
                referenced.append(source)
            if path_map:
                referenced.extend(path_map.values())
        missing = sorted({n for n in referenced if n != END and n not in self._nodes})
        if missing:
            raise ValueError(f"edges reference unknown nodes: {missing}")
        conditional = {
            source: (path, None if path_map is None else dict(path_map))
            for source, (path, path_map) in self._conditional.items()
        }
        return CompiledGraph(
            nodes=dict(self._nodes),
            edges=dict(self._edges),
            entry=self._entry,
            conditional=conditional,
            reducers=_reducers_from_schema(self.state_schema),
            checkpointer=checkpointer,
            interrupt_before=interrupts,
            retries=dict(self._retries),
            store=store,
        )

    def _reject_second_outgoing(self, source: str) -> None:
        if source in self._conditional or source in self._edges or (
            source == START and self._entry is not None
        ):
            raise ValueError(
                f"{source!r} already has an outgoing edge; "
                "this subset allows one normal edge or one conditional edge per node"
            )


def install_as_langgraph() -> None:
    """Register this module under the LangGraph import paths lessons use."""

    import sys
    import types

    graph = sys.modules[__name__]
    pkg = sys.modules.get("langgraph")
    if pkg is None:
        pkg = types.ModuleType("langgraph")
        pkg.__path__ = []  # mark as package
        sys.modules["langgraph"] = pkg
    else:
        pkg.__path__ = getattr(pkg, "__path__", [])
    pkg.graph = graph
    sys.modules["langgraph.graph"] = graph

    errors = types.ModuleType("langgraph.errors")
    errors.GraphRecursionError = GraphRecursionError
    pkg.errors = errors
    sys.modules["langgraph.errors"] = errors

    message = types.ModuleType("langgraph.graph.message")
    message.add_messages = add_messages
    sys.modules["langgraph.graph.message"] = message

    checkpoint_pkg = sys.modules.get("langgraph.checkpoint")
    if checkpoint_pkg is None:
        checkpoint_pkg = types.ModuleType("langgraph.checkpoint")
        checkpoint_pkg.__path__ = []
        sys.modules["langgraph.checkpoint"] = checkpoint_pkg
    pkg.checkpoint = checkpoint_pkg

    memory = types.ModuleType("langgraph.checkpoint.memory")
    memory.InMemorySaver = InMemorySaver
    memory.MemorySaver = MemorySaver
    checkpoint_pkg.memory = memory
    sys.modules["langgraph.checkpoint.memory"] = memory

    types_mod = types.ModuleType("langgraph.types")
    types_mod.Send = Send
    types_mod.RetryPolicy = RetryPolicy
    pkg.types = types_mod
    sys.modules["langgraph.types"] = types_mod

    store_pkg = sys.modules.get("langgraph.store")
    if store_pkg is None:
        store_pkg = types.ModuleType("langgraph.store")
        store_pkg.__path__ = []
        sys.modules["langgraph.store"] = store_pkg
    pkg.store = store_pkg
    store_memory = types.ModuleType("langgraph.store.memory")
    store_memory.InMemoryStore = InMemoryStore
    store_pkg.memory = store_memory
    sys.modules["langgraph.store.memory"] = store_memory
