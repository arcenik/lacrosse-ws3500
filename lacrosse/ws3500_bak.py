class WS3500():

    # def load_main_data(self):
    #     """
    #     Loads all the data from the device.
    #     """
    #     if not self._init:
    #         if not self._initialize():
    #             return ""
    #
    #     ADDR_BASE = 0x00
    #     TOTAL_DATA_LEN = 0x16F
    #     data_read = self._read_safe(ADDR_BASE, TOTAL_DATA_LEN)
    #
    #     return data_read

    # def read_history_info(self):
    #     if not self._init:
    #         if not self._initialize():
    #             return ""
    #     address = 0x6B2 - 2
    #     l = 12
    #     data_read = self._read_safe(address, l)
    #
    #     debug(string2hex(data_read), 1)
    #
    #     data = []
    #
    #     interval = (ord(data_read[1]) & 0xF) * 256 + ord(data_read[0]) + 1
    #     data.append(interval)
    #     countdown = ord(data_read[2])*16 + (ord(data_read[1]) >> 4) + 1
    #     data.append(countdown)
    #
    #     jour = (ord(data_read[0]) >> 4) * 10 + (ord(data_read[0]) & 0xF)
    #     mois = (ord(data_read[1]) >> 4) * 10 + (ord(data_read[1]) & 0xF)
    #     annee = 2000 + (ord(data_read[2]) >> 4) * 10 + (ord(data_read[2]) & 0xF)
    #     data.append((jour, mois, annee))
    #     no_records = ord(data_read[9])
    #     data.append(no_records)
    #
    #     return data

    # def read_history_record(self, data, record_no):
    #     record = data
    #
    #     minute = ((ord(record[0]) & 0xf0) >> 4)* 10 + (ord(record[0]) & 0xf)
    #     if minute >= 60:
    #         return None
    #     heure = ((ord(record[1]) & 0xf0) >> 4) * 10 + (ord(record[1]) & 0xf)
    #     jour = ((ord(record[2]) & 0xf0) >> 4) * 10 + (ord(record[2]) & 0xf)
    #     mois = ((ord(record[3]) & 0xf0) >> 4) * 10 + (ord(record[3]) & 0xf)
    #     annee = 2000 + ((ord(record[4]) & 0xf0) >> 4) * 10 + (ord(record[4]) & 0xf)
    #
    #     temperature_int = ((ord(record[5]) & 0xf0) >> 4) * 10 + (ord(record[5]) & 0xf)
    #     temperature_int += (ord(record[6]) & 0xf) * 100 - 400
    #     ##temperature_int /= 10.0
    #     temperature_ext = (ord(record[6]) & 0xf0) >> 4
    #     temperature_ext += ((ord(record[7]) & 0xf0) >> 4) * 100 + (ord(record[7]) & 0xf) * 10 - 400
    #     ##temperature_ext /= 10.0
    #     pressure = ((ord(record[8]) & 0xf0) >> 4) * 10 + (ord(record[8]) & 0xf)
    #     pressure += ((ord(record[9]) & 0xf0) >> 4) * 1000 + (ord(record[9]) & 0xf) * 100
    #     pressure += (ord(record[10]) & 0xf) * 10000
    #     ##pressure /= 10.0
    #     humidity_int = (ord(record[10]) & 0xf0) >> 4
    #     humidity_int += (ord(record[11]) & 0xf) * 10
    #     humidity_ext = (ord(record[11]) & 0xf0) >> 4
    #     humidity_ext += (ord(record[12]) & 0xf) * 10
    #     raincount = ord(record[12]) >> 4
    #     raincount += ord(record[13]) * 16
    #     windspeed = (ord(record[15]) & 0xf) * 256 + ord(record[14])
    #     ##windspeed /= 10.0
    #     if (ord(record[17]) & 0xf) != 1 or ord(record[16]) != 0xFE:
    #         windgust = (ord(record[17]) & 0xf) * 256 + ord(record[16])
    #         ##windgust /= 10.0
    #     else:
    #         windgust = -1
    #     winddir_degrees = ((ord(record[15]) & 0xF0)>> 4) * 22.5
    #
    #     return ["%04i-%02i-%02i %02i:%02i" % (annee, mois, jour, heure, minute), temperature_int, temperature_ext, pressure, humidity_int, humidity_ext, raincount, windspeed, winddir_degrees]

    # def read_history(self, delai_dernier_releve = 0):
    #     if not self._init:
    #         if not self._initialize():
    #             return ""
    #     l = 0x7fff - HISTORY_BUFFER_ADR + 1
    #     nb = 12 * 5 * 20
    #     l = 18 * nb
    #     nb_enreg_max = 1750
    #     address_max = HISTORY_BUFFER_ADR + nb_enreg_max * 18 - 1
    #     address = HISTORY_BUFFER_ADR
    #     end_of_data = False
    #     data = []
    #     j = 0
    #     last_record = None
    #     while not end_of_data and j < MAXRETRIES:
    #         nb_ok = 0
    #         j += 1
    #         debug("read history from address : %s" % hex(address), 1)
    #         if l + address > address_max:
    #             l = address_max - address + 1
    #         if l > 0:
    #             data_read = self._read_safe(address, l)
    #
    #         if data_read:
    #             for i in range(nb):##range(HISTORY_REC_NO):
    #                 try:
    #                     record = None
    #                     record = self.read_history_record(data_read[i*18:(i+1)*18], i)
    #                 except Exception as e:
    #                     print "exception :", e, i, string2hex(data_read[i*18:(i+1)*18])
    #                     record = None
    #                 if record is None:
    #                     end_of_data = False
    #                     break
    #                 else:
    #                     last_record = record
    #                     nb_ok += 1
    #                 data.append(record)
    #
    #             address += 18 * nb_ok
    #             if last_record and delai_dernier_releve > 0 :
    #                 try:
    #                     if DateTime.DateTimeFrom(last_record[0]) + DateTime.RelativeDateTime(minutes = delai_dernier_releve) > DateTime.now():
    #                         end_of_data = True
    #                 except:
    #                     pass
    #         else:
    #             debug("no data read", 1)
    #             end_of_data = False
    #
    #     return data
