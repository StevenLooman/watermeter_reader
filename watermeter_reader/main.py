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
PERSISTENT_USAGE_FILE = '/home/pi/.watermeter_usage'
PERSISTENT_REF_VALUE_FILE = '/home/pi/watermeter_values'
#MQTT_SERVER = 'localhost'
MQTT_SERVER = '192.168.178.73'
MQTT_TOPIC_USAGE = 'watermeter/usage'

MIN_VALUE_CHANGE = 20
LASTS_SIZE = 5

# constants
STATE_HIGH = 'high'
STATE_LOW = 'low'


logging.basicConfig(format='%(asctime)s:%(name)s:%(levelname)s:%(message)s',level=logging.DEBUG)
logging.getLogger('Adafruit_I2C').setLevel(logging.INFO)
_LOGGER = logging.getLogger(__name__)


def read_usage_value(filename):
    if not os.path.exists(PERSISTENT_USAGE_FILE):
        _LOGGER.debug('Creating new persistence file')
        store_usage_value(filename, 0)
        return 

    with open(filename, 'r') as fd:
        line = fd.readline()
        return int(line)


def store_usage_value(filename, value):
    with open(filename, 'w') as fd:
        value_str = str(value)
        fd.write(value_str)


def rising(values):
    return sorted(values) == values


def falling(values):
    return reversed(sorted(values)) == values


class Machine:

    STATE_HIGH = 'high'
    STATE_LOW = 'low'

    def __init__(self, min_size, callback):
        """Initializer."""
        self._min_size = min_size
        self._last_values = []
        self._state = STATE_HIGH  # arbitrary
        self._callback = callback

    def _values_falling(self):
        """Check if values are falling."""
        return list(reversed(sorted(self._last_values))) == self._last_values

    def _values_rising(self):
        """Check if values are rising."""
        return sorted(self._last_values) == self._last_values

    def _set_state(self, new_state):
        """Set a new state."""
        self._state = new_state
        self._callback(self)

    @property
    def last_value(self):
        """Get last value."""
        return self._last_values[0] if self._last_values else None

    @property
    def last_values(self):
        """Get last values."""
        return self._last_values

    @property
    def state(self):
        """Get current state."""
        return self._state

    def add_value(self, value):
        """Add a new value."""
        self._last_values = [value] + self._last_values[0:self._min_size - 1]
        if len(self._last_values) < self._min_size:
            return

        # debugging
        last_values_report = self._last_values_report()
        pattern = 'rising' if self._values_rising() else 'falling' if self._values_falling() else None
        _LOGGER.debug('Last values: %s, pattern: %s', last_values_report, pattern)

        if self._state == STATE_HIGH and \
           self._values_falling():
            self._set_state(STATE_LOW)
        elif self._state == STATE_LOW and \
             self._values_rising():
            self._set_state(STATE_HIGH)

    def _last_values_report(self):
        """Add rising/falling between last values."""
        last = self._last_values[0]
        result = [last]
        for value in self._last_values[1:]:
            change = '↑' if value > last else '↓' if value < last else '→'
            result.append(change)
            result.append(last)
            last = value
        return result


def main():
    # init ADC
    adc = Adafruit_ADS1x15.ADS1115()

    # init mqtt
    mqtt_client = mqtt.Client('watermeter_reader')
    mqtt_client.loop_start()
    mqtt_client.connect(MQTT_SERVER)
    _LOGGER.debug('Connected to mqtt')

    # init current value, and publish
    usage_value = read_usage_value(PERSISTENT_USAGE_FILE)
    mqtt_client.publish(MQTT_TOPIC_USAGE, usage_value, retain=True)
    _LOGGER.debug('Published usage: %s %s', MQTT_TOPIC_USAGE, usage_value)

    # state change reaction
    def state_changed(machine):
        """Handle changed state."""
        nonlocal usage_value
        _LOGGER.debug('Machine state: %s, last_values: %s', machine.state, machine.last_values)

        if machine.state == Machine.STATE_HIGH:
            ## send pulse to MQTT
            #mqtt_client.publish('watermeter/pulse')
            #_LOGGER.debug('Published pulse')

            # store usage_value and publish
            usage_value += 1
            store_usage_value(PERSISTENT_USAGE_FILE, usage_value)
            mqtt_client.publish(MQTT_TOPIC_USAGE, usage_value, retain=True)
            _LOGGER.debug('Published usage: %s %s', MQTT_TOPIC_USAGE, usage_value)

    value = adc.read_adc(PORT, gain=GAIN)
    machine = Machine(LASTS_SIZE, state_changed)
    machine.add_value(value)

    # main loop
    last_value = value
    while True:
        value = adc.read_adc(PORT, gain=GAIN)

        # ensure new value is interesting
        if abs(last_value - value) >= MIN_VALUE_CHANGE:
            machine.add_value(value)
            last_value = value

        time.sleep(DELAY)


if __name__ == '__main__':
    main()
