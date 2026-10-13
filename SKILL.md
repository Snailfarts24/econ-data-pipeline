---
name: "econ-data-pipeline"
description: Guardrails for empirical economics work in Python — downloading, cleaning, and merging data with pandas, building panels, and running statistical or causal inference analyses (OLS, fixed effects, difference-in-differences, event studies, IV, double ML). Use this skill whenever a task involves writing or editing a data pipeline, merging datasets, constructing a panel, or estimating a regression or treatment effect, even if the user does not mention validation, checks, or this skill by name.
---

# Econ data pipeline

The main risk in research code is not crashes but silent errors: a many-to-many merge that duplicates rows, a filter that drops a state, a FIPS code that loses its leading zero, a treatment indicator that is off by a year, the wrong level of clustering. None of these raise exceptions, and all of them change results. Everything below exists to make such errors fail loudly and early.

If the project's CLAUDE.md specifies a directory layout, naming convention, or package choice, follow it over the defaults here.

## 1. Downloads

- Save raw files exactly as downloaded under `data/raw/`. Never edit, overwrite, or clean in place.
- Append one row per file to `data/raw/MANIFEST.csv`: filename, source URL, access date, SHA-256 hash. This is the provenance record for the data appendix.
- Skip the download if the file already exists; refresh only behind an explicit flag (e.g. `--refresh`). Agencies revise data, and silently picking up a new vintage makes results irreproducible.

## 2. Cleaning

- Inspect data with `df.info()`, `df.describe()`, `value_counts()`, and `head()`. Never print large frames or full columns: big outputs fill the context window and degrade the rest of the session.
- Call `log_shape()` from `scripts/audit.py` after each transformation step so row counts are visible throughout.
- Every row drop gets a stated reason and a count in the log. An unexplained change in N is a bug until shown otherwise.
- Save each stage's output as parquet under `data/derived/` so later stages can be rerun alone.

## 3. Merges

Use `audited_merge()` from `scripts/audit.py` (copy it into the project, e.g. `src/audit.py`). If writing the merge by hand, reproduce what it does: pass `validate=`, use `indicator=True`, report match counts, and check key uniqueness afterward.

Before every merge:
- State the expected relationship (1:1, m:1) and a rough expected match rate.
- Check that key columns agree in dtype and formatting: zero-padded codes (FIPS, NAICS), string vs. integer, whitespace, case, year as int vs. datetime. Low match rates almost always come from this.

After the merge, compare the actual match rate to the expectation. If it is far off, or `validate` raises, stop and report to the user. Do not call `drop_duplicates()` to make validation pass: that hides the problem instead of fixing it. Ask the user which duplicate is correct, or find out why duplicates exist.

## 4. Validation

- At the end of each cleaning stage, validate the output with a pandera schema: dtypes, allowed ranges, non-null columns, unique keys. Check the installed pandera version before writing the import, since the import path changed across versions.
- Put pipeline checks in `tests/` as pytest tests so a hook can run them after edits.

## 5. Estimation

Before writing any estimation code, write a short specification statement and show it to the user:

- **Estimand**: what effect, for whom (ATT, ATE, LATE, etc.)
- **Identifying assumption**: parallel trends, exclusion restriction, unconfoundedness, etc.
- **Sample**: units, periods, restrictions, final N
- **Specification**: outcome, treatment, controls, fixed effects
- **Inference**: SE type and clustering level, with the reason for that level
- **Event studies**: reference period and endpoint binning

If any part was not specified by the user, flag it instead of choosing silently. Research design choices belong to the user.

Read `references/estimation.md` before estimating. It covers package choices, staggered-timing DiD, clustering, IV diagnostics, and the simulation check.

## 6. Review pass

After nontrivial pipeline or estimation changes, review the code as a skeptical referee. Use a fresh subagent if available, since a reviewer without your reasoning won't share your assumptions. Check:

- Does each merge's key structure match its `validate` argument, and are match rates plausible?
- Are sample restrictions applied before or after constructing variables that depend on the full sample (leads, lags, group means)?
- Is treatment timing coded correctly relative to the outcome period?
- Does the code estimate what the specification statement says?
- Is clustering at the level of treatment assignment?

## Reporting

End each pipeline or analysis task with a brief summary covering:

- rows at each stage
- merge match rates
- rows dropped and why
- the specification statement, if estimation ran
- any check that failed or was skipped
