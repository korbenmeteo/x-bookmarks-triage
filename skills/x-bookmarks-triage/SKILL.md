---
name: x-bookmarks-triage
description: Turn a pile of X (Twitter) bookmarks into a curated knowledge base. Collects bookmarks from the user's own browser, ingests them into a markdown vault (Obsidian-friendly), triages each one critically against the user's projects, routes the keepers to the right pages and writes a weekly digest. Use when the user wants to make sense of their X bookmarks, run a backlog triage, or set up a weekly bookmark digest.
---

# X bookmarks triage

Most bookmarks die the moment they are saved: no destination, no verb. This
skill turns each one into a decision. Keep it for a stated reason and send it
where it will be used, or let it go without regret.

The pipeline:

```
x.com/i/bookmarks ──collector.js──▶ export JSON ──ingest.py──▶ raw/ (one .md per bookmark)
        ──model + rubric──▶ triage.jsonl ──route.py──▶ vault pages + raw marked processed
        ──stats.py + model──▶ digest
```

## Before anything

1. Find or create the user's config and profile, next to their vault:
   - `x-bookmarks.config.json`, from `config.example.json` (paths, destinations, routing threshold).
   - `x-bookmarks.profile.md`, from `profile.example.md` (who they are, domains, active projects, trusted and noisy sources, language and writing rules).
   If either is missing, ask the user the few questions needed to fill them. Do not invent projects.
2. Read `references/rubric.md`. It is the contract for every triage.
3. All scripts are Python 3.9+ standard library. Run them from `scripts/` or with their full path, always with `--config`.

## Workflow

### 1. Collect

Follow `references/collect-in-chrome.md`. In short: open the bookmarks page in
a new tab, paste `scripts/collector.js`, `__xb.start(...)`, poll `__xb.status()`,
then get the data out with `__xb.dump()` + page text, or `__xb.download()` if
the user agrees to a file download. Save the export in `exports_dir`.

For a weekly run, pass the ids already in the vault as `knownIds` so collection
stops early.

### 2. Ingest

```
python3 scripts/ingest.py EXPORT.json --config x-bookmarks.config.json
```

Idempotent. Creates one raw markdown file per new bookmark.

### 3. Triage

Apply `references/rubric.md` to every new bookmark and write one JSON line per
bookmark to `analysis_dir/triage-YYYY-MM-DD.jsonl`.

- Small batch (a week): read the raw files directly.
- Backlog: `python3 scripts/condense.py EXPORT.json analysis_dir/backlog --chunk 200`, then one sub-agent per chunk, in parallel, each given the rubric and the profile. Merge, then personally review every score 3 and look for clusters across chunks.
- Before giving a 3 to a truncated post or an X article, open it and read it.

Be harsh. Expect most bookmarks, especially AI tool announcements, to end up as
`noise`. That is the useful outcome.

### 4. Route

```
python3 scripts/route.py analysis_dir/triage-YYYY-MM-DD.jsonl --config x-bookmarks.config.json --dry-run
python3 scripts/route.py analysis_dir/triage-YYYY-MM-DD.jsonl --config x-bookmarks.config.json
```

Appends keepers to their destination pages under a dated heading, inside a
marked block, without touching the rest of the page. Marks every triaged raw
file as processed with its score and critique. Read the warnings it prints.

Optionally, add short hand-written context at the top of a destination page (what
is known, what is not) when a batch reveals a pattern. That synthesis is where
the vault gains value.

Create a task in the user's own system only for a `try` item worth testing
within 30 days, and check for an equivalent task first.

### 5. Digest

```
python3 scripts/stats.py analysis_dir/triage-*.jsonl --config x-bookmarks.config.json
```

Then write the digest described in `references/digest-and-schedule.md`.

### 6. Schedule (optional)

`references/digest-and-schedule.md` explains the weekly unattended run.

## Rules

- The user's bookmarks, exports, profile and config are personal data: keep them out of any repository and never send them anywhere.
- Never remove a bookmark on X and never delete a file without the user's explicit agreement.
- Never present a figure taken from a post as a fact. Verify before any reuse in writing that leaves the vault.
- Ask before downloading a file in the browser. Unattended runs use `dump()` instead.
