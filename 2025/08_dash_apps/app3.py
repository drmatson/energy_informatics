from dash import Dash, html, dcc, Input, Output
import pandas as pd
import numpy as np
import plotly.express as px

# synthetic data for two weeks
rng = pd.date_range("2024-02-01", periods=24*7, freq="H")
week1 = 1100 + 240*np.sin(2*np.pi*(rng.hour/24)) + np.random.normal(0, 35, len(rng))
week2 = week1 * 1.07 + np.random.normal(0, 20, len(rng))

df1 = pd.DataFrame({"time": rng, "demand_MW": week1, "label": "Week 1"})
df2 = pd.DataFrame({"time": rng, "demand_MW": week2, "label": "Week 2"})
DATA = {"Week 1": df1, "Week 2": df2}

app = Dash(__name__)
app.layout = html.Div([
    html.H2("Demand Viewer"),
    dcc.Dropdown(
        id="week-dd",
        options=[{"label": k, "value": k} for k in DATA.keys()],
        value="Week 1", clearable=False, style={"width": 250}
    ),
    dcc.Graph(id="demand-graph")
])

@app.callback(
    Output("demand-graph", "figure"),
    Input("week-dd", "value")
)
def update_chart(week_key):
    df = DATA[week_key]
    fig = px.line(df, x="time", y="demand_MW", title=f"Hourly Demand — {week_key}")
    fig.update_layout(xaxis_title="Time", yaxis_title="Demand [MW]")
    return fig

if __name__ == "__main__":
    app.run_server(debug=True)