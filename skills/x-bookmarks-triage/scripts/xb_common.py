"""Shared helpers for x-bookmarks-triage scripts. Python 3.8+, standard library only."""
import json
import pathlib
import re

DEFAULT_CONFIG = {
    "vault_root": ".",
    "raw_dir": "raw/x-bookmarks",
    "exports_dir": "raw/x-bookmarks/_exports",
    "analysis_dir": "raw/x-bookmarks/_triage",
    "digest_dir": "outputs/x-bookmarks",
    "health_file": None,
    "log_file": None,
    "min_score_to_route": 2,
    "destinations": {},
    "wikilinks": True,
}

ID_IN_NAME = re.compile(r" - (\d{6,})\.md$")
URL_SPLIT = re.compile(r"(https?://)\s*\n([^\s]+)\n?([^\s…]*)\n?…")


def load_config(path):
    cfg = dict(DEFAULT_CONFIG)
    if path:
        p = pathlib.Path(path)
        if not p.exists():
            raise SystemExit(f"Config not found: {p}")
        cfg.update(json.loads(p.read_text(encoding="utf-8")))
        base = p.resolve().parent
        root = pathlib.Path(cfg["vault_root"])
        cfg["vault_root"] = str(root if root.is_absolute() else (base / root).resolve())
    else:
        cfg["vault_root"] = str(pathlib.Path(cfg["vault_root"]).resolve())
    return cfg


def vpath(cfg, rel):
    """Resolve a vault-relative path from the config."""
    if rel is None:
        return None
    p = pathlib.Path(rel)
    return p if p.is_absolute() else pathlib.Path(cfg["vault_root"]) / p


def clean(s):
    """Re-join URLs that X's DOM splits across lines."""
    if not s:
        return ""
    s = URL_SPLIT.sub(lambda m: m.group(1) + m.group(2) + m.group(3) + "…", s)
    s = re.sub(r"(https?://)\s*\n", r"\1", s)
    return s.strip()


def raw_index(raw_dir):
    """Map bookmark id -> raw file path."""
    out = {}
    for p in pathlib.Path(raw_dir).glob("*.md"):
        m = ID_IN_NAME.search(p.name)
        if m:
            out[m.group(1)] = p
    return out


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def split_frontmatter(text):
    if not text.startswith("---\n"):
        return None, text
    head, _, body = text[4:].partition("\n---\n")
    return head, body
