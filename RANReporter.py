#usage: python3 RANReporter.py -v <filename.csv>
#Author: Conard James B. Faraon

"""This creates objects for generating reports on distribution of RAN type tests by radio technology.
See official documentation for further details."""

import argparse
import threading
import time
import os
from ran_report_makers import RANReport

#parse arguments here
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", help="Shows various messages from debugging and processing.", action="store_true")
parser.add_argument("root_csv", help="Root Metrics CSV File.")
args = parser.parse_args()

def main():
	start = time.time()
	print("Generating Distribution of RAN type tests by radio technology using ", args.root_csv, "\n")

	ran_report_directory_name = createDirectory()

	if args.verbose:
		print("Started Multi-threading for RANReporter")

	thread_lock = threading.Lock()
	threads = []

	ran_report1 = RANReport.RANReport("ALL",args.root_csv, ran_report_directory_name)
	ran_report2 = RANReport.RANReport("Uplink",args.root_csv, ran_report_directory_name)
	ran_report3 = RANReport.RANReport("Downlink",args.root_csv, ran_report_directory_name)
	ran_report4 = RANReport.RANReport("Lite_Data_Test",args.root_csv, ran_report_directory_name)
	ran_report5 = RANReport.RANReport("Lite_Data_Secure_Test",args.root_csv, ran_report_directory_name)

	ran_report1.start()
	ran_report2.start()
	ran_report3.start()
	ran_report4.start()
	ran_report5.start()

	threads.append(ran_report1)
	threads.append(ran_report2)
	threads.append(ran_report3)
	threads.append(ran_report4)
	threads.append(ran_report5)

	#wait for all threads to complete
	#TODO better way to wait for threads, currently a blocking call
	if args.verbose:
		print("RANReporter.py Main thread is waiting for other threads.")

	for t in  threads:
		thread_name = t.name
		print("Waiting on ", thread_name)
		t.join()
		print("Finished waiting for ", thread_name)

	print("Exiting RANReporter.py Main Thread", "\n")

	end = time.time()
	print("RANReporter.py Elapsed Time: ", (end - start), " s\n")

def createDirectory():
	ran_report_directory_name = args.root_csv[:-4] + "_RANReport"
	if not os.path.exists(ran_report_directory_name):
		if args.verbose:
			print("Making a directory for ", ran_report_directory_name)
		os.makedirs(ran_report_directory_name)
	return ran_report_directory_name

main()