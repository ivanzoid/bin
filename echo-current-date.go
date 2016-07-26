//usr/bin/env go run $0 $@; exit $?
package main

import (
	"fmt"
	"time"
)

func main() {
	fmt.Println(time.Now().Format("2006-01-02"))
}
