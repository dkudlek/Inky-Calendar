from PIL import Image, ImageDraw, ImageFont, ImageOps
from pathlib import Path
import arrow
import calendar

def write_text(image, box_width, box_height, text, tuple, font, alignment='middle'):
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

class CalendarWidget:
    def __init__(self, config, resources_path=None):
        if resources_path is None:
            resources_path = Path(__file__).absolute().parents[1] / 'resources'
        self.width = config['general']['epd_width']
        self.height = config['general']['epd_height']
        self.height_actual = None
        self.resources_path = resources_path
        self.config = config

    def render(self, month_events=None):
        app_style = self.config['general']['app_style']
        language = self.config['general']['language']
        week_starts_on = self.config['CalenderWidget']['week_start']
        show_weekday_indicator = self.config['CalenderWidget']['show_weekday_indicator']

        weekday_names_list = arrow.locales.get_locale(language).day_abbreviations[1:]
        if week_starts_on == "Monday":
            calendar.setfirstweekday(calendar.MONDAY)
        elif week_starts_on == "Sunday":
            calendar.setfirstweekday(calendar.SUNDAY)
            weekday_names_list = weekday_names_list[-1:] + weekday_names_list[0:-1]

        now = arrow.now()

        fpath = self.resources_path / 'fonts'
        month_style = self.config['CalenderWidget'][app_style]['month']
        month_font = ImageFont.truetype(str(fpath / (month_style['font'])), month_style['size'])
        month_size = month_style['size'] + 2 * month_style['margin']
        weekday_style = self.config['CalenderWidget'][app_style]['weekday']
        weekday_font = ImageFont.truetype(str(fpath / (weekday_style['font'])), weekday_style['size'])
        weekday_size = weekday_style['size'] + 2 * weekday_style['margin']

        """Events"""
        days = None
        if month_events is not None:
            days = [ev.begin.date().day for ev in month_events]

        row_ptr = 0
        image = Image.new('RGB', (self.width, self.height), 'white')
        """Add the icon with the current month's name"""
        write_text(image, self.width, month_size,
                   now.format('MMMM', locale=language), (0, row_ptr),
                   font=month_font)
        row_ptr += month_size

        cal = calendar.monthcalendar(now.year, now.month)
        weekday_left_margin = 2
        weekday_x = row_ptr
        weekday_y = weekday_left_margin
        weekday_y_offset = 54
        weekday = Image.open(self.resources_path / 'other' / 'weekday.png')
        for idx, name in enumerate(weekday_names_list):
            write_text(image, 54, weekday_size, name, (weekday_y, weekday_x), font=weekday_font)
            if name in now.format('ddd',locale=language) and show_weekday_indicator:
                image.paste(weekday, (weekday_y, weekday_x), weekday)
            weekday_y += weekday_y_offset
        row_ptr += weekday_size

        """Create the calendar template of the current month"""
        dpath = self.resources_path / 'days'
        left_margin = weekday_left_margin
        day_x = row_ptr
        day_y = left_margin
        day_x_offset = 63
        day_y_offset = 54
        for row in cal:
            day_y = left_margin
            for col in row:
                path = dpath / '{}.jpeg'.format(col)
                pos = (day_y, day_x)
                with Image.open(path) as number_img:
                    image.paste(number_img, pos)

                if now.day == col:
                    today_path = self.resources_path / 'other' / 'today.png'
                    with Image.open(today_path) as today_img:
                        image.paste(today_img, pos, today_img)
                if days is not None and col in days:
                    event_path = self.resources_path / 'other' / 'event.png'
                    with Image.open(event_path) as event_img:
                        image.paste(event_img, pos, event_img)


                day_y += day_y_offset
            day_x += day_x_offset
        row_ptr = day_x
        self.height_actual = row_ptr
        return image.crop((0, 0, self.width, self.height_actual))

if __name__ == "__main__":
    import yaml
    config = None
    with open("../settings.yaml", 'r') as stream:
        try:
            config = yaml.safe_load(stream)
            #print(config)
        except yaml.YAMLError as exc:
            print(exc)
    widget = CalendarWidget(config=config)
    widget.render().show()
