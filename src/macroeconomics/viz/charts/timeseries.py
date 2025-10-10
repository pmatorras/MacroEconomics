import pandas as pd
import plotly.express as px
from macroeconomics.core.common import FIGURE_DIR, COUNTRIES_ISO3, INDICATORS, DATA_DIR
from macroeconomics.logging_config import logger
from macroeconomics.viz.theme import get_shared_data_components,shared_title_style




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
    fig = shared_title_style(fig, indicator, indicators_dict)
    fig.update_layout(
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
    logger.info(country_codes)

    shared_data = get_shared_data_components()
    df_timeseries = shared_data["time_series"]
    latest_year = shared_data["latest_year"]
    
    country_dict = shared_data["country_dict"]

    df_indicators_fil = shared_data["df_indicators"]
    indicators_dict = shared_data["indicators_dict"]


    country_suffix='_all' if country_codes is COUNTRIES_ISO3 else f"_{'_'.join(country_dict.keys())}"

    for indicator in indicators_dict.keys():
        makePlotly(df_timeseries, indicator,indicators_dict, df_indicators_fil, latest_year, save_html=True, suffix=country_suffix)
