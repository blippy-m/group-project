import unittest

import numpy as np
import pandas as pd

from habitat_analysis import adjusted_associations, merge_habitat_data


def sample_data():
    summaries = []
    pressures = []
    for region_number in range(2):
        for species_number in range(2):
            for point in range(6):
                cuid = len(summaries) + 1
                region = f"Region {region_number}"
                species = f"Species {species_number}"
                pressure = 10 + 15 * region_number + 10 * species_number + 5 * point
                keys = {"cuid": cuid, "region": region, "species_name": species}
                summaries.append({
                    **keys, "cu_name_pse": f"CU {cuid}",
                    "summary_status": "complete_stream_panel", "observations": 10,
                    "window_start": 2015, "window_end": 2024,
                    "trend_pct_of_mean_per_year": 2 * pressure / 10 + 3 * region_number - 2 * species_number,
                    "cv_annual_panel_count": 0.04 * pressure / 10 + 0.3 + 0.1 * region_number + 0.2 * species_number,
                })
                pressures.append({
                    **keys, "cumulative_modhipct": pressure, "cumulative_lopct": 100 - pressure,
                    "cumulative_modpct": pressure, "cumulative_hipct": 0, "cumulative_defpct": 0,
                })
    return pd.DataFrame(summaries), pd.DataFrame(pressures)


class HabitatAnalysisTests(unittest.TestCase):
    def test_join_preserves_cus_and_flags_coverage_missing_and_deficient_habitat(self):
        summary, pressures = sample_data()
        summary.loc[0, "summary_status"] = "no_complete_stream_panel"
        pressures = pressures[pressures.cuid != 2].copy()
        pressures.loc[pressures.cuid == 3, "cumulative_defpct"] = 5
        pressures.loc[pressures.cuid == 3, "cumulative_lopct"] -= 5
        extra_region = pressures.iloc[[0]].assign(region="Other region")
        merged = merge_habitat_data(summary, pd.concat([pressures, extra_region]))
        self.assertEqual(len(merged), len(summary))
        self.assertTrue(merged.cuid.is_unique)
        by_cu = merged.set_index("cuid")
        self.assertEqual(by_cu.loc[1, "analysis_status"], "no_complete_stream_panel")
        self.assertEqual(by_cu.loc[2, "analysis_status"], "unmatched_habitat")
        self.assertEqual(by_cu.loc[3, "analysis_status"], "data_deficient_habitat")
        self.assertEqual(merged.analysis_status.eq("eligible").sum(), 21)

    def test_adjustment_recovers_known_per_ten_point_associations(self):
        summary, pressures = sample_data()
        results, coefficients, primary = adjusted_associations(merge_habitat_data(summary, pressures))
        by_outcome = results.set_index("outcome")
        self.assertAlmostEqual(
            by_outcome.loc["trend_pct_of_mean_per_year", "pressure_coefficient_per_10_percentage_points"], 2
        )
        self.assertAlmostEqual(
            by_outcome.loc["cv_annual_panel_count", "pressure_coefficient_per_10_percentage_points"], 0.04
        )
        self.assertTrue(np.allclose(results.with_pressure_r_squared, 1))
        self.assertTrue(results.additional_r_squared.gt(0).all())
        self.assertEqual(len(primary), 24)
        self.assertAlmostEqual(primary["pressure_residual_percentage_points"].mean(), 0)
        self.assertEqual(set(coefficients["model"]), {"species_region_baseline", "baseline_plus_pressure"})

    def test_rejects_duplicate_keys_and_invalid_habitat_percentages(self):
        summary, pressures = sample_data()
        cases = [
            (pd.concat([pressures, pressures.iloc[[0]]]), "unique"),
            (pressures.assign(cumulative_modhipct=101), "between 0 and 100"),
            (pressures.assign(cumulative_modhipct=0), "equal moderate plus high"),
        ]
        for habitat, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                merge_habitat_data(summary, habitat)

    def test_rejects_unidentifiable_pressure_model(self):
        summary, pressures = sample_data()
        pressures["cumulative_modhipct"] = 20
        pressures["cumulative_modpct"] = 20
        pressures["cumulative_lopct"] = 80
        with self.assertRaisesRegex(ValueError, "independent observations"):
            adjusted_associations(merge_habitat_data(summary, pressures))


if __name__ == "__main__":
    unittest.main()
