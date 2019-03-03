# -*- coding: iso-8859-1 -*-

import time
import logging
# import serial

DELAY_CONST = 0.001
MAXRETRIES = 10
HISTORY_BUFFER_ADR = 0x1A0
HISTORY_REC_NO = 1796
SETBIT = 0x12
UNSETBIT = 0x32

DEBUG = 0


def string2hex(s):
    return " ".join(map(lambda x: hex(ord(x)), s))


class WS3500():

    def __init__(self, ser, logger=None):
        self.ser = ser
        self._init = False

        if logger is None:
            self.logger = logging.getLogger('WS3500')

            # DEBUG, INFO, WARNING, ERROR, CRITICAL
            self.logger.setLevel(logging.ERROR)

            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        else:
            self.logger = logger

    def _initialize(self):
        self.logger.info("initialize()")
        buff = "U"*85

        retries = 10
        success = False
        while retries > 0:

            self.ser.write(buff.encode())
            self.logger.info("initialize() first write(buf) completed")

            self.logger.debug("-DTR")
            self.ser.setDTR(0)
            self.logger.debug("-RTS")
            self.ser.setRTS(0)

            INIT_WAIT = 500
            i = 0
            while i < INIT_WAIT and not self.ser.getDSR():
                i += 1
                time.sleep(DELAY_CONST)
            if i == INIT_WAIT:
                self.logger.warning("initialize timeout 1")
                retries -= 1
            else:
                retries = 0
                success = True

        i = 0
        time.sleep(DELAY_CONST)
        while i < INIT_WAIT and self.ser.getDSR():
            i += 1
            time.sleep(DELAY_CONST)

        if i != INIT_WAIT:
            self.logger.debug("+RTS")
            self.ser.setRTS(1)
            self.logger.debug("+DTR")
            self.ser.setDTR(1)
        else:
            self.logger.warning("initialize timeout 2")
            return 0

        self.ser.write(buff.encode())
        self.logger.info("initialize() second write(buf) completed")

        self._init = True
        self.logger.info("initialize() succeeded")
        return 1

    def _read_safe(self, address, number):
        self.logger.info("_read_safe({a},{n})".format(a=address, n=number))
        readdata = ""
        readdata2 = ""
        self.count_failed_differs = 0
        self.count_failed_zeroes = 0
        self.count_failed_ones = 0
        for j in range(MAXRETRIES):
            self.count_retries = j
            # self._init = False
            # self._initialize()
            self._write_data(address, 0, None, tab=1)
            readdata = self._read_data(number, tab=1)

            self._write_data(address, 0, None, tab=1)
            readdata2 = self._read_data(number, tab=1)

            if readdata == readdata2:
                if readdata == chr(0) * number or readdata == "":
                    self.logger.warning(
                        "_read_safe : only 0x00, initialize() again")
                    self.count_failed_zeroes += 1
                    time.sleep(0.1)
                elif readdata == chr(255) * number:
                    self.logger.warning(
                        "_read_safe : only 0xFF, initialize() again")
                    self.count_failed_ones += 1
                    time.sleep(0.1)
                else:
                    break
            else:
                self.logger.warning("_read_safe : not identical, try again")
                self.count_failed_differs += 1

            self._init = False
            self._initialize()

        if j == MAXRETRIES:
            return None

        return readdata

    def _read_data(self, number, tab=0):
        self.logger.debug("_read_data({n})".format(n=number))
        command = 0xa1
        readdata = ""

        if self._write_byte(command, tab=tab+1):
            for i in range(number):
                b = self._read_byte(tab=tab+1)
                readdata = readdata + chr(b)
                if i + 1 < number:
                    self._read_next_byte_seq(tab=tab+1)

            self._read_last_byte_seq(tab=tab+1)

            self.logger.info("_read_data : {raw}".format(
                raw=string2hex(readdata)))

            return readdata
        else:
            self.logger.warning("_read_data : write error")
            return ""

    def _write_data(self, address, number, writedata, tab=0):
        self.logger.info("_write_data({a},{n})".format(a=address, n=number))
        command = 0xa0
        i = -1

        self._write_byte(command, tab=tab+1)
        self._write_byte(address/256, tab=tab+1)
        self._write_byte(address % 256, tab=tab+1)

        if writedata is not None:
            for i in range(number):
                self._write_byte(ord(writedata[i]), tab=tab+1)

        self.logger.debug("-DTR")
        self.ser.setDTR(0)
        self.logger.debug("-RTS")
        self.ser.setRTS(0)
        self.logger.debug("+RTS")
        self.ser.setRTS(1)
        self.logger.debug("+DTR")
        self.ser.setDTR(1)
        self.logger.debug("-RTS")
        self.ser.setRTS(0)

        return i

    def _read_next_byte_seq(self, tab=0):
        self.logger.debug("_read_next_byte_seq()")
        self._write_bit(0)
        self.logger.debug("-RTS")
        self.ser.setRTS(0)

    def _read_last_byte_seq(self, tab=0):
        self.logger.info("_read_last_byte_seq()")
        self.logger.debug("+RTS")
        self.ser.setRTS(1)
        self.logger.debug("-DTR")
        self.ser.setDTR(0)
        self.logger.debug("-RTS")
        self.ser.setRTS(0)
        self.logger.debug("+RTS")
        self.ser.setRTS(1)
        self.logger.debug("+DTR")
        self.ser.setDTR(1)
        self.logger.debug("-RTS")
        self.ser.setRTS(0)

    def _read_bit(self, tab=0):
        self.logger.debug("_read_bit()")
        self.logger.debug("-DTR")
        self.ser.setDTR(0)
        status = self.ser.getCTS()
        self.logger.debug("CTS -> {s}".format(s=str(status)))
        self.logger.debug("+DTR")
        self.ser.setDTR(1)

        self.logger.debug(
            "_read_bit result {res:d}".format(res=int(not status)))

        return int(not status)

    def _write_bit(self, bit, tab=0):
        self.logger.debug("_write_bit({b})".format(b=bit))
        if bit:
            self.logger.debug("-RTS")
            self.ser.setRTS(0)
        else:
            self.logger.debug("+RTS")
            self.ser.setRTS(1)
        self.logger.debug("-DTR")
        self.ser.setDTR(0)
        self.logger.debug("+DTR")
        self.ser.setDTR(1)

    def _read_byte(self, tab=0):
        self.logger.debug("_read_byte()")
        byte = 0

        for i in range(8):
            byte *= 2
            byte += self._read_bit(tab=tab+1)

        self.logger.debug(
            "_read_byte result {d} ({h})".format(d=byte, h=hex(byte)))

        return byte

    def _write_byte(self, byte, tab=0):
        self.logger.debug("_write_byte({b})".format(b=byte))
        byte = int(byte)
        for i in range(8):
            self._write_bit(byte & 0x80, tab=tab+1)
            byte <<= 1
            byte &= 0xff

        self.logger.debug("-RTS")
        self.ser.setRTS(0)
        status = self.ser.getCTS()
        self.logger.debug("CTS return {s}".format(s=str(status)))
        self.logger.debug("-DTR")
        self.ser.setDTR(0)
        self.logger.debug("+DTR")
        self.ser.setDTR(1)
        self.logger.debug("status {s}".format(s=int(status)))
        if status:
            return 1
        else:
            return 0

    def _getTemp(self, address):
        # 12.3 -> [1] 0x....1111 [0] 0x22223333
        data_read = self._read_safe(address, 2)
        return (
            ((ord(data_read[1]) & 0xF) * 10)
            + (ord(data_read[0]) >> 4)
            + ((ord(data_read[0]) & 0xF) / 10.0)
            - 40.0
        )

    def _getTemp2(self, address):
        # 12.3 -> [1] 0x11112222   [0] 0x3333....
        data_read = self._read_safe(address, 2)
        return (
            ((ord(data_read[1]) >> 4) * 10)
            + (ord(data_read[1]) & 0xF)
            + ((ord(data_read[0]) >> 4) / 10.0)
            - 40.0
        )

    def _getDateTime(self, address):
        ""
        data_read = self._read_safe(address, 6)
        return "{a:04d}-{m:02d}-{j:02d} {h:02d}:{mi:02d}".format(
            a=2000 + (ord(data_read[4]) >> 4) + (ord(data_read[5]) & 0xF) * 10,
            m=(ord(data_read[3]) >> 4) + (ord(data_read[4]) & 0xF) * 10,
            j=(ord(data_read[2]) >> 4) + (ord(data_read[3]) & 0xF) * 10,
            h=(ord(data_read[1]) >> 4) + (ord(data_read[2]) & 0xF) * 10,
            mi=(ord(data_read[0]) >> 4) + (ord(data_read[1]) & 0xF) * 10
        )

    def _getDateTime2(self, address):
        ""
        data_read = self._read_safe(address, 5)
        return "{a:04d}-{m:02d}-{j:02d} {h:02d}:{mi:02d}".format(
            a=2000 + (ord(data_read[4]) >> 4) * 10 + (ord(data_read[4]) & 0xF),
            m=(ord(data_read[3]) >> 4) * 10 + (ord(data_read[3]) & 0xF),
            j=(ord(data_read[2]) >> 4) * 10 + (ord(data_read[2]) & 0xF),
            h=(ord(data_read[1]) >> 4) * 10 + (ord(data_read[1]) & 0xF),
            mi=(ord(data_read[0]) >> 4) * 10 + (ord(data_read[0]) & 0xF)
        )

    def _getHumidity(self, address):
        "Returns the humitidy at the given address`"
        data_read = self._read_safe(address, 1)
        return (ord(data_read[0]) >> 4) * 10 + (ord(data_read[0]) & 0xf)

    def _getPressure(self, address):
        "Returns the pressure for the given address"
        data_read = self._read_safe(address, 3)
        return (
            ((ord(data_read[2]) & 0xF) * 1000)
            + ((ord(data_read[1]) >> 4) * 100)
            + ((ord(data_read[1]) & 0xF) * 10)
            + (ord(data_read[0]) >> 4)
            + ((ord(data_read[0]) & 0xF) / 10.0)
        )

    def tendency(self):
        "Returns tendency"
        ADDR_TENDENCY = 0x24
        tendency_values = ["Constant", "Increasing", "Decreasing"]
        data_read = self._read_safe(ADDR_TENDENCY, 1)

        return tendency_values[ord(data_read[0]) >> 4]

    def forecast(self):
        "Returns tendency and forecast"
        ADDR_TENDENCY = 0x24
        forecast_values = ["Rainy", "Cloudy", "Sunny"]
        data_read = self._read_safe(ADDR_TENDENCY, 1)
        return forecast_values[ord(data_read[0]) & 0xF]

    def recording_interval(self):
        "Returns recording interval, in minutes"
        ADDR_RECORD_INT = 0xE3
        duree = {0: 1,  # 1 min
                 1: 5,  # 5 min
                 2: 10,  # 10 min
                 3: 15,  # 15 min
                 4: 20,  # 20 min
                 5: 30,  # 30 min
                 6: 60,  # 1 hour
                 7: 120,  # 2 hours
                 8: 180,  # 3 hours
                 9: 240,  # 4 hours
                 0xa: 360,  # 6 hours
                 0xb: 480,  # 8 hours
                 0xc: 720,  # 12 hours
                 0xd: 1440}  # 24 hours
        data_read = self._read_safe(ADDR_RECORD_INT, 1)
        return duree[ord(data_read[0]) >> 4]

    def temp_int(self):
        "Returns the current internal temperature"
        ADDR_TEMP_INT = 0x26
        return self._getTemp(ADDR_TEMP_INT)

    def temp_int_min(self):
        "Returns the minimum internal temperature"
        ADDR_TEMP_INT_MIN = 0x28
        return self._getTemp2(ADDR_TEMP_INT_MIN)

    def temp_int_min_time(self):
        "Returns the date/time of the mininal internal temperature"
        ADDR_TEMP_INT_MIN_TIME = 0x2C
        return self._getDateTime(ADDR_TEMP_INT_MIN_TIME)

    def temp_int_max(self):
        "Returns the maximum internal temperature"
        ADDR_TEMP_INT_MAX = 0x2B
        return self._getTemp(ADDR_TEMP_INT_MAX)

    def temp_int_max_time(self):
        "Returns the date/time of the maximum internal temperature"
        ADDR_TEMP_INT_MAX_TIME = 0x31
        return self._getDateTime(ADDR_TEMP_INT_MAX_TIME)

    def temp_ext(self):
        "Returns the current external temperature"
        ADDR_TEMP_EXT = 0x3D
        return self._getTemp(ADDR_TEMP_EXT)

    def temp_ext_min(self):
        "Returns the minimum external temperature"
        ADDR_TEMP_EXT_MIN = 0x3F
        return self._getTemp(ADDR_TEMP_EXT_MIN)

    def temp_ext_min_time(self):
        "Returns the date/time of the minimum external temperature"
        ADDR_TEMP_EXT_MIN_TIME = 0x43
        return self._getDateTime(ADDR_TEMP_EXT_MIN_TIME)

    def temp_ext_max(self):
        "Returns the maximum external temperature"
        ADDR_TEMP_EXT_MAX = 0x42
        return self._getTemp(ADDR_TEMP_EXT_MAX)

    def temp_ext_max_time(self):
        "Returns the date/time of the maximum external temperature"
        ADDR_TEMP_EXT_MAX_TIME = 0x48
        return self._getDateTime(ADDR_TEMP_EXT_MAX_TIME)

    def dewpoint(self):
        "Returns the current dewpoint"
        ADDR_DEWPOINT = 0x6B
        return self._getTemp(ADDR_DEWPOINT)

    def dewpoint_min(self):
        "Returns the minimum dewpoint"
        ADDR_DEWPOINT_MIN = 0x6D
        return self._getTemp2(ADDR_DEWPOINT_MIN)

    def dewpoint_min_time(self):
        "Returns the date/time of the minimum dewpoint"
        ADDR_DEWPOINT_MIN_TIME = 0x71
        return self._getDateTime(ADDR_DEWPOINT_MIN_TIME)

    def dewpoint_max(self):
        "Returns the maximum dewpoint"
        ADDR_DEWPOINT_MAX = 0x70
        return self._getTemp(ADDR_DEWPOINT_MAX)

    def dewpoint_max_time(self):
        "Returns the date/time of the maximum dewpoint"
        ADDR_DEWPOINT_MAX_TIME = 0x76
        return self._getDateTime(ADDR_DEWPOINT_MAX_TIME)

    def humidity_int(self):
        "Returns the current internal humidity"
        ADDR_HUMIDITY_INT = 0x81
        return self._getHumidity(ADDR_HUMIDITY_INT)

    def humidity_int_min(self):
        "Returns the minimum internal humidity"
        ADDR_HUMIDITY_INT_MIN = 0x82
        return self._getHumidity(ADDR_HUMIDITY_INT_MIN)

    def humidity_int_min_time(self):
        "Returns the date/time of the internal humidity"
        ADDR_HUMIDITY_INT_MIN_TIME = 0x84
        return self._getDateTime2(ADDR_HUMIDITY_INT_MIN_TIME)

    def humidity_int_max(self):
        "Returns the maximum of the internal humidity"
        ADDR_HUMIDITY_INT_MAX = 0x83
        return self._getHumidity(ADDR_HUMIDITY_INT_MAX)

    def humidity_int_max_time(self):
        "Returns the date/time of the maximum internal humidity"
        ADDR_HUMIDITY_INT_MAX_TIME = 0x89
        return self._getDateTime2(ADDR_HUMIDITY_INT_MAX_TIME)

    def humidity_ext(self):
        "Returns the current external humidity"
        ADDR_HUMIDITY_EXT = 0x90
        return self._getHumidity(ADDR_HUMIDITY_EXT)

    def humidity_ext_min(self):
        "Returns the minimum external humidity"
        ADDR_HUMIDITY_EXT_MIN = 0x91
        return self._getHumidity(ADDR_HUMIDITY_EXT_MIN)

    def humidity_ext_min_time(self):
        "Returns the date/time of the minimum external humidity"
        ADDR_HUMIDITY_EXT_MIN_TIME = 0x93
        return self._getDateTime2(ADDR_HUMIDITY_EXT_MIN_TIME)

    def humidity_ext_max(self):
        "Returns the maximum external humidity"
        ADDR_HUMIDITY_EXT_MAX = 0x92
        return self._getHumidity(ADDR_HUMIDITY_EXT_MAX)

    def humidity_ext_max_time(self):
        "Returns the date/time of the maximum external humitidy"
        ADDR_HUMIDITY_EXT_MAX_TIME = 0x98
        return self._getDateTime2(ADDR_HUMIDITY_EXT_MAX_TIME)

    def rel_pressure(self):
        "Returns the current pression"
        ADDR_PRESSURE_REL = 0x13D
        return self._getPressure(ADDR_PRESSURE_REL)

    def rel_pressure_min(self):
        "Returns the minimum pression"
        ADDR_PRESSURE_REL_MIN = 0x156
        return self._getPressure(ADDR_PRESSURE_REL_MIN)

    def rel_pressure_min_time(self):
        "Returns the date/time of the minimum pression"
        ADDR_PRESSURE_REL_MIN_TIME = 0x160
        return self._getDateTime2(ADDR_PRESSURE_REL_MIN_TIME)

    def rel_pressure_max(self):
        "Returns the maximum pression"
        ADDR_PRESSURE_REL_MAX = 0x14C
        return self._getPressure(ADDR_PRESSURE_REL_MAX)

    def rel_pressure_max_time(self):
        "Returns the date/time of the maximum pression"
        ADDR_PRESSURE_REL_MAX_TIME = 0x15B
        return self._getDateTime2(ADDR_PRESSURE_REL_MAX_TIME)

    # def abs_pressure(self):
    #     ADDR_PRESSURE_ABS = 0x138
    #     return self._getPressure(ADDR_PRESSURE_ABS)
    #
    # def abs_pressure_min(self):
    #     ADDR_PRESSURE_ABS_MIN = 0x5F6
    #     return self._getPressure(ADDR_PRESSURE_ABS_MIN)
    #
    # def abs_pressure_min_time(self):
    #     ADDR_PRESSURE_ABS_MIN_TIME = 0x61E
    #     return self._getDateTime2(ADDR_PRESSURE_ABS_MIN_TIME)
    #
    # def abs_pressure_max(self):
    #     ADDR_PRESSURE_ABS_MAX = 0x5F6 + 12
    #     return self._getPressure(ADDR_PRESSURE_ABS_MAX)
    #
    # def abs_pressure_max_time(self):
    #     ADDR_PRESSURE_ABS_MAX_TIME = 0x61E + 5
    #     return self._getDateTime2(ADDR_PRESSURE_ABS_MAX_TIME)
