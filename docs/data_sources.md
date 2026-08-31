# Data sources for draft-pick valuation

**Purpose.** This document scopes the datasets available for predicting individual
NFL player performance, so that `project-hAIl-mary` can identify **underrated draft
picks** — players whose expected production exceeds their draft cost.

Finding an underrated pick requires two independent quantities:

1. **Expected production** — what we think a player will score. Rich, free, and
   well-maintained public data exists for this.
2. **Draft cost** — what the market charges for that player, i.e. average draft
   position (ADP). This is the scarcer half, and it constrains the project more
   than the stats do.

Most public "NFL data" work solves (1) and quietly ignores (2). The gap between
them *is* the edge, so both halves get equal weight below.

---

## TL;DR — recommended starting stack

| Need | Source | Cost | Status |
|---|---|---|---|
| Weekly & seasonal fantasy production | **nflverse** `player_stats` | Free | ✅ Verified |
| Opportunity / usage share | **nflverse** `snap_counts`, `player_stats` | Free | ✅ Verified |
| Expected fantasy points (skill vs. luck) | **ffopportunity** `ep_weekly` | Free | ✅ Verified |
| Player identity crosswalk | **nflverse** `players` | Free | ✅ Verified |
| Injury / availability history | **nflverse** `injuries` | Free | ✅ Verified |
| Role & depth chart | **nflverse** `depth_charts` | Free | ✅ Verified |
| **Draft cost (ADP)** | Fantasy Football Calculator API; our own league platform | Free | ⚠️ Unverified here |
| Rookie priors | **nflverse** `draft_picks`, `combine` | Free | ✅ Verified |

