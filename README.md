# Environmental Effects on Salmon Run Populations

> Are freshwater habitat pressures associated with differences in observed salmon abundance trends and fluctuations across regions?

---

## Project Overview

Using data regarding the western coast of Canada, accessed from the Pacific Salmon Foundation's Salmon Data Library. 
Provide a short and concise overview of the project. Mention the problem it solves, the data used, and the key outcomes or findings.

- **Objective:** Examine associations between cumulative freshwater habitat pressures and observed spawner-count trends and variability, comparing conservation units within regions while accounting for species. Temperature and flow are not included in this analysis.
- **Domain:** Nature and Global warming
- **Key Techniques:** (e.g., Regression, Classification, Clustering, NLP, Time Series)

---

## Project Structure

```
├── data/                 # Raw and processed data
├── code/                 # Jupyter notebooks and Python scripts
├── reports/              # Generated reports and visualizations
├── requirements.txt      # Dependencies
└── README.md             # Project documentation
```

---

## Salmon Spawner Survey Data

- **Title:** dataset2_spawner_surveys.zip
- **Source:**  Pacific Salmon Foundation's Salmon Data Library via the Pacific Salmon Explorer
- **Description:** Number of spawners observed in freshwater streams. Measures all five salmon species (Chinook, Coho, Chum, Pink, Sockeye) and Steelhead. 
- **License:**  "Pacific Salmon Foundation" (retrieved Oct 2026)
- **Link:** (https://salmonexplorer.ca/explore/data/overview/all-regions/all-species/all-cus/)
  

## Stream Temperatures Data

- **Title:** stream_temp_manual.csv
- **Source:**  Pacific Salmon Foundation's Salmon Data Library via the Pacific Salmon Explorer
- **Description:** Max stream temperature collected manually from PSE and labelled by region.
- **License:** "Pacific Salmon Foundation" (retrieved Nov 2026)
- **Link:** https://salmonexplorer.ca/explore/data/stream-temperature/all-regions/all-species/all-cus/


## Run Timing Data

- **Title:** dataset90_run_timing.csv
- **Source:** Pacific Salmon Foundation's Salmon Data Library via the Pacific Salmon Explorer
- **Description:** Information of when salmon and Steelhead usually enter freshwater to spawn. Gives a relative proportion and estimated percentage.
- **License:** "Pacific Salmon Foundation" (retrieved Nov 2026)
- **Link:** https://salmonexplorer.ca/explore/data/run-timing/all-regions/all-species/all-cus/


## Habitat Threats Data

- **Title:** dataset556_cu_habitat_threats.csv
- **Source:** Pacific Salmon Foundation's Salmon Data Library via the Pacific Salmon Explorer
- **Description:** Cumulative habitat pressures/threats including: forest harvest, fire, insect damage, agriculture, urban & industrial development, roads, and mines.
- **License:** "Pacific Salmon Foundation" (retrieved Nov 2026)
- **Link:** https://salmonexplorer.ca/explore/data/cumulative-pressures/all-regions/all-species/all-cus/
---

## Analysis

Describe the notebooks and/or scripts used to perform the analysis. Specify the order in which the code should be run to reproduce the results.

### Running the updated data-processing notebook locally

Open [code/new_data.ipynb](code/new_data.ipynb) and select a Python kernel with the dependencies in [requirements.txt](requirements.txt). Start the kernel from the repository root or the `code` folder, then run the cells in order.

Data paths are resolved from the repository's `data` folder. The spawner CSV is read directly from `dataset2_spawner_surveys.zip`, so no extraction or personal file-path substitutions are needed. The optional station DBF conversion is shown as documentation because the converted CSV is already included.

The original export cells write `data/spawners_clean.csv` and overwrite `data/region_stats.csv`. The final section builds conservation-unit summaries using [code/cu_summaries.py](code/cu_summaries.py), without changing those earlier regional summaries.

### Conservation-unit summaries

The selected window is **2015–2024**. Observed survey coverage falls from 1,449 stream observations in 2024 to 27 in 2025 and 6 in 2026, so those sparsely represented years are excluded. This is a coverage-based choice, not proof that earlier surveys are complete.

All 413 conservation units in the cleaned source are retained. A fixed panel contains only streams with an observed count in every selected year. Annual panel counts sum those fixed streams; they are **observed-count indices, not estimates of total conservation-unit abundance**. Changing survey methods, quality, and within-stream observation effort can still affect these indices.

The final notebook cells export:

- [reports/survey_coverage_by_year.csv](reports/survey_coverage_by_year.csv): full-history annual observation, stream, and CU counts, with the selected window flagged.
- [reports/cu_annual_observations_2015_2024.csv](reports/cu_annual_observations_2015_2024.csv): observed years for each CU, stream coverage, and fixed-panel annual counts where available. Missing years are not imputed.
- [reports/cu_summaries_2015_2024.csv](reports/cu_summaries_2015_2024.csv): one row per CU, window coverage, number/fraction of streams in the panel, mean/median annual panel count, sample standard deviation, coefficient of variation (SD/mean), trends, and survey-quality composition.

`summary_status` distinguishes a complete stream panel, no complete panel, and no observations in the window. Units without a complete panel retain coverage and quality information but have blank abundance statistics. Zero observed counts are retained; CV and relative trends are undefined when the mean is zero.

For this dataset, 308 CUs have observations in the selected window: 124 have complete panels (481 streams), and 184 do not. Another 105 CUs have no observations in the window. Eligible panels represent Chinook (33 CUs), Chum (15), Coho (21), Sockeye (46), and Steelhead (9). No Pink CU meets the all-ten-years rule, so no pink abundance/trend metrics are produced under this selection. The eligible subset must not be presented as representative of all CUs or all species.

Linear trends are observed counts per calendar year. `trend_pct_of_mean_per_year` is the slope divided by mean annual count, times 100, not a compounded annual growth rate. Pink-salmon slopes are calculated separately for odd/even years, with the pooled slope left blank; their overall SD/CV still includes differences between cycles. Trends are descriptive, without significance or causality claims.

Quality counts/fractions are provided separately for all window observations (`all_quality_*`) and fixed-panel observations (`panel_quality_*`). Categories are High, Medium-High, Medium, Medium-Low, Low, Unknown, and Missing. Missing-value codes are treated as Missing, not Unknown; fractions are blank when there are no observations.

Run focused summary tests from the repository root with:

```powershell
python -m unittest discover -s code -p test_cu_summaries.py
```

### Habitat-pressure analysis and visualization reports

The final section of [code/new_data.ipynb](code/new_data.ipynb) calls [code/habitat_analysis.py](code/habitat_analysis.py) to create PNG charts and CSV tables in `reports`. Use a Python environment with the dependencies in [requirements.txt](requirements.txt). After the CU-summary exports exist, regenerate these reports independently with:

```powershell
python code\habitat_analysis.py
```

All 124 complete-panel CUs match habitat data. Four have a nonzero data-deficient habitat percentage; they are retained with explicit exclusion statuses in [reports/cu_habitat_analysis_2015_2024.csv](reports/cu_habitat_analysis_2015_2024.csv). The primary sample contains **120 fully assessed CUs**. No missing habitat values are interpreted as zero pressure.

The primary predictor is the percentage of CU spawning habitat under moderate/high **cumulative** threat. Pressure-specific causal effects are not estimated. Outcomes are the annual observed-count slope divided by mean annual count (%/year), and the coefficient of variation (SD/mean).

Unweighted descriptive OLS compares `outcome ~ species + region` with the same model plus cumulative pressure, scaled per 10 percentage points. Both models use the same CUs. Coefficients and additional in-sample R-squared are exported, without significance tests or confidence intervals: independence/spatial dependence has not been established, and this is not validated prediction. Regional/species medians summarize individual CUs, not pooled regional populations.

PNG figures show:

- Annual survey coverage and the selected window.
- Regional representation and analysis exclusions.
- CU trends and variability within regions, colored by species.
- Habitat pressure versus each outcome, separated by species and colored by region.
- Adjusted pressure/outcome residuals after accounting for species and region.

CSV tables include the complete merge with exclusion statuses, regional coverage, region/species descriptive summaries, model results and coefficients, adjusted CU observations, and [reports/habitat_analysis_methods_2015_2024.csv](reports/habitat_analysis_methods_2015_2024.csv) documenting definitions and limitations. Some region/species groups are very small; selection, varying survey quality/effort, shared habitats, and habitat snapshots from different years limit interpretation. Pink salmon remain excluded by the complete-panel rule.

Run all directly related tests with:

```powershell
python -m unittest discover -s code -p "test_*.py"
```

data_prep.ipynb was created and used first in order to process and produce our clean salmon/temp dataframe (water_salmon_clean.csv)

analysis_1.ipynb was created and run second in order to perform initial visualizations and models using our clean salmon/temp data (water_salmon_clean.csv)

---

## Results

For the 120 fully assessed fixed-panel CUs, adding cumulative habitat pressure to the species/region baseline increases in-sample R-squared from 0.3355 to 0.3409 for normalized abundance trends, and from 0.2693 to 0.2724 for variability. These are small absolute improvements (approximately 0.54 and 0.31 percentage points). They do not establish environmental causation, statistical significance, or out-of-sample prediction.

See [reports/habitat_model_results_2015_2024.csv](reports/habitat_model_results_2015_2024.csv) for coefficients and model comparisons, and [reports/adjusted_habitat_associations_2015_2024.png](reports/adjusted_habitat_associations_2015_2024.png) for the adjusted descriptive relationships.

---

## Authors

- Jacqueline Muse https://github.com/blippy-m
- Shweta Bodhankar https://github.com/shwetabodhankar
- with initial contributions from Nina Fossen https://github.com/Ninofo

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgements

- Tools/libraries used
- Tutorials or papers referenced
- Inspiration or collaborators
