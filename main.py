import os
import argparse

from serial import Serial
from loguru import logger
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from sensor import Sensor, SensorError, Measurement


def get_measurement(sensor: Sensor) -> Measurement:
    m = sensor.get_measurement()
    logger.info(
        f"PM1={m.pm_standard.v_1_0} PM2.5={m.pm_standard.v_2_5} PM10={m.pm_standard.v_10_0}"
    )
    return m


def communicate(sensor: Sensor):
    try:
        while True:
            try:
                get_measurement(sensor)
            except SensorError as sensor_error:
                logger.error(f"SensorError: {sensor_error}")
    except KeyboardInterrupt:
        logger.info("Program interrupted by user")
    finally:
        sensor.port.close()
        logger.info("Serial port closed")


def read_and_send_to_influxdb(sensor: Sensor):
    measurement = get_measurement(sensor)

    token = os.environ.get("INFLUXDB_TOKEN")
    org = "home-automation"
    url = "http://localhost:8086"
    bucket = "air-quality"
    client = InfluxDBClient(url=url, token=token, org=org)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    pm1 = Point("air-quality").field("PM1", measurement.pm_standard.v_1_0)
    write_api.write(bucket=bucket, org=org, record=pm1)
    pm2_5 = Point("air-quality").field("PM2.5", measurement.pm_standard.v_2_5)
    write_api.write(bucket=bucket, org=org, record=pm2_5)
    pm10 = Point("air-quality").field("PM10", measurement.pm_standard.v_10_0)
    write_api.write(bucket=bucket, org=org, record=pm10)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--loop", action=argparse.BooleanOptionalAction, help="Loop forever"
    )
    args = parser.parse_args()

    port = Serial(port="/dev/serial0", baudrate=9600, timeout=1)
    sensor = Sensor(port)

    if args.loop:
        communicate(sensor)
    else:
        read_and_send_to_influxdb(sensor)


if __name__ == "__main__":
    main()
