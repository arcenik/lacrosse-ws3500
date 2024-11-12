#! /usr/bin/env python3
###############################################################################
import logging
import threading
import time
import traceback
import sys
from pprint import pformat as pf

import argparse
from flask import Flask, Response, redirect, render_template
import serial

from lacrosse import WS3500

###############################################################################
# globals
APP = Flask('WS3500')
SER = None
RUN = True
LASTDATA = None
LASTERROR = None
LOGGER = None
DEVICE = None

TEMPLATE = {
    'ws3500_external_temp': {
        'help': 'External Temperature', 'type': 'gauge', 'value': ''},
    'ws3500_external_humidity': {
        'help': 'External Humidity', 'type': 'gauge', 'value': ''},
    'ws3500_internal_temp': {
        'help': 'Internal Temperature', 'type': 'gauge', 'value': ''},
    'ws3500_internal_humidity': {
        'help': 'Internal Humitidy', 'type': 'gauge', 'value': ''},
    'ws3500_dewpoint': {
        'help': 'Dew Point', 'type': 'gauge', 'value': ''},
    'ws3500_pressure': {
        'help': 'Pressure', 'type': 'gauge', 'value': ''},
    'ws3500_fetch_duration': {
        'help': 'Time taken to fetch data', 'type': 'gauge', 'value': ''},
    'ws3500_fetch_time': {
        'help': 'Timestamp when data was fetched',
        'type': 'gauge', 'value': ''},
    'ws3500_retries_count': {
        'help': 'Number of retries', 'type': 'gauge', 'value': ''},
    'ws3500_fails_differ_count': {
        'help': 'Number of read failed due to differents values',
        'type': 'gauge', 'value': ''},
    'ws3500_fails_zeroes_count': {
        'help': 'Number of read failed due to only zeroes returned',
        'type': 'gauge', 'value': ''},
    'ws3500_fails_ones_count': {
        'help': 'Number of read failed due to only ones returned',
        'type': 'gauge', 'value': ''}
}

###############################################################################
@APP.template_filter('datetime')
def _jinja2_filter_datetime(date):
    return time.ctime(date)

###############################################################################
@APP.route('/')
def root():
    "Returns a 302 redirect to /metrics"
    return redirect('/metrics', code=302)

###############################################################################
@APP.route('/metrics')
def metrics():
    "Returns prometheus data (as text/plain)"

    res = ''

    if LASTDATA is not None:
        for k in LASTDATA:
            res += f"# HELP {k} {LASTDATA[k]['help']}\n"
            res += f"# TYPE {k} {LASTDATA[k]['type']}\n"
            res += f"{k} {LASTDATA[k]['value']}\n"
    return Response(res, mimetype='text/plain')

###############################################################################
@APP.route('/status')
def status():
    "Returns status.html rendered template"

    return render_template('status.html.j2', data=LASTDATA, error=LASTERROR)


###############################################################################
def single_fetch(ws):
    """
    Make a single synchronous read

    single_fetch(ws)
        ws : Weather Station object

    """

    ws.initialize()

    newdata = TEMPLATE
    t1 = time.time()

    newdata['ws3500_external_temp']['value'] = ws.temp_ext()
    newdata['ws3500_external_humidity']['value'] = ws.humidity_ext()
    newdata['ws3500_internal_temp']['value'] = ws.temp_int()
    newdata['ws3500_internal_humidity']['value'] = ws.humidity_int()
    newdata['ws3500_dewpoint']['value'] = ws.dewpoint()
    newdata['ws3500_pressure']['value'] = ws.rel_pressure()

    newdata['ws3500_retries_count']['value'] = ws.count_retries
    newdata['ws3500_fails_differ_count']['value'] = ws.count_failed_differs
    newdata['ws3500_fails_zeroes_count']['value'] = ws.count_failed_zeroes
    newdata['ws3500_fails_ones_count']['value'] = ws.count_failed_ones

    t2 = time.time()
    ellapsed = t2-t1
    newdata['ws3500_fetch_duration']['value'] = ellapsed
    newdata['ws3500_fetch_time']['value'] = time.time()

    return newdata


###############################################################################
###############################################################################
###############################################################################
class Ws3500Fetcher(threading.Thread):
    def __init__(self, name, device, logger):
        threading.Thread.__init__(self)
        self.name = name
        self.device = device
        self.logger = logger
        self.ser = None
        self.ws = None

    def run(self):

        global LASTDATA, LASTERROR

        self.logger.info('[fetcher] starting thread')
        while RUN:
            try:

                LASTERROR = None

                if not self.ws:
                    self.logger.info('[fetcher] opening device')
                    self.ser = serial.Serial(
                        baudrate=300, port=self.device,
                        bytesize=serial.EIGHTBITS,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE,
                        timeout=None,
                        writeTimeout=None,
                        interCharTimeout=None,
                        rtscts=0,
                        dsrdtr=None,
                        xonxoff=0
                    )

                    # self.ws = WS3500(self.ser, logger=self.logger)
                    self.ws = WS3500(self.ser)

                LASTDATA = single_fetch(self.ws)
                time.sleep(5)

            except Exception as e:
                self.logger.warning(
                    '[fetcher] exception catched, cleaning data')
                self.logger.warning(pf(e))
                self.ser = None
                self.ws = None
                LASTERROR = pf(e)
                LASTDATA = None

                print("-"*60)
                traceback.print_exc(file=sys.stdout)
                print("-"*60)

                time.sleep(5)

        self.logger.info('[fetcher] exiting thread')


###############################################################################
###############################################################################
###############################################################################
if __name__ == '__main__':

    parser = argparse.ArgumentParser(prog='daemon.py', description='WS3500 deamon')

    parser.add_argument(
        '-d', '--device', dest='DEVICE', default='/dev/ttyUSB0',
        help='Device to access serial port')

    parser.add_argument(
        '-P', '--port', dest='PORT', default='5000',
        help='Listen port (listen is 5000)')

    parser.add_argument(
        '-H', '--host', dest='HOST', default='127.0.0.1',
        help='Listen host (default is 127.0.0.1)')

    # parser.add_argument(
    #     '--async', action='store_true', dest='ASYNC',
    #     help='Operate in asynchronous mode (data fetch in background)')
    # parser.add_argument(
    #     '--sync', action='store_false', dest='ASYNC',
    #     help='Operate in synchronous mode (data fetch in foreground)')

    (options, args) = parser.parse_args()

    LOGGER = logging.getLogger('WS3500')
    LOGGER.setLevel(logging.INFO)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    LOGGER.addHandler(handler)

    f = Ws3500Fetcher(
        'ws3500-fetcher', device=options.DEVICE, logger=LOGGER)
    f.start()

    APP.run(host=options.HOST, port=options.PORT)
