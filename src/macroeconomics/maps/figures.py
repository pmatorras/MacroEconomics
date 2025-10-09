from __future__ import annotations

from pathlib import Path
import pandas as pd
import plotly.express as px

from macroeconomics.common import EUROPE_ISO3, FIGURE_DIR, DATA_DIR
from macroeconomics.logging_config import logger
from macroeconomics.maps.geo import get_geojson, DEFAULT_FEATUREIDKEY
from macroeconomics.maps.europe import clip_to_mainland_europe

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

def make_europe_map_interactive(csv_path: Path, outfile: Path | None = None):
    """
    Build a single choropleth figure with dropdowns for indicator and year.
    Expects a tidy CSV with columns: ISO3, indicator, year, value.
    """

    
    geojson = get_geojson()
    fkey = "id"
    continental_geo =  clip_to_mainland_europe(geojson)
    from .shared_plots import get_shared_data_components

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
    init_year = 2025
    initial_idx = years.index(init_year)

    init_indicator = shared_data['default_indicator']
    init_unit = units_dict[init_indicator]
    print(init_indicator)
    # Create indicators button:
    buttons_indicator = []
    for option in shared_data["indicator_options"]:
        print(option, units_dict.get(option["value"], ""))
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
                        x=0.5, y=1.01,
                        xref="paper", yref="paper",
                        showarrow=False,
                        font=dict(size=26),
                        xanchor="center", yanchor="bottom"
                    )],
                    "coloraxis.colorbar.title.text": unit
                }
            ]
        ))
    # Year buttons
    buttons_year = []
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
                    x=0.5, y=1.01, xref="paper", yref="paper",
                    showarrow=False, font=dict(size=26),
                    xanchor="center", yanchor="bottom"
                )]}
            ]
        ))
    
    fig = px.choropleth(
        df.query("indicator == @init_indicator and year == @init_year"),
        geojson=continental_geo,
        featureidkey=fkey,
        locations="country",
        color="value",
        projection="mercator",
        color_continuous_scale="Viridis",
    )
    fig.update_geos(fitbounds="locations", visible=False)
    # After fig = px.choropleth(...)
    initial_annotation = dict(
        text=f"{shared_data['indicators_dict'][init_indicator]} ({init_year})",
        x=0.5, y=1.01, xref="paper", yref="paper",
        showarrow=False, font=dict(size=26),
        xanchor="center", yanchor="bottom"
    )
    
    fig.update_layout(annotations=[initial_annotation])
    fig.update_layout(
        coloraxis_colorbar=dict(
            title=init_unit,
            thickness=15,
            len=0.8,
            x=1.01,
            xanchor="left"
        )
    )
    # Layout: figure size & colorbar
    fig.update_layout(
        margin=dict(l=20, r=100, t=80, b=20),  # More space for colorbar on right
        coloraxis_colorbar=dict(
            thickness=15,
            len=0.8,
            x=1.01,
            xanchor="left"
        ),
        updatemenus=[
            dict(
                buttons=buttons_indicator,
                direction="down", showactive=True,
                x=0.0, xanchor="left", y=1.02, yanchor="top",
                pad={"r":10, "t":10}
            ),
            dict(
                buttons=buttons_year,
                direction="down", showactive=True,
                x=0.5, xanchor="left", y=1.02, yanchor="top",
                pad={"r":10, "t":10},
                active=initial_idx

            ),
        ]
    )

    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    outfile = outfile or (FIGURE_DIR / "europe_interactive_map.html")
    fig.write_html(outfile, include_plotlyjs="cdn")
    logger.info(f"Wrote {outfile}")
    return fig, outfile

if __name__ == "__main__":
    # Default to the latest tidy CSV produced by data.py
    # Adjust the filename/tag to your actual output
    candidates = sorted(DATA_DIR.glob("imf_weo_timeseries_*.csv"))
    if not candidates:
        raise SystemExit("No tidy WEO CSVs found in data/. Run the data pipeline first.")
    csv = candidates[-1]
    make_europe_map_interactive(csv)