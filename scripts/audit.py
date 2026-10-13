"""Audit helpers for pandas data pipelines.

Copy into the project (e.g. src/audit.py) and import:
    from audit import audited_merge, assert_unique, log_shape
"""
import pandas as pd


def log_shape(df: pd.DataFrame, step: str, keys=None) -> pd.DataFrame:
    """Print row/column counts (and distinct key combos) after a step. Returns df for chaining."""
    msg = f"[{step}] rows={len(df):,} cols={df.shape[1]}"
    if keys is not None:
        msg += f" unique_keys={len(df.drop_duplicates(subset=keys)):,}"
    print(msg)
    return df


def assert_unique(df: pd.DataFrame, keys, name: str = "df") -> pd.DataFrame:
    """Raise if any combination of `keys` appears more than once."""
    dup = df.duplicated(subset=keys, keep=False)
    if dup.any():
        examples = df.loc[dup, keys].head(10).to_string(index=False)
        raise AssertionError(
            f"{name}: {int(dup.sum()):,} rows share duplicated keys {keys}.\n"
            f"Examples:\n{examples}"
        )
    return df


def audited_merge(
    left: pd.DataFrame,
    right: pd.DataFrame,
    on=None,
    how: str = "left",
    validate: str = "m:1",
    name: str = "merge",
    min_match: float | None = None,
    keep_indicator: bool = False,
    **kwargs,
) -> pd.DataFrame:
    """pd.merge with validation, a match report, and an optional match-rate floor.

    validate: '1:1', '1:m', 'm:1', or 'm:m'. Choose the relationship you expect;
              pandas raises MergeError if the keys don't satisfy it.
    min_match: if set, raise when the share of left rows matched falls below it.
    """
    n_left, n_right = len(left), len(right)
    out = left.merge(right, on=on, how=how, validate=validate, indicator=True, **kwargs)

    counts = out["_merge"].value_counts().reindex(
        ["both", "left_only", "right_only"], fill_value=0
    )
    both, left_only, right_only = (int(counts[k]) for k in ["both", "left_only", "right_only"])

    # Share of left rows matched. Exact for validate in {'1:1','m:1'}, where left rows
    # are not duplicated; for '1:m'/'m:m' it counts matched output rows instead.
    if how in ("left", "outer"):
        denom = both + left_only
    else:
        denom = n_left
    match_rate = both / denom if denom else float("nan")

    print(
        f"[{name}] how={how} validate={validate} | left={n_left:,} right={n_right:,} "
        f"out={len(out):,} | both={both:,} left_only={left_only:,} right_only={right_only:,} "
        f"| left match rate={match_rate:.1%}"
    )

    if min_match is not None and match_rate < min_match:
        raise AssertionError(
            f"{name}: left match rate {match_rate:.1%} is below min_match {min_match:.1%}. "
            "Check key dtypes and formatting (zero-padding, str vs int, whitespace, case)."
        )

    if not keep_indicator:
        out = out.drop(columns="_merge")
    return out
