from __future__ import annotations

from pathlib import Path
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots  # not strictly needed but useful later

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
    df = load_tidy(csv_path)

    # Filter to Europe to match the GeoJSON subset
    df = df[df["country"].isin(EUROPE_ISO3)].copy()

    if df.empty:
        raise ValueError("No European rows found in CSV")

    indicators = sorted(df["indicator"].dropna().unique().tolist())
    years = sorted(int(y) for y in df["year"].dropna().unique().tolist())
    df_eu = df[df["country"].isin(EUROPE_ISO3)].copy()
    sub = df_eu[(df_eu["indicator"]==indicators[0]) & (df_eu["year"]==years[0])][["country","value"]]
    assert {"FRA","NOR"} <= set(df_eu["country"])  # confirm present
    geojson = get_geojson()
    fkey = "id"
    # Start with the first indicator/year as default
    init_indicator = indicators[0]
    init_year = years[-1]

    base = df[(df["indicator"] == init_indicator) & (df["year"] == init_year)][["country", "value"]]
    continental_geo =  clip_to_mainland_europe(geojson)
    from .shared_plots import apply_shared_title_style, get_shared_data_components

    shared_data = get_shared_data_components()
    indicators_dict = shared_data['indicators_dict']
    units_dict = shared_data['units_dict']
    init_unit = shared_data["units_dict"][shared_data["default_indicator"]]

    indicator_options = shared_data['indicator_options']
    default_indicator = shared_data['default_indicator']
    latest_year = shared_data['latest_year']
    print(indicators_dict, indicator_options)
    # Create indicators button:
    indicator_buttons = []
    for option in shared_data["indicator_options"]:
        iid = option["value"]
        label = option["label"]
        unit = units_dict.get(iid, "")
        indicator_buttons.append(dict(
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
    
    # And for titles, replace your current title with:
    fig = px.choropleth(
        base,
        geojson=continental_geo,
        featureidkey=fkey,
        locations="country",
        color="value",
        projection="mercator",
        color_continuous_scale="Viridis",
    )
    fig.update_layout(
    margin=dict(l=20, r=100, t=80, b=20),  # More space for colorbar on right
    coloraxis_colorbar=dict(
        thickness=15,
        len=0.6,
        x=1.01,
        xanchor="left"
    )
    )

    fig.update_geos(fitbounds="locations", visible=False)


    fig.update_layout(
    coloraxis_colorbar=dict(
        title="Value",
        thickness=20,   # thicker bar
        len=1.0,        # covers 80% of map height
        x=0.92,         # shift colorbar left (0.5 is center, 1.0 is far right)
        xanchor="left",
        y=0.5,          # center vertically
        yanchor="middle",
        )
    )
    fig.update_layout(
            coloraxis_colorbar=dict(title=dict(text=init_unit))
        )

    fig.update_layout(
        updatemenus=[
            dict(
                buttons=indicator_buttons,  # The buttons we created above
                direction="down",
                showactive=True,
                x=0.1,
                xanchor="left",
                y=1.02,
                yanchor="top",
            ),
        ]
    )

    trace_locs = set(fig.to_dict()["data"][0].get("locations", []))
    missing = set(sub["country"]) - trace_locs
    print("Missing locations:", sorted(missing))  # should be []

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