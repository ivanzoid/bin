#!/usr/bin/env python3.2

from __future__ import division
import math

wheel_diameter = 26
wheel_length = wheel_diameter * math.pi

class Gear(object):
	def __init__(self, ratio, front_index, rear_index):
		self.ratio = ratio
		self.front_index = front_index
		self.rear_index = rear_index


front_gears = [24, 34, 42]
rear_gears = [32, 28, 24, 21, 18, 15, 13, 11]
all_gears = []

for i, f in enumerate(front_gears):
	for j, r in enumerate(rear_gears):
		gear = Gear(f/r, i+1, j+1)
		all_gears.append(gear)
		print("%.2f, " % gear.ratio, end="")
	print()

all_gears = sorted(all_gears, key=lambda gear: gear.ratio)

for i, gear in enumerate(all_gears):
	print("%d:%d %.2f" % (gear.front_index, gear.rear_index, gear.ratio), end="")
	if i != len(all_gears) - 1:
		print(" %.2f" % (all_gears[i+1].ratio - all_gears[i].ratio))
