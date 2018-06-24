#!/usr/bin/python3

import time

import Adafruit_ADS1x15


GAIN = 1
DELAY = 0.1


def read_sensor(adc, ports):
    global GAIN
    values = {}
    for port in ports:
        values[port] = adc.read_adc(port, gain=GAIN)

    return values


def print_header_csv(ports):
    header_items = ['timestamp'] + ['Port {}'.format(port) for port in sorted(ports)]
    print(','.join(header_items))


def print_values_csv(timestamp, values):
    sorted_ports = sorted(values.keys())
    sorted_values = [timestamp] + [values[port] for port in sorted_ports]
    str_values = [str(value) for value in sorted_values]
    print(','.join(str_values))


def main():
    global DELAY
    adc = Adafruit_ADS1x15.ADS1115()

    ports = [0]
    print_header_csv(ports)

    while True:
        timestamp = int(round(time.time() * 1000))
        values = read_sensor(adc, ports)
        print_values_csv(timestamp, values)

        time.sleep(DELAY)


if __name__ == '__main__':
    main()
