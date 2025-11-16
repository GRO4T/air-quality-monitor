
# Air Quality Monitor

This repository contains the code and instructions to build a simple air quality
monitor using a Plantower PMS5003 sensor and a Raspberry Pi.

## Quick overview

- Sensor: PMS5003 (particulate matter / PM2.5, PM10)
- Target platform: Raspberry Pi (3B+ or any 40-pin Pi with UART)
- Components: Python scripts, a small helper `aqm` binary, and a local InfluxDB
	stack for storing measurements.

## Prerequisites

- PMS5003 air quality sensor
- Raspberry Pi (3B+, 4, or similar) with UART pins exposed

On the Pi you should have:
- Python 3
- Docker & Docker Compose (for InfluxDB in this project)

## Setup

Below are the common steps to prepare the Pi and get the project running.

### 1) Connect PMS5003 sensor to Raspberry Pi

#### PMS5003 Pinout ([source](https://elty.pl/upload/download/PMS5003_LOGOELE.pdf))

![PMS5003 pins](docs/pms5003_pins.png)

| Pin number | Function                                | Explain                                                |
| ---------- | --------------------------------------- | ------------------------------------------------------ |
| PIN1       | VCC                                     | Power supply DC5V                                      |
| PIN2       | GND                                     | Negative power supply                                  |
| PIN3       | SET (Internal 50K pull-up)              | Set pin, 3.3V level                                    |
| PIN4       | RXD / I2C_SCL                           | Digital pin, 3.3V level                                |
| PIN5       | TXD / I2C_SDL                           | Digital pin, 3.3V level                                |
| PIN6       | RESET                                   | Module reset signal, 3.3V level                        |
| PIN7       | PWM                                     | PWM output, 3.3V level (only for single sensor output) |
| PIN8       | Mode selection (Internal 50K pull-up)   | High or NC: Serial port mode (3.3V). Low: I2C mode.    |

#### Raspberry Pi Pinout

As of writing this, all Raspberry Pi boards use the same 40-pin layout ([source](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio-pads-control)).

![Raspberry Pi Pinout](docs/raspberry_pinout.png)

#### Connection

In order to connect the sensor to the board, connect the corresponding power (VCC) and ground (GND) pins, then wire the sensor's TX pin to the Raspberry Pi's RX pin. The PMS5003 only transmits data and does not accept serial input.

![](docs/pms5003_to_raspberrypi.png)

### 2) Copy project files to the Pi

Use the included Makefile target:

```
make sync HOST=<host>
```

### 3) SSH with port-forwarding (InfluxDB UI)

This project uses InfluxDB which exposes a web UI on port `8086` by default.
To access the UI from your workstation via SSH forwarding run:

```
ssh -L 8086:localhost:8086 pi@<host>
```

### 4) Install Python dependencies (on the Pi)

On the Pi, from the project directory:

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

(Make sure `python3-venv` is installed on the Pi if `venv` creation fails.)

### 5) Deploy InfluxDB (Docker Compose)

From the project directory on the Pi:

```
docker compose up -d
```

This will bring up the InfluxDB service and any other containers defined in
`docker-compose.yml`.

### 6) Schedule sensor measurements in cron

Edit the Pi user's crontab (`crontab -e`) and add:

```
* * * * * cd $HOME/air-quality-monitor && ./aqm
```

This runs the `aqm` helper once every minute (adjust schedule as needed).

### 7) (Optional) Create a Wi-Fi hotspot on the Pi

If you want to access InfluxDB UI without SSH and port forwarding:

```
sudo nmcli device wifi hotspot ssid <SSID> password <PASSWORD> ifname wlan0
```

Then find the Pi's IP via `ifconfig` or `hostname -I` and connect from your
client device.

#### 7.1) (Optional) Configure the hotspot to be created on boot

Open `/etc/NetworkManager/system-connections/Hotspot.nmconnection`:
```
[connection]
...
autoconnect=true # <-- Start on boot
```

## Verify everything is working

- After `docker compose up -d` and the sensor is running, check InfluxDB UI at
	`http://localhost:8086` (via SSH tunnel) and verify measurements appear.
- Check `docker compose ps` to confirm containers are healthy.
- Inspect logs for the `aqm` process or `main.py` if measurements are missing.


## Resources

- PMS5003 datasheet: https://www.aqmd.gov/docs/default-source/aq-spec/resources-page/plantower-pms5003-manual_v2-3.pdf
- PMS5003 pinout PDF: https://elty.pl/upload/download/PMS5003_LOGOELE.pdf
- Raspberry Pi GPIO docs: https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio-pads-control
- Raspberry Pi configuration docs: https://www.raspberrypi.com/documentation/computers/configuration.html

