from dash import Dash, html, dcc
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import pandas as pd
import numpy as np

idx = pd.date_range("2024-04-01", periods=30, freq="D")
dem = 1300 + 150*np.sin(2*np.pi*(np.arange(len(idx))/7)) + np.random.normal(0, 40, len(idx))
price = 50 + 0.07*(dem - dem.mean()) + np.random.normal(0, 4, len(idx))

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Scatter(x=idx, y=dem, name="Demand [MW]", mode="lines+markers"), secondary_y=False)
fig.add_trace(go.Bar(x=idx, y=price, name="Price [€/MWh]", opacity=0.5), secondary_y=True)
fig.update_layout(title_text="Demand vs Price", bargap=0.2, legend=dict(orientation="h", y=1.1))
fig.update_xaxes(title_text="Day")
fig.update_yaxes(title_text="Demand [MW]", secondary_y=False)
fig.update_yaxes(title_text="Price [€/MWh]", secondary_y=True)

app = Dash(__name__)
app.layout = html.Div([html.H2("Dual-Axis Example"), dcc.Graph(figure=fig)])

if __name__ == "__main__":
    app.run_server(debug=True)
