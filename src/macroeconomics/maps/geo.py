# src/macroeconomics/maps/geo.py
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Optional, Tuple, Union

import requests

from macroeconomics.common import EUROPE_ISO3, NATURAL_EARTH_URL, GEOBOUNDARIES_URL, DEFAULT_FEATUREIDKEY, DEFAULT_GEOJSON, ASSETS_DIR
from macroeconomics.maps.europe import filter_to_europe, clip_to_mainland_europe
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


def _ensure_local_world_geojson(path: Path, primary_url: str, fallback_url: Optional[str] = None) -> Json:
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


def _normalize_ids_inplace(geojson: Json) -> None:
    """
    Set 'id' on each feature to the first valid ISO code from preferred keys.
    Also stores 'id_source_key' on the feature to track which key was used.
    """
    placeholders = {"-99", "NULL", "N/A", "", None}
    preferred_keys = ["ISO_A3", "ISO_A3_EH", "ADM0_A3", "SOV_A3"]

    for feature in geojson.get("features", []):
        props = feature.get("properties", {})
        id_set = False

        for key in preferred_keys:
            val = props.get(key)
            if val is None:
                continue
            code = str(val).strip().upper()

            if code in placeholders:
                continue

            try:
                if int(code) <= -99:
                    continue
            except Exception:
                pass

            feature["id"] = code
            feature["id_source_key"] = key
            id_set = True
            break

        if not id_set:
            feature["id"] = None
            feature["id_source_key"] = None





@lru_cache(maxsize=8)
def get_geojson(onlyEurope: bool = True, source: Optional[PathLike] = None) -> Json:
    if source is None:
        data = _ensure_local_world_geojson(DEFAULT_GEOJSON, NATURAL_EARTH_URL, GEOBOUNDARIES_URL)
    elif _is_url(source):
        data = _download_json(str(source))
    else:
        data = _load_json_local(source)

    _normalize_ids_inplace(data)
    if onlyEurope: data = filter_to_europe(data, EUROPE_ISO3)

    return data



if __name__ == "__main__":
    import pandas as pd
    import plotly.express as px

    geo = get_geojson()
    fkey = "id"
    print("Using featureidkey:", fkey)

    id_set = {feat.get("id") for feat in geo["features"]}
    # Optionally check France or other ISO3 code presence here
    # assert "FRA" in id_set, f"FRA not found among feature ids"

    df = pd.DataFrame({"ISO3": ["DEU", "FRA", "ESP", "ITA", "NOR"], "value": [1.0, 2.0, 3.0, 4.0, 4.0]})
    from macroeconomics.maps.europe import clip_to_mainland_europe
    continental_geo = clip_to_mainland_europe(geo)
    fig = px.choropleth(
        df,
        geojson=continental_geo,
        featureidkey=fkey,
        locations="ISO3",
        color="value",
        projection="mercator",
    )
    out = ASSETS_DIR / "europe_map_test.html"
    fig.update_geos(fitbounds="locations", visible=False)
    fig.write_html(out, include_plotlyjs="cdn")
    print(f"Wrote {out}")
    trace_locations = fig.to_dict()["data"][0].get("locations", [])
    assert set
