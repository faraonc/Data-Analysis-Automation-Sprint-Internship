#Author: Conard James Faraon

"""This processes the ho report summary of the rootmetrics test summary.
See official documentation for more details."""

import threading
import csv
import glob

class HOReport(threading.Thread):

	UL = "Uplink"
	DL = "Downlink"
	DT = "Lite_Data_Test"
	ST = "Lite_Data_Secure_Test"

	INDEX_HO_FAILED = 0
	INDEX_HO_PASSED = 1
	INDEX_NO_HO_FAILED = 2
	INDEX_NO_HO_PASSED = 3

	def __init__(self, test_type, root_csv, ho_report_directory):
		print("Constructed HOReport.")
		threading.Thread.__init__(self, name=test_type)
		self.__test_type = test_type
		self.__root_csv = root_csv
		self.__ho_report_directory = ho_report_directory
		self.__devices = {}
		self.__globList = []
		device_kits = self.__findDevices()

		for kit in device_kits:
			self.__devices[kit] = [0, 0, 0, 0]

		if HOReport.UL in self.__test_type:
			self.__globList.append("Uplink")
		if HOReport.DL in self.__test_type:
			self.__globList.append("Downlink")
		if HOReport.DT in self.__test_type:
			self.__globList.append("Lite Data Test")
		if HOReport.ST in self.__test_type:
			self.__globList.append("Lite Data Secure Test")

		print("Created HOReport object to make report for = ", self.__root_csv, " ===> with test type = ", self.__test_type)
		print("Report's directory is = ", self.__ho_report_directory)
		print(self.__globList, "\n")

	def __findDevices(self):
		driver_kit_glob_path = self.__root_csv[:-4] + "/*/A-*"
		driver_kit_paths = glob.glob(driver_kit_glob_path)
		driver_kit_paths = set([path.split('/')[2] for path in driver_kit_paths])
		print("Driver kits = ", driver_kit_paths)

		return driver_kit_paths

	def run(self):
		print("Starting thread for HOReport of type = ", self.__test_type, ", using the file ", self.__root_csv)
		self.__setupTestReport()
		self.__generateTestReport()

	def __setupTestReport(self):
		try:
			root_csv_file = open(self.__root_csv,'r')
			root_csv_reader = csv.reader(root_csv_file)

			#setup indices
			self.__setupColumnIndicesForAllTestReport(root_csv_reader)

			data_network_buffer = []
			eci_buffer = []
			enodebid_buffer = []
			isGatheringDataForATest = False
			current_test_type = ''

			for row in root_csv_reader:
				for substring in self.__globList:
					if '' in current_test_type and substring in row[self.__test] and "Start" in row[self.__test]:
						current_test_type = substring
						isGatheringDataForATest = True
						if row[self.__data_network_type] not in data_network_buffer and row[self.__data_network_type] != '':
							data_network_buffer.append(row[self.__data_network_type])

						if row[self.__lte_eci] not in eci_buffer and row[self.__lte_eci] != '':
							eci_buffer.append(row[self.__lte_eci])

						if row[self.__lte_enb_id] not in enodebid_buffer and row[self.__lte_enb_id] != '':
							enodebid_buffer.append(row[self.__lte_enb_id])

					elif substring in current_test_type and substring in row[self.__test] and "End" in row[self.__test]:
						if row[self.__data_network_type] not in data_network_buffer and row[self.__data_network_type] != '':
							data_network_buffer.append(row[self.__data_network_type])

						if row[self.__lte_eci] not in eci_buffer and row[self.__lte_eci] != '':
							eci_buffer.append(row[self.__lte_eci])

						if row[self.__lte_enb_id] not in enodebid_buffer and row[self.__lte_enb_id] != '':
							enodebid_buffer.append(row[self.__lte_enb_id])

						if "Complete" in row[self.__message]:
							self.__analyzeTest(row, data_network_buffer, eci_buffer, enodebid_buffer)

						del data_network_buffer[:]
						del eci_buffer[:]
						del enodebid_buffer[:]
						isGatheringDataForATest = False
						current_test_type = ''

					elif substring in current_test_type and isGatheringDataForATest:
						if row[self.__data_network_type] not in data_network_buffer and row[self.__data_network_type] != '':
							data_network_buffer.append(row[self.__data_network_type])

						if row[self.__lte_eci] not in eci_buffer and row[self.__lte_eci] != '':
							eci_buffer.append(row[self.__lte_eci])

						if row[self.__lte_enb_id] not in enodebid_buffer and row[self.__lte_enb_id] != '':
							enodebid_buffer.append(row[self.__lte_enb_id])

		finally:
			root_csv_file.close()

	def __setupColumnIndicesForAllTestReport(self, root_csv_reader):
		first_row = next(root_csv_reader)
		self.__test = first_row.index("Test")
		self.__task_summary = first_row.index("Task_Summary")
		self.__message = first_row.index("Message")
		self.__data_network_type = first_row.index("Data_Network_Type")
		self.__driver_kit = first_row.index("Driver-Kit")
		self.__lte_eci = first_row.index("LTE_eCI")
		self.__lte_enb_id = first_row.index("LTE_eNB_ID")

	def __analyzeTest(self, row, data_network_buffer, eci_buffer, enodebid_buffer):
		#do only data that has a task summary result
		if row[self.__task_summary] != '':
			isNotPureLTE = self.__checkForOtherDataNetwork(data_network_buffer)

			if not isNotPureLTE:
				driver_kit = row[self.__driver_kit].strip().replace('.', '_')
				hasHO = False
				if len(eci_buffer) != 1 or len(enodebid_buffer) != 1:
					hasHO = True

				isFailedTest = False
				task_value = float(row[self.__task_summary].strip('%')) 
				if task_value < 100:

					isFailedTest = True

				self.__processToDeviceBin(driver_kit, isFailedTest, hasHO)

	def __checkForOtherDataNetwork(self, data_network_buffer):
		isNotPureLTE = False
		for data_network in data_network_buffer:
			if "LTE" not in data_network:
				isNotPureLTE = True
		return isNotPureLTE

	def __processToDeviceBin(self, driver_kit, isFailedTest, hasHO):
		if hasHO:
			if isFailedTest:
				self.__devices[driver_kit][HOReport.INDEX_HO_FAILED] += 1
			else:
				self.__devices[driver_kit][HOReport.INDEX_HO_PASSED] += 1
		else:
			if isFailedTest:
				self.__devices[driver_kit][HOReport.INDEX_NO_HO_FAILED] += 1
			else:
				self.__devices[driver_kit][HOReport.INDEX_NO_HO_PASSED] += 1

	def __generateTestReport(self):
		report_file_location = self.__ho_report_directory + "/" + self.__ho_report_directory + "_" + self.__test_type + ".csv"
		print("Saving " + self.__test_type +" HOReport in = ", report_file_location)
		try:
			report_file = open(report_file_location,'w')
			report_writer = csv.writer(report_file, delimiter=',')
			tmp = ["Device Kit", "Failed with HO", "Passed with HO", "Failed with NO_HO", "Passed with NO_HO"]
			report_writer.writerow(tmp)
			del tmp[:]

			for kit in self.__devices.keys():
				tmp.append(kit)
				tmp.append(self.__devices[kit][HOReport.INDEX_HO_FAILED])
				tmp.append(self.__devices[kit][HOReport.INDEX_HO_PASSED])
				tmp.append(self.__devices[kit][HOReport.INDEX_NO_HO_FAILED])
				tmp.append(self.__devices[kit][HOReport.INDEX_NO_HO_PASSED])
				report_writer.writerow(tmp)
				del tmp[:]

		finally:
			report_file.close()

