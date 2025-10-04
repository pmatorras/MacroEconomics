# app.py
import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plot
import common


# Load latest files and prepare data
latest_files, latest_year = plot.find_latest_files_and_year(common.DATA_DIR, prompt_on_mismatch=False)

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
plot.latest_year     = latest_year
plot.df_indicators   = df_indicators
plot.indicators_dict = indicators_dict

# Dropdown options
country_options = [{"label": country_dict.get(cid, cid), "value": cid} for cid in sorted(country_dict)]
indicator_options = [{"label": indicators_dict.get(iid, iid), "value": iid} for iid in sorted(indicators_dict)]
# Ensure numeric years for slider and filtering
df_timeseries["year"] = pd.to_numeric(df_timeseries["year"], errors="coerce")
# Compute bounds and marks
years = sorted(y for y in df_timeseries["year"].dropna().unique())
YEAR_MIN, YEAR_MAX = int(years[0]), int(years[-1])
marks = {y: str(y) for y in range(YEAR_MIN, YEAR_MAX + 1, 5)}

app = Dash(__name__)
server = app.server  # expose Flask server for Gunicorn

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
                html.Div(
                    style={"minWidth": "320px", "flex": "1"},
                    children=[
                        html.Label("Years"),
                        dcc.RangeSlider(
                            id="year-range",
                            min=YEAR_MIN,
                            max=YEAR_MAX,
                            value=[2010, YEAR_MAX],
                            step=1,
                            allowCross=False,
                            marks=marks,
                        ),
                    ],
                ),
            ],
        ),
        dcc.Graph(id="macro-graph", style={"height": "72vh"}),
    ],
)



@app.callback(
    Output("macro-graph", "figure"),
    Input("countries", "value"),
    Input("indicator", "value"),
    Input("year-range", "value"),

)

def update_graph(countries, indicator, year_range):
    if not countries or not indicator:
        return {"data": [], "layout": {"title": {"text": ""}}}
    y0, y1 = year_range if year_range else [YEAR_MIN, YEAR_MAX]
    df_sel = df_timeseries[
        (df_timeseries["country"].isin(countries)) &
        (df_timeseries["indicator"] == indicator) &
        (df_timeseries["year"] >= y0) &
        (df_timeseries["year"] <= y1)
    ]

    return plot.makePlotly(df_sel, indicator, indicators_dict, df_indicators, latest_year, save_html=False)
def main(debug=True, host="127.0.0.1", port=8050):
    app.run(debug=debug, host=host, port=port)

if __name__ == "__main__":
    main()