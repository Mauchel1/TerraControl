# File zur Temperatur und Feuchtigkeitssteuerung im Terrarium. 
# Anzeige der Daten auf LCD und Eingabe ueber Buttons
# Loggen der Daten

# Erstellt am 17.02.2017 von Daniel Friedrich

#--- Imports ---

import time
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

state = 11

GPIO.setmode(GPIO.BCM)
GPIO.setup(6, GPIO.IN)
GPIO.setup(13, GPIO.IN)
GPIO.setup(19, GPIO.IN)
GPIO.setup(26, GPIO.IN)

prev_select = 1
prev_back = 1
prev_up = 1
prev_down = 1


# Raspberry Pi hardware SPI config:
DC = 23
RST = 24
SPI_PORT = 0
SPI_DEVICE = 0

disp = LCD.PCD8544(DC, RST, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=4000000))

disp.begin(contrast = 60)

# clear display
disp.clear()
disp.display()

# LCD 

image = Image.new('1', (LCD.LCDWIDTH, LCD.LCDHEIGHT))

draw = ImageDraw.Draw(image)
draw.rectangle((0,0,LCD.LCDWIDTH, LCD.LCDHEIGHT), outline=255, fill=255)
font = ImageFont.load_default()


while 1 :
  actualTime = time.time()

  # update buttons

  btn_select_pressed = 0
  btn_back_pressed = 0
  btn_up_pressed = 0
  btn_down_pressed = 0

  btn_select = GPIO.input(6)
  btn_back = GPIO.input(13)
  btn_up = GPIO.input(19)
  btn_down = GPIO.input(26)

  if ((not prev_select) and btn_select):
	btn_select_pressed = 1;

  if ((not prev_back) and btn_back):
	btn_back_pressed = 1;

  if ((not prev_up) and btn_up):
	btn_up_pressed = 1;

  if ((not prev_down) and btn_down):
	btn_down_pressed = 1;

  prev_select = btn_select
  prev_back = btn_back
  prev_up = btn_up
  prev_down = btn_down
  
  time.sleep(0.05) #debounce

  # update sensors
  if ((actualTime - lastTempUpdate) > 1):
    lastTempUpdate = time.time()
    print "Update Sensors"

  # write to LCD

  if state == 11:
    print "elf"
    if ((actualTime - lastLCDUpdate) > 3):
      lastLCDUpdate = time.time()
      state = 12
    draw.text((8,30), 'Testtext', font=font)
    if btn_select_pressed:
      state = 21
  elif state == 12:
    print "zwoelf"
    if ((actualTime - lastLCDUpdate) > 3):
      lastLCDUpdate = time.time()
      state = 11
    if btn_select_pressed:
      state = 21    
  elif state == 21:
    print "21"
    if btn_select_pressed:
      state = 211
    elif btn_back_pressed:
      state = 11
    elif btn_up_pressed:
      state = 22
    elif btn_down_pressed:
      state = 24
  elif state == 22:
    print "22"
    if btn_select_pressed:
      state = 221
    elif btn_back_pressed:
      state = 11
    elif btn_up_pressed:
      state = 23
    elif btn_down_pressed:
      state = 21
  elif state == 23:
    if btn_select_pressed:
      state = 231
    elif btn_back_pressed:
      state = 11
    elif btn_up_pressed:
      state = 24
    elif btn_down_pressed:
      state = 22
  elif state == 24:
    if btn_select_pressed:
      state = 11
    elif btn_back_pressed:
      state = 11
    elif btn_up_pressed:
      state = 21
    elif btn_down_pressed:
      state = 23
  elif state == 211:
    if btn_select_pressed:
      state = 2111
    elif btn_back_pressed:
      state = 21
    elif btn_up_pressed:
      state = 212
    elif btn_down_pressed:
      state = 213
  elif state == 212:
    if btn_select_pressed:
      state = 11
      with open("fuetterung.txt", "a") as f:
        f.write("Fuetterung erfolgreich: " + time.strftime("%a, %d %b %Y", time.gmtime()) + "\n")
    elif btn_back_pressed:
      state = 21
    elif btn_up_pressed:
      state = 213
    elif btn_down_pressed:
      state = 211
  elif state == 213:
    if btn_select_pressed:
      state = 11
      with open("fuetterung.txt", "a") as f:
        f.write("Fuetterung verweigert: " + time.strftime("%a, %d %b %Y", time.gmtime()) + "\n")
    elif btn_back_pressed:
      state = 21
    elif btn_up_pressed:
      state = 211
    elif btn_down_pressed:
      state = 212
  elif state == 221:
    if btn_select_pressed:
      state = 11
      with open("saeuberungen.txt", "a") as f:
        f.write("Saeuberung: " + time.strftime("%a, %d %b %Y", time.gmtime()) + "\n")
    elif btn_back_pressed:
      state = 22
    elif btn_up_pressed:
      state = 222
    elif btn_down_pressed:
      state = 222
  elif state == 222:
    if btn_select_pressed:
      state = 2221
    elif btn_back_pressed:
      state = 22
    elif btn_up_pressed:
      state = 221
    elif btn_down_pressed:
      state = 221
  elif state == 231:
    print "231"
    if btn_select_pressed:
      state = 11
      with open("haeutungen.txt", "a") as f:
        f.write("Haeutung: " + time.strftime("%a, %d %b %Y", time.gmtime()) + "\n")
    elif btn_back_pressed:
      state = 23
  elif state == 2111:
    if btn_select_pressed:
      state = 11
    elif btn_back_pressed:
      state = 211
    elif btn_up_pressed:
      state = 2111      
    elif btn_down_pressed:
      state = 2111
  elif state == 2221:
    if btn_select_pressed:
      state = 11
    elif btn_back_pressed:
      state = 222
    elif btn_up_pressed:
      state = 2221
    elif btn_down_pressed:
      state = 2221
  else:
    print "error - invalid state"

  disp.image(image)
  disp.display()

  # write to log-file


