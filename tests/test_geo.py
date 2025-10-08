from pathlib import Path
from macroeconomics.common import EUROPE_ISO3
from macroeconomics.maps.geo import get_europe_geojson, _normalize_ids_inplace

FIXTURE = Path("tests/data/world_countries.geojson")

def test_featureidkey_default():
    geo, fkey = get_europe_geojson(FIXTURE)
    assert fkey == "properties.ISO_A3"

def test_subset_to_europe():
    geo, _ = get_europe_geojson(FIXTURE)
    ids = {f["id"] for f in geo["features"]}
    assert ids.issubset(EUROPE_ISO3)
    assert "DEU" in ids

def test_normalize_ids():
    sample = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"ISO_A3": "DEU"}, "geometry": None},
        {"type": "Feature", "properties": {"ISO_A3": "FRA"}, "geometry": None},
    ]}
    _normalize_ids_inplace(sample, "properties.ISO_A3")
    assert {f["id"] for f in sample["features"]} == {"DEU", "FRA"}

