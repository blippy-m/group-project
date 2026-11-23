# Environmental Effects on Salmon Run Populations

> Determine to what degree the number of salmon in yearly salmon runs are impacted by changing water temperatures and human-driven environmental changes in and near freshwater spawning rivers. 

---

## Project Overview

Using data regarding the western coast of Canada, accessed from the Pacific Salmon Foundation's Salmon Data Library. 
Provide a short and concise overview of the project. Mention the problem it solves, the data used, and the key outcomes or findings.

- **Objective:** Determine if there is a correlation between upriver freshwater temperatures, flow discharge, logging, fire, insect damage, agricultural development, urban and industrial development, mining, roads, and salmon run populations
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

- **Title:** se_streamtemp_stations.csv
- **Source:**  Pacific Salmon Foundation's Salmon Data Library via the Pacific Salmon Explorer
- **Description:** Brief overview of the dataset features, size, and format
- **License:** "Pacific Salmon Foundation" (retrieved Nov 2026)
- **Link:** https://salmonexplorer.ca/explore/data/stream-temperature/all-regions/all-species/all-cus/


## Run Timing Data

- **Title:** dataset90_run_timing.csv
- **Source:** Pacific Salmon Foundation's Salmon Data Library via the Pacific Salmon Explorer
- **Description:** Information of when salmon and Steelhead usually enter freshwater to spawn. Gives a relative proportion and estimated percentage.
- **License:** "Pacific Salmon Foundation" (retrieved Nov 2026)
- **Link:** https://salmonexplorer.ca/explore/data/run-timing/all-regions/all-species/all-cus/
---

## Analysis

Describe the notebooks and/or scripts used to perform the analysis. Specify the order in which the code should be run to reproduce the results.

data_prep.ipynb was created and used first in order to process and produce our clean salmon/temp dataframe (water_salmon_clean.csv)

analysis_1.ipynb was created and run second in order to perform initial visualizations and models using our clean salmon/temp data (water_salmon_clean.csv)

---

## Results

Include a short discussion of the findings and what they imply.

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
