set -e

# this shell script is very odd because find only lets {} be at the end of the exec command OR only lets it be used once

# if find worked the way I wanted it to I'd be able to do something like
# find * -name '*.yml' -exec chevron -d << parameters.json-data-file-path >> {} > < "parameters.output-folder-path >>/{}" \;
# but I am not that good at Bash. So this script is written to be used by find/exec and
# not by humans. Sorry.

# $1 = data path
# $2 = starting path for the output files generated by this command
# $3 = relative path specifically that we are working on
"$(python3 -m site --user-base)/bin/chevron" -d "$1" "$3" > "$2/$3"
