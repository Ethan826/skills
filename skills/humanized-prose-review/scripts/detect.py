#!/usr/bin/env python3
"""Run an AI-text detector once over finished prose. Advisory only.

Backends: none; editlens and sloptotal (local); pangram and gptzero (hosted).
The core needs only the standard library. See references/detectors.md for
setup, licenses, and what a score can and cannot tell you.

Exit codes: 0 the detector ran, or none was asked for; 2 it could not run.
A score never fails the command: this is a report-only check, because a
detector's opinion is not a correctness rule. A refusal or an outage exits 2
and is never reported as a low score.

Blind spots: the adapters were tested against each vendor's documented
samples, so a changed API fails closed with "unexpected". Detectors disagree,
drift between versions, and have not been validated on technical prose.
"""
import argparse
import json
import math
import os
import re
import statistics
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tell_lint  # noqa: E402

MIN_WORDS = 80  # SlopTotal's stated floor; fiat for the other backends
MIN_SAMPLES = 5  # fiat: fewer files cannot give any spread at all
MAX_POLLS = 60
POLL_SECONDS = 2
SLOP_WORDS = 300
PASSAGE_MIN = 110  # scores shift with window size, so compare one length
PASSAGE_MAX = 180  # fiat: the test that showed the effect used this range
EDITLENS_TOKENS = 510  # the EditLens CLI says "must be <512" for RoBERTa
EDITLENS_CHECKPOINT = "pangram/editlens_roberta-large"
EDITLENS_BASE = "FacebookAI/roberta-large"
BOILERPLATE = ("Sure", "Here", "Abstract", "Title", "I'm happy to help", "Certainly")


class DetectError(Exception):
    """The detector did not produce a score."""


def http(method, url, headers, body):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(url, data=data, method=method, headers={
        "Content-Type": "application/json", "User-Agent": "tell-detect", **headers})
    try:
        with urllib.request.urlopen(request, timeout=120) as reply:
            return reply.status, json.loads(reply.read() or b"{}")
    except urllib.error.HTTPError as error:
        try:
            return error.code, json.loads(error.read() or b"{}")
        except ValueError:
            return error.code, {}
    except (urllib.error.URLError, OSError) as error:
        raise DetectError("cannot reach %s: %s" % (url, error))
    except ValueError:
        raise DetectError("unexpected non-JSON reply from %s" % url)


def prose(text):
    """Only the prose goes to a detector: no code, URLs or front matter."""
    masked = tell_lint.mask(text)
    masked = re.sub(r"[ \t]+", " ", masked)
    masked = re.sub(r" ?\n ?", "\n", masked)
    return re.sub(r"\n{3,}", "\n\n", masked).strip()


def split_oversized(paragraph, limit, count):
    pieces, current = [], []
    for word in paragraph.split():
        if current and count(" ".join(current + [word])) > limit:
            pieces.append(" ".join(current))
            current = []
        current.append(word)
    return pieces + ([" ".join(current)] if current else [])


def chunk(text, limit, count):
    """Pack paragraphs into windows under the limit, so nothing is truncated."""
    chunks, current = [], ""
    for paragraph in re.split(r"\n\s*\n", text):
        parts = [paragraph] if count(paragraph) <= limit else split_oversized(
            paragraph, limit, count)
        for part in parts:
            joined = current + "\n\n" + part if current else part
            if count(joined) <= limit:
                current = joined
            else:
                chunks.append(current)
                current = part
    return chunks + ([current] if current else [])


def word_count(text):
    return len(text.split())


def passages(text):
    """Cut text into passages of one comparable length, keeping every word.
    A remainder under the floor is scored but marked short, and never flagged."""
    pieces, current = [], []
    for paragraph in re.split(r"\n\s*\n", text):
        words = paragraph.split()
        while words:
            room = PASSAGE_MAX - len(current)
            current, words = current + words[:room], words[room:]
            if len(current) == PASSAGE_MAX:
                pieces.append(current)
                current = []
        if len(current) >= PASSAGE_MIN:
            pieces.append(current)
            current = []
    if current:
        pieces.append(current)
    return [{"text": " ".join(p), "words": len(p), "short": len(p) < PASSAGE_MIN}
            for p in pieces]


def weighted(windows):
    total = sum(w["words"] for w in windows)
    return sum(w["score"] * w["words"] for w in windows) / total if total else None


