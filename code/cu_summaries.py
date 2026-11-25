"""Coverage-aware summaries of observed spawner counts, not total CU abundance."""

import numpy as np
import pandas as pd


QUALITY_LABELS = {
    "High": "high",
    "Medium-High": "medium_high",
    "Medium": "medium",
    "Medium-Low": "medium_low",
    "Low": "low",
    "Unknown": "unknown",
    "Missing": "missing",
}


def _linear_trend(annual: pd.DataFrame) -> tuple[float, float]:
    years = annual["year"].to_numpy(dtype=float)
    counts = annual["panel_observed_count"].to_numpy(dtype=float)
    centered_years = years - years.mean()
    slope = float(np.dot(centered_years, counts - counts.mean()) /
                  np.dot(centered_years, centered_years))
    relative_slope = slope / counts.mean() * 100 if counts.mean() > 0 else np.nan
    return slope, relative_slope


def build_cu_summaries(
    spawners: pd.DataFrame, start_year: int, end_year: int
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return full-history coverage, window annual counts, and one row per CU.

    Only streams observed in every selected year contribute to abundance
    statistics. Quality composition is reported for both all window observations
    and the complete-stream panel. Pink trends use separate calendar-year slopes
    for odd and even years.
    """
    if start_year > end_year or end_year - start_year + 1 < 4:
        raise ValueError("Select an ordered window of at least four calendar years.")

    metadata_columns = ["cuid", "region", "species_name", "cu_name_pse"]
    required = metadata_columns + [
        "streamid", "year", "stream_observed_count", "stream_survey_quality"
    ]
    missing = sorted(set(required) - set(spawners.columns))
    if missing:
        raise ValueError(f"Missing required spawner columns: {missing}")
    data = spawners[required].copy()
    if data.empty or data[metadata_columns + ["streamid", "year"]].isna().any().any():
        raise ValueError("Spawner data must contain nonmissing CU, stream, and year identifiers.")
    for column in ["year", "stream_observed_count"]:
        if not pd.api.types.is_numeric_dtype(data[column]) or not np.isfinite(data[column]).all():
            raise ValueError(f"{column} must contain finite numeric values.")
    if (data["year"] % 1 != 0).any() or (data["stream_observed_count"] < 0).any():
        raise ValueError("Years must be integers and observed counts must be nonnegative.")
    if data.duplicated(["cuid", "streamid", "year"]).any():
        raise ValueError("Duplicate CU/stream/year observations require resolution before summarizing.")
    if (data.groupby("cuid")[metadata_columns[1:]].nunique() > 1).any().any():
        raise ValueError("Each CU must have consistent region, species, and name metadata.")
    data["year"] = data["year"].astype(int)
    data["stream_survey_quality"] = (
        data["stream_survey_quality"]
        .replace([-989898, "-989898", "-989898.0"], pd.NA)
        .fillna("Missing")
    )
    unexpected_quality = set(data["stream_survey_quality"]) - set(QUALITY_LABELS)
    if unexpected_quality:
        raise ValueError(f"Unrecognized survey quality categories: {sorted(unexpected_quality)}")

    coverage = data.groupby("year").agg(
        observations=("streamid", "size"),
        conservation_units=("cuid", "nunique"),
        streams=("streamid", "nunique"),
    )
    coverage = coverage.reindex(
        range(data["year"].min(), data["year"].max() + 1), fill_value=0
    ).rename_axis("year").reset_index()
    coverage["selected_window"] = coverage["year"].between(start_year, end_year)

    window = data[data["year"].between(start_year, end_year)]
    if window.empty:
        raise ValueError("No observed spawner counts fall inside the selected window.")
    window_years = end_year - start_year + 1
    stream_years = window.groupby(["cuid", "streamid"])["year"].nunique()
    complete_streams = stream_years[stream_years == window_years].index
    panel = window[window.set_index(["cuid", "streamid"]).index.isin(complete_streams)]

    annual = window.groupby(["cuid", "year"]).agg(
        observed_streams=("streamid", "nunique")
    ).reset_index()
    panel_annual = panel.groupby(["cuid", "year"]).agg(
        panel_streams=("streamid", "nunique"),
        panel_observed_count=("stream_observed_count", "sum"),
    ).reset_index()
    annual = annual.merge(panel_annual, on=["cuid", "year"], how="left", validate="one_to_one")
    annual["panel_streams"] = annual["panel_streams"].fillna(0).astype(int)

    summary = data[metadata_columns].drop_duplicates().set_index("cuid")
    summary["window_start"] = start_year
    summary["window_end"] = end_year
    summary["window_years"] = window_years
    observed = window.groupby("cuid").agg(
        years_observed=("year", "nunique"),
        streams_surveyed=("streamid", "nunique"),
        observations=("streamid", "size"),
        first_observed_year=("year", "min"),
        last_observed_year=("year", "max"),
    )
    summary = summary.join(observed)
    for column in ["years_observed", "streams_surveyed", "observations"]:
        summary[column] = summary[column].fillna(0).astype(int)
    summary["year_coverage_fraction"] = summary["years_observed"] / window_years
    for column in ["first_observed_year", "last_observed_year"]:
        summary[column] = summary[column].astype("Int64")
    summary["panel_streams"] = (
        panel.groupby("cuid")["streamid"].nunique().reindex(summary.index, fill_value=0)
    )
    summary["panel_stream_fraction"] = summary["panel_streams"] / summary["streams_surveyed"].replace(0, np.nan)
    stats = panel_annual.groupby("cuid").agg(
        panel_years=("year", "nunique"),
        mean_annual_panel_count=("panel_observed_count", "mean"),
        median_annual_panel_count=("panel_observed_count", "median"),
        sd_annual_panel_count=("panel_observed_count", "std"),
    )
    summary = summary.join(stats)
    summary["panel_years"] = summary["panel_years"].fillna(0).astype(int)
    summary["cv_annual_panel_count"] = (
        summary["sd_annual_panel_count"] /
        summary["mean_annual_panel_count"].replace(0, np.nan)
    )
    summary["summary_status"] = "complete_stream_panel"
    summary.loc[summary["panel_streams"] == 0, "summary_status"] = "no_complete_stream_panel"
    summary.loc[summary["observations"] == 0, "summary_status"] = "no_observations_in_window"

    for prefix, observations in [("all", window), ("panel", panel)]:
        quality = pd.crosstab(observations["cuid"], observations["stream_survey_quality"])
        quality = quality.reindex(index=summary.index, columns=QUALITY_LABELS, fill_value=0)
        denominator = quality.sum(axis=1).replace(0, np.nan)
        for label, suffix in QUALITY_LABELS.items():
            summary[f"{prefix}_quality_{suffix}_count"] = quality[label]
            summary[f"{prefix}_quality_{suffix}_fraction"] = quality[label] / denominator

    trend_columns = [
        "trend_count_per_year", "trend_pct_of_mean_per_year",
        "odd_trend_count_per_year", "odd_trend_pct_of_mean_per_year",
        "even_trend_count_per_year", "even_trend_pct_of_mean_per_year",
    ]
    summary[trend_columns] = np.nan
    summary["trend_status"] = summary["summary_status"]
    for cuid, series in panel_annual.groupby("cuid"):
        if summary.at[cuid, "species_name"] == "Pink":
            summary.at[cuid, "trend_status"] = "pink_odd_even_trends"
            for parity, remainder in [("odd", 1), ("even", 0)]:
                subset = series[series["year"] % 2 == remainder]
                slope, relative_slope = _linear_trend(subset)
                summary.at[cuid, f"{parity}_trend_count_per_year"] = slope
                summary.at[cuid, f"{parity}_trend_pct_of_mean_per_year"] = relative_slope
        else:
            summary.at[cuid, "trend_status"] = "available"
            slope, relative_slope = _linear_trend(series)
            summary.at[cuid, "trend_count_per_year"] = slope
            summary.at[cuid, "trend_pct_of_mean_per_year"] = relative_slope

    annual = annual.merge(
        summary[["region", "species_name", "cu_name_pse"]].reset_index(),
        on="cuid", how="left", validate="many_to_one",
    )
    return coverage, annual, summary.reset_index()
