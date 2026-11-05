"""Local web UI for LangGraph Interactive — Lesson 01."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
LESSON = ROOT / "lessons" / "01_minimal_graph"
STATIC = Path(__file__).resolve().parent / "static"
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"
TIMEOUT_SEC = 15

app = FastAPI(title="LangGraph Interactive", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")


class GradeRequest(BaseModel):
    code: str = Field(..., max_length=80_000)


def _read_lesson(name: str) -> str:
    path = LESSON / name
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Missing {name}")
    return path.read_text(encoding="utf-8")


@app.get("/", response_class=HTMLResponse)
async def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/api/lesson")
async def get_lesson() -> dict:
    return {
        "id": "01",
        "title": "Lesson 01 — Minimal StateGraph",
        "theory": _read_lesson("theory.md"),
        "starter": _read_lesson("starter.py"),
        "solution": _read_lesson("solution.py"),
    }


@app.post("/api/grade")
async def grade(body: GradeRequest) -> dict:
    """Grade submitted lesson-01 code via venv subprocess (timeout, no shell)."""
    py = str(VENV_PYTHON if VENV_PYTHON.exists() else sys.executable)
    with tempfile.TemporaryDirectory(prefix="lgi_web_") as td:
        code_path = Path(td) / "submission.py"
        code_path.write_text(body.code, encoding="utf-8")
        env = {
            k: v
            for k, v in os.environ.items()
            if k not in ("PYTHONPATH",)
        }
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        try:
            proc = subprocess.run(
                [py, "-m", "harness.grade_submission", str(code_path)],
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SEC,
                cwd=str(ROOT),
                env=env,
            )
        except subprocess.TimeoutExpired:
            return {
                "ok": False,
                "lines": [f"❌ Grader timed out after {TIMEOUT_SEC}s (infinite loop?)"],
            }

    out_lines = (proc.stdout or "").strip().splitlines()
    raw = out_lines[-1] if out_lines else ""
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

    err = (proc.stderr or proc.stdout or "unknown error").strip().splitlines()[-12:]
    return {
        "ok": False,
        "lines": ["❌ Grader process failed"] + [f"   {e}" for e in err],
    }
