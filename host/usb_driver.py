#!/usr/bin/env python3
"""
Host driver for clipboard dongle serial communication.
Receives data over USB serial and copies it to the system clipboard.
Supports macOS, Windows, and Linux.
"""
import glob
import platform
import sys

import pyperclip
import serial
from serial import SerialException
from serial.tools import list_ports


BEGIN_MARKER = b'<<<BEGIN>>>'
END_MARKER = b'<<<END>>>'
BAUD_RATE = 115200
TIMEOUT = 1


def find_serial_port() -> str:
    """Find the USB modem serial port based on platform."""
    system = platform.system()

    if system == 'Darwin':  # macOS
        ports = glob.glob('/dev/tty.usbmodem*')
    elif system == 'Linux':
        ports = glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*')
    elif system == 'Windows':
        ports = [
            p.device for p in list_ports.comports()
            if 'USB' in p.description.upper() or 'MODEM' in p.description.upper()
        ]
    else:
        raise SerialException(f"Unsupported platform: {system}")

    if not ports:
        raise SerialException("No USB modem found. Is the device connected?")
    if len(ports) > 1:
        print(f"Multiple ports found: {ports}, using {ports[-1]}", file=sys.stderr)
    return ports[-1]


def receive_data(ser: serial.Serial) -> bytes | None:
    """
    Receive a length-prefixed message from the serial port.
    Returns the data bytes, or None if transfer failed.
    """
    try:
        length = int(ser.readline().strip())
    except ValueError:
        print("Warning: Invalid length header", file=sys.stderr)
        return None

    data = ser.read(length)
    if len(data) < length:
        print(f"Warning: Expected {length} bytes, got {len(data)}", file=sys.stderr)
        return None

    end_line = ser.readline()
    if end_line.strip() != END_MARKER:
        print(f"Warning: Expected {END_MARKER}, got {end_line.strip()}", file=sys.stderr)
        return None

    return data


def main() -> None:
    port = find_serial_port()
    print(f"Listening on {port}...")

    with serial.Serial(port, BAUD_RATE, timeout=TIMEOUT) as ser:
        while True:
            line = ser.readline()
            if line.strip() == BEGIN_MARKER:
                data = receive_data(ser)
                if data is not None:
                    pyperclip.copy(data.decode('utf-8'))
                    print(f"Copied {len(data)} bytes to clipboard")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
    except SerialException as e:
        print(f"Serial error: {e}", file=sys.stderr)
        sys.exit(1)
