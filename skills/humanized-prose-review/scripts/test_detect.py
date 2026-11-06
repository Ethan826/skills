"""Tests for detect.py. A fake transport replays each vendor's documented
samples, so these prove the adapters match the docs, not that a live API
still does. The adapters need a real run with a key before they are trusted.
"""
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import detect  # noqa: E402

detect.POLL_SECONDS = 0
LONG = " ".join(["word"] * 120)

PANGRAM_DONE = {
    "stage": "STAGE_SUCCESS", "text": "AI-assisted passage. Human passage.",
    "version": "4.0", "headline": "AI Assisted", "prediction_short": "Mixed",
    "fraction_ai": 0.0, "fraction_ai_assisted": 0.6, "fraction_human": 0.4,
    "windows": [{"text": "AI-assisted passage. ", "label": "AI-Assisted",
                 "ai_assistance_score": 0.55, "confidence": "High",
                 "start_index": 0, "end_index": 21, "word_count": 2,
                 "token_length": 5, "is_humanized": True, "humanizer_score": 0.91}],
}
GPTZERO_DONE = {
    "documents": [{"predicted_class": "mixed",
                   "class_probabilities": {"human": 0.1, "ai": 0.2, "mixed": 0.7},
                   "confidence_category": "high", "result_message": "text"}],
    "version": "2026-10-07-base",
}


class FakeTransport:
    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls = []

    def __call__(self, method, url, headers, body):
        self.calls.append({"method": method, "url": url, "headers": headers, "body": body})
        return self.replies.pop(0)


def options(**extra):
    base = {"allow_upload": True, "noncommercial": False, "url": None,
            "model": None, "checkpoint": None, "base_model": None,
            "by_passage": False}
    base.update(extra)
    return base


ENV = {"PANGRAM_API_KEY": "secret-p", "GPTZERO_API_KEY": "secret-g"}


class None_(unittest.TestCase):
    def test_none_reports_that_no_detector_ran(self):
        result = detect.run("none", LONG, options(), ENV, None)
        self.assertIsNone(result["score"])
        self.assertEqual(result["interpretation"], "no detector ran")


class Prose(unittest.TestCase):
    def test_code_blocks_are_not_sent(self):
        text = "The body of it.\n\n```\nsecret code\n```\n\nThe end of it."
        self.assertNotIn("secret code", detect.prose(text))

    def test_chunks_respect_the_limit_and_keep_every_word(self):
        text = "\n\n".join(" ".join("w%d" % i for i in range(n, n + 30))
                           for n in range(0, 300, 30))
        chunks = detect.chunk(text, 70, lambda s: len(s.split()))
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(c.split()) <= 70 for c in chunks))
        self.assertEqual(" ".join(chunks).split(), text.split())

    def test_a_paragraph_over_the_limit_is_split(self):
        text = " ".join(["word"] * 50)
        chunks = detect.chunk(text, 20, lambda s: len(s.split()))
        self.assertTrue(all(len(c.split()) <= 20 for c in chunks))
        self.assertEqual(sum(len(c.split()) for c in chunks), 50)


class Upload(unittest.TestCase):
    def test_closed_backend_refuses_without_consent(self):
        for backend in ("pangram", "gptzero"):
            with self.subTest(backend=backend):
                fake = FakeTransport()
                with self.assertRaisesRegex(detect.DetectError, "--allow-upload"):
                    detect.run(backend, LONG, options(allow_upload=False), ENV, fake)
                self.assertEqual(fake.calls, [])

    def test_closed_backend_needs_its_key(self):
        with self.assertRaisesRegex(detect.DetectError, "PANGRAM_API_KEY"):
            detect.run("pangram", LONG, options(), {}, FakeTransport())

    def test_remote_sloptotal_counts_as_an_upload(self):
        fake = FakeTransport()
        with self.assertRaisesRegex(detect.DetectError, "--allow-upload"):
            detect.run("sloptotal", LONG, options(
                allow_upload=False, url="https://slop.example"), ENV, fake)
        self.assertEqual(fake.calls, [])

    def test_a_lookalike_host_is_not_local(self):
        with self.assertRaisesRegex(detect.DetectError, "--allow-upload"):
            detect.run("sloptotal", LONG, options(
                allow_upload=False, url="http://localhost.example:8000"), ENV,
                FakeTransport())


