"""Every number in README.md must trace to an artifact in this repository.

Not a whitelist of "numbers that exist somewhere". Each assertion names the claim, the file it
must come from, and the row it must come from -- because a figure copied out of the table above
it passes any check that only asks whether the digits appear on disk.
[[a-whitelist-checks-existence-not-placement]] [[describe-the-artifact-from-the-artifact]]

Run: python3 tracecheck.py   (exits non-zero on any mismatch)
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
J = lambda n: json.load(open(os.path.join(HERE, n)))
T = lambda n: open(os.path.join(HERE, n)).read()

r, fc, dt, rd = J("results.json"), J("forkcheck_summary.json"), T("distinctness.txt"), T("README.md")
fails = []


def chk(label, ok, detail=""):
    print(f"  {'OK  ' if ok else 'FAIL'}  {label}{'  ' + detail if detail else ''}")
    if not ok:
        fails.append(label)


# --- the arm table: README cell must equal results.json, and appear in README as a table row ---
for arm, dr, fe, di, ac, pct in [
    ("shallow", 300, 299, 63, 9, "14.29"), ("deep", 174, 174, 4, 0, "0.00"),
    ("b_shallow", 300, 298, 178, 41, "23.03"), ("b_deep", 300, 300, 11, 3, "27.27"),
]:
    s = r["stats"][arm]
    chk(f"{arm}: counts match results.json",
        (s["drawn"], s["fetched"], s["distinct"], s["active"]) == (dr, fe, di, ac),
        f"{(s['drawn'], s['fetched'], s['distinct'], s['active'])}")
    calc = f"{100 * s['active'] / s['distinct']:.2f}" if s["distinct"] else None
    chk(f"{arm}: README rate {pct}% is recomputed, not copied", calc == pct, f"recomputed {calc}%")
    # the row must exist in README with these cells adjacent, not merely somewhere in the file
    chk(f"{arm}: README table row present",
        bool(re.search(rf"\|\s*{dr}\s*\|\s*{fe}\s*\|\s*\*\*{di}\*\*\s*\|\s*{ac}\s*\|\s*{pct}%", rd)))

# --- distinctness: every README row must be a real row of distinctness.txt ---
A = [(1, 152, 59), (2, 94, 8), (3, 53, 3), (4, 100, 2), (5, 74, 3)]
B = [(1, 298, 178), (5, 83, 5), (6, 51, 4), (7, 13, 4), (8, 30, 5), (9, 75, 8), (10, 48, 3)]
for lbl, rows in (("A", A), ("B", B)):
    for page, n, d in rows:
        chk(f"{lbl} page {page}: {d}/{n} in distinctness.txt",
            bool(re.search(rf"^\s*{page}\s+{n}\s+{d}\s", dt, re.M)))
        chk(f"{lbl} page {page}: {d}/{n} quoted in README", f"({d}/{n})" in rd)

# --- fork check ---
chk("fork: 0 of 40", fc["pct_fork"] == 0.0 and fc["sampled"] == 40 and "**0 of 40.**" in rd)
chk("fork: group sizes 105/101",
    fc["by_group"]["A-deep"]["group_size"] == 105 and fc["by_group"]["B-deep"]["group_size"] == 101
    and "105 repos" in rd and "101 repos" in rd)

# --- instrument control: the classifier still reproduces directpay's published numbers ---
chk("instrument unchanged", r["instrument"] == r["published"], str(r["instrument"]))
chk("README quotes 1,256/879/163", "1,256 fetched / 879 distinct / 163" in rd)

# --- p-values: README rounds them; check against the computed value, not against itself ---
for arm, quoted in (("A", 0.42), ("B", 0.75)):
    p = r["test"][arm]["p"]
    chk(f"p-value {arm} = {quoted}", abs(p - quoted) < 0.005, f"computed {p:.4f}")

# --- directpay's own log must contain every total the README attributes to it ---
log_path = os.environ.get("DIRECTPAY_LOG", "/home/agent/work/directpay/collect.log")
if os.path.exists(log_path):
    log = open(log_path).read()
    for total in ("654", "664", "1124", "456", "33088"):
        chk(f"collect.log contains {total}", total in log)
else:
    print(f"  SKIP  directpay collect.log not readable at {log_path} "
          f"(set DIRECTPAY_LOG) -- the four coverage totals are UNVERIFIED in this run")

print()
if fails:
    print(f"{len(fails)} TRACE FAILURE(S):")
    for f in fails:
        print("  *", f)
    sys.exit(1)
print("every checked number in README.md traces to an artifact")
