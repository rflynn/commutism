#!/bin/bash -ve

sudo apt-get install -y libyaml-dev

test -d venv || virtualenv venv
source venv/bin/activate
pip install \
    --allow-external python-graph-core \
    --allow-unverified python-graph-core \
    -r requirements.txt
