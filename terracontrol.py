# File zur Temperatur und Feuchtigkeitssteuerung im Terrarium. 
# Anzeige der Daten auf LCD und Eingabe ueber Buttons
# Loggen der Daten

# Erstellt am 17.02.2017 von Daniel Friedrich

#--- Imports ---

import time
import threading
from datetime import datetime, timedelta
import RPi.GPIO as GPIO
import numpy as np

from influxdb import InfluxDBClient

import Adafruit_Nokia_LCD as LCD
import Adafruit_GPIO.SPI as SPI
import Adafruit_DHT

#18b20 temp sensor
import os
import glob
import time

import Image

import Image
import ImageDraw
import ImageFont

#--- Config ---

actualTime = time.time()
lastTempUpdate = actualTime
lastLCDUpdate = actualTime
lastBacklightUpdate = actualTime
lastLog = actualTime
lastFoggerOn = actualTime

#18b20 temp sensor
os.system('modprobe w1-gpio') 
os.system('modprobe w1-therm')

humSensor = Adafruit_DHT.DHT11

base_dir = '/sys/bus/w1/devices/'
device_folder1 = glob.glob(base_dir + '28*')[0]
device_folder2 = glob.glob(base_dir + '28*')[1]
device_file1 = device_folder1 + '/w1_slave'
device_file2 = device_folder2 + '/w1_slave'

# influxDB
host = "localhost"
port = 8086
user = "root"
password = "root"

dbname = "TerraDB"

client = InfluxDBClient(host, port, user, password, dbname)

state = 11

PIN_FOGGER = 17
PIN_HEAT = 27
PIN_COOLER = 22
PIN_LIGHT = 12
PIN_LED_FUETTERUNG = 16
PIN_LED_SAEUBERUNG = 20
PIN_LED_TEMPERATUR = 21
PIN_BUTTON_SEL = 6
PIN_BUTTON_BACK = 13
PIN_BUTTON_UP = 19
PIN_BUTTON_DOWN = 26
#PIN_BUTTON_PAUSE =
PIN_BACKLIGHT_LCD = 25
PIN_DHT11_1 = 14
PIN_DHT11_2 = 15

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(PIN_BUTTON_SEL, GPIO.IN)  
GPIO.setup(PIN_BUTTON_BACK, GPIO.IN) 
GPIO.setup(PIN_BUTTON_UP, GPIO.IN) 
GPIO.setup(PIN_BUTTON_DOWN, GPIO.IN) 
#GPIO.setup(PIN_BUTTON_PAUSE, GPIO.IN)
GPIO.setup(PIN_BACKLIGHT_LCD, GPIO.OUT)
GPIO.setup(PIN_FOGGER, GPIO.OUT)
GPIO.setup(PIN_HEAT, GPIO.OUT)
GPIO.setup(PIN_LIGHT, GPIO.OUT)
GPIO.setup(PIN_COOLER, GPIO.OUT)
GPIO.setup(PIN_LED_FUETTERUNG, GPIO.OUT)
GPIO.setup(PIN_LED_SAEUBERUNG, GPIO.OUT)
GPIO.setup(PIN_LED_TEMPERATUR, GPIO.OUT)

btn_select_pressed = 0
btn_back_pressed = 0
btn_up_pressed = 0
btn_down_pressed = 0
some_btn_pressed = 0
btn_pause_pressed = 0

prev_select = 1
prev_back = 1
prev_up = 1
prev_down = 1

heaterOn = 0
coolerOn = 0
foggerOn = 0
humidity = 50
actualTemp = 22
rawTemp1 = 22
rawTemp2 = 22
rawHum1 = 50
hum1 = 50
rawHum2 = 50
hum2 = 50
humidityKrit = 40
tempStable = 0
tempNightLow = 18
tempDayLow = 26
tempDayHigh = 31
tempHystereseNight = 2
averageHum1Array = np.zeros(5)
averageHum2Array = np.zeros(5)
averageHum1 = 50
averageHum2 = 50
averageTemp1Array = np.zeros(5)
averageTemp2Array = np.zeros(5)
averageTemp1 = 25
averageTemp2 = 25

