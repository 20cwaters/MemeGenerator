#!/usr/bin/env bash
# exit on error
set -o errexit

# Install ImageMagick
apt-get update
apt-get install -y imagemagick

# Install Python dependencies
pip install -r requirements.txt 