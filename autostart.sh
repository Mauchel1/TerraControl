#!/bin/bash

#prüft ob terracontrol läuft, startet es gegebenfalls

if ! pgrep -f "terra/terracontrol.py" >/dev/null 2>&1 ; then

  python terra/terracontrol.py

fi

#prüft ob influxDB läuft , startet es gegebenfalls

if ! pgrep -f "influxd" >/dev/null 2>&1 ; then

  influxd

fi

#prüft ob grafana läuft, startet es gegebenfalls

if ! pgrep -f "/usr/sbin/grafa" >/dev/null 2>&1 ; then

  sudo service grafana-server start

fi

