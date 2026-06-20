#!/usr/bin/env python3
"""eval_retrieval.py — can each subdocument be successfully retrieved via routing?

Two levels, cheap by default:

  Level 1 (default, FREE, no LLM)  — keyword distinctness.
    For each subdocument, build a query from its when-to-read line, score keyword
    overlap against every routing entry, and check whether top-1 lands on the doc
    itself. A doc whose description is not distinct enough mis-routes here — and an
    LLM would likely mis-route too.

  Level 2 (--llm)  — real LLM routing, sampled. OPTIONAL, bring your own key.
    Hands the index (filename + blurb for every doc) to an OpenAI-compatible chat
    model and asks, per doc, "to do <when-to-read>, which file?". Each doc is
    asked --samples times (default 3) IN PARALLEL; a doc counts as hit on a
    majority vote (>=2/3). Total calls = subdocuments x samples, one sweep, NO
    improve/eval loop. --max-calls caps TOTAL calls; if docs x samples exceeds
    it, samples are reduced to fit (never silently dropped docs).

    Configure via environment variables (any OpenAI-compatible provider works —
    DeepSeek, Groq, OpenRouter, Gemini's OpenAI endpoint, z.ai's, ...):
      EVAL_LLM_BASE_URL   e.g. https://api.deepseek.com
      EVAL_LLM_MODEL      e.g. deepseek-v4-flash
      EVAL_LLM_API_KEY    your key
    The script reads these at runtime only; it never stores, logs, or transmits
    the key anywhere except to EVAL_LLM_BASE_URL.

Usage:
  python3 eval_retrieval.py <skill_dir>
  python3 eval_retrieval.py <skill_dir> --llm [--samples 3] [--max-calls 90]

Exit 0 if everything that ran is clean, else 1. (--llm requested but unconfigured
is reported as skipped — it is never counted as a pass.)
"""

import argparse
import json
import os
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

STOPWORDS = set("""a an the to of for and or in on at by with from into when how what
which this that these those is are be use used using read when-to-read see file files
doc docs document documents skill reference references it its as a""".split())

FENCE_RE = re.compile(r"```.*?```", re.DOTALL)


def strip_fences(t: str) -> str:
    return FENCE_RE.sub("", t)


def tokenize(text: str):
    toks = re.findall(r"[a-z0-9_]+", text.lower())
    return [t for t in toks if t not in STOPWORDS and len(t) > 2]


def list_subdocs(root: Path):
    """references/*.md excluding any index file."""
    refs = root / "references"
    if not refs.is_dir():
        return []
    out = []
    for p in sorted(refs.rglob("*.md")):  # rglob: cover subdirectories too (match check_routes)
        if p.stem.lower() in ("index", "_index", "readme"):
            continue
        out.append(p)
    return out


def find_index_text(root: Path) -> str:
    refs = root / "references"
    if refs.is_dir():
        for p in sorted(refs.glob("*.md")):  # case-insensitive: INDEX.md on Linux too
            if p.stem.lower() in ("index", "_index"):
                return p.read_text(encoding="utf-8")
    return (root / "SKILL.md").read_text(encoding="utf-8")


def extract_entry(routing_text: str, filename: str):
    """Pull the description block for a given filename out of an index/SKILL.md.

    Returns dict {blurb, when, keywords, raw} or None if the file is not routed.
    """
    body = strip_fences(routing_text)
    lines = body.splitlines()
    stem = filename
    base = filename.rsplit(".", 1)[0]
    block = []
    captured = False
    for i, line in enumerate(lines):
        if stem in line or base in line:
            # capture this line + following indented / sub-bullet lines
            block = [line]
            j = i + 1
            while j < len(lines):
                nxt = lines[j]
                if nxt.strip() == "":
                    break
                if nxt.startswith((" ", "\t", "-", "|")) and not re.match(r"^\S", nxt):
                    block.append(nxt)
                    j += 1
                elif nxt.lstrip().startswith(("when-to-read", "keywords")):
                    block.append(nxt)
                    j += 1
                else:
                    break
            captured = True
            break
    if not captured:
        return None
    raw = "\n".join(block)
    when = ""
    keywords = ""
    for b in block:
        bl = b.strip().lower()
        if bl.startswith("when-to-read"):
            when = b.split(":", 1)[-1].strip()
        elif bl.startswith("keywords"):
            keywords = b.split(":", 1)[-1].strip()
    blurb = block[0]
    return {"blurb": blurb, "when": when, "keywords": keywords, "raw": raw}


def build_entries(root: Path):
    routing = find_index_text(root)
    entries = []
    missing = []
    for p in list_subdocs(root):
        e = extract_entry(routing, p.name)
        if e is None:
            missing.append(p.name)
            continue
        query = e["when"] or e["blurb"]
        entries.append({"file": p.name, "query": query, "desc": e["raw"]})
    return entries, missing


def level1_keyword(entries):
    print("[eval_retrieval] Level 1 — keyword distinctness (free)")
    hits = 0
    misses = []
    for e in entries:
        q = set(tokenize(e["query"]))
        best, best_score = None, -1
        for cand in entries:
            score = len(q & set(tokenize(cand["desc"])))
            if score > best_score:
                best, best_score = cand["file"], score
        if best == e["file"]:
            hits += 1
        else:
            misses.append((e["file"], best))
    total = len(entries) or 1
    print(f"  hit-rate: {hits}/{len(entries)} = {100*hits//total}%")
    for f, got in misses:
        print(f"  [mis-route] '{f}' query collides with -> '{got}'  (descriptions not distinct enough)")
    return hits, len(entries)


