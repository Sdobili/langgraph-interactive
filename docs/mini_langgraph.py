"""Pure-Python LangGraph subset for the Pages course (lessons 01–06).

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
- ``langgraph.checkpoint.memory.InMemorySaver`` (``MemorySaver`` is the same class)

Not implemented (do not expect these to work here):

- Parallel fan-out / ``Send``, deferred nodes, subgraphs, interrupts, commands
- Stores, time travel, sqlite/postgres checkpointers, pending writes
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
- Checkpoints store the latest full state dict per ``thread_id`` only.
  The next ``invoke`` merges that input onto the checkpoint (reducers apply)
  and runs the graph from the start again. Pass ``{}`` to continue unchanged.
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
    "add_messages",
    "install_as_langgraph",
]


class GraphRecursionError(RecursionError):
    """Raised when a run exceeds ``recursion_limit`` (``langgraph.errors``)."""


class StateSnapshot:
    """Subset of LangGraph's snapshot: only ``.values`` is populated."""

    def __init__(self, values: dict) -> None:
        self.values = values


class InMemorySaver:
    """RAM checkpointer: one latest state dict per thread id.

    Same idea as ``langgraph.checkpoint.memory.InMemorySaver`` / ``MemorySaver``.
    No history and no cross-process persistence.
    """

    def __init__(self) -> None:
        self._store: Dict[str, dict] = {}

    def get(self, thread_id: str) -> Optional[dict]:
        saved = self._store.get(thread_id)
        if saved is None:
            return None
        return copy.deepcopy(saved)

    def put(self, thread_id: str, state: dict) -> None:
        self._store[thread_id] = copy.deepcopy(state)


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
    ) -> None:
        self.nodes = nodes
        self.edges = edges
        self.entry = entry
        self.conditional = conditional
        self.reducers = reducers
        self.checkpointer = checkpointer

    def invoke(self, state: Any = None, config: Any = None) -> dict:
        limit = _recursion_limit(config)
        current = self._initial_state(state, config)
        node = self.entry if self.entry is not None else self._route(START, current)
        steps = 0
        while node is not None and node != END:
            steps += 1
            if steps > limit:
                raise GraphRecursionError(
                    f"Recursion limit of {limit} reached without hitting a stop condition."
                )
            if node not in self.nodes:
                raise KeyError(f"unknown node: {node!r}")
            update = self.nodes[node](current)
            _apply(current, update, self.reducers)
            node = self._route(node, current)
        self._save(current, config)
        return current

    def get_state(self, config: Any) -> StateSnapshot:
        thread_id = _thread_id(config)
        if self.checkpointer is None or thread_id is None:
            return StateSnapshot({})
        saved = self.checkpointer.get(thread_id)
        if not saved:
            return StateSnapshot({})
        return StateSnapshot(_clone(saved))

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
        thread_id = _thread_id(config)
        if self.checkpointer is None or thread_id is None:
            return
        self.checkpointer.put(thread_id, state)

    def _route(self, source: str, state: dict) -> str:
        if source in self.conditional:
            path, path_map = self.conditional[source]
            chosen = path(state)
            if isinstance(chosen, (list, tuple)):
                raise TypeError(
                    "conditional path returned multiple destinations; "
                    "this teaching subset runs one node at a time (no Send / parallel fan-out)"
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
        self._entry: Optional[str] = None

    def add_node(self, name: str, action: Callable) -> "StateGraph":
        if name in (START, END):
            raise ValueError(f"reserved node name: {name}")
        if not callable(action):
            raise TypeError(f"node {name!r} action must be callable")
        self._nodes[name] = action
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

    def compile(self, checkpointer: Any = None) -> CompiledGraph:
        if self._entry is None and START not in self._conditional:
            raise ValueError("missing edge from START")
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
