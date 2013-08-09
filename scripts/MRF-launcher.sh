#!/bin/bash
. /usr/local/shellscripts/0.1.2/bin/functions
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
log_start
script -q -c "$DIR/MRF 2>'$stderr_file_name'" --timing="$timing_file_name" "$stdio_file_name"
log_stop
