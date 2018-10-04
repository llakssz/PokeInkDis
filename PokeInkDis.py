#!/usr/bin/env python
# -*- coding: utf-8 -*-

# PokeInkDis
# Joshua Miller - jtm.gg - 2018
# v1.0

import argparse
import calendar
import datetime
import json
import locale
import os
import random
import sys
from collections import OrderedDict

from PIL import Image, ImageDraw, ImageFont

import inkyphat
import requests

total_pokes = 649
# First national dex of each gen
poke_gen = [1, 152, 252, 387, 494]
today = datetime.datetime.today()
black = (0, 0, 0)
white = (255, 255, 255)
red = (255, 0, 0)

# Check if pokemon number is legal. This is in a function, 
# because if we use argparse's range restriction, on help/error it prints every single number possibility and is ugly
def poke_check(string):
    try:
        value = int(string)
        if (value < 1) or (value > total_pokes):
            msg = "{0} is not valid. Choose a number from 1 to {1}".format(string, total_pokes)
            raise argparse.ArgumentTypeError(msg)
        return value
    except ValueError:
        msg = "{0} is not valid. Choose a number from 1 to {1}".format(string, total_pokes)
        raise argparse.ArgumentTypeError(msg)

parser = argparse.ArgumentParser()
parser.add_argument('-dskey', action='store', dest='dskey', required=True, help='Dark Sky API key')
parser.add_argument('-lat', action='store', dest='lat', default='40.737778', help='Latitude')
parser.add_argument('-lon', action='store', dest='lon', default='-73.986111', help='Longitude')
parser.add_argument('-g', action='store', dest='gen', type=int, default='0', choices=range(1, len(poke_gen)+1), help='Choose a generation to limit to (Gen Number)')
parser.add_argument('-p', action='store', dest='pokemon', type=poke_check, help='Choose a specific pokemon (Dex Number)')
parser.add_argument('-j', action='store_true', help='Display in Japanese')
parser.add_argument('-f', action='store_false', dest='celsius', default=True, help='Use Fahrenheit')
args = parser.parse_args()

# Default text
min_text = "Min"
max_text = "Max"
pop_text = "PoP"

# Default date format
date_format = "%a %b %d"

# Japanese
if args.j:
    locale.setlocale(locale.LC_ALL, 'ja_JP.utf8')
    date_format = "%m月%d日(%a)"
    min_text = "最低"
    max_text = "最高"
    pop_text = "降水確率"

# Fonts used
# Thanks itouhiro(?)
# http://mplus-fonts.osdn.jp/mplus-bitmap-fonts/
# https://osdn.net/projects/mix-mplus-ipa/releases/58930
font = ImageFont.truetype("PixelMplus10-Regular.ttf", 10)
bold_font = ImageFont.truetype("PixelMplus10-Bold.ttf", 10)
# Thanks weathericons.io - https://erikflowers.github.io/weather-icons/
weather_font = ImageFont.truetype("weathericons-regular-webfont.ttf", 26)

# Get weather data from Dark Sky
r = requests.get('https://api.darksky.net/forecast/{0}/{1},{2}?{3}&exclude=currently,minutely,hourly,alerts,flags'.format(args.dskey, args.lat, args.lon, "units=si&" if args.celsius else ""))
min_temp = int(r.json()['daily']['data'][0]['temperatureLow'])
max_temp = int(r.json()['daily']['data'][0]['temperatureHigh'])
pop = int(100 * r.json()['daily']['data'][0]['precipProbability'])
weather_icon_text = r.json()['daily']['data'][0]['icon']
# Get the matching unicode character for the weather font
weather_icon = ""
with open("weather.json", "r") as read_file:
    data = json.load(read_file)
    weather_icon = data[weather_icon_text]["char"]  

# Check if it's a very auspicious day, I really tried to implement my own method but the calculations needed are not pretty.
r = requests.get('http://koyomi.zing2.org/api/?targetyyyy={0}&targetmm={1}&targetdd={2}&mode=d&cnt=1'.format(today.year, today.month, today.day))
very_auspicious = False
if (r.json()['datelist'][today.strftime("%Y-%m-%d")]['kyurekim'] + r.json()['datelist'][today.strftime("%Y-%m-%d")]['kyurekid']) % 6 == 0:
    very_auspicious = True

