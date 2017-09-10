#usage: python3 tsg.py <pcap file> -v
#Author: Conard James B. Faraon

"""Generate a time sequence graph for a small pcap file specific to a test.
A pdf image is save with the associated test folder.
See official documentation for more details."""

from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
import os
import time
import datetime
import matplotlib
from matplotlib import pyplot, markers
from matplotlib.lines import Line2D
from matplotlib.transforms import Affine2D

#parse arguments here
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", help="Shows various messages from debugging and processing.", action="store_true")
parser.add_argument("pcap_file", help="PCAP File.")
args = parser.parse_args()

#constants
COLOURS = {"white":"#1b9e77",
		   "black": "#666666",
		   "orange": "#a6761d",
		   "green": "#66a61e",
		   "yellow": "#e6ab02",
		   "red": "#d95f02",
		   "blue": "#386cb0",
		   "purple": "#7570b3",
		   "pink": "#ff1493"}

MARKERS = {'darrow': markers.CARETDOWN,
		   'uarrow': markers.CARETUP,
		   'box': 's',
		   'dot': '.',
		   'utick': '^',
		   'dtick': 'v',
		   'htick': '_',
		   'diamond': 'D'}

#change if necessary
FILETYPES = {'rm *tline.xpl',
			 'rm *owin.xpl',
			 'rm *rtt.xpl',
			 'rm *ssize.xpl',
			 'rm *tput.xpl'}

def main():
	start = time.time()

	if args.verbose:
		print("Generating TSG for = ", args.pcap_file)

	generateXpl()
	xpl_list = getFiles()

	if args.verbose:
		print(xpl_list)

	for file in xpl_list:
		plot(file)

	cleanUp()

	end = time.time()
	print("tsg.py Elapsed Time: ", (end - start), " s\n")

def generateXpl():
	#-n   don't resolve host or service names (much faster)
	#-C   produce color plot[s]
	#-G   create ALL graphs
	tcptrace_cmd = "tcptrace -n -C -G " + args.pcap_file

	if args.verbose:
		print(tcptrace_cmd)

	os.system(tcptrace_cmd)

	#remove specific xpl files not needed
	#edit FILETYPES declarations and assignments aboive if necesary
	for rm_cmd in FILETYPES:
		os.system(rm_cmd)

def getFiles():
	tmp = []

	for file in os.listdir(os.curdir):
		if file.endswith(".xpl"):
			tmp.append(file)

	return tmp

def cleanUp():
	os.system("rm *xpl")

def plot(filename):
	if args.verbose:
		print("Plotting = ", filename)

	xpl_file = open(filename, "r")

	fig, ax = pyplot.subplots()
	ax.get_xaxis().get_major_formatter().set_scientific(False)
	ax.get_yaxis().get_major_formatter().set_scientific(False)
	col = "black"

	markers = {}
	def addMarker(col, m, parts):
		if len(parts) == 4 and parts[3] in COLOURS:
			col = parts[3]

		key = col,m
		x,y = map(float, parts[1:3])

		if key in markers:
			markers[key][0].append(x)
			markers[key][1].append(y)
		else:
			markers[key] = ([x],[y])

	lines = {}
	def addLine(col, parts):
		x1,y1,x2,y2 = map(float, parts[1:])

		if not col in lines:
			lines[col] = [([x1,x2],[y1,y2])]
		else:
			found = False
			for l in lines[col][-5:]:
				if l[0][-1] == x1 and l[1][-1] == y1:
					l[0].append(x2)
					l[1].append(y2)
					found = True
					break
			if not found:
				lines[col].append(([x1,x2],[y1,y2]))

	#actual plotting starts here
	for line in xpl_file:
		line = line.strip()
		parts = line.split()

		if line.startswith("timeval"):
			pass

		elif line == "title":
			fig.suptitle(args.pcap_file.split("/")[-1] + '\n' + next(xpl_file).strip(), fontsize=9)

		elif line == "xlabel":
			ax.set_xlabel(next(xpl_file).strip().replace('t', 'T') + " (s)", fontsize=8)

		elif line == "ylabel":
			ax.set_ylabel(next(xpl_file).strip().replace('s', 'S') + " (B)", fontsize=8)

		elif line in COLOURS:
			col = line

		elif parts[0] == "line":
			x1,y1,x2,y2 = map(float, parts[1:])
			addLine(col, parts)

		elif parts[0] in ("atext","rtext","ltext"):
			text = next(xpl_file).strip()
			x,y = map(float, parts[1:3])
			kwargs = {'ha': 'center', 'va':'center', 'color': COLOURS[col],'textcoords':'offset points'}
			theta = 0
			offset = (0,5)

			if len(parts) == 4 and parts[3] in COLOURS:
				kwargs['color'] = COLOURS[parts[3]]
			if parts[0] == "rtext":
				kwargs['ha'] = 'left'
				offset = (2,0)
			elif parts[0] == "ltext":
				kwargs['ha'] = 'right'
				offset = (-2,0)
			t = ax.annotate(text,(x,y),offset,**kwargs,fontsize=5)

		# Markers are specified as 'marker x y'
		elif parts[0] in MARKERS.keys():
			addMarker(col,MARKERS[parts[0]],parts)

		# draw
		elif line == "go":
			break
		else:
			print("Unknown: %s" % line)

	# Draw the lines
	for c,ll in lines.items():
		for x,y in ll:
			#for val in x
			ax.plot(x,y,lw=1,c=COLOURS[c])
	# Draw the markers
	for (c,m),(x,y) in markers.items():
		ax.plot(x,y,ls="",marker=m,markeredgecolor=COLOURS[c],markerfacecolor='none',markersize=2)

	for tick in ax.xaxis.get_major_ticks():
				tick.label.set_fontsize(6)
	for tick in ax.yaxis.get_major_ticks():
				tick.label.set_fontsize(6)

	ax.get_xaxis().get_major_formatter().set_useOffset(False)
	ax.get_yaxis().get_major_formatter().set_useOffset(False)
	saveFile = args.pcap_file[:-5] + '_' + filename[:-4] + ".pdf"
	fig.savefig(saveFile, format="pdf", bbox_inches="tight")

main()
