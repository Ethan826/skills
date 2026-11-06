# Detectors

You can run a detector once on finished text, or skip it. The loop works the
same either way. There are three modes:

| Mode | Backend | Text leaves the machine | Cost and terms | Locates the problem |
|---|---|---|---|---|
| None | `none` | No | Free | The lint and auditor do this |
| Open source | `editlens` | No | Non-commercial only | Per window of about 500 tokens |
| Open source | `sloptotal` | No | MIT code; check weight licenses | Per window of about 300 words |
| Closed source | `pangram` | **Yes** | $0.05 per 100 words | Per scored window |
| Closed source | `gptzero` | **Yes** | See GPTZero's site | Whole document only in this adapter |

Originality.ai has no adapter yet.

## How to use a score

```bash
python3 scripts/detect.py score DRAFT.md --backend none
```

- Run it once, after `CLEAN`.
- Never rewrite to lower a number. A detector scores statistics, and text
  can be pushed down its scale while getting worse. WriteHuman reports moving
  GPTZero from 73.7 percent to 4.0 percent, without saying whether the
  prose improved.
- A high window is a reason to look again. Give those passages to one new
  auditor as an extra round. If the auditor finds nothing, stop.
- Do not use a score to judge who wrote something. Error rates are not
  zero, and Open Pangram's terms forbid enforcing an AI policy with it. Its
  reported false positive rate on non-native English is 5.5 to 9.9 percent.
- An uncalibrated score means nothing. The script labels it
  uncalibrated, so report it that way.

The script always exits 0 when the detector ran, whatever the score. It exits
2 when it could not run.

## Calibrate first

No backend has been validated on READMEs, PR descriptions or commit messages,
and thresholds differ by detector. Measure one on your own writing:

```bash
python3 scripts/detect.py calibrate --backend sloptotal \
  --human HUMAN_DIR --ai AI_DIR --out BASELINE.json
python3 scripts/detect.py score DRAFT.md --backend sloptotal --baseline BASELINE.json
```

`HUMAN_DIR` holds at least five `.md` or `.txt` files you wrote before 2023,
and `AI_DIR` at least five samples of raw model output of the same kind. Each
needs 80 words or more. The baseline records the 95th percentile of your human
scores and the median AI score. If the 95th percentile is not below the median,
document scoring reports that the detector does not separate your writing, and
you should ignore it. Passage scoring does not warn. Calibrating
with a closed backend uploads every sample, and costs money.

## Scoring passages

Scores shift a lot with window size: one section of copy scored 0.53 alone and
0.21 inside a larger window. So a local backend can score fixed passages of 110
to 180 words instead, with a baseline made the same way:

```bash
~/.venvs/editlens/bin/python scripts/detect.py calibrate --backend editlens --noncommercial --passages \
  --human HUMAN_DIR --ai AI_DIR --out PASSAGES.json
~/.venvs/editlens/bin/python scripts/detect.py score DRAFT.md --backend editlens --noncommercial \
  --passages --baseline PASSAGES.json
```

The result counts the passages above your human range, and `--json` gives every
passage. An auditor can start there. That line is the 95th percentile of
human scores, so about one human passage in twenty lands above it, and a passage
under it may still be AI-written. Hosted backends refuse this
mode, because each passage would be a separate paid upload.

## Open source: EditLens (Open Pangram)

Pangram released this from its ICLR 2026 EditLens work. It scores from 0 to 1
how much of a text looks AI-edited.

The license is CC BY-NC-SA 4.0. Pangram's post adds that it must not be
used commercially or to enforce an AI usage policy in education or at work.
Pass `--noncommercial` to state that a run qualifies. This skill includes none
of its code or weights, and must stay that way to remain MIT.

