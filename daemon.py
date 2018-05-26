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

template = {
    "ws3500_external_temp":    {"help":"External Temperature", "type":"gauge", "value":""},
    "ws3500_external_humidity":{"help":"External Humidity",    "type":"gauge", "value":""},
    "ws3500_internal_temp":    {"help":"Internal Temperature", "type":"gauge", "value":""},
    "ws3500_internal_humidity":{"help":"Internal Humitidy",    "type":"gauge", "value":""},
    "ws3500_dewpoint":         {"help":"Dew Point",            "type":"gauge", "value":""},
    "ws3500_pressure":         {"help":"Pressure",             "type":"gauge", "value":""},
    "ws3500_fetch_duration":   {"help":"Time taken to fetch data", "type":"gauge", "value":""},
    "ws3500_fetch_time":       {"help":"Timestamp when data was fetched", "type":"gauge", "value":""}
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
    global lastdata

    res = ""
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
    global lastdata
    return render_template('status.html.j2', data=lastdata, error=lasterror)

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

                newdata = template
                t1 = time.time()

                newdata["ws3500_external_temp"]["value"] = self.ws.temp_ext()
                newdata["ws3500_external_humidity"]["value"] = self.ws.humidity_ext()
                newdata["ws3500_internal_temp"]["value"] = self.ws.temp_int()
                newdata["ws3500_internal_humidity"]["value"] = self.ws.humidity_int()
                newdata["ws3500_dewpoint"]["value"] = self.ws.dewpoint()
                newdata["ws3500_pressure"]["value"] = self.ws.rel_pressure()

                t2 = time.time()
                ellapsed = t2-t1
                newdata["ws3500_fetch_duration"]["value"] = ellapsed
                newdata["ws3500_fetch_time"]["value"] = time.time()
                lastdata = newdata
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

    parser = OptionParser()

    parser.add_option("-d", "--device", dest="DEVICE",
        default="/dev/ttyUSB0", help="Device to access serial port")

    parser.add_option("-P", "--port", dest="PORT",
        default="5000", help="Listen port (listen is 5000)")

    parser.add_option("-H", "--host", dest="HOST",
        default="127.0.0.1", help="Listen host (default is 127.0.0.1)")

    (options, args) = parser.parse_args()

    logger = logging.getLogger('WS3500')
    logger.setLevel(logging.INFO) # DEBUG, INFO, WARNING, ERROR, CRITICAL
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    f = ws3500_fetcher("ws3500-fetcher", device=options.DEVICE, logger=logger)
    f.start()

    app.run(host=options.HOST, port=options.PORT)
