from __future__ import annotations

from pathlib import Path
import pandas as pd
import plotly.express as px
from datetime import datetime


from macroeconomics.core.constants import EUROPE_ISO3, FIGURE_DIR, DATA_DIR
from macroeconomics.core.functions import get_shared_data_components
from macroeconomics.logging_config import logger
from macroeconomics.viz.maps.geo import get_geojson, DEFAULT_FEATUREIDKEY
from macroeconomics.viz.maps.europe import clip_to_mainland_europe
from macroeconomics.viz.theme import shared_title_style, wrap_title

def load_tidy(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"country", "indicator", "year", "value"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing columns: {sorted(missing)}")
    # ensure types
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    return df



def get_colorscale_limits(data_series, percentile=95):
    """Use percentile to handle outliers elegantly"""
    lower = data_series.quantile((100 - percentile) / 100)
    upper = data_series.quantile(percentile / 100)
    return lower, upper

def make_europe_map(do_features, save_html=True, do_buttons=True, custom_indicator=None, custom_year=None):
    """
    Build a single choropleth figure with dropdowns for indicator and year.
    Expects a tidy CSV with columns: ISO3, indicator, year, value.
    """
    geojson = get_geojson()
    fkey = "id"
    continental_geo =  clip_to_mainland_europe(geojson)

    shared_data = get_shared_data_components(do_features=do_features)
    df = shared_data["time_series"]
    # Filter to Europe to match the GeoJSON subset
    df = df[df["country"].isin(EUROPE_ISO3)].copy()
    if df.empty:
        raise ValueError("No European rows found in CSV")
    #assert {"FRA","NOR"} <= set(df["country"])  # confirm present

    country_dict = shared_data["country_dict"]
    units_dict = shared_data['units_dict']
    years = sorted(df["year"].dropna().unique())

    unit_suffix_dict = shared_data['suffix'] 
    # Use custom values if provided (for Dash integration)
    if custom_indicator is not None and custom_year is not None:
        init_indicator = custom_indicator
        init_year = custom_year
    else:
        # Use defaults for standalone version
        init_indicator = shared_data['default_indicator']
        init_year = datetime.now().year

    init_unit = units_dict[init_indicator]
    initial_idx = years.index(init_year)
    init_unit_suffix = unit_suffix_dict[init_indicator]
    current_data = df.query("indicator == @init_indicator and year == @init_year")
    zmin, zmax = get_colorscale_limits(current_data["value"], percentile=95)

    fig = px.choropleth(
        df.query("indicator == @init_indicator and year == @init_year"),
        geojson=continental_geo,
        featureidkey=fkey,
        locations="country",
        color="value",
        projection="mercator",
        color_continuous_scale="Viridis",
        custom_data=["country_name", "value"], 
        range_color= [zmin, zmax],
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_traces(
        hovertemplate=f"<b>%{{customdata[0]}}</b><br>Value: %{{customdata[1]:.2f}}{init_unit_suffix}<extra></extra>"
    )
    shared_title_style(fig, init_indicator, shared_data['indicators_dict'])

    fig.update_layout(
        margin=dict(l=20, r=100, t=80, b=20), 
        coloraxis_colorbar=dict(
            title=wrap_title(init_unit),
            thickness=15,
            len=0.8,
            x=1.01,
            xanchor="left"
        )
    )
    # Layout: figure size & colorbar
    if do_buttons:
        buttons_year = []
        button_year_x = 0.0
        button_indicator_x = 0.15
        for yr in years:
            year_data = df.loc[(df.indicator==init_indicator)&(df.year==yr)]
            buttons_year.append(dict(
                label=str(yr),
                method="update",
                args=[
                    {
                        "z": [year_data["value"].tolist()],
                        "locations": [year_data["country"].tolist()],  
                        "customdata": [year_data[["country_name", "value"]].values.tolist()]  # UPDATE THIS TOO
                    },
                    {"annotations": [dict(
                        text=f"{shared_data['indicators_dict'][init_indicator]} ({yr})",
                        x=button_year_x, y=1.01, xref="paper", yref="paper",
                        showarrow=False, font=dict(size=26),
                        xanchor="center", yanchor="bottom"
                    )]}
                ]
            ))
        # Create indicators button:
        buttons_indicator = []
        for option in shared_data["indicator_options"]:
            iid = option["value"]
            # Get the filtered data for this indicator
            indicator_data = df.loc[(df["indicator"] == iid) & (df["year"] == init_year)]
            label = option["label"] 
            unit = units_dict.get(iid, "")
            unit_suffix = unit_suffix_dict.get(iid, "")  
            template = (
                "<b>%{customdata[0]}</b><br>"
                "Value: %{customdata[1]:.2f}" + unit_suffix_dict[iid] + "<extra></extra>"
            )
            buttons_indicator.append(dict(
            label=label,
            method="update",
            args=[
                # 1) Trace updates
                {
                    "z": [indicator_data["value"].tolist()],
                    "locations": [indicator_data["country"].tolist()],
                    "customdata": [indicator_data[["country_name","value"]].values.tolist()],
                    "hovertemplate": f"%{{customdata[0]}} Value: %{{customdata[1]:.2f}}{unit_suffix}"
                },
                # 2) Layout updates
                {
                    "annotations": [
                        dict(
                            text=label,
                            x=button_indicator_x, y=1.01,
                            xref="paper", yref="paper",
                            showarrow=False, font=dict(size=26),
                            xanchor="center", yanchor="bottom"
                        )
                    ],
                    "coloraxis.colorbar.title.text": wrap_title(unit)
                }
            ]
        ))
        fig.update_layout(
            updatemenus=[
                dict(
                    buttons=buttons_indicator,
                    direction="down", showactive=True,
                    x=button_indicator_x, xanchor="left", y=1.02, yanchor="top",
                    pad={"r":10, "t":10}
                ),
                dict(
                    buttons=buttons_year,
                    direction="down", showactive=True,
                    x=button_year_x, xanchor="left", y=1.02, yanchor="top",
                    pad={"r":10, "t":10},
                    active=initial_idx

                ),
            ]
        )

    if save_html:
        outfile = FIGURE_DIR / "europe_interactive_map.html"
        fig.write_html(outfile, include_plotlyjs="cdn")
        logger.info(f"Wrote {outfile}")
        return fig
    else:
        logger.info(f"Omitting save to html")
        return fig
