Fixtures for test_drift_issue.py.

- `drift.json`: four items trimmed from the live `detect_drift.py` run of
  2026-11-14 (before installed/humanizer was re-anchored), one per kind
  shape: fork, tool, vendored with a release line, and anchor-missing with
  a null `to`.
- `gh-issues-open.jsonl`: what `GhClient.find_open` reads, one JSON object
  per line as `gh api --paginate --jq '.[]'` prints it. The fields and
  their shapes (a pull request has a `pull_request` object; an issue
  has none) were recorded from the GitHub REST issues list on 2026-11-14;
  the values are synthetic.
- `gh-labels.txt`: label names, one per line, as `--jq '.[].name'` prints
  them.
