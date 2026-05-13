#!/bin/sh

deep-translator -trans google -src auto -tg ru -txt "$*" 2>/dev/null | tail -1 | sed 's/^Translation result: //'
