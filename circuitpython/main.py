import mdns
import os
import socketpool
import usb_hid
import wifi
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_httpserver import MIMETypes, Request, Response, Server, status

import pages


name = os.getenv('NAME', 'Clipboard Dongle')
hostname = os.getenv('SERVER_HOSTNAME', 'clipboard-dongle')
port = int(os.getenv('SERVER_PORT', '5000'))

wifi.radio.start_ap(ssid=os.getenv('AP_SSID'), password=os.getenv('AP_PASSWORD'))

MIMETypes.configure(
    default_to="text/plain",
    # Unregistering unnecessary MIME types can save memory
    keep_for=[".html", ".css", ".js", ".png"],
)
pool = socketpool.SocketPool(wifi.radio)
server = Server(pool, "/static", debug=True)  # type: ignore

mdns_server = mdns.Server(wifi.radio)
mdns_server.hostname = hostname
mdns_server.advertise_service(service_type="_http", protocol="_tcp", port=port)

keyboard = Keyboard(usb_hid.devices)
keyboard_layout = KeyboardLayoutUS(keyboard)

########################################################################################################################
@server.route("/")
def root(request: Request):
    return Response(request, pages.HTML.replace('{NAME}', name), content_type="text/html")


@server.route("/submit", methods=["POST"])
def submit(request: Request):
    try:
        text = request.body.decode('utf-8')
        print(f'Submitted: "{text}"')

        try:
            keyboard_layout.write(text)
        except ValueError as e:
            print(f"Keyboard error: {e}")
            return Response(request, str(e), content_type="text/plain", status=status.BAD_REQUEST_400)

        return Response(request, "OK", content_type="text/plain")

    except Exception as e:
        print(f"Error processing request: {e}")
        return Response(request, "Error", content_type="text/plain", status=status.INTERNAL_SERVER_ERROR_500)

########################################################################################################################
server.serve_forever(port=port)
