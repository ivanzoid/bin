//usr/bin/env go run $0 $@; exit $?
package main

import (
	"fmt"
	"log"
	"os"
	"time"
)

func main() {
	name := ""
	if len(os.Args) > 1 {
		name = os.Args[1]
	}

	dateString := time.Now().Format("06-01-02")

	dirName := dateString
	if len(name) != 0 {
		dirName = dateString + " " + name
	}

	fmt.Println(dirName)

	err := os.Mkdir(dirName, os.ModeDir|os.ModePerm)

	if err != nil {
		log.Fatalln(err)
	}
}
