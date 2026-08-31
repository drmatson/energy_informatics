from dash import Dash, html, dcc
import pandas as pd
import numpy as np
import plotly.express as px

# --- synthetic hourly demand (7 days)
rng = pd.date_range("2024-01-01", periods=24*7, freq="H")
demand = 1200 + 250*np.sin(2*np.pi*(rng.hour/24)) + np.random.normal(0, 40, len(rng))
df = pd.DataFrame({"time": rng, "demand_MW": demand})

app = Dash(__name__)
fig = px.line(df, x="time", y="demand_MW", title="Hourly Electricity Demand")

app.layout = html.Div([
    html.H2("Energy Demand (Interactive Plotly in Dash)"),
    dcc.Graph(figure=fig, id="demand-graph")
])

if __name__ == "__main__":
    app.run_server(debug=True)