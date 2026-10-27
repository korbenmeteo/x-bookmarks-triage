# Triage rubric

The triage is **critical by default**. A bookmark has to earn its place. An
interesting topic is not enough: the post itself must bring something specific
(a paper, a dataset, a figure with its source, a named method, working code, a
first-hand account). In the test backlog that shaped this rubric, 85 % of 863
bookmarks did not survive, and that was the point.

Read the user's profile (`x-bookmarks.profile.md`) first. Judge relevance for
**this user, today**.

## Intent (exactly one)

| Intent | Meaning |
|---|---|
| `try` | A tool, repo, skill, prompt, model or tip to actually test |
| `post` | Material for a post or op-ed: an event, a strong figure, an angle, a debate, a structure worth studying |
| `reference` | Durable knowledge for the vault: paper, dataset, method, actor, market, quantified lesson |
| `noise` | Off-topic, engagement bait, expired, duplicate with nothing new, nothing to do |

## Score (relevance today, for this user)

| Score | Meaning |
|---|---|
| 3 | Feeds an active project directly, or is a reference the user would cite; specific and checkable |
| 2 | Useful but generic, or needs checking before use |
| 1 | Weak: vague promise, unverifiable figures, self-promotion, outdated tool, idea seen everywhere |
| 0 | Noise, off-topic, expired |

Only score 2 and above gets routed (configurable with `min_score_to_route`).

## Red flags (lower the score and name them in the critique)

- Engagement hooks: "🚨", "THIS IS A GOLDMINE", "nobody is talking about", "it's so over", "save this", "thread 🧵" with no substance.
- Income or P&L claims nobody can check ("this trader makes $2,000 a day", "$27k in 28 days"), worse when they lead to a Telegram channel, a referral link or a paid product.
- A founder announcing their own product with no independent demonstration.
- Aggregator accounts recycling AI news (lists of "10 free repos", "9 prompts to try"): prefer the primary source.
- AI tools older than about 6 months: presumed outdated unless they became standard.
- Duplicates: the same announcement relayed by several accounts. Keep the primary source, mark the others `noise` with the same `cluster`.

## Perishability

- `perishable`: tools, models, tips, product news (useful for less than ~3 months).
- `durable`: science, data, methods, markets, first-hand lessons, reference events.

## Output: one JSON object per line

```json
{"id":"1234567890","intent":"try|post|reference|noise","domain":"<profile domain>","score":0,"perishability":"perishable|durable","projects":["<profile project>"],"cluster":"short-key-or-null","critique":"One sentence: why it is worth keeping or not, red flags named.","action":"One line: what to do concretely.","target":"<destinations key or null>"}
```

Rules:

- Every bookmark in the input gets exactly one line; copy `id` exactly.
- `target` must be a key of `destinations` in the config, or `null`.
- Write `critique` and `action` in the language set in the profile.
- Never present a figure from a post (P&L, accuracy, growth) as a fact: write "claims".
- Mark truncated posts and X articles you could not read in full. Open them before giving a 3.

## Large backlogs

For more than ~200 bookmarks, run `condense.py` with `--chunk 200` and give each
chunk to a sub-agent with this rubric and the profile. Ask each one to write its
own `triage-partN.jsonl` and to check that every id from its chunk is present
exactly once. Then concatenate, spot-check every score 3 and a sample of 2s, and
look for clusters that span chunks.