**Access these through [`nflreadpy`](https://nflreadpy.nflverse.com/), not
`nfl_data_py`.** The older `nfl_data_py` package is deprecated — nflverse have
stated that all future development happens in `nflreadpy` and that users should
switch. Neither package is currently declared in this repo's `pyproject.toml`;
adding `nflreadpy` is a prerequisite for any of this work.

---

## How to read this document

Everything below was checked from an automated build environment whose outbound
network is filtered. That produces three distinct states, and conflating them
would be misleading:

- ✅ **Verified** — I downloaded it. HTTP 200, and where noted I inspected the
  actual schema and row counts. These are facts, not claims.
- ⚠️ **Unverified here** — the host is blocked by *this environment's* egress
  policy, so I could not test it. This says nothing about the source's health;
  it is documented as freely available and should be re-checked from a normal
  network before being relied on.
- ❌ **Not found** — a URL I expected to exist returned 404. Usually a naming
  change rather than a missing dataset.

---

## 1. nflverse — the backbone

[nflverse](https://nflreadr.nflverse.com/) is the single most valuable resource
here. It publishes tidy, versioned CSV/Parquet files as GitHub release assets,
refreshed automatically in season. No API key, no scraping, no rate limits.

Base URL pattern:

```
https://github.com/nflverse/nflverse-data/releases/download/<tag>/<file>
```

| Dataset | Tag / file | Verified size | What it gives us |
|---|---|---|---|
| Weekly player stats | `player_stats/player_stats_2024.csv` | 1.7 MB, 53 cols, 5,598 rows | The core target variable |
| Defensive player stats | `player_stats/player_stats_def_2024.csv` | ✅ 200 | IDP scoring, if relevant |
| Player master list | `players/players.csv` (also `.parquet`) | 7.2 MB / 3.3 MB | ID crosswalk across platforms |
| Weekly rosters | `weekly_rosters/roster_weekly_2024.csv` | 14.9 MB | Team, status, age by week |
| Snap counts | `snap_counts/snap_counts_2024.csv` | 16 cols, 26,616 rows | Playing-time share (2012+) |
| Depth charts | `depth_charts/depth_charts_2024.csv` | 3.4 MB | Declared role |
| Injuries | `injuries/injuries_2024.csv` | 16 cols, 6,264 rows | Practice/game status history |
| Next Gen Stats | `nextgen_stats/ngs_receiving.csv.gz` | ✅ 200 | Separation, cushion, air yards (2016+) |
| Draft picks | `draft_picks/draft_picks.csv` | 36 cols, 12,928 rows | Draft capital, all years |
| Combine | `combine/combine.csv` | 894 KB | Athletic testing |
| Play-by-play | `pbp/play_by_play_2024.parquet` | ✅ 200 | Full granularity, 1999+ |
| Contracts | `contracts/historical_contracts.csv.gz` | ✅ 200 | Investment as a role signal |

Per-season files follow `<name>_<year>.csv`; several tags also publish an
all-years file (`combine.csv`, `draft_picks.csv`).

❌ Not found under the names I tried: `pbp_participation_*`, `ftn_charting_*`,
`espn_data/espn_players.csv`. FTN charting data exists but is licensed
separately (see §9) — confirm current tags against the
[nflreadr reference](https://nflreadr.nflverse.com/reference/index.html) rather
than assuming these are gone.

### Why `player_stats` is the important one

I inspected its 53 columns. It ships **fantasy scoring already computed** —
`fantasy_points`, `fantasy_points_ppr` — so there is no need to reimplement
league scoring just to reproduce baseline numbers. More usefully, it carries the
opportunity metrics that separate a genuine breakout from a fluke:

- `target_share`, `air_yards_share`, `wopr` — how much of the offense a player
  commands. A rising target share on flat production is the classic
  buy-low signal.
- `racr`, `pacr`, `dakota` — efficiency ratios that tend to regress, useful for
  identifying players whose *last* season flattered them.
- `passing_epa`, `rushing_epa`, `receiving_epa` — value over expectation.
- Volume: `carries`, `targets`, `receptions`, `attempts`.

A first pass at "underrated" can be built from these alone: find players whose
opportunity metrics rose late last season while their season-long totals — and
therefore their ADP — stayed low.

---

## 2. Expected fantasy points — ffopportunity

[`ffopportunity`](https://ffopportunity.ffverse.com/) applies an XGBoost model to
nflverse play-by-play to estimate how many points an *average* player would have
scored given the same opportunities.

```
https://github.com/ffverse/ffopportunity/releases/download/latest-data/ep_weekly_2024.parquet
```

✅ Verified (both `latest-data` and pinned `v1.0.0-data` tags; `.parquet` and
`.rds`, no `.csv.gz`).

This matters more than its obscurity suggests. **Actual minus expected points is
a direct mispricing signal.** Drafters anchor on last year's actual points; a
player who underperformed his expected points is likely to be cheap *and* due for
positive regression. That is close to a working definition of "underrated."

---

## 3. Draft cost (ADP) — the constrained half

Without ADP we can predict production but cannot identify a *bargain*. Every
candidate here was blocked by this environment's egress filter, so all are
⚠️ **unverified** and need re-checking from a normal network.

| Source | Access | Notes |
|---|---|---|
| [Fantasy Football Calculator](https://help.fantasyfootballcalculator.com/article/42-adp-rest-api) | Free REST API, JSON | Documented free for personal **and commercial** use. Standard/PPR/2QB/dynasty, by league size. Best starting point. |
| [Sleeper](https://docs.sleeper.com/) | Free, no auth | Read-only; ~1,000 calls/min guideline. Player metadata, drafts, leagues. If the league runs on Sleeper this is the ground truth. |
| MyFantasyLeague | Free API | Long-standing ADP export; high-stakes-leaning population. |
| [FantasyPros](https://www.fantasypros.com/nfl/adp/overall.php) | Free tier / API key | Consensus ADP across host sites, plus ECR. API keys are gated. |
| RotoWire, DraftSharks, 4for4 (Underdog) | Web | Useful cross-checks; scraping terms vary. |

**The ADP that matters is the one from the platform we actually draft on.**
Population differs sharply between sources — an FFC mock-draft ADP and an FFPC
high-stakes ADP disagree, and the disagreement is not noise. If our league is on
Sleeper or ESPN, that platform's ADP is the target, and everything else is a
proxy. This is the single most important open question in §12.

**Historical ADP is the real scarcity.** Current-year ADP is easy; ADP *as it
stood before past drafts* is what we need to backtest whether a method actually
found bargains. Options: FFC's API accepts a `year` parameter;
[DynastyProcess](https://github.com/dynastyprocess/data) publishes a
FantasyPros ECR history file. Worth confirming depth early — a strategy we cannot
backtest is a strategy we cannot trust.

---

## 4. Projections and consensus rankings

Consensus projections are useful in two opposite ways: as a **baseline to beat**,
and as the **market view we are trying to disagree with** in a measurable way.

- **FantasyPros** — ECR aggregated across many experts, with tiers and spread
  (best/worst/std-dev). The *spread* is arguably more valuable than the mean:
  high expert disagreement marks genuinely uncertain players, which is where
  mispricing lives.
- **DynastyProcess** — ✅ Verified: `values-players.csv` (42 KB) downloads from
  `raw.githubusercontent.com/dynastyprocess/data/master/files/`. Dynasty-oriented
  trade values, useful as a second market opinion.
- **`ffanalytics`** (R) — scrapes and aggregates projections from many sites.
  R-only, so it would need a bridge or a port.

---

## 5. Rookies and college production

Rookies have no NFL history, so they need their own feature path — and they are
frequently mispriced in both directions.

- **nflverse `draft_picks`** ✅ (36 cols, 12,928 rows) — draft capital is the
  single strongest public rookie prior. Includes `cfb_player_id` for joining to
  college data.
- **nflverse `combine`** ✅ (894 KB) — athletic testing.
- **CollegeFootballData API** ⚠️ — free with a registered key; college box scores
  and advanced stats. Blocked here, not tested.

Decision needed on whether rookies are in scope at all (§12) — they roughly
double the modelling work for a minority of draft picks.

---

## 6. Availability and role context

Games missed is often a larger driver of season-long fantasy points than
per-game skill, and it is systematically underweighted by drafters.

- **`injuries`** ✅ — weekly practice and game status, 2009+.
- **`depth_charts`** ✅ — declared role; a change here is an early usage signal.
- **`snap_counts`** ✅ — 2012+, offense/defense/special-teams snaps and share.
- **`historical_contracts`** ✅ — guaranteed money is a decent proxy for how
  committed a team is to a player's role.

---

## 7. Game situation

- **Betting lines** — nflverse play-by-play already carries `spread_line` and
  `total_line` per game, so implied team totals are available ✅ without a
  separate provider. The Odds API ⚠️ offers a free tier for live odds.
- **Weather / venue** — play-by-play includes `roof` and `surface`. Detailed
  weather needs an external provider, and its effect is mostly a
  weekly-lineup concern rather than a draft one. Low priority.

---

## 8. Paid options

Not recommended for a league project, but recorded for completeness: **PFF** (charting
and player grades), **SportsDataIO / FantasyData** (commercial API), **FTN DVOA**
(team efficiency), **PlayerProfiler** and **4for4** (analytics subscriptions).

The free stack above is genuinely competitive for draft-time analysis. Paid data
mostly buys charting depth that matters more for weekly decisions than for
identifying draft bargains.

---

## 9. Licensing and attribution

nflverse data is published under **CC-BY-SA 4.0**, and data from 2023 onward
requires attribution to **FTN Data via nflverse**. Two practical consequences:

1. Any published output should carry that attribution.
2. CC-BY-**SA** is a share-alike licence. If we redistribute derived datasets,
   the share-alike term may attach. Keeping this repo's *code* separate from any
   redistributed *data* avoids the question entirely — which is a further reason
   not to commit raw data to git (§12).

Package code (`nflreadr`, `nflreadpy`) is MIT; the underlying NFL data is
governed by its own owners' terms. Scraping-based sources (PFR, FantasyPros)
have their own terms that a personal-use project should still respect.

---

## 10. Gaps and risks

- **ADP is the bottleneck**, not player stats. Nothing else on this list is hard
  to get; ADP — especially historical ADP for backtesting — is.
- **Egress**: several key hosts are blocked from this build environment. If CI
  is ever expected to *fetch* data rather than read a cache, this will bite.
- **Small-n problem**: a fantasy season is ~17 games and a draft happens once a
  year. There are only so many independent observations, and it is very easy to
  overfit a model to a handful of seasons. Backtesting discipline matters more
  than model sophistication here.
- **ID joins**: crossing nflverse ↔ ADP sources ↔ college data means matching on
  names. `players.csv` carries cross-platform IDs and should be the hub for every
  join; ad-hoc name matching will silently corrupt results.
- **Survivorship / selection**: players who lost their job mid-season vanish from
  some aggregates. Care needed when computing per-game rates.

---

## 11. A minimal v1 that would actually work

Deliberately small, to get an end-to-end result before adding sophistication:

1. Pull `player_stats` for the last 5–8 seasons via `nflreadpy`.
2. Join `snap_counts` and `depth_charts` for opportunity; `players` for IDs.
3. Pull `ep_weekly` from ffopportunity; compute actual − expected points.
4. Pull current ADP from one source; convert to an expected-points-at-cost
   baseline.
5. Rank by (projection − ADP-implied baseline). Inspect the top 30 by hand — if
   the list is not football-plausible, the model is wrong, not the league.
6. Backtest the same procedure against a prior season's ADP before trusting it.

---

## 12. Open questions on strategy

These change what gets built, and several block meaningful modelling. Grouped by
how much they matter.

### Blocking — these determine what "underrated" even means

1. **What are the league's scoring settings?** PPR, half-PPR, or standard? PPR
   changes which players are undervalued more than almost any modelling choice —
   pass-catching backs and slot receivers move dramatically. Also: any premiums
   (TE premium, first-down bonuses)?
2. **What is the roster structure?** Starting lineup, bench size, and especially
   **superflex / 2QB** — superflex reprices quarterbacks so completely that a
   model built for single-QB is actively misleading.
3. **Redraft, keeper, or dynasty?** This sets the prediction horizon. Redraft
   cares about next season; dynasty needs multi-year trajectories, and age curves
   become central.
4. **Snake or auction?** A snake draft needs a ranked list. An auction needs
   dollar values, which is a different output — a calibrated price, not an order.
5. **Which platform hosts the league?** Determines which ADP is ground truth
   (§3), and whether we can pull league history directly.

### Important — shape the modelling approach

6. **How should "underrated" be defined?** Candidates: projected points minus
   ADP-implied points; value over replacement at position; or probability of
   returning a top-N season at that cost. These give materially different lists.
   I lean toward VOR-based, since it accounts for positional scarcity, but this
   is a real choice.
7. **Are rookies in scope?** They need a separate feature path (§5) and roughly
   double the work. Excluding them for v1 is defensible.
8. **Build projections, or start from consensus?** Building our own is more
   work but fully ours. Starting from FantasyPros consensus and modelling only
   the *deviation* is cheaper, and arguably better aimed — the goal is to
   disagree with the market in specific, defensible places.
9. **How far back should the training window go?** The NFL changes; pre-2018
   passing environments differ meaningfully from today's. More data versus more
   relevant data.
10. **What does success look like?** Backtested accuracy against past seasons, or
    simply a shortlist that survives eyeball scrutiny before draft day? A stated
    metric would keep this honest.

### Repo mechanics

11. **How should data be stored?** I'd suggest *not* committing raw data — fetch
    into a gitignored `data/` cache with a script, keeping the repo code-only.
    This also sidesteps the CC-BY-SA redistribution question (§9). But if
    reproducibility matters more than repo size, committing pinned snapshots is
    the alternative.
12. **Notebooks or pipeline?** The scaffold provides both `notebooks/` and a
    package. Suggest exploration in notebooks, with anything reused promoted
    into `project_hail_mary/` — but worth agreeing before habits set.
13. **Should `nflreadpy` be added to `pyproject.toml`?** No NFL data package is
    currently declared. This is a required first step and I can do it in a
    follow-up PR.
14. **When is the draft?** A hard date changes priorities — it is the difference
    between building a defensible pipeline and getting a usable list in time.

---

## Appendix: verification log

Checked from this build environment on 2026-08-31.

**Downloaded successfully (HTTP 200):** nflverse `players.csv` / `players.parquet`,
`player_stats_2024.csv`, `player_stats_def_2024.csv`, `roster_weekly_2024.csv`,
`snap_counts_2024.csv`, `depth_charts_2024.csv`, `injuries_2024.csv`,
`ngs_receiving.csv.gz`, `ngs_2024_receiving.csv.gz`, `combine.csv`,
`draft_picks.csv`, `play_by_play_2024.csv.gz`, `play_by_play_2024.parquet`,
`historical_contracts.csv.gz`; ffopportunity `ep_weekly_2024.parquet` (`latest-data`
and `v1.0.0-data`); DynastyProcess `values-players.csv`.

**404 under the names tried:** `pbp_participation_2023.csv.gz`,
`ftn_charting_2024.csv.gz`, `espn_data/espn_players.csv`,
`nextgen_stats/ngs_2024_receiving.csv` (the `.gz` form works).

**Blocked by this environment's egress policy — untested, not known to be down:**
`api.sleeper.app`, `docs.sleeper.com`, `fantasyfootballcalculator.com`,
`api.myfantasyleague.com`, `api.collegefootballdata.com`, `site.api.espn.com`,
`api.the-odds-api.com`.
