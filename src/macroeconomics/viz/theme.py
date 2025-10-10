from macroeconomics.core.common import COUNTRIES_ISO3, INDICATORS, DATA_DIR
from macroeconomics.logging_config import logger
import pandas as pd
import re
from pathlib import Path


def find_latest_files_and_year(data_folder, prompt_on_mismatch=False):
    '''Ensure the input file is the latest IMF information'''
    data_folder = Path(data_folder)
    patterns = {
        "timeseries": r"imf_weo_timeseries_(\d{4})_(april|october)\.csv",
        "countries": r"imf_weo_countries_(\d{4})_(april|october)\.csv",
        "indicators": r"imf_weo_indicators_(\d{4})_(april|october)\.csv"
    }

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

def get_shared_data_components(country_codes=None, indicator_codes=None):
    """Get the same data loading logic as plot.py and dash_app.py"""
    
    country_codes = country_codes or COUNTRIES_ISO3
    indicator_codes = indicator_codes or INDICATORS
    
    # Use same file loading
    latest_files, latest_year = find_latest_files_and_year(DATA_DIR)
    # Load same dictionaries
    print(latest_files)
    df = pd.read_csv(latest_files.get("timeseries"))

    df_countries = pd.read_csv(latest_files.get("countries"))
    df_countries_fil = df_countries[df_countries['id'].isin(country_codes)]
    country_dict = pd.Series(df_countries_fil['label'].values, index=df_countries_fil['id']).to_dict()
    
    df_indicators = pd.read_csv(latest_files.get("indicators"))
    df_indicators_fil = df_indicators[df_indicators['id'].isin(indicator_codes)]
    indicators_dict = pd.Series(df_indicators_fil['label'].values, index=df_indicators_fil['id']).to_dict()
    units_dict = pd.Series(
        df_indicators_fil["unit"].values,
        index=df_indicators_fil["id"]
    ).to_dict()
    # Create the same indicator options as dash_app.py
    indicator_options = [{"label": indicators_dict.get(iid, iid), "value": iid} for iid in sorted(indicators_dict)]
    default_indicator = indicator_codes[0]  # Same as dash_app default
    
    return {
        'time_series': df,
        'country_dict': country_dict,
        'units_dict': units_dict,
        'indicators_dict': indicators_dict,
        'df_indicators': df_indicators,
        'latest_year': latest_year,
        'indicator_options': indicator_options, 
        'default_indicator': default_indicator  
    }

def apply_shared_title_style(fig, indicator, indicators_dict):
    """Apply the same title formatting as makePlotly"""
    fig.update_layout(
        title=dict(text=''),  # Clear default title
        annotations=[dict(
            text=indicator,
            x=0.5, y=1.01,
            xref='paper', yref='paper',
            showarrow=False,
            font=dict(size=26),
            xanchor='center', yanchor='bottom'
        )]
    )
    return fig
