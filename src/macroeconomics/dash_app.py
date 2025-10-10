# app.py
from pathlib import Path
import pandas as pd
import os
from dash import Dash, dcc, html, Input, Output
from macroeconomics.viz.charts.timeseries import find_latest_files_and_year, makePlotly
from macroeconomics.core.common import DATA_DIR, INDICATORS

# Load latest files and prepare data
def _load_latest_data(data_dir):

    latest_files, latest_year = find_latest_files_and_year(data_dir, prompt_on_mismatch=False)
    ts = Path(latest_files["timeseries"])
    co = Path(latest_files["countries"])
    ind = Path(latest_files["indicators"])

    # Read CSVs
    df_timeseries = pd.read_csv(ts)
    df_countries = pd.read_csv(co)
    df_indicators = pd.read_csv(ind)
    return {
        "year": latest_year,
        "timeseries": df_timeseries,
        "countries": df_countries,
        "indicators": df_indicators,
    }


def create_app():
    data = _load_latest_data(Path(DATA_DIR))  # returns a dict
    df_timeseries = data["timeseries"]
    df_countries = data["countries"]
    df_indicators = data["indicators"]
    default_indicators = INDICATORS
    latest_year = data["year"]

    # Optional: sanitize headers/types
    df_indicators.columns = df_indicators.columns.str.strip()
    df_indicators["id"] = df_indicators["id"].astype(str)

    df_indicators_fil = df_indicators[df_indicators["id"].isin(default_indicators)]
    df_countries_fil   = df_countries[df_countries['id'].isin(df_timeseries['country'].unique())]
    country_dict       = pd.Series(df_countries_fil['label'].values, index=df_countries_fil['id']).to_dict()
    indicators_dict = pd.Series(
        df_indicators_fil["label"].values, index=df_indicators_fil["id"]
    ).to_dict()
    country_options = [{"label": country_dict.get(cid, cid), "value": cid} for cid in sorted(country_dict)]
    indicator_options = [{"label": indicators_dict.get(iid, iid), "value": iid} for iid in sorted(indicators_dict)]
    # Infer available years from wide timeseries columns that look like integers
    years = sorted(y for y in df_timeseries["year"].dropna().unique())
    YEAR_MIN, YEAR_MAX = int(years[0]), int(years[-1])
    marks = {y: str(y) for y in range(YEAR_MIN, YEAR_MAX + 1, 5)}
    default_countries = ["ESP", "FRA"]
    default_indicator = default_indicators[0]
    app = Dash(__name__)
    # Your layout and callbacks...
    app.server.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret")
    )
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
        y0, y1 = int(year_range[0]), int(year_range[1])
        # Filter tidy data
        df = df_timeseries[
            (df_timeseries["country"].isin(countries)) &
            (df_timeseries["indicator"] == indicator) &
            (df_timeseries["year"].between(y0, y1))
        ].copy()
        # Guarantee country_name exists (in case)
        if "country_name" not in df.columns:
            df["country_name"] = df["country"].map(country_dict)
        # Use makePlotly with expected signature
        fig = makePlotly(df, indicator, indicators_dict, df_indicators, latest_year, save_html=False, suffix=None)
        return fig

        # Call your existing plot helper; adjust the signature to match your makePlotly
        fig = makePlotly(
            df=df,
            indicator=indicator,
            countries=countries,
            year_min=y_start,
            year_max=y_end,
            save_html=False,
        )
        return fig

    return app
