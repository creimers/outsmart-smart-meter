import os
import re

from dotenv import load_dotenv
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import serial


###########
# REFERENCE
###########

# "1-0:1.8.0"       Meter reading import
# "1-0:2.8.0"       Meter reading export
# "1-0:21.7.255"    Power L1
# "1-0:41.7.255"    Power L2
# "1-0:61.7.255"    Power L3
# "1-0:1.7.255"     Power total in
# "1-0:1.7.255"     Power total out


def get_energy_usage() -> dict:
    with serial.Serial(
        port="/dev/ttyUSB0", baudrate=9600, bytesize=7, parity="E", timeout=1
    ) as ser:
        while True:
            reading = ser.read(300).decode("utf-8")
            ser.flushInput()
            if reading.startswith("/"):
                # accumulated
                acc = re.search(r"(\d*\.\d*)\*kWh", reading)
                acc = acc.groups()[0]

                # current
                curr = re.search(r"1-0:1\.7\.0\*255\((\d*\.\d*)\*W", reading)
                curr = curr.groups()[0]
                return {"acc": float(acc), "curr": float(curr)}


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
        "fields": {
            "acc": energy_usage["acc"],
            "curr": energy_usage["curr"],
        },
    }

    write_api.write(bucket, org, Point.from_dict(point))


def main():
    energy_usage = get_energy_usage()
    if energy_usage is not None:
        write_energy_usage_to_influx(energy_usage)


if __name__ == "__main__":
    main()
