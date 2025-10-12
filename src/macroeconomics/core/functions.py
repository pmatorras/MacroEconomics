import re
import pandas as pd
from pathlib import Path
from typing import Iterable
from macroeconomics.core.constants import COUNTRIES_ISO3,INDICATORS,DATA_DIR, FIGURE_DIR, LOG_DIR,ASSETS_DIR
from macroeconomics.logging_config import logger

def ensure_dirs(paths: Iterable[Path] | None = None) -> None:
    """
    Create output directories if they don't exist (idempotent).
    """
    targets = tuple(paths) if paths else (DATA_DIR, FIGURE_DIR, LOG_DIR,ASSETS_DIR)
    for p in targets:
        p.mkdir(parents=True, exist_ok=True)

def notInDictionary(codes, dict):
    '''Ensure the country codes are in the dictionary'''
    missing_countries = set(codes) - set(dict.keys())
    if missing_countries:
        logger.warning("These country codes are missing from the dictionary:", missing_countries)
        
def get_suffix(units_dict):
    suffix_dict = {}
    for key in units_dict:
        suffix = ''
        if 'percent' in units_dict[key].lower() or '(pp)' in units_dict[key].lower():
            suffix = '%'
        elif 'billion' in units_dict[key].lower():
            suffix = ' billions'
        elif 'million' in units_dict[key].lower():
            suffix = ' millions'
        if 'dollars' in units_dict[key].lower():
            suffix = ' USD' + suffix
        suffix_dict[key] = suffix
    return suffix_dict

def do_patterns(do_features: bool = False) -> dict[str, str]:
    patterns = {
        "time_series": r"imf_weo_timeseries_(\d{4})_(april|october)\.csv",
        "countries":   r"imf_weo_countries_(\d{4})_(april|october)\.csv",
        "indicators":  r"imf_weo_indicators_(\d{4})_(april|october)\.csv",
    }
    if not do_features:
        return patterns

    # Only mutate keys that produce feature-augmented files
    mutate = {"time_series", "indicators"}
    return {
        k: re.sub(r"\.csv$", "_with_features.csv", v) if k in mutate else v
        for k, v in patterns.items()
    }

def find_latest_files_and_year(data_folder, do_features=False, prompt_on_mismatch=False):
    '''Ensure the input file is the latest IMF information'''
    data_folder = Path(data_folder)

    patterns = do_patterns(do_features)

    latest_files = {}
    years = {}

    for key, pattern in patterns.items():
        matched_files = []
        for file_path in data_folder.iterdir():
            if file_path.is_file():
                match = re.match(pattern, file_path.name)
                if match:
                    year = match.group(1)
                    mod_time = file_path.stat().st_mtime
                    matched_files.append((file_path, mod_time, year))
        if matched_files:
            latest_file = max(matched_files, key=lambda x: x[1])
            latest_files[key] = latest_file[0]
            years[key] = latest_file[2]

    # Check if years differ between files and send a warning if so
    unique_years = set(years.values())
    if len(unique_years) > 1:
        if prompt_on_mismatch:
            logger.warning(f"Different data years found in files: {years}")
            cont = input("Continue with these files? (y/n): ")
            if cont.lower() != 'y':
                raise RuntimeError("Execution stopped by user due to mismatched file years.")
    latest_year = max_year = max(int(y) for y in years.values()) if years else None
    return latest_files, latest_year

def get_shared_data_components(do_features=False, country_codes=None, indicator_codes=None):
    """Get the same data loading logic as plot.py and dash_app.py"""
    
    country_codes = country_codes or COUNTRIES_ISO3
    indicator_codes = indicator_codes or INDICATORS
    
    # Use same file loading
    latest_files, latest_year = find_latest_files_and_year(data_folder=DATA_DIR, do_features=do_features)
    TIMESERIES_FILE = latest_files.get("time_series")
    COUNTRIES_FILE = latest_files.get("countries")
    INDICATORS_FILE = latest_files.get("indicators")

    logger.info(f"Using files from year: {latest_year}")
    logger.info(f"Timeseries file: {TIMESERIES_FILE}")
    logger.info(f"Countries file: {COUNTRIES_FILE}")
    logger.info(f"Indicators file: {INDICATORS_FILE}")
    # Load same dictionaries
    #Protect in case the csv gets to be extremely big
    filtered_chunks = []
    for chunk in pd.read_csv(TIMESERIES_FILE, chunksize=10000):
        filtered_chunk = chunk[chunk['country'].isin(country_codes)]
        filtered_chunks.append(filtered_chunk)
    df_timeseries = pd.concat(filtered_chunks)
    df_countries = pd.read_csv(latest_files.get("countries"))
    df_indicators = pd.read_csv(latest_files.get("indicators"))
    df_countries_fil = df_countries[df_countries['id'].isin(country_codes)]
    if do_features:
        df_indicators_fil = df_indicators #should work given that the modified file is curated
    else:
        df_indicators_fil = df_indicators[df_indicators['id'].isin(indicator_codes)]
    # Optional: sanitize headers/types
    df_indicators.columns = df_indicators.columns.str.strip()
    df_indicators["id"] = df_indicators["id"].astype(str)
    country_dict = pd.Series(df_countries_fil['label'].values, index=df_countries_fil['id']).to_dict()
    indicators_dict = pd.Series(df_indicators_fil['label'].values, index=df_indicators_fil['id']).to_dict()
    units_dict = pd.Series( df_indicators_fil["unit"].values, index=df_indicators_fil["id"]).to_dict()
    notInDictionary(country_codes, country_dict)
    notInDictionary(indicator_codes,indicators_dict)

    df_timeseries['country_name'] = df_timeseries['country'].map(country_dict)

    # Create the same indicator options as dash_app.py
    country_options = [{"label": country_dict.get(cid, cid), "value": cid} for cid in sorted(country_dict)]
    indicator_options = [{"label": indicators_dict.get(iid, iid), "value": iid} for iid in sorted(indicators_dict)]
    default_indicator = indicator_codes[0] 
    suffix = get_suffix(units_dict)

    return {
        'time_series': df_timeseries,
        'countries': df_countries_fil,
        'country_dict': country_dict,
        'units_dict': units_dict,
        'indicators_dict': indicators_dict,
        'df_indicators': df_indicators_fil,
        'latest_year': latest_year,
        'latest_files' : latest_files,
        'country_options':country_options,
        'indicator_options': indicator_options, 
        'default_indicator': default_indicator,
        'suffix': suffix  

    }
