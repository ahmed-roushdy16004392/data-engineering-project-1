# NYC Affordable Housing and Serious Road Crashes

Data Engineering and Visualization Project 1

We combine two NYC Open Data datasets, completed affordable housing and serious injury road crashes, and ask how both are distributed across the city's 51 council districts from 2022 to 2025. Every result is an association between counts. Nothing here shows that housing causes crashes, or the reverse.

## Live website
https://data-engineering-project-1-deploy-d.vercel.app/

The site is on a free host, so the first visit after a quiet period can take up to a minute to wake up.

## Datasets
- Housing (H2): [Affordable Housing Production by Building](https://data.cityofnewyork.us/Housing-Development/Affordable-Housing-Production-by-Building/hg8x-zxpr/about_data), NYC Open Data
- Crashes (T4): [Serious Injury Response, Tracking and Analysis Program (SIRTA)](https://data.cityofnewyork.us/Transportation/Serious-Injury-Response-Tracking-Analysis-Program-/xeqp-qz8h/about_data), NYC Open Data
- Supporting data: [City Council Districts](https://data.cityofnewyork.us/d/872g-cjhh), NYC Department of City Planning (version 26c)

The two datasets are joined by council district and year, for the full years 2022 to 2025.

## Repository contents
- `app.py`: the interactive Dash website
- `requirements.txt`: Python packages needed to run it
- `Data/`: the cleaned files used by the website and notebooks (`housing_clean.csv`, `crashes_clean.csv`, `panel_district_year.csv`, `panel_borough_year.csv`, `council_districts.geojson`) and the original downloads in `Raw Data/`
- `Notebook/Data_Engineering_Project_1_Finalized.ipynb`: the main notebook with cleaning, integration, and the 10 research questions
- `Notebook/q*_*.ipynb`: each member's own question notebook, kept to show individual commits

## What the project found
- After cleaning, we have 2,957 affordable housing building records (101,249 units) and 11,958 serious crashes (11,033 severe-injury and 925 fatal) for 2022 to 2025.
- Affordable units are very uneven: District 12 completed about 17,000 units, far more than any other district.
- Severe injuries are highest in Districts 8 (358), 3 (324) and 17 (299).
- Across districts, the relation is loose (rank correlation 0.50): the 13 districts with the most affordable units average 245 severe injuries, against 170 for the 13 with the least.
- Inside each district over time, there is almost no relation (rank correlation 0.05), so larger and busier districts having more of both is the more likely explanation.

## Website features
Search bar (district number, street name, or words like "Brooklyn 2022 fatal Friday"), dropdown filters for borough, year, district, construction type, severity and weekday, a Generate Report button, a district map, a ranked bar chart, a housing-versus-injuries scatter plot, a district-group comparison, and a short story and limitations section.

## Run the website locally
```
pip install -r requirements.txt
python app.py
```
Then open the address printed in the terminal (usually http://127.0.0.1:8050). Run it from the repository's top folder so the `Data/` folder is found.

## Team contributions

| Member | Role | Questions |
|---|---|---|
| Ahmed Alaa | Data cleaning and integration (main notebook), the Dash website (`app.py`), repository setup | Questions 1 and 4 |
| Seif Moustapha | Datasets exploration | Questions 2 and 3 |
| Abdelrahman Elakkad | Visualization work | Questions 5 and 6 |
| Steven Elias | Data cleaning and integration | Questions 7 and 9 |
| Omar Nasr | Website deployment | Questions 8 and 10 |

Each member's own notebook is in the `Notebook/` folder, and their commits are in the repository history.

## Main limitations
- All measures are counts, not rates. We have no population, traffic or road-length data.
- About 82% of crashes could be placed in a council district, so district totals are lower bounds. Only about 22% of fatal crashes in 2022 to 2025 have coordinates.
- 17.4% of housing buildings in the original file have no completion date and are left out of year-based views.
- Some crashes recorded at exactly 00:00 may have an unknown time.
- Only street-name endings (such as AVE) were standardised, so other spelling variants of a street can remain separate.

## AI assistance
We used Claude (an AI assistant) for help with the cleaning, charts and website. Every suggestion was run and checked against the real output. See the "Prompts used" section of the main notebook.
