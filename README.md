# x-bookmarks-triage

A Claude skill that turns years of X (Twitter) bookmarks into a curated,
linked knowledge base, then keeps it tidy every week.

I had 863 bookmarks going back to 2020 and could not use any of them. After one
critical pass with this skill, 126 earned a place (15 %), 24 of them strong. The
rest were expired AI tool launches, recycled threads and bait. Half of my
bookmarks were about AI and only 1 in 10 survived; weather and climate posts were
rarer but 1 in 3 survived. The X folders I had been "organising" with held 70
bookmarks in total. Seeing that was worth the exercise on its own.

## What it does

1. **Collect** your bookmarks from your own logged-in browser (no API key), including X articles, quotes, links and Premium folders.
2. **Ingest** them into a markdown vault: one file per bookmark, with frontmatter. Works with Obsidian.
3. **Triage** each one against *your* profile and projects: intent (`try`, `post`, `reference`, `noise`), a 0 to 3 relevance score, red flags, duplicates grouped by cluster, and a one-line critique and next action.
4. **Route** the keepers to the pages where you will actually use them (post ideas, tools to try, research notes, project pages), under dated headings, without touching the rest of your notes.
5. **Digest**: a short weekly brief, plus stats on which sources earn their place and which never do.

## Requirements

- Claude Code or Claude Cowork, with **Claude in Chrome** for the collection step.
- Python 3.10+ (standard library only).
- A folder of markdown notes (any structure; an Obsidian vault is ideal).

## Install

As a Claude Code plugin:

```
/plugin marketplace add korbenmeteo/x-bookmarks-triage
/plugin install x-bookmarks-triage@x-bookmarks-triage
```

Or copy `skills/x-bookmarks-triage/` into `~/.claude/skills/`.

## Quick start

1. In your vault, copy `config.example.json` to `x-bookmarks.config.json` and `profile.example.md` to `x-bookmarks.profile.md`. Fill in the profile: who you are, your domains, your active projects, the sources you trust. The triage is only as sharp as this file.
2. Ask Claude: *"Triage my X bookmarks."* For a first run it collects the whole backlog, splits it into chunks for parallel sub-agents, and shows you the result before routing.
3. Optionally schedule a weekly run (see `references/digest-and-schedule.md`).

To see the pipeline on synthetic data: `bash examples/run-example.sh`.

## Privacy

Everything runs on your machine and in your browser. The collector sends
nothing anywhere. Your exports, profile and config are listed in `.gitignore`;
keep them out of any repository.

## Limits

- The browser route reads what the bookmarks page shows. It worked back to 2020 on an 863-item account; X does not document a cap for the web page. The official API stops at the 800 most recent bookmarks.
- Use the browser route on your own account, at human speed. For an officially supported path, use the X API.
- X changes its markup from time to time. The selectors live in one function (`parse` in `collector.js`).
- The triage is a model's judgement guided by a rubric. Review the 3s; spot-check the rest.

## Author

Built by Ruben Hallali ([@RubenHallali](https://x.com/RubenHallali)). I am
building my own tooling in public; issues and pull requests are welcome.

## Licence

MIT
