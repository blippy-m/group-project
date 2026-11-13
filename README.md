# Global Warming on Salmon Run Populations

> Determine if the number of salmon in yearly salmon runs are impacted by increasing water temperatures in freshwater spawning rivers. 

---

## Project Overview

Focusing on the Yukon River Basin in Canada. 
Provide a short and concise overview of the project. Mention the problem it solves, the data used, and the key outcomes or findings.

- **Objective:** Determine if there is a correlation between increased upriver freshwater temperatures and salmon run populations
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

## Salmon Population Data

- **Source:**  Pacific Salmon Commission at www.psc.org
- **Description:** Brief overview of the dataset features, size, and format
- **License:**  Pacific Salmon Commission (PSC) www.psc.org (retrieved Oct 2026)
- **Link:** https://psc1.shinyapps.io/salmon-run-size-app/
  

## Yukon Watershed Temperatures Data

- **Source:** Yukon River Panel 
- **Description:** includes water temperatures of multiple rivers within the Yukon River Basin in Canada.
- **License:** "Pacific Salmon Foundation (retrieved Oct 2026)
- **Link:** https://data.salmonwatersheds.ca/result?datasetid=555


## Yukon River Flow and Leval Data

- **Source:** Government of Canada
- **Description:** Yukon River flow and level measured at Whitehorse from 1902 to 2024 (incomplete)
- **License:** 
- **Link:** https://wateroffice.ec.gc.ca/report/data_availability_e.html?type=historical&station=09AB001&parameter_type=Flow+and+Level
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

- Nina Fossen https://github.com/Ninofo
- Jacqueline Muse https://github.com/blippy-m

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgements

- Tools/libraries used
- Tutorials or papers referenced
- Inspiration or collaborators
