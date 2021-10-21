#!/bin/bash

Xvfb :10 -ac &
exec python app.py
