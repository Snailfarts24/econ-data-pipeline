# Estimation reference

## Contents
1. Packages
2. Difference-in-differences and event studies
3. Inference and clustering
4. Instrumental variables
5. Simulation check

## 1. Packages

- **pyfixest**: OLS/Poisson with high-dimensional fixed effects, clustered SEs, wild bootstrap, event studies, heterogeneity-robust DiD estimators. Use this as the default for fixed-effects work.
- **linearmodels**: IV (IV2SLS, IVGMM), PanelOLS, system estimators.
- **statsmodels**: general regression, GLMs, time series, diagnostics.
- **DoubleML**: double/debiased machine learning for treatment effects with many controls.

APIs change across versions. Before writing calls, check the installed version (`python -c "import pyfixest; print(pyfixest.__version__)"`) and the current function signatures. Do not rely on remembered syntax.

## 2. Difference-in-differences and event studies

When treatment adoption is staggered and effects may vary across cohorts or over time, the two-way fixed effects (TWFE) coefficient is a weighted average that can put negative weight on some treatment effects. It can even have the wrong sign. Use a heterogeneity-robust estimator as the main specification and report TWFE only for comparison.

Relevant literature:
- Goodman-Bacon, A. (2021). Difference-in-differences with variation in treatment timing. *Journal of Econometrics*, 225(2), 254–277.
- de Chaisemartin, C., & D'Haultfœuille, X. (2020). Two-way fixed effects estimators with heterogeneous treatment effects. *American Economic Review*, 110(9), 2964–2996.
- Callaway, B., & Sant'Anna, P. H. C. (2021). Difference-in-differences with multiple time periods. *Journal of Econometrics*, 225(2), 200–230.
- Sun, L., & Abraham, S. (2021). Estimating dynamic treatment effects in event studies with heterogeneous treatment effects. *Journal of Econometrics*, 225(2), 175–199.

Event study checklist:
- State the reference period (usually t = −1) and confirm it is omitted.
- State how endpoints are binned or trimmed, and check how many units contribute to each event time.
- Treat never-treated and not-yet-treated control groups as an explicit choice, and state which is used.
- Pre-period coefficients near zero are consistent with parallel trends but do not prove it; low power can hide violations.

## 3. Inference and clustering

- Cluster at the level of treatment assignment by default (e.g. state for a state policy), and state the reason.
  - Abadie, A., Athey, S., Imbens, G. W., & Wooldridge, J. M. (2023). When should you adjust standard errors for clustering? *Quarterly Journal of Economics*, 138(1), 1–35.
- With few clusters (roughly under 40–50) or very unbalanced cluster sizes, report wild cluster bootstrap p-values in addition to standard clustered SEs.
  - Cameron, A. C., Gelbach, J. B., & Miller, D. L. (2008). Bootstrap-based improvements for inference with clustered errors. *Review of Economics and Statistics*, 90(3), 414–427.
- Report the number of clusters alongside N in every table.

## 4. Instrumental variables

- Always report the first stage and a weak-instrument diagnostic. With heteroskedastic or clustered errors, use the effective F statistic rather than the conventional first-stage F.
  - Montiel Olea, J. L., & Pflueger, C. (2013). A robust test for weak instruments. *Journal of Business & Economic Statistics*, 31(3), 358–369.
- Report the reduced form as well; its sign and significance should line up with the IV estimate.
- State the exclusion restriction in words in the specification statement.

## 5. Simulation check

Before trusting an estimator on real data, confirm it recovers a known effect in data with the same structure: the same number of units and periods, a similar adoption pattern, and the same clustering. This catches coding errors (wrong treatment timing, wrong reference period) and estimator problems (TWFE bias under staggered timing) at the same time.

Skeleton: adapt the adoption pattern and effect dynamics to the real design.

```python
import numpy as np
import pandas as pd

def simulate_staggered_panel(n_units=500, n_periods=20, cohorts=(8, 12, 16),
                             effect_growth=0.1, seed=0):
    """Panel with staggered adoption and effects that grow with time since treatment.
    True ATT for each treated unit-period = effect_growth * (t - g + 1)."""
    rng = np.random.default_rng(seed)
    units = np.arange(n_units)
    # assign cohorts; 0 = never treated
    g = rng.choice(list(cohorts) + [0], size=n_units)
    df = pd.DataFrame([(i, t) for i in units for t in range(1, n_periods + 1)],
                      columns=["unit", "time"])
    df["cohort"] = g[df["unit"]]
    unit_fe = rng.normal(size=n_units)[df["unit"]]
    time_fe = rng.normal(size=n_periods)[df["time"] - 1]
    treated = (df["cohort"] > 0) & (df["time"] >= df["cohort"])
    df["treat"] = treated.astype(int)
    df["true_effect"] = np.where(treated, effect_growth * (df["time"] - df["cohort"] + 1), 0.0)
    df["y"] = unit_fe + time_fe + df["true_effect"] + rng.normal(size=len(df))
    return df

sim = simulate_staggered_panel()
true_att = sim.loc[sim["treat"] == 1, "true_effect"].mean()
# Run the planned estimator on `sim` and compare its estimate to true_att.
# Run plain TWFE as well so the user can see the size of any bias.
```

Report: the true ATT, the estimator's estimate, and the TWFE estimate. If the planned estimator misses the truth by more than sampling noise, stop and diagnose before touching real data.
