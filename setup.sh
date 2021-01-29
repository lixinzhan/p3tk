#!/bin/bash
#
# This script should be run on the folder it is sitting in.

export PWD=`pwd`
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

export PYTHONPATH=$PWD

