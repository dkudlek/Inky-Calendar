from PIL import Image, ImageDraw, ImageFont, ImageOps
from pathlib import Path
import arrow
import calendar
from tools.text_writer import write_line, write_text


class CalendarWidget:
    def __init__(self, config, backend=None, resources_path=None):
        if resources_path is None:
            resources_path = Path(__file__).absolute().parents[1]
        self.width = config['general']['epd_width']
        self.height = config['general']['epd_height']
        self.max_height = None
        self.height_actual = None
        self.resources_path = resources_path
        self.config = config
        self.backend = backend

    def is_dynamic(self):
        return False

    def render(self):
        month_events = None
        if self.backend is not None:
            scope = self.backend.Scope
            month_events = self.backend.get_events(scope.THIS_MONTH)
        app_style = self.config['general']['app_style']
        language = self.config['general']['language']
        widget = self.config['CalenderWidget']
        week_starts_on = widget['week_start']
        show_weekday_indicator = widget['show_weekday_indicator']

        weekday_names_list = arrow.locales.get_locale(language).day_abbreviations[1:]
        if week_starts_on == "Monday":
            calendar.setfirstweekday(calendar.MONDAY)
        elif week_starts_on == "Sunday":
            calendar.setfirstweekday(calendar.SUNDAY)
            weekday_names_list = weekday_names_list[-1:] + weekday_names_list[0:-1]

        now = arrow.now()

        month_style = widget['style'][app_style]['month']
        month_font = ImageFont.truetype(str(self.resources_path  / (month_style['font'])), month_style['size'])
        month_size = month_style['size'] + 2 * month_style['margin']
        weekday_style = widget['style'][app_style]['weekday']
        weekday_font = ImageFont.truetype(str(self.resources_path  / (weekday_style['font'])), weekday_style['size'])
        weekday_size = weekday_style['size'] + 2 * weekday_style['margin']

        """Events"""
        days = None
        if month_events is not None:
            days = [ev.begin.date().day for ev in month_events]

        row_ptr = 0
        image = Image.new('RGB', (self.width, self.height), 'white')
        """Add the icon with the current month's name"""
        part = write_line(self.width, month_size,
                   now.format('MMMM', locale=language), font=month_font)
        image.paste(part, (0, row_ptr))
        row_ptr += month_size

        image_resource = widget["image_resource"]
        cal = calendar.monthcalendar(now.year, now.month)
        weekday_left_margin = 2
        weekday_x = row_ptr
        weekday_y = weekday_left_margin
        weekday_y_offset = 54
        weekday = Image.open(self.resources_path / image_resource["weekday_mask"])
        for idx, name in enumerate(weekday_names_list):
            part = write_line(54, weekday_size, name, font=weekday_font)
            image.paste(part,(weekday_y, weekday_x))
            if name in now.format('ddd',locale=language) and show_weekday_indicator:
                image.paste(weekday, (weekday_y, weekday_x), weekday)
            weekday_y += weekday_y_offset
        row_ptr += weekday_size

        """Create the calendar template of the current month"""
        dpath = self.resources_path / image_resource['day_icon_folder']
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
                    today_path = self.resources_path / image_resource["today_mask"]
                    with Image.open(today_path) as today_img:
                        image.paste(today_img, pos, today_img)
                if days is not None and col in days:
                    event_path = self.resources_path / image_resource["event_mask"]
                    with Image.open(event_path) as event_img:
                        image.paste(event_img, pos, event_img)


                day_y += day_y_offset
            day_x += day_x_offset
        row_ptr = day_x
        self.height_actual = row_ptr
        return image.crop((0, 0, self.width, self.height_actual))
