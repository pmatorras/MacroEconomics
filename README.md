# IMF Macroeconomics Toolkit

A lightweight toolkit to fetch IMF WEO data, generate indicator plots, and launch an interactive Dash dashboard, organized for reuse across CLI and app workflows.

### Features

- Data fetch: downloads country, indicator metadata, and timeseries from the IMF Datamapper API and writes versioned CSVs into the data folder with a release tag inferred from date logic.
- Plotting: creates per‑indicator Plotly HTML charts for selected countries, with a dashed/solid style boundary at the latest projection year and a clean legend treatment.
- Dashboard: Dash app with country and indicator dropdowns plus a year range slider, rendering the same plot logic interactively via a registered callback.


### Project structure

- common.py: central paths and defaults, including DATA_DIR, FIGURE_DIR, chosen_indicators, countries_iso3, and an ensure_dirs() helper for directory creation.
- data.py: IMF API helpers and data_main(args) to fetch metadata and timeseries, deduplicate/validate rows, and write CSV outputs with a computed release tag.
- plot.py: utilities to resolve the latest CSV triplet, validate requested codes, and plot indicators with makePlotly; plot_main(args) orchestrates reading, filtering, and writing HTML charts.
- dash_app.py: builds the Dash app, prepares in‑memory frames and metadata, registers update_graph as the callback, and exposes main(debug, host, port) to run the server.
- main.py: CLI dispatcher with subcommands to fetch, plot, and run the Dash app by delegating into data_main, plot_main, and dash_app respectively.


### Setup

- Dependencies are inferred from imports: requests (HTTP), pandas (dataframes), plotly (charts), dash (web app).
- Directory layout assumes a src layout with the package and that common.ROOT_DIR points to the repository root via Path(__file__).resolve().parents for data/ and figures/.


### Quick start

- From the repository root, ensure the package is importable and paths resolve by running commands with python -m; the commands below call the CLI defined in main.py.
- Before writing outputs, ensure data and figures folders exist; the CLI will call ensure_dirs() if present, or create on write as needed.


### Commands

- Fetch IMF data:
python -m macroeconomics fetch --indicators NGDPD,PCPIEPCH --countries ESP,FRA,DEU.
    - Writes imf_weo_countries_{tag}.csv, imf_weo_indicators_{tag}.csv, and imf_weo_timeseries_{tag}[suffix].csv to DATA_DIR based on latest_weo_release_tag.
- Generate plots:
python -m macroeconomics plot --countries ESP,FRA,DEU.
    - Reads the latest CSVs, filters by countries, and writes one HTML per indicator to FIGURE_DIR with “plot_{indicator}{suffix}.html”.
- Launch dashboard:
python -m macroeconomics dash --host 127.0.0.1 --port 8050 --debug.
    - Starts a Dash app that loads the latest files, offers country/indicator selection and a year range slider, and renders the figure via update_graph.


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


### Extending

- Add indicators/countries: set via CLI strings like --indicators NGDPD,PCPIEPCH and --countries ESP,FRA,DEU, or adjust defaults in common.py.
- Batch pipeline: combine fetch and plot by invoking the two subcommands sequentially, or add a pipeline subcommand that forwards shared args into data_main and plot_main.