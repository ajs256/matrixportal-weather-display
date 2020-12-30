# ############## IMPORTS ###############

# BASICS (these are all built in)
import time         # The function to use the onboard RTC to give us time values
import board        # Pin definitions
import terminalio   # Provides the font we use
import busio        # Provides SPI for talking to the ESP32
import digitalio    # Provides pin I/O for the ESP32
import rtc          # Lets us keep track of the time 
import neopixel     # To drive the onboard NeoPixel.

# INTERNET
import adafruit_requests as requests  # For getting data from the Internet
from adafruit_esp32spi import adafruit_esp32spi  # For talking to the ESP32
import adafruit_esp32spi.adafruit_esp32spi_socket as socket  # For using the ESP32 for internet connections
from adafruit_io.adafruit_io import IO_HTTP  # For talking to Adafruit IO
from config import config  # The config file, see the README for what to put here

# DISPLAY
from adafruit_display_text import label  # For showing text on the display
import displayio  # Main display library
import framebufferio  # For showing things on the display
import rgbmatrix  # For talking to matrices specifically

# ############## DISPLAY SETUP ###############

# If there was a display before (protomatter, LCD, or E-paper), release it so
# we can create ours
displayio.release_displays()

# This next call creates the RGB Matrix object itself. It has the given width
# and height.
#
# These lines are for the Matrix Portal. If you're using a different board,
# check the guide to find the pins and wiring diagrams for your board.
# If you have a matrix with a different width or height, change that too.
matrix = rgbmatrix.RGBMatrix(
    width=64,
    height=32,
    bit_depth=3,
    rgb_pins=[
        board.MTX_R1,
        board.MTX_G1,
        board.MTX_B1,
        board.MTX_R2,
        board.MTX_G2,
        board.MTX_B2,
    ],
    addr_pins=[board.MTX_ADDRA, board.MTX_ADDRB, board.MTX_ADDRC, board.MTX_ADDRD],
    clock_pin=board.MTX_CLK,
    latch_pin=board.MTX_LAT,
    output_enable_pin=board.MTX_OE,
)

# Associate the RGB matrix with a Display so that we can use displayio features
display = framebufferio.FramebufferDisplay(matrix)

group = displayio.Group(max_size=5)  # Create a group to hold all our labels

font = terminalio.FONT  # We'll be using this font for all our labels, let's store it in a variable for later


# Text area 1: Time
text1 = "Loading"
color1 = 0x0000FF  # Blue

time_area = label.Label(font, text=text1, color=color1)

time_area.x = 0
time_area.y = 4

group.insert(0, time_area)  # Add it to the group


# Text area 2: Weather
text2 = "Loading......................"  # Pad it so it doesn't overflow
color2 = 0xFFA500  # Orange

weather_area = label.Label(font, text=text2, color=color2)

weather_area.x = 0
weather_area.y = 25
group.insert(1, weather_area)  # Add it to the group


# Text area 3: AQI
text3 = "Loading..."
color3 = 0xFFFFFF  # White, but it'll be changed

aqi_area = label.Label(font, text=text3, color=color3)

aqi_area.x = 0
aqi_area.y = 14

group.insert(2, aqi_area)


# Text area 4: Date
text4 = "....."
color4 = 0x00FFFF

date_area = label.Label(font, text=text4, color=color4)

date_area.x = 35
date_area.y = 4

group.insert(3, date_area)

# Text area 5: Day of week
text5 = "..."
color5 = 0x00FFFF

dow_area = label.Label(font, text=text5, color=color5)

dow_area.x = 46
dow_area.y = 14

group.insert(4, dow_area)


display.show(group)


# ############## TIME FORMATTING ###############
TIME_BETWEEN_RTC_SYNCS = 24 * 60 * 60  # 24 hours
TIME_BETWEEN_WEATHER_CHECKS = 10 * 60  # 10 min

next_rtc_sync = time.monotonic()
next_weather_check = time.monotonic()  # i.e. NOW!


