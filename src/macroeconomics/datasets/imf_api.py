import requests
import pandas as pd
from urllib.parse import quote
from macroeconomics.logging_config import logger

BASE = "https://www.imf.org/external/datamapper/api/v1/"

def dm_get_json(path, timeout=60):
    url = BASE + path
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.json()



def chunked(iterable, n):
    for i in range(0, len(iterable), n):
        yield iterable[i:i+n]

def fetch_timeseries_chunked(indicator_id, country_ids, years=None, chunk_size=50, timeout=60):
    """
    Fetch indicator timeseries for many countries by chunking the country list.
    Returns a tidy DataFrame with columns: country, indicator, year, value.
    """
    all_rows = []
    years_q = ""
    if years:
        if isinstance(years, (list, tuple)):
            years_q = "?periods=" + ",".join(str(y) for y in years)
        else:
            years_q = "?periods=" + str(years)

    for batch in chunked(country_ids, chunk_size):
        countries_seg = ",".join(batch)
        path = f"timeseries/{quote(indicator_id)}/{countries_seg}{years_q}"
        try:
            js = dm_get_json(path, timeout=timeout)
        except requests.HTTPError as e:
            logger.info(f"Batch failed ({len(batch)} IDs): {e}")
            continue  # skip this batch, try next

        # Prefer values[indicator_id] when present; fall back to js['data'] only if it matches shape.
        values = js.get("values", {})
        data = values.get(indicator_id)

        # If 'values' does not carry this indicator, try 'data' only if it looks like country->year dicts.
        if data is None:
            data = js.get("data")
            # Validate shape conservatively: expect dict of countries mapping to dict of year->value
            if not isinstance(data, dict) or not data:
                continue
            # Peek one item to check inner mapping looks like years
            sample_series = next(iter(data.values()))
            if not isinstance(sample_series, dict) or not sample_series:
                continue
            # Check keys look like years (numeric strings)
            sample_key = next(iter(sample_series.keys()))
            if not (isinstance(sample_key, str) and (sample_key.isdigit() or sample_key.replace("-", "").isdigit())):
                continue

        if not data:
            continue

        # Flatten
        allowed = set(batch)
        for ctry, series in data.items():
            if ctry not in allowed:
                continue
            if not isinstance(series, dict):
                continue
            for year, val in series.items():
                try:
                    yint = int(year)
                except Exception:
                    continue
                all_rows.append({
                    "country": ctry,
                    "indicator": indicator_id,
                    "year": yint,
                    "value": val
                })

    return pd.DataFrame(all_rows)
def get_countries_df():
    js = dm_get_json("countries")
    rows = [{"id": k, **v} for k, v in js.get("countries", {}).items()]
    return pd.DataFrame(rows)

def get_indicators_df():
    js = dm_get_json("indicators")
    rows = [{"id": k, **v} for k, v in js.get("indicators", {}).items()]
    return pd.DataFrame(rows)