class Pangram(unittest.TestCase):
    def client(self, *replies):
        return FakeTransport((200, {"task_id": "t1"}), *replies)

    def test_request_matches_the_documented_shape(self):
        fake = self.client((200, PANGRAM_DONE))
        detect.run("pangram", LONG, options(), ENV, fake)
        first = fake.calls[0]
        self.assertEqual(first["method"], "POST")
        self.assertEqual(first["url"], "https://text.external-api.pangram.com/task")
        self.assertEqual(first["headers"]["x-api-key"], "secret-p")
        self.assertEqual(first["body"], {"text": LONG, "model": "pangram-4",
                                         "public_dashboard_link": False})
        self.assertEqual(fake.calls[1]["url"],
                         "https://text.external-api.pangram.com/task/t1")

    def test_result_reads_score_and_windows(self):
        result = detect.run("pangram", LONG, options(), ENV,
                            self.client((200, PANGRAM_DONE)))
        self.assertAlmostEqual(result["score"], 0.6)
        self.assertEqual(result["label"], "Mixed")
        self.assertEqual(result["windows"][0]["score"], 0.55)
        self.assertEqual(result["windows"][0]["text"], "AI-assisted passage.")

    def test_polls_until_done(self):
        fake = self.client((200, {"task_id": "t1", "stage": "STAGE_PREPROCESSING"}),
                           (200, PANGRAM_DONE))
        detect.run("pangram", LONG, options(), ENV, fake)
        self.assertEqual(len(fake.calls), 3)

    def test_failed_stage_is_an_error(self):
        fake = self.client((200, {"stage": "STAGE_FAILED", "headline": "no valid text"}))
        with self.assertRaisesRegex(detect.DetectError, "no valid text"):
            detect.run("pangram", LONG, options(), ENV, fake)

    def test_polling_gives_up(self):
        waiting = (200, {"stage": "STAGE_PREPROCESSING"})
        fake = self.client(*[waiting] * detect.MAX_POLLS)
        with self.assertRaisesRegex(detect.DetectError, "timed out"):
            detect.run("pangram", LONG, options(), ENV, fake)

    def test_http_error_names_the_status_and_hides_the_key(self):
        fake = FakeTransport((402, {"detail": "no credits"}))
        with self.assertRaises(detect.DetectError) as caught:
            detect.run("pangram", LONG, options(), ENV, fake)
        self.assertIn("402", str(caught.exception))
        self.assertNotIn("secret-p", str(caught.exception))

    def test_response_without_scores_fails_closed(self):
        with self.assertRaisesRegex(detect.DetectError, "unexpected"):
            detect.run("pangram", LONG, options(), ENV,
                       self.client((200, {"stage": "STAGE_SUCCESS"})))


class GptZero(unittest.TestCase):
    def test_request_and_result(self):
        fake = FakeTransport((200, GPTZERO_DONE))
        result = detect.run("gptzero", LONG, options(), ENV, fake)
        self.assertEqual(fake.calls[0]["url"], "https://api.gptzero.me/v2/predict/text")
        self.assertEqual(fake.calls[0]["headers"]["x-api-key"], "secret-g")
        self.assertEqual(fake.calls[0]["body"], {"document": LONG})
        self.assertAlmostEqual(result["score"], 0.9)
        self.assertEqual(result["label"], "mixed")

    def test_unexpected_shape_fails_closed(self):
        with self.assertRaisesRegex(detect.DetectError, "unexpected"):
            detect.run("gptzero", LONG, options(), ENV, FakeTransport((200, {"documents": []})))


