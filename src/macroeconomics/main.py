import argparse
from types import SimpleNamespace

import data, plots  # data.py in the same package
import common

def cmd_fetch(ns):
    # Ensure output directories exist if using common paths
    if hasattr(common, "ensure_dirs"):
        common.ensure_dirs()
    # Build the args object expected by data_main
    args = SimpleNamespace(
        indicators=ns.indicators,   # comma-separated string or None
        countries=ns.countries,     # comma-separated string or None
        debug=ns.debug,             # bool
    )
    data.data_main(args)
def cmd_plot(ns):
    print("do plot", ns)
    plots.plot_main(ns)


def main():
    parser = argparse.ArgumentParser(prog="macroeconomics")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_fetch = sub.add_parser("fetch", help="Fetch IMF WEO data and write CSVs")
    p_fetch.add_argument("--indicators", help="Comma-separated indicator IDs (e.g., NGDPD,PCPIEPCH)")
    p_fetch.add_argument("--countries", help="Comma-separated ISO3 codes (e.g., ESP,FRA,DEU)")
    p_fetch.add_argument("--debug", action="store_true", help="Suffix output filenames with _debug")
    p_fetch.set_defaults(func=cmd_fetch)
# in parser wiring:
    p_plot = sub.add_parser("plot", help="Plot indicators from latest CSVs")
    p_plot.add_argument("--countries", help="Comma-separated ISO3 codes (e.g., ESP,FRA,DEU)")
    p_plot.set_defaults(func=cmd_plot)
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
