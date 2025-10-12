# app.py
from pathlib import Path
import pandas as pd
import os
from dash import Dash, dcc, html, Input, Output
from macroeconomics.core.functions import get_shared_data_components
from macroeconomics.viz.charts.timeseries import makePlotly
from macroeconomics.viz.maps.europe_interactive_map import make_europe_map
from macroeconomics.core.constants import DATA_DIR, INDICATORS
from macroeconomics.logging_config import logger

def create_timeseries_layout(country_options, indicator_options, default_countries, default_indicators, YEAR_MIN, YEAR_MAX, marks):
    return html.Div(
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
def create_map_layout(indicator_options, default_indicators):
    """New map tab layout"""
    return html.Div([
        html.H3("European Map Visualization"),
        html.Div(
            style={"display": "flex", "gap": "12px", "marginBottom": "20px"},
            children=[
                html.Div(
                    style={"minWidth": "320px", "flex": "1"},
                    children=[
                        html.Label("Map Indicator"),
                        dcc.Dropdown(
                            id="map-indicator",
                            options=indicator_options,
                            value=default_indicators[0] if default_indicators else None,
                            multi=False,
                            placeholder="Select indicator for map",
                            clearable=False,
                        ),
                    ],
                ),
                html.Div(
                    style={"minWidth": "200px"},
                    children=[
                        html.Label("Map Year"),
                        dcc.Dropdown(
                            id="map-year",
                            options=[{"label": str(y), "value": y} for y in range(2000, 2025)],
                            value=2023,
                            clearable=False,
                        ),
                    ],
                ),
            ],
        ),
        dcc.Graph(id="europe-map", style={"height": "70vh"}),
    ])

def create_app(args):
    data = get_shared_data_components(args.do_features)  # returns a dict
    df_timeseries = data["time_series"]
    df_countries = data["countries"]
    df_indicators = data["df_indicators"]
    default_indicators = INDICATORS
    latest_year = data["latest_year"]
    country_dict = data["country_dict"]
    indicators_dict = data["indicators_dict"]
    country_options = data["country_options"]
    indicator_options = data["indicator_options"]
    unit_suffix_dict = data["suffix"]
    # Infer available years from wide timeseries columns that look like integers
    years = sorted(y for y in df_timeseries["year"].dropna().unique())
    YEAR_MIN, YEAR_MAX = int(years[0]), int(years[-1])
    marks = {y: str(y) for y in range(YEAR_MIN, YEAR_MAX + 1, 5)}
    default_countries = ["ESP", "FRA"]
    default_indicator = data["default_indicator"]
    app = Dash(__name__)
    # Your layout and callbacks...
    app.server.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret")
    )
    app.layout = html.Div(
        style={"maxWidth": "1200px", "margin": "0 auto", "fontFamily": "Arial, sans-serif"},
        children=[
            html.H2("IMF Macro Dashboard"),
            
            # Tab selector
            dcc.Tabs(id="main-tabs", value="tab-timeseries", children=[
                dcc.Tab(label="Time Series", value="tab-timeseries"),
                dcc.Tab(label="European Map", value="tab-map"),
            ]),
            
            # Tab content
            html.Div(id="tab-content"),
        ]
    )

    # Tab switching callback
    @app.callback(
        Output("tab-content", "children"),
        Input("main-tabs", "value")
    )

    #render the two tab options
    def render_tab_content(active_tab):
        if active_tab == "tab-timeseries":
            return create_timeseries_layout(
                country_options, indicator_options, default_countries, 
                default_indicators, YEAR_MIN, YEAR_MAX, marks
            )
        elif active_tab == "tab-map":
            return create_map_layout(indicator_options, default_indicators)
    #timeseries callback
    @app.callback(
        Output("macro-graph", "figure"),
        Input("countries", "value"),
        Input("indicator", "value"),
        Input("year-range", "value"),

    )

    def update_graph(countries, indicator, year_range):
        if not countries or not indicator or not year_range:
            return {}
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
        fig = makePlotly(df, indicator, indicators_dict, unit_suffix_dict, df_indicators, latest_year, save_html=False, suffix=None)
        return fig

    # Map callback
    @app.callback(
        Output("europe-map", "figure"),
        Input("map-indicator", "value"),
        Input("map-year", "value"),
    )
    def update_map(indicator, year):
        logger.debug(f"DEBUG: indicator={indicator}, year={year}")

        if not indicator:
            return {}
        
        # Filter data for the specific year and indicator for map
        map_data = df_timeseries[
            (df_timeseries["indicator"] == indicator) &
            (df_timeseries["year"] == year)
        ].copy()
        
        # Call your existing map function with filtered data
        fig = make_europe_map(args=args,
                              save_html=False,
                              do_buttons=False,        
                              custom_indicator=indicator,
                              custom_year=year)
        return fig
    return app
