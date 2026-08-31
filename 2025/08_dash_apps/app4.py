from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import pandas as pd
import numpy as np

# synthetic demand vs temperature (with U-shape)
np.random.seed(0)
N = 800
temp   = np.random.uniform(-15, 30, N)
demand = 1250 + 5*(temp-15)**2 + np.random.normal(0, 60, N)
weekday = np.random.choice(["Weekday","Weekend"], size=N, p=[0.7, 0.3])
df = pd.DataFrame({"temp": temp, "demand": demand, "daytype": weekday})

app = Dash(__name__)
app.layout = html.Div([
    html.H2("Demand vs Temperature"),
    html.Div([
        html.Label("Min temperature (°C)"),
        html.Div(  # wrap Slider to style the container instead of the component
            dcc.Slider(
                id="tmin",
                min=-15, max=30, step=1, value=-10,
                marks=None,
                tooltip={"placement": "bottom", "always_visible": True},
                updatemode="mouseup"  # update on mouse release (smoother)
            ),
            style={"width": "400px", "marginRight": "30px"}
        ),
        html.Label("Day type"),
        html.Div(
            dcc.Dropdown(
                id="daytype",
                options=["All", "Weekday", "Weekend"],
                value="All",
                clearable=False
            ),
            style={"width": "200px"}
        ),
    ], style={"display": "flex", "alignItems": "center", "gap": "16px", "flexWrap": "wrap"}),

    dcc.Graph(id="scatter")
])

@app.callback(
    Output("scatter", "figure"),
    Input("tmin", "value"),
    Input("daytype", "value")
)
def filter_and_plot(tmin, daytype):
    sub = df[df["temp"] >= tmin]
    if daytype != "All":
        sub = sub[sub["daytype"] == daytype]
    fig = px.scatter(
        sub, x="temp", y="demand", color="daytype",
        title=f"Demand vs Temperature (temp ≥ {tmin}°C; {daytype})",
        labels={"temp": "Temperature (°C)", "demand": "Demand [MW]"}
    )
    return fig

if __name__ == "__main__":
    app.run_server(debug=True)
