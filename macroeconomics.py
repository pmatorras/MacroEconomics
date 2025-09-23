import pandas as pd
import sys
import matplotlib.pyplot as plt
import argparse

# File paths
GDP_FILE_PATH = "Data/gdp.csv"
INFLATION_FILE_PATH = "Data/API_FP.CPI.TOTL.ZG_DS2_en_csv_v2_59.csv"
FIGURE_FOLDER = "Figures/"

def check_valid_countries(df, country_codes):
    """Exit if any country code not in dataset."""
    available_countries = df['Country_Code'].unique()
    invalid_countries = [c for c in country_codes if c not in available_countries]
    if invalid_countries:
        print(f"❌ Error: The following country codes are not in the dataset: {', '.join(invalid_countries)}")
        print(f"✅ Available country codes: {', '.join(sorted(available_countries))}")
        sys.exit()

def get_country_suffix(country_codes):
    """Generate underscore-separated suffix from country codes."""
    return "_".join(country_codes)

def plot_gdp_comparison(file_path, country_codes=['ESP', 'FRA']):
    """Plot GDP data for selected countries since 2019."""
    df = pd.read_csv(file_path)
    df_filtered = df[['REF_AREA', 'Reference area', 'TIME_PERIOD', 'OBS_VALUE']].rename(
        columns={'REF_AREA': 'Country_Code', 'Reference area': 'Country', 'TIME_PERIOD': 'Year', 'OBS_VALUE': 'GDP'}
    )
    df_filtered['Year'] = pd.to_numeric(df_filtered['Year'], errors='coerce')
    df_filtered['GDP'] = pd.to_numeric(df_filtered['GDP'], errors='coerce')
    check_valid_countries(df_filtered, country_codes)
    country_suffix = get_country_suffix(country_codes)
    df_selected = df_filtered[(df_filtered['Country_Code'].isin(country_codes)) & (df_filtered['Year'] >= 2019)]

    if df_selected.empty:
        print(f"Error: No GDP data found for countries {', '.join(country_codes)}")
        return

    df_pivot = df_selected.pivot(index='Year', columns='Country_Code', values='GDP')

    plt.figure(figsize=(10, 5))
    for country in country_codes:
        plt.plot(df_pivot.index, df_pivot[country], marker='o', label=f"{country} GDP")
    plt.xlabel("Year")
    plt.ylabel("GDP (in million units)")
    plt.title("GDP of Selected Countries since 2019")
    plt.xticks(df_pivot.index)
    plt.legend()
    plt.grid()
    plt.savefig(f"{FIGURE_FOLDER}gdp_since_2019_{country_suffix}.png", dpi=300, bbox_inches="tight")
    plt.close()

def plot_inflation(file_path, country_codes=['ESP', 'FRA']):
    """Plot inflation rates for selected countries in 2019."""
    df = pd.read_csv(file_path, skiprows=4)
    df_filtered = df[['Country Code', '2019']].rename(columns={'Country Code': 'Country_Code', '2019': 'Inflation'})

    country_suffix = get_country_suffix(country_codes)
    df_filtered = df_filtered[df_filtered['Country_Code'].isin(country_codes)]

    if df_filtered.empty:
        print(f"Error: No Inflation data found for countries {', '.join(country_codes)}")
        return

    plt.figure(figsize=(10, 5))
    plt.bar(df_filtered['Country_Code'], df_filtered['Inflation'])
    plt.xlabel("Country")
    plt.ylabel("Inflation Rate (%)")
    plt.title("Inflation Rate for Selected Countries in 2019")
    plt.grid(axis='y')
    plt.savefig(f"{FIGURE_FOLDER}inflation_2019_{country_suffix}.png", dpi=300, bbox_inches="tight")
    plt.close()

def plot_cumulative_inflation(file_path, country_codes=['ESP', 'FRA']):
    """Plot cumulative inflation from 2019 to 2023."""
    year_min, year_max = 2019, 2024
    df = pd.read_csv(file_path, skiprows=4)
    df_filtered = df[['Country Code'] + [str(year) for year in range(year_min, year_max)]]
    country_suffix = get_country_suffix(country_codes)
    df_filtered = df_filtered[df_filtered['Country Code'].isin(country_codes)]

    if df_filtered.empty:
        print(f"Error: No Inflation data found for countries {', '.join(country_codes)}")
        return
    
    plt.figure(figsize=(10, 5))
    for _, row in df_filtered.iterrows():
        country = row['Country Code']
        cumulative_inflation = [0]
        for year in range(year_min + 1, year_max):
            cumulative_inflation.append((1 + cumulative_inflation[-1] / 100) * (1 + row[str(year)] / 100) * 100 - 100)
        plt.plot(range(year_min, year_max), cumulative_inflation, marker='o', label=country)

    plt.xlabel("Year")
    plt.ylabel("Cumulative Inflation (%)")
    plt.title("Cumulative Inflation Since 2019")
    plt.xticks(range(year_min, year_max))
    plt.legend()
    plt.grid()
    plt.savefig(f"{FIGURE_FOLDER}cumulative_inflation_{country_suffix}.png", dpi=300, bbox_inches="tight")
    plt.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare GDP and Inflation for selected countries")
    parser.add_argument("-c", "--countries", type=str, help="Comma-separated list of country codes (e.g., ESP,DEU,ITA)")
    args = parser.parse_args()
    country_codes = args.countries.split(",") if args.countries else ['ESP', 'FRA']
    plot_gdp_comparison(GDP_FILE_PATH, country_codes)
    plot_inflation(INFLATION_FILE_PATH, country_codes)
    plot_cumulative_inflation(INFLATION_FILE_PATH, country_codes)

    print(f"✅ Plots saved as '{FIGURE_FOLDER}gdp_since_2019_{get_country_suffix(country_codes)}.png', "
          f"'{FIGURE_FOLDER}inflation_2019_{get_country_suffix(country_codes)}.png' and "
          f"'{FIGURE_FOLDER}cumulative_inflation_{get_country_suffix(country_codes)}.png'")
