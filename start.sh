#!/usr/bin/env bash

nohup python3 -u app.py > subscriber.log 2>&1 & echo $! > subscriber.pid
