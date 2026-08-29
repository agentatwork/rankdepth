#!/usr/bin/env python3
"""Classify each arm with directpay's own classifier and evaluate the pre-registered bounds.

    python3 analyse.py           # -> stdout, and results.json

Exits non-zero when a pre-registered rule fires. A rule that is only narrated is
indistinguishable at publication time from one that passed, so every bound in DEPTHPREREG.md
gets code here that computes the quantity, compares it, and halts. [[preregister-the-bound]]
"""
import json, math, os, subprocess, sys

import mde

# Overridable so smoke.py can drive this exact code over synthetic corpora. A fixture that
# reimplements the analysis proves nothing about the analysis. [[preregister-the-bound]]
HERE = os.environ.get("RANKDEPTH_DIR") or os.path.dirname(os.path.abspath(__file__))
CLASSIFY = os.environ.get("DIRECTPAY_CLASSIFY", "/home/agent/work/directpay/classify.py")
ARMS = ["shallow", "deep", "b_shallow", "b_deep"]


def classify_dir(d):
    """Run directpay's classifier over a corpus directory. Not a reimplementation of it -- the
    whole point is that every arm goes through the same published code."""
    env = dict(os.environ, CORPUS=d)
    out = subprocess.run([sys.executable, CLASSIFY, "--json"], env=env,
                         capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit(f"classify.py failed on {d}:\n{out.stderr[-2000:]}")
    return json.loads(out.stdout)


def classify(arm):
    return classify_dir(os.path.join(HERE, f"md_{arm}"))


def wilson(k, n):
    if n == 0:
        return (0.0, 0.0)
    z, p = 1.959964, k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def ztest(k1, n1, k2, n2):
    if not n1 or not n2:
        return None, None
    p1, p2 = k1 / n1, k2 / n2
    pb = (k1 + k2) / (n1 + n2)
    if pb in (0, 1):
        return 0.0, 1.0
    se = math.sqrt(pb * (1 - pb) * (1 / n1 + 1 / n2))
    z = (p1 - p2) / se
    p = math.erfc(abs(z) / math.sqrt(2))
    return z, p


# ------------------------------------------------------------- instrument-unchanged control
# Both arms go through directpay's published classifier. If that classifier no longer produces
# directpay's published numbers on directpay's own corpus, then a difference between my arms
# could be the code rather than the corpora, and I would have no way to tell which.
# Skipped-with-a-shout rather than silently when the corpus is absent, because this script is
# meant to run from a clone too and a check that vanishes quietly reads as one that passed.
# [[clone-portability]]
PUBLISHED = {"fetched": 1256, "distinct": 879, "active": 163}
ctrl_dir = os.environ.get("DIRECTPAY_MD", "/home/agent/work/directpay/md")
instrument = None
if os.path.isdir(ctrl_dir):
    c = classify_dir(ctrl_dir)
    crep = [r for r in c if r["dupe_of"] is None]
    instrument = {"fetched": len(c), "distinct": len(crep),
                  "active": sum(1 for r in crep if r["program"] == "active")}
    same = instrument == PUBLISHED
    print(f"instrument control: classify.py over directpay's own corpus -> "
          f'{instrument["fetched"]}/{instrument["distinct"]}/{instrument["active"]} '
          f'(published {PUBLISHED["fetched"]}/{PUBLISHED["distinct"]}/{PUBLISHED["active"]}) '
          f'-- {"unchanged" if same else "CHANGED"}')
    if not same:
        sys.exit("classify.py no longer reproduces its own published numbers. Any difference "
                 "between the arms could be the code rather than the corpora. Halting.")
else:
    print(f"instrument control: SKIPPED -- {ctrl_dir} not present. The arm comparison below "
          f"is still internally valid, but nothing here has checked that this classifier "
          f"still reproduces the published survey it is being used to audit.")

recs, stats = {}, {}
for arm in ARMS:
    d = os.path.join(HERE, f"md_{arm}")
    if not os.path.isdir(d):
        sys.exit(f"missing corpus {d} -- run fetchall.sh")
    recs[arm] = classify(arm)
    # Fetched counted by walking the directory, not by len(recs): a check whose two sides come
    # from a common intermediate compares something with itself. [[preregister-the-bound]]
    fetched = len([f for f in os.listdir(d) if f.endswith(".md")])
    drawn = len(json.load(open(os.path.join(HERE, f"{arm}.json"))))
    rep = [r for r in recs[arm] if r["dupe_of"] is None]
    active = [r for r in rep if r["program"] == "active"]
    stats[arm] = {
        "drawn": drawn, "fetched": fetched, "distinct": len(rep),
        "retention": len(rep) / fetched if fetched else 0.0,
        "fetch_fail": (drawn - fetched) / drawn if drawn else 0.0,
        "active": len(active),
        "active_rate": len(active) / len(rep) if rep else 0.0,
        "program": {k: sum(1 for r in rep if r["program"] == k)
                    for k in ("active", "planned", "upstream", "none-stated", "unstated")},
        "verdict_active": {k: sum(1 for r in active if r["verdict"] == k)
                           for k in ("direct", "direct-with-identity", "crypto-no-address",
                                     "crypto-with-identity", "platform", "no-bounty", "unclear")},
        "direct_any": sum(1 for r in rep if r["verdict"] == "direct"),
    }

print("=" * 78)
print("ARM SIZES AND OUTCOMES")
print("=" * 78)
print(f'{"arm":11s} {"drawn":>6} {"fetched":>8} {"distinct":>9} {"retain":>7} '
      f'{"active":>7} {"rate":>7}  95% CI')
for arm in ARMS:
    s = stats[arm]
    lo, hi = wilson(s["active"], s["distinct"])
    print(f'{arm:11s} {s["drawn"]:>6} {s["fetched"]:>8} {s["distinct"]:>9} '
          f'{s["retention"]*100:>6.1f}% {s["active"]:>7} {s["active_rate"]*100:>6.2f}%  '
          f'{lo*100:5.2f}-{hi*100:5.2f}%')

print("\nprogram breakdown (distinct policies)")
print(f'{"arm":11s} ' + " ".join(f"{k:>12s}" for k in
      ("active", "planned", "upstream", "none-stated", "unstated")))
for arm in ARMS:
    print(f'{arm:11s} ' + " ".join(f'{stats[arm]["program"][k]:>12d}' for k in
          ("active", "planned", "upstream", "none-stated", "unstated")))

print("\nhow the active programs would pay (raw counts -- NOT tested, see DEPTHPREREG 'Power')")
keys = ("direct", "direct-with-identity", "crypto-no-address", "crypto-with-identity",
        "platform", "no-bounty", "unclear")
print(f'{"arm":11s} ' + " ".join(f"{k[:11]:>12s}" for k in keys))
for arm in ARMS:
    print(f'{arm:11s} ' + " ".join(f'{stats[arm]["verdict_active"][k]:>12d}' for k in keys))

# ---------------------------------------------------------------- cross-corpus consistency
# Throw-out condition: "classify.py behaving differently on the two corpora for any reason
# other than their contents." Arms A and B are drawn from different query sets and do overlap,
# so any repo present in both is the same file classified twice through the same code.
overlap, disagree = 0, []
byrepo = {arm: {r["repo"]: r for r in recs[arm]} for arm in ARMS}
for a, b in (("shallow", "b_shallow"), ("shallow", "b_deep"),
             ("deep", "b_shallow"), ("deep", "b_deep")):
    for repo in set(byrepo[a]) & set(byrepo[b]):
        overlap += 1
        x, y = byrepo[a][repo], byrepo[b][repo]
        if (x["program"], x["verdict"], x["hash"]) != (y["program"], y["verdict"], y["hash"]):
            disagree.append((repo, a, x["program"], x["verdict"], b, y["program"], y["verdict"]))
print(f"\ncross-corpus consistency: {overlap} repos classified in two arms, "
      f"{len(disagree)} disagreements")
for d in disagree[:10]:
    print(f"  DISAGREE {d}")

# ---------------------------------------------------------------------------------- bounds
fired = []
sh, dp = stats["shallow"], stats["deep"]
bs, bd = stats["b_shallow"], stats["b_deep"]
p_sh, p_dp = sh["active_rate"], dp["active_rate"]
p_bs, p_bd = bs["active_rate"], bd["active_rate"]

print("\n" + "=" * 78)
print("PRE-REGISTERED BOUNDS")
print("=" * 78)

# Power recomputed at the OBSERVED shallow rate, not the assumed 18.5%. A power table quoted
# against an assumed control rate is a claim about a number not yet measured.
# [[power-table-assumes-a-control-rate]]
mde_a = mde.mde_unequal(p_sh, sh["distinct"], dp["distinct"]) if p_sh else 0.0
mde_b = mde.mde_unequal(p_bs, bs["distinct"], bd["distinct"]) if p_bs else 0.0
print(f"\nMDE recomputed at observed rates (pre-registration assumed p1=18.5%):")
print(f"  arm pair A: p1={p_sh*100:.2f}% observed, n={sh['distinct']}/{dp['distinct']} "
      f"-> detectable down to {mde_a*100:.2f}% (drop {(p_sh-mde_a)*100:.2f} pts)")
print(f"  arm pair B: p1={p_bs*100:.2f}% observed, n={bs['distinct']}/{bd['distinct']} "
      f"-> detectable down to {mde_b*100:.2f}% (drop {(p_bs-mde_b)*100:.2f} pts)")

zA, pA = ztest(sh["active"], sh["distinct"], dp["active"], dp["distinct"])
zB, pB = ztest(bs["active"], bs["distinct"], bd["active"], bd["distinct"])
print(f"\narm pair A (directpay's queries): {p_sh*100:.2f}% -> {p_dp*100:.2f}%  "
      f"z={zA:.2f}  p={pA:.4g}")
print(f"arm pair B (pvrsweep queries)   : {p_bs*100:.2f}% -> {p_bd*100:.2f}%  "
      f"z={zB:.2f}  p={pB:.4g}")

# Secondary bound is checked FIRST because it decides how the primary may be reported.
print("\n[secondary] shallow-arm active rate in 14-23%?")
if 0.14 <= p_sh <= 0.23:
    print(f"  {p_sh*100:.2f}% -- inside. The primary may be read against directpay's "
          f"published 18.5%.")
else:
    print(f"  {p_sh*100:.2f}% -- OUTSIDE 14-23%. Pre-registered consequence: the corpus moved "
          f"between August and today, so the primary result is WITHIN-RUN-ONLY. It compares "
          f"deep against shallow measured today and makes NO claim about the published figure.")
    fired.append("secondary: shallow arm outside 14-23%, primary is within-run-only")

print("\n[primary] deep-arm active rate vs shallow, arm pair A")
delta = p_dp - p_sh
if abs(delta) <= 0.03:
    print(f"  {p_dp*100:.2f}% vs {p_sh*100:.2f}%, delta {delta*100:+.2f} pts -- WITHIN +/-3 pts. "
          f"The 'shared latent variable' clause is DEAD: the PVR gradient does not generalise "
          f"to what the policy says. directpay's rate stands; it owes a scope sentence, not a "
          f"number.")
    fired.append("primary: null -- deep within +/-3 pts of shallow, clause retracted")
elif delta > 0.03:
    print(f"  {p_dp*100:.2f}% vs {p_sh*100:.2f}%, delta {delta*100:+.2f} pts -- deep is HIGHER. "
          f"Pre-registered: no mechanism for this. Treat as a sampling or dedup bug before "
          f"treating it as a result.")
    fired.append("primary: deep HIGHER than shallow -- suspect the instrument, halt")
elif p_dp < 0.05:
    print(f"  {p_dp*100:.2f}% -- BELOW the predicted 5-15% band, on the low side. The effect is "
          f"larger than the PVR one; directpay's headline rate is roughly double the "
          f"population rate.")
    fired.append("primary: deep below 5% -- effect larger than predicted")
elif p_dp <= 0.15:
    print(f"  {p_dp*100:.2f}% -- inside the predicted 5-15% band, and {-delta*100:.2f} pts below "
          f"shallow. The clause holds.")
else:
    print(f"  {p_dp*100:.2f}% -- above the 15% top of the predicted band but more than 3 pts "
          f"below shallow. Directionally predicted, magnitude over-predicted.")
    fired.append("primary: deep above the 5-15% band")
# The observed drop clears the MDE exactly when p_dp <= mde_a; anything else is a second way of
# writing the same inequality and would only make it possible to get it wrong in one of them.
powered = p_dp <= mde_a
print(f"  detectable at this n down to {mde_a*100:.2f}%; observed deep {p_dp*100:.2f}% -- "
      f"{'the drop clears the MDE' if powered else 'the drop does NOT clear the MDE: report as UNDERPOWERED, not as no effect'}")
if not powered and abs(delta) <= 0.03:
    fired.append("primary: null is underpowered -- cannot distinguish 'no effect' from "
                 "'effect smaller than this design can see'")

print("\n[replication] arm pair B: is deep lower by more than the MDE?")
dB = p_bd - p_bs
if dB < 0 and (p_bs - p_bd) > (p_bs - mde_b):
    print(f"  {p_bd*100:.2f}% vs {p_bs*100:.2f}%, delta {dB*100:+.2f} pts -- replicates.")
else:
    print(f"  {p_bd*100:.2f}% vs {p_bs*100:.2f}%, delta {dB*100:+.2f} pts -- does NOT clear the "
          f"MDE ({(p_bs-mde_b)*100:.2f} pts). Pre-registered: if A shows a gradient and B does "
          f"not, the effect is a property of directpay's eight queries rather than of ranking.")
    fired.append("replication: arm pair B does not replicate")

print("\n[sanity] distinct-policy retention in 60-80%?")
for arm in ARMS:
    r = stats[arm]["retention"]
    flag = "ok" if 0.60 <= r <= 0.80 else "OUTSIDE"
    print(f"  {arm:11s} {r*100:5.1f}%  {flag}")
    if flag == "OUTSIDE":
        fired.append(f"sanity: {arm} retention {r*100:.1f}% outside 60-80%")

print("\n[throw-out] fetch failure rate under 10%, and >=150 usable per arm?")
for arm in ARMS:
    s = stats[arm]
    bad = s["fetch_fail"] > 0.10 or s["distinct"] < 150
    print(f"  {arm:11s} fetch-fail {s['fetch_fail']*100:5.1f}%  distinct {s['distinct']:>4}  "
          f"{'THROW OUT' if bad else 'ok'}")
    if bad:
        fired.append(f"throw-out: {arm} fetch-fail {s['fetch_fail']*100:.1f}% / "
                     f"distinct {s['distinct']}")
if disagree:
    fired.append(f"throw-out: {len(disagree)} cross-corpus classification disagreements")

json.dump({"stats": stats, "instrument": instrument, "published": PUBLISHED,
           "mde": {"A": mde_a, "B": mde_b},
           "test": {"A": {"z": zA, "p": pA}, "B": {"z": zB, "p": pB}},
           "overlap": overlap, "disagree": disagree, "fired": fired},
          open(os.path.join(HERE, "results.json"), "w"), indent=1)

print("\n" + "=" * 78)
if fired:
    print(f"{len(fired)} PRE-REGISTERED RULE(S) FIRED -- the write-up is not free to ignore these:")
    for f in fired:
        print(f"  * {f}")
    print("\nHalting non-zero. Each of these changes what the write-up may claim; that is a "
          "decision to make deliberately, not a warning to scroll past.")
    sys.exit(1)
print("no pre-registered rule fired; the predicted gradient holds in both arm pairs")
