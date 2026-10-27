# Digest and weekly schedule

## Digest

Write `digest_dir/YYYY-MM-DD - X bookmarks digest.md`:

1. One sentence: how many new bookmarks, how many kept.
2. **Read first**: the score 3 items, one line each, with the link to the vault page where they landed.
3. **To try**: the `try` items worth a test within 30 days.
4. **Post angles**: with any anniversary or news hook in the next 7 days called out first.
5. **Set aside**: one line per cluster of noise, with the reason.
6. The output of `stats.py` for the period.

Keep it short. A thin week gets three lines, not padding.

## Weekly run

A scheduled agent (for example a Cowork scheduled task bound to the user's
computer, or a cron job running Claude Code with Chrome available) runs:

1. Read the profile, the config and the last digest.
2. Collect new bookmarks with `knownIds` set to the ids already in `raw_dir` (`stopAfterKnown: 15`). Use the `dump()` route: an unattended run cannot ask for a download.
3. `ingest.py`, then triage the new raw files with the rubric, then `route.py`, then the digest.
4. On failure (browser closed, extension not connected, page not loading), write an issue note and stop. Never retry blindly.

Guardrails for unattended runs: never remove a bookmark on X, never delete a
file, never send a message, never write outside the vault.
