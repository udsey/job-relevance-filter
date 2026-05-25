"""App style."""
import plotly.express as px
import plotly.io as pio

pio.templates["custom"] = pio.templates["plotly_dark"]
pio.templates["custom"].layout.colorway = px.colors.qualitative.Prism
pio.templates.default = "custom"

TABLE_STYLE = {
    "style_table": {
        "overflowX": "auto",
        "width": "100%",
        "minWidth": "100%",
        "margin": "20px 0 20px",
    },
    "style_cell": {
        "maxWidth": "200px",
        "maxHeight": "200px",
    },
}
