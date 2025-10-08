# src/macroeconomics/maps/geo.py
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Optional, Tuple, Union

import requests

from macroeconomics.common import EUROPE_ISO3, NATURAL_EARTH_URL, GEOBOUNDARIES_URL, DEFAULT_FEATUREIDKEY, DEFAULT_GEOJSON, ASSETS_DIR

Json = dict
PathLike = Union[str, Path]





def _is_url(source: PathLike) -> bool:
    s = str(source)
    return s.startswith("http://") or s.startswith("https://")


def _load_json_local(path: PathLike) -> Json:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _download_json(url: str) -> Json:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _ensure_local_world_geojson(path: Path, primary_url: str, fallback_url: str | None = None) -> Json:
    """
    Use cached file if present. If not present, download from primary, or from fallback if there is an error.
    Cache to 'path', and return the JSON.
    """
    if path.exists():
        return _load_json_local(path)
    try:
        data = _download_json(primary_url)
    except Exception:
        if not fallback_url:
            raise
        data = _download_json(fallback_url)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return data


def _normalize_ids_inplace(geojson: Json, id_field: str) -> None:
    props_key = id_field.split(".", 1)[-1] if id_field.startswith("properties.") else id_field
    for feat in geojson.get("features", []):
        if "id" not in feat or not feat["id"]:
            props = feat.get("properties", {})
            if props_key in props:
                feat["id"] = props[props_key]


def _filter_to_europe(geojson: Json, id_field: str, europe_iso3: Iterable[str]) -> Json:
    props_key = id_field.split(".", 1)[-1] if id_field.startswith("properties.") else id_field
    selected = []
    for feat in geojson.get("features", []):
        code = feat.get("id")
        if not code:
            props = feat.get("properties", {})
            code = props.get(props_key)
        if code in europe_iso3:
            selected.append(feat)
    return {"type": "FeatureCollection", "features": selected}


@lru_cache(maxsize=8)
def get_europe_geojson(
    source: Optional[PathLike] = None,
    featureidkey: Optional[str] = None,
    *,
    subset_to_europe: bool = True,
    normalize_ids: bool = True,
) -> Tuple[Json, str]:
    """
    Load/Download world GeoJSON, filter to Europe, normalize IDs,
    and return (geojson, featureidkey) ready for Plotly.
    """
    fkey = featureidkey or DEFAULT_FEATUREIDKEY

    if source is None:
        data = _ensure_local_world_geojson(DEFAULT_GEOJSON, NATURAL_EARTH_URL, GEOBOUNDARIES_URL)
    elif _is_url(source):
        data = _download_json(str(source))
    else:
        data = _load_json_local(source)

    if subset_to_europe:
        data = _filter_to_europe(data, fkey, EUROPE_ISO3)
    if normalize_ids:
        _normalize_ids_inplace(data, fkey)
    return data, fkey


def get_world_geojson(
    source: Optional[PathLike] = None,
    featureidkey: Optional[str] = None,
    *,
    normalize_ids: bool = False,
) -> Tuple[Json, str]:
    """
    Return (world geojson, featureidkey) without Europe filtering.
    """
    fkey = featureidkey or DEFAULT_FEATUREIDKEY

    if source is None:
        data = _ensure_local_world_geojson(DEFAULT_GEOJSON, NATURAL_EARTH_URL, GEOBOUNDARIES_URL)
    elif _is_url(source):
        data = _download_json(str(source))
    else:
        data = _load_json_local(source)

    if normalize_ids:
        _normalize_ids_inplace(data, fkey)
    return data, fkey


if __name__ == "__main__":
    # Self-test: run from project root after `pip install -e .`:
    #   python -m macroeconomics.maps.geo
    import pandas as pd
    import plotly.express as px

    geo, fkey = get_europe_geojson()

    df = pd.DataFrame({"ISO3": ["DEU", "FRA", "ESP", "ITA"], "value": [1.0, 2.0, 3.0, 4.0]})

    fig = px.choropleth(
        df,
        geojson=geo,
        featureidkey=fkey,
        locations="ISO3",
        color="value",
        projection="mercator",
    )
    fig.update_geos(fitbounds="locations", visible=False)

    # Assert expected locations are present
    trace_locations = fig.to_dict()["data"][0].get("locations", [])
    assert set(df["ISO3"]).issubset(set(trace_locations)), "Missing expected locations"

    out = ASSETS_DIR / "europe_map_test.html"
    fig.write_html(out, include_plotlyjs="cdn")
    print(f"Wrote {out}")

    print("geo.py self-test OK — features:", len(geo.get("features", [])), "featureidkey:", fkey)
