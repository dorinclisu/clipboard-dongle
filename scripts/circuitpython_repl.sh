#!/bin/bash
echo "Exit screen with Ctrl+A then K"
sleep 1
DEVICE=`ls /dev/cu.usbmodem*`
screen $DEVICE 115200