time_display = None
date_display = None
dow = "..."


def time_format(current):
    global time_display
    global date_display

    hour = current.tm_hour % 12
    if hour == 0:
        hour = 12

    am_pm = "a"
    if current.tm_hour / 12 >= 1:
        am_pm = "p"

    time_display = "{:d}:{:02d}{}".format(hour, current.tm_min, am_pm)
    date_display = "{:d}/{:d}".format(current.tm_mon, current.tm_mday)


def get_day_of_week(date):
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    day_num = date.tm_wday
    return days[day_num]


# ############## AQI FORMATTING ###############


# The PurpleAir JSON endpoint.
PURPLEAIR_URL = "https://www.purpleair.com/json?show={id}".format(
    id=config["pa_sensor_id"]
)


"""
# Below functions come from the MatrixPortal PurpleAir Display guide from learn.adafruit.com. MIT Licensed.
"""


def aqi_transform(val):
    aqi = pm_to_aqi(val)  # derive Air Quality Index from Particulate Matter 2.5 value
    aqi


def aqi_to_list_index(aqi):
    aqi_groups = (301, 201, 151, 101, 51, 0)
    for index, group in enumerate(aqi_groups):
        if aqi >= group:
            return index
    return None


def calculate_aqi(Cp, Ih, Il, BPh, BPl):
    # wikipedia.org/wiki/Air_quality_index#Computing_the_AQI
    return round(((Ih - Il) / (BPh - BPl)) * (Cp - BPl) + Il)


def pm_to_aqi(pm):
    pm = float(pm)
    if pm < 0:
        return pm
    if pm > 1000:
        return 1000
    if pm > 350.5:
        return calculate_aqi(pm, 500, 401, 500, 350.5)
    elif pm > 250.5:
        return calculate_aqi(pm, 400, 301, 350.4, 250.5)
    elif pm > 150.5:
        return calculate_aqi(pm, 300, 201, 250.4, 150.5)
    elif pm > 55.5:
        return calculate_aqi(pm, 200, 151, 150.4, 55.5)
    elif pm > 35.5:
        return calculate_aqi(pm, 150, 101, 55.4, 35.5)
    elif pm > 12.1:
        return calculate_aqi(pm, 100, 51, 35.4, 12.1)
    elif pm >= 0:
        return calculate_aqi(pm, 50, 0, 12, 0)
    else:
        return None


def get_color(aqi):
    index = aqi_to_list_index(aqi)
    colors = (
        (106, 0, 27),  # Maroon
        (255, 0, 255),  # Purple
        (255, 0, 0),  # Red
        (255, 165, 0),  # Orange
        (255, 255, 0),  # Yellow
        (0, 255, 0),  # Green
    )
    if index is not None:
        return colors[index]
    return (150, 150, 150)  # White


# ############## WEATHER FORMATTING ###############

weather_display = "Loading..."

WEATHER_UNITS = config["units"]


OPENWEATHER_ENDPOINT = "https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&units={units}&appid={appid}&exclude=daily,minutely,alerts".format(
    lat=config["latitude"],
    lon=config["longitude"],
    units=WEATHER_UNITS,
    appid=config["openweather_token"],
)

# This gets from OpenWeatherMap's "one-call" API, passing in the settings from config.py using format().


# ############## NETWORK SETUP ###############

status_pixel = neopixel.NeoPixel(
    board.NEOPIXEL, 1, brightness=0.05, auto_write=True, pixel_order=neopixel.GRB
)  # Uses the onboard NeoPixel.
status_pixel.fill(0xFF0000)  # red because we aren't connected yet

