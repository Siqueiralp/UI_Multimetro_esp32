import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import serial
import threading
import pandas as pd
import time
#pip install dash plotly pyserial pandas
# ordem de leitura: tensao, corrente
# Configure Serial Port
SERIAL_PORT = "COM7"  # Change this based on your system
BAUD_RATE = 115200

# Global variables for storing data
data = pd.DataFrame(columns=["Voltage", "Current"])
latest_current = {"value": "0.0"}  # To store latest current value
latest_voltage = {"value": "0.0"}  # To store latest current value
latest_power = {"value": "0.0"}  # To store latest current value
# Function to read serial data
def read_serial():
    global data, latest_current, latest_voltage, latest_power
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2000)
        while True:
            line = ser.readline().decode("utf-8").strip()
            if line:
                try:
                    voltage, current = map(float, line.split())
                    new_data = pd.DataFrame({"Voltage": [voltage], "Current": [current], "Power":[(voltage*current)]})
                    data = pd.concat([data, new_data], ignore_index=True).tail(100)
                    latest_current["value"] = f"{current:.2f} A"
                    latest_voltage["value"] = f"{voltage:.2f} V"
                    latest_power["value"] = f"{(current*voltage):.2f} W"
                except ValueError:
                    pass  # Ignore malformed data
    except serial.SerialException as e:
        #print(f"Serial error: {e}")
        pass

# Start the serial reading thread
#threading.Thread(target=read_serial, daemon=True).start()

# Dash app setup
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Multímetro em microcontrolado", style={"fontFamily": "Arial"}),
    dcc.Graph(id="live-graph", config={'responsive': True, 'scrollZoom': True}),
    html.Div([
        html.Div([
            html.H3("Corrente atual:", style={"fontFamily": "Arial"}),
            html.Div(id="current-value", style={"fontSize": "24px", "color": "blue", "fontFamily": "Arial"})
        ], style={"display": "inline-block", "width": "30%", "textAlign": "center"}),
        html.Div([
            html.H3("Tensão atual:", style={"fontFamily": "Arial"}),
            html.Div(id="voltage-value", style={"fontSize": "24px", "color": "blue", "fontFamily": "Arial"})
        ], style={"display": "inline-block", "width": "30%", "textAlign": "center"}),
        html.Div([
            html.H3("Potência:", style={"fontFamily": "Arial"}),
            html.Div(id="power-value", style={"fontSize": "24px", "color": "blue", "fontFamily": "Arial"})
        ], style={"display": "inline-block", "width": "30%", "textAlign": "center"})
    ], style={"display": "flex", "justifyContent": "center"}),
    dcc.Interval(id="interval", interval=1000, n_intervals=0)  # Refresh every second
])

@app.callback(
    [Output("live-graph", "figure"), Output("current-value", "children"),Output("voltage-value", "children"),Output("power-value", "children")],
    [Input("interval", "n_intervals")]
)
def update_graph(n):
    global data
    read_serial()
    if data.empty:
         return go.Figure(), "0.00 A", "0.00 V", "0.00 W"

    fig = go.Figure()
    fig.add_trace(go.Scatter(y=data["Voltage"], mode="lines", name="Tensão (V)"))
    fig.add_trace(go.Scatter(y=data["Current"], mode="lines", name="Corrente (A)"))
    fig.add_trace(go.Scatter(y=data["Power"], mode="lines", name="Potência (W)"))
    

    fig.update_layout(
        title="Histórico de tensão e corrente",
        xaxis_title="Time",
        yaxis=dict(title="Leitura"),
        yaxis2=dict(title="Corrente (A)", overlaying="y", side="right"),
        uirevision='constant',
    )

    return fig, latest_current["value"], latest_voltage["value"], latest_power["value"]

if __name__ == "__main__":
    app.run_server(debug=True)
