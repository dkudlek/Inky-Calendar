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
try:
    from urllib.request import urlopen
except Exception as e:
    print("Something didn't work right, maybe you're offline?"+e.reason)

import e_paper_drivers
from backends import calendar_backend
from widgets import calendar_widget, agenda_widget, timestamp_widget
epd = e_paper_drivers.EPD()



EPD_WIDTH = 640
EPD_HEIGHT = 384

if language in ['ja','zh','zh_tw','ko']:
    default = ImageFont.truetype(str(fpath / (NotoSansCJK + 'Light.otf')), 18)
    semi = ImageFont.truetype(str(fpath / (NotoSansCJK + 'DemiLight.otf')), 18)
    bold = ImageFont.truetype(str(fpath / (NotoSansCJK + 'Regular.otf')), 18)
    month_font = ImageFont.truetype(str(fpath / (NotoSansCJK + 'DemiLight.otf')), 40)
else:
    default = ImageFont.truetype(str(fpath / (NotoSans + 'Light.ttf')), 18)
    semi = ImageFont.truetype(str(fpath / (NotoSans + '.ttf')), 18)
    bold = ImageFont.truetype(str(fpath / (NotoSans + 'Medium.ttf')), 18)
    month_font = ImageFont.truetype(str(fpath / (NotoSans + 'Light.ttf')), 40)

