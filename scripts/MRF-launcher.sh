#!/bin/bash
. /usr/local/shellscripts/0.1.1/bin/functions
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
log_start
exit
script -c "$DIR/MRF 2>'$stderr_file_name'" -t 2>"$timing_file_name" "$stdio_file_name"
log_stop
