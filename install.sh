#!/bin/bash -ve

sudo apt-get install -y libyaml-dev

test -d venv || virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
