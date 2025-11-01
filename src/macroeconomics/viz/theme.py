from macroeconomics.core.constants import COUNTRIES_ISO3, INDICATORS, DATA_DIR
from macroeconomics.logging_config import logger
from macroeconomics.core.functions import notInDictionary


def shared_title_style(fig, indicator, indicators_dict):
    """Apply the same title formatting as makePlotly"""
    wrapped_title = wrap_title(indicators_dict[indicator], width=40)
    fig.update_layout(
        title=dict(text=''),  # Clear default title
        annotations=[dict(
            text=wrapped_title,
            x=0.5, y=1.005,
            xref='paper', yref='paper',
            showarrow=False,
            font=dict(size=24),
            xanchor='center',
            yanchor='bottom')]
    )
    return fig

def wrap_title(name: str, unit: str | None = None, width: int = 25) -> str:
    """Wrap title at the last space before width, using HTML line breaks"""
    label = name.strip()
    if len(label) > width and " " in label:
        i = label.rfind(" ", 0, width)
        if i != -1:
            label = label[:i] + "<br>" + label[i+1:]
    if unit:
        label += f"<br>({unit})"
    return label
