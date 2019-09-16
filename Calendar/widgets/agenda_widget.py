from PIL import Image, ImageDraw, ImageFont, ImageOps
from pathlib import Path
from pytz import timezone
import arrow
from tools.text_writer import write_line, write_text, get_line_height


class AgendaWidget:
    def __init__(self, config, backend, resources_path=None):
        if resources_path is None:
            resources_path = Path(__file__).absolute().parents[1]
        self.width = config['general']['epd_width']
        self.height = config['general']['epd_height']
        self.height_actual = None
        self.resources_path = resources_path
        self.config = config
        self.backend = backend

    def render(self):
        scope = self.backend.Scope
        next_events = self.backend.get_events(scope.NEXT)
        app_style = self.config['general']['app_style']
        language = self.config['general']['language']
        tzinfo = timezone(str(self.config['general']['timezone']))
        event_style = self.config['AgendaWidget']['style'][app_style]['event']
        font = ImageFont.truetype(str(self.resources_path / event_style['font']), event_style['size'])
        line_height = get_line_height(font)

        index = 0
        text_offset = event_style['date_offset']
        allowed_events = self.height / line_height
        num_next_events = len(next_events)
        max_events = int(min(allowed_events, num_next_events))
        image = Image.new('RGB', (self.width, self.height), 'white')
        while index < max_events:
            event = next_events[index]
            readable_date = event.begin.to(tzinfo)
            date_dm = readable_date.format('DD MMM', locale=language)
            date = write_line(text_offset, line_height, date_dm, font, 'left')
            image.paste(date, (0, index * line_height))
            title = write_line(self.width - text_offset, line_height, event.name, font, 'left')
            image.paste(title, (text_offset, index * line_height))
            index += 1
        return image
