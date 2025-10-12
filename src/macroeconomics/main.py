import argparse
from types import SimpleNamespace
from macroeconomics.logging_config import logger
from macroeconomics.datasets.data import data_main
from macroeconomics.viz.charts.timeseries import plot_main 
from macroeconomics.viz.maps.europe_interactive_map import make_europe_map
from macroeconomics.features.build_features import features_main
def cmd_fetch(ns):    
    # Build the args object expected by data_main
    args = SimpleNamespace(
        indicators=ns.indicators,   # comma-separated string or None
        countries=ns.countries,     # comma-separated string or None
        debug=ns.debug,             # bool
    )
    data_main(args)
def cmd_features(ns):
    logger.info(f"Add extra features {ns}")
    features_main(ns)
def cmd_plot(ns):
    logger.info(f"Do plots {ns}")
    plot_main(ns)

def cmd_map(ns):
    logger.info(f"Do maps {ns}")
    make_europe_map(ns)
def cmd_dash(ns):
    from .dash_app import create_app
    app = create_app()
    app.run(debug=ns.debug, host=ns.host, port=ns.port)

def main():
    parser = argparse.ArgumentParser(prog="macroeconomics")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_fetch = sub.add_parser("data", help="Fetch IMF WEO data and write CSVs")
    p_fetch.add_argument("--indicators", help="Comma-separated indicator IDs (e.g., NGDPD,PCPIEPCH)")
    p_fetch.add_argument("--countries", help="Comma-separated ISO3 codes (e.g., ESP,FRA,DEU)")
    p_fetch.add_argument("--debug", action="store_true", help="Suffix output filenames with _debug")
    p_fetch.set_defaults(func=cmd_fetch)

    p_features = sub.add_parser("features", help="Add additional features") #For now, only calculate ratios vs 2019
    p_features.set_defaults(func=cmd_features)

    p_plot = sub.add_parser("plot", help="Plot indicators from latest CSVs")
    p_plot.add_argument("--countries", help="Comma-separated ISO3 codes (e.g., ESP,FRA,DEU)")
    p_plot.set_defaults(func=cmd_plot)

    p_map = sub.add_parser("map", help="Draw interactive maps of Europe")
    p_map.set_defaults(func=cmd_map)

    p_dash = sub.add_parser("dash", help="Run the Dash app")
    p_dash.add_argument("--host", default="127.0.0.1")
    p_dash.add_argument("--port", type=int, default=8050)
    p_dash.add_argument("--debug", action="store_true")
    p_dash.set_defaults(func=cmd_dash)
    args = parser.parse_args()
    args.func(args)
