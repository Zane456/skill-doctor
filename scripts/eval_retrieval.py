#!/usr/bin/env python3
"""eval_retrieval.py — can each subdocument be successfully retrieved via routing?

Two levels, cheap by default:

  Level 1 (default, FREE, no LLM)  — keyword distinctness.
    For each subdocument, build a query from its when-to-read line, score keyword
    overlap against every routing entry, and check whether top-1 lands on the doc
    itself. A doc whose description is not distinct enough mis-routes here — and an
    LLM would likely mis-route too.

  Level 2 (--glm, glm-5.2)  — real LLM routing, sampled.
    Hands the index (filename + blurb for every doc) to glm-5.2 and asks, per
    doc, "to do <when-to-read>, which file?". Each doc is asked --samples times
    (default 3) IN PARALLEL; a doc counts as hit on a majority vote (>=2/3).
    Total calls = subdocuments x samples, one sweep, NO improve/eval loop.
    --max-calls caps TOTAL calls; if docs x samples exceeds it, samples are
    reduced to fit (never silently dropped docs). Projected count printed up front.

Usage:
  python3 eval_retrieval.py <skill_dir>
  python3 eval_retrieval.py <skill_dir> --glm [--samples 3] [--max-calls 90]

Exit 0 if hit-rate == 100%, else 1.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

GLM_ENDPOINT = "https://api.z.ai/api/anthropic/v1/messages"
GLM_MODEL = "glm-5.2"
PLIST = Path.home() / "Library/LaunchAgents/com.user.sync-knowledge-profile.plist"

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


def read_glm_key() -> str:
    key = os.environ.get("GLM_API_KEY")
    if key:
        return key.strip()
    try:
        out = subprocess.run(
            ["/usr/libexec/PlistBuddy", "-c",
             "Print :EnvironmentVariables:GLM_API_KEY", str(PLIST)],
            capture_output=True, text=True, timeout=10,
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except Exception:
        pass
    return ""


def glm_call(key: str, prompt: str, timeout: int = 60) -> str:
    body = json.dumps({
        "model": GLM_MODEL,
        "max_tokens": 64,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(GLM_ENDPOINT, data=body, method="POST")
    req.add_header("x-api-key", key)
    req.add_header("anthropic-version", "2023-06-01")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read().decode("utf-8"))
    return data["content"][0]["text"]


def level2_glm(entries, max_calls: int, samples: int):
    print("[eval_retrieval] Level 2 — glm-5.2 routing (parallel sampled, majority vote)")
    n = len(entries)
    if n * samples > max_calls:
        samples = max(1, max_calls // n)
        print(f"  NOTE: {n} docs x requested samples > --max-calls {max_calls}; samples reduced to {samples}.")
    majority = samples // 2 + 1
    print(f"  Will call {GLM_MODEL} {n} docs x {samples} samples = {n * samples} call(s) in parallel; "
          f"hit = >={majority}/{samples} votes. One sweep, no loop.")
    key = read_glm_key()
    if not key:
        print("  ERROR: no GLM_API_KEY (env or plist). GLM level did NOT run — "
              "reporting FAILURE, not a silent skip.", file=sys.stderr)
        return 0, 0  # total=0 -> main marks the run as failed (see glm_ok)
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
            ans = glm_call(key, prompt)
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
            print(f"  [mis-route] '{e['file']}' only {oks}/{samples} votes; GLM picked {wrong or errs}")
    total = len(entries) or 1
    print(f"  hit-rate (majority): {hits}/{len(entries)} = {100*hits//total}%")
    return hits, len(entries)


def main():
    ap = argparse.ArgumentParser(description="Subdocument retrievability check")
    ap.add_argument("skill_dir")
    ap.add_argument("--glm", action="store_true", help="also run glm-5.2 routing (parallel sampled)")
    ap.add_argument("--samples", type=int, default=3, help="parallel samples per subdocument (default 3, majority vote)")
    ap.add_argument("--max-calls", type=int, default=90, help="hard cap on TOTAL GLM calls (default 90)")
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
    if args.glm:
        h2, t2 = level2_glm(entries, args.max_calls, args.samples)

    level1_ok = (h1 == t1)
    # When --glm is requested it MUST actually run (t2>0) and fully pass; a
    # skipped/keyless/all-errored GLM level must NOT be reported as success.
    glm_ok = (not args.glm) or (t2 is not None and t2 > 0 and h2 == t2)
    clean = level1_ok and (missing == []) and glm_ok
    sys.exit(0 if clean else 1)


if __name__ == "__main__":
    main()
