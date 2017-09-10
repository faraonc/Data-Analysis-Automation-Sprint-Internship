#usage: python3 ul_latency_graph.py <directory name> -v -n -f
#Author: Conard James B. Faraon

"""Generate the latency graphs for each 100ms bins using the Uplink Throughput Test pcap files.
A new folder is generated for this reports.
See official documentation for more details."""

import os
import glob
import argparse
import random
import re
import time
import csv
import numpy as np
import matplotlib.pyplot as plt
from collections import OrderedDict

#parse arguments here
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", help="Show various messages from debugging and processing.", action="store_true")
parser.add_argument("-n", "--no_tshark", help="Disables Tshark for processing pcaps files.", action="store_true")
parser.add_argument("-f", "--fairness", help="Enables fairness for sampling and generating graphs.", action="store_true")
parser.add_argument("dir", help="Directory name of small Uplink Throughput pcap files generated from previous data processing scripts.")
args = parser.parse_args()

#constants
PASSED = "passed"
FAILED = "failed"
DIR_EXT = "_UL_Latency_Graph/"
MAX_SAMPLE = 200

def main():
	start = time.time()

	if args.verbose:
		print("Generating UL Latency Graph for directory = ", args.dir, "\n")

	#TODO maybe needed for later
	# ul_pcap_list = findULStreamListTextFile()

	# if args.verbose:
	# 	print("Entries for ULStreamList:")
	# 	for e in ul_pcap_list:
	# 		print(e)
	# 	print()

	#glob paths of Uplink Throughput Test pcap files.
	passed_ul_pcap_list = findULPcaps(PASSED)
	failed_ul_pcap_list = findULPcaps(FAILED)

	if args.verbose:
		print("Entries for passed_ul_pcap_list:")
		for e in passed_ul_pcap_list:
			print(e)
		print()

		print("Entries for failed_ul_pcap_list:")
		for e in failed_ul_pcap_list:
			print(e)
		print()

	makeLatencyGraphDir()
	passed_ul_data_path = processULPcaps(passed_ul_pcap_list)
	failed_ul_data_path = processULPcaps(failed_ul_pcap_list)

	print("Number of passed UL Tests = ", len(passed_ul_data_path), "\n")
	print("Number of failed UL Tests = ", len(failed_ul_data_path), "\n")

	if args.verbose:
		print("Entries for passed_ul_data_path:")
		for e in passed_ul_data_path:
			print(e)
		print()

		print("Entries for failed_ul_data_path:")
		for e in failed_ul_data_path:
			print(e)
		print()

	passed_ul_data = getData(passed_ul_data_path)
	failed_ul_data = getData(failed_ul_data_path)

	#shuffle for sampling
	random.shuffle(passed_ul_data)
	random.shuffle(failed_ul_data)

	if args.verbose:
		print("Data for passed_ul_data:")
		print(passed_ul_data, "\n")
		print("Data for failed_ul_data:")
		print(failed_ul_data, "\n")

	sample_numbers = len(passed_ul_data)
	if len(passed_ul_data) > len(failed_ul_data):
		sample_numbers = len(failed_ul_data)

	passed_ul_dict = mapSamples(passed_ul_data, sample_numbers)
	failed_ul_dict = mapSamples(failed_ul_data, sample_numbers)

	if args.verbose:
		print("Samples taken = ", len(passed_ul_data))
		print("Dictionary for passed_ul_dict:")
		for k,v in passed_ul_dict.items():
			print(k,v)
		print()
		print("Samples taken = ", len(failed_ul_data))
		print("Dictionary for failed_ul_dict:")
		for k,v in failed_ul_dict.items():
			print(k,v)
		print()

	generateLogFile(passed_ul_dict, failed_ul_dict)

	#plot a side by side bar graph
	plotBarGraph(passed_ul_dict, failed_ul_dict)

	#plot separate bar graphs
	plotBar(passed_ul_dict, PASSED)
	plotBar(failed_ul_dict, FAILED)

	#cleanup
	cmd = "rm " + args.dir + DIR_EXT + "*.txt"
	os.system(cmd)

	end = time.time()
	print("latency_graph.py Elapsed Time: ", (end - start), " s\n")

