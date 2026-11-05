# LangGraph Interactive — Lesson 01 MVP

FastAPI-Interactive-style grader for LangGraph. No API keys. Lesson 1 is a pure `StateGraph` (no LLM).

## Open a live demo

| Path | Works? | Notes |
|------|--------|--------|
| **GitHub Pages** | **No** | Pages is static only. This app needs FastAPI + a Python subprocess to grade LangGraph code. |
| **Render (Docker, free)** | **Yes (recommended)** | Connect this repo → Deploy Blueprint / Web Service. Public `*.onrender.com` URL. Free tier sleeps after idle. |
| **GitHub Codespaces** | **Yes** | Green **Code → Codespaces → Create**. Dev container installs deps and starts uvicorn on **8765**; use the forwarded URL. |
| **Fly.io** | Yes (account) | `fly launch` / `fly deploy` with included `fly.toml`. Needs a Fly account. |
| **Local / Tailscale Funnel** | Interim | `uvicorn web.app:app --host 0.0.0.0 --port 8765` |

### Render one-click (public URL)

1. Open [Render Dashboard → New → Blueprint](https://dashboard.render.com/blueprints) (or Web Service).
2. Connect GitHub and select **`Sdobili/langgraph-interactive`**.
3. Accept `render.yaml` (Docker, port 8765, free plan).
4. Wait for build; open the `*.onrender.com` URL.

Cold starts on free tier can take ~30–60s.

### Codespaces one-click

1. On this repo: **Code → Codespaces → Create codespace on main**.
2. After attach, uvicorn should be on port **8765**.
3. Click the Ports tab → open the public forwarded URL.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn web.app:app --host 0.0.0.0 --port 8765
# open http://127.0.0.1:8765/
```

CLI grader:

```bash
python -m harness.grade 01
python -m harness.grade 01 --solution
```

## Lesson 01 contract

| Piece | Spec |
|-------|------|
| State | `TypedDict` with `count: int` |
| Nodes | `inc` → `count + 1`; `double` → `count * 2` |
| Edges | `START → inc → double → END` |
| Check | `invoke({"count": 3})` → `{"count": 8}` |

## Layout

```
langgraph-interactive/
  Dockerfile          # production image
  render.yaml         # Render Blueprint (free web)
  fly.toml            # optional Fly.io
  .devcontainer/      # Codespaces
  harness/            # grader
  lessons/01_minimal_graph/
  web/                # FastAPI UI + /api/grade
```

## Why not GitHub Pages / Actions static deploy?

The UI is HTML + Monaco, but **Run grade** POSTs to `/api/grade`, which writes a temp file and runs `python -m harness.grade_submission` with **langgraph** installed. GitHub Pages cannot run that backend. A Pages-only deploy would show the editor with a dead Grade button.
