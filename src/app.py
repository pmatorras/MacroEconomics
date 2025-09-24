# app.py
import pandas as pd
from dash import Dash, dcc, html, Input, Output
import macroeconomics as m
import common

# Load latest files and prepare data
latest_files, latest_year = m.find_latest_files_and_year(common.DATA_FOLDER, prompt_on_mismatch=False)

TIMESERIES_FILE = latest_files.get("timeseries")
COUNTRIES_FILE  = latest_files.get("countries")
INDICATORS_FILE = latest_files.get("indicators")

# Load into memory (adjust if too large)
df_timeseries = pd.read_csv(TIMESERIES_FILE)
df_countries  = pd.read_csv(COUNTRIES_FILE)
df_indicators = pd.read_csv(INDICATORS_FILE)

# Defaults
default_countries  = ['ESP', 'FRA']
default_indicators = common.chosen_indicators

df_countries_fil   = df_countries[df_countries['id'].isin(df_timeseries['country'].unique())]
country_dict       = pd.Series(df_countries_fil['label'].values, index=df_countries_fil['id']).to_dict()

df_indicators_fil  = df_indicators[df_indicators['id'].isin(df_timeseries['indicator'].unique())]
indicators_dict    = pd.Series(df_indicators_fil['label'].values, index=df_indicators_fil['id']).to_dict()

df_timeseries['country_name'] = df_timeseries['country'].map(country_dict)
# Install module-level variables expected by makePlotly
m.latest_year     = latest_year
m.df_indicators   = df_indicators
m.indicators_dict = indicators_dict

# Dropdown options
country_options = [{"label": country_dict.get(cid, cid), "value": cid} for cid in sorted(country_dict)]
indicator_options = [{"label": indicators_dict.get(iid, iid), "value": iid} for iid in sorted(indicators_dict)]

app = Dash(__name__)

app.layout = html.Div(
    style={"maxWidth": "1100px", "margin": "0 auto", "fontFamily": "Arial, sans-serif"},
    children=[
        html.H2("IMF Macro Dashboard"),
        html.Div(
            style={"display": "flex", "gap": "12px", "flexWrap": "wrap"},
            children=[
                html.Div(
                    style={"minWidth": "320px", "flex": "1"},
                    children=[
                        html.Label("Countries"),
                        dcc.Dropdown(
                            id="countries",
                            options=country_options,
                            value=default_countries,
                            multi=True,
                            placeholder="Select countries",
                        ),
                    ],
                ),
                html.Div(
                    style={"minWidth": "320px", "flex": "1"},
                    children=[
                        html.Label("Indicator"),
                        dcc.Dropdown(
                            id="indicator",
                            options=indicator_options,
                            value=default_indicators[0] if default_indicators else None,
                            multi=False,
                            placeholder="Select indicator",
                            clearable=False,
                        ),
                    ],
                ),
            ],
        ),
        dcc.Graph(id="macro-graph", style={"height": "72vh"}),
    ],
)

# app.py (after reading CSVs)
df_timeseries["year"] = pd.to_numeric(df_timeseries["year"], errors="coerce")
# ... rest unchanged ...

@app.callback(
    Output("macro-graph", "figure"),
    Input("countries", "value"),
    Input("indicator", "value"),
)
def update_graph(countries, indicator):
    if not countries or not indicator:
        return {"data": [], "layout": {"title": {"text": ""}}}
    df_sel = df_timeseries[
        (df_timeseries["country"].isin(countries)) &
        (df_timeseries["indicator"] == indicator)
    ]
    return m.makePlotly(df_sel, indicator, save_html=False)



if __name__ == "__main__":
    app.run(debug=False)
