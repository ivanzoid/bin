//usr/bin/env go run "$0" "$@"; exit "$?"

package main

import (
	"bufio"
	"flag"
	"fmt"
	"log"
	"os"
	"sort"
)

type DayLog struct {
	entries []string
}

func main() {
	prefix := ""
	flag.Parse()
	if flag.NArg() != 0 {
		prefix = fmt.Sprintf("%v: ", flag.Arg(0))
	}

	dayLogs := make(map[string]DayLog)

	scanner := bufio.NewScanner(os.Stdin)
	for scanner.Scan() {
		line := scanner.Text()
		if len(line) < 10 {
			continue
		}
		dateString := line[0:10]
		text := line[11:len(line)]

		var dayLog DayLog
		if dayLogFound, ok := dayLogs[dateString]; ok {
			dayLog = dayLogFound
		} else {
			dayLog.entries = make([]string, 0)
		}

		dayLog.entries = append(dayLog.entries, text)

		dayLogs[dateString] = dayLog
	}

	if err := scanner.Err(); err != nil {
		log.Println(err)
	}

	dateStrings := make([]string, 0, len(dayLogs))
	for dateString := range dayLogs {
		dateStrings = append(dateStrings, dateString)
	}

	sort.Strings(dateStrings)

	for _, dateString := range dateStrings {
		fmt.Printf("%v:\n", dateString)
		dayLog := dayLogs[dateString]
		for _, entry := range dayLog.entries {
			fmt.Printf("    %v%v\n", prefix, entry)
		}
	}

	// fmt.Printf("%v\n", dayLogs)
}
