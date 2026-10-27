# Triage profile

Copy this file to `x-bookmarks.profile.md` (kept out of git) and make it yours.
The model reads it before every triage. The more concrete it is, the harsher
and more useful the triage gets.

## Who I am

One or two lines: role, field, what I am building. Example: "Founder of a
weather risk start-up, PhD in atmospheric science, building an open source
forecast model in public."

## Domains

The `domain` values the triage may use (keep it to 4 to 7):

- `ai`
- `weather-climate`
- `business`
- `other`

## Active projects

The `projects` values, one per line with a short description. A bookmark that
feeds one of these can score 3; one that feeds none rarely scores above 2.

- `my-product`: what it is, what it needs right now
- `side-project`: ...
- `content`: my posting programme (topics, formats, voices I study)

## Destinations

Map intents to the `destinations` keys of `x-bookmarks.config.json`, and add
project pages if you have them:

- `post` → `post-ideas`
- `try` → `tools-to-try`
- `reference` → `research` (or a project page key)
- adopted rules → `playbook` (only after a test)

## Sources

- Trusted primary sources (score generously if specific): ...
- Aggregators to be strict with: ...

## House rules

Language for critiques and digests, writing constraints (for example: no em
dashes, sentence case headings), what must always be verified before reuse.
