from __future__ import annotations

from pathlib import Path
import pandas as pd
import plotly.express as px
from datetime import datetime


from macroeconomics.core.constants import EUROPE_ISO3, FIGURE_DIR, DATA_DIR
from macroeconomics.logging_config import logger
from macroeconomics.viz.maps.geo import get_geojson, DEFAULT_FEATUREIDKEY
from macroeconomics.viz.maps.europe import clip_to_mainland_europe
from macroeconomics.viz.theme import shared_title_style
from macroeconomics.core.functions import get_shared_data_components

def load_tidy(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    print(df)
    required = {"country", "indicator", "year", "value"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing columns: {sorted(missing)}")
    # ensure types
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    return df

def wrap_title(name: str, unit: str | None = None, width: int = 25) -> str:
    # naive wrap: break at the last space before width
    label = name.strip()
    if len(label) > width and " " in label:
        i = label.rfind(" ", 0, width)
        if i != -1:
            label = label[:i] + "<br>" + label[i+1:]
    if unit:
        label += f"<br>({unit})"
    return label

def make_europe_map(save_html=True, do_buttons=True, custom_indicator=None, custom_year=None):
    """
    Build a single choropleth figure with dropdowns for indicator and year.
    Expects a tidy CSV with columns: ISO3, indicator, year, value.
    """

    geojson = get_geojson()
    fkey = "id"
    continental_geo =  clip_to_mainland_europe(geojson)

    shared_data = get_shared_data_components()
    df = shared_data["time_series"]
    # Filter to Europe to match the GeoJSON subset
    df = df[df["country"].isin(EUROPE_ISO3)].copy()
    if df.empty:
        raise ValueError("No European rows found in CSV")
    assert {"FRA","NOR"} <= set(df["country"])  # confirm present

    country_dict = shared_data["country_dict"]
    units_dict = shared_data['units_dict']
    years = sorted(df["year"].dropna().unique())


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


    fig = px.choropleth(
        df.query("indicator == @init_indicator and year == @init_year"),
        geojson=continental_geo,
        featureidkey=fkey,
        locations="country",
        color="value",
        projection="mercator",
        color_continuous_scale="Viridis",
        custom_data=["country_name", "value"],  # carry readable name

    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_traces(
        hovertemplate="%{customdata[0]}<br>Value=%{customdata[1]:,.2f}<extra></extra>"
    )
    shared_title_style(fig, init_indicator, shared_data['indicators_dict'])

    fig.update_layout(
        margin=dict(l=20, r=100, t=80, b=20), 
        coloraxis_colorbar=dict(
            title=init_unit,
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
            buttons_year.append(dict(
                label=str(yr),
                method="update",
                args=[
                    {"z": [df.loc[
                        (df.indicator==init_indicator)&(df.year==yr),
                        "value"
                    ].tolist()]},
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
            label = option["label"]
            unit = units_dict.get(iid, "")
            buttons_indicator.append(dict(
                label=label,
                method="update",
                args=[
                    # Update the map's data
                    {"z": [ df.loc[(df["indicator"] == iid) & (df["year"] == init_year), "value"].tolist() ]},
                    # Update layout: title annotation stays indicator label,
                    # colorbar title uses unit
                    {
                        "annotations": [dict(
                            text=label,
                            x=button_indicator_x, y=1.01,
                            xref="paper", yref="paper",
                            showarrow=False,
                            font=dict(size=26),
                            xanchor="center", yanchor="bottom"
                        )],
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
