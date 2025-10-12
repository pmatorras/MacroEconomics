from macroeconomics.core.constants import COUNTRIES_ISO3, INDICATORS, DATA_DIR
from macroeconomics.logging_config import logger
from pathlib import Path

def shared_title_style(fig, indicator, indicators_dict):
    """Apply the same title formatting as makePlotly"""
    fig.update_layout(
        title=dict(text=''),  # Clear default title
        annotations=[dict(
            text=indicators_dict[indicator],
            x=0.5, y=1.01,
            xref='paper', yref='paper',
            showarrow=False,
            font=dict(size=26),
            xanchor='center',
            yanchor='bottom')]
    )
    return fig
