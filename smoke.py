#!/usr/bin/env python3
"""Feed synthetic corpora through the REAL analyse.py and assert each halt fires.

    python3 smoke.py

Every bound in DEPTHPREREG.md has code in analyse.py. That is not the same as that code being
able to fire. A bound whose two sides come from a common intermediate, or whose branch is
unreachable, prints "satisfied" over anything -- so each case here constructs an outcome that
must trip a specific rule, and the test fails if the rule stays quiet.

The corpora are real SECURITY.md text run through directpay's real classifier, not stubbed
records: a fixture that bypasses the classifier tests only my arithmetic.
"""
import json, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

# Preflight. Without directpay's classifier every case below fails, and the output is six
# assertion failures that look like broken logic rather than one missing dependency. A test
# suite that cannot tell "your setup is incomplete" from "your code is wrong" wastes the reader's
# time in exactly the situation where they have the least context. [[clone-portability]]
_CLASSIFY = os.environ.get("DIRECTPAY_CLASSIFY", "/home/agent/work/directpay/classify.py")
if not os.path.exists(_CLASSIFY):
    sys.exit(
        f"smoke.py needs directpay's classifier, and it is not at:\n"
        f"    {_CLASSIFY}\n\n"
        f"These fixtures deliberately run real SECURITY.md text through the real classifier --\n"
        f"stubbing it would test only this file's arithmetic. Clone the survey being audited and\n"
        f"point at it:\n\n"
        f"    git clone https://github.com/agentatwork/directpay\n"
        f"    DIRECTPAY_CLASSIFY=$PWD/directpay/classify.py python3 smoke.py\n")

ACTIVE = """# Security Policy
We operate a bug bounty program. Rewards range from $500 to $10,000 depending on severity.
Report to security@example.com and include your wallet address to receive payment.
"""
QUIET = """# Security Policy
Please report vulnerabilities to security@example.com. We aim to respond within 72 hours.
Do not disclose publicly until a fix has shipped.
"""


def build(base, arm, n_active, n_quiet, n_dup=0):
    d = os.path.join(base, f"md_{arm}")
    os.makedirs(d, exist_ok=True)
    repos = []
    for i in range(n_active):
        # Vary the text so texthash does not collapse them into one dup group -- dedup keeps
        # ONE representative per identical file, so identical fixtures would silently reduce
        # every arm to n=1 and every bound would be evaluated on a sample of one.
        open(os.path.join(d, f"org{arm}{i}__active.md"), "w").write(
            ACTIVE + f"\nProgram id {arm}-{i}.\n")
        repos.append(f"org{arm}{i}/active")
    for i in range(n_quiet):
        open(os.path.join(d, f"org{arm}{i}__quiet.md"), "w").write(
            QUIET + f"\nContact id {arm}-{i}.\n")
        repos.append(f"org{arm}{i}/quiet")
    # Byte-identical copies, so the fixture's retention lands inside the 60-80% band the real
    # corpora are expected to show. Without these every synthetic arm retains 100%, the sanity
    # rule fires in every case, and the "a clean run exits 0" assertion becomes unfalsifiable
    # -- a fixture that can only ever see a non-zero exit tests the exit code not at all.
    for i in range(n_dup):
        open(os.path.join(d, f"dup{arm}{i}__copy.md"), "w").write(QUIET)
        repos.append(f"dup{arm}{i}/copy")
    json.dump([{"repo": r, "path": "SECURITY.md"} for r in repos],
              open(os.path.join(base, f"{arm}.json"), "w"))


def run(case, arms, expect_substr, expect_absent=(), want_rc=1):
    base = tempfile.mkdtemp(prefix="rankdepth-smoke-")
    try:
        for arm, spec in arms.items():
            build(base, arm, *spec)
        env = dict(os.environ, RANKDEPTH_DIR=base)
        r = subprocess.run([sys.executable, os.path.join(HERE, "analyse.py")],
                           env=env, capture_output=True, text=True)
        out = r.stdout + r.stderr
        ok = True
        for s in expect_substr:
            if s not in out:
                print(f"  FAIL [{case}] expected to see {s!r}")
                ok = False
        for s in expect_absent:
            if s in out:
                print(f"  FAIL [{case}] did NOT expect {s!r}")
                ok = False
        if want_rc is not None and r.returncode != want_rc:
            print(f"  FAIL [{case}] expected exit {want_rc}, got {r.returncode}")
            ok = False
        print(f"  {'PASS' if ok else 'FAIL'} [{case}] rc={r.returncode}")
        if not ok:
            print("\n".join("      " + l for l in out.splitlines()[-45:]))
        return ok
    finally:
        shutil.rmtree(base, ignore_errors=True)


# (n_active, n_quiet, n_dup) per arm. 300 unique + 130 identical copies retains 301/430 = 70%,
# inside the sanity band, so a clean case really can exit 0. Active rates: 54/301 = 17.9%
# (inside the 14-23% secondary band) and 24/301 = 8.0% (inside the 5-15% primary band, and
# below the 10.0% MDE at n=301/arm, so the drop is powered).
SH = (54, 246, 130)   # 17.94% active
DP = (24, 276, 130)   #  7.97% active
CASES = [
    # Deep far below shallow in both pairs: every bound is satisfied, so this case must exit 0.
    # It is the only case that proves the halts are not simply always-on.
    ("gradient present, nothing fires",
     {"shallow": SH, "deep": DP, "b_shallow": SH, "b_deep": DP},
     ["inside the predicted 5-15% band", "replicates", "no pre-registered rule fired"],
     ["clause is DEAD", "UNDERPOWERED"], 0),
    # Deep equals shallow: the primary null must fire AND be flagged underpowered, since a
    # zero delta can never clear the MDE.
    ("primary null + underpowered",
     {"shallow": SH, "deep": SH, "b_shallow": SH, "b_deep": SH},
     ["clause is DEAD", "null is underpowered", "does NOT clear the MDE"]),
    # Deep above shallow: must be treated as an instrument fault, not a result.
    ("deep higher than shallow",
     {"shallow": SH, "deep": (90, 210, 130), "b_shallow": SH, "b_deep": DP},
     ["suspect the instrument"]),
    # Shallow far outside 14-23%: the primary must be demoted to within-run-only.
    ("shallow outside the secondary band",
     {"shallow": (6, 294, 130), "deep": (3, 297, 130), "b_shallow": SH, "b_deep": DP},
     ["WITHIN-RUN-ONLY"]),
    # Too few policies in an arm: the throw-out rule must fire.
    ("arm below the 150 floor",
     {"shallow": SH, "deep": (10, 90, 0), "b_shallow": SH, "b_deep": DP},
     ["throw-out"]),
    # No duplicates at all: retention 100%, the sanity rule must fire on its own.
    ("retention outside 60-80%",
     {"shallow": (54, 246, 0), "deep": (24, 276, 0), "b_shallow": SH, "b_deep": DP},
     ["sanity: shallow retention"]),
]

print("smoke: driving the real analyse.py over synthetic corpora")
ok = all(run(*c) for c in CASES)
print("\nsmoke:", "all cases pass" if ok else "FAILURES ABOVE")
sys.exit(0 if ok else 1)