w_font_l = ImageFont.truetype(str(fpath / weather_font), 60)
w_font_s = ImageFont.truetype(str(fpath / weather_font), 22)

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

            """Custom function to display text on the E-Paper"""
            def write_text(box_width, box_height, text, tuple, font=default, alignment='middle'):
                text_width, text_height = font.getsize(text)
                while (text_width, text_height) > (box_width, box_height):
                    text=text[0:-1]
                    text_width, text_height = font.getsize(text)
                if alignment is "" or "middle" or None:
                    x = int((box_width / 2) - (text_width / 2))
                if alignment is 'left':
                    x = 0
                y = int((box_height / 2) - (text_height / 1.7))
                space = Image.new('RGB', (box_width, box_height), color='white')
                ImageDraw.Draw(space).text((x, y), text, fill='black', font=font)
                image.paste(space, tuple)

            def internet_available(host="8.8.8.8", port=53, timeout=3):
                """
                Parameters:
                -----------
                Host: 8.8.8.8 (google-public-dns-a.google.com)
                OpenPort: 53/tcp
                Service: domain (DNS/TCP)

                Credits:
                -----------
                https://stackoverflow.com/a/33117579
                """
                try:
                    socket.setdefaulttimeout(timeout)
                    socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
                    return True
                except socket.error as ex:
                    print(ex)
                    return False


            """Connect to Openweathermap API and fetch weather data"""
            if top_section is "Weather" and api_key != "" and owm.is_API_online() is True:
                try:
                    print("Connecting to Openweathermap API servers...")
                    observation = owm.weather_at_place(location)
                    print("weather data:")
                    weather = observation.get_weather()
                    weathericon = weather.get_weather_icon_name()
                    Humidity = str(weather.get_humidity())
                    cloudstatus = str(weather.get_clouds())
                    weather_description = (str(weather.get_detailed_status()))

                    if units is "metric":
                        Temperature = str(int(weather.get_temperature(unit='celsius')['temp']))
                        windspeed = str(int(weather.get_wind()['speed']))
                        write_text(50, 35, Temperature + " °C", (334, 0))
                        write_text(100, 35, windspeed+" km/h", (114, 0))

                    if units is "imperial":
                        Temperature = str(int(weather.get_temperature('fahrenheit')['temp']))
                        windspeed = str(int(weather.get_wind()['speed']*0.621))
                        write_text(50, 35, Temperature + " °F", (334, 0))
                        write_text(100, 35, windspeed+" mph", (114, 0))

                    sunrisetime = arrow.get(weather.get_sunrise_time()).to(system_tz)
                    sunsettime = arrow.get(weather.get_sunset_time()).to(system_tz)

                    """Show the fetched weather data"""
                    print('Temperature:',Temperature, '°C')
                    print('Humidity:', Humidity, '%')
                    print('Wind speed:', windspeed, 'km/h')
                    print('Sunrise-time:', sunrisetime.format('HH:mm'))
                    print('Sunset time:', sunsettime.format('HH:mm'))
                    print('Cloudiness:', cloudstatus, '%')
                    print('Weather description:', weather_description, '\n')

                    """Add the weather icon at the top left corner"""
                    write_text(70,70, weathericons[weathericon], wiconplace, font = w_font_l)

                    """Add the temperature icon at it's position"""
                    write_text(35,35, '\uf055', tempplace, font = w_font_s)

                    """Add the humidity icon and display the humidity"""
                    write_text(35,35, '\uf07a', humplace, font = w_font_s)
                    write_text(50, 35, Humidity + " %", (334, 35))

                    """Add the sunrise/sunset icon and display the time"""
                    if (now <= sunrisetime and now <= sunsettime) or (now >= sunrisetime and now >= sunsettime):
                        write_text(35,35, '\uf051', sunriseplace, font = w_font_s)
                        print('sunrise coming next')
                        if hours is "24":
                            write_text(50, 35, sunrisetime.format('H:mm'), (249, 0))
                        if hours is "12":
                            write_text(50, 35, sunrisetime.format('h:mm'), (249, 0))

                    if now >= sunrisetime and now <= sunsettime:
                        write_text(35,35, '\uf052', sunriseplace, font = w_font_s)
                        print('sunset coming next')
                        if hours is "24":
                            write_text(50, 35, sunsettime.format('H:mm'), (249, 0))
                        if hours is "12":
                            write_text(50, 35, sunsettime.format('h:mm'), (249, 0))

                    """Add the wind icon at it's position"""
                    write_text(35,35, '\uf050', windiconspace, font = w_font_s)

                    """Add a short weather description"""
                    write_text(229, 35, weather_description, (70, 35))

                except Exception as e:
                    """If no response was received from the openweathermap
                    api server, add the cloud with question mark"""
                    print('__________OWM-ERROR!__________'+'\n')
                    print('Reason: ',e,'\n')
                    write_text(70,70, '\uf07b', wiconplace, font = w_font_l)
                    pass



            #image.show("Step2: This month calendar with today added")
            """Add rss-feeds at the bottom section of the Calendar"""
            if bottom_section is "RSS" and rss_feeds != []:

                """Custom function to display longer text into multiple lines (wrapping)"""
                def multiline_text(text, max_width, font=default):
                    lines = []
                    if font.getsize(text)[0] <= max_width:
                        lines.append(text)
                    else:
                        words = text.split(' ')
                        i = 0
                        while i < len(words):
                            line = ''
                            while i < len(words) and font.getsize(line + words[i])[0] <= max_width:
                                line = line + words[i] + " "
                                i += 1
                            if not line:
                                line = words[i]
                                i += 1
                            lines.append(line)
                    return lines

                """Parse the RSS-feed titles and save them to a list"""
                rss_feed = []
                for feeds in rss_feeds:
                    text = feedparser.parse(feeds)
                    for posts in text.entries:
                        rss_feed.append(posts.summary)#title

                """Shuffle the list to prevent displaying the same titles over and over"""
                random.shuffle(rss_feed)
                news = []

                """Remove all titles except the first 4 or 6,
                depenfing on how much space is available on the """
                if middle_section is 'Calendar' and len(cal) is 5 or middle_section is 'Agenda':
                    del rss_feed[6:]

                if len(cal) is 6:
                    del rss_feed[4:]

                """Split titles of the rss feeds into lines that can fit
                on the Calendar and add them to a list"""
                for title in range(len(rss_feeds)):
                    news.append(multiline_text(rss_feed[title], 384))

                news = [j for i in news for j in i]

                """Display the split lines of the titles"""
                if middle_section is 'Calendar' and len(cal) is 5 or middle_section is 'Agenda':
                    if len(news) > 6:
                        del news[6:]
                    for lines in range(len(news)):
                        write_text(384, 25, news[lines], rss_places['line_'+str(lines+1)], alignment = 'left')

                if len(cal) is 6:
                    if len(news) > 4:
                        del news[4:]
                    for lines in range(len(news)):
                        write_text(384, 25, news[lines], rss_places['line_'+str(lines+3)], alignment = 'left')

            #image.show("Step3")
            if middle_section is "Calendar" or "Agenda":
                scope = calendar_backend.CalendarBackend.Scope
                upcoming = ics_cal.get_events(scope.NEXT)
                this_month = ics_cal.get_events(scope.THIS_MONTH)

                idx = 72  # separator place
                h = seperator.size[1]
                image.paste(seperator, (0, idx))

                idx += h
                widget = calendar_widget.CalendarWidget(config)
                my_calendar = widget.render(this_month)
                h = my_calendar.size[1]
                image.paste(widget.render(this_month), (0, idx))

                idx += h
                agenda = agenda_widget.AgendaWidget(config)
                agenda.height = 130
                my_agenda = agenda.render(upcoming)
                h = my_agenda.size[1]
                image.paste(my_agenda, (0, idx))

                idx += h
                timestamp_wgt = timestamp_widget.TimestampWidget(config)
                my_timestamp = timestamp_wgt.render()
                image.paste(my_timestamp, (0, idx))
#                image.show("Step4")



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
