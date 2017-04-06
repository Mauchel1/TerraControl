# File zur Temperatur und Feuchtigkeitssteuerung im Terrarium. 
# Anzeige der Daten auf LCD und Eingabe ueber Buttons
# Loggen der Daten

# Erstellt am 17.02.2017 von Daniel Friedrich

#--- Imports ---

import time
from datetime import datetime, timedelta
import RPi.GPIO as GPIO

import Adafruit_Nokia_LCD as LCD
import Adafruit_GPIO.SPI as SPI

import Image

import Image
import ImageDraw
import ImageFont

#--- Config ---

actualTime = time.time()
lastTempUpdate = actualTime
lastLCDUpdate = actualTime
lastBacklightUpdate = actualTime

state = 11

PIN_FOGGER = 27

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(6, GPIO.IN)  #btn
GPIO.setup(13, GPIO.IN) #btn
GPIO.setup(19, GPIO.IN) #btn
GPIO.setup(26, GPIO.IN) #btn
GPIO.setup(25, GPIO.OUT)#backlight LCD
GPIO.setup(PIN_FOGGER, GPIO.OUT)

prev_select = 1
prev_back = 1
prev_up = 1
prev_down = 1

foggerOn = 0
humidity = 50
humidityKrit = 40
tempStable = 0
tempNightLow = 18
tempDayLow = 28
tempDayHigh = 32
tempHystereseNight = 2

sunriseH = 8
sunriseM = 15
sunsetH = 21
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

while 1 :
  actualTime = time.time()
  actualDate = datetime.now()
  nextFInDays = (nextFuetterung - actualDate).days + 1 # Anzahl der verbleibenden Tage
  nextSInDays = (nextSaeuberung - actualDate).days + 1 # Anzahl der verbleibenden Tage

  # update buttons

  btn_select_pressed = 0
  btn_back_pressed = 0
  btn_up_pressed = 0
  btn_down_pressed = 0
  some_btn_pressed = 0

  btn_select = GPIO.input(6)
  btn_back = GPIO.input(13)
  btn_up = GPIO.input(19)
  btn_down = GPIO.input(26)

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

  # update sensors
  if ((actualTime - lastTempUpdate) > 1):
    lastTempUpdate = time.time()
    print "Update Sensors"
    #actualTemp = (in Grad C)
    #humidity = (0-100)
  
  # Regulation

  if ((actualDate.hour > sunriseH and actualDate.hour < sunsetH) or (actualDate.hour == sunriseH and actualDate.minute > sunriseM) or (actualDate.hour == sunsetH and actualDate.minute < sunsetM)):
    day = 1
  else:
    day = 0
  
  if (day):
    
    if (actualTemp < tempDayLow):
      tempStable = 0
      #switch on Heat
    elif (actualTemp > tempDayHigh):
      tempStable = 0
      #switch on cooler
    else:
      tempStable = 1
      #switch off cooler // Heat
      
    # Humidity Area
    if (tempStable and (humidity < humidityKrit) and ((actualTime - lastFoggerOn) > 300)):
      GPIO.output(PIN_FOGGER, GPIO.HIGH)
      lastFoggerOn = time.time()
      foggerOn = 1
      
  else:
    if (actualTemp < tempNightLow):
      #switch on heat
    elif (actualTemp > tempNightLow + tempHystereseNight):
      #switch off heat
      
    
  if (foggerOn and (actualTime - lastFoggerOn) > 20):
	  #switch off fogger
    foggerOn = 0
    GPIO.output(PIN_FOGGER, GPIO.LOW)

  # LCD backlight control

  if (some_btn_pressed == 1):
    GPIO.output(25, GPIO.HIGH)
    lastBacklightUpdate = time.time()
    some_btn_pressed = 0

  if ((actualTime - lastBacklightUpdate) > 3):
    GPIO.output(25, GPIO.LOW)

  # write to LCD

  draw.rectangle((0,0,LCD.LCDWIDTH, LCD.LCDHEIGHT), outline=255, fill=255)
  LCDDate = time.strftime("%d.%m.%y %H:%M", time.localtime())

  if state == 11:
    draw.text((0,1), LCDDate, font=font)    
    draw.text((0,13), 'Temp1: ' + '00.0 C', font=font)
    draw.text((0,25), 'Hum1: ' + '00.0 %', font=font)
    draw.text((0,37), 'Fuetter: ' + str(nextFInDays) + " d", font=font)
    if ((actualTime - lastLCDUpdate) > 5):
      lastLCDUpdate = time.time()
      state = 12
    if btn_select_pressed:
      state = 21
  elif state == 12:
    draw.text((0,1), LCDDate, font=font)    
    draw.text((0,13), 'Temp2: ' + '00.0 C', font=font)
    draw.text((0,25), 'Hum2: ' + '00.0 %', font=font)
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
      state = 11
      with open("/home/pi/terra/fuetterung.txt", "a") as f:
        f.write("Fuetterung erfolgreich: " + time.strftime("%a, %d %b %Y", time.localtime()) + "\n")
    elif btn_back_pressed:
      state = 21
    elif btn_up_pressed:
      state = 213
    elif btn_down_pressed:
      state = 211
  elif state == 213:
    draw.polygon([(0,27), (6,30), (0,33)], outline=0, fill=0)
    draw.text((10,1), 'naechste F.', font=font)    
    draw.text((10,13), 'erfolgreich!', font=font)
    draw.text((10,25), 'verweigert...', font=font)
    if btn_select_pressed:
      state = 11
      with open("/home/pi/terra/fuetterung.txt", "a") as f:
        f.write("Fuetterung verweigert: " + time.strftime("%a, %d %b %Y", time.localtime()) + "\n")
    elif btn_back_pressed:
      state = 21
    elif btn_up_pressed:
      state = 211
    elif btn_down_pressed:
      state = 212
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

  # write to log-file


