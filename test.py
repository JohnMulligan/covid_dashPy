import dash_bootstrap_components as dbc
from dash import html
import dash
from dash import Dash, html, dcc, Input, Output


app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server


app.layout = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(html.Div("One of three columns"), md=4),
                dbc.Col(html.Div("One of three columns"), md=4),
                dbc.Col(html.Div("One of three columns"), md=4),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(html.Div("One of four columns"), width=6, lg=3),
                dbc.Col(html.Div("One of four columns"), width=6, lg=3),
                dbc.Col(html.Div("One of four columns"), width=6, lg=3),
                dbc.Col(html.Div("One of four columns"), width=6, lg=3),
            ]
        ),
    ]
)



if __name__ == '__main__':
	app.run_server(debug=False)