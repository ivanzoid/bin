#!/usr/bin/env python3

import os
import subprocess

subprocess.run(["mkdir", "-p", "2"])
subprocess.run(["mkdir", "-p", "2.5"])
subprocess.run(["mkdir", "-p", "3"])
subprocess.run(["mkdir", "-p", "4"])
subprocess.run(["mkdir", "-p", "5"])

for f in os.listdir('.'):
    if not os.path.isfile(f):
        continue

    print(f'{f}... ', end='')

    res = subprocess.run(["video-duration", f], capture_output=True)

    if res.returncode != 0:
        print(f'{f}: unknown duration (returncode = {res.returncode})')
        continue

    duration = float(res.stdout)

    print(f'duration = {duration}', end='')

    if duration >= 5.0:
        print(' -> 5')
        subprocess.run(["mv", f, "5"])
    elif duration >= 4.0:
        print(' -> 4')
        subprocess.run(["mv", f, "4"])
    elif duration >= 3.0:
        print(' -> 3')
        subprocess.run(["mv", f, "3"])
    elif duration >= 2.5:
        print(' -> 2.5')
        subprocess.run(["mv", f, "2.5"])
    elif duration >= 2.0:
        print(' -> 2')
        subprocess.run(["mv", f, "2"])
    else:
        print('')
