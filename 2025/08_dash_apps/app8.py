from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import pandas as pd
import numpy as np

app = Dash(__name__, suppress_callback_exceptions=True)
app.layout = html.Div([
    dcc.Location(id="url"),
    html.Div([
        dcc.Link("Demand", href="/"),
        html.Span(" | "),
        dcc.Link("Mix", href="/mix")
    ], style={"marginBottom": 12}),
    html.Div(id="page-content")
])

def demand_layout():
    rng = pd.date_range("2024-01-01", periods=24*7, freq="h")
    demand = 1200 + 240*np.sin(2*np.pi*(rng.hour/24)) + np.random.normal(0, 40, len(rng))
    fig = px.line(pd.DataFrame({"time": rng, "demand": demand}), x="time", y="demand", title="Demand (Week)")
    return html.Div([html.H3("Demand Page"), dcc.Graph(figure=fig)])

def mix_layout():
    days = pd.date_range("2024-03-01", periods=10, freq="D")
    solar = np.clip(200 + 50*np.sin(2*np.pi*(days.dayofyear/365)), 150, 300)
    wind  = 300 + 80*np.sin(2*np.pi*(days.dayofyear/14) + 1)
    hydro = 500 + np.random.normal(0, 25, len(days))
    long = (pd.DataFrame({"day": days, "Solar": solar, "Wind": wind, "Hydro": hydro})
            .melt(id_vars="day", var_name="source", value_name="MWh"))
    fig = px.area(long, x="day", y="MWh", color="source", title="Generation Mix (10 days)")
    return html.Div([html.H3("Mix Page"), dcc.Graph(figure=fig)])

@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def route(path):
    if path == "/mix":
        return mix_layout()
    else:
        return demand_layout()

if __name__ == "__main__":
    app.run_server(debug=True)
