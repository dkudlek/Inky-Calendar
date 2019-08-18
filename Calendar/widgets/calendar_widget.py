from PIL import Image, ImageDraw, ImageFont, ImageOps
from pathlib import Path
import arrow
import calendar

EPD_HEIGHT = 384
EPD_WIDTH  = 640



language = 'de_DE'


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
    def __init__(self, resources_path=None):
        if resources_path is None:
            resources_path = Path(__file__).absolute().parents[1] / 'resources'

        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT
        self.heigh_actual = None
        self.resources_path = resources_path
        NotoSans = 'NotoSans/NotoSans-SemiCondensed'
        fpath = resources_path / 'fonts'
        self.font = ImageFont.truetype(str(fpath / (NotoSans + 'Light.ttf')), 18)

    def render(self, month_events=None):
        image = Image.new('RGB', (self.height, self.width), 'white')
        now = arrow.now()
        weekday_names_list = arrow.locales.get_locale(language).day_abbreviations[1:]

        week_starts_on = "Sunday"
        if week_starts_on is "Monday":
            calendar.setfirstweekday(calendar.MONDAY)
        elif week_starts_on is "Sunday":
            calendar.setfirstweekday(calendar.SUNDAY)
            weekday_names_list = weekday_names_list[-1:] + weekday_names_list[0:-1]

        cal = calendar.monthcalendar(now.year, now.month)
        opath = self.resources_path / 'other'
        weekday = Image.open(opath / 'weekday.png')
        row_ptr = 0

        """Events"""
        days = None
        if month_events is not None:
            days = [ev.begin.date().day for ev in month_events]

        """Add the icon with the current month's name"""
        headline_size = 60
        write_text(image, self.width, headline_size, now.format('MMMM',locale=language), (0, row_ptr), font=self.font)
        row_ptr += headline_size

        """Create a list containing the weekday abbrevations for the
        chosen language"""

        weekday_size = 28
        left_margin = 3
        cal_x = row_ptr
        cal_y = left_margin
        cal_y_offset = 54
        for idx, name in enumerate(weekday_names_list):
            write_text(image, 54, weekday_size, name, (cal_y, cal_x), font=self.font)
            if name in now.format('ddd',locale=language):
                image.paste(weekday, (cal_y, cal_x), weekday)
            cal_y += cal_y_offset
        row_ptr += weekday_size

        """Create the calendar template of the current month"""
        dpath = self.resources_path / 'days'
        left_margin = 3
        cal_x = row_ptr
        cal_y = left_margin
        cal_x_offset = 63
        cal_y_offset = 54
        for row in cal:
            cal_y = left_margin
            for col in row:
                path = dpath / '{}.jpeg'.format(col)
                pos = (cal_y, cal_x)
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


                cal_y += cal_y_offset
            cal_x += cal_x_offset
        row_ptr = cal_x
        self.heigh_actual = row_ptr
        return image.crop((0,0, self.width, row_ptr))

if __name__ == "__main__":
    widget = CalendarWidget()
    widget.render().show()
