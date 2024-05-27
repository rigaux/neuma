#!/bin/bash
git restore *.log
git restore scorelib/local_settings.py
git pull
cp scorelib/humanum_local_settings.py scorelib/local_settings.py
