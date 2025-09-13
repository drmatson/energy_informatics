from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime

app = Dash(__name__)
app.layout = html.Div([
    html.H2("Live Demand (simulated)"),
    dcc.Graph(id="live"),
    dcc.Interval(id="tick", interval=5000, n_intervals=0)  # 5 seconds
])

# keep a small rolling buffer in memory
BUF = pd.DataFrame(columns=["time","demand"])

@app.callback(
    Output("live", "figure"),
    Input("tick", "n_intervals")
)
def refresh(_):
    global BUF
    now = pd.Timestamp(datetime.now().replace(microsecond=0))
    new_row = pd.DataFrame({"time":[now], "demand":[1200 + np.random.normal(0,40)]})
    BUF = pd.concat([BUF, new_row], ignore_index=True).tail(100)  # last 100 points
    fig = px.line(BUF, x="time", y="demand", title="Live Demand (last 100 points)")
    fig.update_layout(xaxis_title="Time", yaxis_title="Demand [MW]")
    return fig

if __name__ == "__main__":
    app.run_server(debug=True)