sunriseH = 9
sunriseM = 15
sunsetH = 20
sunsetM = 20

# Raspberry Pi hardware SPI config:
DC = 23
RST = 24
SPI_PORT = 0
SPI_DEVICE = 0

disp = LCD.PCD8544(DC, RST, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=4000000))

disp.begin(contrast = 55)

# clear display
disp.clear()
disp.display()

# LCD 

image = Image.new('1', (LCD.LCDWIDTH, LCD.LCDHEIGHT))

draw = ImageDraw.Draw(image)
draw.rectangle((0,0,LCD.LCDWIDTH, LCD.LCDHEIGHT), outline=255, fill=255)
font = ImageFont.load_default()

# get last Dates
lastH = datetime.now()

infile = open('/home/pi/terra/haeutungen.txt')
lines = infile.readlines()
infile.close()

for revert_line in lines [::-1]:
  if "Haeutung: " in revert_line:
    line = revert_line[10:] #ersten Teil loeschen
    line = line.splitlines() #letztes \n entfernen
    lastH = datetime.strptime(line[0], "%a, %d %b %Y")
    break

# get next Dates
nextFuetterung = datetime.now() 
nextSaeuberung = datetime.now()

infile = open('/home/pi/terra/saeuberungen.txt')
lines = infile.readlines()
infile.close()

for revert_line in lines [::-1]:
  if "naechste Saeuberung: " in revert_line:
    line = revert_line[21:] #ersten Teil loeschen
    line = line.splitlines() #letztes \n entfernen
    nextSaeuberung = datetime.strptime(line[0], "%B %d %Y")
    break

infile = open('/home/pi/terra/fuetterung.txt')
lines = infile.readlines()
infile.close()

for revert_line in lines [::-1]:
  if "naechste Fuetterung: " in revert_line:
    line = revert_line[21:] #ersten Teil loeschen
    line = line.splitlines() #letztes \n entfernen
    nextFuetterung = datetime.strptime(line[0], "%B %d %Y")
    break

def read_temp_raw(device_file):
  f = open(device_file, 'r')
  lines = f.readlines()
  f.close()
  return lines

def read_temp(sensor):
  lines = read_temp_raw(sensor)
  while lines[0].strip()[-3:] != 'YES':
    time.sleep(0.2)
    lines = read_temp_raw(sensor)
  equals_pos = lines[1].find('t=')
  if equals_pos != -1:
    temp_string = lines[1][equals_pos+2:]
    temp_c = float(temp_string) / 1000.0
    #TODO return bei else-zweig hinzufuegen
    return temp_c

def thread_temp_1(sensor):
  global rawTemp1
  rawTemp1 = read_temp(sensor)

def thread_temp_2(sensor):
  global rawTemp2
  rawTemp2 = read_temp(sensor)
  
def thread_hum_1(sensor):
  global rawHum1, rawTempDHT1  
  rawHum1, rawTempDHT1 = Adafruit_DHT.read_retry(sensor, PIN_DHT11_1)
  
def thread_hum_2(sensor):
  global rawHum2, rawTempDHT2  
  rawHum2, rawTempDHT2 = Adafruit_DHT.read_retry(sensor, PIN_DHT11_2)

