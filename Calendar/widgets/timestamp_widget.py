from PIL import Image, ImageDraw, ImageFont, ImageOps
from pathlib import Path
from pytz import timezone
import arrow
from tools.text_writer import write_line, write_text, get_line_height


class TimestampWidget:
    def __init__(self, config, resources_path=None):
        if resources_path is None:
            resources_path = Path(__file__).absolute().parents[1]
        self.width = config['general']['epd_width']
        self.height = config['general']['epd_height']
        self.height_actual = None
        self.resources_path = resources_path
        self.config = config

    def is_dynamic(self):
        return False

    def render(self):
        app_style = self.config['general']['app_style']
        language = self.config['general']['language']
        tzinfo = timezone(str(self.config['general']['timezone']))
        time_now = arrow.now(tzinfo)
        config = self.config['TimezoneWidget']

        timestamp_style = config['style'][app_style]['timestamp']
        font = ImageFont.truetype(str(self.resources_path / timestamp_style['font']),
                                  timestamp_style['size'])
        line_height = get_line_height(font)
        self.height = line_height
        image = Image.new('RGB', (self.width, line_height), 'white')
        mode = config['mode']
        time_style = self.config['general']['time_style']
        text_string = config['strings'][language][mode]['image_created']
        time_stamp_image = None
        if mode == 'short':
            if time_style == 24:
                print('hello world')
                time_stamp_image = write_text(self.width, line_height, text_string.format(time_now.format('H:mm', locale=language)), font)
            else:
                time_stamp_image = write_text(self.width, line_height, text_string.format(time_now.format('h:mm a', locale=language)), font)
        else:
            if time_style == 24:
                time_stamp_image = write_text(self.width, line_height, text_string.format(time_now.format('DD.MM', locale=language), time_now.format('H:mm', locale=language)), font)
            else:
                time_stamp_image = write_text(self.width, line_height, text_string.format(time_now.format('DD.MM', locale=language), time_now.format('h:mm a', locale=language)), font)
        image.paste(time_stamp_image, (0, 0))
        return image
