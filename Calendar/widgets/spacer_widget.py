from PIL import Image, ImageDraw, ImageFont, ImageOps


class SpacerWidget:
    def __init__(self, config, resources_path=None):
        self.width = config['general']['epd_width']
        self.height = config['general']['epd_height']
        self.max_height = None
        self.height_actual = None
        self.config = config

    def is_dynamic(self):
        return False

    def render(self):
        image = Image.new('RGB', (self.width, 2), 'red')
        return image
