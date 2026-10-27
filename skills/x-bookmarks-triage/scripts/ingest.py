#!/usr/bin/env python3
"""Ingest an X bookmarks export (JSON produced by collector.js) into a markdown vault.

One markdown file per bookmark, named "YYYY-MM-DD - handle - id.md", with YAML
frontmatter (type: raw_source, status: unprocessed). Idempotent: bookmarks that
already have a file are skipped, so you can re-run it on overlapping exports.

Usage:
  python3 ingest.py EXPORT.json [--config x-bookmarks.config.json]
"""
import argparse
import datetime
import json
import pathlib

from xb_common import clean, load_config, raw_index, vpath


def kind_of(it):
    if not it.get("text") and it.get("article_hint"):
        return "article"
    if it.get("quote"):
        return "quote"
    return "post"


def q(s):
    return json.dumps(s or "", ensure_ascii=False)


def render(it, export_name, today):
    k = kind_of(it)
    title = clean(it.get("article_hint", "")).split(" | ")[0] if k == "article" else ""
    order = it.get("order")
    lines = [
        "---",
        "type: raw_source",
        "source: x-bookmarks",
        f'source_id: "{it["id"]}"',
        f"url: {it['url']}",
        f"author: {q(it.get('author'))}",
        f'handle: "@{it["handle"]}"',
        f"posted: {it['posted']}",
        f"bookmark_rank: {order if order is not None else 'null'}",
        f"x_folders: {json.dumps(it.get('folders') or [], ensure_ascii=False)}",
        f"kind: {k}",
        f"media: {json.dumps(it.get('media') or [])}",
        f"truncated: {'true' if it.get('show_more') else 'false'}",
        "status: unprocessed",
        f"ingested: {today}",
        f"export: {export_name}",
        "---",
        "",
        f"# @{it['handle']} · {it['posted'][:10]}" + (f" · {title}" if title else ""),
        "",
    ]
    if k == "article":
        lines += ["*X article (long form). Preview captured from the bookmarks list:*", "",
                  clean(it.get("article_hint", "")).replace(" | ", "\n\n")]
    else:
        lines.append(clean(it.get("text")) or "*(no text: media only)*")
    if it.get("show_more"):
        lines += ["", "*Text truncated in the bookmarks list; open the post for the rest.*"]
    quote = it.get("quote")
    if quote:
        lines += ["", f"> **Quoting {quote.get('author', '').strip()}**", ">"]
        lines += ["> " + l for l in clean(quote.get("text")).splitlines()]
    if it.get("card"):
        lines += ["", f"**Link card:** {clean(it['card'])}"]
    links = ["".join(l.split()) for l in it.get("links") or []]
    if links:
        lines += ["", "**Links shown:** " + ", ".join(links)]
    if it.get("media"):
        lines += ["", "**Media:** " + ", ".join(it["media"])]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("export")
    ap.add_argument("--config", default=None)
    a = ap.parse_args()
    cfg = load_config(a.config)
    src = pathlib.Path(a.export)
    data = json.loads(src.read_text(encoding="utf-8"))
    items = data["items"]
    raw = vpath(cfg, cfg["raw_dir"])
    raw.mkdir(parents=True, exist_ok=True)
    have = raw_index(raw)
    today = datetime.date.today().isoformat()
    new = 0
    for it in items:
        if it["id"] in have:
            continue
        name = f"{it['posted'][:10]} - {it['handle']} - {it['id']}.md"
        (raw / name).write_text(render(it, src.name, today), encoding="utf-8")
        new += 1
    total = len(raw_index(raw))
    now = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    hf = vpath(cfg, cfg.get("health_file"))
    if hf:
        hf.parent.mkdir(parents=True, exist_ok=True)
        hf.write_text(
            "---\ntype: source_health\nsource: x-bookmarks\nstatus: healthy\n"
            f"last_sync: {now}\nitems_last_run: {new}\nitems_total: {total}\nlast_export: {src.name}\n---\n",
            encoding="utf-8",
        )
    lf = vpath(cfg, cfg.get("log_file"))
    if lf:
        lf.parent.mkdir(parents=True, exist_ok=True)
        with open(lf, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": now, "export": src.name, "in_export": len(items), "new": new, "total": total}) + "\n")
    print(f"export={src.name} in_export={len(items)} new={new} total_raw={total}")


if __name__ == "__main__":
    main()
