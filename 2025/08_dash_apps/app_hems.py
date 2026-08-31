from dash import Dash, html, dcc, Input, Output
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd

# ---------- Synthetic day of data (hourly) ----------
rng = pd.date_range("2024-05-01", periods=24, freq="h")
hours = np.arange(24)

# Demand profile (evening peak)
demand = 1.8 + 0.4*np.exp(-0.5*((hours-8)/2.3)**2) + 1.1*np.exp(-0.5*((hours-19)/2.6)**2)
demand += np.random.default_rng(0).normal(0, 0.05, size=24)   # noise
demand = np.clip(demand, 0, None)  # kW

# Forecast (noisy version of demand, as if day-ahead)
forecast = demand + np.random.default_rng(1).normal(0, 0.1, size=24)

# Simple PV bell curve (kW)
pv = 0.0 + 2.8*np.exp(-0.5*((hours-13)/3.0)**2)  # midday peak ~2.8 kW

df_base = pd.DataFrame({"time": rng, "demand_kW": demand, "forecast_kW": forecast, "pv_kW": pv}).set_index("time")

# ---------- Battery simulator ----------
def simulate_battery(df, cap_kwh=5.0, eta=0.95, soc0_ratio=0.5, dt_h=1.0):
    """
    Very simple self-consumption battery:
    - charge from PV surplus (pv > demand), up to capacity
    - discharge to cover demand (or forecast) when pv < demand
    - unlimited power rate for simplicity (educational)
    - round-trip modeled as symmetric efficiency factor on charge+discharge
    """
    demand = df["demand_kW"].values.copy()
    pv = df["pv_kW"].values.copy()
    n = len(demand)

    soc = np.zeros(n+1)
    soc[0] = soc0_ratio * cap_kwh  # initial SoC in kWh
    grid = np.zeros(n)             # net grid import (+ import, negative means export)
    ch = np.zeros(n)               # battery charge power (kW)
    dis = np.zeros(n)              # battery discharge power (kW)

    for t in range(n):
        load = demand[t]
        gen  = pv[t]
        net  = load - gen  # positive means net load; negative means surplus PV

        if net > 0:
            # Need energy -> try to discharge battery
            # available discharge energy this hour (kWh) respecting SoC and efficiency
            e_need = net * dt_h                      # kWh
            e_avail = soc[t] * eta                   # usable energy considering efficiency
            e_use = min(e_need, e_avail)
            dis[t] = e_use / dt_h                    # kW
            soc[t+1] = soc[t] - e_use/eta            # battery loses e_use/eta from SoC
            grid[t] = net - dis[t]                   # remaining from grid
        else:
            # Surplus PV -> try to charge battery
            e_surplus = -net * dt_h                  # kWh
            e_room = (cap_kwh - soc[t])              # kWh free
            e_store = min(e_surplus * eta, e_room)   # store with charge efficiency
            ch[t] = e_store / dt_h                   # kW
            soc[t+1] = soc[t] + e_store              # SoC increases by e_store
            grid[t] = net + ch[t]                    # net after charging (often still <= 0)

    out = df.copy()
    out["grid_kW"] = grid
    out["bat_charge_kW"] = ch
    out["bat_discharge_kW"] = dis
    out["soc_kWh"] = soc[1:]
    return out

def kpis(df_sim):
    # Energy terms (kWh) with 1h timestep
    load = df_sim["demand_kW"].sum()
    pv = df_sim["pv_kW"].sum()
    grid_import = df_sim["grid_kW"].clip(lower=0).sum()
    grid_export = (-df_sim["grid_kW"].clip(upper=0)).sum()
    self_consumed = pv - grid_export
    self_consumption_ratio = self_consumed / pv if pv > 0 else 0.0
    peak_grid = df_sim["grid_kW"].max()
    return dict(
        load_kWh=load,
        pv_kWh=pv,
        grid_import_kWh=grid_import,
        grid_export_kWh=grid_export,
        self_consumption_pct=100* self_consumption_ratio,
        peak_grid_kW=peak_grid
    )

# ---------- Dash app ----------
app = Dash(__name__)
app.title = "HEMS Mini"