def thread_LCD(threadName):
  global actualDate
  global nextFInDays
  global nextSInDays
  global nextFuetterung
  global nextSaeuberung
  global lastH
  global state
  global some_btn_pressed
  global lastBacklightUpdate
  global actualTime
  global LCDDate
  global lastTempUpdate
  global lastLCDUpdate
  global lastLog

  global prev_select
  global prev_back
  global prev_up
  global prev_down

  global heaterOn
  global coolerOn
  global foggerOn
  global humidity 
  global actualTemp 
  global rawTemp1 
  global rawTemp2 
  global rawHum1 
  global hum1 
  global rawHum2 
  global hum2 
  global humidityKrit 
  global tempStable
  global tempNightLow 
  global tempDayLow 
  global tempDayHigh 
  global tempHystereseNight
  global averageHum1Array
  global averageHum2Array
  global averageHum1
  global averageHum2
  global averageTemp1Array
  global averageTemp2Array
  global averageTemp1
  global averageTemp2

  global sunriseH
  global sunriseM
  global sunsetH
  global sunsetM

  # LCD backlight control
  while 1 :

    # update buttons
    btn_select_pressed = 0
    btn_back_pressed = 0 
    btn_up_pressed = 0
    btn_down_pressed = 0
    some_btn_pressed = 0

    btn_select = GPIO.input(PIN_BUTTON_SEL)
    btn_back = GPIO.input(PIN_BUTTON_BACK)
    btn_up = GPIO.input(PIN_BUTTON_UP)
    btn_down = GPIO.input(PIN_BUTTON_DOWN)

    if ((not prev_select) and btn_select):
      btn_select_pressed = 1;
      some_btn_pressed = 1;

    if ((not prev_back) and btn_back):
      btn_back_pressed = 1;
      some_btn_pressed = 1;

    if ((not prev_up) and btn_up):
      btn_up_pressed = 1;
      some_btn_pressed = 1;

    if ((not prev_down) and btn_down):
      btn_down_pressed = 1;
      some_btn_pressed = 1;

    prev_select = btn_select
    prev_back = btn_back
    prev_up = btn_up
    prev_down = btn_down
  
    time.sleep(0.05) #debounce

    if (some_btn_pressed == 1):
      GPIO.output(PIN_BACKLIGHT_LCD, GPIO.HIGH)
      lastBacklightUpdate = time.time()
      some_btn_pressed = 0

    if ((actualTime - lastBacklightUpdate) > 3):
      GPIO.output(PIN_BACKLIGHT_LCD, GPIO.LOW)

    # write to LCD

    draw.rectangle((0,0,LCD.LCDWIDTH, LCD.LCDHEIGHT), outline=255, fill=255)
    LCDDate = time.strftime("%d.%m.%y %H:%M", time.localtime())

    if state == 11:
      draw.text((0,1), LCDDate, font=font)    
      draw.text((0,13), 'Temp1: ' + ("%.2f" % rawTemp1) + ' C', font=font)
      draw.text((0,25), 'Hum1: ' + ("%.1f" % hum1) + ' %', font=font)
      draw.text((0,37), 'Fuetter: ' + str(nextFInDays) + " d", font=font)
      if ((actualTime - lastLCDUpdate) > 5):
        lastLCDUpdate = time.time()
        state = 12
      if btn_select_pressed:
        state = 21
    elif state == 12:
      draw.text((0,1), LCDDate, font=font)    
      draw.text((0,13), 'Temp2: ' + ("%.2f" % rawTemp2) + ' C', font=font)
      draw.text((0,25), 'Hum2: ' + ("%.1f" % hum2) + ' %', font=font)
      draw.text((0,37), 'Saeuber: ' + str(nextSInDays) + " d", font=font)
      if ((actualTime - lastLCDUpdate) > 5):
        lastLCDUpdate = time.time()
        state = 11
      if btn_select_pressed:
        state = 21    
    elif state == 21:
      draw.polygon([(0,3), (6,6), (0,9)], outline=0, fill=0)
      draw.text((10,1), 'Fuetterung', font=font)    
      draw.text((10,13), 'Saeuberung', font=font)
      draw.text((10,25), 'Haeutung', font=font)
      draw.text((10,37), 'Licht an', font=font)
      if btn_select_pressed:
        state = 211
      elif btn_back_pressed:
        state = 11
      elif btn_up_pressed:
        state = 22
      elif btn_down_pressed:
        state = 24
    elif state == 22:
      draw.polygon([(0,15), (6,18), (0,21)], outline=0, fill=0)
      draw.text((10,1), 'Fuetterung', font=font)    
      draw.text((10,13), 'Saeuberung', font=font)
      draw.text((10,25), 'Haeutung', font=font)
      draw.text((10,37), 'Licht an', font=font)
      if btn_select_pressed:
        state = 221
      elif btn_back_pressed:
        state = 11
      elif btn_up_pressed:
        state = 23
      elif btn_down_pressed:
        state = 21
    elif state == 23:
      draw.polygon([(0,27), (6,30), (0,33)], outline=0, fill=0)
      draw.text((10,1), 'Fuetterung', font=font)    
      draw.text((10,13), 'Saeuberung', font=font)
      draw.text((10,25), 'Haeutung', font=font)
      draw.text((10,37), 'Licht an', font=font)
      if btn_select_pressed:
        state = 231
      elif btn_back_pressed:
        state = 11
      elif btn_up_pressed:
        state = 24
      elif btn_down_pressed:
        state = 22
    elif state == 24:
      draw.polygon([(0,39), (6,42), (0,45)], outline=0, fill=0)
      draw.text((10,1), 'Fuetterung', font=font)    
      draw.text((10,13), 'Saeuberung', font=font)
      draw.text((10,25), 'Haeutung', font=font)
      draw.text((10,37), 'Licht an', font=font)
      if btn_select_pressed:
        state = 11
      elif btn_back_pressed:
        state = 11
      elif btn_up_pressed:
        state = 21
      elif btn_down_pressed:
        state = 23
    elif state == 211:
      draw.polygon([(0,3), (6,6), (0,9)], outline=0, fill=0)
      draw.text((10,1), 'naechste F.', font=font)    
      draw.text((10,13), 'erfolgreich!', font=font)
      draw.text((10,25), 'verweigert...', font=font)
      if btn_select_pressed:
        state = 2111
        nextF = 5
      elif btn_back_pressed:
        state = 21
      elif btn_up_pressed:
        state = 212
      elif btn_down_pressed:
        state = 213
    elif state == 212:
      draw.polygon([(0,15), (6,18), (0,21)], outline=0, fill=0)
      draw.text((10,1), 'naechste F.', font=font)    
      draw.text((10,13), 'erfolgreich!', font=font)
      draw.text((10,25), 'verweigert...', font=font)
      if btn_select_pressed:
        state = 2121
      elif btn_back_pressed:
        state = 21
      elif btn_up_pressed:
        state = 213
      elif btn_down_pressed:
        state = 211
    elif state == 2121:
      draw.polygon([(0,3), (6,6), (0,9)], outline=0, fill=0)
      draw.text((10,1), 'erfolg er', font=font)    
      draw.text((10,13), 'erfolg sie', font=font)
      draw.text((10,25), 'beide', font=font)
      if btn_select_pressed:
        state = 11
        with open("/home/pi/terra/fuetterung.txt", "a") as f:
          f.write("Fuetterung erfolgreich ER: " + time.strftime("%a, %d %b %Y", time.localtime()) + "\n")
      elif btn_back_pressed:
        state = 212
      elif btn_up_pressed:
        state = 2122
      elif btn_down_pressed:
        state = 2123
    elif state == 2122:
      draw.polygon([(0,15), (6,18), (0,21)], outline=0, fill=0)
      draw.text((10,1), 'erfolg er', font=font)    
      draw.text((10,13), 'erfolg sie', font=font)
      draw.text((10,25), 'beide', font=font)
      if btn_select_pressed:
        state = 11
        with open("/home/pi/terra/fuetterung.txt", "a") as f:
          f.write("Fuetterung erfolgreich SIE: " + time.strftime("%a, %d %b %Y", time.localtime()) + "\n")
      elif btn_back_pressed:
        state = 212
      elif btn_up_pressed:
        state = 2123
      elif btn_down_pressed:
        state = 2121
    elif state == 2123:
      draw.polygon([(0,27), (6,30), (0,33)], outline=0, fill=0)
      draw.text((10,1), 'erfolg er', font=font)    
      draw.text((10,13), 'erfolg sie', font=font)
      draw.text((10,25), 'beide', font=font)
      if btn_select_pressed:
        state = 11
        with open("/home/pi/terra/fuetterung.txt", "a") as f:
          f.write("Fuetterung erfolgreich ER: " + time.strftime("%a, %d %b %Y", time.localtime()) + "\n")
          f.write("Fuetterung erfolgreich SIE: " + time.strftime("%a, %d %b %Y", time.localtime()) + "\n")
      elif btn_back_pressed:
        state = 212
      elif btn_up_pressed:
        state = 2121
      elif btn_down_pressed:
        state = 2122
    elif state == 213:
      draw.polygon([(0,27), (6,30), (0,33)], outline=0, fill=0)
      draw.text((10,1), 'naechste F.', font=font)    
      draw.text((10,13), 'erfolgreich!', font=font)
      draw.text((10,25), 'verweigert...', font=font)
      if btn_select_pressed:
        state = 2131
      elif btn_back_pressed:
        state = 21
      elif btn_up_pressed:
        state = 211
      elif btn_down_pressed:
        state = 212
    elif state == 2131:
      draw.polygon([(0,3), (6,6), (0,9)], outline=0, fill=0)
      draw.text((10,1), 'verweig. er', font=font)    
      draw.text((10,13), 'verweig. sie', font=font)
      draw.text((10,25), 'beide', font=font)
      if btn_select_pressed:
        state = 11
        with open("/home/pi/terra/fuetterung.txt", "a") as f:
          f.write("Fuetterung verweigert ER: " + time.strftime("%a, %d %b %Y", time.localtime()) + "\n")
      elif btn_back_pressed:
        state = 213
      elif btn_up_pressed:
        state = 2132
      elif btn_down_pressed:
        state = 2133
    elif state == 2132:
      draw.polygon([(0,15), (6,18), (0,21)], outline=0, fill=0)
      draw.text((10,1), 'verweig. er', font=font)    
      draw.text((10,13), 'verweig. sie', font=font)
      draw.text((10,25), 'beide', font=font)
      if btn_select_pressed:
        state = 11
        with open("/home/pi/terra/fuetterung.txt", "a") as f:
          f.write("Fuetterung verweigert SIE: " + time.strftime("%a, %d %b %Y", time.localtime()) + "\n")
      elif btn_back_pressed:
        state = 213
      elif btn_up_pressed:
        state = 2133
      elif btn_down_pressed:
        state = 2131
    elif state == 2133:
      draw.polygon([(0,27), (6,30), (0,33)], outline=0, fill=0)
      draw.text((10,1), 'verweig. er', font=font)    
      draw.text((10,13), 'verweig. sie', font=font)
      draw.text((10,25), 'beide', font=font)
      if btn_select_pressed:
        state = 11
        with open("/home/pi/terra/fuetterung.txt", "a") as f:
          f.write("Fuetterung verweigert ER: " + time.strftime("%a, %d %b %Y", time.localtime()) + "\n")
          f.write("Fuetterung verweigert SIE: " + time.strftime("%a, %d %b %Y", time.localtime()) + "\n")
      elif btn_back_pressed:
        state = 213
      elif btn_up_pressed:
        state = 2131
      elif btn_down_pressed:
        state = 2132
    elif state == 221:
      draw.polygon([(0,3), (6,6), (0,9)], outline=0, fill=0)
      draw.text((10,1), 'heute gemacht', font=font)    
      draw.text((10,13), 'naechste S.', font=font)
      if btn_select_pressed:
        state = 11
        with open("/home/pi/terra/saeuberungen.txt", "a") as f:
          f.write("Saeuberung: " + time.strftime("%a, %d %b %Y", time.localtime()) + "\n")
      elif btn_back_pressed:
        state = 22
      elif btn_up_pressed:
        state = 222
      elif btn_down_pressed:
        state = 222
    elif state == 222:
      draw.polygon([(0,15), (6,18), (0,21)], outline=0, fill=0)
      draw.text((10,1), 'heute gemacht', font=font)    
      draw.text((10,13), 'naechste S.', font=font)
      if btn_select_pressed:
        nextS = 5
        state = 2221
      elif btn_back_pressed:
        state = 22
      elif btn_up_pressed:
        state = 221
      elif btn_down_pressed:
        state = 221
    elif state == 231:
      draw.polygon([(0,3), (6,6), (0,9)], outline=0, fill=0)
      draw.text((10,1), 'heute gewesen', font=font)    
      draw.text((0,25), 'letzte Haeutung:', font=font)
      draw.text((20,37), lastH.strftime("%d.%m.%Y"), font=font)
      if btn_select_pressed:
        state = 11
        lastH = datetime.now()
        with open("/home/pi/terra/haeutungen.txt", "a") as f:
          f.write("Haeutung: " + time.strftime("%a, %d %b %Y", time.localtime()) + "\n")
      elif btn_back_pressed:
        state = 23
    elif state == 2111:
      draw.text((0,1), 'naechste F in:', font=font)    
      draw.text((40,20), str(nextF), font=font)
      draw.text((0,37), 'Tagen', font=font)
      if btn_select_pressed:
        state = 11
        td = timedelta(days=nextF)
        nextDate = actualDate + td
        nextFuetterung = nextDate
        with open("/home/pi/terra/fuetterung.txt", "a") as f:
          f.write("naechste Fuetterung: " + nextDate.strftime("%B %d %Y") + "\n")
      elif btn_back_pressed:
        state = 211
      elif btn_up_pressed:      
        nextF += 1
      elif btn_down_pressed:
        nextF -= 1
        if (nextF < 1):
          nextF = 1
    elif state == 2221:
      draw.text((0,1), 'naechste S in:', font=font)    
      draw.text((40,20), str(nextS), font=font)
      draw.text((0,37), 'Wochen', font=font)
      if btn_select_pressed:
        state = 11
        td = timedelta(days=nextS*7)
        nextDate = actualDate + td
        nextSaeuberung = nextDate
        with open("/home/pi/terra/saeuberungen.txt", "a") as f:
          f.write("naechste Saeuberung: " + nextDate.strftime("%B %d %Y") + "\n")
      elif btn_back_pressed:
        state = 222
      elif btn_up_pressed:
        nextS += 1
      elif btn_down_pressed:       
        nextS -= 1
        if (nextS < 1):
          nextS = 1
    else:
      print "error - invalid state"
 
    disp.image(image)
    disp.display()

