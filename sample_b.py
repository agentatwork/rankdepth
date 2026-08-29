#!/usr/bin/env python3
"""Arm pair B: draw page-1 and pages-5+ repos from the pvrsweep corpus.

    python3 sample_b.py          # ../pvrsweep/hits_p2.tsv -> b_shallow.json, b_deep.json

Same arm rule as sample.py -- the MINIMUM page across all queries, because that is the page at
which a collector paging in order would first have seen the repo. Same output shape, so
directpay's fetchmd.py reads these too.

Why this corpus exists as a second arm pair: directpay's eight queries yield only 174 deep repos
today, and they are all crypto-payment flavoured. hits_p2.tsv was paged to the empty page over
thirteen reward/scope/contract queries in one run on the same collapsed index, and 459 of its
repos first appear on page 5 or later. Different queries, three times the depth range, one
classifier. [[DEPTHPREREG.md amendment 4]]
"""
import collections, json, os, random

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.environ.get("PVRSWEEP_HITS", os.path.join(HERE, "..", "pvrsweep", "hits_p2.tsv"))
N = 300
SEED = 20260829
DEEP_MIN = 5  # pages 5-10: the band where pvrsweep measured PVR-on at 1.55%

minpage, paths, queries = {}, {}, collections.defaultdict(set)
rows = 0
for line in open(SRC):
    f = line.rstrip("\n").split("\t")
    if len(f) < 4:
        continue
    repo, path, q, page = f[0], f[1], f[2], int(f[3])
    rows += 1
    queries[repo].add(q)
    if repo not in minpage or page < minpage[repo]:
        minpage[repo], paths[repo] = page, path
    paths.setdefault(repo, path)

print(f"{rows} rows over {len(minpage)} distinct repos")
arms = {"b_shallow": [r for r, p in minpage.items() if p == 1],
        "b_deep": [r for r, p in minpage.items() if p >= DEEP_MIN]}
print(f"page 1        : {len(arms['b_shallow'])}")
print(f"pages {DEEP_MIN}+ only : {len(arms['b_deep'])}")

rnd = random.Random(SEED)
for arm, repos in arms.items():
    repos = sorted(repos)
    rnd.shuffle(repos)
    pick = repos[:N]
    json.dump([{"repo": r, "path": paths[r], "queries": sorted(queries[r]),
                "minpage": minpage[r]} for r in sorted(pick)],
              open(os.path.join(HERE, f"{arm}.json"), "w"), indent=1)
    print(f"drew {len(pick)} for {arm} -> {arm}.json")
