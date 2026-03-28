#!/bin/bash

#turn on error exit, treat unset variables as errors, and pipefail (exit on error in pipes)    
set -euo pipefail

#cd to the directory of this script so it can be run from root
cd "$(dirname "$0")"

#run the uvicorn server
uvicorn controller:app --host 10.10.10.2 --port 8000
