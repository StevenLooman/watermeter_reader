#!/usr/bin/python3

import logging
import os.path
import time

import Adafruit_ADS1x15
import paho.mqtt.client as mqtt

# settings
GAIN = 1
DELAY = 0.1
PORT = 0
PERSISTENT_VALUE_FILE = '/home/pi/.watermeter_usage'
#MQTT_SERVER = 'localhost'
MQTT_SERVER = '192.168.178.73'
MQTT_TOPIC_USAGE = 'watermeter/usage'

THRESHOLD_STATE_HIGH = 1500
THRESHOLD_STATE_LOW = 1300

# constants
STATE_HIGH = 'high'
STATE_LOW = 'low'


logging.basicConfig(format='%(asctime)s:%(name)s:%(levelname)s:%(message)s',level=logging.DEBUG)
logging.getLogger('Adafruit_I2C').setLevel(logging.INFO)
_LOGGER = logging.getLogger(__name__)


def read_value(filename):
    if not os.path.exists(PERSISTENT_VALUE_FILE):
        _LOGGER.debug('Creating new persistence file')
        store_value(filename, 0)
        return 

    with open(filename, 'r') as fd:
        line = fd.readline()
        return int(line)


def store_value(filename, value):
    with open(filename, 'w') as fd:
        value_str = str(value)
        fd.write(value_str)


def main():
    # init ADC
    adc = Adafruit_ADS1x15.ADS1115()

    # init mqtt
    mqtt_client = mqtt.Client('watermeter_reader')
    mqtt_client.loop_start()
    mqtt_client.connect(MQTT_SERVER)
    _LOGGER.debug('Connected to mqtt')

    # init current value, and publish
    usage_value = read_value(PERSISTENT_VALUE_FILE)
    mqtt_client.publish(MQTT_TOPIC_USAGE, usage_value, retain=True)
    _LOGGER.debug('Published usage: %s %s', MQTT_TOPIC_USAGE, usage_value)

    # init current state
    value = adc.read_adc(PORT, gain=GAIN)
    current_state = STATE_HIGH if value > THRESHOLD_STATE_HIGH else STATE_LOW
    _LOGGER.debug('New state: %s, value: %s', current_state, value)

    while True:
        # main loop
        value = adc.read_adc(PORT, gain=GAIN)
        if current_state == STATE_HIGH and value < THRESHOLD_STATE_LOW:
            current_state = STATE_LOW
            _LOGGER.debug('New state: %s, value: %s', current_state, value)
        elif current_state == STATE_LOW and value > THRESHOLD_STATE_HIGH:
            current_state = STATE_HIGH
            _LOGGER.debug('New state: %s, value: %s', current_state, value)

            ## send pulse to MQTT
            #mqtt_client.publish('watermeter/pulse')
            #_LOGGER.debug('Published pulse')

            # store usage_value and publish
            usage_value += 1
            store_value(PERSISTENT_VALUE_FILE, usage_value)
            mqtt_client.publish(MQTT_TOPIC_USAGE, usage_value, retain=True)
            _LOGGER.debug('Published usage: %s %s', MQTT_TOPIC_USAGE, usage_value)

        time.sleep(DELAY)


if __name__ == '__main__':
    main()
