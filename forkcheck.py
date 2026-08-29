"""Are the repos sharing a duplicated SECURITY.md forks, or independent copies?

Pre-registered in DEPTHPREREG.md Addendum 2, before this was run: I predict FEWER than 50%
carry `fork: true`, because the GitHub code-search API excludes forks by default -- so a
result set full of git forks would be a contradiction, and the duplication is more likely
template-copying. The bound is stated there; this script computes it and prints the verdict
either way. [[same-mechanism-is-not-confirmation]]
"""
import hashlib, json, os, sys, time, urllib.request, urllib.error, collections

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
HERE = os.path.dirname(os.path.abspath(__file__))
PER_GROUP = 20


def norm(path):
    t = open(path, encoding="utf-8", errors="replace").read()
    return hashlib.sha1(" ".join(t.split()).encode()).hexdigest()


def modal_group(d):
    """Repos holding the single most-duplicated document in directory d."""
    by = collections.defaultdict(list)
    for fn in sorted(os.listdir(d)):
        if fn.endswith(".md"):
            by[norm(os.path.join(d, fn))].append(fn[:-3].replace("__", "/"))
    h, repos = max(by.items(), key=lambda kv: len(kv[1]))
    return h, repos


def get(repo):
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}",
        headers={"Authorization": f"Bearer {TOK}", "Accept": "application/vnd.github+json",
                 "User-Agent": "rankdepth-forkcheck"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None                      # deleted/renamed since the search hit
            if e.code in (403, 429):
                time.sleep(20 * (attempt + 1)); continue
            raise
        except Exception:
            time.sleep(5 * (attempt + 1))
    # An unresolved repo is NOT evidence either way. Counting it as non-fork would let network
    # failure manufacture support for my own prediction. [[parse-bugs-flatter-in-one-direction]]
    return "ERROR"


rows, summary = [], {}
for d, label in [("md_deep", "A-deep"), ("md_b_deep", "B-deep")]:
    h, repos = modal_group(os.path.join(HERE, d))
    sample = repos[:PER_GROUP]
    print(f"\n{label}: modal document held by {len(repos)} repos, sampling {len(sample)}")
    forks = nonforks = gone = err = 0
    for repo in sample:
        info = get(repo)
        if info == "ERROR":
            err += 1; state = "unresolved"
        elif info is None:
            gone += 1; state = "404"
        elif info.get("fork"):
            forks += 1; state = f"FORK of {info.get('parent', {}).get('full_name', '?')}"
        else:
            nonforks += 1; state = "not-a-fork"
        rows.append((label, repo, state))
        time.sleep(0.4)
    summary[label] = (forks, nonforks, gone, err, len(repos))
    print(f"   fork:true {forks}   fork:false {nonforks}   404 {gone}   unresolved {err}")

print("\n" + "=" * 70)
print("PRE-REGISTERED BOUND: >50% fork:true means the 'copied template' reading is WRONG")
print("=" * 70)
tf = sum(s[0] for s in summary.values())
tn = sum(s[1] for s in summary.values())
resolved = tf + tn
if resolved == 0:
    sys.exit("no repos resolved -- the check did not run")
pct = 100 * tf / resolved
print(f"resolved {resolved} repos: {tf} forks, {tn} non-forks -> {pct:.1f}% fork")
if pct > 50:
    print("\nBOUND FIRED. The prediction was wrong. The writeup must say *forks*, and must "
          "explain why fork-excluding code search returned them.")
    rc = 1
else:
    print(f"\nPrediction held: the duplication is COPYING, not forking. {tn} of {resolved} "
          f"resolved repos are independent repositories carrying someone else's policy text.")
    rc = 0

with open(os.path.join(HERE, "forkcheck.json"), "w") as f:
    json.dump({"rows": rows, "summary": summary, "pct_fork": pct}, f, indent=1)
print(f"\nwrote forkcheck.json ({len(rows)} rows)")
sys.exit(rc)