class SlopTotal(unittest.TestCase):
    def test_scores_each_chunk_and_scales_to_one(self):
        text = LONG + "\n\n" + LONG + "\n\n" + LONG
        reply = (200, {"overall_score": 40, "overall_verdict": "Mixed", "engine_results": []})
        fake = FakeTransport(reply, reply)
        result = detect.run("sloptotal", text, options(), ENV, fake)
        self.assertEqual(fake.calls[0]["url"], "http://localhost:8000/api/analyze")
        self.assertEqual(len(result["windows"]), 2)
        self.assertAlmostEqual(result["score"], 0.4)

    def test_waits_on_a_queue_ticket(self):
        fake = FakeTransport((202, {"ticket_id": "q1"}), (202, {"ticket_id": "q1"}),
                             (200, {"overall_score": 10, "overall_verdict": "Human"}))
        result = detect.run("sloptotal", LONG, options(), ENV, fake)
        self.assertEqual(fake.calls[1]["url"], "http://localhost:8000/api/queue/ticket/q1")
        self.assertAlmostEqual(result["score"], 0.1)

    def test_unreachable_server_is_an_error(self):
        def refuse(method, url, headers, body):
            raise detect.DetectError("cannot reach %s" % url)
        with self.assertRaisesRegex(detect.DetectError, "cannot reach"):
            detect.run("sloptotal", LONG, options(), ENV, refuse)


class RealTransport(unittest.TestCase):
    """The urllib transport, against a real local server."""

    def serve(self, status, reply):
        seen = {}

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers["Content-Length"])
                seen["body"] = json.loads(self.rfile.read(length))
                seen["path"] = self.path
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(reply).encode())

            def log_message(self, *args):
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        return "http://127.0.0.1:%d" % server.server_port, seen

    def test_posts_json_and_reads_the_reply(self):
        url, seen = self.serve(200, {"overall_score": 25, "overall_verdict": "Human"})
        result = detect.run("sloptotal", LONG, options(url=url), ENV, detect.http)
        self.assertEqual(seen["path"], "/api/analyze")
        self.assertEqual(seen["body"], {"text": LONG})
        self.assertAlmostEqual(result["score"], 0.25)

    def test_http_error_status_reaches_the_adapter(self):
        url, _ = self.serve(429, {"retry_after": 5})
        with self.assertRaisesRegex(detect.DetectError, "429"):
            detect.run("sloptotal", LONG, options(url=url), ENV, detect.http)

    def test_refused_connection_is_named(self):
        with self.assertRaisesRegex(detect.DetectError, "cannot reach"):
            detect.run("sloptotal", LONG, options(url="http://127.0.0.1:9"), ENV, detect.http)


class EditLens(unittest.TestCase):
    class Fake:
        name = "fake"
        limit = 50

        def count(self, text):
            return len(text.split())

        def predict(self, text):
            return [0.0, 1.0, 3.0]

    def test_refuses_without_the_noncommercial_statement(self):
        with self.assertRaisesRegex(detect.DetectError, "--noncommercial"):
            detect.run("editlens", LONG, options(noncommercial=False), ENV, None)

    def test_score_is_the_expected_bucket_over_the_top_bucket(self):
        self.assertAlmostEqual(detect.bucket_score([1.0, 0.0]), 0.0)
        self.assertAlmostEqual(detect.bucket_score([0.0, 1.0]), 1.0)
        self.assertAlmostEqual(detect.bucket_score([0.0, 1.0, 0.0]), 0.5)

    def test_normalize_lowers_and_collapses(self):
        self.assertEqual(detect.editlens_normalize("Some  TEXT\n\nhere"), "some text here")

    def test_normalize_drops_a_leading_boilerplate_paragraph(self):
        self.assertEqual(detect.editlens_normalize("Sure, here it is.\n\nThe body."),
                         "the body.")

    def test_long_text_is_scored_in_windows_and_weighted_by_words(self):
        class Scorer(self.Fake):
            def predict(self, text):
                return [1.0, 0.0] if text.startswith("a") else [0.0, 1.0]
        text = " ".join(["a"] * 50) + "\n\n" + " ".join(["b"] * 150)
        result = detect.score_windows(Scorer(), text)
        self.assertGreaterEqual(len(result["windows"]), 2)
        self.assertAlmostEqual(result["score"], 0.75)

    def test_llama_is_refused_with_the_reason(self):
        with self.assertRaisesRegex(detect.DetectError, "RoBERTa only"):
            detect.run("editlens", LONG, options(
                noncommercial=True, checkpoint="pangram/editlens_Llama-3.2-3B"), ENV, None)


