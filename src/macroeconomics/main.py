import argparse
from types import SimpleNamespace

from .data import data_main
from .plot import plot_main 
from .common import ensure_dirs

def cmd_fetch(ns):    
    # Build the args object expected by data_main
    args = SimpleNamespace(
        indicators=ns.indicators,   # comma-separated string or None
        countries=ns.countries,     # comma-separated string or None
        debug=ns.debug,             # bool
    )
    data_main(args)
def cmd_plot(ns):
    print("do plot", ns)
    plot_main(ns)

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
# in parser wiring:
    p_plot = sub.add_parser("plot", help="Plot indicators from latest CSVs")
    p_plot.add_argument("--countries", help="Comma-separated ISO3 codes (e.g., ESP,FRA,DEU)")
    p_plot.set_defaults(func=cmd_plot)
    p_dash = sub.add_parser("dash", help="Run the Dash app")
    p_dash.add_argument("--host", default="127.0.0.1")
    p_dash.add_argument("--port", type=int, default=8050)
    p_dash.add_argument("--debug", action="store_true")
    p_dash.set_defaults(func=cmd_dash)
    args = parser.parse_args()
    args.func(args)
