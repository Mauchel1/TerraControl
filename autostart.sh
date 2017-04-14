#!/bin/bash

#prüft ob terracontrol läuft, startet es gegebenfalls

if ! pgrep -f "terra/terracontrol.py" >/dev/null 2>&1 ; then

  python terra/terracontrol.py

fi

#prüft ob influxDB läuft , startet es gegebenfalls

if ! pgrep -f "influxd" >/dev/null 2>&1 ; then

  influxd

fi

