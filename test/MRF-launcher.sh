#!/bin/bash

# cvl_emap shell functions
. /usr/local/share/cvl_emap_functions

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
log_start
script -q -c "$DIR/MRF 2>'$stderr_file_path'" --timing="$timing_file_path" "$stdio_file_path"
log_stop
