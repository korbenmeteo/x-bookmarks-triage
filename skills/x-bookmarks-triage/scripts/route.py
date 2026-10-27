#!/usr/bin/env python3
"""Route triaged bookmarks into vault pages and mark the raw files as processed.

Reads a triage JSONL file (one object per bookmark, see references/rubric.md).
Every bookmark with score >= min_score_to_route, an intent other than "noise"
and a `target` that exists in config["destinations"] is appended to that page,
inside a marked block, under a dated sub-heading. Re-running is safe: a bookmark
already present in a page's block is not added twice.

Every bookmark in the triage file (routed or not) gets its raw file updated:
status: processed, processed: DATE, triage: {...}, triage_note, processed_into.

Usage:
  python3 route.py TRIAGE.jsonl [--config x-bookmarks.config.json] [--date YYYY-MM-DD] [--dry-run]
"""
import argparse
import datetime
import json
import pathlib
import re

from xb_common import load_config, raw_index, read_jsonl, split_frontmatter, vpath

BEGIN, END = "<!-- x-bookmarks:start -->", "<!-- x-bookmarks:end -->"
VALID_INTENTS = {"try", "post", "reference", "noise"}


def dest_spec(cfg, key):
    d = cfg["destinations"].get(key)
    if d is None:
        return None
    if isinstance(d, str):
        d = {"path": d}
    d = dict(d)
    d.setdefault("title", pathlib.Path(d["path"]).stem)
    d.setdefault("description", "")
    return d


def raw_meta(path):
    head, _ = split_frontmatter(path.read_text(encoding="utf-8"))
    meta = {}
    for line in (head or "").splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"')
    return meta


def entry(t, meta, raw_path, wikilinks):
    stars = "★" * int(t.get("score", 0))
    url = meta.get("url", "")
    handle = meta.get("handle", "")
    posted = meta.get("posted", "")[:10]
    raw_ref = f"[[{raw_path.stem}|raw]]" if wikilinks else f"[raw]({raw_path.name})"
    trunc = " · *truncated*" if meta.get("truncated") == "true" else ""
    out = f"- **{handle}**, {posted} · {stars} · [post]({url}) · {raw_ref}{trunc}\n  {t.get('critique', '').strip()}"
    if t.get("action"):
        out += f"\n  *Next:* {t['action'].strip()}"
    return out


def upsert_page(path, spec, date, entries, ids):
    if path.exists():
        text = path.read_text(encoding="utf-8")
    else:
        text = (f"---\ntype: topic\nname: {spec['title']}\ndescription: {spec['description']}\n"
                f"created: {date}\nlast_updated: {date}\nsources:\n  - x-bookmarks\n---\n\n# {spec['title']}\n")
    if BEGIN not in text:
        text = text.rstrip() + f"\n\n{BEGIN}\n## From X bookmarks\n{END}\n"
    pre, rest = text.split(BEGIN, 1)
    block, post = rest.split(END, 1)
    fresh = [(i, e) for i, e in zip(ids, entries) if f"/status/{i})" not in block]
    if not fresh:
        return 0
    heading = f"### {date}"
    if heading in block:
        block = block.replace(heading + "\n", heading + "\n" + "\n".join(e for _, e in fresh) + "\n", 1)
    else:
        block = block.rstrip() + f"\n\n{heading}\n" + "\n".join(e for _, e in fresh) + "\n"
    text = pre + BEGIN + block + END + post
    text = re.sub(r"^last_updated: .*$", f"last_updated: {date}", text, count=1, flags=re.M)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return len(fresh)


def mark_processed(path, t, date, into):
    text = path.read_text(encoding="utf-8")
    head, body = split_frontmatter(text)
    if head is None:
        return False
    head = re.sub(r"^status: .*$", "status: processed", head, flags=re.M)
    head = re.sub(r"^(processed|triage|triage_note|processed_into):.*\n?", "", head, flags=re.M).rstrip("\n")
    keys = ("intent", "score", "domain", "perishability", "cluster", "projects")
    head += f"\nprocessed: {date}"
    head += "\ntriage: " + json.dumps({k: t.get(k) for k in keys}, ensure_ascii=False)
    head += "\ntriage_note: " + json.dumps(t.get("critique", ""), ensure_ascii=False)
    head += "\nprocessed_into: " + json.dumps(into, ensure_ascii=False)
    path.write_text("---\n" + head + "\n---\n" + body, encoding="utf-8")
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("triage")
    ap.add_argument("--config", default=None)
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    cfg = load_config(a.config)
    rows = read_jsonl(a.triage)
    idx = raw_index(vpath(cfg, cfg["raw_dir"]))
    min_score = int(cfg.get("min_score_to_route", 2))

    problems, plan = [], {}
    for t in rows:
        if t.get("intent") not in VALID_INTENTS:
            problems.append(f"{t.get('id')}: unknown intent {t.get('intent')!r}")
        if t.get("id") not in idx:
            problems.append(f"{t.get('id')}: no raw file")
            continue
        if t.get("intent") == "noise" or int(t.get("score", 0)) < min_score:
            continue
        key = t.get("target")
        if not key:
            continue
        if dest_spec(cfg, key) is None:
            problems.append(f"{t['id']}: target {key!r} not in config destinations")
            continue
        plan.setdefault(key, []).append(t)

    routing = {}
    for key, items in plan.items():
        spec = dest_spec(cfg, key)
        path = vpath(cfg, spec["path"])
        items.sort(key=lambda t: -int(t.get("score", 0)))
        entries = [entry(t, raw_meta(idx[t["id"]]), idx[t["id"]], cfg.get("wikilinks", True)) for t in items]
        ids = [t["id"] for t in items]
        added = len(ids) if a.dry_run else upsert_page(path, spec, a.date, entries, ids)
        routing[spec["path"]] = ids
        verb = "would add up to" if a.dry_run else "added"
        print(f"{spec['path']}: {verb} {added} ({len(ids)} routed)")

    into = {}
    for page, ids in routing.items():
        for i in ids:
            into.setdefault(i, []).append(page)
    marked = 0
    if not a.dry_run:
        for t in rows:
            if t.get("id") in idx and mark_processed(idx[t["id"]], t, a.date, into.get(t["id"], [])):
                marked += 1
        out_dir = vpath(cfg, cfg["analysis_dir"])
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"routing-{a.date}.json").write_text(json.dumps(routing, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"rows={len(rows)} routed={sum(len(v) for v in routing.values())} marked_processed={marked}" + (" (dry run, nothing written)" if a.dry_run else ""))
    for p in problems:
        print("WARNING", p)


if __name__ == "__main__":
    main()
