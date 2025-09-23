import os
import requests
import pandas as pd
from datetime import datetime
from urllib.parse import quote

FOLDER_NAME = r"../Data/"
os.makedirs(FOLDER_NAME, exist_ok=True)

BASE = "https://www.imf.org/external/datamapper/api/v1/"

def latest_weo_release_tag(today=None):
    if today is None:
        today = datetime.now()
    y, m = today.year, today.month
    if m >= 10:
        return f"{y}_october"
    elif m >= 4:
        return f"{y}_april"
    else:
        return f"{y-1}_october"

def dm_get_json(path, timeout=60):
    url = BASE + path
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.json()

def get_countries_df():
    js = dm_get_json("countries")
    rows = [{"id": k, **v} for k, v in js.get("countries", {}).items()]
    return pd.DataFrame(rows)

def get_indicators_df():
    js = dm_get_json("indicators")
    rows = [{"id": k, **v} for k, v in js.get("indicators", {}).items()]
    return pd.DataFrame(rows)

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
            print(f"Batch failed ({len(batch)} IDs): {e}")
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

def main():
    release_tag = latest_weo_release_tag()

    # Metadata
    countries = get_countries_df()
    indicators = get_indicators_df()

    countries.to_csv(FOLDER_NAME+f"imf_weo_countries_{release_tag}.csv", index=False)
    indicators.to_csv(FOLDER_NAME+f"imf_weo_indicators_{release_tag}.csv", index=False)

    # Choose indicators (remove stray/invalid IDs)
    chosen_indicators = ["LP", "NGDPD", "PPPPC", "NGDPDPC", "PCPIEPCH", "LUR"]

    # Validate indicators against metadata to avoid alias/fallback duplicates
    valid_set = set(indicators["id"].astype(str))
    chosen_indicators = [i for i in chosen_indicators if i in valid_set]
    if not chosen_indicators:
        print("No valid indicators selected; exiting.")
        return

    # Build EU members list from metadata names
    countries_iso3 = ["AUT","BEL","BGR","HRV","CYP","CZE","DNK","EST","FIN","FRA","DEU","GRC","HUN",
           "IRL","ITA","LVA","LTU","LUX","MLT","NLD","POL","PRT","ROU","SVK","SVN","ESP","SWE", "USA", "PHL", "CHN", "KOR", "CHE", "CHL", "JPN", "IND", "THA", "UZB", "VNM",  "RUS", "UKR"]
    selected_countries = countries.loc[countries["id"].isin(countries_iso3), "id"].astype(str).tolist()

    # Years: last 15 + next 5 (WEO projections)
    y = datetime.now().year
    years = list(range(1991, y + 6))

    frames = []
    for ind in chosen_indicators:
        print("processing:", ind)
        df = fetch_timeseries_chunked(ind, selected_countries, years=years, chunk_size=40)
        if df is None or df.empty:
            print(f"Empty for {ind}, skipped")
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
        out.to_csv(FOLDER_NAME+f"imf_weo_timeseries_{release_tag}.csv", index=False)
        print(f"Saved {len(out):,} rows ...")
    else:
        print("No data retrieved! check indicators/countries/year ranges.")

if __name__ == "__main__":
    main()
