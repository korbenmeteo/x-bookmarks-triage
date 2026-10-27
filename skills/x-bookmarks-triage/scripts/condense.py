#!/usr/bin/env python3
"""Turn an export into compact one-line-per-bookmark text for the model to triage.

Line format:
  id | rRANK | YYYY-MM-DD | @handle [folders] | text || QT author: quote || CARD: ... || ARTICLE: ... [media:...] [truncated]

Large backlogs are split into chunks (default 200 lines) so several sub-agents
can triage in parallel with the same rubric.

Usage:
  python3 condense.py EXPORT.json OUT_PREFIX [--chunk 200] [--only-ids ids.txt]
Writes OUT_PREFIX-part1.txt, OUT_PREFIX-part2.txt, ...
"""
import argparse
import json
import pathlib
import re

from xb_common import clean


def line(it):
    sq = lambda s, n: re.sub(r"\s+", " ", clean(s))[:n]
    q = it.get("quote")
    parts = [sq(it.get("text"), 420)]
    if q:
        parts.append(f"|| QT {q.get('author', '').strip()}: {sq(q.get('text'), 180)}")
    if it.get("card"):
        parts.append("|| CARD: " + it["card"][:130])
    if not it.get("text") and it.get("article_hint"):
        parts.append("|| ARTICLE: " + sq(it["article_hint"], 260))
    if it.get("media"):
        parts.append("[media:" + ",".join(it["media"]) + "]")
    if it.get("show_more"):
        parts.append("[truncated]")
    folders = f" [{','.join(it['folders'])}]" if it.get("folders") else ""
    return f"{it['id']} | r{it.get('order')} | {it['posted'][:10]} | @{it['handle']}{folders} | " + " ".join(p for p in parts if p)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("export")
    ap.add_argument("out_prefix")
    ap.add_argument("--chunk", type=int, default=200)
    ap.add_argument("--only-ids", default=None)
    a = ap.parse_args()
    items = json.loads(pathlib.Path(a.export).read_text(encoding="utf-8"))["items"]
    if a.only_ids:
        keep = set(pathlib.Path(a.only_ids).read_text().split())
        items = [i for i in items if i["id"] in keep]
    lines = [line(i) for i in items]
    n = 0
    for k in range(0, len(lines), a.chunk):
        n += 1
        out = pathlib.Path(f"{a.out_prefix}-part{n}.txt")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n".join(lines[k:k + a.chunk]) + "\n", encoding="utf-8")
        print(out, len(lines[k:k + a.chunk]))


if __name__ == "__main__":
    main()