def pieces_of(text, by_passage, limit, count):
    if by_passage:
        return passages(text)
    return [{"text": c, "words": word_count(c), "short": False}
            for c in chunk(text, limit, count)]


def expect_object(name, body):
    if not isinstance(body, dict):
        raise DetectError("unexpected %s reply: not an object" % name)


def expect_ok(name, status, body):
    if status != 200:
        raise DetectError("%s returned %s: %s" % (name, status, str(body)[:200]))
    expect_object(name, body)


def require_key(env, name):
    if not env.get(name):
        raise DetectError("%s is not set" % name)
    return env[name]


def require_upload(opts, where):
    if not opts["allow_upload"]:
        raise DetectError("this would send the text to %s; get the user's approval, "
                          "then pass --allow-upload" % where)


def refuse_passages(opts):
    if opts.get("by_passage"):
        raise DetectError("--passages is for local backends: each passage would be a "
                          "separate paid upload")


def run_none(text, opts, env, transport):
    return {"model": None, "score": None, "label": None, "windows": []}


def run_pangram(text, opts, env, transport):
    base = "https://text.external-api.pangram.com"
    refuse_passages(opts)
    require_upload(opts, "Pangram")
    headers = {"x-api-key": require_key(env, "PANGRAM_API_KEY")}
    model = opts["model"] or "pangram-4"
    status, body = transport("POST", base + "/task", headers, {
        "text": text, "model": model, "public_dashboard_link": False})
    expect_ok("pangram", status, body)
    task = body.get("task_id")
    if not task:
        raise DetectError("unexpected pangram reply: no task_id")
    for _ in range(MAX_POLLS):
        status, body = transport("GET", "%s/task/%s" % (base, task), headers, None)
        expect_ok("pangram", status, body)
        if body.get("stage") == "STAGE_FAILED":
            raise DetectError("pangram failed: %s" % body.get("headline"))
        if body.get("stage") == "STAGE_SUCCESS":
            return read_pangram(body, model)
        if not str(body.get("stage")).startswith("STAGE_"):
            raise DetectError("unexpected pangram reply: stage %s" % body.get("stage"))
        time.sleep(POLL_SECONDS)
    raise DetectError("pangram timed out")


def read_pangram(body, model):
    try:
        windows = [{
            "text": w["text"].strip(), "start": w["start_index"], "end": w["end_index"],
            "score": w["ai_assistance_score"], "label": w["label"],
            "confidence": w.get("confidence"), "humanized": w.get("is_humanized"),
        } for w in body["windows"]]
        return {"model": model, "version": body.get("version"),
                "score": 1 - body["fraction_human"], "label": body["prediction_short"],
                "windows": windows}
    except (AttributeError, KeyError, TypeError):
        raise DetectError("unexpected pangram reply: fields missing")


def run_gptzero(text, opts, env, transport):
    refuse_passages(opts)
    require_upload(opts, "GPTZero")
    headers = {"x-api-key": require_key(env, "GPTZERO_API_KEY")}
    status, body = transport("POST", "https://api.gptzero.me/v2/predict/text",
                             headers, {"document": text})
    expect_ok("gptzero", status, body)
    try:
        document = body["documents"][0]
        return {"model": opts["model"] or "gptzero", "version": body.get("version"),
                "score": 1 - document["class_probabilities"]["human"],
                "label": document["predicted_class"], "windows": []}
    except (AttributeError, KeyError, IndexError, TypeError):
        raise DetectError("unexpected gptzero reply: fields missing")


def slop_score(base, text, transport):
    status, body = transport("POST", base + "/api/analyze", {}, {"text": text})
    expect_object("sloptotal", body)
    ticket = body.get("ticket_id")
    for _ in range(MAX_POLLS):
        if status != 202:
            break
        time.sleep(POLL_SECONDS)
        status, body = transport("GET", "%s/api/queue/ticket/%s" % (base, ticket), {}, None)
        expect_object("sloptotal", body)
    expect_ok("sloptotal", status, body)
    if "overall_score" not in body:
        raise DetectError("unexpected sloptotal reply: no overall_score")
    return body


