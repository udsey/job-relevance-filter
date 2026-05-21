import dash_bootstrap_components as dbc


def kpi_card(title, value) -> dbc.Card:
    return dbc.Card([
            dbc.CardHeader(title),
            dbc.CardBody([str(value)])
        ],
        outline=True,
        class_name='kpi-card')
