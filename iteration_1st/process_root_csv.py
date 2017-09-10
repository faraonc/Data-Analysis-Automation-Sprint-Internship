#usage: python3 process_root_csv.py <Root file.csv> -v
#Author: Conard James B. Faraon

"""This processess different tests from the Root csv file into specific tests that are saved in a structured directory.
See official documentation for more details."""

import argparse
import os
import time
import csv

#parse arguments here
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", help="Shows various messages from debugging and processing.", action="store_true")
parser.add_argument("csv_file", help="Root Metrics CSV File.")
args = parser.parse_args()

#constants
LTE = "LTE"
EHRPD = "eHRPD"
OTHER = "Other"
START = "Start"
END = "End"
FAILED = -1
GOOD = 0
PERCENT = '%'
HO = 1
NO_HO = 2
OTHER = 3

def main():
	try:
		start = time.time()

		if args.verbose:
			print('Started running process_root_csv.py')
			print('Root Metrics CSV = ', args.csv_file, "\n")

		#make directory for the specific market
		makeMarketDir(args.csv_file)
		csvfile = open(args.csv_file, 'r')
		csv_reader = csv.reader(csvfile)

		#prep buffer
		mylist = []
		#this is used for the first row of headers
		firstround = True

		#these are the column indices
		#make folders out of test cycle id
		test_cycle_id = 0
		test = 0

		#look for 100% or 1
		access_summary = 0

		#note that each test is unique with a test cycle id + the driver kit
		driver_kit = 0

		#look for  < 100% or 1
		task_summary = 0

		#look for LTE or eHPRD
		data_network_type = 0

		#check for multiple values for handover
		lte_eci = 0
		lte_enb_id = 0

		#buffer for header
		header = []
		databuffer = []
		#flag for failed or passed test
		goodtest = True
		id = 0
		start = False;
		network_type = ""

		#start reading csv
		for row in csv_reader:
			for cell in row:
				if firstround:
					header.append(cell)
				else:
					mylist.append(cell)

			#get header for first round
			if firstround:
				test_cycle_id = header.index("Test_Cycle_ID")
				driver_kit = header.index("Driver-Kit")
				test = header.index("Test")
				access_summary = header.index("Access_Summary")
				task_summary = header.index("Task_Summary")
				data_network_type = header.index("Data_Network_Type")
				lte_eci = header.index("LTE_eCI")
				lte_enb_id = header.index("LTE_eNB_ID")
				firstround = False

			else:

				#check the test result
				#currently the access summary should be at least 50% completed
				if mylist[access_summary] is not None and mylist[task_summary] is not None and PERCENT in mylist[access_summary] and PERCENT in mylist[task_summary]:
					temp_access_summary = float(mylist[access_summary].strip(PERCENT))/100
					temp_task_summary = float(mylist[task_summary].strip(PERCENT))/100
					if temp_access_summary <= 1.0 and temp_access_summary >= 0.1 and temp_task_summary  < 1.0:
						goodtest = False

				#tests are initially labeled with Start and ends with End
				if mylist[test] is not None:
					if START in mylist[test]:
						start = True
						databuffer.append(header)
						databuffer.append(mylist)

					elif goodtest and END in mylist[test] and start:
						start = False
						databuffer.append(mylist)
						#verify HO
						ho_flag = checkHO(databuffer, lte_eci, lte_enb_id)
						writeToDisk(databuffer, GOOD, network_type, test_cycle_id, test, ho_flag, driver_kit)
						databuffer = []

					elif not goodtest and END in mylist[test] and start:
						start = False
						databuffer.append(mylist)
						#for p in databuffer:
						#	print(p)
						#verify HO
						ho_flag = checkHO(databuffer, lte_eci, lte_enb_id)
						writeToDisk(databuffer, FAILED, network_type, test_cycle_id, test, ho_flag, driver_kit)

						#reset the test, assume a passed test
						goodtest = True
						databuffer = []

					elif start:
						#TODO check data network type for eHRPD and Other
						if network_type == "":
							network_type = identifyNetworkType(mylist, data_network_type)

						databuffer.append(mylist)

			mylist = []

		end = time.time()

		print("process_root_csv.py Elapsed Time: ", (end - start), " s\n")

	finally:
		csvfile.close()

#Makes a directory for the market.
def makeMarketDir(marketname):
	if marketname.endswith('.csv'):
		marketname = marketname[:-4]

	if not os.path.exists(marketname):
		os.makedirs(marketname)
		os.makedirs(marketname + "/LTE")
		os.makedirs(marketname + "/eHRPD")
		os.makedirs(marketname + "/Other")

		return marketname

#writes to disk
def writeToDisk(buffer, test_result, network_type, id, test, ho_flag, driver_kit):
	try:
		filename = buffer[1][id]
		if args.csv_file.endswith('.csv'):
			marketname = args.csv_file[:-4]

		if ho_flag == OTHER:
			dirname = marketname + "/Other/" + buffer[1][driver_kit].replace('.', '_') 
		else:
			dirname = marketname + "/" + network_type + "/" + buffer[1][driver_kit].replace('.', '_') 

		if network_type == LTE:
			if test_result == GOOD:
				if ho_flag == HO:
					dirname += "/passed/HO/" + filename
				elif ho_flag == NO_HO:
					dirname += "/passed/NO_HO/" + filename
				else:
					dirname += "/passed/" + filename
			else:
				#failed
				if ho_flag == HO:
					dirname += "/failed/HO/" + filename
				elif ho_flag == NO_HO:
					dirname += "/failed/NO_HO/" + filename
				else:
					dirname += "/failed/" + filename

		test_type = buffer[1][test].replace(START, '').rstrip().replace(' ', '_')

		dirname += "/" + buffer[1][driver_kit].replace('.','_') + '_' + filename + '_' + test_type

		if not os.path.exists(dirname):
			os.makedirs(dirname)

		dirname += "/" + buffer[1][driver_kit].replace('.', '_') + '_' + filename + '_' + test_type + ".csv"

		if args.verbose:
			print("Saving file with dirname = ", dirname)

		temp = open(dirname, 'w')
		writer = csv.writer(temp, delimiter=',')

		for row in buffer:
			writer.writerow(row)

	finally:
		temp.close()

def identifyNetworkType(buffer, data_network_type):
	if buffer[data_network_type] is not None and buffer[data_network_type] == LTE:
		network_type = LTE

	elif buffer[data_network_type] is not None and network_type != LTE and buffer[data_network_type] == EHRPD:
		network_type = EHRPD

	elif buffer[data_network_type] is not None and network_type != LTE and network_type != EHRPD:
		network_type = OTHER

	return network_type

#Returns: HO = 1
#Returns: NO_HO = 2
#Returns: OTHER = 3
def checkHO(buffer, lte_eci, lte_enb_id):
	eci = ""
	enb_id = ""
	firstround = True
	counterX = 0
	counterY = 0

	for row in buffer:
		if firstround:
			firstround = False
			continue

		#check for HO
		if row[lte_eci] is not None and row[lte_eci].strip():
			if eci == "" or eci == row[lte_eci]:
				eci = row[lte_eci]
				counterX+=1

			elif eci != row[lte_eci]:
				return HO

		if row[lte_enb_id] is not None and row[lte_enb_id].strip():
			if enb_id == "" or enb_id == row[lte_enb_id]:
				enb_id = row[lte_enb_id]
				counterY+=1

			elif enb_id != row[lte_enb_id]:
				return HO

	#not enough data therefore placed in a folder named "Other"
	if counterX == 1 and counterY == 1:
		return OTHER

	#no HO
	return NO_HO

main()