class Interpret(unittest.TestCase):
    BASE = {"backend": "pangram", "model": "pangram-4", "human_p95": 0.3,
            "ai_median": 0.8, "separates": True}

    def result(self, score, words=200):
        return {"backend": "pangram", "model": "pangram-4", "score": score, "words": words,
                "unit": "document", "windows": []}

    def test_without_a_baseline_a_score_is_uncalibrated(self):
        self.assertIn("uncalibrated", detect.interpret(self.result(0.9), None))

    def test_score_above_the_human_range_is_a_prompt_to_look(self):
        self.assertIn("above", detect.interpret(self.result(0.5), self.BASE))

    def test_score_inside_the_human_range(self):
        self.assertIn("within", detect.interpret(self.result(0.2), self.BASE))

    def test_short_text_is_not_read(self):
        self.assertIn("too short", detect.interpret(self.result(0.9, words=30), self.BASE))

    def test_a_baseline_that_does_not_separate_says_ignore(self):
        base = dict(self.BASE, separates=False)
        self.assertIn("does not separate", detect.interpret(self.result(0.9), base))

    def test_a_baseline_from_another_detector_is_an_error(self):
        with self.assertRaisesRegex(detect.DetectError, "baseline is for"):
            detect.interpret(self.result(0.9), dict(self.BASE, model="other"))


class Calibrate(unittest.TestCase):
    def test_summary_uses_the_human_upper_range_and_ai_median(self):
        base = detect.summarize("gptzero", "m", [0.1] * 19 + [0.2], [0.7, 0.8, 0.9, 0.9, 0.9])
        self.assertEqual(base["human_p95"], 0.1)
        self.assertEqual(base["ai_median"], 0.9)
        self.assertTrue(base["separates"])

    def test_overlap_is_recorded_as_not_separating(self):
        base = detect.summarize("gptzero", "m", [0.8] * 5, [0.3] * 5)
        self.assertFalse(base["separates"])

    def test_too_few_samples_is_an_error(self):
        with self.assertRaisesRegex(detect.DetectError, "at least 5"):
            detect.summarize("gptzero", "m", [0.1], [0.9] * 5)


class Passages(unittest.TestCase):
    def words(self, n, tag="w"):
        return " ".join("%s%d" % (tag, i) for i in range(n))

    def test_short_paragraphs_join_until_the_floor(self):
        text = "\n\n".join(self.words(60, t) for t in "abcd")
        pieces = detect.passages(text)
        self.assertEqual([p["words"] for p in pieces], [120, 120])

    def test_a_long_paragraph_is_split_under_the_ceiling(self):
        pieces = detect.passages(self.words(400))
        self.assertTrue(all(p["words"] <= detect.PASSAGE_MAX for p in pieces))

    def test_no_word_is_lost(self):
        text = self.words(70, "a") + "\n\n" + self.words(300, "b") + "\n\n" + self.words(30, "c")
        joined = " ".join(p["text"] for p in detect.passages(text))
        self.assertEqual(joined.split(), text.split())

    def test_a_tail_under_the_floor_is_marked_short(self):
        pieces = detect.passages(self.words(120) + "\n\n" + self.words(20, "z"))
        self.assertEqual([(p["words"], p["short"]) for p in pieces],
                         [(120, False), (20, True)])


