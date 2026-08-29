#!/usr/bin/env python3
"""Page directpay's own eight queries to the API's ceiling, recording where each repo was found.

    python3 pagedeep.py          # -> hits_deep.tsv  (repo, path, query, page)

The queries are copied from ../directpay/collect.py *unchanged*. The point of this run is to
test that survey, not to run a better one, so a query I would write differently today is still
the query that has to go in.

Two rules carried over from the pvrsweep re-page:

  * Stop on the first EMPTY page, never on total_count. For these queries total_count now
    reports as little as a tenth of the rows already on disk, and paging to it stops at page 1
    and calls that the end -- which is how "the universe is exhausted" got published.
  * A throttled response is not an empty page. `search()` returns a sentinel when it gives up
    after four backoffs; treating that as "no more results" truncates the corpus silently and
    the truncation looks exactly like a natural end.
"""
import json, os, sys, time, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
def _token():
    """GH_TOKEN, or a path in GH_TOKEN_FILE. No default: a published script that silently
    reads someone's home directory is a script that only runs on the machine that wrote it.
    [[gate-rule-portability]]"""
    t = os.environ.get("GH_TOKEN")
    if t: return t.strip()
    p = os.environ.get("GH_TOKEN_FILE")
    if p and os.path.exists(p): return open(p).read().strip()
    raise SystemExit("Set GH_TOKEN (or GH_TOKEN_FILE) to a GitHub token with public_repo scope.")

TOK = _token()
API = "https://api.github.com/search/code"
SLEEP = 7
MAXPAGE = 10  # the API caps every query at 1000 results

CONTROL = "bounty+filename:SECURITY.md"
QUERIES = [
    "bounty+USDC+filename:SECURITY.md",
    "bounty+ethereum+filename:SECURITY.md",
    "bounty+wallet+address+filename:SECURITY.md",
    "bounty+lightning+filename:SECURITY.md",
    "bounty+bitcoin+filename:SECURITY.md",
    "bounty+monero+filename:SECURITY.md",
    "bounty+paid+in+ETH+filename:SECURITY.md",
    "bug+bounty+no+KYC+filename:SECURITY.md",
]


def search(q, page=1):
    req = urllib.request.Request(
        f"{API}?q={q}&per_page=100&page={page}",
        headers={"Authorization": f"token {TOK}",
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "agentatwork"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                time.sleep(20 * (attempt + 1))
                continue
            if e.code == 422:  # past the 1000-result ceiling
                return {"items": [], "capped": True}
            raise
        except Exception:
            time.sleep(10 * (attempt + 1))
    return {"items": [], "throttled": True}


def main():
    ctrl = search(CONTROL)
    if not ctrl.get("total_count"):
        sys.exit("control query returned nothing -- syntax or auth is broken, not the corpus")
    print(f"control: {ctrl['total_count']} SECURITY.md files mention 'bounty'\n")

    out = open(os.path.join(HERE, "hits_deep.tsv"), "w")
    rows = 0
    for q in QUERIES:
        got, total, stop = 0, None, ""
        for page in range(1, MAXPAGE + 1):
            time.sleep(SLEEP)
            d = search(q, page)
            if d.get("throttled"):
                stop = f"THROTTLED at page {page} -- corpus for this query is INCOMPLETE"
                break
            if total is None:
                total = d.get("total_count")
            items = d.get("items", [])
            for it in items:
                out.write(f'{it["repository"]["full_name"]}\t{it["path"]}\t{q}\t{page}\n')
                rows += 1
            got += len(items)
            out.flush()
            if not items:
                stop = f"empty page at {page}"
                break
            if d.get("capped"):
                stop = f"1000-result ceiling at page {page}"
                break
        else:
            stop = f"reached page {MAXPAGE}"
        print(f"{q:48s} total {str(total):>6}  collected {got:>5}  ({stop})")
    out.close()
    print(f"\n{rows} rows -> hits_deep.tsv")


if __name__ == "__main__":
    main()
