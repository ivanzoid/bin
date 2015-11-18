#!/bin/sh

AGENT="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/601.1.56 (KHTML, like Gecko) Version/9.0 Safari/537.86.1"

curl -A "$AGENT" --get --data-urlencode "&text=$*" "http://translate.google.com/translate_a/t?client=t&sl=auto&tl=ru" 2>/dev/null | sed 's/\[\[\[\"//' | cut -d \" -f 1

