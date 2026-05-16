import os

PRINTER_DEV = os.getenv('PRINTER_DEV', '/dev/usb/lp0')
DPI = 203


def mm_to_dots(mm) -> int:
    return int(float(mm) * DPI / 25.4)


LABEL_WIDTH_PX  = mm_to_dots(os.getenv('LABEL_WIDTH_MM',  '40'))
LABEL_HEIGHT_PX = mm_to_dots(os.getenv('LABEL_HEIGHT_MM', '57'))
LABEL_GAP_DOTS  = int(os.getenv('LABEL_GAP_DOTS', '26'))
