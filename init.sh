#!/bin/bash
apt-get update
apt-get install -y ffmpeg
/usr/local/bin/python -m pip install --upgrade pip
pip install -r /app/requirements.txt
cd /app
playwright install
playwright install-deps
clear
/usr/local/bin/python -u runner.py