To set it up, accept the conditions at
[pangram/editlens_roberta-large](https://huggingface.co/pangram/editlens_roberta-large),
create a Hugging Face token, and install into a virtual environment:

```bash
python3 -m venv ~/.venvs/editlens
~/.venvs/editlens/bin/pip install torch transformers emoji
HF_TOKEN=... ~/.venvs/editlens/bin/python scripts/detect.py score DRAFT.md \
  --backend editlens --noncommercial
```

Its training text comes from GPT-4.1, Claude Sonnet 4 and Gemini 2.5 Flash, and
covers news, creative writing, product reviews and education content. Pangram reports 0.695 ternary
accuracy on held-out emails and 0.736 macro F1 on RAID for this RoBERTa model,
against 0.905 and 0.992 for its production
model.

The Llama model scores better by Pangram's numbers (0.863 and 0.930), but the
adapter refuses it. It needs a custom classification head and 4-bit loading
that may not work on a Mac, and neither has been verified.

## Open source: SlopTotal

SlopTotal's MIT ensemble of 23 engines does not include Pangram's model. It reports 0.942 AUC on its own benchmark, catches humanized text about
half the time, and is weak under about 80 words.

Start it with `docker run -p 8000:8000 ghcr.io/pablocaeg/sloptotal`, or from
source on Python 3.10 or later. It needs about 9 GB of models and 8 GB of
memory. Then run `python3 scripts/detect.py score DRAFT.md --backend sloptotal`.
The default address is `http://localhost:8000`. A `--url` on another host
counts as an upload.

The code is MIT, but its third-party list leaves out the model weights, and the
Docker image includes GPL-3.0 trafilatura. Check each model's license before
commercial use.

## Closed source: Pangram and GPTZero

Sending text to these services discloses it to a third party. Get the user's
approval for each document, and pass `--allow-upload` only after that. Never
send confidential or client text, or unpublished work the user has not cleared.

```bash
PANGRAM_API_KEY=... python3 scripts/detect.py score DRAFT.md \
  --backend pangram --allow-upload
GPTZERO_API_KEY=... python3 scripts/detect.py score DRAFT.md \
  --backend gptzero --allow-upload
```

Pangram scores each window, gives its offsets in the text, and marks windows it
reads as humanized. The adapter sends `pangram-4` unless `--model` says otherwise.
Pangram's privacy page says content is stored while the account is active and
is not used for training, but that page covers only the dashboard and extension.

GPTZero's score here is one minus its human probability. The API also returns
paragraph and sentence results, but those field names are unconfirmed, so the adapter
reports the document only. The documentation pages do not state retention terms, so read
GPTZero's privacy policy before uploading.

If a vendor changes its reply, the script exits 2 with "unexpected".

## What has been run

As of November 2026:

| Backend | Tested with | Never run against |
|---|---|---|
| `none` | The real script | Nothing needed |
| `editlens` | The real RoBERTa weights, and one calibration | Nothing, but see the result below |
| `sloptotal` | A real local server, and one calibration | Nothing, but see the result below |
| `pangram` | Samples from its docs | The live API |
| `gptzero` | Samples from its docs | The live API |

Treat a backend as unproven until it has run for real, and update this table
when it does.

The first EditLens calibration failed. On ten of one author's blog posts from 2019
and 2020 and nine Claude agent reports, the RoBERTa model gave a human 95th
percentile of 0.21 and an AI median of 0.15, with only two of the nine reports
above the human range. This is one small test, and the posts and reports differ in
genre. On this evidence, the model should not be trusted on this author's
technical prose. A paragraph of generic marketing copy scored
1.00, so the model is not broken. Why it failed here is untested: the reports
also followed project style rules and came from newer models than its training
data. None of this tests Pangram's paid model.

SlopTotal did little better on the same samples. It scored all 19 files between
0.12 and 0.22, far below its own 0.45 flag. The human 95th percentile was 0.19
and the AI median 0.18, with three of the nine reports above the human range.
AI reports did tend to score higher (AUC 0.77 on 19 files), but the band is too
narrow to set a threshold. It took about 23 minutes on CPU for 19 files.

EditLens gave a few high scores on short passages. Among passages of 110 to 180 words,
one of 61 from the author's posts reached 0.45, against none of 16 from the AI
reports. Two of three sections of marketing copy of that length also
reached it, though the same copy scored 0.21 in larger windows, and no human
marketing copy was tested. A high score on a short passage may be worth an
auditor's attention. None of the 16 AI passages reached 0.45, so a low score
does not clear a passage.

A passage baseline from the same files (67 human and 40 AI passages) put the
human 95th percentile at 0.31 and the AI median at 0.15.

## Tests

Run these from the skill folder. The ML packages are not needed.

```bash
python3 -m unittest discover -s scripts
```
