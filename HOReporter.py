#usage: python3 HOReporter.py -v <filename.csv>
#Author: Conard James B. Faraon

"""This creates objects for generating HO/No_HO and RAN type reports.
See official documentation for further details."""

import argparse
import threading
import time
import os
from ho_report_makers import HOReport

#parse arguments here
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", help="Shows various messages from debugging and processing.", action="store_true")
parser.add_argument("root_csv", help="Root Metrics CSV File.")
args = parser.parse_args()

def main():
	start = time.time()
	print("Generating HO/No_HO and RAN type reports using ", args.root_csv, "\n")

	ho_report_directory_name = createDirectory()

	if args.verbose:
		print("Started Multi-threading for HOReporter.py", "\n")

	thread_lock = threading.Lock()
	threads = []

	ho_report1 = HOReport.HOReport("Uplink" , args.root_csv, ho_report_directory_name)
	ho_report2 = HOReport.HOReport("Downlink" , args.root_csv, ho_report_directory_name)
	ho_report3 = HOReport.HOReport("Lite_Data_Test" , args.root_csv, ho_report_directory_name)
	ho_report4 = HOReport.HOReport("Lite_Data_Secure_Test" , args.root_csv, ho_report_directory_name)

	ho_report1.start()
	ho_report2.start()
	ho_report3.start()
	ho_report4.start()

	threads.append(ho_report1)
	threads.append(ho_report2)
	threads.append(ho_report3)
	threads.append(ho_report4)

	#wait for all threads to complete
	#TODO better way to wait for threads, currently a blocking call
	if args.verbose:
		print("HOReporter.py Main thread is waiting for other threads.")

	for t in threads:
		thread_name = t.name
		print("Waiting on ", thread_name)
		t.join()
		print("Finished waiting for ", thread_name)

	print("Exiting HOReporter.py Main Thread", "\n")

	end = time.time()
	print("HOReporter.py Elapsed Time: ", (end - start), " s\n")

def createDirectory():
	ho_report_directory_name = args.root_csv[:-4] + "_HOReport"
	if not os.path.exists(ho_report_directory_name):
		if args.verbose:
			print("Making a directory for ", ho_report_directory_name)
		os.makedirs(ho_report_directory_name)

	return ho_report_directory_name

main()
