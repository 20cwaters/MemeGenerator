#!/usr/bin/env bash
# exit on error
set -o errexit

# Install system dependencies using apt-get with sudo
sudo apt-get update
sudo apt-get install -y imagemagick

# Install Python dependencies
pip install -r requirements.txt 