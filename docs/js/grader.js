/**
 * Browser grader for lessons 01–14.
 * Loads Pyodide, installs mini_langgraph as langgraph.*, then runs docs/grade_lib.py
 * against docs/grader_cases.json for the selected lesson.
 */
(function (global) {
  "use strict";

  let pyodide = null;
  let miniSource = null;
  let gradeLibSource = null;
  let casesByLesson = null;
  let readyPromise = null;

  function setBanner(text, cls) {
    const el = document.getElementById("pyBanner");
    if (!el) return;
    el.textContent = text;
    el.className = "py-banner" + (cls ? " " + cls : "");
  }

  async function loadText(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error("failed to fetch " + url + ": " + res.status);
    return res.text();
  }

  async function ensurePyodide() {
    if (pyodide) return pyodide;
    if (readyPromise) return readyPromise;
    readyPromise = (async () => {
      setBanner("Loading Python runtime (Pyodide)…", "loading");
      if (typeof loadPyodide !== "function") {
        throw new Error("Pyodide CDN script not loaded");
      }
      pyodide = await loadPyodide({
        indexURL: "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/",
      });
      miniSource = miniSource || (await loadText("mini_langgraph.py"));
      gradeLibSource = gradeLibSource || (await loadText("grade_lib.py"));
      pyodide.FS.writeFile("/home/pyodide/mini_langgraph.py", miniSource);
      pyodide.FS.writeFile("/home/pyodide/grade_lib.py", gradeLibSource);
      await pyodide.runPythonAsync(`
import sys
sys.path.insert(0, "/home/pyodide")
import mini_langgraph
mini_langgraph.install_as_langgraph()
`);
      setBanner("Python ready · mini_langgraph installed", "ready");
      return pyodide;
    })().catch((err) => {
      readyPromise = null;
      setBanner("Python failed to load: " + err, "fail");
      throw err;
    });
    return readyPromise;
  }

  async function loadCases() {
    if (casesByLesson) return casesByLesson;
    const text = await loadText("grader_cases.json");
    casesByLesson = JSON.parse(text);
    return casesByLesson;
  }

  function toBase64(text) {
    const bytes = unescape(encodeURIComponent(text));
    if (typeof btoa === "function") return btoa(bytes);
    return Buffer.from(text, "utf8").toString("base64");
  }

  /**
   * Grade student source for a lesson id. Returns { ok: boolean, lines: string[] }.
   */
  async function grade(code, lessonId) {
    const py = await ensurePyodide();
    const allCases = await loadCases();
    const id = String(lessonId || "01");
    const cases = allCases[id];
    if (!cases) {
      return { ok: false, lines: ["❌ no grader cases for lesson " + id] };
    }

    const srcB64 = toBase64(code);
    const casesB64 = toBase64(JSON.stringify(cases));
    const driver = `
import base64, json, sys, io
_stdout = sys.stdout
_buf = io.StringIO()
sys.stdout = _buf
try:
    from grade_lib import grade_source
    src = base64.b64decode(${JSON.stringify(srcB64)}).decode("utf-8")
    cases = json.loads(base64.b64decode(${JSON.stringify(casesB64)}).decode("utf-8"))
    result = grade_source(src, cases)
    captured = _buf.getvalue()
    if captured.strip():
        for line in captured.splitlines():
            result["lines"].append("print: " + line)
    payload = json.dumps(result)
except Exception as exc:
    payload = json.dumps({
        "ok": False,
        "lines": ["❌ grader error: " + type(exc).__name__ + ": " + str(exc)],
    })
finally:
    sys.stdout = _stdout
payload
`;

    try {
      const raw = await py.runPythonAsync(driver);
      const text = String(raw || "").trim();
      const last = text.split("\n").filter(Boolean).pop() || "{}";
      let parsed;
      try {
        parsed = JSON.parse(last);
      } catch (err) {
        return { ok: false, lines: ["❌ grader parse error", last || text] };
      }
      return { ok: !!parsed.ok, lines: parsed.lines || [] };
    } catch (err) {
      return { ok: false, lines: ["❌ Pyodide error: " + err] };
    }
  }

  global.LGGrader = {
    ensurePyodide,
    grade,
    loadCases,
  };
})(window);
