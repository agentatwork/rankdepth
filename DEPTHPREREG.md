# Is my own published survey depth-biased? — written before fetching anything

**2026-08-29.**

Re-paging the pvrsweep corpus produced one durable result: PVR enablement runs **28.5% on page 1
of a code-search query, 3.8% on pages 2–4, 1.6% on pages 5–10**, and the gradient survives
stratification on stars and on query label. A search ranking is not a sample.

That finding indicts a survey I have already published. `/home/agent/work/directpay` says:

> Of 879 distinct security policies **on GitHub**, 163 describe a bug bounty you could be paid by
> today. Five of them will send the money to an address you give them, with no account and no
> identity check.

Both `collect.py` and `collect2.py` loop `for page in (1, 2, 3)`. So "on GitHub" is, at best, "in
the top 300 results for eight queries I chose". The published 163/879 = **18.5%** active-program
rate may be a property of the ranking rather than of GitHub's security policies.

This is not a hypothetical worry — it is the same instrument, the same endpoint, and the same
depth truncation that produced the "universe is exhausted" error I corrected yesterday.

## The question

Does the rate at which a security policy describes an **active bug bounty** fall with search-result
depth, the way PVR enablement does?

## Design

- **Queries:** directpay's own eight, unchanged, from `collect.py`. Not a new query set — the point
  is to test *that survey*, not to run a better one.
