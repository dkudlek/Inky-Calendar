from PIL import Image
from backends import calendar_backend
from widgets import calendar_widget, agenda_widget, timestamp_widget, weather_widget, spacer_widget

class BasePanel:
    def __init__(self, panel_config):
        self.panel_config = panel_config
        self.width = panel_config['general']['epd_width']
        self.height = panel_config['general']['epd_height']
        self.backends = []
        calendar_be = calendar_backend.CalendarBackend(panel_config)
        self.backends.append(calendar_be)
        self.widgets = []
        self.widgets.append(weather_widget.WeatherWidget(panel_config))
        self.widgets.append(spacer_widget.SpacerWidget(panel_config))
        self.widgets.append(calendar_widget.CalendarWidget(panel_config, calendar_be))
        self.widgets.append(agenda_widget.AgendaWidget(panel_config, calendar_be))
        self.widgets.append(timestamp_widget.TimestampWidget(panel_config))

    def update(self):
        for module in self.backends:
            module.update()

    def render(self):
        image = Image.new('RGB', (self.width, self.height), 'white')
        idx = 0
        # dry run
        for widget in self.widgets:
            rendered = widget.render()
            image.paste(rendered, (0, idx))
            idx += rendered.size[1]
        overflow = idx - self.height
        if overflow > 0:
            idx= 0
            for widget in self.widgets:
                if widget.is_dynamic():
                    widget.max_height -= overflow
                rendered = widget.render()
                image.paste(rendered, (0, idx))
                idx += rendered.size[1]

        return image
