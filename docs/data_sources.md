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
| **Draft cost (ADP)** | **ESPN** `kona_player_info` (the league's platform) | Free | ⚠️ Unverified here |
| Rookie priors | **nflverse** `draft_picks`, `combine` | Free | ✅ Verified |

**Access these through [`nflreadpy`](https://nflreadpy.nflverse.com/), not
`nfl_data_py`.** The older `nfl_data_py` package is deprecated — nflverse have
stated that all future development happens in `nflreadpy` and that users should
switch. Neither package is currently declared in this repo's `pyproject.toml`;
adding `nflreadpy` is a prerequisite for any of this work.

---

## League settings (confirmed)

Confirmed by @chrisdoering8197 in review of this document. These are not
assumptions — they are the spec, and they narrow the problem considerably.

| Setting | Value | Consequence for the model |
|---|---|---|
| Platform | **ESPN** | ESPN's own ADP is ground truth, not a proxy (§3) |
| Quarterbacks | **1 QB** (not superflex) | QBs stay low-priority; positional scarcity sits at RB/WR |
| Draft type | **Snake** | Output is a *ranked list*, not auction dollar values |
| Horizon | **Redraft** (non-dynasty) | One season ahead. Age curves and rookie upside matter far less |
| Starting lineup | **1 QB, 3 WR, 2 RB, 1 TE, 1 K, 1 DST** | No FLEX; 3 WR slots make WR depth the dominant need |

Two consequences worth stating explicitly:

- **3 WR and no FLEX** means weekly WR demand is high and inflexible. Depth at
  receiver is worth more here than in a 2-WR-plus-FLEX league.
- **K and DST are starting slots**, so they need *some* valuation. They are also
  where the market is laziest, which fits the late-round focus below.

**Where the value is.** The reviewer's steer: this work earns its keep **in the
later rounds, on the weird pickups** — not in re-deriving that the consensus
first-rounders are good. That is a real narrowing of scope and it changes what
"success" means (§12).


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

Without ADP we can predict production but cannot identify a *bargain*. Since the
league drafts on **ESPN**, ESPN's own ADP is the target, and everything else is a
proxy for it.

### 3.1 ESPN — the primary source

ESPN has no documented public API, but its fantasy back end is reachable and
widely used. The relevant call:

```
https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/<year>/players
    ?view=kona_player_info
```

Each player carries an `ownership` object with the two fields that matter:

- **`averageDraftPosition`** — ESPN's ADP, drawn from actual ESPN drafts. This is
  our draft cost.
- **`percentOwned`** — how widely the player is rostered across ESPN leagues,
  and how fast that is moving. This is the closest thing to a live read on
  where ESPN's population is heading.

Practical notes: the endpoint needs an `x-fantasy-filter` JSON header to page and
sort, plus a browser-like `User-Agent`. The
[`espn-api`](https://github.com/cwendt94/espn-api) Python package and
[`ffscrapr`](https://ffscrapr.ffverse.com/articles/espn_getendpoint.html) (R)
both wrap this and are the fastest way in. ⚠️ Unverified from this environment —
`lm-api-reads.fantasy.espn.com` is egress-blocked here, so this needs a first
call from a normal network to confirm shape and headers.

**ESPN's own projections matter beyond ADP.** ESPN surfaces its projections
inside the draft room, so they actively *shape* what our leaguemates do. A player
ESPN projects highly will be drafted earlier in our league regardless of what any
outside model says. That makes ESPN projections useful twice: as a competing
forecast, and as a **predictor of our opponents' behaviour**. Disagreeing with
ESPN is precisely where a pick becomes available at a discount.

### 3.2 Current-year draft trends

Per review: many drafts for this season will already have happened before ours,
and that movement is signal. A single end-of-preseason ADP snapshot throws it
away. We should capture **ADP as a time series**, not a number.

What that buys us:

- **Direction and velocity.** A player drifting from ADP 90 to 60 over three
  weeks is being re-priced by the market in real time. Whether we agree with the
  move determines if he is now overvalued or still cheap.
- **Staleness detection.** ADP lags news. A player whose situation changed days
  ago (a starter ruled out, a depth-chart move) may not have been repriced yet —
  a window that closes.
- **Cross-platform gaps.** Where ESPN ADP disagrees with mock-draft sources, the
  gap is exploitable *in our league specifically*, since our opponents draft on
  ESPN and are anchored to ESPN's board.

The mechanics are simple and worth starting now: **snapshot ADP on a schedule and
keep the history.** Nobody sells us last month's ESPN ADP, so if we do not record
it we cannot use it. A dated file per pull is enough.

| Source | Access | Role |
|---|---|---|
| **ESPN** (`kona_player_info`) | Unofficial, no auth | **Primary.** Our draft cost + `percentOwned` trend |
| [Fantasy Football Calculator](https://help.fantasyfootballcalculator.com/article/42-adp-rest-api) | Free REST API, JSON | Cross-check; live mock drafts; accepts a `year` parameter |
| [Sleeper](https://docs.sleeper.com/) | Free, no auth | Cross-check; trending adds/drops is a fast news proxy |
| [FantasyPros](https://www.fantasypros.com/nfl/adp/overall.php) | Free tier / API key | Consensus ADP across hosts, plus expert spread |
| RotoWire, DraftSharks, FTN | Web | Published daily; useful for sanity-checking our own series |

All ⚠️ unverified here (egress-blocked), and all secondary to ESPN.

**Historical ADP remains the backtesting gap.** Current ADP is easy; ADP *as it
stood before past drafts* is what proves a method actually found bargains. FFC's
API takes a `year` parameter and
[DynastyProcess](https://github.com/dynastyprocess/data) publishes a FantasyPros
ECR history — but neither is ESPN. Worth confirming depth early, and worth
starting our own ESPN snapshot archive immediately regardless, because this
season's history can only be captured while it is happening.

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

**Largely settled by the league being redraft, not dynasty.** Rookie
long-term upside carries little weight when the horizon is one season, so the
college pipeline above is low priority. Draft capital is still worth keeping as a
cheap feature — a first-round rookie RB walking into touches is a real
late-round-ADP opportunity — but building out college production modelling is not
justified for this league.

---

## 6. Availability and role context

Games missed is often a larger driver of season-long fantasy points than
per-game skill, and it is systematically underweighted by drafters.

- **`injuries`** ✅ — weekly practice and game status.
- **`depth_charts`** ✅ — declared role; a change here is an early usage signal.
- **`snap_counts`** ✅ — 2012+, offense/defense/special-teams snaps and share.
- **`historical_contracts`** ✅ — guaranteed money is a decent proxy for how
  committed a team is to a player's role.

### 6.1 Preseason practice participation — asked in review, and the answer is no

**Short answer: not in nflverse, and this is a genuine gap.** I checked the 2024
injuries file directly rather than assuming:

- `game_type` values are `REG` (5,954), `WC`, `DIV`, `CON`, `SB` — **no `PRE`**.
- Weeks run **1–22**, i.e. regular season and playoffs only.
- The earliest `date_modified` is **2024-09-04**, which is after the preseason
  has finished.

The cause is upstream, not a packaging choice: the NFL only *mandates* practice
participation reports during the regular season. There is no official preseason
report for nflverse to mirror.

**Why this matters more than it looks.** The reviewer's instinct is right, and it
lands exactly where this project is aimed. Preseason absences are one of the main
drivers of late-round ADP movement — a backup who takes first-team reps because
the starter is out is precisely the "weird pickup" this project wants to catch,
and that information exists *only* in beat reporting during August.

**Practical substitutes**, none as clean as a structured practice table:

| Substitute | What it gives | Notes |
|---|---|---|
| Sleeper trending adds/drops | Spikes when news breaks | Free, no auth; a fast proxy for "something happened" |
| ESPN `percentOwned` velocity | The same signal, on our own platform | Comes free with the ADP pull (§3.1) |
| Rotowire / Rotoworld player news | Actual beat reporting | Unstructured text; scraping terms apply |
| `depth_charts` weekly diffs | Role changes once they are official | Lags the news but is structured and free |

The honest recommendation: **treat August news as a manual input**, not a
modelled feature. Trying to NLP beat-writer tweets for one draft is poor value.
Watching `percentOwned` velocity and depth-chart diffs, and keeping a short
hand-maintained watchlist, gets most of the benefit for a fraction of the effort.

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
  to get; ADP — especially *historical* ESPN ADP for backtesting — is. And unlike
  the rest, this season's ADP trend is perishable: it can only be captured while
  the season's drafts are happening (§11.3).
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

## 11. Updated plan

Revised after review. The confirmed league settings above and the reviewer's steer —
**ADP-implied points, aimed at the late rounds** — change this from a generic
projection exercise into something much more specific.

### 11.1 The metric: points over ADP-implied expectation

Chosen over value-over-replacement, per review. VOR is genuinely useful for
spotting positional cliffs *during* a live draft, but it is awkward as
preparation because it answers "which position should I take next" rather than
"who is mispriced." The metric we want is:

```
value = projected_points  -  expected_points_at(ADP)
```

where `expected_points_at(ADP)` is a curve fitted across past seasons: given a
player drafted at position *N*, how many fantasy points did players drafted
around *N* actually score? That curve is the market's implicit forecast. A player
whose projection sits well above the curve at his cost is underrated, by
definition and in one number.

Two properties make this the right fit:

- **It is a pre-draft artifact.** It produces a ranked list of names with a
  number attached, readable before the draft, not a decision rule needing live
  board state.
- **It degrades gracefully in the late rounds.** The ADP curve flattens hard
  after ~round 8 — expected points barely differ between pick 100 and pick 140.
  That flatness is exactly why late-round mistakes are cheap for the market to
  make and profitable for us to exploit. A modest projection edge at pick 130
  outranks a large one at pick 8, where the market is efficient and the curve
  steep.

VOR is still worth computing as a *secondary* column for draft-day use. It is
just not the headline.

### 11.2 Steps

1. **Data pull.** `player_stats` for the last 5–8 seasons via `nflreadpy`, joined
   to `snap_counts`, `depth_charts` and `players` for IDs.
2. **Start the ADP archive now.** Snapshot ESPN `kona_player_info`
   (`averageDraftPosition` + `percentOwned`) on a schedule, one dated file per
   pull. This season's trend data is perishable — it cannot be reconstructed
   later. This is the single most time-sensitive item here.
3. **Fit the ADP→points curve** on past seasons, using whatever historical ADP we
   can assemble (§3.2). Confirm the depth available before committing.
4. **Project points** for the coming season. Start simple — prior-year production
   adjusted for opportunity (`target_share`, snap share) and expected points from
   ffopportunity. Sophistication can come later; the curve matters more than the
   projection at first.
5. **Rank by the gap**, then **filter to ADP > ~80** to focus where the reviewer
   expects the value. Inspect the top 30 by hand: if the list is not
   football-plausible, the model is wrong, not the league.
6. **Backtest** the same procedure against a prior season before trusting it.
7. **Track ADP drift** through August and re-run. Late movement is where the
   final edge appears.

### 11.3 Sequencing note

Step 2 is the only step with a deadline attached. Everything else can be built
after the draft and still be useful next year; the ADP time series cannot. If
only one thing gets done this week, it should be the snapshot job.

## 12. Open questions

Most of the original blocking questions were answered in review and have moved to
the "League settings (confirmed)" section and §11. What follows is what
genuinely remains.

### Still blocking

1. **What are the scoring settings?** Still unanswered, and it is now the *only*
   remaining blocker. PPR, half-PPR, or standard changes which players are
   undervalued more than any modelling choice we make — full PPR can move a
   pass-catching back 20+ picks relative to standard. With 3 WR slots and no
   FLEX, the PPR question hits the position we most need to get right. Any
   projection built before this is settled may need redoing.

   Also useful, though not blocking: any bonuses (TE premium, 100-yard games,
   return yardage), since those tend to be where a league's scoring quietly
   diverges from the defaults every public projection assumes.

2. **How many teams, and how many bench spots?** League size sets where
   replacement level falls and therefore how deep "draftable" runs. Bench depth
   determines how many late-round swings we actually get — which, given the
   late-round focus, directly sizes the opportunity.

3. **When is the draft?** This is a scheduling constraint, not a modelling one,
   but it decides how much of §11 is achievable and how long the ADP archive
   gets to run before it is needed.

### Worth confirming

4. **No FLEX, correct?** The roster given (1 QB, 3 WR, 2 RB, 1 TE, 1 K, 1 DST)
   has no flex slot. Confirming this matters because it changes RB/WR
   substitutability at the margin.
5. **How should K and DST be handled?** They are starting slots, so they need
   *some* number. They are also close to unpredictable year over year, and
   modelling them seriously is usually wasted effort. Suggest a minimal
   streaming-oriented treatment and spending the effort on WR depth instead —
   but flagging it rather than silently skipping two starting positions.
6. **Build projections, or model deviation from ESPN's?** Given that ESPN's
   projections visibly shape our leaguemates' behaviour (§3.1), modelling the
   *deviation* from ESPN is arguably better aimed than building projections from
   scratch: it directly targets where our opponents are wrong.

### Repo mechanics

7. **Data storage.** Suggest fetching into a gitignored `data/` cache rather than
   committing raw data — with one deliberate exception: the **ESPN ADP snapshots
   from §11.2 should be committed**. They are small, they are irreplaceable once
   the moment passes, and they are our own observations rather than redistributed
   third-party data, which also keeps clear of the CC-BY-SA question in §9.
8. **`nflreadpy` needs adding to `pyproject.toml`.** No NFL data package is
   currently declared. Prerequisite for everything above; happy to do it in a
   follow-up PR.
9. **Notebooks or pipeline?** Suggest exploration in `notebooks/`, with anything
   reused promoted into `project_hail_mary/`.

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
`lm-api-reads.fantasy.espn.com`, `fantasy.espn.com`, `api.the-odds-api.com`.

**Inspected to answer a review question (§6.1):** `injuries_2024.csv`, 6,215 rows.
`game_type` ∈ {REG 5,954; WC 127; DIV 74; CON 45; SB 15} — no `PRE`. Weeks 1–22.
Earliest `date_modified` 2024-09-04. Conclusion: no preseason practice
participation data in nflverse.
