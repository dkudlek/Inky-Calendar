try:
    import epdif as epdif
except:
    import fake_epdif as epdif
    print("fake interface is used. No EPD output")
import time
from PIL import Image

# Display resolution
EPD_WIDTH       = 640
EPD_HEIGHT      = 384

# EPD7IN5 commands
PANEL_SETTING                               = 0x00
POWER_SETTING                               = 0x01
POWER_OFF                                   = 0x02
POWER_OFF_SEQUENCE_SETTING                  = 0x03
POWER_ON                                    = 0x04
POWER_ON_MEASURE                            = 0x05
BOOSTER_SOFT_START                          = 0x06
DEEP_SLEEP                                  = 0x07
DATA_START_TRANSMISSION_1                   = 0x10
DATA_STOP                                   = 0x11
DISPLAY_REFRESH                             = 0x12
IMAGE_PROCESS                               = 0x13
LUT_FOR_VCOM                                = 0x20
LUT_BLUE                                    = 0x21
LUT_WHITE                                   = 0x22
LUT_GRAY_1                                  = 0x23
LUT_GRAY_2                                  = 0x24
LUT_RED_0                                   = 0x25
LUT_RED_1                                   = 0x26
LUT_RED_2                                   = 0x27
LUT_RED_3                                   = 0x28
LUT_XON                                     = 0x29
PLL_CONTROL                                 = 0x30
TEMPERATURE_SENSOR_COMMAND                  = 0x40
TEMPERATURE_CALIBRATION                     = 0x41
TEMPERATURE_SENSOR_WRITE                    = 0x42
TEMPERATURE_SENSOR_READ                     = 0x43
VCOM_AND_DATA_INTERVAL_SETTING              = 0x50
LOW_POWER_DETECTION                         = 0x51
TCON_SETTING                                = 0x60
TCON_RESOLUTION                             = 0x61
SPI_FLASH_CONTROL                           = 0x65
REVISION                                    = 0x70
GET_STATUS                                  = 0x71
AUTO_MEASUREMENT_VCOM                       = 0x80
READ_VCOM_VALUE                             = 0x81
VCM_DC_SETTING                              = 0x82

class EPD:
    def __init__(self, config):
        self.config = config['general']
        self.width = self.config['epd_height']
        self.height = self.config['epd_width']
        self.display_colours = str(self.config['display_colours'])


    def digital_write(self, pin, value):
        epdif.epd_digital_write(pin, value)


    def digital_read(self, pin):
        return epdif.epd_digital_read(pin)


    def delay_ms(self, delaytime):
        epdif.epd_delay_ms(delaytime)


    def init(self):
        if (epdif.epd_init() != 0):
            return -1
        self.reset()
        epdif.send_command(POWER_SETTING)
        epdif.send_data(0x37)
        epdif.send_data(0x00)
        epdif.send_command(PANEL_SETTING)
        epdif.send_data(0xCF)
        epdif.send_data(0x08)
        epdif.send_command(BOOSTER_SOFT_START)
        epdif.send_data(0xc7)
        epdif.send_data(0xcc)
        epdif.send_data(0x28)
        epdif.send_command(POWER_ON)
        self.wait_until_idle()
        epdif.send_command(PLL_CONTROL)
        epdif.send_data(0x3c)
        epdif.send_command(TEMPERATURE_CALIBRATION)
        epdif.send_data(0x00)
        epdif.send_command(VCOM_AND_DATA_INTERVAL_SETTING)
        epdif.send_data(0x77)
        epdif.send_command(TCON_SETTING)
        epdif.send_data(0x22)
        epdif.send_command(TCON_RESOLUTION)
        epdif.send_data(0x02)     #source 640
        epdif.send_data(0x80)
        epdif.send_data(0x01)     #gate 384
        epdif.send_data(0x80)
        epdif.send_command(VCM_DC_SETTING)
        epdif.send_data(0x1E)      #decide by LUT file
        epdif.send_command(0xe5)           #FLASH MODE
        epdif.send_data(0x03)


    def wait_until_idle(self):
        while(epdif.is_busy()):      # 0: busy, 1: idle
            self.delay_ms(100)


    def reset(self):
        epdif.reset_low()
        self.delay_ms(200)
        epdif.reset_high()
        self.delay_ms(200)

    def serialize(self, image):
        # serialize
        buffer = [0x00] * int(self.width * self.height / 2)
        pixels = list(image.getdata())
        byte = 0x00
        for idx, val in enumerate(pixels):
            # Set the bits for the column of pixels at the current position.
            nibble = None
            if val == 0:  # black
                nibble = 0x0
            elif val == 255:  # white
                nibble = 0x3
            else:  # red
                nibble = 0x4

            if idx % 2:
                byte |= (nibble << 4)
            else:
                byte |= nibble
                buffer[int((idx - 1) / 2)] = byte
                byte = 0x00
        return buffer

    def send_buffer(self, buffer):
        epdif.send_command(DATA_START_TRANSMISSION_1)
        for el in buffer:
            epdif.send_data(el)
        epdif.send_command(DISPLAY_REFRESH)
        self.delay_ms(100)
        self.wait_until_idle()

    def convert_image(self, image, display_mode='bw'):

        image_converted = None
        if display_mode is 'bwr':
            image_converted = image.convert('L', dither=None)
        else:  # default
            image_converted = image.convert('1')

        # sanity check
        imwidth, imheight = image_converted.size
        if imwidth != self.width or imheight != self.height:
            raise ValueError('Image must be same dimensions as display \
                ({0}x{1}).' .format(self.width, self.height))
        return image_converted

    def display_image(self, image):
        image_converted = self.convert_image(image, display_mode=self.display_colours)
        buffer = self.serialize(image_converted)
        self.send_buffer(buffer)

    def sleep(self):
        epdif.send_command(POWER_OFF)
        self.wait_until_idle()
        epdif.send_command(DEEP_SLEEP)
        epdif.send_data(0xa5)

    def calibration(self):
        """Function for Calibration"""
        print('_________Calibration for E-Paper started_________'+'\n')
        black_img = Image.new('RGB', (self.width, self.height), "black")
        red_img = Image.new('RGB', (self.width, self.height), "red")
        white_img = Image.new('RGB', (self.width, self.height), "white")
        turns = 2
        for i in range(turns):
            self.init()
            print('Calibrating black...')
            self.display_image(black_img)
            if display_colours == "bwr":
                print('calibrating red...')
                self.display_image(red_img)
            print('Calibrating white...')
            self.display_image(white_img)
            self.sleep()
            print('Cycle {}/{} complete\n'.format(str(i+1), turns))
        print('Calibration complete')


if __name__ == '__main__':
    """Added timer"""
    start = time.time()
    epd = EPD()
    epd.calibration()
    end = time.time()
    print('Calibration complete in', int(end - start), 'seconds')
