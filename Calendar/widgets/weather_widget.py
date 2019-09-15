from PIL import Image, ImageDraw, ImageFont, ImageOps
import pyowm
from pathlib import Path
from pytz import timezone
import arrow
from tools.text_writer import write_line, write_text, get_line_height


weathericons = {
    '01d': '\uf00d', '02d': '\uf002', '03d': '\uf013',
    '04d': '\uf012', '09d': '\uf01a', '10d': '\uf019',
    '11d': '\uf01e', '13d': '\uf01b', '50d': '\uf014',
    '01n': '\uf02e', '02n': '\uf013', '03n': '\uf013',
    '04n': '\uf013', '09n': '\uf037', '10n': '\uf036',
    '11n': '\uf03b', '13n': '\uf038', '50n': '\uf023'
    }

class WeatherWidget:
    def __init__(self, config, resources_path=None):
        if resources_path is None:
            resources_path = Path(__file__).absolute().parents[1]
        self.width = config['general']['epd_width']
        self.height = config['general']['epd_height']
        self.height_actual = None
        self.resources_path = resources_path
        self.config = config

    def render(self):
        app_style = self.config['general']['app_style']
        language = self.config['general']['language']
        time_style = self.config['general']['time_style']
        tzinfo = timezone(str(self.config['general']['timezone']))
        config = self.config['WeatherWidget']
        api_key = config['api_key']
        units = config['units']
        location = config['location']

        weather_large = config['style'][app_style]['weather_large']
        weather_large_font = ImageFont.truetype(str(self.resources_path / weather_large['font']),
                                                weather_large['size'])
        weather_small = config['style'][app_style]['weather_small']
        weather_small_font = ImageFont.truetype(str(self.resources_path /
                                                weather_small['font']), weather_small['size'])
        weather_regular = config['style'][app_style]['weather_regular']
        weather_regular_font = ImageFont.truetype(str(self.resources_path / weather_regular['font']),
                                                weather_regular['size'])

#        line_height = get_line_height(font)
        owm = pyowm.OWM(api_key, language=language)
        temperature_pos = config['layout']['temperature_pos']
        windspeed_pos = config['layout']['windspeed_pos']

        image = Image.new('RGB', (self.width, self.height), 'white')
        try:
            #print("Connecting to Openweathermap API servers...")
            observation = owm.weather_at_place(location)
            weather = observation.get_weather()
            weathericon = weather.get_weather_icon_name()
            humidity = str(weather.get_humidity())
            cloudstatus = str(weather.get_clouds())
            weather_description = (str(weather.get_detailed_status()))

            temperature_image = None
            windspeed_text = None
            if units == "imperial":
                temperature = str(int(weather.get_temperature('fahrenheit')['temp']))
                windspeed = str(int(weather.get_wind()['speed']*0.621))
                temperature_image = write_line(50, 35, "{} °F".format(temperature), weather_regular_font)
                windspeed_text = write_line(100, 35, "{} mph".format(windspeed), weather_regular_font)
            else:
                temperature = str(int(weather.get_temperature(unit='celsius')['temp']))
                windspeed = str(int(weather.get_wind()['speed']))
                temperature_image = write_line(50, 35, "{} °C".format(temperature), weather_regular_font)
                windspeed_text = write_line(100, 35, "{} km/h".format(windspeed), weather_regular_font)

            now = arrow.now(tzinfo)
            sunrisetime = arrow.get(weather.get_sunrise_time()).to(tzinfo)
            sunsettime = arrow.get(weather.get_sunset_time()).to(tzinfo)

            rise_set_icon = None
            rise_set_time = None
            if (now <= sunrisetime and now <= sunsettime) or (now >= sunrisetime and now >= sunsettime):
                rise_set_icon = write_line(35,35, '\uf051', weather_small_font)
                print('sunrise coming next')
                if str(time_style):
                    rise_set_time = write_line(50, 35, sunrisetime.format('H:mm'), weather_regular_font)
                else:
                    rise_set_time = write_line(50, 35, sunrisetime.format('h:mm'), weather_regular_font)

            if now >= sunrisetime and now <= sunsettime:
                rise_set_icon = write_line(35,35, '\uf052', weather_small_font)
                print('sunset coming next')
                if str(time_style) == "24":
                    rise_set_time = write_line(50, 35, sunsettime.format('HH:mm'), weather_regular_font)
                else:
                    rise_set_time = write_line(50, 35, sunsettime.format('h:mm'), weather_regular_font)

            """Add the weather icon at the top left corner"""
            icon_image = write_line(70,70, weathericons[weathericon], weather_large_font)
            image.paste(icon_image, (0, 0))
            """Add the wind icon at it's position"""
            wind_icon = write_line(35,35, '\uf050', weather_small_font)
            image.paste(wind_icon, (79, 0))
            image.paste(windspeed_text, (windspeed_pos, 0))

            """Add the sunrise/sunset icon and display the time"""
            image.paste(rise_set_icon, (214, 0))
            image.paste(rise_set_time, (249, 0))

            """Add the temperature icon at it's position"""
            temp_icon = write_line(35,35, '\uf055', weather_small_font)
            image.paste(temp_icon, (299, 0))
            image.paste(temperature_image, (temperature_pos, 0))


            """Add the humidity icon and display the humidity"""
            hum_icon = write_line(35,35, '\uf07a', weather_small_font)
            image.paste(hum_icon, (299, 35))
            hum_text = write_line(50, 35, "{} %".format(humidity), weather_regular_font)
            image.paste(hum_text, (334, 35))

            """Add a short weather description"""
            desc = write_text(229, 35, weather_description, weather_regular_font)
            image.paste(desc, (70, 35))

        except Exception as e:
            """If no response was received from the openweathermap
            api server, add the cloud with question mark"""
            print('__________OWM-ERROR!__________'+'\n')
            print('Reason: ',e,'\n')
            no_connection_image = write_line(70,70, '\uf07b', weather_large_font)
            image.paste(no_connection_image, (0, 0))
        return image.crop((0, 0, self.width, 70))