app.layout = html.Div([
    html.H2("Home Energy Mini-Dashboard"),
    html.P("Adjust battery capacity to see how grid import and self-consumption change."),

    html.Div([
        html.Div([
            html.Label("Battery capacity (kWh)"),
            dcc.Slider(
                id="cap",
                min=0, max=20, step=1, value=5,
                marks={0:"0", 5:"5", 10:"10", 15:"15", 20:"20"},
                tooltip={"placement": "bottom", "always_visible": True}
            ),
        ], style={"width": "420px", "marginRight": "24px"}),

        html.Div([
            html.Label("Round-trip efficiency (0.80–1.00)"),
            dcc.Slider(
                id="eta",
                min=0.80, max=1.00, step=0.01, value=0.95,
                marks={0.80:"0.80", 0.9:"0.90", 1.0:"1.00"},
                tooltip={"placement": "bottom", "always_visible": False}
            ),
        ], style={"width": "420px", "marginRight": "24px"}),

        html.Div([
            html.Label("Initial SoC (%)"),
            dcc.Slider(
                id="soc0",
                min=0, max=100, step=5, value=50,
                marks={0:"0", 50:"50", 100:"100"},
                tooltip={"placement": "bottom", "always_visible": False}
            ),
        ], style={"width": "420px"}),
    ], style={"display": "flex", "flexWrap": "wrap", "alignItems": "center", "gap": "16px"}),

    dcc.Graph(id="timeseries", style={"height": "420px", "marginTop": "10px"}),

    html.Div(id="kpi", style={"display": "flex", "gap": "24px", "flexWrap": "wrap", "marginTop": "8px"})
], style={"maxWidth": "1200px", "margin": "0 auto", "fontFamily": "sans-serif"})

@app.callback(
    Output("timeseries", "figure"),
    Output("kpi", "children"),
    Input("cap", "value"),
    Input("eta", "value"),
    Input("soc0", "value"),
)
def update(cap, eta, soc0):
    df_sim = simulate_battery(df_base, cap_kwh=float(cap), eta=float(eta), soc0_ratio=float(soc0)/100.0)

    # KPIs
    m = kpis(df_sim)
    kpi_boxes = [
        html.Div([
            html.H4("Load (kWh)"),
            html.P(f"{m['load_kWh']:.1f}")
        ], style=box_style()),
        html.Div([
            html.H4("PV (kWh)"),
            html.P(f"{m['pv_kWh']:.1f}")
        ], style=box_style()),
        html.Div([
            html.H4("Grid import (kWh)"),
            html.P(f"{m['grid_import_kWh']:.1f}")
        ], style=box_style()),
        html.Div([
            html.H4("Grid export (kWh)"),
            html.P(f"{m['grid_export_kWh']:.1f}")
        ], style=box_style()),
        html.Div([
            html.H4("Self-consumption (%)"),
            html.P(f"{m['self_consumption_pct']:.1f}%")
        ], style=box_style()),
        html.Div([
            html.H4("Peak grid (kW)"),
            html.P(f"{m['peak_grid_kW']:.2f}")
        ], style=box_style()),
    ]

    # Figure
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_sim.index, y=df_sim["demand_kW"], name="Demand [kW]", line=dict(color="#1f77b4")))
    fig.add_trace(go.Scatter(x=df_sim.index, y=df_sim["forecast_kW"], name="Forecast [kW]", line=dict(color="#ff7f0e", dash="dot")))
    fig.add_trace(go.Scatter(x=df_sim.index, y=df_sim["pv_kW"], name="PV [kW]", line=dict(color="#2ca02c")))
    fig.add_trace(go.Scatter(x=df_sim.index, y=df_sim["grid_kW"], name="Grid after battery [kW]", line=dict(color="#d62728")))
    fig.add_trace(go.Scatter(x=df_sim.index, y=df_sim["bat_charge_kW"], name="Battery charge [kW]", line=dict(color="#9467bd"), visible="legendonly"))
    fig.add_trace(go.Scatter(x=df_sim.index, y=df_sim["bat_discharge_kW"], name="Battery discharge [kW]", line=dict(color="#8c564b"), visible="legendonly"))
    fig.add_trace(go.Scatter(x=df_sim.index, y=df_sim["soc_kWh"], name="SoC [kWh]", line=dict(color="#17becf"), yaxis="y2"))

    fig.update_layout(
        title=f"HEMS Simulation — Battery {cap} kWh, η={eta:.2f}, SoC0={soc0}%",
        xaxis_title="Time",
        yaxis_title="Power [kW]",
        legend=dict(orientation="h", y=0.95, x=1, xanchor="right", yanchor="bottom"),
        margin=dict(l=40, r=40, t=80, b=40),
        template="plotly_white",
        yaxis2=dict(
            title="State of Charge [kWh]",
            overlaying="y",
            side="right",
            showgrid=False
        ),
    )
    return fig, kpi_boxes

def box_style():
    return {
        "background": "#f7f7f9",
        "padding": "10px 14px",
        "border": "1px solid #e6e6e6",
        "borderRadius": "10px",
        "minWidth": "160px",
    }

if __name__ == "__main__":
    app.run_server(debug=True)
