import os
import requests
import pandas as pd
from datetime import datetime
from urllib.parse import quote
from macroeconomics.logging_config import logger
from macroeconomics.core.constants import DATA_DIR, COUNTRIES_ISO3, INDICATORS
from macroeconomics.datasets.imf_api import BASE, get_countries_df, get_indicators_df, fetch_timeseries_chunked

BASE = "https://www.imf.org/external/datamapper/api/v1/"
def get_selected_indicators(args, valid_set):
    if getattr(args, "indicators", None):
        return args.indicators.split(",")
    else:
        return [i for i in INDICATORS if i in valid_set]
    
def latest_weo_release_tag(today=None):
    if today is None:
        today = datetime.now()
    y, m, d = today.year, today.month, today.day
    
    if m > 10 or (m == 10 and d >= 23):  # after Oct 20
        return f"{y}_october"
    elif m > 4 or (m == 4 and d >= 23):   # after Apr 20
        return f"{y}_april"
    else:
        return f"{y-1}_october"






def data_main(args):

    release_tag = latest_weo_release_tag()

    # Metadata
    countries = get_countries_df()
    indicators = get_indicators_df()

    suffix = '_debug' if args.debug else ''

    countries.to_csv(DATA_DIR/f"imf_weo_countries_{release_tag}.csv", index=False)
    indicators.to_csv(DATA_DIR/f"imf_weo_indicators_{release_tag}.csv", index=False)

    # Choose indicators (remove stray/invalid IDs)

    # Validate indicators against metadata to avoid alias/fallback duplicates
    valid_set = set(indicators["id"].astype(str))
    chosen_indicators = get_selected_indicators(args, valid_set)
    selected_indicators = (
        args.indicators.split(",")
        if getattr(args, "indicators", None)
        else [i for i in chosen_indicators if i in valid_set]
    )
    if not chosen_indicators:
        logger.error("No valid indicators selected; exiting.")
        return

    country_codes = args.countries.split(",") if args.countries else countries.loc[countries["id"].isin(COUNTRIES_ISO3), "id"].astype(str).tolist()
    
    # Years: last 15 + next 5 (WEO projections)
    y = datetime.now().year
    years = list(range(1990, y + 6))

    logger.info(f"Chosen indicators: {chosen_indicators}")
    frames = []
    for ind in selected_indicators:
        logger.info(f"processing: {ind}")
        df = fetch_timeseries_chunked(ind, country_codes, years=years, chunk_size=40)
        if df is None or df.empty:
            logger.warning(f"Empty for {ind}, skipped")
            continue
        # Ensure correct indicator label
        if "indicator" not in df.columns:
            df = df.assign(indicator=ind)
        else:
            # Force to expected value in case upstream mislabeled
            df["indicator"] = ind
        frames.append(df)

    # Concatenate and write once
    if frames:
        out = pd.concat(frames, ignore_index=True)
        out.drop_duplicates(subset=["indicator","country","year"], inplace=True)
        out.sort_values(["indicator","country","year"], inplace=True)
        timeseriesnm = DATA_DIR / f"imf_weo_timeseries_{release_tag}{suffix}.csv"
        out.to_csv(timeseriesnm, index=False)
        logger.info(f"Saved {len(out):,} rows to {timeseriesnm}")
    else:
        logger.error("No data retrieved! check indicators/countries/year ranges.")

