#!/bin/bash
# Start the batch so that the Mac neither sleeps nor idles the CPU.
# Usage: ./run.sh [--smoke | --blocks A,B ...]   (log goes to batch.log)
cd "$(dirname "$0")"
caffeinate -i -s -m .venv-g13/bin/python run.py "$@" 2>&1 | tee -a batch.log
