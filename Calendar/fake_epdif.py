import time

# Pin definition
RST_PIN         = 17
DC_PIN          = 25
CS_PIN          = 8
BUSY_PIN        = 24


def epd_digital_write(pin, value):
    print("epd_digital_write {} {}".format(pin, value))

def epd_digital_read(pin):
    print("epd_digital_read {}".format(pin))
    return 1

def epd_delay_ms(delaytime):
    time.sleep(delaytime / 1000.0)

def spi_transfer(data):
    print("spi_transfer {}".format(data))

def epd_init():
    print("epd_init")
    return 0

def is_busy():
    val = epd_digital_read(BUSY_PIN)
    print("is_busy {}".format(val))
    if val == 0:
        return True
    else:
        return False

def reset_low():
    print("reset_low")
    epd_digital_write(RST_PIN, 0)

def reset_high():
    print("reset_high")
    epd_digital_write(RST_PIN, 1)

def send_command(command):
    epd_digital_write(DC_PIN, 0)
    # the parameter type is list but not int
    # so use [command] instead of command
    print("send_command {}".format([command]))

def send_data(data):
    epd_digital_write(DC_PIN, 1)
    # the parameter type is list but not int
    # so use [data] instead of data
    print("send_data {}".format([hex(data)]))

def epd_exit():
    print("epd_exit")
