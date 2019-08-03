import spidev
import RPi.GPIO as GPIO
import time

# Pin definition
RST_PIN         = 17
DC_PIN          = 25
CS_PIN          = 8
BUSY_PIN        = 24

# SPI device, bus = 0, device = 0
SPI = spidev.SpiDev(0, 0)
#SPI.no_cs = True

def epd_digital_write(pin, value):
    GPIO.output(pin, value)

def epd_digital_read(pin):
    return GPIO.input(BUSY_PIN)

def epd_delay_ms(delaytime):
    time.sleep(delaytime / 1000.0)

def spi_transfer(data):
    SPI.writebytes(data)

def epd_init():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(RST_PIN, GPIO.OUT)
    GPIO.setup(DC_PIN, GPIO.OUT)
    GPIO.setup(CS_PIN, GPIO.OUT)
    GPIO.setup(BUSY_PIN, GPIO.IN)
    SPI.max_speed_hz = 2000000
    SPI.mode = 0b00
    return 0

def is_busy():
    val = epd_digital_read(BUSY_PIN)
    if val == 0:
        return True
    else:
        return False

def reset_low():
    epd_digital_write(RST_PIN, GPIO.LOW)

def reset_high():
    epd_digital_write(RST_PIN, GPIO.HIGH)

def send_command(command):
    epd_digital_write(DC_PIN, GPIO.LOW)
    # the parameter type is list but not int
    # so use [command] instead of command
    spi_transfer([command])

def send_data(data):
    epd_digital_write(DC_PIN, GPIO.HIGH)
    # the parameter type is list but not int
    # so use [data] instead of data
    spi_transfer([data])

def epd_exit():
    print("spi end")
    SPI.close()

    print("close 5V, Module enters 0 power consumption ...")
    GPIO.output(RST_PIN, 0)
    GPIO.output(DC_PIN, 0)

    GPIO.cleanup()