thrd_LCD = threading.Thread(target=thread_LCD, args=("Thread_LCD",))
thrd_LCD.setDaemon(True)
thrd_LCD.start()

while 1 :
  while 1:
    actualTime = time.time()
    actualDate = datetime.now()
    nextFInDays = (nextFuetterung - actualDate).days + 1 # Anzahl der verbleibenden Tage
    nextSInDays = (nextSaeuberung - actualDate).days + 1 # Anzahl der verbleibenden Tage
    
    while (btn_pause_pressed == 1):
      time.sleep(1)
      #btn_pause_pressed = GPIO.input(PIN_BUTTON_PAUSE)
    
    # update sensors
    if ((actualTime - lastTempUpdate) > 4):
      lastTempUpdate = time.time()
      thrd1 = threading.Thread(target=thread_temp_1, args=(device_file1,))
      thrd1.start()
      thrd2 = threading.Thread(target=thread_temp_2, args=(device_file2,))
      thrd2.start()
      thrd3 = threading.Thread(target=thread_hum_1, args=(humSensor,))
      thrd3.start()
      thrd4 = threading.Thread(target=thread_hum_2, args=(humSensor,))
      thrd4.start()
      thrd1.join()
      thrd2.join()
      thrd3.join()
      thrd4.join()
      actualTemp = (rawTemp1 + rawTemp2) / 2
      print "actualTemp = " + str(actualTemp)
      if (rawHum1 < 100 and rawHum1 > 0):
        hum1 = rawHum1
      if (rawHum2 < 100 and rawHum2 > 0):
        hum2 = rawHum2
      averageHum1Array = np.insert(averageHum1Array, 0, hum1)
      averageHum1Array = np.resize(averageHum1Array, 5)
      averageHum1 = np.mean(averageHum1Array)
      averageHum2Array = np.insert(averageHum2Array, 0, hum2)
      averageHum2Array = np.resize(averageHum2Array, 5)
      averageHum2 = np.mean(averageHum2Array)
      humidity = (averageHum1 + averageHum2) / 2
      averageTemp1Array = np.insert(averageTemp1Array, 0, rawTemp1)
      averageTemp1Array = np.resize(averageTemp1Array, 5)
      averageTemp1 = np.mean(averageTemp1Array)
      averageTemp2Array = np.insert(averageTemp2Array, 0, rawTemp2)
      averageTemp2Array = np.resize(averageTemp2Array, 5)
      averageTemp2 = np.mean(averageTemp2Array)
      actualTemp = (averageTemp1 * 0.25) + (averageTemp2 * 0.75)

      if (np.count_nonzero(averageTemp1Array) == 5): # bei Programmstart das array mit werten fuellen
        break

  # Regulation

  if ((actualDate.hour > sunriseH and actualDate.hour < sunsetH) or (actualDate.hour == sunriseH and actualDate.minute > sunriseM) or (actualDate.hour == sunsetH and actualDate.minute < sunsetM)):
    day = 1
    print "day"
  else:
    day = 0
    print "night"
  
  if (day):
    
    GPIO.output(PIN_LIGHT, GPIO.LOW)
    print "Licht an"

    # Temperature Area
    if (actualTemp < tempDayLow):
      tempStable = 0
      heaterOn = 1
      GPIO.output(PIN_HEAT, GPIO.LOW)
      print "Hitze an"
    elif (actualTemp > tempDayHigh):
      tempStable = 0
      coolerOn = 1
      GPIO.output(PIN_COOLER, GPIO.LOW)
      print "Luefter an"
    else:
      tempStable = 1
      
    if (heaterOn and actualTemp > (tempDayLow + ((tempDayHigh - tempDayLow) / 2)) ):
      heaterOn = 0
      GPIO.output(PIN_HEAT, GPIO.HIGH)
      print "Hitze aus"
          
    if (coolerOn and actualTemp < (tempDayLow + ((tempDayHigh - tempDayLow) / 2)) ):
      coolerOn = 0
      GPIO.output(PIN_COOLER, GPIO.HIGH)
      print "Luefter aus"
          
    # Humidity Area
    #if (tempStable and (humidity < humidityKrit) and ((actualTime - lastFoggerOn) > 300)):
    #  GPIO.output(PIN_FOGGER, GPIO.LOW)
    #  print "Nebel an"
    #  lastFoggerOn = time.time()
    #  foggerOn = 1
      
  else:
    GPIO.output(PIN_LIGHT, GPIO.HIGH)
    print "Licht aus"
    if (actualTemp < tempNightLow):
      GPIO.output(PIN_HEAT, GPIO.LOW)
      tempStable = 0
      print "Hitze an"
    elif (actualTemp > tempNightLow + tempHystereseNight):
      print "Hitze aus"
      tempStable = 1
      GPIO.output(PIN_HEAT, GPIO.HIGH)
  
  if (foggerOn and (actualTime - lastFoggerOn) > 20):
    foggerOn = 0
    GPIO.output(PIN_FOGGER, GPIO.HIGH)

  # Warning LED's
  
  if (nextFInDays < 3):
    GPIO.output(PIN_LED_FUETTERUNG, GPIO.HIGH)
    print "LED Fuetterung an"
  else: 
    GPIO.output(PIN_LED_FUETTERUNG, GPIO.LOW)
    
  if (nextSInDays < 3):
    GPIO.output(PIN_LED_SAEUBERUNG, GPIO.HIGH)
    print "LED Saeuberung an"
  else: 
    GPIO.output(PIN_LED_SAEUBERUNG, GPIO.LOW)
    
  if (not tempStable):
    print "LED TEMP an"
    GPIO.output(PIN_LED_TEMPERATUR, GPIO.HIGH)
  else: 
    GPIO.output(PIN_LED_TEMPERATUR, GPIO.LOW)
  

  # write to log-file

  if ((actualTime - lastLog) > 5):
    lastLog = time.time()
    json_body = [
    {
      "measurement": "terralog",
        "fields": {
          "Temp1" : float(rawTemp1), "Temp2" : float(rawTemp2), "Hum1" : float(hum1), "Hum2" : float(hum2), "Temp" : float(actualTemp), "Hum" : float(humidity)
        }
      }
    ]

    client.write_points(json_body)
    print "write log file"

