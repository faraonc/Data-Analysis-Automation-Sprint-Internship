#Author: Conard James Faraon

"""This processes the report on distribution of ran type tests by radio technology.
See official documentation for more details."""

import threading
import csv
import glob

class RANReport(threading.Thread):

	ALL = "ALL"
	UL = "Uplink"
	DL = "Downlink"
	DT = "Lite_Data_Test"
	ST = "Lite_Data_Secure_Test"

	RAN_TYPES = ["LTE", "EVDO", "eHRPD", "1xRTT", "Other"]

	INDEX_NUM_TESTS = 0
	INDEX_NUM_TASK_FAILURES = 1
	INDEX_RETS_SUM = 2

	def __init__(self, test_type, root_csv, ran_report_directory):
		print("Constructed RANReport.")
		threading.Thread.__init__(self, name=test_type)
		self.__test_type = test_type
		self.__root_csv = root_csv
		self.__ran_report_directory = ran_report_directory
		self.__rans = {}

		for ran in RANReport.RAN_TYPES:
			self.__rans[ran] = [0.0, 0.0, 0.0]

		self.__globList = []

		if RANReport.UL in self.__test_type or RANReport.ALL in self.__test_type:
			self.__globList.append("Uplink")
		if RANReport.DL in self.__test_type or RANReport.ALL in self.__test_type:
			self.__globList.append("Downlink")
		if RANReport.DT in self.__test_type or RANReport.ALL in self.__test_type:
			self.__globList.append("Lite Data Test")
		if RANReport.ST in self.__test_type or RANReport.ALL in self.__test_type:
			self.__globList.append("Lite Data Secure Test")

		print("Created RANReport object to make report for = ", self.__root_csv, " ===> with test type = ", self.__test_type)
		print("Report's directory is = ", self.__ran_report_directory)
		print(self.__globList, "\n")

	def run(self):
		print("Starting thread for RANReport of type = ", self.__test_type, ", using the file ", self.__root_csv)
		self.__setupTestReport()
		self.__generateTestReport()

	def __setupTestReport(self):
		try:
			root_csv_file = open(self.__root_csv,'r')
			root_csv_reader = csv.reader(root_csv_file)

			#setup indices
			self.__setupColumnIndicesForAllTestReport(root_csv_reader)

			data_network_buffer = []
			isGatheringDataForATest = False
			current_test_type = ''

			for row in root_csv_reader:
				for substring in self.__globList:
					if '' in current_test_type and substring in row[self.__test] and "Start" in row[self.__test]:
						current_test_type = substring
						isGatheringDataForATest = True
						if row[self.__data_network_type] not in data_network_buffer and row[self.__data_network_type] != '':
							data_network_buffer.append(row[self.__data_network_type])

					elif substring in current_test_type and substring in row[self.__test] and "End" in row[self.__test]:
						if row[self.__data_network_type] not in data_network_buffer and row[self.__data_network_type] != '':
							data_network_buffer.append(row[self.__data_network_type])

						if "Complete" in row[self.__message]:
							self.__analyzeTest(row, data_network_buffer)

						del data_network_buffer[:]
						isGatheringDataForATest = False
						current_test_type = ''

					elif substring in current_test_type and isGatheringDataForATest:
						if row[self.__data_network_type] not in data_network_buffer and row[self.__data_network_type] != '':
							data_network_buffer.append(row[self.__data_network_type])

		finally:
			root_csv_file.close()

	def __setupColumnIndicesForAllTestReport(self, root_csv_reader):
		first_row = next(root_csv_reader)
		self.__test = first_row.index("Test")
		self.__task_summary = first_row.index("Task_Summary")
		self.__message = first_row.index("Message")
		self.__data_network_type = first_row.index("Data_Network_Type")
		self.__driver_kit = first_row.index("Driver-Kit")

	def __analyzeTest(self, row, data_network_buffer):
		#do only data that has a task summary result
		if row[self.__task_summary] != '':
			ran = self.__checkForRanType(data_network_buffer,)
			if "EVDO" in ran:
				ran = "EVDO"

			task_value = float(row[self.__task_summary].strip('%')) 
			self.__rans[ran][RANReport.INDEX_NUM_TESTS] += 1
			self.__rans[ran][RANReport.INDEX_RETS_SUM] += task_value

			isFailedTest = False
			if task_value < 100:
				isFailedTest = True
				self.__rans[ran][RANReport.INDEX_NUM_TASK_FAILURES] += 1

	def __checkForRanType(self, data_network_buffer):
		ran = None
		if len(data_network_buffer) == 1:
			ran = data_network_buffer[0]
		else:
			ran = "Other"

		return ran

	def __generateTestReport(self):
		report_file_location = self.__ran_report_directory + "/" + self.__ran_report_directory + "_" + self.__test_type + ".csv"
		print("Saving " + self.__test_type +" RANReport in = ", report_file_location)
		try:
			report_file = open(report_file_location,'w')
			report_writer = csv.writer(report_file, delimiter=',')
			tmp = ["RAN Type", "# Tests", "#Tests with Task Failure", "Root Estimated Task Success %"]
			report_writer.writerow(tmp)
			del tmp[:]

			for ran in RANReport.RAN_TYPES:
				if ran == "Other":
					tmp.append(ran + " (mixed/unknown)")
				else:
					tmp.append(ran)

				tmp.append(self.__rans[ran][RANReport.INDEX_NUM_TESTS])
				tmp.append(self.__rans[ran][RANReport.INDEX_NUM_TASK_FAILURES])
				rets = 0
				if self.__rans[ran][RANReport.INDEX_NUM_TESTS] != 0:
					rets = round((self.__rans[ran][RANReport.INDEX_RETS_SUM] / self.__rans[ran][RANReport.INDEX_NUM_TESTS]), 2)

				tmp.append(rets)
				report_writer.writerow(tmp)
				del tmp[:]

		finally:
			report_file.close()

















