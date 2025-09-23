import requests, os
import pandas as pd
from datetime import datetime
from urllib.parse import quote

FOLDER_NAME=r"../Data/"
os.makedirs(FOLDER_NAME, exist_ok=True)
BASE = "https://www.imf.org/external/datamapper/api/v1/"

def latest_weo_release_tag(today=None):
    # Full WEO releases are April and October (Updates in Jan/Jul are partial)
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
    Fetch indicator timeseries for many countries by chunking the country list
    to avoid 400 errors due to URL length or validation issues.
    """
    all_rows = []
    years_q = ""
    if years:
        if isinstance(years, (list, tuple)):
            years_q = "?periods=" + ",".join(str(y) for y in years)
        else:
            years_q = "?periods=" + str(years)
    for batch in chunked(country_ids, chunk_size):
        # Join countries; quote not strictly necessary for alnum/underscore, but safe
        countries_seg = ",".join(batch)
        path = f"timeseries/{quote(indicator_id)}/{countries_seg}{years_q}"
        try:
            js = dm_get_json(path, timeout=timeout)
        except requests.HTTPError as e:
            # Skip failing batch but continue others; log minimal context
            print(f"Batch failed ({len(batch)} IDs): {e}")
            continue
        data = js.get("data") or js.get("values", {}).get(indicator_id)  # API sometimes exposes 'data' vs 'values'
        if not data:
            continue
        # 'data' usually maps country-> {year: value}
        for ctry, series in data.items():
            for year, val in series.items():
                all_rows.append({"country": ctry, "indicator": indicator_id, "year": int(year), "value": val})
    return pd.DataFrame(all_rows)

def main():
    release_tag = latest_weo_release_tag()
    # Metadata
    countries = get_countries_df()
    indicators = get_indicators_df()
    countries.to_csv(FOLDER_NAME+f"imf_weo_countries_{release_tag}.csv", index=False)
    indicators.to_csv(FOLDER_NAME+f"imf_weo_indicators_{release_tag}.csv", index=False)

    # Choose indicators (customize as needed)
    #chosen = ["NGDP_RPCH", "NGDPD"]  # real GDP growth, nominal GDP, inflation eop, debt%GDP
    chosen = ["LP", "GDP", "PPPPC", "NGDPDPC","PCPIEPCH", "LUR","d"]
    # Validate country IDs: use all IDs returned by API; optionally filter aggregates if desired
    all_ids = countries["id"].dropna().astype(str).tolist()

    # Year window: last 15 years + next 5 (adjust as needed)
    y =  datetime.now().year
    years = list(range(y - 15, y + 6))

    frames = []
    for ind in chosen:
        print("processing:", ind)
        df = fetch_timeseries_chunked(ind, all_ids, years=years, chunk_size=40)
        frames.append(df)
    if frames:
        out = pd.concat(frames, ignore_index=True)
        out.sort_values(["indicator", "country", "year"], inplace=True)
        out.to_csv(FOLDER_NAME+f"imf_weo_timeseries_{release_tag}.csv", index=False)
        print(f"Saved" +FOLDER_NAME+f"imf_weo_timeseries_{release_tag}.csv with {len(out):,} rows")
    else:
        print("No data retrieved; check indicators/countries/year ranges.")

if __name__ == "__main__":
    main()
