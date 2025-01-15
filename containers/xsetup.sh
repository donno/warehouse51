#!/bin/sh
# Set up a X-server and VNC
# The display server will be DISPLAY=:1
Xvfb :1 -screen 0 1024x768x24 > /root/xvfb.stdout.log 2> /root/xvfb.stderr.log & 
x11vnc -display :1 > /root/x11vnc.stdout.log 2> /root/x11vnc.stderr.log &

# TODO: Setup xrdp