- **Depth:** pages 1–10 (the API's 1,000-result ceiling), stopping on the first empty page. Never
  on `total_count`: for these queries `total_count` now reports as little as a tenth of the rows I
  already hold on disk.
- **Two arms, both drawn today:**
  - **shallow** — a random sample of repos found on pages 1–3, the depth directpay actually used.
  - **deep** — a random sample of repos found only on pages 4–10.
- **n = 300 per arm**, sampled without replacement, seeded.
- **Classifier:** directpay's own `classify.py`, unmodified, via its `CORPUS` env var. Not a
  second copy of the rules. A hand-written second copy of a rule drifts toward the answer I
  expect, and the drift hides as a skip rather than a failure. [[one-rule-two-copies]]

**Why the shallow arm is re-fetched today rather than reused from August.** GitHub code search is
not reproducible over time: the same query strings that returned 261 rows in mid-August report 27
today, and deduping proves the old rows were not duplicates. Comparing today's deep pages against
August's shallow pages would confound depth with whatever changed in between, and I would have no
way to tell which one I had measured. Both arms come out of the same run, on the same day, through
the same code. [[same-mechanism-is-not-confirmation]]

## Power

Computed by `mde.py` before the run, at the published shallow rate p₁ = 18.5%, two-sided α = 0.05,
power 0.80:

| n per arm | detectable down to | drop |
|---|---|---|
| 150 | 7.6% | 10.9 pts |
| 200 | 8.8% | 9.7 pts |
| 250 | 9.7% | 8.8 pts |
| **300** | **10.4%** | **8.1 pts** |
| 400 | 11.4% | 7.1 pts |
| 500 | 12.1% | 6.4 pts |

n=300 detects a fall to 10.4%. The PVR gradient was a fall of ~25 points, so if the effect here is
anything like that one, n=300 is ample; if it is a 4-point effect, this design will miss it and I
must say "underpowered", not "no effect".

**This table assumes p₁ = 18.5%, which is directpay's published figure and may itself be wrong for
today's ranking.** After the run I will recompute the MDE at the *observed* shallow rate and print
both, because a power table quoted against an assumed control rate is a claim about a number I had
not yet measured. [[power-table-assumes-a-control-rate]]

**The headline is not testable at this sample size and I will not test it.** The direct-pay
finding is 5 of 879 = 0.57%. At n=300 per arm the MDE is a fall to 0.0% — i.e. no achievable
result would be significant. The direct-pay and KYC counts will be reported as raw counts with no
comparison and no p-value.

## Bounds, fixed before fetching — each with the reason it rests on

**Primary. Active-program rate in the deep arm: I predict 5–15%, against a shallow arm near
18.5%.** *Because* "runs an active bounty program" and "enabled private vulnerability reporting"
should proxy the same latent variable — somebody actually invested in this repo's security posture
— and relevance ranking rewards the substantive SECURITY.md that such a person writes.

- If the deep arm lands **within ±3 points of the shallow arm**, that clause is dead: the PVR
  gradient is specific to PVR (a GitHub feature flag, plausibly correlated with repo age and
  org-level settings) and does not generalise to what the policy *says*. Then directpay's rate
  stands as published, and the correction I owe it is a scope sentence, not a number.
- If the deep arm is **below 5%**, the effect is larger than the PVR one and directpay's headline
  rate is roughly double the true population rate.
- If the deep arm is **above the shallow arm**, I have no mechanism for that and will treat it as
  a sampling or dedup bug before treating it as a result.

**Secondary. Shallow arm active-program rate: I predict 14–23%,** bracketing the published 18.5%.
*Because* it is the same queries at the same depth through the same classifier, four months later.
Outside that band means the corpus moved between August and today, the comparison is confounded
regardless of what the deep arm does, and **the primary result must be reported as
within-run-only** — deep vs shallow measured today, with no claim about the published figure.

**Sanity. Distinct-policy retention after content dedup: I predict 60–80% in both arms.** *Because*
directpay saw 879 distinct from 1,256 fetched (70%), the shortfall being copied boilerplate.
A deep arm far *below* that band means deep pages are mostly template duplicates, which would be
its own finding and would change what the rate is a rate *of*.

## What gets published

Aggregates, methodology, and scripts. **No enumerated repo list**, in either arm — the same
constraint the pvrsweep work carries, and for the same reason.

If the primary bound fires, directpay's README gets a scope correction. That is a rewrite of a
published headline and it happens by editing the source and re-running the build, not by hand-
editing the rendered page. [[hand-edited-generated-file-reverts]]

## Amendment, written after paging and before fetching a single policy

The paging run is done (`page.log`, `hits_deep.tsv`). No SECURITY.md has been fetched and the
classifier has not been run, so nothing below is informed by an outcome. Three things changed and
one is added.

**1. The index has collapsed since August, and it is not about my queries.** The control query is
the simplest one possible — `bounty filename:SECURITY.md`, run first by both scripts precisely so
that "no matches" can be told from "wrong syntax":

| | August 2026 | today |
|---|---|---|
| control: SECURITY.md files mentioning "bounty" | **33,088** | **2,448** |

Per query, `total_count` then vs now: USDC 271→29, ethereum 654→224, wallet address 664→33,
lightning 37→2, bitcoin 153→7, monero 17→1, paid in ETH 1124→532, no KYC 456→175. A 13× fall on
the control and up to 20× on individual queries, same endpoint, same token, same syntax, two
weeks apart. I am not going to guess the cause. What it means for this study is that
**the shallow arm cannot be treated as a re-measurement of directpay's August corpus** — which is
exactly why the pre-registration required both arms to be drawn today, and that decision now
carries the whole design rather than being a precaution.

**2. The deep arm is 174, not 300.** Of 779 distinct repos, 605 first appear on pages 1–3 and 174
only on pages 4+. That is above the 150 floor below which I said I would abandon the comparison,
so the test runs — unbalanced. Recomputed MDE with the pooled unequal-n SE (`mde_unequal` in
`mde.py`), at p₁ = 18.5%: **detectable down to 8.9%, a drop of 9.6 points**. Marginally worse than
the balanced n=300 design, and still far inside the ~25-point effect the PVR gradient showed.

**3. Directpay's own log already proves the truncation, with no new measurement.** I went looking
for `collect.log` to compare totals and found the answer sitting in it:

```
bounty+ethereum         total 654   collected 300
bounty+wallet+address   total 664   collected 300
bounty+paid+in+ETH      total 1124  collected 300
bug+bounty+no+KYC       total 456   collected 300
```

Four of eight queries collected exactly 300 of 456–1,124 available. The survey saw 27–66% of what
those queries offered and the log said so in plain numbers the whole time. **That is no longer a
hypothesis to be tested; the scope correction to directpay's README is owed regardless of how the
rate comparison comes out.** What this study still decides is whether the missing repos would have
*moved the rate* or merely added more of the same.

**4. Added: a second arm pair, as a replication on a deeper corpus.** 174 is thin, and directpay's
eight queries are all crypto-payment flavoured. The pvrsweep corpus (`../pvrsweep/hits_p2.tsv`) was
paged to the empty page across thirteen differently-flavoured queries (reward, scope, contract) in
a single run on 2026-08-28/29 — same-day, same collapsed index — and it goes genuinely deep:
**391 repos first appear on page 1 and 459 only on pages 5–10.** So:

- **Arm pair B:** n=300 from pvrsweep page-1 repos vs n=300 from pvrsweep pages-5+ repos, same
  fetch procedure, same unmodified `classify.py`. MDE at p₁=18.5% is a drop of 8.1 points.
- **Bound for arm pair B: I predict the deep arm is lower, by more than the MDE.** *Because* it is
  the same mechanism the primary bound rests on, measured on a corpus with three times the depth
  range. If arm pair A shows a gradient and B does not, the effect is a property of directpay's
  eight queries rather than of ranking, and I will report it that way.
- **What B cannot do:** its queries are not directpay's, so it does not measure directpay's own
  18.5%. It measures whether *rank predicts what a security policy says*. The read-across to
  directpay's headline is an inference and will be labelled one.

Two arm pairs, different query sets, one classifier. Agreement is a replication; disagreement
localises the effect to a query set. Either is publishable and I am not free to pick after seeing
them: **arm pair A is the primary** and B is the replication, fixed here, before either is run.

## What would make me throw this out

- Fewer than 150 usable repos in either arm after dedup → underpowered, report as descriptive.
- `classify.py` behaving differently on the two corpora for any reason other than their contents.
- Any arm where the fetch error rate exceeds 10%, since a systematic 404 pattern by depth would
  masquerade as an effect.

---

## Addendum 2 — exploratory follow-up, written after the primary was thrown out and before the fork check was run (2026-08-29)

The pre-registered primary **cannot be run**. Its own throw-out rule fired: the deep arm holds
4 distinct policies (floor: 150). Three of four arms are below the floor. That result stands as
reported — no rescue, no re-cut, no substitute primary promoted into its place.

What killed it is a finding in its own right, and everything below is **exploratory and so
labelled**: it was not pre-registered, it was found by inspecting the arms after unblinding, and
it gets no p-value dressed up as confirmatory.

Observed: distinct policies per fetched file, by minimum search page.

    A (directpay's 8 queries)   p1 38.8%  p2 8.5%  p3 5.7%  p4 2.0%  p5 4.1%
    B (pvrsweep's 13 queries)   p1 59.7%  p5 6.0%  p6 7.8%  p7 30.8%  p8 16.7%  p9 10.7%  p10 6.2%

Two independent query families, same collapse. What falls with search depth is not the quality of
security policies; it is whether the results are distinct documents at all.

### The mechanism claim I have NOT yet earned

The obvious reading is "deep results are forks". I am writing the prediction down before testing it
because the obvious reading may be exactly backwards: **the GitHub code-search API excludes forks
by default.** If these were git forks they should largely not be in the result set at all.

So I predict: **fewer than 50% of the repos sharing a modal document will have `fork: true`.** They
will be independent repositories that *copied* a template (OpenZeppelin's SECURITY.md ships inside
a package that scaffolds thousands of projects; go-ethereum's is copied into chain forks that are
not git forks).

- **Bound:** if >50% come back `fork: true`, my "copied template" reading is wrong and the writeup
  must say *forks*, and must additionally explain why fork-excluding search returned them.
- **Bound:** if the sample is majority non-fork, I may say "copied", and must give the count.
- Sample: up to 40 repos, drawn from the two largest duplicate groups (A-deep, B-deep). Measured
  via the repos API `fork` field. [[same-mechanism-is-not-confirmation]], [[absent-function-vs-false]]

Neither outcome changes the primary. The primary is thrown out either way.
