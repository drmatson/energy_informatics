from dash import Dash, html, dcc, Input, Output
import pandas as pd
import numpy as np
import plotly.express as px

# 90 days hourly series
idx = pd.date_range("2024-01-01", periods=24*90, freq="H")
demand = 1200 + 260*np.sin(2*np.pi*(idx.hour/24)) + np.random.normal(0, 45, len(idx))
df = pd.DataFrame({"time": idx, "demand": demand})

app = Dash(__name__)
app.layout = html.Div([
    html.H2("Time Window Viewer"),
    dcc.DatePickerRange(
        id="range",
        start_date=idx.min().date(),
        end_date=idx.max().date(),
        display_format="YYYY-MM-DD"
    ),
    dcc.Graph(id="ts")
])

@app.callback(
    Output("ts", "figure"),
    Input("range", "start_date"),
    Input("range", "end_date")
)
def update_range(start_date, end_date):
    sub = df[(df["time"] >= start_date) & (df["time"] <= (pd.to_datetime(end_date) + pd.Timedelta(days=1)))]
    fig = px.line(sub, x="time", y="demand", title=f"Demand: {start_date} → {end_date}")
    fig.update_layout(xaxis_title="Time", yaxis_title="Demand [MW]")
    return fig

if __name__ == "__main__":
    app.run_server(debug=True)