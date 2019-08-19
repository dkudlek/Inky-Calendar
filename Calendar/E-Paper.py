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

from settings import *
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
from widgets import calendar_widget
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
    ics_cal = calendar_backend.CalendarBackend(ical_urls)
    while True:
        ics_cal.update()
        time = datetime.now().replace(tzinfo=local_tz)
        print(time)
        hour = int(time.strftime("%H"))
        month = int(time.now().strftime('%m'))
        year = int(time.now().strftime('%Y'))
        mins = int(time.strftime("%M"))
        seconds = int(time.strftime("%S"))
        now = arrow.now(tz=system_tz)

        for i in range(1):
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

            """Check if internet is available by trying to reach google"""
            def internet_available():
                try:
                    urlopen('https://google.com',timeout=5)
                    return True
                except URLError as err:
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

            """Set the Calendar to start on the day specified by the settings file """
            if week_starts_on is "Monday":
                calendar.setfirstweekday(calendar.MONDAY)

            """For those whose week starts on Sunday, change accordingly"""
            if week_starts_on is "Sunday":
                calendar.setfirstweekday(calendar.SUNDAY)

            """Using the built-in calendar to generate the monthly Calendar
            template"""
            cal = calendar.monthcalendar(time.year, time.month)
            #image.show("Step1: Weather added")


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
                upcoming = ics_cal.get_events(calendar_backend.CalendarBackend.Scope.STARTING_TODAY_WITH_ACTIVE)
                this_month = ics_cal.get_events(calendar_backend.CalendarBackend.Scope.THIS_MONTH)

                image.paste(seperator, seperatorplace)

                widget = calendar_widget.CalendarWidget()
                image.paste(widget.render(this_month), monthplace)
                #image.show("Step4")
#                print(ics_cal.get_active_events())  # to be used for active agenda points
                events_this_month = [int((event.begin).format('D')) for event in this_month]
                if middle_section is 'Agenda':
                    """For the agenda view, create a list containing dates and events of the next 22 days"""
                    if len(upcoming) is not 0:
                        while (upcoming[-1].begin.date().day - now.day) + len(upcoming) >= 22:
                            del upcoming[-1]
                    agenda_list = []
                    for i in range(22):
                        date = now.replace(days=+i)
                        agenda_list.append({'value':date.format('ddd D MMM YY', locale=language),'type':'date'})
                        for events in upcoming:
                            if events.begin.date().day == date.day:
                                if not events.all_day:
                                    if hours is '24':
                                        agenda_list.append({'value':events.begin.to(system_tz).format('HH:mm')+ ' '+ str(events.name), 'type':'timed_event'})
                                    if hours is '12':
                                        agenda_list.append({'value':events.begin.to(system_tz).format('hh:mm a')+ ' '+ str(events.name), 'type':'timed_event'})
                                else:
                                    agenda_list.append({'value':events.name, 'type':'full_day_event'})

                    if bottom_section is not "":
                        del agenda_list[16:]
                        image.paste(seperator2, agenda_view_lines['line17'])

                    if bottom_section is "":
                        del agenda_list[22:]
                        image.paste(seperator2, agenda_view_lines['line22'])

                    for lines in range(len(agenda_list)):
                        if agenda_list[lines]['type'] is 'date':
                            write_text(384, 25, agenda_list[lines]['value'], agenda_view_lines['line'+str(lines+1)], font=semi, alignment='left')
                            image.paste(seperator2, agenda_view_lines['line'+str(lines+1)])
                        elif agenda_list[lines]['type'] is 'timed_event':
                            write_text(384, 25, agenda_list[lines]['value'], agenda_view_lines['line'+str(lines+1)], alignment='left')
                        else:
                            write_text(384, 25, agenda_list[lines]['value'], agenda_view_lines['line'+str(lines+1)])
            #image.show("Step5: Events added")
            """Write event dates and names on the E-Paper"""
            if bottom_section is "Events":
                if len(cal) is 5:
                    del upcoming[6:]
                    for dates in range(len(upcoming)):
                        readable_date = upcoming[dates].begin.format('D MMM', locale=language)
                        write_text(70, 25, readable_date, date_positions['d'+str(dates+1)])
                    for events in range(len(upcoming)):
                        write_text(314, 25, upcoming[events].name, event_positions['e'+str(events+1)], alignment = 'left')

                if len(cal) is 6:
                    del upcoming[4:]
                    for dates in range(len(upcoming)):
                        readable_date = upcoming[dates].begin.format('D MMM', locale=language)
                        write_text(70, 25, readable_date, date_positions['d'+str(dates+3)])
                    for events in range(len(upcoming)):
                        write_text(314, 25, upcoming[events].name, event_positions['e'+str(events+3)], alignment = 'left')
            #image.show("Step6: Agenda added")
            'Show the time of the last update if set in the settings file'
            if show_last_update_time is 'True':
                if hours is "24":
                    write_text(384, 25, 'Image created at '+now.format('H:mm'), (0, 615))
                if hours is "12":
                    write_text(384, 25, 'Image created at '+now.format('h:mm a'), (0, 615))
            #image.show("Step7: Time created added")

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

            if middle_section is 'Calendar':
                del events_this_month
                del upcoming
#                del weekday_names_list

            if bottom_section is 'RSS':
                del rss_feed
                del news

            if middle_section is 'Agenda':
                del agenda_list

            del buffer
            del image
            del improved_image
            gc.collect()

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
