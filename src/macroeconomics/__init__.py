"""
MacroEconomics Toolkit

A lightweight toolkit to fetch IMF WEO data, generate indicator plots, 
and launch an interactive Dash dashboard.
"""

__version__ = "0.2.0"
__author__ = "Pablo Matorras-Cuevas"

# Package-level configuration
from macroeconomics.core.functions import ensure_dirs

# Ensure directories exist when package is imported
ensure_dirs()
# Import main functions for easy access
from macroeconomics.logging_config import setup_logging
from macroeconomics.datasets.data import data_main
from macroeconomics.viz.charts.timeseries import plot_main  
from macroeconomics.viz.maps.europe_interactive_map import make_europe_map
#from .dash_app import main as dash_main

# Define what gets imported with "from macroeconomics import *"
__all__ = [
    '__version__'
    'setup_logging'
    'data_main',
    'plot_main', 
    'make_europe_map'
]

