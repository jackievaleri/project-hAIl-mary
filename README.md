# project-hAIl-mary

**Finding the underrated draft picks that win fantasy football leagues.**

## What this is

`project-hAIl-mary` is a fantasy football draft research project. The goal is
simple: **identify undervalued players before draft day** — the guys going
later than they should, whose production outpaces where the consensus has them
ranked.

Everyone in the league is looking at the same rankings. The edge is in the
players those rankings get wrong.

## The goal

Surface **underrated draft picks** — players whose expected fantasy production
is meaningfully higher than their draft cost.

Concretely, that means answering questions like:

- Which players are being drafted below their projected point total?
- Where is average draft position (ADP) lagging behind a change in situation —
  a new offensive scheme, a departed starter, an expanded role?
- Which breakout signals (target share, snap share, red-zone usage, efficiency
  on limited volume) actually predict a jump in fantasy production, and which
  are noise?
- Which "sleepers" are genuinely mispriced, and which are just popular sleeper
  picks whose ADP has already caught up?

The output we care about is practical: **a shortlist of players to target in
each round, with the reasoning behind each one**, in time for the draft.

## Approach

1. **Gather** — player stats, usage data, team/depth-chart context, and
   consensus rankings and ADP.
2. **Project** — estimate expected fantasy points for the coming season.
3. **Compare** — measure projected value against draft cost to find the gap.
4. **Rank** — turn the biggest gaps into a round-by-round target list.
5. **Review** — track how the picks actually performed, and feed that back into
   the next draft.

## Status

Early days. The project is scaffolded (see below) but the analysis itself —
data sources, projections, rankings — is still to come. Issues and pull
requests are the place to propose approaches, data sources, or scoring
assumptions.

## League context

Built for our fantasy football league. Scoring settings, roster structure, and
league rules affect which players count as underrated, so those assumptions
should be written down here as the analysis takes shape.

## Project layout

Scaffolded with [`pyds-cli`](https://github.com/ericmjl/pyds-cli), which
generates a standard Python data science project:

```
project_hail_mary/     # the package: analysis code lives here
  preprocessing.py     #   loading and cleaning player/usage data
  models.py            #   projection models
  schemas.py           #   dataframe schemas (pandera)
  utils.py             #   shared helpers
  cli.py               #   command line entry point (typer)
notebooks/             # exploratory analysis
tests/                 # pytest suite
docs/                  # mkdocs documentation site
```

Environments and dependencies are managed with
[pixi](https://pixi.sh/) via `pyproject.toml`; pandas, scikit-learn, pymc,
jax, matplotlib and seaborn are already declared.

## Get started for development

```bash
git clone git@github.com:jackievaleri/project-hAIl-mary
cd project-hAIl-mary
pixi install
```

Common tasks:

```bash
pixi run test         # run the test suite
pixi run lint         # run pre-commit across the repo
pixi run serve-docs   # preview the docs site locally
```

## Contributing

Contributions welcome — especially data sources, projection ideas, and sanity
checks on the assumptions. Open an issue or a pull request.
