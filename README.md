# IMF Macroeconomics Toolkit

A lightweight toolkit to fetch IMF WEO data, generate indicator plots, and launch an interactive Dash dashboard, organized for reuse across CLI and app workflows.

### Features 

- Data fetch: downloads country, indicator metadata, and timeseries from the IMF Datamapper API and writes versioned CSVs into the data folder with a release tag inferred from date logic.
- Plotting: 
    - creates per‑indicator Plotly HTML charts for selected countries, with a dashed/solid style boundary at the latest projection year and a clean legend treatment.
    - Interactive european maps for each chosen indicator and year
- Dashboard: Dash app with two tabs:
    1.  One with country and indicator dropdowns plus a year range slider, rendering the same plot logic interactively via a registered callback.
    1. One representing the interactive map of europe, with options to chose from a range of indicators, and years. 

## Table of Contents
- [Project structure](#project-structure)
- [Setup](#setup)
- [Quick start](#quick-start)
    - [Commands](#commands)
    - [Data outputs](#data-outputs)
    - [Plot details](#plot-details)
    - [Dashboard notes](#dashboard-notes)
    - [Troubleshooting](#troubleshooting)
    - [Extending data](#extending-data)

## Project structure

The project structure is as follows:
```
macroeconomics/
├── core/
│ └── common.py # Central paths, defaults, and directory helpers
├── datasets/
│ └── data.py # IMF API integration and CSV generation
├── viz/
│ ├── theme.py # Shared styling, data loading, and theming utilities
│ ├── charts/
│ │ └── timeseries.py # makePlotly: time series chart logic
│ └── maps/
│ ├── geo.py # GeoJSON loading and utility functions
│ ├── europe.py # Mainland Europe clipping and processing
│ └── europe_interactive_map.py
│ # make_europe_map: standalone Plotly & Dash-compatible maps
├── logging_config.py # Logging setup for CLI and app
├── main.py # CLI entry point: fetch, plot, dash subcommands
├── dash_app.py # Dash application: multi-tab layout (Time Series, Map)
└── wsgi.py # WSGI server entry for deployment
````
### Key Components

- **`core/common.py`**: Central configuration including `DATA_DIR`, `FIGURE_DIR`, default indicators, and path management utilities
- **`dataset/data.py`**: IMF API helpers, data validation, deduplication, and CSV output with computed release tags
- **`viz/theme.py`**: Shared data loading, styling utilities, and consistent theming across visualizations
- **`dash_app.py`**: Multi-tab application featuring interactive time series charts and European choropleth maps
- **`main.py`**: CLI dispatcher with subcommands to fetch, plot, and run the Dash app


## Setup
1. **Download the Github repository**
```
git@github.com:pmatorras/MacroEconomics.git
```
2. **Create and activate a virtual environment:**

```
python3 -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```
(this file is ignored by `.gitignore`)

3. **Installing dependencies**:
```
pip install -e.
```
For development, performing `pip install -r requirement.txt` might be required

4. **Environment setup**
- Generate a secure key locally:
```
python -c "import secrets; print(secrets.token_hex(32))"
```
- Create a .env file at the project root and add:
```
SECRET_KEY=<paste a long random value>
```

- Copy the output into SECRET_KEY.
    - If using online tools like [Render.com](https://dashboard.render.com/) allow to define the enviromental variable on their platform, so its not recommended to include `.env` into the Github repository.



This key is used by the Dash/Flask server for session signing. It must be non-empty in production.



## Quick start

- From the repository root, ensure the package is importable and paths resolve by running commands with python -m; the commands below call the CLI defined in main.py.
- Before writing outputs, ensure data and figures folders exist; the CLI will call ensure_dirs() if present, or create on write as needed.


### Commands

- Fetch IMF data:
`python -m macroeconomics fetch --indicators NGDPD,PCPIEPCH --countries ESP,FRA,DEU`.
    - Writes imf_weo_countries_{tag}.csv, imf_weo_indicators_{tag}.csv, and imf_weo_timeseries_{tag}[suffix].csv to `DATA_DIR` based on latest_weo_release_tag.
- Generate time series:
`python -m macroeconomics plot --countries ESP,FRA,DEU`.
    - Reads the latest CSVs, filters by countries, and writes one HTML per indicator to `FIGURE_DIR` with “plot_{indicator}{suffix}.html”.
- Generate interactive maps:
`python -m macroeconomics map`
    - Reads the latest CSVs, generates one interactive european map where the indicator and the year can be chosen. It is saved into to `FIGURE_DIR` with “plot_{indicator}{suffix}.html”.
- Launch dashboard:
`python -m macroeconomics dash --host 127.0.0.1 --port 8050 --debug`.
    - Starts a Dash app that loads the latest files, with two tabs. One offers country/indicator selection and a year range slider, and renders the figure via update_graph. The other the interactive european map.


### Data outputs

- Release tag: computed by latest_weo_release_tag to pick {year}_april or {year}_october based on the current date and WEO timing.
- CSV schema: timeseries includes columns country, indicator, year, value; metadata files include id and descriptive fields from the IMF responses.


### Plot details

- Indicator styling: dashed lines for years >= latest_year and solid for earlier observations, with duplicated boundary rows to produce continuous style changes.
- Labels/units: y‑axis label derived from indicator units in df_indicators; title annotation uses the indicator’s descriptive label.


### Dashboard notes

- Layout: country and indicator dropdowns, year range slider, and a main graph component, all wired to update_graph via @app.callback.
- Entrypoint: dash_app(debug, host, port) runs app.run; server is also exposed as server for deployments.


### Troubleshooting

- Module not found when running python -m: run from the repo root so the src layout is discoverable, or use an editable install to make imports work from any directory within the venv.
- “update_graph takes N args” errors: ensure the function signature matches the number and order of Inputs/States in the @app.callback decorator for the dashboard.


### Extending data

- Add indicators/countries: set via CLI strings like --indicators NGDPD,PCPIEPCH and --countries ESP,FRA,DEU, or adjust defaults in common.py.
- Batch pipeline: combine fetch and plot by invoking the two subcommands sequentially, or add a pipeline subcommand that forwards shared args into data_main and plot_main.
