# LangGraph Interactive — Lessons 01–06

FastAPI-Interactive-style lessons: edit a `StateGraph` in the browser, grade it with **Pyodide** (Python in the browser) + a tiny `mini_langgraph` shim. **No API keys. No backend.**

Basics track:

| Lesson | Topic | Contract |
|--------|--------|----------|
| 01 | Minimal `StateGraph` | `inc` then `double` |
| 02 | Ticket routing | conditional edge picks billing, engineering, or general |
| 03 | Passage reducer | `operator.add` keeps every hit; `draft` overwrites |
| 04 | Lookup queue | drain `remaining` until `END`; `recursion_limit` stops a long queue |
| 05 | Draft reply | `add_messages` appends, and id `draft` replaces the previous draft |
| 06 | Support thread | `InMemorySaver` keeps `acct-1042` across the next user turn |

`mini_langgraph.py` is a teaching subset (one destination per step, dict messages, latest checkpoint only). The module docstring lists what matches the real API and what is left out. `InMemorySaver` and the older name `MemorySaver` are the same class here.

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

Theory panel: **中文 | EN** tabs (persisted in `localStorage`), skeleton code highlighted with highlight.js (github-dark).

## Lesson contract

Every lesson exports `build_graph()` and returns a compiled graph. The grader calls `invoke` (and, in lesson 06, `get_state`) with the cases in `docs/grader_cases.json`. **Show solution** opens a separate read-only panel. Only **Reset**, or switching lessons, replaces the student editor.

Lesson 01 check: `invoke({"count": 3})` → `{"count": 8}` (`START → inc → double → END`).

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

## Layout (3-column, FastAPI Interactive style)

```
LEFT    Lesson list (01–06)
CENTER  Monaco editor · Run grade / Reset / Show solution · grade output
RIGHT   Courseware (中文|EN theory + highlighted skeleton) · Further reading
```

```
docs/                         # ← GitHub Pages root
  index.html                  # 3-column UI
  mini_langgraph.py           # pure-Python StateGraph subset
  grade_lib.py                # shared assert runner
  grader_cases.json           # per-lesson cases
  js/grader.js                # load Pyodide, run grade_lib
  lessons/01/ … lessons/06/
    starter.py  solution.py
    theory.en.md  theory.zh.md
lessons/01_minimal_graph/     # lesson 01 again, for the optional CLI harness
harness/                      # optional local CLI (needs langgraph installed; lesson 01 only)
web/                          # optional FastAPI UI (not required for Pages)
```

Smoke the Pages lessons locally (no Pyodide, same grader the browser calls):

```bash
python3 -m unittest discover -s tests -v
```

Each `solution.py` passes. Each `starter.py` fails with an expected-vs-actual line (lesson 01 says `build_graph()` returned None).

## Optional: CLI grader (real langgraph)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m harness.grade 01
python -m harness.grade 01 --solution
```

## Optional: FastAPI UI

Still available under `web/` if you want a server-side grader, but **Pages does not use it**.