# If a certain generation was selected
if args.gen:
    # If the selected gen is the last gen, get max value from total pokemon
    if args.gen == len(poke_gen):
        poke_num = random.randint(poke_gen[args.gen - 1], total_pokes)
    else:
        # Otherwise, get max value from next gen -1
        poke_num = random.randint(poke_gen[args.gen - 1], poke_gen[args.gen] - 1)
else:
    poke_num = random.randint(1, total_pokes)

# If a specific pokemon was selected
if args.pokemon:
    poke_num = args.pokemon

# Get the pokemon's name from the json file
with open("pokemon.json", "r") as read_file:
    data = json.load(read_file)
    if args.j:
        poke_name = data[str(poke_num)]["ja"]
    else:
        poke_name = data[str(poke_num)]["en"] 

# Build the path to the selected pokemon image and open it
poke_path = os.path.join("pokemon", str(poke_num) + ".png")
poke_image = Image.open(poke_path).convert("RGBA")

# Open our base image (full screen size) - we will draw everything onto this
base = Image.open("base_dot.png").convert("RGBA")
draw = ImageDraw.Draw(base)

# Paste our pokemon over the dotted square area on the base
base.paste(poke_image, (4, 4), poke_image)
# Get the width of the text that the national dex number label will be
national_dex_w = draw.textsize("#"+str(poke_num).zfill(3), font=bold_font)[0]
# Use the width to draw a black rectangle behind the white text
# Drawing 2 pixels longer, because I want a 1px buffer left and right
draw.rectangle(((4, 4), (4+national_dex_w+1, 14)), fill="#000000")
# Draw the white national dex text
draw.text((5, 4),"#"+str(poke_num).zfill(3), white, font=bold_font)
# Do similar stuff for the name of the pokemon...
name_w = draw.textsize(poke_name, font=bold_font)[0]
draw.rectangle(((4+96-name_w-2, 4), (4+96-1, 14)), fill="#000000")
draw.text((4+96-name_w-1, 4), poke_name, white, font=bold_font)

# Start drawing weather/date stats at y = 4
y_pos = 4
day_w = draw.textsize("{0}".format(today.strftime(date_format)), font=font)[0]
draw.text((105, y_pos), "{0}".format(today.strftime(date_format)), black, font=font)
# If it's a very auspicious day, draw a red star after today's date
if very_auspicious:
    draw.text((105+day_w, y_pos), "★", red, font=font)
y_pos += 11
draw.text((105, y_pos), "{text}: {temp}°{unit}".format(text=min_text, temp=min_temp, unit="C" if args.celsius else "F"), red, font=font)
y_pos += 11
draw.text((105, y_pos), "{text}: {temp}°{unit}".format(text=max_text, temp=max_temp, unit="C" if args.celsius else "F"), red, font=font)
y_pos += 11
draw.text((105, y_pos), "{0}: {1}%".format(pop_text, pop), red, font=font)

# Draw the weather icon 4 pixels away from the right of the screen
weather_w = draw.textsize(weather_icon, font=weather_font)[0]
draw.text((212-weather_w-5, 4), weather_icon, black, font=weather_font)

# Trick I saw somewhere: Create a new image just to hold our needed palette
pal_image = Image.new('P', (1, 1))
# Fill our 256 colors in the palette with: 1. black, 2. white, 3. red, then black until the end.
pal_image.putpalette((255, 255, 255, 0, 0, 0, 255, 0, 0) + (0,0,0)*253)
# Quantize the image we built down to 3 colors, using palette from the dummy image above
finalimage = base.convert("RGB").quantize(palette=pal_image)
# Save image because it's cool to see the previous days
finalimage.save("PokeInkDis-{0}-#{1}.png".format(today.strftime('%Y-%m-%d'), str(poke_num).zfill(3)))

# Finally, use the inkyphat library to draw the image we built to the screen
inkyphat.set_border(inkyphat.RED)
inkyphat.set_image(finalimage)
inkyphat.show()