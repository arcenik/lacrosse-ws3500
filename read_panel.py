#! /usr/bin/env python3
###############################################################################
import atexit
import logging

from optparse import OptionParser
import serial

from lacrosse import WS3500

###############################################################################
def dump_all(ws):
    """
    Dump All value to stdout

    Take a ws3500 instance as unique argument
    """

    print(f"Recording interval : {ws.recording_interval()} minute(s)")
    print(f"Forecast is {ws.forecast()} with {ws.tendency()} trends")
    print('')
    print('Value                | Current    | Minumum                        | Maximum')
    print('=====================X============X================================X===============================')
    print(f"Internal Temperature |  {ws.temp_int():+3.1f}     |  {ws.temp_int_min():+3.1f}     on {ws.temp_int_min_time()} |  {ws.temp_int_max():+3.1f}     on {ws.temp_int_max_time()}")
    print(f"Internal Humidity    |  {ws.humidity_int():3} %     |  {ws.humidity_int_min():3} %     on {ws.humidity_int_min_time()} |  {ws.humidity_int_max():3} %     on {ws.humidity_int_max_time()}")
    print(f"External Temperature |  {ws.temp_ext():+3.1f}     |  {ws.temp_ext_min():+3.1f}     on {ws.temp_ext_min_time()} |  {ws.temp_ext_max():+3.1f}     on {ws.temp_ext_max_time()}")
    print(f"External Humidity    |  {ws.humidity_ext():3} %     |  {ws.humidity_ext_min():3} %     on {ws.humidity_ext_min_time()} |  {ws.humidity_ext_max():3} %     on {ws.humidity_ext_max_time()}")
    print(f"Dewpoint             |  {ws.dewpoint():+3.1f}     |  {ws.dewpoint_min():+3.1f}     on {ws.dewpoint_min_time()} |  {ws.dewpoint_max():+3.1f}     on {ws.dewpoint_max_time()}")
    print(f"Relative Pressure    | {ws.rel_pressure():6} hPa | {ws.rel_pressure_min():6} hPa on {ws.rel_pressure_min_time()} | {ws.rel_pressure_max():6} hPa on {ws.rel_pressure_max_time()}")

###############################################################################
def close_serial(s):
    """
    AtExit function that closes serial port
    """
    s.close()

###############################################################################
###############################################################################
###############################################################################
if __name__ == '__main__':

    parser = OptionParser()

    parser.add_option('-d', '--device', dest='DEVICE',
                      help='Device to access serial port',
                      default='/dev/ttyUSB0')

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
    logger.info('serial port opened')
    atexit.register(close_serial, ser)

    ws = WS3500(ser, logger=logger)

    dump_all(ws)
