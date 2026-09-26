# ESP32 Multimeter Dashboard

Dash/Plotly interface for voltage and current samples received over a serial link from a microcontroller. Power is calculated as `V × I` and the latest samples are plotted continuously.

## Serial protocol

Each line must contain two floating-point values separated by whitespace:

```text
<voltage> <current>
```

Example:

```text
12.04 0.83
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Configuration is read from environment variables:

- `MULTIMETER_SERIAL_PORT` (default: `COM7`)
- `MULTIMETER_BAUD_RATE` (default: `115200`)
- `MULTIMETER_MAX_SAMPLES` (default: `100`)

The serial reader runs in a background thread so the Dash callback remains responsive even when the device is disconnected.
