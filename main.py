import os
import re

from dotenv import load_dotenv
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import serial

KEYWORDS = {
    "A+": "1-0:1.8.0",  # Meter reading import
    "A-": "1-0:2.8.0",  # Meter reading export
    "L1": "1-0:21.7.255",  # Power L1
    "L2": "1-0:41.7.255",  # Power L2
    "L3": "1-0:61.7.255",  # Power L3
    "In": "1-0:1.7.255",  # Power total in
    "Out": "1-0:1.7.255",  # Power total out
}


def get_energy_usage() -> dict:
    with serial.Serial(
        port="/dev/ttyUSB0", baudrate=9600, bytesize=7, parity="E", timeout=1
    ) as ser:
        while True:
            reading = ser.read(300).decode("utf-8")
            ser.flushInput()
            if reading.startswith("/"):
                total = re.search(r"(\d*\.\d*)\*kWh", reading)
                total = total.groups()[0]
                current = re.search(r"1-0:1\.7\.0\*255\((\d*\.\d*)\*W", reading)
                current = current.groups()[0]
                return {"total": total, "current": current}


def write_energy_usage_to_influx(energy_usage: dict):
    load_dotenv()
    token = os.getenv("INFLUX_TOKEN")
    org = os.getenv("INFLUX_ORG")
    bucket = os.getenv("INFLUX_BUCKET")
    url = os.getenv("INFLUX_URL")
    client = InfluxDBClient(url=url, token=token)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    point = {
        "measurement": "electricity",
        "fields": {"kwh": energy_usage["total"], "current": energy_usage["current"]},
    }

    write_api.write(bucket, org, Point.from_dict(point))

    pass


def main():
    energy_usage = get_energy_usage()
    if energy_usage is not None:
        write_energy_usage_to_influx(energy_usage)


if __name__ == "__main__":
    main()