def run_sloptotal(text, opts, env, transport):
    base = (opts["url"] or "http://localhost:8000").rstrip("/")
    if urlparse(base).hostname not in ("localhost", "127.0.0.1", "::1"):
        require_upload(opts, base)
    windows = []
    for piece in pieces_of(text, opts.get("by_passage"), SLOP_WORDS, word_count):
        body = slop_score(base, piece["text"], transport)
        windows.append(dict(piece, text=piece["text"][:80],
                            score=body["overall_score"] / 100,
                            label=body.get("overall_verdict")))
    return {"model": "sloptotal", "score": weighted(windows),
            "label": None, "windows": windows}


def bucket_score(probabilities):
    """The expected bucket, scaled so 0 is human and 1 is fully AI."""
    top = len(probabilities) - 1
    return sum(i * p for i, p in enumerate(probabilities)) / top


def strip_boilerplate(text):
    parts = re.split(r"\n\s*\n", text.strip(), maxsplit=1)
    if len(parts) == 2 and parts[0].startswith(BOILERPLATE):
        return parts[1]
    return text


def collapse(text):
    return " ".join(text.lower().split())


def editlens_normalize(text):
    return collapse(strip_boilerplate(text))


class EditLensModel:
    """Written from the EditLens README and script behavior, not copied from
    them: that code is CC BY-NC-SA and this skill is MIT. Scores may differ a
    little from Pangram's own script."""

    limit = EDITLENS_TOKENS

    def __init__(self, checkpoint, base_model):
        try:
            import emoji
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
        except ImportError as error:
            raise DetectError("editlens needs torch, transformers and emoji: %s" % error)
        self.emoji, self.torch = emoji, torch
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(base_model)
            self.model = AutoModelForSequenceClassification.from_pretrained(checkpoint)
        except OSError as error:
            raise DetectError("cannot load %s; accept its conditions on Hugging Face "
                              "and log in: %s" % (checkpoint, error))
        self.model.to(self.device).eval()

    def clean(self, text):
        return collapse(self.emoji.demojize(text))

    def count(self, text):
        return len(self.tokenizer(self.clean(text))["input_ids"])

    def predict(self, text):
        inputs = self.tokenizer(self.clean(text), return_tensors="pt").to(self.device)
        with self.torch.no_grad():
            logits = self.model(**inputs).logits
        return self.torch.softmax(logits.float(), dim=-1)[0].tolist()


def score_windows(model, text, by_passage=False):
    windows = []
    for piece in pieces_of(text, by_passage, model.limit, model.count):
        windows.append(dict(piece, text=piece["text"][:80],
                            score=bucket_score(model.predict(piece["text"]))))
    return {"score": weighted(windows), "label": None, "windows": windows}


def run_editlens(text, opts, env, transport):
    if not opts["noncommercial"]:
        raise DetectError("Open Pangram is CC BY-NC-SA 4.0; pass --noncommercial to "
                          "state that this run is non-commercial")
    checkpoint = opts["checkpoint"] or EDITLENS_CHECKPOINT
    if "llama" in checkpoint.lower():
        raise DetectError("this adapter is RoBERTa only: the Llama checkpoint needs a "
                          "custom head and 4-bit loading that were not verified here")
    model = EditLensModel(checkpoint, opts["base_model"] or EDITLENS_BASE)
    scored = score_windows(model, strip_boilerplate(text), opts.get("by_passage"))
    return dict(scored, model=checkpoint)


BACKENDS = {"none": run_none, "editlens": run_editlens, "sloptotal": run_sloptotal,
            "pangram": run_pangram, "gptzero": run_gptzero}


def interpret(result, baseline):
    if result["score"] is None:
        return "no detector ran"
    if baseline and (baseline["backend"], baseline["model"],
                     baseline.get("unit", "document")) != (
            result["backend"], result["model"], result["unit"]):
        raise DetectError("baseline is for %s %s by %s" % (
            baseline["backend"], baseline["model"], baseline.get("unit", "document")))
    if result["words"] < MIN_WORDS:
        return "too short to read: under %d words" % MIN_WORDS
    if not baseline:
        return "uncalibrated: do not act on this score; run calibrate first"
    if result["unit"] == "passage":
        full = [w for w in result["windows"] if not w["short"]]
        high = [w for w in full if w["score"] > baseline["human_p95"]]
        return ("%d of %d passages above your human range: have an auditor look at "
                "those; a low score clears nothing" % (len(high), len(full)))
    if not baseline["separates"]:
        return "this detector does not separate your writing from AI text; ignore it"
    if result["score"] > baseline["human_p95"]:
        return "above your human range: audit the highest windows once more"
    return "within your human range"


