import pandas as pd
import os
import plotly.express as px
from macroeconomics.core.common import FIGURE_DIR, COUNTRIES_ISO3, INDICATORS, DATA_DIR
from macroeconomics.logging_config import logger
from pathlib import Path
from macroeconomics.viz.theme import find_latest_files_and_year
os.makedirs(FIGURE_DIR, exist_ok=True)



def notInDictionary(codes, dict):
    '''Ensure the country codes are in the dictionary'''
    missing_countries = set(codes) - set(dict.keys())
    if missing_countries:
        logger.warning("These country codes are missing from the dictionary:", missing_countries)

def makePlotly(df_input, indicator, indicators_dict, df_indicators, latest_year, save_html=True, suffix=None):
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
    # Cleanup legend: one entry per country that controls both solid & dashed
    legend_shown_countries = set()
    for trace in fig.data:
        # Normalize: remove PX suffixes so both styles share one name/group
        base_name = trace.name.replace(", solid", "").replace(", dash", "")
        trace.name = base_name
        trace.legendgroup = base_name
        # Show only one legend entry per country
        if base_name not in legend_shown_countries:
            trace.showlegend = True
            legend_shown_countries.add(base_name)
        else:
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
            groupclick="togglegroup",
            font=dict(size=14),
            bgcolor='rgba(255,255,255,0.7)',
        )
    )
    if save_html:
        plotname= FIGURE_DIR/('plot_'+indicator+suffix+".html")
        fig.write_html(plotname)
        logger.info(f"file saved to:{plotname}")
    return fig


def plot_main(args):

    country_codes = args.countries.split(",") if args.countries else COUNTRIES_ISO3
    indicator_codes = INDICATORS
    logger.info(country_codes)

    latest_files, latest_year = find_latest_files_and_year(DATA_DIR)

    TIMESERIES_FILE = latest_files.get("timeseries")
    COUNTRIES_FILE = latest_files.get("countries")
    INDICATORS_FILE = latest_files.get("indicators")

    logger.info(f"Using files from year: {latest_year}")
    logger.info(f"Timeseries file: {TIMESERIES_FILE}")
    logger.info(f"Countries file: {COUNTRIES_FILE}")
    logger.info(f"Indicators file: {INDICATORS_FILE}")

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
    country_suffix='_all' if country_codes is COUNTRIES_ISO3 else f"_{'_'.join(country_dict.keys())}"
    notInDictionary(indicator_codes,indicators_dict)
    df_timeseries['country_name'] = df_timeseries['country'].map(country_dict)

    for indicator in indicators_dict.keys():
        makePlotly(df_timeseries, indicator,indicators_dict, df_indicators, latest_year, save_html=True, suffix=country_suffix)
