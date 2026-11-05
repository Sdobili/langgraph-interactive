"""Smoke the Pages lessons: solutions pass, starters fail with a useful line."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
sys.path.insert(0, str(DOCS))

import grade_lib  # noqa: E402

CASES = json.loads((DOCS / "grader_cases.json").read_text(encoding="utf-8"))
LESSONS = ["01", "02", "03", "04", "05", "06"]

# A substring that only appears once the starter is graded helpfully.
STARTER_HINT = {
    "01": "returned None",
    "02": "engineering",
    "03": "faq",
    "04": "GraphRecursionError",
    "05": "Can I get a refund?",
    "06": "What is the order id?",
}

THEORY_MARKERS = {
    "02": "add_conditional_edges",
    "03": "operator.add",
    "04": "recursion_limit",
    "05": "add_messages",
    "06": "InMemorySaver",
}


class PagesLessonsTest(unittest.TestCase):
    def test_case_file_covers_every_lesson(self):
        self.assertEqual(list(CASES), LESSONS)

    def test_solutions_pass(self):
        for lesson_id in LESSONS:
            src = (DOCS / "lessons" / lesson_id / "solution.py").read_text(encoding="utf-8")
            result = grade_lib.grade_source(src, CASES[lesson_id])
            self.assertTrue(
                result["ok"],
                f"lesson {lesson_id} solution failed\n" + "\n".join(result["lines"]),
            )

    def test_starters_fail_helpfully(self):
        for lesson_id in LESSONS:
            src = (DOCS / "lessons" / lesson_id / "starter.py").read_text(encoding="utf-8")
            result = grade_lib.grade_source(src, CASES[lesson_id])
            text = "\n".join(result["lines"])
            self.assertFalse(result["ok"], f"lesson {lesson_id} starter unexpectedly passed\n{text}")
            self.assertIn("❌", text)
            self.assertIn(STARTER_HINT[lesson_id], text, text)

    def test_theory_and_nav_are_wired(self):
        html = (DOCS / "index.html").read_text(encoding="utf-8")
        grader = (DOCS / "js" / "grader.js").read_text(encoding="utf-8")
        self.assertIn("grade_lib", grader)
        self.assertIn("grader_cases.json", grader)
        self.assertIn("LGGrader.grade(editor.getValue(), currentLesson.id)", html)
        self.assertNotIn("active: false", html)
        for lesson_id in LESSONS:
            self.assertIn(f'id: "{lesson_id}"', html)
            folder = DOCS / "lessons" / lesson_id
            for name in ("starter.py", "solution.py", "theory.en.md", "theory.zh.md"):
                self.assertTrue((folder / name).is_file(), name)
            for lang in ("en", "zh"):
                theory = (folder / f"theory.{lang}.md").read_text(encoding="utf-8")
                self.assertIn("```python", theory)
            if lesson_id in THEORY_MARKERS:
                en = (folder / "theory.en.md").read_text(encoding="utf-8")
                self.assertIn(THEORY_MARKERS[lesson_id], en)


if __name__ == "__main__":
    unittest.main()
