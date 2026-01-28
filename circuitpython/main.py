import json
import mdns
import os
import socketpool
import usb_hid
import wifi

from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_httpserver import MIMETypes, Request, Response, Server, status



ap_ssid = os.getenv('AP_SSID', 'Clipboard Dongle')
ap_password = os.getenv('AP_PASSWORD', '0987654321')
name = os.getenv('NAME', 'Clipboard Dongle')
srv_hostname = os.getenv('SERVER_HOSTNAME', 'clipboard-dongle')
srv_port = int(os.getenv('SERVER_PORT', '5000'))

########################################################################################################################
keyboard = Keyboard(usb_hid.devices)
keyboard_layout = KeyboardLayoutUS(keyboard)

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
    with open('/replace.csv', 'w') as f:
        for k, v in replacements.items():
            f.write(f'{k} {v}\n')

char_replacements = dict(load_replacements())

########################################################################################################################
with open('main.html', 'r') as f:
    html_template = f.read()
html_content = html_template.replace('{NAME}', name)

MIMETypes.configure(
    default_to="text/plain",
    keep_for=[".html", ".css", ".js", ".png"],
)
pool = socketpool.SocketPool(wifi.radio)
server = Server(pool, "/static", debug=True)  # type: ignore

mdns_server = mdns.Server(wifi.radio)
mdns_server.hostname = srv_hostname
mdns_server.advertise_service(service_type="_http", protocol="_tcp", port=srv_port)

wifi.radio.start_ap(ssid=ap_ssid, password=ap_password)

########################################################################################################################
@server.route("/")
def root(request: Request):
    return Response(request, html_content, content_type="text/html")


@server.route("/submit", methods=["POST"])
def submit(request: Request):
    try:
        text = request.body.decode('utf-8')
        print(f'Submitted: "{text[:64]}..."')

        to_replace = set()
        for char in text:
            if char in char_replacements:
                to_replace.add(char)
            elif ord(char) > 127:
                return Response(request, "Non-ASCII character: " + char, content_type="text/plain", status=status.BAD_REQUEST_400)

        for char in to_replace:
            text = text.replace(char, char_replacements[char])

        keyboard_layout.write(text)
        return Response(request, "OK", content_type="text/plain")

    except Exception as e:
        print(f"Error processing request: {e}")
        return Response(request, "Error", content_type="text/plain", status=status.INTERNAL_SERVER_ERROR_500)

########################################################################################################################
server.serve_forever(port=srv_port)
