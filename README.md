# LangGraph Interactive — Lesson 01

FastAPI-Interactive-style lesson: edit a minimal `StateGraph` in the browser, grade it with **Pyodide** (Python in the browser) + a tiny `mini_langgraph` shim. **No API keys. No backend.**

## Open the live site (GitHub Pages)

1. Repo → **Settings → Pages**
2. **Build and deployment → Source**: Deploy from a branch
3. Branch: **`main`** / folder: **`/docs`**
4. Save, wait ~1 minute, open:
   - `https://sdobili.github.io/langgraph-interactive/`

Local preview of the same static site:

```bash
cd docs && python3 -m http.server 8080
# open http://127.0.0.1:8080/
```

On first load the banner shows **Loading Python…** while Pyodide boots from the CDN. Then **Run grade** executes your code inside that runtime against `mini_langgraph.py` (no server process).

## Lesson 01 contract

| Piece | Spec |
|-------|------|
| State | `TypedDict` with `count: int` |
| Nodes | `inc` → `count + 1`; `double` → `count * 2` |
| Edges | `START → inc → double → END` |
| Check | `invoke({"count": 3})` → `{"count": 8}` |

## How grading works (Pages-only)

```
Browser
  ├─ Monaco editor (student Python)
  ├─ Pyodide (CPython WASM from CDN)
  │    ├─ mini_langgraph.py  → aliased as langgraph.graph
  │    └─ exec(student) → build_graph().invoke(...)
  └─ assert cases → PASS / FAIL
```

Student imports stay the same (`from langgraph.graph import StateGraph, START, END`). The shim installs itself as that module before `exec`.

## Layout

```
docs/                         # ← GitHub Pages root
  index.html                  # UI + Pyodide boot banner
  mini_langgraph.py           # pure-Python StateGraph subset
  js/grader.js                # load Pyodide, run asserts
  lessons/01/
    starter.py  solution.py  theory.md
lessons/01_minimal_graph/     # same lesson for optional CLI harness
harness/                      # optional local CLI (needs langgraph installed)
web/                          # optional FastAPI UI (not required for Pages)
```

## Optional: CLI grader (real langgraph)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m harness.grade 01
python -m harness.grade 01 --solution
```

## Optional: FastAPI UI

Still available under `web/` if you want a server-side grader, but **Pages does not use it**.
