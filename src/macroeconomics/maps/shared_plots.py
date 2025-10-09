from macroeconomics.plot import find_latest_files_and_year, notInDictionary
from macroeconomics.common import COUNTRIES_ISO3, INDICATORS, DATA_DIR
import pandas as pd
def get_shared_data_components(country_codes=None, indicator_codes=None):
    """Get the same data loading logic as plot.py and dash_app.py"""
    from macroeconomics.common import COUNTRIES_ISO3, INDICATORS, DATA_DIR
    
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
