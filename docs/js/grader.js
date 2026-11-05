/**
 * Browser grader for Lesson 01 via Pyodide + mini_langgraph.py
 * Flow: load Pyodide → install mini as langgraph.graph → exec student code → assert invokes
 */
(function (global) {
  "use strict";

  const CASES = [
    { input: { count: 3 }, expected: { count: 8 } },
    { input: { count: 0 }, expected: { count: 2 } },
    { input: { count: 5 }, expected: { count: 12 } },
  ];

  let pyodide = null;
  let miniSource = null;
  let readyPromise = null;

  function setBanner(text, cls) {
    const el = document.getElementById("pyBanner");
    if (!el) return;
    el.textContent = text;
    el.className = "py-banner" + (cls ? " " + cls : "");
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
      if (!miniSource) {
        const res = await fetch("mini_langgraph.py");
        if (!res.ok) throw new Error("failed to fetch mini_langgraph.py: " + res.status);
        miniSource = await res.text();
      }
      // Install mini_langgraph into the interpreter and alias as langgraph.graph
      pyodide.FS.writeFile("/home/pyodide/mini_langgraph.py", miniSource);
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

  /**
   * Grade student source. Returns { ok: boolean, lines: string[] }
   */
  async function grade(code) {
    const lines = [];
    const py = await ensurePyodide();

    // Escape student code into a Python triple-quoted string safely
    // Use base64 to avoid quote/indent issues
    const b64 =
      typeof btoa === "function"
        ? btoa(unescape(encodeURIComponent(code)))
        : Buffer.from(code, "utf8").toString("base64");

    const driver = `
import base64, json, traceback
from mini_langgraph import install_as_langgraph
install_as_langgraph()

src = base64.b64decode(${JSON.stringify(b64)}).decode("utf-8")
ns = {}
result = {"ok": False, "lines": [], "error": None}
try:
    exec(compile(src, "<student>", "exec"), ns, ns)
except Exception as e:
    result["lines"].append("❌ exec error: " + type(e).__name__ + ": " + str(e))
    result["error"] = traceback.format_exc()
    print(json.dumps(result))
else:
    if "build_graph" not in ns:
        result["lines"].append("❌ build_graph() not defined")
        print(json.dumps(result))
    else:
        try:
            g = ns["build_graph"]()
        except Exception as e:
            result["lines"].append("❌ build_graph() raised: " + type(e).__name__ + ": " + str(e))
            print(json.dumps(result))
        else:
            if g is None:
                result["lines"].append("❌ returned None — did you forget return g.compile()?")
                print(json.dumps(result))
            elif not hasattr(g, "invoke"):
                result["lines"].append("❌ compiled object has no invoke()")
                print(json.dumps(result))
            else:
                cases = ${JSON.stringify(CASES)}
                all_ok = True
                for case in cases:
                    try:
                        out = g.invoke(case["input"])
                    except Exception as e:
                        all_ok = False
                        result["lines"].append(
                            "❌ invoke(" + json.dumps(case["input"]) + ") raised: "
                            + type(e).__name__ + ": " + str(e)
                        )
                        continue
                    if out == case["expected"]:
                        result["lines"].append(
                            "✅ invoke(" + json.dumps(case["input"]) + ") → " + json.dumps(out)
                        )
                    else:
                        all_ok = False
                        result["lines"].append(
                            "❌ invoke(" + json.dumps(case["input"]) + ") → " + json.dumps(out)
                            + "  (expected " + json.dumps(case["expected"]) + ")"
                        )
                result["ok"] = all_ok
                if all_ok:
                    result["lines"].insert(0, "✅ PASS — all cases matched")
                else:
                    result["lines"].insert(0, "❌ FAIL — see cases below")
                print(json.dumps(result))
`;

    try {
      // Capture stdout for JSON result
      await py.runPythonAsync(`
import sys, io
_stdout = sys.stdout
sys.stdout = io.StringIO()
`);
      await py.runPythonAsync(driver);
      const raw = await py.runPythonAsync(`
_out = sys.stdout.getvalue()
sys.stdout = _stdout
_out
`);
      const text = String(raw || "").trim();
      // last non-empty line should be JSON
      const last = text.split("\n").filter(Boolean).pop() || "{}";
      let parsed;
      try {
        parsed = JSON.parse(last);
      } catch {
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
    CASES,
  };
})(window);
