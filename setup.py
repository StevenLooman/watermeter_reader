import sys

import os.path

from setuptools import setup
from setuptools import find_packages
from setuptools.command.test import test as TestCommand


here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    LONG_DESCRIPTION = f.read()


INSTALL_REQUIRES=[
    'Adafruit-ADS1x15==1.0.2',
    'paho-mqtt==1.3.1',
]


setup(
    name='watermeter-reader',
    version='0.0.1-dev',
    description='Watermeter reader for RPi + ADS1015 sensor',
    long_description=LONG_DESCRIPTION,
    url='https://github.com/StevenLooman/watermeter_reader',
    author='Steven Looman',
    author_email='steven.looman@gmail.com',
    license='BSD',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
    ],
    packages=['watermeter_reader'],
    install_requires=INSTALL_REQUIRES,
)
