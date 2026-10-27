#!/usr/bin/env python3
"""Summarise one or more triage files as markdown, for the digest.

Shows keep rate by domain and intent, the authors who earn their place and the
ones who never do, and whether X bookmark folders actually helped.

Usage:
  python3 stats.py TRIAGE.jsonl [MORE.jsonl ...] [--config x-bookmarks.config.json]
"""
import argparse
import collections

from route import raw_meta
from xb_common import load_config, raw_index, read_jsonl, vpath


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("triage", nargs="+")
    ap.add_argument("--config", default=None)
    a = ap.parse_args()
    cfg = load_config(a.config)
    min_score = int(cfg.get("min_score_to_route", 2))
    rows = {}
    for f in a.triage:
        for t in read_jsonl(f):
            rows[t["id"]] = t
    idx = raw_index(vpath(cfg, cfg["raw_dir"]))
    keep = lambda t: t.get("intent") != "noise" and int(t.get("score", 0)) >= min_score

    total, kept = len(rows), sum(keep(t) for t in rows.values())
    top = sum(int(t.get("score", 0)) == 3 for t in rows.values())
    print(f"**{total} bookmarks triaged, {kept} kept ({round(100 * kept / max(total, 1))} %), {top} rated 3.**\n")

    print("| Domain | Bookmarks | Kept | Rate |\n|---|---|---|---|")
    dom = collections.defaultdict(lambda: [0, 0])
    for t in rows.values():
        dom[t.get("domain", "?")][0] += 1
        dom[t.get("domain", "?")][1] += keep(t)
    for d, (n, k) in sorted(dom.items(), key=lambda x: -x[1][0]):
        print(f"| {d} | {n} | {k} | {round(100 * k / n)} % |")

    print("\n| Intent | Kept |\n|---|---|")
    for i, n in collections.Counter(t["intent"] for t in rows.values() if keep(t)).most_common():
        print(f"| {i} | {n} |")

    auth = collections.defaultdict(lambda: [0, 0])
    folders = [0, 0]
    for i, t in rows.items():
        if i not in idx:
            continue
        m = raw_meta(idx[i])
        auth[m.get("handle", "?")][0] += 1
        auth[m.get("handle", "?")][1] += keep(t)
        if m.get("x_folders", "[]") not in ("[]", ""):
            folders[0] += 1
            folders[1] += keep(t)
    best = sorted((v[1], v[0], h) for h, v in auth.items() if v[1])[::-1][:10]
    never = sorted((v[0], h) for h, v in auth.items() if v[1] == 0 and v[0] >= 3)[::-1][:10]
    if best:
        print("\n**Sources that earn their place:** " + ", ".join(f"{h} ({k}/{n})" for k, n, h in best))
    if never:
        print("\n**Bookmarked often, never kept:** " + ", ".join(f"{h} (0/{n})" for n, h in never))
    if folders[0]:
        print(f"\n**X folders:** {folders[0]} bookmark(s) filed in folders, {folders[1]} kept.")


if __name__ == "__main__":
    main()
