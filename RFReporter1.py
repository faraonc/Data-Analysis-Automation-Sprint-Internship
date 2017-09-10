#usage: python3 RFReporter1.py <filename.csv> -v
#Author: Conard James B. Faraon

"""This creates several objects of class RFReport1.py and places each object in a separate thread.
See official documenation for further details."""

import argparse
import threading
import time
import os
from rf_report_makers import RFReport1

#parse arguments here
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", help="Shows various messages from debugging and processing.", action="store_true")
parser.add_argument("root_csv", help="Root Metrics CSV File.")
args = parser.parse_args()

def main():
	start = time.time()
	print("Generating RF Perfomance Report# 1 based from ", args.root_csv, "\n")

	dirname = createDirectory()

	if args.verbose:
		print("Started Multi-threading for RFReporter1", "\n")

	threadLock = threading.Lock()
	threads = []

	rf_reporter_1_UL = RFReport1.RFReport1("Uplink", args.root_csv, dirname)
	rf_reporter_1_DL = RFReport1.RFReport1("Downlink", args.root_csv, dirname)
	rf_reporter_1_DT = RFReport1.RFReport1("Lite_Data_Test", args.root_csv, dirname)
	rf_reporter_1_ST = RFReport1.RFReport1("Lite_Data_Secure_Test", args.root_csv, dirname)

	rf_reporter_1_UL.start()
	rf_reporter_1_DL.start()
	rf_reporter_1_DT.start()
	rf_reporter_1_ST.start()

	threads.append(rf_reporter_1_UL)
	threads.append(rf_reporter_1_DL)
	threads.append(rf_reporter_1_DT)
	threads.append(rf_reporter_1_ST)

	#wait for all threads to complete
	#TODO better way to wait for threads, currently a blocking call
	if args.verbose:
		print("RFReporter1 Main thread is waiting for other threads.")

	for t in threads:
		thread_name = t.name
		print("Waiting on ", thread_name)
		t.join()
		print("Finished waiting for ", thread_name)

	print("Exiting RFReporter 1 Main Thread\n")

	end = time.time()
	print("RFReporter1 Elapsed Time: ", (end - start), " s\n")

def createDirectory():
	dirname = args.root_csv[:-4] +  "_RFReport#1"
	if not os.path.exists(dirname):
		if args.verbose:
			print("Making a directory for ", dirname)
		os.makedirs(dirname)

	if not os.path.exists(dirname + "/records"):
		if args.verbose:
			print("Making a directory for ", dirname + "/records" )
		os.makedirs(dirname + "/records")

	return dirname

main()