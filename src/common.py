from pathlib import Path

# Directory where this script resides
base_dir = Path(__file__).parent
print(base_dir)
chosen_indicators = ["LP", "NGDPD", "PPPPC", "NGDPDPC", "PCPIEPCH", "LUR", "NGDP_RPCH"]
countries_iso3 = ["AUT","BEL","BGR","HRV","CYP","CZE","DNK","EST","FIN","FRA","DEU","GRC","HUN",
           "IRL","ITA","LVA","LTU","LUX","MLT","NLD","POL","PRT","ROU","SVK","SVN","ESP","SWE", "USA", "PHL", "CHN", "KOR", "CHE", "CHL", "JPN", "IND", "THA", "UZB", "VNM",  "RUS", "UKR"]
DATA_FOLDER = base_dir /"../Data/"
FIGURE_FOLDER = base_dir/ "../Figures/"
