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

#constants
LTE_PASSED = args.dir + "_LTE_passed_report.csv"
LTE_FAILED = args.dir + "_LTE_failed_report.csv"
OTHER_PASSED = args.dir + "_Other_passed_report.csv"
OTHER_FAILED = args.dir + "_Other_failed_report.csv"

def main():
	start = time.time()

	if args.verbose:
		print('Started running "find_test_results.py"')
		print('Directory = ', args.dir, "\n")

	#get the path for passed and failed tests	
	lte_fails, other_fails = getFailedPaths()
	lte_success, other_success = getPassedPaths()

	if args.verbose:
		print()
		print("lte_fails")
		for e in lte_fails:
			print(e)

		print()
		print("other_fails")
		for e in other_fails:
			print(e)

		print()
		print("lte_success")
		for e in lte_success:
			print(e)

		print()
		print("other_success")
		for e in other_success:
			print(e)

		print()

	generateLTEFailedReport(lte_fails)
	generateOtherFailedReport(other_fails)
	generateLTEPassedReport(lte_success)
	generateOtherPassedReport(other_success)

	end = time.time()
	print("find_test_results.py Elapsed Time: ", (end - start), " s\n")

def getFailedPaths():
	lte_tmp_path = args.dir + "/*/*/failed/*/*/*/*.csv"
	lte_tmp = glob.glob(lte_tmp_path)

	other_tmp_path = args.dir + "/Other/*/failed/*/*/*.csv"
	other_tmp = glob.glob(other_tmp_path)

	return lte_tmp, other_tmp

def getPassedPaths():
	lte_tmp_path = args.dir + "/*/*/passed/*/*/*/*.csv"
	lte_tmp = glob.glob(lte_tmp_path)

	other_tmp_path = args.dir + "/Other/*/passed/*/*/*.csv"
	other_tmp = glob.glob(other_tmp_path)

	return lte_tmp, other_tmp

def generateLTEFailedReport(lte_fails):
	try:
		failed_csv = open(LTE_FAILED, 'w')
		failed_writer = csv.writer(failed_csv, delimiter=',')

		for path in lte_fails:
			csvtmp = open(path, 'r')
			csv_reader = csv.reader(csvtmp)

			#this is used for the first row of headers
			firstround = True
			#these are the column indices
			test = 0
			test_cycle_id = 0
			utc_time = 0
			header = []

			for row in csv_reader:
				for cell in row:
					if firstround:
						header.append(cell)
					else:
						break
						
				if firstround:
					test = header.index("Test")
					utc_time = header.index("UTC_Time")
					test_cycle_id = header.index("Test_Cycle_ID")
					firstround = False
				else:
					data = []
					data.append(row[utc_time])
					data.append(row[test])
					data.append(row[test_cycle_id])
					data.append(path)
					failed_writer.writerow(data)
					break

	finally:
		failed_csv.close()

def generateLTEPassedReport(lte_success):
	try:
		passed_csv = open(LTE_PASSED, 'w')
		passed_writer = csv.writer(passed_csv, delimiter=',')

		for path in lte_success:
			csvtmp = open(path, 'r')
			csv_reader = csv.reader(csvtmp)

			#this is used for the first row of headers
			firstround = True
			#these are the column indices
			test = 0
			test_cycle_id = 0
			utc_time = 0
			header = []

			for row in csv_reader:
				for cell in row:
					if firstround:
						header.append(cell)
					else:
						break
						
				if firstround:
					test = header.index("Test")
					utc_time = header.index("UTC_Time")
					test_cycle_id = header.index("Test_Cycle_ID")
					firstround = False
				else:
					data = []
					data.append(row[utc_time])
					data.append(row[test])
					data.append(row[test_cycle_id])
					data.append(path)
					passed_writer.writerow(data)
					break

	finally:
		passed_csv.close()


def generateOtherFailedReport(other_fails):
	try:
		other_csv = open(OTHER_FAILED, 'w')
		other_writer = csv.writer(other_csv, delimiter=',')

		for path in other_fails:
			csvtmp = open(path, 'r')
			csv_reader = csv.reader(csvtmp)

			#this is used for the first row of headers
			firstround = True
			#these are the column indices
			test = 0
			test_cycle_id = 0
			utc_time = 0
			header = []

			for row in csv_reader:
				for cell in row:
					if firstround:
						header.append(cell)
					else:
						break
						
				if firstround:
					test = header.index("Test")
					utc_time = header.index("UTC_Time")
					test_cycle_id = header.index("Test_Cycle_ID")
					firstround = False
				else:
					data = []
					data.append(row[utc_time])
					data.append(row[test])
					data.append(row[test_cycle_id])
					data.append(path)
					other_writer.writerow(data)
					break

	finally:
		other_csv.close()


def generateOtherPassedReport(other_success):
	try:
		other_csv = open(OTHER_PASSED, 'w')
		other_writer = csv.writer(other_csv, delimiter=',')

		for path in other_success:
			csvtmp = open(path, 'r')
			csv_reader = csv.reader(csvtmp)

			#this is used for the first row of headers
			firstround = True
			#these are the column indices
			test = 0
			test_cycle_id = 0
			utc_time = 0
			header = []

			for row in csv_reader:
				for cell in row:
					if firstround:
						header.append(cell)
					else:
						break
						
				if firstround:
					test = header.index("Test")
					utc_time = header.index("UTC_Time")
					test_cycle_id = header.index("Test_Cycle_ID")
					firstround = False
				else:
					data = []
					data.append(row[utc_time])
					data.append(row[test])
					data.append(row[test_cycle_id])
					data.append(path)
					other_writer.writerow(data)
					break

	finally:
		other_csv.close()

main()
