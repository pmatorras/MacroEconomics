import pandas as pd
import sys,re
import matplotlib.pyplot as plt
import argparse
import plotly.express as px
import common
from pathlib import Path

def find_latest_files_and_year(data_folder, prompt_on_mismatch=True):
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
            print(f"Warning: Different data years found in files: {years}")
            cont = input("Continue with these files? (y/n): ")
            if cont.lower() != 'y':
                raise RuntimeError("Execution stopped by user due to mismatched file years.")
    latest_year = max_year = max(int(y) for y in years.values()) if years else None
    return latest_files, latest_year

def notInDictionary(codes, dict):
    '''Ensure the country codes are in the dictionary'''
    missing_countries = set(codes) - set(dict.keys())
    if missing_countries:
        print("Warning: these country codes are missing from the dictionary:", missing_countries)

def makePlotly(df_input, indicator, save_html=True, suffix=None):
    '''Make an automatised plot using plotly given the df and the variable to plot. Uses IMF data'''
    df= df_input[df_input["indicator"]==indicator]
    df = df.copy()
    df['line_style'] = df['year'].apply(lambda y: 'dash' if y >= latest_year else 'solid')
    boundary_rows = df[df['year'] == latest_year]
    df = pd.concat([
        df,
        boundary_rows.assign(line_style='solid'),
        boundary_rows.assign(line_style='dash')
    ], ignore_index=True)
    df = df.sort_values(['country_name', 'year']).reset_index(drop=True)

    units = df_indicators.loc[df_indicators['id'] == indicator, 'unit'].iloc[0]
    fig = px.line(df, x='year', y='value', color='country_name', line_dash='line_style',
            labels={'value': units, 'year': 'Year', 'country': 'Country'})
    #Cleanup legend
    for trace in fig.data:
        if trace.line.dash == 'solid' and trace.name.endswith(", solid"):
            trace.name = trace.name.replace(", solid", "")
        if trace.line.dash != 'solid':
            trace.showlegend = False
    fig.update_layout(
        title=dict(text=''),
        xaxis_type='category',
        annotations=[dict(
            text=indicators_dict[indicator],
            x=0.5,
            y=1.01,
            xref='paper',
            yref='paper',
            showarrow=False,
            font=dict(size=26),
            xanchor='center',
            yanchor='bottom')],
        xaxis=dict(
            title_font=dict(size=16, family='Arial', color='black', weight='bold'),
            tickfont=dict(size=14, family='Arial', color='black')
        ),
        yaxis=dict(
            title_font=dict(size=16, family='Arial', color='black', weight='bold'),
            tickfont=dict(size=14, family='Arial', color='black')
        ),
        legend_title_text='Country Name',
        legend=dict(
            font=dict(size=14),
            bgcolor='rgba(255,255,255,0.7)',
        )
    )
    if save_html:
        plotname= common.FIGURE_FOLDER/('plot_'+indicator+suffix+".html")
        fig.write_html(plotname)
        print("file saved to:",plotname)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare GDP and Inflation for selected countries")
    parser.add_argument("-c", "--countries", type=str, help="Comma-separated list of country codes (e.g., ESP,DEU,ITA)")
    args = parser.parse_args()
    country_codes = args.countries.split(",") if args.countries else common.countries_iso3
    indicator_codes = common.chosen_indicators
    print (country_codes)
    

    latest_files, latest_year = find_latest_files_and_year(common.DATA_FOLDER)

    TIMESERIES_FILE = latest_files.get("timeseries")
    COUNTRIES_FILE = latest_files.get("countries")
    INDICATORS_FILE = latest_files.get("indicators")

    print(f"Using files from year: {latest_year}")
    print(f"Timeseries file: {TIMESERIES_FILE}")
    print(f"Countries file: {COUNTRIES_FILE}")
    print(f"Indicators file: {INDICATORS_FILE}")

    #Protect in case the csv gets to be extremely big
    filtered_chunks = []
    for chunk in pd.read_csv(TIMESERIES_FILE, chunksize=10000):
        filtered_chunk = chunk[chunk['country'].isin(country_codes)]
        filtered_chunks.append(filtered_chunk)
    df_timeseries = pd.concat(filtered_chunks)
    df_countries = pd.read_csv(COUNTRIES_FILE)
    df_countries_fil = df_countries[df_countries['id'].isin(country_codes)]
    country_dict = pd.Series(df_countries_fil['label'].values, index=df_countries_fil['id']).to_dict()
    df_indicators = pd.read_csv(INDICATORS_FILE)
    df_indicators_fil = df_indicators[df_indicators['id'].isin(indicator_codes)]
    indicators_dict = pd.Series(df_indicators_fil['label'].values, index=df_indicators_fil['id']).to_dict()


    notInDictionary(country_codes, country_dict)
    country_suffix='_all' if country_codes is common.countries_iso3 else f"_{'_'.join(country_dict.keys())}"
    notInDictionary(indicator_codes,indicators_dict)
    df_timeseries['country_name'] = df_timeseries['country'].map(country_dict)

    for indicator in indicators_dict.keys():
        makePlotly(df_timeseries, indicator,save_html=True, suffix=country_suffix)