def run(backend, text, opts, env, transport):
    body = prose(text)
    result = BACKENDS[backend](body, opts, env, transport)
    result.update(backend=backend, advisory=True, words=word_count(body),
                  unit="passage" if opts.get("by_passage") else "document")
    result["interpretation"] = interpret(result, opts.get("baseline"))
    return result


def nearest_rank(values, fraction):
    ordered = sorted(values)
    return ordered[max(math.ceil(fraction * len(ordered)) - 1, 0)]


def summarize(backend, model, human, ai, unit="document"):
    if min(len(human), len(ai)) < MIN_SAMPLES:
        raise DetectError("calibrate needs at least %d long samples of each kind" % MIN_SAMPLES)
    p95, median = nearest_rank(human, 0.95), statistics.median(ai)
    return {"backend": backend, "model": model, "unit": unit, "human_p95": p95,
            "ai_median": median, "human_samples": len(human), "ai_samples": len(ai),
            "separates": p95 < median}


def score_folder(folder, backend, opts):
    scores, model = [], None
    paths = sorted(p for p in Path(folder).iterdir() if p.suffix in (".md", ".txt"))
    for path in paths:
        text = tell_lint.read_text(path)
        if word_count(prose(text)) < MIN_WORDS:
            print("skipped, too short: %s" % path, file=sys.stderr)
            continue
        result = run(backend, text, opts, os.environ, http)
        model = result["model"]
        if opts["by_passage"]:
            scores.extend(w["score"] for w in result["windows"] if not w["short"])
        else:
            scores.append(result["score"])
    return scores, model


def render(result):
    if result["score"] is None:
        return "detector: %s" % result["interpretation"]
    lines = ["%s %s: score %.2f (%s)" % (result["backend"], result["model"], result["score"],
                                        result.get("label") or "no label"),
             "advisory: %s" % result["interpretation"]]
    ranked = sorted(result["windows"], key=lambda w: -w["score"])[:5]
    lines += ["  %.2f %s%s" % (w["score"], "(short, not counted) " if w.get("short") else "",
                               w["text"][:80].replace("\n", " ")) for w in ranked]
    return "\n".join(lines)


def add_backend_options(parser):
    parser.add_argument("--backend", choices=sorted(BACKENDS), required=True)
    parser.add_argument("--allow-upload", action="store_true",
                        help="the user approved sending this text to the service")
    parser.add_argument("--noncommercial", action="store_true",
                        help="this run is non-commercial, as Open Pangram's license requires")
    parser.add_argument("--url", help="SlopTotal address, default http://localhost:8000")
    parser.add_argument("--model", help="vendor model selector")
    parser.add_argument("--checkpoint", help="EditLens checkpoint")
    parser.add_argument("--base-model", help="EditLens tokenizer source")
    parser.add_argument("--passages", action="store_true",
                        help="score fixed-length passages, for local backends")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    score = commands.add_parser("score", help="score one file")
    score.add_argument("path")
    score.add_argument("--baseline", help="file written by calibrate")
    score.add_argument("--json", action="store_true")
    add_backend_options(score)
    calibrate = commands.add_parser("calibrate", help="measure a detector on known text")
    calibrate.add_argument("--human", required=True, help="folder of writing from before 2023")
    calibrate.add_argument("--ai", required=True, help="folder of raw model output")
    calibrate.add_argument("--out", required=True)
    add_backend_options(calibrate)
    args = parser.parse_args(argv)
    opts = {"allow_upload": args.allow_upload, "noncommercial": args.noncommercial,
            "url": args.url, "model": args.model, "checkpoint": args.checkpoint,
            "base_model": args.base_model, "baseline": None, "by_passage": args.passages}
    try:
        if args.command == "calibrate":
            human, model = score_folder(args.human, args.backend, opts)
            ai, _ = score_folder(args.ai, args.backend, opts)
            base = summarize(args.backend, model, human, ai,
                             "passage" if args.passages else "document")
            Path(args.out).write_text(json.dumps(base, indent=2), encoding="utf-8")
            print(json.dumps(base))
            return 0
        if args.baseline:
            opts["baseline"] = json.loads(tell_lint.read_text(args.baseline))
        result = run(args.backend, tell_lint.read_text(args.path), opts, os.environ, http)
    except (DetectError, tell_lint.LintError, ValueError, OSError) as error:
        print("detect: %s" % error, file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2) if args.json else render(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
