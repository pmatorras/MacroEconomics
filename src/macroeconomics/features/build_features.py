from macroeconomics.logging_config import logger
from macroeconomics.core.constants import DATA_DIR, COUNTRIES_ISO3, INDICATORS, ROOT_DIR, MODIFIED_NAME 
from macroeconomics.core.functions import get_shared_data_components
# src/macroeconomics/features/build_features.py

import math
import pandas as pd

def _is_yoy_indicator(ind: str) -> bool:
    # IMF YoY percent-change often ends with 'PCH' (e.g., PCPIEPCH)
    return ind.endswith("PCH")

def _add_level_baselines(g, baseline_year):
    g = g.sort_values("year").copy()
    s = g.set_index("year")["value"]
    base = s.get(baseline_year, None)
    g[f"baseline{str(baseline_year)}"] = base
    if base is None or base == 0:
        g[f"index{str(baseline_year)}"] = pd.NA
        g[f"rel{str(baseline_year)}"] = pd.NA
    else:
        g[f"index{str(baseline_year)}"] = ((g["value"] / base) * 100.0)
        g[f"rel{str(baseline_year)}"] = (g["value"] / base) - 1.0
    g[f"delta{str(baseline_year)}"] = g["value"] - (base if base is not None else pd.NA)
    return g.round(2)

def _chain_from_yoy(g, baseline_year = 2019):
    # g has: country, indicator, year, value (value is YoY %, e.g., 6.6 means +6.6%)
    g = g.sort_values("year").copy()
    years = g["year"].tolist()
    rates = g["value"].astype(float).tolist()
    col_nm ='index'+str(baseline_year)
    if baseline_year not in years:
        g[col_nm] = pd.NA
        return g.round(2)
    idx = {}
    k = years.index(baseline_year)
    idx[baseline_year] = 100.0
    # Forward: t = k+1..end uses YoY of that year
    for j in range(k + 1, len(years)):
        r = 0.0 if pd.isna(rates[j]) else float(rates[j])
        idx[years[j]] = (idx[years[j - 1]] * (1.0 + r / 100.0))
        
    # Backward: t = k-1..0 divides by next year's factor
    for j in range(k - 1, -1, -1):
        r_next = 0.0 if pd.isna(rates[j + 1]) else float(rates[j + 1])
        denom = (1.0 + r_next / 100.0)
        idx[years[j]] = (idx[years[j + 1]] / denom) if denom != 0 else math.nan
    g[col_nm] = g["year"].map(idx)
    g[col_nm] = g[col_nm].round(2)
    return g



def compute_additional_variables_df(df, baseline_year = 2019, do_cum = False, keep_rate_pp_delta = False):
    parts = []
    for (ctry, ind), g in df.groupby(["country", "indicator"], as_index=False):
        if _is_yoy_indicator(ind):
            g = _chain_from_yoy(g, baseline_year)
            if keep_rate_pp_delta:
                base = g.loc[g["year"] == baseline_year, "value"]
                base_val = base.iloc[0] if len(base) else pd.NA
                g[f"delta{str(baseline_year)}"] = g["value"] - base_val
        else:
            g = _add_level_baselines(g, baseline_year)
        parts.append(g)
    df_wide =  pd.concat(parts, ignore_index=True).sort_values(["country", "indicator", "year"])
    if do_cum: 
        df_wide[f"pct_cum{str(baseline_year)}"] = (df_wide[f"index{str(baseline_year)}"] -100).round(2)
    return df_wide
def add_2019_norm_long(df, baseline_year=2019, do_cum=True, include_all=False):
    keep_rate_delta = False
    wide = compute_additional_variables_df(df, baseline_year=baseline_year, do_cum=True, keep_rate_pp_delta=include_all) 

    out = [df]
    pos_columns = [f'index{str(baseline_year)}']
    if do_cum: pos_columns.extend([f"pct_cum{str(baseline_year)}"])
    if include_all: pos_columns.extend([f'delta{str(baseline_year)}'])
    for col in pos_columns:
       if col in wide.columns: 
            tmp = wide.dropna(subset=[col]).copy()
            tmp['indicator'] = tmp['indicator'].astype(str) + '_' + col
            tmp['value'] = tmp[col]
            out.append(tmp[['country','indicator','year','value']])
    return pd.concat(out, ignore_index=True).sort_values(['country','indicator','year'])

def features_main():
    data = get_shared_data_components()
    latest_files = data["latest_files"]
    print(latest_files["time_series"])
    time_series_path = latest_files["time_series"]
    indicators_path = latest_files["indicators"]
    new_timeseries_path = time_series_path.with_stem(time_series_path.stem + MODIFIED_NAME) 
    new_indicators_path = indicators_path.with_stem(indicators_path.stem + MODIFIED_NAME) 
    time_series = data["time_series"].drop(columns = ["country_name"])
    df_indicators = data["df_indicators"]
    df_long = add_2019_norm_long(time_series)

    baseline_year =2019
    indicators_dict = data["indicators_dict"]
    print(df_indicators, indicators_dict)
    dup_id = df_indicators.assign(
        id=df_indicators["id"].astype(str) + f"_index{baseline_year}",
        label=df_indicators["label"].astype(str) + f" ({baseline_year}=100)",
        dataset=df_indicators["dataset"].astype(str)+ " recalculated"
    )
    dup_pct = df_indicators.assign(
        id=df_indicators["id"].astype(str) + f"_pct_cum{baseline_year}",
        label=df_indicators["label"].astype(str) + f" (percent vs. {baseline_year})",
        unit=f"Change since {baseline_year} (pp)",
        dataset=df_indicators["dataset"].astype(str)+ " recalculated"
    )
    df_indicators_with_features = pd.concat([df_indicators, dup_id, dup_pct], ignore_index=True)
    pos_columns = [f'index{str(baseline_year)}']
    pos_columns.extend([f"pct_cum{str(baseline_year)}"])


    logger.info(f"Saving modified timeseries df to: {new_timeseries_path}")
    logger.info(f"Saving modified indicators df to: {new_timeseries_path}")

    df_long.to_csv(new_timeseries_path, index=False)
    df_indicators_with_features.to_csv(new_indicators_path,index=False)

if __name__ == "__main__":
    features_main()