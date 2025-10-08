from __future__ import annotations

from pathlib import Path
from typing import Iterable

# Project root directory (repo/src/macroeconomics/common.py -> parents[2] == repo/)
ROOT_DIR: Path = Path(__file__).resolve().parents[2]

# Standard output directories under project root
DATA_DIR: Path = ROOT_DIR / "data"
FIGURE_DIR: Path = ROOT_DIR / "figures"
LOG_DIR: Path = ROOT_DIR / "logs"

# Dashboard indicators (treat as constants)
INDICATORS: tuple[str, ...] = (
    "LP", "NGDPD", "PPPPC", "NGDPDPC", "PCPIEPCH", "LUR", "NGDP_RPCH"
)

# ISO3 codes used across dashboards
COUNTRIES_ISO3: tuple[str, ...] = (
    "AUT","BEL","BGR","HRV","CYP","CZE","DNK","EST","FIN","FRA","DEU","GRC","HUN",
    "IRL","ITA","LVA","LTU","LUX","MLT","NLD","POL","PRT","ROU","SVK","SVN","ESP","SWE",
    "USA","PHL","CHN","KOR","CHE","CHL","JPN","IND","THA","UZB","VNM","RUS","UKR"
)

# Europe whitelist for choropleths (use set for fast membership)
EUROPE_ISO3: frozenset[str] = frozenset((
    "ALB","AND","AUT","BEL","BGR","BIH","BLR","CHE","CYP","CZE","DEU","DNK","ESP","EST","FIN",
    "FRA","GBR","GRC","HRV","HUN","IRL","ISL","ITA","KOS","LIE","LTU","LUX","LVA","MCO","MDA",
    "MKD","MLT","MNE","NLD","NOR","POL","PRT","ROU","SMR","SRB","SVK","SVN","SWE","UKR","VAT"
))

# Reliable upstreams for GeoJSON maps (primary + fallback)
NATURAL_EARTH_URL: str = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"
    "ne_110m_admin_0_countries.geojson"
)
GEOBOUNDARIES_URL: str = (
    "https://www.geoboundaries.org/gbRequest.html?ISO=ALL&ADM=ADM0&format=GeoJSON"
)
DEFAULT_FEATUREIDKEY = "properties.ISO_A3"

ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"

DEFAULT_GEOJSON = ASSETS_DIR / "world_countries.geojson"

def ensure_dirs(paths: Iterable[Path] | None = None) -> None:
    """
    Create output directories if they don't exist (idempotent).
    """
    targets = tuple(paths) if paths else (DATA_DIR, FIGURE_DIR, LOG_DIR)
    for p in targets:
        p.mkdir(parents=True, exist_ok=True)