class PassageMode(unittest.TestCase):
    class Fake:
        limit = 500

        def count(self, text):
            return len(text.split())

        def predict(self, text):
            return [0.0, 1.0] if text.startswith("hot") else [1.0, 0.0]

    BASE = {"backend": "editlens", "model": "m", "unit": "passage",
            "human_p95": 0.3, "ai_median": 0.2, "separates": False}

    def result(self, scores, unit="passage", words=300):
        return {"backend": "editlens", "model": "m", "unit": unit, "words": words,
                "score": 0.5, "windows": [
                    {"text": "t", "words": 120, "short": False, "score": s} for s in scores]}

    def test_score_windows_uses_passages_when_asked(self):
        text = " ".join(["hot"] * 120) + "\n\n" + " ".join(["cold"] * 120)
        result = detect.score_windows(self.Fake(), text, by_passage=True)
        self.assertEqual([w["score"] for w in result["windows"]], [1.0, 0.0])

    def test_flags_passages_above_the_human_range_even_if_files_overlap(self):
        message = detect.interpret(self.result([0.5, 0.1]), self.BASE)
        self.assertIn("1 of 2 passages", message)
        self.assertIn("clears nothing", message)

    def test_no_flag_still_clears_nothing(self):
        message = detect.interpret(self.result([0.1, 0.1]), self.BASE)
        self.assertIn("0 of 2 passages", message)
        self.assertIn("clears nothing", message)

    def test_a_short_passage_is_never_flagged(self):
        result = self.result([0.9])
        result["windows"][0]["short"] = True
        self.assertIn("0 of 0 passages", detect.interpret(result, self.BASE))

    def test_units_must_match(self):
        with self.assertRaisesRegex(detect.DetectError, "baseline is for"):
            detect.interpret(self.result([0.5], unit="document"), self.BASE)

    def test_a_document_baseline_without_a_unit_is_a_document_baseline(self):
        base = {"backend": "editlens", "model": "m", "human_p95": 0.3,
                "ai_median": 0.8, "separates": True}
        self.assertIn("within", detect.interpret(
            dict(self.result([0.1], unit="document"), score=0.2), base))

    def test_hosted_backends_refuse_passage_mode(self):
        fake = FakeTransport()
        with self.assertRaisesRegex(detect.DetectError, "local backends"):
            detect.run("pangram", LONG, options(by_passage=True), ENV, fake)
        self.assertEqual(fake.calls, [])

    def test_sloptotal_scores_each_passage(self):
        text = LONG + "\n\n" + LONG
        reply = (200, {"overall_score": 40, "overall_verdict": "x"})
        fake = FakeTransport(reply, reply)
        result = detect.run("sloptotal", text, options(by_passage=True), ENV, fake)
        self.assertEqual(result["unit"], "passage")
        self.assertEqual(len(fake.calls), 2)

    def test_render_marks_a_short_passage(self):
        result = dict(self.result([0.9]), label=None, interpretation="x")
        result["windows"][0]["short"] = True
        self.assertIn("(short, not counted)", detect.render(result))

    def test_summary_records_the_unit(self):
        base = detect.summarize("editlens", "m", [0.1] * 5, [0.9] * 5, unit="passage")
        self.assertEqual(base["unit"], "passage")


class Cli(unittest.TestCase):
    def run_cli(self, *args, env=None):
        clean = {k: v for k, v in os.environ.items() if not k.endswith("_API_KEY")}
        return subprocess.run([sys.executable, "-I", str(HERE / "detect.py"), *args],
                              capture_output=True, text=True, env={**clean, **(env or {})})

    def test_none_exits_zero(self):
        with tempfile.NamedTemporaryFile("w", suffix=".md") as handle:
            handle.write(LONG)
            handle.flush()
            done = self.run_cli("score", handle.name, "--backend", "none", "--json")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(json.loads(done.stdout)["backend"], "none")

    def test_refusal_exits_two_and_is_never_a_clean_result(self):
        with tempfile.NamedTemporaryFile("w", suffix=".md") as handle:
            handle.write(LONG)
            handle.flush()
            done = self.run_cli("score", handle.name, "--backend", "pangram")
        self.assertEqual(done.returncode, 2)
        self.assertIn("--allow-upload", done.stderr)

    def test_missing_ml_packages_are_named(self):
        with tempfile.NamedTemporaryFile("w", suffix=".md") as handle:
            handle.write(LONG)
            handle.flush()
            done = self.run_cli("score", handle.name, "--backend", "editlens",
                                "--noncommercial")
        self.assertEqual(done.returncode, 2)
        self.assertRegex(done.stderr, "torch|transformers|emoji")


if __name__ == "__main__":
    unittest.main()
