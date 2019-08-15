#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Calibration module for the Black-White and Black-White-Red E-Paper display
Calibration refers to flushing all pixels in a single colour to prevent
ghosting.
"""

from __future__ import print_function
import time
from settings import display_colours
from PIL import Image

def calibration():
    """Function for Calibration"""
    import e_paper_drivers
    epd = e_paper_drivers.EPD()
    print('_________Calibration for E-Paper started_________'+'\n')
    black_img = Image.new('RGB', (epd.width, epd.height), "black")
    red_img = Image.new('RGB', (epd.width, epd.height), "red")
    white_img = Image.new('RGB', (epd.width, epd.height), "white")
    for i in range(2):
        epd.init()
        print('Calibrating black...')
        epd.display_image(black_img)
        if display_colours == "bwr":
            print('calibrating red...')
            epd.display_image(red_img)
        print('Calibrating white...')
        epd.display_image(white_img)
        epd.sleep()
        print('Cycle', str(i+1)+'/2', 'complete'+'\n')
    print('Calibration complete')

def main():
    """Added timer"""
    start = time.time()
    calibration()
    end = time.time()
    print('Calibration complete in', int(end - start), 'seconds')

if __name__ == '__main__':
    main()
