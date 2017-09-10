#usage: python3 process_root_csv.py <Root file.csv> -v
#Author: Conard James B. Faraon

"""This processess different tests from the Root csv file into specific tests that are saved in a structured directory.
See official documentation for more details."""

import argparse
import os
import sys
import time
import csv

#parse arguments here
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", help="Shows various messages from debugging and processing.", action="store_true")
parser.add_argument("csv_file", help="Root Metrics CSV File.")
args = parser.parse_args()

COLUMNS_ATTR = ["Driver-Kit", 
				"Test", 
				"Access_Summary", 
				"Task_Summary",
				"Test_Cycle_ID",
				"Message",
				"Data_Network_Type",
				"LTE_eCI",
				"LTE_eNB_ID"]

TEST_TYPES = ["Uplink", "Downlink", "Lite Data Test", "Lite Data Secure Test"]

def main():
	start = time.time()

	if args.verbose:
		print("Started running process_root_csv.py for Root Metrics csv file = ", args.csv_file, "\n")

	makeMarketDirectory()

	try:
		csv_file = open(args.csv_file,'r')
		csv_reader = csv.reader(csv_file)
		columns_dict, header_buffer = setupColumnsForDict(csv_reader)

		if args.verbose:
			print("Display indices for attributes:")
			for k,v in columns_dict.items():
				print(k, ' ', v)

		processCSV(csv_reader, columns_dict, header_buffer)

	finally:
		csv_file.close()

	end = time.time()
	print("Completed process_root_csv_py Elasped Time: ", (end - start), "s\n")

def makeMarketDirectory():
	marketname = None
	if args.csv_file.endswith(".csv"):
		markename = args.csv_file[:-4]
	else:
		sys.exit("Invalid file format! File is not in csv.")

def setupColumnsForDict(csv_reader):
	first_row = next(csv_reader)
	columns_dict = {}
	for attr in COLUMNS_ATTR:
		columns_dict[attr] = first_row.index(attr)
	return columns_dict, first_row

def processCSV(csv_reader, columns_dict, header_buffer):
	row_buffer = []
	data_network_buffer = []
	lte_eci_buffer = []
	lte_enodebid_buffer = []
	current_test_type = ''
	isGatheringDataForATest = False

	for row in csv_reader:
		for test in TEST_TYPES:
			if '' in current_test_type and test in row[columns_dict["Test"]] and "Start" in row[columns_dict["Test"]]:
				current_test_type = test
				isGatheringDataForATest = True
				getData(row, row_buffer, data_network_buffer, lte_eci_buffer, lte_enodebid_buffer, columns_dict)

			elif test in current_test_type and test in row[columns_dict["Test"]] and "End" in row[columns_dict["Test"]]:
				getData(row, row_buffer, data_network_buffer, lte_eci_buffer, lte_enodebid_buffer, columns_dict)

				if "Complete" in row[columns_dict["Message"]]:
					analyzeTest(row, header_buffer, row_buffer, data_network_buffer, lte_eci_buffer, lte_enodebid_buffer, columns_dict)

				del row_buffer[:]
				del data_network_buffer[:]
				del lte_eci_buffer[:]
				del lte_enodebid_buffer[:]
				isGatheringDataForATest = False
				current_test_type = ''

			elif test in current_test_type and isGatheringDataForATest:
				getData(row, row_buffer, data_network_buffer, lte_eci_buffer, lte_enodebid_buffer, columns_dict)

def getData(row, row_buffer, data_network_buffer, lte_eci_buffer, lte_enodebid_buffer, columns_dict):
	row_buffer.append(row)
	if row[columns_dict["Data_Network_Type"]] not in data_network_buffer and row[columns_dict["Data_Network_Type"]] != '':
		data_network_buffer.append(row[columns_dict["Data_Network_Type"]])

	if row[columns_dict["LTE_eCI"]] not in lte_eci_buffer and row[columns_dict["LTE_eCI"]] != '':
		lte_eci_buffer.append(row[columns_dict["LTE_eCI"]])

	if row[columns_dict["LTE_eNB_ID"]] not in lte_enodebid_buffer and row[columns_dict["LTE_eNB_ID"]] != '':
		lte_enodebid_buffer.append(row[columns_dict["LTE_eNB_ID"]])

def analyzeTest(row, header_buffer, row_buffer, data_network_buffer, lte_eci_buffer, lte_enodebid_buffer, columns_dict):
	isGoodTest = checkTestSummary(row, columns_dict)
	hasHO = checkHO(lte_eci_buffer, lte_enodebid_buffer)
	data_network = checkDataNetwork(data_network_buffer)
	driver_id = row[columns_dict["Driver-Kit"]].replace('.','_').strip()
	test_id  = row[columns_dict["Test_Cycle_ID"]].strip()
	test_type = row[columns_dict["Test"]].replace("End", '').rstrip().replace(' ', '_')
	writeToDisk(header_buffer, row_buffer, isGoodTest, hasHO, data_network, driver_id, test_id, test_type)

def writeToDisk(header_buffer, row_buffer, isGoodTest, hasHO, data_network, driver_id, test_id, test_type):
	filename = driver_id + "_" + test_id + "_" + test_type + ".csv"
	directory_name = args.csv_file[:-4] + "/" + data_network + "/" + driver_id

	if isGoodTest:
		directory_name += "/passed"
	else:
		directory_name += "/failed"

	if hasHO:
		directory_name += "/HO/"
	else:
		directory_name += "/NO_HO/"

	directory_name += test_id + "/" + driver_id + "_" + test_id + "_" + test_type

	if not os.path.exists(directory_name):
		os.makedirs(directory_name)

	file_location = directory_name + "/" + filename

	if args.verbose:
		print("Saving file with in location = ", file_location, "\n")

	try:
		csv_file = open(file_location, 'w')
		csv_writer = csv.writer(csv_file, delimiter=',')

		isFirstRound = True
		for row in row_buffer:
			if isFirstRound:
				isFirstRound = False
				csv_writer.writerow(header_buffer)

			csv_writer.writerow(row)
	finally:
		csv_file.close()


def checkTestSummary(row, columns_dict):
	isGoodTest = True
	access_summary = 0.0
	task_summary = 0.0

	if row[columns_dict["Access_Summary"]] is not None and row[columns_dict["Access_Summary"]] or row[columns_dict["Access_Summary"]] != '':
		access_summary = float(row[columns_dict["Access_Summary"]].strip('%').strip())

	if row[columns_dict["Task_Summary"]] is not None and row[columns_dict["Task_Summary"]] or row[columns_dict["Task_Summary"]] != '':
		task_summary = float(row[columns_dict["Task_Summary"]].strip('%').strip())

	if  access_summary <= 100.0 and access_summary >= 0.0 and task_summary < 100.0:
		isGoodTest = False

	if args.verbose:
		print("isGoodTest = ", isGoodTest, ' ', access_summary, ' ', task_summary)
	return isGoodTest

def checkHO(lte_eci_buffer, lte_enodebid_buffer):
	hasHO = True

	if len(lte_eci_buffer) <= 1 and len(lte_enodebid_buffer) <= 1:
		hasHO = False

	if args.verbose:
		print("hasHO = ", hasHO, ' ', lte_eci_buffer, ' ', lte_enodebid_buffer)

	return hasHO

def checkDataNetwork(data_network_buffer):
	data_network = "Other"

	if len(data_network_buffer) == 1:
		data_network = data_network_buffer[0]

	if "Unknown" in data_network:
		data_network = "Other"

	if args.verbose:
		print("data_network = ", data_network)

	return data_network


main()
