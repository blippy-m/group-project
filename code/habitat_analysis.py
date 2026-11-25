"""Descriptive habitat associations for fixed-panel conservation units."""

from pathlib import Path
import textwrap

import numpy as np
import pandas as pd


QUESTION = (
    "Are freshwater habitat pressures associated with differences in observed "
    "salmon abundance trends and fluctuations across regions?"
)
OUTCOMES = {
    "trend_pct_of_mean_per_year": ("trend", "Trend (% of mean observed count per year)"),
    "cv_annual_panel_count": ("variability", "Variability (sample SD / mean observed count)"),
}
KEYS = ["region", "species_name", "cuid"]
PRESSURE_COLUMNS = [
    "cumulative_lopct", "cumulative_modpct", "cumulative_hipct",
    "cumulative_defpct", "cumulative_modhipct",
]


def merge_habitat_data(summary: pd.DataFrame, pressures: pd.DataFrame) -> pd.DataFrame:
    required_summary = KEYS + [
        "cu_name_pse", "summary_status", "observations", "window_start", "window_end",
        *OUTCOMES,
    ]
    for name, frame, required in [
        ("CU summaries", summary, required_summary),
        ("habitat pressures", pressures, KEYS + PRESSURE_COLUMNS),
    ]:
        missing = sorted(set(required) - set(frame.columns))
        if missing:
            raise ValueError(f"{name} is missing required columns: {missing}")
        if frame[KEYS].isna().any().any() or frame.duplicated(KEYS).any():
            raise ValueError(f"{name} must have nonmissing, unique region/species/CU keys.")
    if summary["cuid"].duplicated().any():
        raise ValueError("CU summaries must contain exactly one row per conservation unit.")
    for column in PRESSURE_COLUMNS:
        values = pressures[column]
        if not pd.api.types.is_numeric_dtype(values) or not np.isfinite(values).all():
            raise ValueError(f"{column} must contain finite numeric habitat percentages.")
        if not values.between(0, 100).all():
            raise ValueError(f"{column} must be between 0 and 100.")
    if not np.allclose(pressures[PRESSURE_COLUMNS[:4]].sum(axis=1), 100, atol=1e-6, rtol=0):
        raise ValueError("Low/moderate/high/data-deficient habitat percentages must sum to 100.")
    if not np.allclose(
        pressures["cumulative_modhipct"],
        pressures["cumulative_modpct"] + pressures["cumulative_hipct"],
        atol=1e-6, rtol=0,
    ):
        raise ValueError("Combined moderate/high pressure must equal moderate plus high pressure.")
    valid_statuses = {
        "complete_stream_panel", "no_complete_stream_panel", "no_observations_in_window",
    }
    if not summary["summary_status"].isin(valid_statuses).all():
        raise ValueError("CU summaries contain unrecognized coverage statuses.")
    for column in OUTCOMES:
        if not pd.api.types.is_numeric_dtype(summary[column]):
            raise ValueError(f"{column} must be numeric, with missing metrics represented as NaN.")

    habitat = pressures.rename(columns={"dataset_version": "habitat_dataset_version"})
    merged = summary.merge(habitat, on=KEYS, how="left", validate="one_to_one", indicator=True)
    merged["habitat_match_status"] = np.where(merged["_merge"].eq("both"), "matched", "unmatched")
    merged = merged.drop(columns="_merge")
    merged["analysis_status"] = merged["summary_status"]
    complete = merged["summary_status"].eq("complete_stream_panel")
    matched = merged["habitat_match_status"].eq("matched")
    assessed = merged["cumulative_defpct"].eq(0)
    finite_outcomes = np.isfinite(merged[list(OUTCOMES)]).all(axis=1)
    merged.loc[complete & ~matched, "analysis_status"] = "unmatched_habitat"
    merged.loc[complete & matched & ~assessed, "analysis_status"] = "data_deficient_habitat"
    merged.loc[complete & matched & assessed & ~finite_outcomes, "analysis_status"] = "undefined_abundance_metrics"
    merged.loc[complete & matched & assessed & finite_outcomes, "analysis_status"] = "eligible"
    return merged


def _fit(design: pd.DataFrame, outcome: np.ndarray) -> tuple[np.ndarray, float, np.ndarray]:
    matrix = design.to_numpy(dtype=float)
    if len(matrix) <= matrix.shape[1] or np.linalg.matrix_rank(matrix) < matrix.shape[1]:
        raise ValueError("Insufficient independent observations to estimate the adjusted model.")
    total_squares = float(np.sum((outcome - outcome.mean()) ** 2))
    if total_squares == 0:
        raise ValueError("A constant outcome has no estimable explained-variation comparison.")
    coefficients = np.linalg.lstsq(matrix, outcome, rcond=None)[0]
    residuals = outcome - matrix @ coefficients
    r_squared = 1 - float(np.sum(residuals ** 2)) / total_squares
    return coefficients, r_squared, residuals