def plotBar(data, test_status):
	bar_color = '#3399ff'
	if test_status == PASSED:
		bar_color='#ffcc00'

	N = 21
	y_axis = list(data.values())
	ind = np.arange(N)
	width = 0.5

	fig, ax = plt.subplots()
	fig.set_size_inches(15, 10)
	ax.set_axisbelow(True)
	ax.grid(True)
	rects1 = ax.bar(ind, y_axis, width, color=bar_color)
	ax.set_xlabel("100 ms Bins", fontsize=18)
	ax.set_ylabel("# of Instances", fontsize=18)
	picname = args.dir + "_UL_Smple_Avg_Latency_"+ test_status.upper() +".pdf"
	imagename = args.dir + "_UL_Smple_Avg_Latency_"+ test_status.upper() +".png"
	ax.set_title(picname, fontsize=18)

	ax.tick_params(axis='x', which='major', pad=5)
	ax.set_xticks(ind + width / 2)
	ax.set_xticklabels(('< 0.1', '< 0.2', '< 0.3', '< 0.4', '< 0.5', '< 0.6','< 0.7',
		'< 0.8','< 0.9','< 1.0','< 1.1','< 1.2','< 1.3', '< 1.4','< 1.5', '< 1.6',
		'< 1.7', '< 1.8', '< 1.9', '< 2.0', '>= 2.0'))

	for tick in ax.xaxis.get_major_ticks():
		tick.label.set_fontsize(9)

	#plt.show()
	fig.savefig(args.dir + DIR_EXT + picname)
	fig.savefig(args.dir + DIR_EXT + imagename)

def plotBarGraph(passed_ul_dict, failed_ul_dict):
	N = 21
	y_passed = list(passed_ul_dict.values())
	ind = np.arange(N)
	width = 0.4

	fig, ax = plt.subplots()
	fig.set_size_inches(15, 10)
	ax.set_axisbelow(True)
	ax.grid(True)
	rects1 = ax.bar(ind, y_passed, width, color='#ffcc00')

	y_failed = list(failed_ul_dict.values())
	rects2 = ax.bar(ind + width, y_failed, width, color='#3399ff')
	ax.set_xlabel("100 ms Bins", fontsize=18)
	ax.set_ylabel("# of Instances", fontsize=18)
	picname = args.dir + "_UL_Smple_Avg_Latency.pdf"
	imagename = args.dir + "_UL_Smple_Avg_Latency.png"
	ax.set_title(picname, fontsize=18)
	
	ax.tick_params(axis='x', which='major', pad=5)
	ax.set_xticks(ind + width / 2)
	ax.set_xticklabels(('< 0.1', '< 0.2', '< 0.3', '< 0.4', '< 0.5', '< 0.6','< 0.7',
		'< 0.8','< 0.9','< 1.0','< 1.1','< 1.2','< 1.3', '< 1.4','< 1.5', '< 1.6',
		'< 1.7', '< 1.8', '< 1.9', '< 2.0', '>= 2.0'))

	ax.legend((rects1[0], rects2[0]), ('Passed', 'Failed'))
	for tick in ax.xaxis.get_major_ticks():
		tick.label.set_fontsize(9)

	#plt.show()
	fig.savefig(args.dir + DIR_EXT + picname)
	fig.savefig(args.dir + DIR_EXT + imagename)
	
def findULStreamListTextFile():
	tmp_path = args.dir + "/_*/*ULStreamList_MATCH.txt"

	if args.verbose:
		print("Globbing with tmp_path = ", tmp_path)

	return glob.glob(tmp_path)

def findULPcaps(type):
	glob_path = args.dir + "/*/*/" + type + "/*/*/*/*UL#*.pcap"

	tmp = glob.glob(glob_path)

	return tmp

def makeLatencyGraphDir():
	dirname = args.dir + "_UL_Latency_Graph"
	if not os.path.exists(dirname):
		if args.verbose:
			print("Making a directory for ", dirname)
		os.makedirs(dirname)

