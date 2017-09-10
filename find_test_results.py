#usage: python3 find_test_results.py <directory name> -v
#Author: Conard James B. Faraon

"""Generate passed and failed reports from the directory of the Root Metrics markets.
A new folder is generated for this reports.
See official documentations for more details."""

import argparse
import os
import glob
import time
import csv

#parse arguments here
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", help="Shows various messages from debugging and processing.", action="store_true")
parser.add_argument("dir", help="Directory Name of small CSV files generated from previous data processing scripts.")
args = parser.parse_args()

#file directory
UTC_FOLDER = args.dir + "_UTC_Matcher"

def main():
	start = time.time()

	if args.verbose:
		print("Started running find_test_results.py")
		print("Finding test results in directory = ", args.dir)
		print("Generating passed & failed reports in directory = ", UTC_FOLDER, "\n")

	generateFolder()
	passed_tests_paths = getTestPaths("passed")
	failed_tests_paths = getTestPaths("failed")

	if args.verbose:
		print("The following are the paths for passed_tests_paths:")
		for path in passed_tests_paths:
			print(path)
		print()

	if args.verbose:
		print("\nThe following are the paths for failed_tests_paths:")
		for path in failed_tests_paths:
			print(path)
		print()

	generateUTCReports(passed_tests_paths, "PASSED")
	generateUTCReports(failed_tests_paths, "FAILED")

	end = time.time()
	print("Completed find_test_results.py Elapsed Time: ", (end - start), " s\n")

def generateUTCReports(test_paths, test_result):
	file_location = UTC_FOLDER + "/" + args.dir + "_" + test_result +"_Report.csv"
	if args.verbose:
		print("Saving the file in = ", file_location)

	try:
		report_file = open(file_location, 'w')
		report_writer = csv.writer(report_file, delimiter=',')

		for path in test_paths:
			try:
				test_file = open(path, 'r')
				test_reader = csv.reader(test_file)
				isFirstRound = True
				test= 0
				test_cycle_id = 0
				utc_time = 0
				data = []

				for row in test_reader:
					if isFirstRound:
						isFirstRound = False
						utc_time = row.index("UTC_Time")
						test_cycle_id = row.index("Test_Cycle_ID")
						test = row.index("Test")

					else:
						data.append(row[utc_time])
						data.append(row[test])
						data.append(row[test_cycle_id])
						data.append(path)
						report_writer.writerow(data)
						del data [:]
						break

			finally:
				test_file.close()

	finally:
		report_file.close()

def getTestPaths(test_result):
	glob_path = args.dir + "/*/*/" + test_result + "/*/*/*/*.csv"
	test_path = glob.glob(glob_path)
	return test_path

def generateFolder():
	if not os.path.exists(UTC_FOLDER):
		os.makedirs(UTC_FOLDER)

main()
