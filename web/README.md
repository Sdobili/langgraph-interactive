# Web UI — Lesson 01

Minimal FastAPI + Monaco page for LangGraph Interactive lesson 01.

## Start

From the project root (venv active):

```bash
cd /workspace/langgraph-interactive
source .venv/bin/activate
uvicorn web.app:app --host 0.0.0.0 --port 8765
```

Open http://127.0.0.1:8765/

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Editor UI |
| GET | `/api/lesson` | theory / starter / solution |
| POST | `/api/grade` | body `{"code":"..."}` → `{ok, lines}` |

Grading runs `python -m harness.grade_submission` in a **subprocess** with the project `.venv`, 15s timeout. Only lesson-01 checks; no shell exposure.

## Smoke test

```bash
curl -s http://127.0.0.1:8765/ | head
curl -s -X POST http://127.0.0.1:8765/api/grade \
  -H 'content-type: application/json' \
  -d '{"code":"def build_graph():\n    return None\n"}'
curl -s -X POST http://127.0.0.1:8765/api/grade \
  -H 'content-type: application/json' \
  --data-binary @<(python3 -c 'import json,pathlib; print(json.dumps({"code": pathlib.Path("lessons/01_minimal_graph/solution.py").read_text()}))')
```
