# WARNING:
This does not work. It is a work in progress, and is only public so I can get feedback. If you'd like to open a pull request to fix the errors, great! If not, be prepared to have problems.

# Matrix Portal Weather Display

This project will turn your [Adafruit Matrix Portal](https://adafru.it/4812) into a display for the weather, air quality, and time/date!

## What You Need

* An [Adafruit Matrix Portal](https://adafru.it/4715)
    * You could use any CircuitPython-compatible dev board, as long as it has (or can add) WiFi and an LED matrix addon.
* An [LED matrix](https://adafru.it/2278). I used a 64x32 one, but you could adapt it to any size.
* A free [Adafruit IO](https://adafruit.io) account. We use it to set the time, but it could probably be adapted to use NTP.
* A free [OpenWeatherMap](https://openweathermap.org) account, to get the weather.

## How to set it up
This assumes that you have the Matrix Portal set up and have CircuitPython installed and working.

### Step 1: Get the code
You can either click **Code** above, and then **Download ZIP**, or use the [Github CLI](https://cli.github.com):
```sh
gh repo clone ajs256/matrixportal-weather-display
```

### Step 2: Add your Secrets
Rename [`config.py.example`](config.py.example) to `config.py`. Here's what you need to add:
```py
config = {
    'ssid' : 'YOUR_SSID', 
    'password' : 'SUPER_SECRET_WIFI_PASSWORD',
    # Change the above to your WiFi network name and password.
    'timezone' : "Etc/GMT", 
    # Check https://worldtimeapi.org/timezones to find your timezone
    'aio_username' : 'YOUR_NAME',
    'aio_key' : 'YOUR_HUGE_AIO_KEY',
    # Get a free Adafruit IO account to get a key.
    'openweather_token' : 'YOUR_BIG_OPENWEATHERMAP_KEY', 
    # Sign up at https://openweathermap.org for a free key.
    'latitude' : '40.748433',  
    'longitude' : '-73.985656',  
    # Find your latitude and longitude and put it here.
    # It should look something like the example above.
    'pa_sensor_id' : '58069' 
    # Head to https://purpleair.com/map and find a sensor near you.
    # You want the sensor ID, which comes after "select=" in the URL once you open a sensor.
    'units' : 'imperial'
    # Set your weather units.
    # "standard" = temp in Kelvin
    # "imperial" = temp in Farenheit
    # "metric" = temp in Celcius
}
```

### Step 3: Copy the Code
Copy `code.py` and `secrets.py` to your `CIRCUITPY` drive.

### Step 4: Get Libraries
Download the [latest library bundle](https://circuitpython.org/libraries). Copy these libraries over to the `lib` folder on your CIRCUITPY drive:

* `adafruit_requests`
* `neopixel`
* `adafruit_esp32spi`
* `adafruit_io`
* `adafruit_display_text`
* `rgbmatrix`

## :warning: NON-MATRIXPORTAL BOARD WARNING! :warning:
If you have a board that is not a Matrix Portal, the definitions for the ESP32 and matrix pins **WILL NOT WORK!** Here's what you need to change:

* If your board does not have a built-in ESP32, you will need to change lines 283-285 to point to the pins where you hooked up the corresponding pins on the ESP32.
* If your board is not a MatrixPortal, you will need to change lines 40-54 to refer to your matrix's pins. Check the guide for your addon to know which pins to use.

## Contributing!

I will accept issues and PRs! If you want to report/fix a bug, request/add a feature, or just need help, I will look over every issue or PR when I get a chance.
