# Legacy Matplotlib Scripts

This folder contains legacy plotting code retained for reference. The file `macroeconomics_matplotlib.py` was an earlier approach that:
- generated static charts with Matplotlib,
- relied on manual or ad‑hoc data retrieval,
- saved non‑interactive image outputs.

The current project direction is to:
- automate dataset retrieval and caching,
- generalize transformations across countries and indicators,
- produce interactive Plotly figures and a Dash UI for exploration.

## Why archived instead of deleted?
Keeping this file helps compare implementations and recover snippets (e.g., styling, axes logic, or data-cleaning steps) if needed. It is not part of the supported package API and isn’t used by the CLI or Dash app.

## How to run the legacy script (if needed)
1) Create or activate a Python environment compatible with the historical dependencies.
2) Install typical requirements for Matplotlib workflows:
   - matplotlib
   - pandas
   - numpy
   - python-dateutil
3) Run the script directly (paths and inputs may need adjustment):
