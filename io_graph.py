#usage: python3 io_graph.py <test.pcap file> <ip_address> -v
#Author: Conard James B. Faraon

"""Generate IO Graph similar to WireShark's.
A pdf image is save with the associated test folder.
See official documentation for more details."""

import argparse
import os
import time
import re
import numpy as nps
import matplotlib.pyplot as plt

#parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", help="Shows various messages from debugging and processing.", action="store_true")
parser.add_argument("pcap", help="Test PCAP filename.")
parser.add_argument("ip_address", help="IP address associated with the test pcap.")
args = parser.parse_args()

#constants
FILENAME = args.pcap.replace('.pcap','') + "_IO1sbins.txt" #data are delimited by pipes |
PICNAME = args.pcap.replace('.pcap','') + "_IO1sbins.pdf"
X_LABEL = "Time (s)"
Y_LABEL = "Packets/ 1 sec"
UL_TRAFFIC = "UL Traffic"
DL_TRAFFIC = "DL Traffic"
UL_PACKET = "UL Packets"
DL_PACKET = "DL Packets"
UL_BAR = 1
DL_BAR = 3
UL_LINE = 5
DL_LINE = 7

def main():

	start = time.time()

	if args.verbose:
		print("Processing Uplink Test IO Graph with the following arguments:")
		print("\tpcap = ", args.pcap)
		print("\tip_address = ", args.ip_address, "\n")

	make1secbins()
	io_data = processFile()
	x_axis = getXaxis(io_data)

	uplink_bar = getData(io_data, UL_BAR)
	if args.verbose:
		print("uplink_bar = ", uplink_bar)

	downlink_bar = getData(io_data, DL_BAR)
	if args.verbose:
		print("downlink_bar = ", downlink_bar)

	uplink_line = getData(io_data, UL_LINE)
	if args.verbose:
		print("uplink_line = ", uplink_line)

	downlink_line = getData(io_data, DL_LINE)
	if args.verbose:
		print("downlink_line = ", downlink_line)

	makePlot(x_axis, uplink_bar, downlink_bar, uplink_line, downlink_line)
	end = time.time()
	print("io_graph.py Elapsed Time: ", (end - start), " s\n")

def make1secbins():
	tshark_cmd = 'tshark -nn -r '+ args.pcap + ' -qz io,stat,1,"ip.src == '+ args.ip_address + \
	' && !(tcp.analysis.flags), ip.dst == '+ args.ip_address + \
	' && !(tcp.analysis.flags), ip.src == '+ args.ip_address + \
	', ip.dst == '+ args.ip_address + '" > ' + FILENAME

	if args.verbose:
		print(tshark_cmd)

	os.system(tshark_cmd)

def processFile():
	io_data = []
	try:
		bin = open(FILENAME, 'r')
		regexp = re.compile(r"^.\s*\d+\s*<")

		for line in bin:
			if regexp.search(line):
				data = line.split("|")
				data.remove('')
				data.remove('\n')
				io_data.append(data)
	finally:
		bin.close()

	if args.verbose:
		for e in io_data:
			print(e)

	return io_data


def getXaxis(io_data):
	x_axis = []

	maximima = len(io_data)

	for i in range(maximima):
		x_axis.append(i)

	if args.verbose:
		print("x_axis = ", x_axis)

	return x_axis

def getData(io_data, index):
	temp = []

	for e in io_data:
		temp.append(int(e[index].strip()))

	return temp

def makePlot(x_axis, uplink_bar, downlink_bar, uplink_line, downlink_line):
	figure, ax = plt.subplots()
	figure.set_size_inches(15, 10)
	width = 0.6
	ax.set_axisbelow(True)
	ax.grid(True)
	p1 = plt.bar(x_axis, uplink_bar, width, color='#ffcc00', align='center')
	p2 = plt.bar(x_axis, downlink_bar, width, color='#3399ff', align='center')
	p3 = plt.plot(x_axis, uplink_line,linewidth=1.0, color='#2a6769')
	p4 = plt.plot(x_axis, downlink_line,linewidth=1.0, color='#8b0a50')

	plt.xlim(-1, max(x_axis)+1)
	plt.xlabel(X_LABEL)
	plt.ylabel(Y_LABEL)
	tmp_title = PICNAME.split('/')
	plt.title("IO Graph: " + tmp_title[-1])
	plt.legend((p1[0], p2[0], p3[0], p4[0]), (UL_TRAFFIC, DL_TRAFFIC, UL_PACKET, DL_PACKET))
	#plt.show()
	figure.savefig(PICNAME, format='pdf')

main()