# Here, we define the pins the ESP32 uses. This only works for boards with built-in ESP32s,
# such as the MatrixPortal and Metro M4 Airlift. Read the guide for your add-on to find which pins to use.
cs = digitalio.DigitalInOut(board.ESP_CS)
busy = digitalio.DigitalInOut(board.ESP_BUSY)
rst = digitalio.DigitalInOut(board.ESP_RESET)

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)  # Define the SPI object
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, cs, busy, rst)  # Start talking to the ESP32.
requests.set_socket(socket, esp)  # Tell the requests library to use the ESP32 connection.
io = IO_HTTP(config["aio_username"], config["aio_key"], requests)  # Start talking to Adafruit IO.


# Print info about the ESP32
if esp.status == adafruit_esp32spi.WL_IDLE_STATUS:
    print("ESP32 found and in idle mode")
print("Firmware vers.", esp.firmware_version)
print("MAC addr:", [hex(i) for i in esp.MAC_address])


# Connect to Wifi.
print("Connecting to Wifi...")
while not esp.is_connected:
    try:
        esp.connect_AP(config["ssid"], config["password"])
    except RuntimeError as e:
        print("could not connect, retrying: ", e)
        continue
print("Connected to", str(esp.ssid, "utf-8"), "\tRSSI:", esp.rssi)

# Do some tests to check that it works.
print("My IP address is", esp.pretty_ip(esp.ip_address))
print(
    "IP lookup adafruit.com: %s" % esp.pretty_ip(esp.get_host_by_name("adafruit.com"))
)
print("Ping google.com: %d ms" % esp.ping("google.com"))

status_pixel.fill(0x00FF00)  # we're connected, so make it green

# ############## MAIN LOOP ###############

# Define the AQI outside of the loop so it persists.
aqi = 0

while True:
    current_time = time.monotonic()
    if current_time > next_rtc_sync:
        status_pixel.fill(0x0000FF)  # blue while we're syncing the time
        print("Syncing time:")
        now = io.receive_time()  # grab time
        print("Got time")
        print(now)
        rtc.RTC().datetime = now  # set the time
        time_format(time.localtime())  # format the time
        print(time_display)  # Print it to serial, for debugging.
        print(date_display)
        dow = get_day_of_week(now)  # Calculate the day of the week.
        print("Day of week: " + dow)
        next_rtc_sync = (
            current_time + TIME_BETWEEN_RTC_SYNCS
        )  # Decide when to next sync the time.

    if current_time > next_weather_check:
        # Check weather and AQI.
        status_pixel.fill(0x00FFFF)  # cyan
        print("Getting AQI!")
        aq_response = requests.get(PURPLEAIR_URL)  # Grab data from PurpleAir.
        aqi = pm_to_aqi(aq_response.json()["results"][0]["PM2_5Value"])  # Calculate the AQI.
        print(aqi)

        del aq_response # Get rid of it because we no longer need it

        status_pixel.fill(0xFFA500)  # Orange
        print("Getting weather!")
        weather_response = requests.get(OPENWEATHER_ENDPOINT)  # Grab data from OpenWeather.
        weather_json = weather_response.json() # Parse the JSON.
        temp = weather_json["current"]["temp"]  # Pull the temperature out of the JSON.
        print("Temperature: " + str(temp))
        rain_chance = weather_json["hourly"][0]["pop"]  # Get the chance of rain today from the JSON.
        print("Rain chance: " + str(rain_chance))
        next_weather_check = current_time + TIME_BETWEEN_WEATHER_CHECKS
        weather_display = "{temp} F,{chance}%".format(
            temp=int(temp), chance=int(rain_chance * 100)  # Calculate what to display.
        )
        print("Displayed weather value:" + weather_display)
        
        del weather_response
        del weather_json

    time_format(time.localtime())  # format the time
    dow = get_day_of_week(time.localtime())  # Calculate the day of the week.
    status_pixel.fill(0x00FF00)  # Light up green when we're idle
    # Update the display...
    time_area.text = time_display
    weather_area.text = weather_display
    aqi_area.text = "AQI: " + str(aqi)
    aqi_area.color = get_color(aqi)
    date_area.text = date_display
    dow = get_day_of_week(time.localtime())
    dow_area.text = dow
