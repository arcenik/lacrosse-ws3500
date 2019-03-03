#! /usr/bin/env python2
###############################################################################
from optparse import OptionParser
import serial
import atexit
import logging

from lacrosse import WS3500


###############################################################################
def dump_all(ws):
    """
    Dump All value to stdout

    Take a ws3500 instance as unique argument
    """

    print("Recording interval : {i} minute(s)".format(
        i=ws.recording_interval()))
    print("Forecast is {f} with {t} trends".format(
        f=ws.forecast(), t=ws.tendency()))
    print("")

    print("Value                | Current    | Minumum                        | Maximum")
    print("=====================X============X================================X===============================")

    print("Internal Temperature |  {t:+3.1f}     |  {min:+3.1f}     on {mint} |  {max:+3.1f}     on {maxt}"
          .format(
            t=ws.temp_int(),
            min=ws.temp_int_min(), mint=ws.temp_int_min_time(),
            max=ws.temp_int_max(), maxt=ws.temp_int_max_time()
            )
          )

    print("Internal Humidity    |  {t:3} %     |  {min:3} %     on {mint} |  {max:3} %     on {maxt}"
          .format(
            t=ws.humidity_int(),
            min=ws.humidity_int_min(), mint=ws.humidity_int_min_time(),
            max=ws.humidity_int_max(), maxt=ws.humidity_int_max_time()
            )
          )

    print("External Temperature |  {t:+3.1f}     |  {min:+3.1f}     on {mint} |  {max:+3.1f}     on {maxt}"
          .format(
            t=ws.temp_ext(),
            min=ws.temp_ext_min(), mint=ws.temp_ext_min_time(),
            max=ws.temp_ext_max(), maxt=ws.temp_ext_max_time()
            )
          )

    print("External Humidity    |  {t:3} %     |  {min:3} %     on {mint} |  {max:3} %     on {maxt}"
          .format(
            t=ws.humidity_ext(),
            min=ws.humidity_ext_min(), mint=ws.humidity_ext_min_time(),
            max=ws.humidity_ext_max(), maxt=ws.humidity_ext_max_time()
            )
          )

    print("Dewpoint             |  {t:+3.1f}     |  {min:+3.1f}     on {mint} |  {max:+3.1f}     on {maxt}"
          .format(
            t=ws.dewpoint(),
            min=ws.dewpoint_min(), mint=ws.dewpoint_min_time(),
            max=ws.dewpoint_max(), maxt=ws.dewpoint_max_time()
            )
          )

    print("Relative Pressure    | {p:6} hPa | {min:6} hPa on {mint} | {max:6} hPa on {maxt}"
          .format(
            p=ws.rel_pressure(),
            min=ws.rel_pressure_min(), mint=ws.rel_pressure_min_time(),
            max=ws.rel_pressure_max(), maxt=ws.rel_pressure_max_time()
            )
          )


###############################################################################
def close_serial(s):
    """
    AtExit function that closes serial port
    """
    s.close()


###############################################################################
###############################################################################
###############################################################################
if __name__ == "__main__":

    parser = OptionParser()

    parser.add_option("-d", "--device", dest="DEVICE",
                      help="Device to access serial port",
                      default="/dev/ttyUSB0")

    (options, args) = parser.parse_args()

    logger = logging.getLogger('WS3500')
    logger.setLevel(logging.ERROR)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    ser = serial.Serial(
        baudrate=300,
        port=options.DEVICE,
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
    logger.info("serial port opened")
    atexit.register(close_serial, ser)

    ws = WS3500(ser, logger=logger)

    dump_all(ws)