def processULPcaps(pcap_path_list):
	tmp = []
	for e in pcap_path_list:
		output = args.dir + DIR_EXT + e.split('/')[-1][:-5] + "_Latency_Data.txt"
		tmp.append(output)
		cmd = "tshark -r " + e + " -qz io,stat,0.05,\"AVG(tcp.analysis.ack_rtt)tcp.analysis.ack_rtt\" > " + output
		
		if args.no_tshark is None or not args.no_tshark:
			if args.verbose:
				print(cmd, "\n")
			os.system(cmd)

	return tmp

def getData(data_path):
	data = []
	regexp = re.compile(r"^.\s*\d\.\d*\s*<")
	for e in data_path:
		try:
			data_file = open(e,'r')
			sample_count = 0
			for line in data_file:
				if regexp.search(line):
					sample_count += 1
					data_row = line.split("|")
					data_row.remove('')
					data_row.remove('\n')
					latency = float(data_row[1])
					#print(line, latency)
					data.append(latency)

				if sample_count == MAX_SAMPLE:
					break
		finally:
			data_file.close()

	return data

def mapSamples(data, sample_limit):
	tmp_dict = initDict()

	sample_counter = 0
	for sample in data: #seriously, drink coffee to fix this
		sample_counter += 1
		if sample != 0.0:
			if sample < 0.1:
				tmp_dict[0.0] += 1
			elif sample < 0.2:
				tmp_dict[0.1] += 1
			elif sample < 0.3:
				tmp_dict[0.2] += 1
			elif sample < 0.4:
				tmp_dict[0.3] += 1
			elif sample < 0.5:
				tmp_dict[0.4] += 1
			elif sample < 0.6:
				tmp_dict[0.5] += 1
			elif sample < 0.7:
				tmp_dict[0.6] += 1
			elif sample < 0.8:
				tmp_dict[0.7] += 1
			elif sample < 0.9:
				tmp_dict[0.8] += 1
			elif sample < 1.0:
				tmp_dict[0.9] += 1
			elif sample < 1.1:
				tmp_dict[1.0] += 1
			elif sample < 1.2:
				tmp_dict[1.1] += 1
			elif sample < 1.3:
				tmp_dict[1.2] += 1
			elif sample < 1.4:
				tmp_dict[1.3] += 1
			elif sample < 1.5:
				tmp_dict[1.4] += 1
			elif sample < 1.6:
				tmp_dict[1.5] += 1
			elif sample < 1.7:
				tmp_dict[1.6] += 1
			elif sample < 1.8:
				tmp_dict[1.7] += 1
			elif sample < 1.9:
				tmp_dict[1.8] += 1
			elif sample < 2.0:
				tmp_dict[1.9] += 1
			else:
				tmp_dict[2.0] += 1

		if args.fairness and sample_counter == sample_limit:
			break

	return tmp_dict

def initDict():
	# tmp_dict = {}
	tmp_dict = OrderedDict()
	max_key = 2.0
	curr_key = 0.0

	while curr_key <= max_key:
		tmp_dict[curr_key] = 0
		curr_key += 0.100
		curr_key = round(curr_key, 10)

	return tmp_dict

def generateLogFile(passed_ul_dict, failed_ul_dict):
	passed_filename = args.dir + DIR_EXT + args.dir + "_UL_Smple_Avg_Latency_Passed_Data.csv"
	failed_filename = args.dir + DIR_EXT + args.dir + "_UL_Smple_Avg_Latency_Failed_Data.csv"

	try:
		passed_file = open(passed_filename, 'w')
		passed_writer = csv.writer(passed_file, delimiter=',')
		passed_keys = list(passed_ul_dict.keys())
		for k in passed_keys:
			tmp = []
			tmp.append(k)
			tmp.append(passed_ul_dict[k])
			passed_writer.writerow(tmp)

		failed_file = open(failed_filename, 'w')
		failed_writer = csv.writer(failed_file, delimiter=',')
		failed_keys = list(failed_ul_dict.keys())
		for k in failed_keys:
			tmp = []
			tmp.append(k)
			tmp.append(failed_ul_dict[k])
			failed_writer.writerow(tmp)

	finally:
		passed_file.close()
		failed_file.close()

main()

