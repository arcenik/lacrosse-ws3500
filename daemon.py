#! /usr/bin/env python2
################################################################################
from flask import Flask, Response, redirect, render_template
from optparse import OptionParser
import serial
import atexit
import logging
import threading
import time
import sys

from lacrosse import WS3500

from pprint import pprint as pp
from pprint import pformat as pf

################################################################################
# globals

app = Flask("WS3500")
ser = None
run = True
lastdata = None
lasterror = None
async = True
logger = None
device = None

template = {
    "ws3500_external_temp":    {"help":"External Temperature", "type":"gauge", "value":""},
    "ws3500_external_humidity":{"help":"External Humidity",    "type":"gauge", "value":""},
    "ws3500_internal_temp":    {"help":"Internal Temperature", "type":"gauge", "value":""},
    "ws3500_internal_humidity":{"help":"Internal Humitidy",    "type":"gauge", "value":""},
    "ws3500_dewpoint":         {"help":"Dew Point",            "type":"gauge", "value":""},
    "ws3500_pressure":         {"help":"Pressure",             "type":"gauge", "value":""},
    "ws3500_fetch_duration":   {"help":"Time taken to fetch data",                            "type":"gauge", "value":""},
    "ws3500_fetch_time":       {"help":"Timestamp when data was fetched",                     "type":"gauge", "value":""},
    "ws3500_retries_count":    {"help":"Number of retries",                                   "type":"gauge", "value":""},
    "ws3500_fails_differ_count": {"help":"Number of read failed due to differents values",    "type":"gauge", "value":""},
    "ws3500_fails_zeroes_count": {"help":"Number of read failed due to only zeroes returned", "type":"gauge", "value":""},
    "ws3500_fails_ones_count": {"help":"Number of read failed due to only ones returned",     "type":"gauge", "value":""}
}

################################################################################
@app.template_filter('datetime')
def _jinja2_filter_datetime(date):
    return time.ctime(date)

################################################################################
@app.route("/")
def root():
    "Returns a 302 redirect to /metrics"
    return redirect("/metrics", code=302)

################################################################################
@app.route("/metrics")
def metrics():
    "Returns prometheus data (as text/plain)"
    global lastdata, lasterror, async, logger, device

    res = ""
    if not async:
        try:
            lasterror = None
            ser = serial.Serial(baudrate=300, port=device, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=None, writeTimeout=None, interCharTimeout=None, rtscts=0, dsrdtr=None, xonxoff=0)
            # ser.open()
            ws = WS3500(ser)
            lastdata = single_fetch(ws)

        except Exception, e:
            logger.warning("[fetcher] exception catched, cleaning data")
            logger.warning(pf(e))
            lasterror = pf(e)
            lastdata = None

        # try:
        #     ser.close()

    if lastdata is not None:
        for k in lastdata:
            res += "# HELP {k} {v}\n".format(k=k, v=lastdata[k]["help"])
            res += "# TYPE {k} {v}\n".format(k=k, v=lastdata[k]["type"])
            res += "{k} {v}\n".format(k=k, v=lastdata[k]["value"])
    return Response(res, mimetype="text/plain")

################################################################################
@app.route("/status")
def status():
    "Returns status.html rendered template"
    global lastdata, lasterror

    if async:
        data = lastdata
        # error = lasterror
    else:
        data = XXXX

    return render_template('status.html.j2', data=data, error=lasterror)

################################################################################
def single_fetch(ws):
    """
    Make a single synchronous read

    single_fetch(ws)
        ws : Weather Station object

    """
    global template

    ws._init = False
    ws._initialize()

    newdata = template
    t1 = time.time()

    newdata["ws3500_external_temp"]["value"] = ws.temp_ext()
    newdata["ws3500_external_humidity"]["value"] = ws.humidity_ext()
    newdata["ws3500_internal_temp"]["value"] = ws.temp_int()
    newdata["ws3500_internal_humidity"]["value"] = ws.humidity_int()
    newdata["ws3500_dewpoint"]["value"] = ws.dewpoint()
    newdata["ws3500_pressure"]["value"] = ws.rel_pressure()

    newdata["ws3500_retries_count"]["value"] = ws.count_retries
    newdata["ws3500_fails_differ_count"]["value"] = ws.count_failed_differs
    newdata["ws3500_fails_zeroes_count"]["value"] = ws.count_failed_zeroes
    newdata["ws3500_fails_ones_count"]["value"] = ws.count_failed_ones

    t2 = time.time()
    ellapsed = t2-t1
    newdata["ws3500_fetch_duration"]["value"] = ellapsed
    newdata["ws3500_fetch_time"]["value"] = time.time()

    return newdata

################################################################################
class ws3500_fetcher(threading.Thread):
    def __init__(self, name, device, logger):
        threading.Thread.__init__(self)
        self.name = name
        self.device = device
        self.logger = logger
        self.ser = None
        self.ws = None

    def run(self):
        global lastdata, lasterror

        self.logger.info("[fetcher] starting thread")
        while run:
            try:

                lasterror = None

                if not self.ws:
                    self.logger.info("[fetcher] opening device")
                    self.ser = serial.Serial(baudrate=300, port=self.device, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=None, writeTimeout=None, interCharTimeout=None, rtscts=0, dsrdtr=None, xonxoff=0)

                    # self.ws = WS3500(self.ser, logger=self.logger)
                    self.ws = WS3500(self.ser)

                lastdata = single_fetch(self.ws)
                time.sleep(5)

            except Exception, e:
                self.logger.warning("[fetcher] exception catched, cleaning data")
                self.logger.warning(pf(e))
                self.ser = None
                self.ws = None
                lasterror = pf(e)
                lastdata = None
                time.sleep(5)

        self.logger.info("[fetcher] exiting thread")

################################################################################
################################################################################
################################################################################
if __name__ == "__main__":

    global async, logger, device

    parser = OptionParser()

    parser.add_option("-d", "--device", dest="DEVICE",
        default="/dev/ttyUSB0", help="Device to access serial port")

    parser.add_option("-P", "--port", dest="PORT",
        default="5000", help="Listen port (listen is 5000)")

    parser.add_option("-H", "--host", dest="HOST",
        default="127.0.0.1", help="Listen host (default is 127.0.0.1)")

    parser.add_option("--async", action="store_true", dest="ASYNC",
        help="Operate in asynchronous mode (data fetch in background)")
    parser.add_option("--sync", action="store_false", dest="ASYNC",
        help="Operate in synchronous mode (data fetch in foreground)")

    (options, args) = parser.parse_args()

    logger = logging.getLogger('WS3500')
    logger.setLevel(logging.INFO) # DEBUG, INFO, WARNING, ERROR, CRITICAL
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    async = options.ASYNC

    if async:
        f = ws3500_fetcher("ws3500-fetcher", device=options.DEVICE, logger=logger)
        f.start()
    else:
        device = options.DEVICE

    app.run(host=options.HOST, port=options.PORT)
