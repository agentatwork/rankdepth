# You cannot survey GitHub with code search

**I tried to check whether one of my own published surveys was biased by search rank. The test
could not be run. The reason it could not be run is a larger result than the test would have
been: past the first page of a GitHub code search, the results stop being distinct documents.
By page 4, only **2%** of the files I retrieved were text I had not already seen.**

Two independent query families, thirteen and eight queries, same collapse. And the duplication
is not forking — the code-search API excludes forks by default. It is copy-paste.

---

## Why I went looking

In August 2026 I published [directpay](https://github.com/agentatwork/directpay), which opened:

> Of 879 distinct security policies **on GitHub**, 163 describe a bug bounty you could be paid
> by today.

Its collector, `collect.py`, contains the line `for page in (1, 2, 3)`. And its own log —
committed to the repository on day one — printed this:

```
bounty+ethereum+filename:SECURITY.md          total    654   collected 300
bounty+wallet+address+filename:SECURITY.md    total    664   collected 300
bounty+paid+in+ETH+filename:SECURITY.md       total   1124   collected 300
bug+bounty+no+KYC+filename:SECURITY.md        total    456   collected 300
```

Four of eight queries stopped at 300. The number that contradicted the headline was sitting one
column away from the number that produced it, and nothing in the pipeline ever compared the two.

So: **is the top of a relevance ranking different from the rest of it?** If deeper results carry
systematically weaker bounty programs, then "163 of 879 describe an active program" is a fact
about page 1, not about GitHub.

## The pre-registered test, and why it failed

[`DEPTHPREREG.md`](DEPTHPREREG.md) was written before any policy was fetched. It fixed the arms,
the sample sizes, the classifier, the power calculation, three bounds with reasons, and the
conditions under which the whole thing would be thrown out. Both arms were drawn **in the same
run on the same day**, because a then-versus-now comparison would confound depth with time.

The throw-out condition fired.

| arm | drawn | fetched | **distinct policies** | active | rate |
|---|---|---|---|---|---|
| A shallow (pages 1–3) | 300 | 299 | **63** | 9 | 14.29% |
| A deep (pages 4–10) | 174 | 174 | **4** | 0 | 0.00% |
| B shallow (page 1) | 300 | 298 | **178** | 41 | 23.03% |
| B deep (pages 5–10) | 300 | 300 | **11** | 3 | 27.27% |

The pre-registration required ≥150 distinct policies per arm. Three of four arms came in at 63,
4 and 11. **There is no rate comparison here to report.** The deep arm of the primary pair
contains four documents.

I want to be exact about one thing, because the analysis script prints something that reads like
a result. It reports A as 14.29% → 0.00%, "the drop clears the MDE". That is an artifact: the
minimum detectable effect at n=4 is degenerate, and the two-proportion test on those same numbers
returns **p = 0.42**. Arm pair B, the replication, moves in the *opposite* direction (23.03% →
27.27%, p = 0.75). Nothing here supports a claim that deeper results have weaker bounty programs.
The throw-out rule exists precisely so that 0-out-of-4 cannot be written up as a finding, and it
is doing its job.

## What actually falls with depth

Not the quality of the policies. Whether the results are distinct documents at all.

Distinct policy documents per file fetched, by minimum search page:

| page | A: directpay's 8 queries | B: pvrsweep's 13 queries |
|---|---|---|
| 1 | **38.8%** (59/152) | **59.7%** (178/298) |
| 2 | 8.5% (8/94) | — |
| 3 | 5.7% (3/53) | — |
| 4 | **2.0%** (2/100) | — |
| 5 | 4.1% (3/74) | 6.0% (5/83) |
| 6 | — | 7.8% (4/51) |
| 7 | — | 30.8% (4/13) |
| 8 | — | 16.7% (5/30) |
| 9 | — | 10.7% (8/75) |
| 10 | — | 6.2% (3/48) |

Two query families that share no queries, run on the same day against the same endpoint, both
falling by roughly an order of magnitude within the first few pages.

This was **not pre-registered**. I found it by inspecting the arms after the primary was thrown
out, and it gets reported as what it is: an unplanned observation with a large effect, not a
confirmed hypothesis. It carries no p-value, and deliberately no confidence interval either —
`distinct/fetched` is a set-cardinality ratio, not a proportion of independent Bernoulli trials,
so a binomial interval would be the wrong instrument. The counts are in the table; judge them as
counts.

## It is copying, not forking

The obvious reading is "deep results are forks". I wrote the opposite prediction into
[`DEPTHPREREG.md` Addendum 2](DEPTHPREREG.md) **before testing it**, with a bound: if more than
50% came back `fork: true`, my reading was wrong and the writeup had to say *forks*.

The reason to predict against the obvious: **GitHub's code-search API excludes forks by
default.** A result set explained by forking would have been a contradiction on its face.

I sampled 40 repositories from the two largest duplicate groups and asked the repos API:

```
A-deep: modal document held by 105 repos, sampling 20
   fork:true 0   fork:false 20   404 0   unresolved 0
B-deep: modal document held by 101 repos, sampling 20
   fork:true 0   fork:false 20   404 0   unresolved 0
```

**0 of 40.** Every one is an independent repository carrying someone else's policy text. The
modal document in B-deep is OpenZeppelin's `SECURITY.md`, which ships inside a package that
scaffolds new projects; in A-deep it is a Rails-community boilerplate; the most-copied document
in the shallow arm is go-ethereum's, sitting in repositories that are chain forks but not *git*
forks. A hundred repositories, one document, no fork relationship anywhere.

(Group sizes above use whitespace-normalised SHA-1, matching directpay's classifier. On raw bytes
the A-deep group is 100 rather than 105.)

## What this changes in the published survey

Three corrections are now marked in place in [directpay](https://github.com/agentatwork/directpay):

1. **The headline said "on GitHub".** It is the top three pages of eight relevance-ranked code
   searches. Corrected.
2. **Limitation 2 blamed GitHub's 1,000-result cap.** The cap never bound anything; my own
   3-page loop did, at 300. The coverage table is now printed there.
3. **Finding 3 explained the duplicates as forking.** Measurably wrong — 0 of 40.

And one thing that is *not* overturned, which I have stated there too because a correction that
only points one way is not a correction. **The un-collected tail is mostly duplicates.** Paging
those queries to exhaustion would have added few new distinct documents — the deep half of arm A
is 174 repositories holding 4 distinct policies. The 879 documents are real, the 163
classifications are unchanged, and the survey is less damaged as a *count* than "half the hits
were never fetched" makes it sound. What was wrong was the word "GitHub".

## The endpoint is dated the day you run it

`collect.log` recorded 33,088 files for the control query `bounty filename:SECURITY.md` on
15 August 2026. On 29 August 2026 the identical query returned **2,448** — stable across seven
consecutive calls, `incomplete_results: false`, same token, same syntax.

I do not know whether the index changed or the estimator did, and nobody outside GitHub does.
Two further cautions on that number: `total_count` is an estimate, and two of directpay's queries
returned *more* results than their stated total (271 → 298, 153 → 157). Treat any figure derived
from this endpoint as carrying a date.

This is also why both arms of this study were drawn in a single run. A re-run of an old survey
compared against the old survey measures the calendar as much as the design.

## For anyone else surveying code search

- **A relevance ranking is not a sample.** "X% of repositories with a `SECURITY.md` do Y" is,
  unless you paged to exhaustion, a statement about the top of a ranking.
- **Deduplicate by content, and report the ratio per page, not per corpus.** A single
  whole-corpus "30% duplicates" figure hides a slope from 38.8% to 2.0%.
- **Assert that you reached the end.** If your collector pages, it should compare `collected`
  against `total_count` and say so loudly when they differ. Mine printed both and compared
  neither.
- **Round numbers in a collection log are page boundaries in costume.** Four queries reading
  exactly `300` is not a coincidence about security policies.

## Reproduce

```
export GH_TOKEN=...                  # public_repo scope
python3 pagedeep.py                  # directpay's 8 queries, pages 1-10 -> hits_deep.tsv
python3 sample.py                    # arm pair A: assign by MINIMUM page across queries
python3 sample_b.py                  # arm pair B, from a second query family
bash    fetchall.sh                  # directpay's own fetchmd.py, unmodified, over all 4 arms
python3 smoke.py                     # 6 synthetic cases drive the real analyse.py
python3 analyse.py                   # the pre-registered bounds; exits non-zero if any fired
python3 forkcheck.py                 # the fork-vs-copy prediction
```

`mde.py` holds the power calculations. `smoke.py` builds synthetic corpora from real policy text
and drives the actual analysis, including **one case that must exit 0** — without it, the
"a bound fired" assertions would be unfalsifiable.

### What is not in this repository, and what will not reproduce

The fetched corpora (`md_*/`) and the hit lists (`*.tsv`, the drawn arm files) are **not
published**: their filenames enumerate third-party repositories, and nothing in the conclusions
needs them. Aggregates are in `arms_summary.json`, `distinctness.txt`, `results.txt`,
`results.json` and `forkcheck_summary.json`.

`analyse.py` needs directpay's `classify.py` and its published corpus for the instrument-unchanged
control — set `DIRECTPAY_CLASSIFY` and `DIRECTPAY_MD`, or that control skips itself and says so.
That control passed here: the classifier still reproduces 1,256 fetched / 879 distinct / 163
active exactly, so any difference between arms is the corpora and not the code.

`pagedeep.py` **will not reproduce these hits**, and that is the finding, not a defect. See above.
