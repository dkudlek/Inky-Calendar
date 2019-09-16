#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
E-Paper Software (main script) for the 3-colour and 2-Colour E-Paper display
A full and detailed breakdown for this code can be found in the wiki.
If you have any questions, feel free to open an issue at Github.

Copyright by aceisace
"""
import calendar
from datetime import datetime, date, timedelta
from time import sleep
from dateutil.rrule import *
from dateutil.parser import parse
import arrow
import re
import random
import gc
import feedparser
import numpy as np
from pytz import timezone
from tzlocal import get_localzone
import socket

from settings import *
import yaml
from image_data import *

from PIL import Image, ImageDraw, ImageFont, ImageOps
import pyowm
from ics import Calendar

import e_paper_drivers
from backends import calendar_backend
from widgets import calendar_widget, agenda_widget, timestamp_widget, weather_widget, spacer_widget


epd = e_paper_drivers.EPD()



EPD_WIDTH = 640
EPD_HEIGHT = 384


im_open = Image.open

'''Get system timezone and set timezone accordingly'''
system_tz = get_localzone()
local_tz = timezone(str(system_tz))

print('Initialising weather')
owm = pyowm.OWM(api_key, language=language)

"""Main loop starts from here"""
def main():
    calibration_countdown = 'initial'
    while True:
        time = datetime.now().replace(tzinfo=local_tz)
        print(time)
        hour = int(time.strftime("%H"))
        month = int(time.now().strftime('%m'))
        year = int(time.now().strftime('%Y'))
        mins = int(time.strftime("%M"))
        seconds = int(time.strftime("%S"))
        now = arrow.now(tz=system_tz)

        config = None

        settings_path = Path(__file__).absolute().parents[0] / "settings.yaml"
        with open(str(settings_path), 'r') as stream:
            try:
                config = yaml.safe_load(stream)
                #print(config)
            except yaml.YAMLError as exc:
                print(exc)
        langage = config['general']['language']
        for i in range(1):
            ics_cal = calendar_backend.CalendarBackend(config)
            ics_cal.update()
            print('_________Starting new loop___________'+'\n')

            """Start by printing the date and time for easier debugging"""
            print('Date:', time.strftime('%a %d %b %y'), 'Time: '+time.strftime('%H:%M')+'\n')

            """At the hours specified in the settings file,
            calibrate the display to prevent ghosting"""
            if hour in calibration_hours:
                if calibration_countdown is 'initial':
                    calibration_countdown = 0
                    epd.calibration()
                else:
                    if calibration_countdown % (60 // int(update_interval)) is 0:
                        epd.calibration()
                        calibration_countdown = 0

            """Create a blank white page first"""
            image = Image.new('RGB', (EPD_HEIGHT, EPD_WIDTH), 'white')


            scope = calendar_backend.CalendarBackend.Scope
            upcoming = ics_cal.get_events(scope.NEXT)
            this_month = ics_cal.get_events(scope.THIS_MONTH)

            # WeatherWidget
            idx = 0
            my_weather = weather_widget.WeatherWidget(config).render()
            image.paste(my_weather, (0, idx))
            idx += my_weather.size[1]  # separator place

            # Separator
            my_spacer = spacer_widget.SpacerWidget(config).render()
            image.paste(my_spacer, (0, idx))
            idx += my_spacer.size[1]
            # CalendarWidget
            widget = calendar_widget.CalendarWidget(config, ics_cal)
            my_calendar = widget.render()
            image.paste(my_calendar, (0, idx))
            idx += my_calendar.size[1]
            # AgendaWidget
            agenda = agenda_widget.AgendaWidget(config, ics_cal)
            agenda.height = 130
            my_agenda = agenda.render()
            image.paste(my_agenda, (0, idx))
            idx += my_agenda.size[1]
            # TimestampeWidget
            timestamp_wgt = timestamp_widget.TimestampWidget(config)
            my_timestamp = timestamp_wgt.render()
            image.paste(my_timestamp, (0, idx))




            """
            Map all pixels of the generated image to red, white and black
            so that the image can be displayed 'correctly' on the E-Paper
            """
            buffer = np.array(image)
            r,g,b = buffer[:,:,0], buffer[:,:,1], buffer[:,:,2]
            if display_colours is "bwr":
                buffer[np.logical_and(r > 245, g > 245)] = [255,255,255] #white
                buffer[np.logical_and(r > 245, g < 245)] = [255,0,0] #red
                buffer[np.logical_and(r != 255, r == g )] = [0,0,0] #black

            if display_colours is "bw":
                buffer[np.logical_and(r > 245, g > 245)] = [255,255,255] #white
                buffer[g < 255] = [0,0,0] #black

            improved_image = Image.fromarray(buffer).rotate(270, expand=True)
            print('Initialising E-Paper Display')
            epd.init()
            sleep(5)
            print('Converting image to data and sending it to the display')
            epd.display_image(improved_image)
            #epd.display_frame(epd.get_frame_buffer(improved_image))
            print('Data sent successfully')
            print('______Powering off the E-Paper until the next loop______'+'\n')
            epd.sleep()


            if calibration_countdown is 'initial':
                calibration_countdown = 0
            calibration_countdown += 1

            for i in range(1):
                timings = []
                updates_per_hour = 60//int(update_interval)

                for updates in range(updates_per_hour):
                    timings.append(60 - int(update_interval)*updates)

                for update_times in timings:
                    if update_times >= mins:
                        sleep_for_minutes = update_times - mins

                next_update_countdown = sleep_for_minutes*60 + (60-seconds)

                print(sleep_for_minutes,'Minutes and ', (60-seconds),'Seconds left until next loop')

                del timings
                sleep(next_update_countdown)

if __name__ == '__main__':
    main()
