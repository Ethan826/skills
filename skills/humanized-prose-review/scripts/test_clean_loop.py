"""Tests for clean_loop.py: the decision that ends a review loop."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import clean_loop as loop  # noqa: E402

SOURCE = "The cache held 120 rows in 2024. See `cache.py` and Redis for details.\n"
CLEAN = "The cache held 120 rows in 2024. See `cache.py` and Redis for the details.\n"


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def audit(text, auditor, findings=(), **extra):
    return {"text_sha256": sha(text), "auditor": auditor,
            "findings": list(findings), **extra}


def finding(span, pattern="§1", tier="strong"):
    return {"span": span, "pattern": pattern, "tier": tier, "why": "reason"}


class Decide(unittest.TestCase):
    def setUp(self):
        self.state = loop.new_state(SOURCE, max_rounds=3)

    def test_empty_audit_of_a_lint_clean_text_is_clean(self):
        self.assertEqual(loop.record(self.state, CLEAN, audit(CLEAN, "a1"))["verdict"],
                         "CLEAN")

    def test_a_strong_finding_continues(self):
        round_ = loop.record(self.state, CLEAN,
                             audit(CLEAN, "a1", [finding("The cache held")]))
        self.assertEqual(round_["verdict"], "CONTINUE")

    def test_one_weak_finding_does_not_stop_clean(self):
        round_ = loop.record(self.state, CLEAN, audit(
            CLEAN, "a1", [finding("The cache held", "§9", "weak")]))
        self.assertEqual(round_["verdict"], "CLEAN")

    def test_two_distinct_weak_findings_in_a_paragraph_continue(self):
        round_ = loop.record(self.state, CLEAN, audit(CLEAN, "a1", [
            finding("The cache held", "§9", "weak"),
            finding("See `cache.py`", "§11", "weak")]))
        self.assertEqual(round_["verdict"], "CONTINUE")

    def test_lint_blocking_prevents_clean_even_if_the_auditor_saw_nothing(self):
        text = SOURCE + "\nLet's dive in to the rest.\n"
        round_ = loop.record(self.state, text, audit(text, "a1"))
        self.assertEqual(round_["verdict"], "CONTINUE")
        self.assertEqual(round_["lint_blocking"], ["staged-opener"])

    def test_lost_number_prevents_clean(self):
        text = "The cache held rows in 2024. See `cache.py` and Redis for details.\n"
        round_ = loop.record(self.state, text, audit(text, "a1"))
        self.assertEqual(round_["verdict"], "CONTINUE")
        self.assertEqual(round_["lost"], ["120"])

    def test_lost_code_url_and_name_are_all_caught(self):
        source = "We use `alpha` with Redis at https://example.com/x today.\n"
        lost = loop.fact_floor(source, "We use it there today.\n")
        self.assertEqual(sorted(lost),
                         ["Redis", "`alpha`", "https://example.com/x"])

    def test_an_identifier_is_not_cut_into_a_false_name(self):
        source = "Pass the folder HUMAN_DIR here.\n"
        self.assertEqual(loop.fact_floor(source, source), [])

    def test_sentence_initial_word_is_not_a_name(self):
        self.assertEqual(loop.fact_floor("The cache works.\n", "A cache works.\n"), [])

    def test_accepted_loss_with_a_reason_clears_the_floor(self):
        text = "The cache held rows in 2024. See `cache.py` and Redis for details.\n"
        round_ = loop.record(self.state, text, audit(
            text, "a1", accepted_losses=[{"item": "120", "reason": "owner cut it"}]))
        self.assertEqual(round_["verdict"], "CLEAN")

    def test_accepted_loss_without_a_reason_is_rejected(self):
        text = "The cache held rows in 2024. See `cache.py` and Redis for details.\n"
        with self.assertRaisesRegex(loop.LoopError, "needs item and reason"):
            loop.record(self.state, text,
                        audit(text, "a1", accepted_losses=[{"item": "120"}]))

    def test_facts_are_compared_with_the_source_not_the_last_round(self):
        first = "The cache held rows in 2024. See `cache.py` and Redis for details.\n"
        loop.record(self.state, first, audit(first, "a1", [finding("The cache")]))
        second = first.replace("for details", "for more")
        round_ = loop.record(self.state, second, audit(second, "a2"))
        self.assertEqual(round_["lost"], ["120"])


class Honesty(unittest.TestCase):
    """An audit is rejected unless it can be tied to this text and a new reader."""

    def setUp(self):
        self.state = loop.new_state(SOURCE, max_rounds=5)

    def test_audit_of_a_different_text_is_rejected(self):
        with self.assertRaisesRegex(loop.LoopError, "audit is of another text"):
            loop.record(self.state, CLEAN, audit(SOURCE, "a1"))

    def test_reused_auditor_is_rejected(self):
        loop.record(self.state, CLEAN, audit(CLEAN, "a1", [finding("The cache")]))
        text = CLEAN.replace("the details", "more details")
        with self.assertRaisesRegex(loop.LoopError, "auditor a1 already"):
            loop.record(self.state, text, audit(text, "a1"))

    def test_span_not_in_the_text_is_rejected(self):
        with self.assertRaisesRegex(loop.LoopError, "span not in text"):
            loop.record(self.state, CLEAN, audit(CLEAN, "a1", [finding("nowhere")]))

    def test_span_across_a_line_wrap_is_found(self):
        text = "The cache held 120 rows in\n2024. See `cache.py` and Redis for details.\n"
        round_ = loop.record(self.state, text, audit(
            text, "a1", [finding("rows in 2024. See")]))
        self.assertEqual(round_["verdict"], "CONTINUE")

    def test_unknown_tier_is_rejected(self):
        with self.assertRaisesRegex(loop.LoopError, "tier"):
            loop.record(self.state, CLEAN,
                        audit(CLEAN, "a1", [finding("The cache", "§1", "medium")]))

    def test_missing_fields_are_rejected(self):
        with self.assertRaisesRegex(loop.LoopError, "audit needs"):
            loop.record(self.state, CLEAN, {"auditor": "a1"})


class Stopping(unittest.TestCase):
    def test_round_cap_stops_with_findings_open(self):
        state = loop.new_state(SOURCE, max_rounds=2)
        texts = [CLEAN, CLEAN.replace("the details", "more details")]
        loop.record(state, texts[0], audit(texts[0], "a1", [finding("The cache")]))
        round_ = loop.record(state, texts[1], audit(texts[1], "a2", [finding("See")]))
        self.assertEqual(round_["verdict"], "STOP_CAP")

    def test_clean_on_the_last_round_is_still_clean(self):
        state = loop.new_state(SOURCE, max_rounds=1)
        self.assertEqual(loop.record(state, CLEAN, audit(CLEAN, "a1"))["verdict"], "CLEAN")

    def test_no_rounds_after_a_final_verdict(self):
        state = loop.new_state(SOURCE, max_rounds=3)
        loop.record(state, CLEAN, audit(CLEAN, "a1"))
        with self.assertRaisesRegex(loop.LoopError, "already ended"):
            loop.record(state, CLEAN, audit(CLEAN, "a2"))

    def test_returning_to_an_earlier_text_stops(self):
        state = loop.new_state(SOURCE, max_rounds=5)
        other = CLEAN.replace("the details", "more details")
        loop.record(state, CLEAN, audit(CLEAN, "a1", [finding("The cache")]))
        loop.record(state, other, audit(other, "a2", [finding("The cache")]))
        round_ = loop.record(state, CLEAN, audit(CLEAN, "a3", [finding("The cache")]))
        self.assertEqual(round_["verdict"], "STOP_OSCILLATION")

    def test_same_finding_in_three_rounds_stops(self):
        state = loop.new_state(SOURCE, max_rounds=9)
        texts = [CLEAN, CLEAN + "\nOne.\n", CLEAN + "\nTwo.\n"]
        verdicts = [loop.record(state, text, audit(
            text, "a%d" % n, [finding("The cache held")]))["verdict"]
            for n, text in enumerate(texts)]
        self.assertEqual(verdicts, ["CONTINUE", "CONTINUE", "STOP_RECURRING"])


class Reopen(unittest.TestCase):
    def clean_state(self):
        state = loop.new_state(SOURCE, max_rounds=1)
        loop.record(state, CLEAN, audit(CLEAN, "a1"))
        return state

    def test_a_clean_loop_takes_one_more_round_against_the_same_source(self):
        state = self.clean_state()
        loop.reopen(state)
        text = "The cache held rows in 2024. See `cache.py` and Redis for details.\n"
        round_ = loop.record(state, text, audit(text, "a2"))
        self.assertEqual(round_["round"], 2)
        self.assertEqual(round_["lost"], ["120"])

    def test_a_used_reader_is_still_refused_after_reopening(self):
        state = self.clean_state()
        loop.reopen(state)
        text = CLEAN + "\nMore.\n"
        with self.assertRaisesRegex(loop.LoopError, "auditor a1 already"):
            loop.record(state, text, audit(text, "a1"))

    def test_a_stopped_loop_cannot_be_reopened(self):
        state = loop.new_state(SOURCE, max_rounds=1)
        loop.record(state, CLEAN, audit(CLEAN, "a1", [finding("The cache")]))
        with self.assertRaisesRegex(loop.LoopError, "only a CLEAN loop"):
            loop.reopen(state)

    def test_a_running_loop_cannot_be_reopened(self):
        with self.assertRaisesRegex(loop.LoopError, "only a CLEAN loop"):
            loop.reopen(loop.new_state(SOURCE))


class Malformed(unittest.TestCase):
    def setUp(self):
        self.state = loop.new_state(SOURCE)

    def test_a_plain_string_accepted_loss_is_a_named_error(self):
        with self.assertRaisesRegex(loop.LoopError, "needs item and reason"):
            loop.record(self.state, CLEAN, audit(CLEAN, "a1", accepted_losses=["120"]))

    def test_a_plain_string_finding_is_a_named_error(self):
        with self.assertRaisesRegex(loop.LoopError, "finding"):
            loop.record(self.state, CLEAN, audit(CLEAN, "a1", ["The cache"]))


class OwnerKeep(unittest.TestCase):
    def test_record_can_take_an_owner_keep_list(self):
        text = SOURCE + "\nLet's dive in to the rest.\n"
        state = loop.new_state(SOURCE)
        keep = [{"rule": "staged-opener", "text": "Let's dive", "count": 1, "reason": "owner"}]
        round_ = loop.record(state, text, audit(text, "a1"), keep=keep)
        self.assertEqual(round_["verdict"], "CLEAN")
        self.assertEqual(state["keep"], keep)


class Cli(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-I", str(HERE / "clean_loop.py"), *args],
                              capture_output=True, text=True)

    def test_init_then_clean_record_exits_zero(self):
        with tempfile.TemporaryDirectory() as room:
            room = Path(room)
            (room / "draft.md").write_text(CLEAN, encoding="utf-8")
            (room / "audit.json").write_text(json.dumps(audit(CLEAN, "a1")), encoding="utf-8")
            state = str(room / "state.json")
            done = self.run_cli("init", "--state", state, "--text", str(room / "draft.md"))
            self.assertEqual(done.returncode, 0, done.stderr)
            done = self.run_cli("record", "--state", state, "--text",
                                str(room / "draft.md"), "--audit", str(room / "audit.json"))
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertIn("CLEAN", done.stdout)

    def test_continue_exits_one_and_a_bad_audit_exits_two(self):
        with tempfile.TemporaryDirectory() as room:
            room = Path(room)
            (room / "draft.md").write_text(CLEAN, encoding="utf-8")
            state = str(room / "state.json")
            self.run_cli("init", "--state", state, "--text", str(room / "draft.md"))
            (room / "bad.json").write_text("not json", encoding="utf-8")
            done = self.run_cli("record", "--state", state, "--text",
                                str(room / "draft.md"), "--audit", str(room / "bad.json"))
            self.assertEqual(done.returncode, 2)
            self.assertIn("audit", done.stderr)
            (room / "audit.json").write_text(
                json.dumps(audit(CLEAN, "a1", [finding("The cache")])), encoding="utf-8")
            done = self.run_cli("record", "--state", state, "--text",
                                str(room / "draft.md"), "--audit", str(room / "audit.json"))
            self.assertEqual(done.returncode, 1)
            self.assertIn("CONTINUE", done.stdout)

    def test_reopen_then_record_takes_another_round(self):
        with tempfile.TemporaryDirectory() as room:
            room = Path(room)
            (room / "draft.md").write_text(CLEAN, encoding="utf-8")
            (room / "a1.json").write_text(json.dumps(audit(CLEAN, "a1")), encoding="utf-8")
            (room / "a2.json").write_text(json.dumps(audit(CLEAN, "a2")), encoding="utf-8")
            state = str(room / "state.json")
            draft = str(room / "draft.md")
            self.run_cli("init", "--state", state, "--text", draft)
            self.run_cli("record", "--state", state, "--text", draft,
                         "--audit", str(room / "a1.json"))
            done = self.run_cli("record", "--state", state, "--text", draft,
                                "--audit", str(room / "a2.json"))
            self.assertEqual(done.returncode, 2)
            self.assertIn("already ended", done.stderr)
            done = self.run_cli("reopen", "--state", state)
            self.assertEqual(done.returncode, 0, done.stderr)
            done = self.run_cli("record", "--state", state, "--text", draft,
                                "--audit", str(room / "a2.json"))
            self.assertEqual(done.returncode, 0, done.stderr)

    def test_init_refuses_to_overwrite_a_running_loop(self):
        with tempfile.TemporaryDirectory() as room:
            room = Path(room)
            (room / "draft.md").write_text(CLEAN, encoding="utf-8")
            state = str(room / "state.json")
            self.run_cli("init", "--state", state, "--text", str(room / "draft.md"))
            done = self.run_cli("init", "--state", state, "--text", str(room / "draft.md"))
            self.assertEqual(done.returncode, 2)
            self.assertIn("already exists", done.stderr)


if __name__ == "__main__":
    unittest.main()
