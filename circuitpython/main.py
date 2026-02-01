import digitalio
import json
import mdns
import os
import socketpool
import time
import usb_cdc
import usb_hid
import wifi

from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_httpserver import MIMETypes, Request, Response, Server, status

import pins
from dns_captive import DNSCaptiveServer


ap_ssid = os.getenv('AP_SSID', 'Clipboard Dongle')
ap_password = os.getenv('AP_PASSWORD', '0987654321')
name = os.getenv('NAME', 'Clipboard Dongle')
srv_hostname = os.getenv('SERVER_HOSTNAME', 'clipboard-dongle')
srv_port = int(os.getenv('SERVER_PORT', '5000'))

########################################################################################################################
led = digitalio.DigitalInOut(pins.led_g)
led.switch_to_output()

keyboard = Keyboard(usb_hid.devices)
layout = KeyboardLayoutUS(keyboard)

def load_replacements():
    with open('/replace.csv', 'r') as f:
        for line in f.readlines():
            if not line.strip():
                continue
            key, val = line.strip().split(' ')
            for c in val:
                assert ord(c) <= 127, 'Only ASCII replacements are supported'
            yield key, val

def save_replacements(replacements):
    time.sleep(0.5)
    with open('/replace.csv', 'w') as f:
        for k, v in replacements.items():
            f.write(f'{k} {v}\n')

########################################################################################################################
MIMETypes.configure(
    default_to="text/plain",
    keep_for=[".html", ".css", ".js", ".png"],
)
pool = socketpool.SocketPool(wifi.radio)
server = Server(pool, "/static", debug=True)  # type: ignore

mdns_server = mdns.Server(wifi.radio)
mdns_server.hostname = srv_hostname
mdns_server.advertise_service(service_type="_http", protocol="_tcp", port=srv_port)

dns_server = DNSCaptiveServer(pool, '192.168.4.1')
dns_server.start()

wifi.radio.start_ap(ssid=ap_ssid, password=ap_password)
while not wifi.radio.ipv4_address_ap:
    time.sleep(0.1)
dns_server.set_captive_address(str(wifi.radio.ipv4_address_ap))

########################################################################################################################
# Captive portal detection endpoints - redirect to main page to trigger portal popup
@server.route("/hotspot-detect.html", methods=["GET"])  # Apple iOS/macOS
@server.route("/library/test/success.html", methods=["GET"])  # Apple iOS
@server.route("/generate_204", methods=["GET"])  # Android
@server.route("/gen_204", methods=["GET"])  # Android
def captive_portal_detect(request: Request):
    return Response(
        request,
        "",
        status=status.TEMPORARY_REDIRECT_307,
        headers={"Location": f"http://{dns_server.ip_address}/"}
    )

########################################################################################################################
@server.route("/submit", methods=["POST"])  # query param: ?method=serial or ?method=hid (default: hid)
def submit(request: Request):
    try:
        # Get method from query parameter: ?method=serial or ?method=hid (default: hid)
        method = request.query_params.get('method', 'hid')

        if method == 'hid':
            text = request.body.decode('utf-8')
            print(f'Submitted: "{text[:64]}..."')

            for char in text:
                if ord(char) > 127:
                    return Response(request, "Non-ASCII character: " + char, content_type="text/plain", status=status.BAD_REQUEST_400)

            led.value = True
            layout.write(text)
            led.value = False

        elif method == 'serial':
            if not (usb_cdc.data and usb_cdc.data.connected):
                return Response(request, "USB serial not connected. Is the host software running?", content_type="text/plain", status=status.INTERNAL_SERVER_ERROR_500)

            led.value = True
            usb_cdc.data.write(b'<<<BEGIN>>>\n')
            usb_cdc.data.write(f'{len(request.body)}\n'.encode())
            usb_cdc.data.write(request.body)
            usb_cdc.data.write(b'<<<END>>>\n')
            usb_cdc.data.flush()
            led.value = False
            print(f"Sent {len(request.body)} bytes via serial")
        else:
            return Response(request, f'Unknown method: {method}', content_type="text/plain", status=status.BAD_REQUEST_400)

        return Response(request, "OK", content_type="text/plain")

    except Exception as e:
        print(f"Error processing request: {e}")
        return Response(request, str(e), content_type="text/plain", status=status.INTERNAL_SERVER_ERROR_500)


@server.route("/replacements", methods=["GET"])
def get_replacements(request: Request):
    try:
        replacements = dict(load_replacements())
        return Response(request, json.dumps(replacements), content_type="application/json")

    except Exception as e:
        print(f"Error processing request: {e}")
        return Response(request, str(e), content_type="text/plain", status=status.INTERNAL_SERVER_ERROR_500)


@server.route("/replacements", methods=["POST"])
def update_replacements(request: Request):
    try:
        replacements = json.loads(request.body.decode('utf-8'))
        for k, v in replacements.items():
            for c in v:
                if ord(c) > 127:
                    return Response(request, f'Non-ASCII character in replacement for "{k}": ' + c,
                                    content_type="text/plain", status=status.BAD_REQUEST_400)
        save_replacements(replacements)
        return Response(request, "OK", content_type="text/plain")

    except Exception as e:
        print(f"Error processing request: {e}")
        return Response(request, str(e), content_type="text/plain", status=status.INTERNAL_SERVER_ERROR_500)

########################################################################################################################
server.start(port=srv_port)

while True:
    server.poll()
    dns_server.process_request()
