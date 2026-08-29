#!/usr/bin/env python3
"""Split the paged corpus into a shallow and a deep arm and draw n=300 from each.

    python3 sample.py            # hits_deep.tsv -> shallow.json, deep.json, arms.json

**The arm is decided by the MINIMUM page on which a repo appears across all eight queries**,
not by the page of any single row. A repo on page 1 of `bounty+bitcoin` and page 7 of
`bounty+USDC` is a repo directpay's collector *did* see, so it belongs in the shallow arm. The
question is not "where does this row live" but "would the published survey have found this
repository", and only the minimum answers that.

Both files come out in candidates.json's shape ({repo, path, queries}) so that directpay's own
fetchmd.py reads them unmodified.
"""
import collections, json, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
N = 300
SEED = 20260829
SHALLOW_MAX = 3  # the depth ../directpay/collect.py actually reached: for page in (1, 2, 3)

rows = 0
minpage, paths, queries = {}, {}, collections.defaultdict(set)
for line in open(os.path.join(HERE, "hits_deep.tsv")):
    f = line.rstrip("\n").split("\t")
    if len(f) != 4:
        continue
    repo, path, q, page = f[0], f[1], f[2], int(f[3])
    rows += 1
    queries[repo].add(q)
    if repo not in minpage or page < minpage[repo]:
        minpage[repo], paths[repo] = page, path
    elif repo not in paths:
        paths[repo] = path

print(f"{rows} rows over {len(minpage)} distinct repos")

arms = {"shallow": [], "deep": []}
for repo, p in minpage.items():
    arms["shallow" if p <= SHALLOW_MAX else "deep"].append(repo)

dist = collections.Counter(minpage.values())
print("\nrepos by first page of appearance:")
for p in sorted(dist):
    print(f"  page {p:>2}: {dist[p]:>5}")
print(f"\nshallow (pages 1-{SHALLOW_MAX}): {len(arms['shallow'])}")
print(f"deep    (pages {SHALLOW_MAX+1}+ only): {len(arms['deep'])}")

if len(arms["deep"]) < N:
    print(f"\nNOTE: deep arm holds only {len(arms['deep'])} repos, fewer than n={N}. "
          f"Taking all of them; the shallow arm is still drawn at {N} and the comparison "
          f"is unbalanced but valid. Power must be recomputed at the realised sizes.")

rnd = random.Random(SEED)
out = {}
for arm, repos in arms.items():
    repos = sorted(repos)          # sort first: dict order is insertion order, so an unsorted
    rnd.shuffle(repos)             # list makes the "seeded" draw depend on fetch order too
    pick = repos[:N]
    out[arm] = pick
    json.dump([{"repo": r, "path": paths[r], "queries": sorted(queries[r]),
                "minpage": minpage[r]} for r in sorted(pick)],
              open(os.path.join(HERE, f"{arm}.json"), "w"), indent=1)
    print(f"drew {len(pick)} for {arm} -> {arm}.json")

json.dump({"n": N, "seed": SEED, "shallow_max_page": SHALLOW_MAX,
           "arm_sizes": {k: len(v) for k, v in arms.items()},
           "page_distribution": {str(k): v for k, v in sorted(dist.items())},
           "drawn": out},
          open(os.path.join(HERE, "arms.json"), "w"), indent=1)
