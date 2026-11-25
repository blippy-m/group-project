import unittest

import numpy as np
import pandas as pd

from cu_summaries import build_cu_summaries


def observation(cuid, streamid, year, count, quality="High", species="Chinook"):
    return {
        "cuid": cuid,
        "region": "Test region",
        "species_name": species,
        "cu_name_pse": f"CU {cuid}",
        "streamid": streamid,
        "year": year,
        "stream_observed_count": count,
        "stream_survey_quality": quality,
    }


class ConservationUnitSummaryTests(unittest.TestCase):
    def test_fixed_panel_excludes_changing_coverage_and_preserves_unavailable_units(self):
        rows = [
            observation(1, 10, year, count)
            for year, count in zip(range(2001, 2005), [10, 20, 10, 20])
        ]
        rows += [
            observation(1, 11, 2001, 1000, "-989898"),
            observation(1, 11, 2002, 2000, "Low"),
            observation(2, 20, 2001, 500),
            observation(3, 30, 1999, 100),
        ]
        coverage, annual, summaries = build_cu_summaries(pd.DataFrame(rows), 2001, 2004)
        summary = summaries.set_index("cuid")
        first = summary.loc[1]
        self.assertEqual(first["years_observed"], 4)
        self.assertEqual(first["streams_surveyed"], 2)
        self.assertEqual(first["panel_streams"], 1)
        self.assertEqual(first["median_annual_panel_count"], 15)
        self.assertAlmostEqual(first["sd_annual_panel_count"], np.std([10, 20, 10, 20], ddof=1))
        self.assertAlmostEqual(first["trend_count_per_year"], 2)
        self.assertAlmostEqual(first["trend_pct_of_mean_per_year"], 2 / 15 * 100)
        self.assertEqual(first["all_quality_missing_count"], 1)
        self.assertAlmostEqual(first["all_quality_high_fraction"], 4 / 6)
        self.assertEqual(first["panel_quality_high_fraction"], 1)
        self.assertEqual(annual[annual.cuid == 1]["panel_observed_count"].tolist(), [10, 20, 10, 20])
        self.assertEqual(summary.loc[2, "summary_status"], "no_complete_stream_panel")
        self.assertTrue(pd.isna(summary.loc[2, "median_annual_panel_count"]))
        self.assertEqual(summary.loc[3, "years_observed"], 0)
        self.assertEqual(summary.loc[3, "summary_status"], "no_observations_in_window")
        self.assertTrue(pd.isna(summary.loc[3, "all_quality_high_fraction"]))
        self.assertEqual(coverage.loc[coverage.year == 2000, "observations"].item(), 0)

    def test_pink_trends_separate_cycles_and_zero_mean_has_no_relative_metrics(self):
        rows = [
            observation(1, 10, year, 10 if year % 2 else 100, species="Pink")
            for year in range(2001, 2005)
        ]
        rows += [observation(2, 20, year, 0) for year in range(2001, 2005)]
        _, _, summaries = build_cu_summaries(pd.DataFrame(rows), 2001, 2004)
        summary = summaries.set_index("cuid")
        self.assertEqual(summary.loc[1, "trend_status"], "pink_odd_even_trends")
        self.assertTrue(pd.isna(summary.loc[1, "trend_count_per_year"]))
        self.assertEqual(summary.loc[1, "odd_trend_count_per_year"], 0)
        self.assertEqual(summary.loc[1, "even_trend_count_per_year"], 0)
        self.assertEqual(summary.loc[2, "median_annual_panel_count"], 0)
        self.assertEqual(summary.loc[2, "trend_count_per_year"], 0)
        self.assertTrue(pd.isna(summary.loc[2, "trend_pct_of_mean_per_year"]))
        self.assertTrue(pd.isna(summary.loc[2, "cv_annual_panel_count"]))

    def test_no_complete_panels_still_returns_coverage_and_quality(self):
        data = pd.DataFrame([observation(1, 10, 2001, 10, quality=None)])
        _, annual, summaries = build_cu_summaries(data, 2001, 2004)
        self.assertEqual(summaries.loc[0, "panel_streams"], 0)
        self.assertEqual(summaries.loc[0, "all_quality_missing_fraction"], 1)
        self.assertTrue(pd.isna(summaries.loc[0, "panel_quality_missing_fraction"]))
        self.assertTrue(annual["panel_observed_count"].isna().all())

    def test_rejects_duplicates_invalid_counts_and_unrecognized_quality(self):
        row = observation(1, 10, 2001, 10)
        cases = [
            ([row, row], "Duplicate CU/stream/year"),
            ([{**row, "stream_observed_count": -989898}], "nonnegative"),
            ([{**row, "stream_survey_quality": "Unexpected"}], "Unrecognized survey quality"),
        ]
        for rows, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                build_cu_summaries(pd.DataFrame(rows), 2001, 2004)


if __name__ == "__main__":
    unittest.main()
