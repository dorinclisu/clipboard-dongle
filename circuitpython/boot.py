import digitalio
import storage
import time
import usb_cdc

import pins


update = digitalio.DigitalInOut(pins.update)
update.pull = digitalio.Pull.UP
time.sleep(0.01)
update_enabled = not update.value  # connected to GND

if update_enabled:
    led = digitalio.DigitalInOut(pins.led_g)
    led.switch_to_output(True)
    led.value = True  # turn on LED
    time.sleep(1)
else:
    storage.remount('/', readonly=False)
    storage.disable_usb_drive()
    usb_cdc.enable(console=False, data=True)  # disable console due to insufficient USB endpoints on ESP32-S3
