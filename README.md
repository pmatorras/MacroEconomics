# MacroEconomics

A lightweight project to display several macroeconomic indicators, intended as a starting point for a Python-based dashboard or analysis toolkit.

### Overview

This repository’s purpose is to organize code and documentation for collecting, processing, and visualizing macroeconomic time series in a clear, reproducible workflow.

### Required dependencies
the required dependencies are obtained via:
```
cd src/
pip install -r .\requirements.txt #Python 3
```

### Running the program

To Download the datasets:
```
python updateMacro.py
optional arguments:
    "-c", "--countries", type=str, help="Comma-separated list of country codes (e.g., ESP,DEU,ITA)"
    "-i", "--indicators", type=str, help="Comma-separated list of IMF indicators (e.g., PCPIEPCH)"
    "-d", "--debug", action="store_true", help="Enable debug mode"
```
Make the plots via plotly and save them locally in html:
```
python macroeconomics.py
optional arguments:
    "-c", "--countries", type=str, help="Comma-separated list of country codes (e.g., ESP,DEU,ITA)"
```
Interactive plots via dash:
```
python app.py
```
This code has been designed to be able to run interactively on [Render.com](https://macroeconomics-22w4.onrender.com)
