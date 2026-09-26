import os
import threading
import time
from collections import deque

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import serial

SERIAL_PORT = os.getenv("MULTIMETER_SERIAL_PORT", "COM7")
BAUD_RATE = int(os.getenv("MULTIMETER_BAUD_RATE", "115200"))
MAX_SAMPLES = int(os.getenv("MULTIMETER_MAX_SAMPLES", "100"))

samples = deque(maxlen=MAX_SAMPLES)
samples_lock = threading.Lock()

latest_current = "0.00 A"
latest_voltage = "0.00 V"
latest_power = "0.00 W"


def parse_measurement(line: str):
    parts = line.split()
    if len(parts) != 2:
        raise ValueError("expected '<voltage> <current>'")

    voltage, current = map(float, parts)
    return voltage, current, voltage * current


def read_serial():
    global latest_current, latest_voltage, latest_power

    while True:
        try:
            with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1.0) as ser:
                while True:
                    raw = ser.readline()
                    if not raw:
                        continue

                    try:
                        voltage, current, power = parse_measurement(
                            raw.decode("utf-8", errors="strict").strip()
                        )
                    except (UnicodeDecodeError, ValueError):
                        continue

                    with samples_lock:
                        samples.append((voltage, current, power))
                        latest_current = f"{current:.2f} A"
                        latest_voltage = f"{voltage:.2f} V"
                        latest_power = f"{power:.2f} W"

        except serial.SerialException:
            time.sleep(2.0)


threading.Thread(target=read_serial, daemon=True, name="serial-reader").start()

app = dash.Dash(__name__)

app.layout = html.Div(
    [
        html.H1("Multímetro em microcontrolador", style={"fontFamily": "Arial"}),
        dcc.Graph(id="live-graph", config={"responsive": True, "scrollZoom": True}),
        html.Div(
            [
                html.Div(
                    [
                        html.H3("Corrente atual:", style={"fontFamily": "Arial"}),
                        html.Div(
                            id="current-value",
                            style={
                                "fontSize": "24px",
                                "color": "blue",
                                "fontFamily": "Arial",
                            },
                        ),
                    ],
                    style={
                        "display": "inline-block",
                        "width": "30%",
                        "textAlign": "center",
                    },
                ),
                html.Div(
                    [
                        html.H3("Tensão atual:", style={"fontFamily": "Arial"}),
                        html.Div(
                            id="voltage-value",
                            style={
                                "fontSize": "24px",
                                "color": "blue",
                                "fontFamily": "Arial",
                            },
                        ),
                    ],
                    style={
                        "display": "inline-block",
                        "width": "30%",
                        "textAlign": "center",
                    },
                ),
                html.Div(
                    [
                        html.H3("Potência:", style={"fontFamily": "Arial"}),
                        html.Div(
                            id="power-value",
                            style={
                                "fontSize": "24px",
                                "color": "blue",
                                "fontFamily": "Arial",
                            },
                        ),
                    ],
                    style={
                        "display": "inline-block",
                        "width": "30%",
                        "textAlign": "center",
                    },
                ),
            ],
            style={"display": "flex", "justifyContent": "center"},
        ),
        dcc.Interval(id="interval", interval=1000, n_intervals=0),
    ]
)


@app.callback(
    [
        Output("live-graph", "figure"),
        Output("current-value", "children"),
        Output("voltage-value", "children"),
        Output("power-value", "children"),
    ],
    [Input("interval", "n_intervals")],
)
def update_graph(_):
    with samples_lock:
        snapshot = list(samples)
        current = latest_current
        voltage = latest_voltage
        power = latest_power

    if not snapshot:
        return go.Figure(), current, voltage, power

    voltages = [item[0] for item in snapshot]
    currents = [item[1] for item in snapshot]
    powers = [item[2] for item in snapshot]

    fig = go.Figure()
    fig.add_trace(go.Scatter(y=voltages, mode="lines", name="Tensão (V)"))
    fig.add_trace(go.Scatter(y=currents, mode="lines", name="Corrente (A)"))
    fig.add_trace(go.Scatter(y=powers, mode="lines", name="Potência (W)"))

    fig.update_layout(
        title="Histórico de tensão, corrente e potência",
        xaxis_title="Amostra",
        yaxis_title="Leitura",
        uirevision="constant",
    )

    return fig, current, voltage, power


if __name__ == "__main__":
    app.run(debug=True)