def adjusted_associations(
    merged: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Compare region/species baseline OLS with baseline plus cumulative pressure.

    Fits are unweighted, in-sample descriptions. No independence assumption,
    inferential p-values, or causal interpretation is asserted.
    """
    primary = merged[merged["analysis_status"].eq("eligible")].copy()
    if primary.empty:
        raise ValueError("No fully assessed fixed-panel CUs are available for analysis.")
    primary = primary.reset_index(drop=True)
    baseline = pd.get_dummies(primary[["species_name", "region"]], drop_first=True, dtype=float)
    baseline.insert(0, "intercept", 1.0)
    pressure = primary["cumulative_modhipct"].to_numpy(dtype=float) / 10
    full = baseline.assign(pressure_per_10_percentage_points=pressure)
    pressure_coefficients = np.linalg.lstsq(baseline.to_numpy(), pressure, rcond=None)[0]
    primary["pressure_residual_percentage_points"] = (
        pressure - baseline.to_numpy() @ pressure_coefficients
    ) * 10
    results = []
    coefficient_rows = []
    for outcome, (name, _) in OUTCOMES.items():
        values = primary[outcome].to_numpy(dtype=float)
        base_coefficients, base_r_squared, residuals = _fit(baseline, values)
        full_coefficients, full_r_squared, _ = _fit(full, values)
        primary[f"{name}_residual"] = residuals
        results.append({
            "outcome": outcome,
            "conservation_units": len(primary),
            "regions": primary["region"].nunique(),
            "species": primary["species_name"].nunique(),
            "pressure_coefficient_per_10_percentage_points": full_coefficients[-1],
            "baseline_r_squared": base_r_squared,
            "with_pressure_r_squared": full_r_squared,
            "additional_r_squared": full_r_squared - base_r_squared,
            "full_model_parameters": full.shape[1],
            "residual_degrees_of_freedom": len(primary) - full.shape[1],
            "interpretation": "Exploratory in-sample association; not causal or predictive validation",
        })
        for model_name, design, coefficients in [
            ("species_region_baseline", baseline, base_coefficients),
            ("baseline_plus_pressure", full, full_coefficients),
        ]:
            coefficient_rows.extend({
                "outcome": outcome, "model": model_name, "term": term,
                "coefficient": coefficient,
            } for term, coefficient in zip(design.columns, coefficients))
    return pd.DataFrame(results), pd.DataFrame(coefficient_rows), primary


def _regional_tables(merged: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    coverage_rows = []
    for region, group in merged.groupby("region", sort=True):
        coverage_rows.append({
            "region": region,
            "all_cus": len(group),
            "recently_observed_cus": int(group["observations"].gt(0).sum()),
            "complete_panel_cus": int(group["summary_status"].eq("complete_stream_panel").sum()),
            "primary_analysis_cus": int(group["analysis_status"].eq("eligible").sum()),
            "no_recent_observations_cus": int(group["summary_status"].eq("no_observations_in_window").sum()),
            "no_complete_panel_cus": int(group["summary_status"].eq("no_complete_stream_panel").sum()),
            "other_analysis_exclusions_cus": int(
                (group["summary_status"].eq("complete_stream_panel") &
                 ~group["analysis_status"].eq("eligible")).sum()
            ),
        })
    primary = merged[merged["analysis_status"].eq("eligible")]
    regional = primary.groupby(["region", "species_name"]).agg(
        conservation_units=("cuid", "size"),
        median_cumulative_pressure_pct=("cumulative_modhipct", "median"),
        median_trend_pct_of_mean_per_year=("trend_pct_of_mean_per_year", "median"),
        median_cv=("cv_annual_panel_count", "median"),
        trend_q25=("trend_pct_of_mean_per_year", lambda values: values.quantile(0.25)),
        trend_q75=("trend_pct_of_mean_per_year", lambda values: values.quantile(0.75)),
        cv_q25=("cv_annual_panel_count", lambda values: values.quantile(0.25)),
        cv_q75=("cv_annual_panel_count", lambda values: values.quantile(0.75)),
    ).reset_index()
    return pd.DataFrame(coverage_rows), regional


def _charts(
    merged: pd.DataFrame, primary: pd.DataFrame, coverage: pd.DataFrame,
    regional_coverage: pd.DataFrame, models: pd.DataFrame, output: Path, window: str,
) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    regions = sorted(merged["region"].unique())
    species = sorted(primary["species_name"].unique())
    region_colors = dict(zip(regions, plt.get_cmap("tab10").colors))
    species_colors = dict(zip(species, plt.get_cmap("tab10").colors))
    start, end = int(merged["window_start"].iloc[0]), int(merged["window_end"].iloc[0])

    def save(fig, name):
        fig.savefig(output / f"{name}_{window}.png", dpi=180, facecolor="white")
        plt.close(fig)

    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    recent = coverage[coverage["year"] >= start - 5]
    for ax, column, label in [
        (axes[0], "streams", "Observed population-stream IDs"),
        (axes[1], "conservation_units", "Observed conservation units"),
    ]:
        ax.plot(recent["year"], recent[column], marker="o", color="#236b8e")
        ax.axvspan(start - 0.5, end + 0.5, color="#b8ddcb", alpha=0.6, label="Selected window")
        ax.set_ylabel(label)
        ax.grid(alpha=0.2)
        ax.legend()
    axes[1].set_xlabel("Observation year")
    fig.suptitle("Survey coverage, not population abundance")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    save(fig, "survey_coverage")

    fig, ax = plt.subplots(figsize=(13, 9))
    bottom = np.zeros(len(regional_coverage))
    for column, label, color in [
        ("primary_analysis_cus", "Primary analysis", "#236b8e"),
        ("other_analysis_exclusions_cus", "Complete panel; excluded from analysis", "#e5a34b"),
        ("no_complete_panel_cus", "Recent observations; no complete panel", "#91b6a5"),
        ("no_recent_observations_cus", "No recent observations", "#d4d8da"),
    ]:
        counts = regional_coverage[column].to_numpy()
        ax.barh(np.arange(len(regional_coverage)), counts, left=bottom, label=label, color=color)
        bottom += counts
    ax.set_yticks(np.arange(len(regional_coverage)))
    ax.set_yticklabels([textwrap.fill(region, 30) for region in regional_coverage["region"]])
    ax.set_xlabel("Number of conservation units")
    ax.set_title(f"Regional representation and exclusions ({start}-{end})")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2)
    fig.tight_layout()
    save(fig, "regional_coverage")

    region_positions = {region: i for i, region in enumerate(regions)}
    for outcome, (name, label) in OUTCOMES.items():
        fig, ax = plt.subplots(figsize=(13, 9))
        rng = np.random.default_rng(42)
        for species_name in species:
            group = primary[primary["species_name"].eq(species_name)]
            positions = group["region"].map(region_positions).to_numpy() + rng.uniform(-0.22, 0.22, len(group))
            ax.scatter(group[outcome], positions, label=species_name,
                       color=species_colors[species_name], alpha=0.75, s=35)
        counts = primary.groupby("region").size()
        ax.set_yticks(np.arange(len(regions)))
        ax.set_yticklabels([
            textwrap.fill(f"{region} (n={counts.get(region, 0)})", 34) for region in regions
        ])
        if name == "trend":
            ax.axvline(0, color="#777777", linestyle="--", linewidth=1)
        ax.set_xlabel(label)
        ax.set_title(f"Observed {name} across regions ({start}-{end})\nEach point is one eligible CU, not a regional total")
        ax.grid(axis="x", alpha=0.2)
        ax.legend(title="Species")
        fig.tight_layout()
        save(fig, f"regional_{name}")

        rows = (len(species) + 1) // 2
        fig, axes = plt.subplots(rows, 2, figsize=(16, 4 * rows + 3), squeeze=False, sharex=True, sharey=True)
        for ax, species_name in zip(axes.flat, species):
            subset = primary[primary["species_name"].eq(species_name)]
            for region, group in subset.groupby("region"):
                ax.scatter(group["cumulative_modhipct"], group[outcome],
                           color=region_colors[region], alpha=0.8, s=32)
            ax.set_title(f"{species_name} (n={len(subset)})")
            ax.set_xlabel("Moderate/high cumulative habitat pressure (%)")
            ax.set_ylabel(label)
            ax.set_xlim(-3, 103)
            ax.grid(alpha=0.2)
            if name == "trend":
                ax.axhline(0, color="#777777", linestyle="--", linewidth=1)
        for ax in list(axes.flat)[len(species):]:
            ax.set_visible(False)
        handles = [Line2D([], [], color=region_colors[region], marker="o", linestyle="",
                          label=region) for region in regions]
        fig.legend(handles=handles, loc="lower center", ncol=2, fontsize=9)
        fig.suptitle(f"Habitat pressure vs. observed {name} ({start}-{end})\nUnadjusted CU observations, separated by species")
        fig.tight_layout(rect=(0, 0.18, 1, 0.94))
        save(fig, f"pressure_{name}")

    fig, axes = plt.subplots(1, 2, figsize=(16, 8))
    for ax, (outcome, (name, label)) in zip(axes, OUTCOMES.items()):
        for region, group in primary.groupby("region"):
            ax.scatter(group["pressure_residual_percentage_points"], group[f"{name}_residual"],
                       color=region_colors[region], alpha=0.75, s=30)
        coefficient = models.loc[models["outcome"].eq(outcome),
                                 "pressure_coefficient_per_10_percentage_points"].item()
        x = np.array([
            primary["pressure_residual_percentage_points"].min(),
            primary["pressure_residual_percentage_points"].max(),
        ])
        ax.plot(x, coefficient * x / 10, color="#222222", linewidth=2)
        ax.axhline(0, color="#999999", linewidth=0.8)
        ax.axvline(0, color="#999999", linewidth=0.8)
        ax.set_title(f"{name.title()}: coefficient = {coefficient:.4g} per 10 pressure points")
        ax.set_xlabel("Pressure residual (percentage points)\nAfter species and region adjustment")
        ax.set_ylabel(f"{label}\nAfter species and region adjustment")
        ax.grid(alpha=0.2)
    fig.legend(handles=handles, loc="lower center", ncol=2, fontsize=9)
    fig.suptitle(f"Adjusted descriptive associations (n={len(primary)})\nIn-sample OLS; no causal or significance claim")
    fig.tight_layout(rect=(0, 0.21, 1, 0.93))
    save(fig, "adjusted_habitat_associations")


def write_habitat_reports(
    summary: pd.DataFrame, pressures: pd.DataFrame, coverage: pd.DataFrame, output: Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    windows = summary[["window_start", "window_end"]].drop_duplicates()
    if len(windows) != 1 or windows.isna().any().any():
        raise ValueError("The report must use a single nonmissing summary time window.")
    start, end = windows.iloc[0].astype(int)
    window = f"{start}_{end}"
    merged = merge_habitat_data(summary, pressures)
    models, coefficients, primary = adjusted_associations(merged)
    regional_coverage, regional = _regional_tables(merged)
    output.mkdir(parents=True, exist_ok=True)
    for name, table in [
        ("cu_habitat_analysis", merged), ("regional_coverage", regional_coverage),
        ("region_species_analysis", regional), ("habitat_model_results", models),
        ("habitat_model_coefficients", coefficients), ("habitat_adjusted_observations", primary),
    ]:
        table.to_csv(output / f"{name}_{window}.csv", index=False)
    methods = {
        "research_question": QUESTION,
        "time_window": f"{start}-{end}",
        "unit_of_analysis": "One conservation unit; regional figures show individual CUs",
        "primary_pressure": "Percentage of CU spawning habitat under moderate/high cumulative threat",
        "primary_eligibility": "Complete stream panel, matched habitat, zero data-deficient area, finite outcomes",
        "merged_cus": str(len(merged)),
        "primary_cus": str(len(primary)),
        "coverage_status_counts": str(merged["analysis_status"].value_counts().to_dict()),
        "outcomes": "Linear trend divided by mean count (%/year); sample SD divided by mean count",
        "baseline_model": "Outcome ~ categorical species + categorical region",
        "pressure_model": "Baseline + cumulative moderate/high pressure per 10 percentage points",
        "model_weighting": "One CU, one observation; unweighted OLS",
        "r_squared": "In-sample only; additional R-squared is full minus baseline R-squared",
        "inference": "No p-values or confidence intervals; independence and spatial dependence are not established",
        "pink_salmon": "No eligible Pink CUs under the all-years panel rule",
        "survey_limitations": "Fixed streams do not ensure fixed methods, quality, effort, or total CU coverage",
        "habitat_limitations": "Pressure snapshots have differing reference years; not historical environmental time series",
        "selection_limitations": "Eligible CUs are not representative of all CUs, species, or regions; some groups are very small",
        "interpretation": "Exploratory association; not causal attribution or validated prediction",
        "regeneration": "python code\\habitat_analysis.py, after producing the CU-summary CSVs",
    }
    pd.DataFrame(methods.items(), columns=["item", "description"]).to_csv(
        output / f"habitat_analysis_methods_{window}.csv", index=False
    )
    _charts(merged, primary, coverage, regional_coverage, models, output, window)
    return merged, models


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    reports = root / "reports"
    merged, models = write_habitat_reports(
        pd.read_csv(reports / "cu_summaries_2015_2024.csv"),
        pd.read_csv(root / "data" / "dataset556_cu_habitat_threats.csv"),
        pd.read_csv(reports / "survey_coverage_by_year.csv"),
        reports,
    )
    print("Analysis status:", merged["analysis_status"].value_counts().to_dict())
    print(models.to_string(index=False))
    print(f"Saved PNG charts and CSV analysis tables to {reports}")
