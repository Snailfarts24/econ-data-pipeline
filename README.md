# econ-data-pipeline

A Claude skill with guardrails for empirical economics work in Python: downloading, cleaning and merging data with pandas, building panels, and running regressions or causal inference (OLS, fixed effects, difference-in-differences, event studies, IV, double ML).

The main risk in research code is silent errors, not crashes. Examples include a many-to-many merge that duplicates rows, a FIPS code that loses its leading zero, a treatment indicator that is off by a year, or clustering at the wrong level. This skill makes Claude set things up so those errors fail loudly and early.

## What it does

- **Downloads:** raw files are never edited in place. A `MANIFEST.csv` records the source URL, access date and SHA-256 hash of each file. Files are downloaded again only behind an explicit `--refresh` flag.
- **Cleaning:** row counts are logged after every step, and every dropped row needs a stated reason. Each stage's output is saved as parquet.
- **Merges:** every merge states the expected relationship (`1:1`, `m:1`) and match rate in advance, uses `validate=` and `indicator=True`, and reports the match counts. Claude never uses `drop_duplicates()` to make validation pass.
- **Validation:** each cleaning stage ends with a pandera schema check, and the checks live in `tests/` as pytest tests.
- **Estimation:** before writing any estimation code, Claude writes a specification statement covering the estimand, identifying assumption, sample, specification and inference. It flags any choice you haven't made instead of deciding silently.
- **Review pass:** after big changes, the code gets a skeptical referee-style review. If possible this runs in a fresh subagent.

## Contents

| File | Purpose |
|---|---|
| `SKILL.md` | The skill instructions |
| `references/estimation.md` | Package choices (pyfixest, linearmodels, statsmodels, DoubleML), staggered-timing DiD, clustering, IV diagnostics, simulation check |
| `scripts/audit.py` | `audited_merge()`, `assert_unique()` and `log_shape()` helpers to copy into your project |

## Installation

**Claude Code:** clone the repo into your skills directory:

```bash
git clone https://github.com/Snailfarts24/econ-data-pipeline.git ~/.claude/skills/econ-data-pipeline
```

**Claude.ai:** zip the folder, then upload it under Settings → Capabilities → Skills.

## Usage

The skill turns on automatically whenever a task involves a data pipeline, a merge, building a panel, or estimating a regression or treatment effect, so you don't need to invoke it. If the project's `CLAUDE.md` specifies its own directory layout or package choices, those take precedence.

## Companion skill

[econ-learning](https://github.com/Snailfarts24/econ-learning) is a Socratic learning mode for the full research process. When both are installed, econ-learning handles the reasoning checkpoints, and this skill handles implementation once you've settled the reasoning.
