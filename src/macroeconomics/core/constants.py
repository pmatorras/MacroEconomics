from __future__ import annotations
from pathlib import Path
from importlib.resources import files

# Project root directory (repo/src/macroeconomics/common.py -> parents[2] == repo/)
ROOT_DIR: Path = Path(__file__).resolve().parents[3]
# Standard output directories under project root
DATA_DIR: Path = ROOT_DIR / "data"
FIGURE_DIR: Path = ROOT_DIR / "figures"
LOG_DIR: Path = ROOT_DIR / "logs"
MODIFIED_NAME = "_with_features"
# Dashboard indicators (treat as constants)
INDICATORS: tuple[str, ...] = (
    "LP", "NGDPD", "PPPPC", "NGDPDPC", "PCPIEPCH", "LUR", "NGDP_RPCH"
)

# Europe base set
EUROPE_ISO3: frozenset[str] = frozenset((
    "ALB","AND","AUT","BEL","BGR","BIH","BLR","CHE","CYP","CZE","DEU","DNK","ESP","EST","FIN",
    "FRA","GBR","GRC","HRV","HUN","IRL","ISL","ITA","KOS","LIE","LTU","LUX","LVA","MCO","MDA",
    "MKD","MLT","MNE","NLD","NOR","POL","PRT","ROU", "RUS","SMR","SRB","SVK","SVN","SWE","TUR",
    "UKR","VAT"
))

# Non-European extras for dashboards
EXTRAS_ISO3: frozenset[str] = frozenset((
    "USA","PHL","CHN","KOR","CHE","CHL","JPN","IND","THA","UZB","VNM",
))

# Single source of truth for dashboard countries
COUNTRIES_ISO3: tuple[str, ...] = tuple(sorted(EUROPE_ISO3 | EXTRAS_ISO3))

# Reliable upstreams for GeoJSON maps (primary + fallback)
NATURAL_EARTH_URL: str = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"
    "ne_50m_admin_0_countries.geojson"
)
GEOBOUNDARIES_URL: str = (
    "https://www.geoboundaries.org/gbRequest.html?ISO=ALL&ADM=ADM0&format=GeoJSON"
)
DEFAULT_FEATUREIDKEY = "properties.ISO_A3"

ASSETS_DIR = files("macroeconomics").joinpath("assets")


DEFAULT_GEOJSON = ASSETS_DIR / "world_countries.geojson"