def read_llm_config():
    """Return (base_url, model, api_key) from EVAL_LLM_* env vars; '' for any unset.

    Reads the key at runtime only — never stored, logged, or sent anywhere except
    to base_url. No per-machine fallback: configure via the environment.
    """
    return (
        os.environ.get("EVAL_LLM_BASE_URL", "").strip(),
        os.environ.get("EVAL_LLM_MODEL", "").strip(),
        os.environ.get("EVAL_LLM_API_KEY", "").strip(),
    )


def llm_call(base_url: str, model: str, key: str, prompt: str, timeout: int = 60) -> str:
    """One OpenAI-compatible /chat/completions call. Returns the message text."""
    endpoint = base_url.rstrip("/") + "/chat/completions"
    body = json.dumps({
        "model": model,
        "max_tokens": 64,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(endpoint, data=body, method="POST")
    req.add_header("Authorization", f"Bearer {key}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def level2_llm(entries, max_calls: int, samples: int):
    """Returns (hits, total). total == -1 means 'requested but not configured'
    (skipped, not a pass and not a hard failure)."""
    base_url, model, key = read_llm_config()
    if not (base_url and model and key):
        missing = [n for n, v in (("EVAL_LLM_BASE_URL", base_url),
                                  ("EVAL_LLM_MODEL", model),
                                  ("EVAL_LLM_API_KEY", key)) if not v]
        print("[eval_retrieval] Level 2 — SKIPPED (not configured): missing "
              + ", ".join(missing))
        print("  Set EVAL_LLM_BASE_URL / EVAL_LLM_MODEL / EVAL_LLM_API_KEY to enable "
              "the real-routing test (any OpenAI-compatible provider). "
              "Not run = not counted as a pass.")
        return 0, -1
    print(f"[eval_retrieval] Level 2 — {model} routing (parallel sampled, majority vote)")
    n = len(entries)
    if n * samples > max_calls:
        samples = max(1, max_calls // n)
        print(f"  NOTE: {n} docs x requested samples > --max-calls {max_calls}; samples reduced to {samples}.")
    majority = samples // 2 + 1
    print(f"  Will call {model} {n} docs x {samples} samples = {n * samples} call(s) in parallel; "
          f"hit = >={majority}/{samples} votes. One sweep, no loop.")
    catalog = "\n".join(
        f"- {e['file']}: {(e['desc'].splitlines() or [''])[0].strip(' -*')[:120]}"
        for e in entries
    )

    def ask(e):
        prompt = (
            "You route a task to the single best file. Reply with ONLY the filename, nothing else.\n\n"
            f"Files:\n{catalog}\n\n"
            f"Task: {e['query']}\n\nFilename:"
        )
        try:
            ans = llm_call(base_url, model, key, prompt)
        except Exception as ex:
            return ("error", str(ex))
        picked = ans.strip().split()[0].strip("`'\"") if ans.strip() else ""
        ok = e["file"] in ans or e["file"].rsplit(".", 1)[0] in ans
        return ("ok", picked) if ok else ("miss", picked)

    jobs = [(e, s) for e in entries for s in range(samples)]
    with ThreadPoolExecutor(max_workers=min(8, len(jobs))) as pool:
        results = list(pool.map(lambda j: ask(j[0]), jobs))

    hits = 0
    for i, e in enumerate(entries):
        votes = results[i * samples:(i + 1) * samples]
        oks = sum(1 for v, _ in votes if v == "ok")
        errs = [p for v, p in votes if v == "error"]
        wrong = [p for v, p in votes if v == "miss"]
        if oks >= majority:
            hits += 1
            if wrong or errs:
                print(f"  [shaky] '{e['file']}' {oks}/{samples} votes (misses -> {wrong}, errors {len(errs)})")
        else:
            print(f"  [mis-route] '{e['file']}' only {oks}/{samples} votes; model picked {wrong or errs}")
    total = len(entries) or 1
    print(f"  hit-rate (majority): {hits}/{len(entries)} = {100*hits//total}%")
    return hits, len(entries)


def main():
    ap = argparse.ArgumentParser(description="Subdocument retrievability check")
    ap.add_argument("skill_dir")
    ap.add_argument("--llm", "--glm", dest="llm", action="store_true",
                    help="also run real LLM routing (OpenAI-compatible, parallel sampled); "
                         "configure via EVAL_LLM_BASE_URL / EVAL_LLM_MODEL / EVAL_LLM_API_KEY")
    ap.add_argument("--samples", type=int, default=3, help="parallel samples per subdocument (default 3, majority vote)")
    ap.add_argument("--max-calls", type=int, default=90, help="hard cap on TOTAL LLM calls (default 90)")
    args = ap.parse_args()

    root = Path(args.skill_dir).resolve()
    if not (root / "SKILL.md").exists():
        print(f"ERROR: {root}/SKILL.md not found", file=sys.stderr)
        sys.exit(2)

    entries, missing = build_entries(root)
    print(f"[eval_retrieval] {root}")
    print(f"  subdocuments routed: {len(entries)}  unrouted: {len(missing)}")
    for m in missing:
        print(f"  [no-route] references/{m} has no description in SKILL.md/index — cannot be retrieved")

    if not entries:
        print("  nothing to evaluate (no routed subdocuments).")
        sys.exit(1 if missing else 0)

    h1, t1 = level1_keyword(entries)
    h2 = t2 = None
    if args.llm:
        h2, t2 = level2_llm(entries, args.max_calls, args.samples)

    level1_ok = (h1 == t1)
    # Level 2 affects the verdict ONLY when it actually ran (t2 > 0). Requested but
    # unconfigured (t2 == -1) is a skip: never a pass, never a hard failure here.
    llm_ran = (t2 is not None and t2 > 0)
    llm_ok = (not llm_ran) or (h2 == t2)
    clean = level1_ok and (missing == []) and llm_ok
    sys.exit(0 if clean else 1)


if __name__ == "__main__":
    main()
