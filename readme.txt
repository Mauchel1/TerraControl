Folgende Kommandos sind wichtig fuer die Kommandozeile:

Um Zahl der relevanten Prozesse zu bekommen
    pgrep -f terra/terracontrol.py
    pgrep -f /usr/sbin/grafa
    pgrep -f influxd

Um Prozesse der Zahl XXX abzubrechen
    kill -9 XXX

Wenn git push nicht funktioniert (weil no route to host - wlanzugriff)
    sudo ifdown eth0 

Um terracontrol zu starten
    python terra/terracontrol.py

Um Grafana zu starten:
    service grafana-server start

Um influxDB zu starten
    influxd
