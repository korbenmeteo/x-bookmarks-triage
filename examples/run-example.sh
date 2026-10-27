#!/usr/bin/env bash
# Runs the whole pipeline on the synthetic sample in a temporary vault.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
HERE="$(cd "$(dirname "$0")" && pwd)"
S="$HERE/../skills/x-bookmarks-triage/scripts"
V="$(mktemp -d)"
cp "$HERE/../skills/x-bookmarks-triage/config.example.json" "$V/x-bookmarks.config.json"
cd "$V"
python3 "$S/ingest.py" "$HERE/export.sample.json" --config x-bookmarks.config.json
python3 "$S/ingest.py" "$HERE/export.sample.json" --config x-bookmarks.config.json   # second run: 0 new
python3 "$S/route.py" "$HERE/triage.sample.jsonl" --config x-bookmarks.config.json --date 2026-10-27 --dry-run
python3 "$S/route.py" "$HERE/triage.sample.jsonl" --config x-bookmarks.config.json --date 2026-10-27
python3 "$S/route.py" "$HERE/triage.sample.jsonl" --config x-bookmarks.config.json --date 2026-10-27   # idempotent: 0 added
python3 "$S/stats.py" "$HERE/triage.sample.jsonl" --config x-bookmarks.config.json
python3 "$S/condense.py" "$HERE/export.sample.json" "$V/raw/x-bookmarks/_triage/sample" --chunk 2
echo "--- wiki/Post ideas.md"; cat "$V/wiki/Post ideas.md"
echo "--- processed raw files:"; grep -l "status: processed" "$V"/raw/x-bookmarks/*.md | wc -l
# Checks: every raw file processed, and three route runs left a single entry.
test "$(grep -l "status: processed" "$V"/raw/x-bookmarks/*.md | wc -l)" -eq 4
test "$(grep -c "status/1000000000000000004" "$V/wiki/Post ideas.md")" -eq 1
echo "Vault left in $V"
