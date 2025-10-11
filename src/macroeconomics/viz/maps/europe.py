from shapely.geometry import shape, mapping,box

from macroeconomics.core.common import EUROPE_ISO3
from typing import Iterable

Json = dict

CONTINENTAL_EUROPE_BOUNDS = box(-12.0, 35.0, 40.0, 75.0)  # Rough bounding box

def filter_to_europe(geojson: Json, europe_iso3: Iterable[str]) -> Json:
    selected = []
    for feature in geojson.get("features", []):
        id_code = feature.get("id")
        if id_code in europe_iso3:
            selected.append(feature)
    return {"type": "FeatureCollection", "features": selected}

def clip_to_mainland_europe(geojson):
    clipped_features = []
    for feat in geojson.get("features", []):
        iso3 = feat.get("id")
        if iso3 in EUROPE_ISO3:
            geom = shape(feat["geometry"])
            clipped_geom = geom.intersection(CONTINENTAL_EUROPE_BOUNDS)
            if not clipped_geom.is_empty:
                feat["geometry"] = mapping(clipped_geom)
                clipped_features.append(feat)
        # Optionally skip non-mainland countries
    return {"type": "FeatureCollection", "features": clipped_features}
