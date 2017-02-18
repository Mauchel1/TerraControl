# File zur Temperatur und Feuchtigkeitssteuerung im Terrarium. 
# Anzeige der Daten auf LCD und Eingabe ueber Buttons
# Loggen der Daten

# Erstellt am 17.02.2017 von Daniel Friedrich

#--- Imports ---

import time

import Adafruit_Nokia_LCD as LCD
import Adafruit_GPIO.SPI as SPI

import Image

import Image
import ImageDraw
import ImageFont

#--- Config ---

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


while 1 :
  print "RUNRUNRUN"
