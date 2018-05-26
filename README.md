
This is a Python module that allow accessing LaCrosse WS3500 weather station.

It is provided with an exporter for Prometheus and a command line tool to read the panel values.

This is derived from the work on this site : http://www.morichon.eu/python_WS3500.php

# Programs an tools

## read_pannel.py

```sh
$ python2 read_panel.py
Recording interval : 5 minute(s)
Forecast is Cloudy with Decreasing trends

Value                | Current    | Minumum                        | Maximum
=====================X============X================================X===============================
Internal Temperature |  +22.7     |  +18.7     on 2017-09-02 08:22 |  +29.0     on 2016-12-28 11:05
Internal Humidity    |   51 %     |   28 %     on 2017-03-14 15:42 |   66 %     on 2016-06-23 21:32
External Temperature |  +23.8     |  -22.0     on 2018-01-10 01:38 |  +40.0     on 2016-06-24 14:18
External Humidity    |   47 %     |   26 %     on 2018-04-22 14:32 |   89 %     on 2016-10-26 13:30
Dewpoint             |  +11.7     |  -23.1     on 2017-12-05 19:36 |  +23.3     on 2016-08-26 13:13
Relative Pressure    | 1018.9 hPa | 1041.9 hPa on 2016-12-27 22:02 |  985.0 hPa on 2017-12-11 13:02
```

## daemon.py : Web server and Prometheus exporter

Starting the script directly

```sh
$ python2 daemon.py --device /dev/ttyUSB0 -P 1234 -H 0.0.0.0
2018-05-26 19:24:39,153 - WS3500 - INFO - [fetcher] starting thread
2018-05-26 19:24:39,154 - WS3500 - INFO - [fetcher] opening device
 * Serving Flask app "WS3500" (lazy loading)
 * Environment: production
   WARNING: Do not use the development server in a production environment.
   Use a production WSGI server instead.
 * Debug mode: off
 * Running on http://0.0.0.0:1234/ (Press CTRL+C to quit)
```

The status page :

![status page](.doc/cap-status.png?raw=true)

If there is an error :

![status page with an error](.doc/cap-error.png?raw=true)

# Using docker

You can use docker interactively

```sh
$ docker run -ti --rm --device /dev/ttyUSB0  ws3500  bash -l
```
