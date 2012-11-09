#!/usr/bin/env python3.2

from tkinter import *
import os.path
import sys
import datetime

class Dlg(Frame):

	def __init__(self, parent):

		Frame.__init__(self, parent)

		self.movie = None
		self.parent = parent

		Label(parent, text="Movie name: ").pack(padx=5, pady=5)

		self.input = Entry(parent)
		self.input.pack(padx=5)

		b = Button(parent, text="OK", command=self.ok)
		b.pack(padx=5, pady=5)

	def ok(self):

		self.movie = self.input.get()
		self.parent.destroy()

root = Tk()
dlg = Dlg(root)
root.wait_window(dlg)

movie = dlg.movie

fname = os.path.join(sys.path[0], '..', 'My', 'Movies.txt')

with open(fname, 'a') as f:
	now = datetime.datetime.now()
	f.write('%s | %s\n' % (now.strftime('%Y-%m-%d'), movie))


