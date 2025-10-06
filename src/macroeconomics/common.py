from pathlib import Path

# Directory where this script resides
ROOT_DIR = Path(__file__).resolve().parents[2]
chosen_indicators = ["LP", "NGDPD", "PPPPC", "NGDPDPC", "PCPIEPCH", "LUR", "NGDP_RPCH"]
countries_iso3 = ["AUT","BEL","BGR","HRV","CYP","CZE","DNK","EST","FIN","FRA","DEU","GRC","HUN",
           "IRL","ITA","LVA","LTU","LUX","MLT","NLD","POL","PRT","ROU","SVK","SVN","ESP","SWE", "USA", "PHL", "CHN", "KOR", "CHE", "CHL", "JPN", "IND", "THA", "UZB", "VNM",  "RUS", "UKR"]
DATA_DIR = ROOT_DIR /"data/"
FIGURE_DIR = ROOT_DIR/ "figures/"
LOG_DIR = ROOT_DIR/"logs/"
def ensure_dirs():
    for p in (DATA_DIR, FIGURE_DIR, LOG_DIR):
        p.mkdir(parents=True, exist_ok=True)