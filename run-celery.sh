#!/bin/bash

Xvfb :10 -ac &
exec celery -A subscriber worker --loglevel=INFO -c 1 -Q main
