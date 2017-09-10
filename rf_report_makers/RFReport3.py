#Author: Conard James Faraon

"""This processes the report summary of RF Performance bands based on LTE_RSRP.
See official documentation for more details."""

import threading
import csv
import decimal
import sys

class RFReport3(threading.Thread):
	UL = "Uplink"
	DL = "Downlink"
	DT = "Lite_Data_Test"
	ST = "Lite_Data_Secure_Test"

	EXCELLENT_RSRP = -95
	GOOD_RSRP = -105
	MARGINAL_RSRP = -115
	POOR_RSRP = -120 #anything below is bad

	EXCELLENT_SINR = 10
	GOOD_SINR = 5
	MARGINAL_SINR = 0
	POOR_SINR = -5 #anything below is bad

	BANDWIDTH = ["ALL", "25", "26", "41", "Mixed", "Unknown"]

	#TODO setup indices
	INDEX_EXCELLENT_RSRP_NUM_TEST = 0
	INDEX_EXCELLENT_RSRP_NUM_FAILED_TEST = 1
	INDEX_EXCELLENT_RSRP_ROOT_SUCCESS = 2

	INDEX_GOOD_RSRP_NUM_TEST = 3
	INDEX_GOOD_RSRP_NUM_FAILED_TEST = 4
	INDEX_GOOD_RSRP_ROOT_SUCCESS = 5

	INDEX_MARGINAL_RSRP_NUM_TEST = 6
	INDEX_MARGINAL_RSRP_NUM_FAILED_TEST = 7
	INDEX_MARGINAL_RSRP_ROOT_SUCCESS = 8

	INDEX_POOR_RSRP_NUM_TEST = 9
	INDEX_POOR_RSRP_NUM_FAILED_TEST = 10
	INDEX_POOR_RSRP_ROOT_SUCCESS = 11

	INDEX_BAD_RSRP_NUM_TEST = 12
	INDEX_BAD_RSRP_NUM_FAILED_TEST = 13
	INDEX_BAD_RSRP_ROOT_SUCCESS = 14

	#aggregate maps here
	ECI_MAP_PATH = "ecgi_maps/eci_lookup_data.csv"
	SUPPLEMENTARY_ECI_MAP_PATH = "ecgi_maps/ws_eci.csv"

	def __init__(self, test_type, csv_filename, dirname):
		threading.Thread.__init__(self, name=test_type)
		self.__test_type = test_type
		self.__csv_filename = csv_filename
		self.__dirname = dirname
		self.__globList = []
		self.__enodebid_not_found_list = []
		self.__bandDict = {}
		for band in RFReport3.BANDWIDTH:
			self.__bandDict[band] = []
			for i in range(15):
				self.__bandDict[band].append(0.0)

		if RFReport3.UL in self.__test_type:
			self.__globList.append("Uplink")
		if RFReport3.DL in self.__test_type:
			self.__globList.append("Downlink")
		if RFReport3.DT in self.__test_type:
			self.__globList.append("Lite Data Test")
		if RFReport3.ST in self.__test_type:
			self.__globList.append("Lite Data Secure Test")

		print("Created RFReport3 object to make report3 for = ", self.__csv_filename, " ===> with test type = ", self.__test_type)
		print("Report's directory is = ", self.__dirname)
		print(self.__globList, "\n")

	def run(self):
		print("Startng a thread for RFReport3 of type  = ", self.__test_type, ", using the file ", self.__csv_filename)
		print("Generating Band Report3 for = ", self.__csv_filename, " ===> with test type = ", self.__test_type)
		self.__setupAllBandReport()
		self.__mapECI()
		self.__setupSpecificBandReport()

		for band in RFReport3.BANDWIDTH:
				self.__generateReport(band)

	def __generateReportFilename(self, band):
		report_filename = self.__csv_filename[:-4] + "_" + band + "_" + self.__test_type +"_RF#3.csv"
		print("Report3 filename = ", report_filename)
		return report_filename

	def __generateReport(self, band):
		try:
			report_filename = self.__generateReportFilename(band)
			report_file_location = self.__dirname + "/" + report_filename
			report_file = open(report_file_location,'w')
			report_writer = csv.writer(report_file, delimiter=',')
			RFReport3.__writeHeader(report_writer, band)

			excellent_task_rate = 0
			good_task_rate = 0
			marginal_task_rate = 0
			poor_task_rate = 0
			bad_task_rate = 0

			if self.__bandDict[band][RFReport3.INDEX_EXCELLENT_RSRP_NUM_TEST] != 0:
				excellent_task_rate = round(decimal.Decimal(self.__bandDict[band][RFReport3.INDEX_EXCELLENT_RSRP_ROOT_SUCCESS]) / decimal.Decimal(self.__bandDict[band][RFReport3.INDEX_EXCELLENT_RSRP_NUM_TEST]), 2)

			if self.__bandDict[band][RFReport3.INDEX_GOOD_RSRP_NUM_TEST] != 0:
				good_task_rate = round(decimal.Decimal(self.__bandDict[band][RFReport3.INDEX_GOOD_RSRP_ROOT_SUCCESS]) / decimal.Decimal(self.__bandDict[band][RFReport3.INDEX_GOOD_RSRP_NUM_TEST]), 2)

			if self.__bandDict[band][RFReport3.INDEX_MARGINAL_RSRP_NUM_TEST] != 0:
				marginal_task_rate = round(decimal.Decimal(self.__bandDict[band][RFReport3.INDEX_MARGINAL_RSRP_ROOT_SUCCESS]) / decimal.Decimal(self.__bandDict[band][RFReport3.INDEX_MARGINAL_RSRP_NUM_TEST]), 2)

			if self.__bandDict[band][RFReport3.INDEX_POOR_RSRP_NUM_TEST] != 0:
				poor_task_rate = round(decimal.Decimal(self.__bandDict[band][RFReport3.INDEX_POOR_RSRP_ROOT_SUCCESS]) / decimal.Decimal(self.__bandDict[band][RFReport3.INDEX_POOR_RSRP_NUM_TEST]), 2)

			if self.__bandDict[band][RFReport3.INDEX_BAD_RSRP_NUM_TEST] != 0:
				bad_task_rate = round(decimal.Decimal(self.__bandDict[band][RFReport3.INDEX_BAD_RSRP_ROOT_SUCCESS]) / decimal.Decimal(self.__bandDict[band][RFReport3.INDEX_BAD_RSRP_NUM_TEST]), 2)

			tmp_buffer = []
			tmp_buffer.append("Excellent, AVE RSRP > -95")
			tmp_buffer.append(self.__bandDict[band][RFReport3.INDEX_EXCELLENT_RSRP_NUM_TEST])
			tmp_buffer.append(self.__bandDict[band][RFReport3.INDEX_EXCELLENT_RSRP_NUM_FAILED_TEST])
			tmp_buffer.append(excellent_task_rate)
			report_writer.writerow(tmp_buffer)
			del tmp_buffer[:]

			tmp_buffer.append("Good, AVE RSRP (-105,-95]")
			tmp_buffer.append(self.__bandDict[band][RFReport3.INDEX_GOOD_RSRP_NUM_TEST])
			tmp_buffer.append(self.__bandDict[band][RFReport3.INDEX_GOOD_RSRP_NUM_FAILED_TEST])
			tmp_buffer.append(good_task_rate)
			report_writer.writerow(tmp_buffer)
			del tmp_buffer[:]

			tmp_buffer.append("Marginal, AVE RSRP (-115,-105]")
			tmp_buffer.append(self.__bandDict[band][RFReport3.INDEX_MARGINAL_RSRP_NUM_TEST])
			tmp_buffer.append(self.__bandDict[band][RFReport3.INDEX_MARGINAL_RSRP_NUM_FAILED_TEST])
			tmp_buffer.append(marginal_task_rate)
			report_writer.writerow(tmp_buffer)
			del tmp_buffer[:]

			tmp_buffer.append("Poor, AVE RSRP (-120,-115]")
			tmp_buffer.append(self.__bandDict[band][RFReport3.INDEX_POOR_RSRP_NUM_TEST])
			tmp_buffer.append(self.__bandDict[band][RFReport3.INDEX_POOR_RSRP_NUM_FAILED_TEST])
			tmp_buffer.append(poor_task_rate)
			report_writer.writerow(tmp_buffer)
			del tmp_buffer[:]

			tmp_buffer.append("Bad, AVE RSRP <= -120")
			tmp_buffer.append(self.__bandDict[band][RFReport3.INDEX_BAD_RSRP_NUM_TEST])
			tmp_buffer.append(self.__bandDict[band][RFReport3.INDEX_BAD_RSRP_NUM_FAILED_TEST])
			tmp_buffer.append(bad_task_rate)
			report_writer.writerow(tmp_buffer)
			del tmp_buffer[:]

		finally:
			report_file.close()

	def __writeHeader(report_writer, band):
		header = []
		if band is "ALL":
			header.append("All LTE Coverage Bands")
		elif band == "Mixed":
			header.append("Mixed Band Coverage")
		elif band == "Unknown":
			header.append("Unknown Band Coverage")
		else:
			header.append("B" + band.strip() + " Coverage")

		header.append("# Tests")
		header.append("# Tests with Task Failure")
		header.append("# Root Estimated Task Success %")
		report_writer.writerow(header)

	def __setupAllBandReport(self):
		try:
			root_csv_file = open(self.__csv_filename,'r')
			root_csv_reader = csv.reader(root_csv_file)

			#setup indices
			self.__setupColumnIndicesForAllBand(root_csv_reader)
			lte_rsrp_buffer = []
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

						lte_rsrp_buffer.append(row[self.__lte_rsrp])

					elif substring in current_test_type and substring in row[self.__test] and "End" in row[self.__test]:
						lte_rsrp_buffer.append(row[self.__lte_rsrp])

						if row[self.__data_network_type] not in data_network_buffer and row[self.__data_network_type] != '':
							data_network_buffer.append(row[self.__data_network_type])

						if "Complete" in row[self.__message]:
							self.__analyzeTest("ALL", row, lte_rsrp_buffer, data_network_buffer)

						del data_network_buffer[:]
						del lte_rsrp_buffer[:]
						isGatheringDataForATest = False
						current_test_type = ''

					elif substring in current_test_type and isGatheringDataForATest:
						if row[self.__data_network_type] not in data_network_buffer and row[self.__data_network_type] != '':
							data_network_buffer.append(row[self.__data_network_type])

						lte_rsrp_buffer.append(row[self.__lte_rsrp])
		finally:
			root_csv_file.close()

	def __setupColumnIndicesForAllBand(self, root_csv_reader):
		first_row = next(root_csv_reader)
		self.__test = first_row.index("Test")
		self.__task_summary = first_row.index("Task_Summary")
		self.__lte_rsrp = first_row.index("LTE_RSRP")
		self.__message = first_row.index("Message")
		self.__lte_eci = first_row.index("LTE_eCI")
		self.__lte_enb_id = first_row.index("LTE_eNB_ID")
		self.__data_network_type = first_row.index("Data_Network_Type")

	def __analyzeTest(self, band, row, lte_rsrp_buffer, data_network_buffer):
		#do only data that has a task summary result
		if row[self.__task_summary] != '':
			isNotPureLTE = self.__checkForOtherDataNetwork(data_network_buffer)

			if not isNotPureLTE:
				lte_rsrp_buffer = [float(rsrp) for rsrp in lte_rsrp_buffer if rsrp != '']
				rsrp_average  = round(sum(lte_rsrp_buffer) / len(lte_rsrp_buffer), 2)
				isFailedTest = False
				task_value = float(row[self.__task_summary].strip('%')) 
				if task_value < 100:
					isFailedTest = True

				self.__processToBin(band, rsrp_average, task_value, isFailedTest)

	def __checkForOtherDataNetwork(self, data_network_buffer):
		isNotPureLTE = False
		for data_network in data_network_buffer:
			if "LTE" not in data_network:
				isNotPureLTE = True;
		return isNotPureLTE

	def __processToBin(self, band, rsrp_average, task_value, isFailedTest):
		if rsrp_average > RFReport3.EXCELLENT_RSRP: #excellent bin > -95
			self.__bandDict[band][RFReport3.INDEX_EXCELLENT_RSRP_NUM_TEST] += 1
			self.__bandDict[band][RFReport3.INDEX_EXCELLENT_RSRP_ROOT_SUCCESS] += task_value
			if isFailedTest:
				self.__bandDict[band][RFReport3.INDEX_EXCELLENT_RSRP_NUM_FAILED_TEST] += 1

		elif rsrp_average > RFReport3.GOOD_RSRP and rsrp_average <= RFReport3.EXCELLENT_RSRP: #good bin (-105, -95]
			self.__bandDict[band][RFReport3.INDEX_GOOD_RSRP_NUM_TEST] += 1
			self.__bandDict[band][RFReport3.INDEX_GOOD_RSRP_ROOT_SUCCESS] += task_value
			if isFailedTest:
				self.__bandDict[band][RFReport3.INDEX_GOOD_RSRP_NUM_FAILED_TEST] += 1

		elif rsrp_average > RFReport3.MARGINAL_RSRP and rsrp_average <= RFReport3.GOOD_RSRP: #marginal bin (-115, -105]
			self.__bandDict[band][RFReport3.INDEX_MARGINAL_RSRP_NUM_TEST] += 1
			self.__bandDict[band][RFReport3.INDEX_MARGINAL_RSRP_ROOT_SUCCESS] += task_value
			if isFailedTest:
				self.__bandDict[band][RFReport3.INDEX_MARGINAL_RSRP_NUM_FAILED_TEST] +=1

		elif rsrp_average > RFReport3.POOR_RSRP and rsrp_average <= RFReport3.MARGINAL_RSRP: #poor bin (-120, -115]
			self.__bandDict[band][RFReport3.INDEX_POOR_RSRP_NUM_TEST] += 1
			self.__bandDict[band][RFReport3.INDEX_POOR_RSRP_ROOT_SUCCESS] += task_value
			if isFailedTest:
				self.__bandDict[band][RFReport3.INDEX_POOR_RSRP_NUM_FAILED_TEST] +=1

		elif rsrp_average <= RFReport3.POOR_RSRP: #bad bin <= -120
			self.__bandDict[band][RFReport3.INDEX_BAD_RSRP_NUM_TEST] += 1
			self.__bandDict[band][RFReport3.INDEX_BAD_RSRP_ROOT_SUCCESS] += task_value
			if isFailedTest:
				self.__bandDict[band][RFReport3.INDEX_BAD_RSRP_NUM_FAILED_TEST] +=1

	def __mapECI(self):
		self.__eci_dict = {}
		try:
			eci_map_file = open(RFReport3.ECI_MAP_PATH,'r')
			eci_map_reader = csv.reader(eci_map_file)
			self.__setupColumnIndicesForEciMap(eci_map_reader)

			for row in eci_map_reader:
				key = row[self.__eci_map].strip()
				if key in self.__eci_dict and row[self.__band].strip() != self.__eci_dict[key]:
					print("Colission in self.__eci_dict with key = ", key, " and band = ", row[self.__band].strip(), " self.__eci_dict[key] = ", self.__eci_dict[key])
					continue
				elif row[self.__band].strip() != '':
					self.__eci_dict[key] = row[self.__band].strip()

			#TODO better way to integrate supplementary mapping
			supplementary_eci_map_file = open(RFReport3.SUPPLEMENTARY_ECI_MAP_PATH,'r')
			supplementary_eci_map_reader = csv.reader(supplementary_eci_map_file)
			self.__setupColumnIndicesforSupplementaryMap(supplementary_eci_map_reader)

			for row in supplementary_eci_map_reader:
				key = row[self.__supp_eci].strip()
				if key in self.__eci_dict and row[self.__supp_band].strip() != self.__eci_dict[key]:
					print("Colission in self.__eci_dict with key = ", key, " and band = ", row[self.__supp_band].strip(), " self.__eci_dict[key] = ", self.__eci_dict[key])
					continue
				elif row[self.__supp_band].strip() != '' and row[self.__supp_band].strip() != "Not Found":
					self.__eci_dict[key] = row[self.__supp_band].strip()

		finally:
			eci_map_file.close()
			supplementary_eci_map_file.close()

	def __setupColumnIndicesForEciMap(self, eci_map_reader):
		first_row = next(eci_map_reader)
		self.__market = first_row.index("Market")
		self.__vendor = first_row.index("VENDOR")
		self.__enodebid = first_row.index("Enodebid")
		self.__band = first_row.index("Band")
		self.__eci_map = first_row.index("ECI")

	def __setupColumnIndicesforSupplementaryMap(self, supplementary_eci_map_reader):
		first_row = next(supplementary_eci_map_reader)
		self.__supp_eci = first_row.index("LTE_eCI")
		self.__supp_band = first_row.index("Band")

	def __setupSpecificBandReport(self):
		try:
			root_csv_file = open(self.__csv_filename, 'r')
			root_csv_reader = csv.reader(root_csv_file)
			lte_rsrp_buffer = []
			eci_buffer = []
			data_network_buffer = []
			isGatheringDataForATest = False
			current_test_type = ''
			isFirstRound = True

			for row in root_csv_reader:
				if isFirstRound:
					isFirstRound = False
					continue

				for substring in self.__globList:
					if '' in current_test_type and substring in row[self.__test] and "Start" in row[self.__test]:
						current_test_type = substring
						isGatheringDataForATest = True
						eci_buffer.append(row[self.__lte_eci])
						if row[self.__data_network_type] not in data_network_buffer and row[self.__data_network_type] != '':
							data_network_buffer.append(row[self.__data_network_type])
						lte_rsrp_buffer.append(row[self.__lte_rsrp])

					elif substring in current_test_type and substring in row[self.__test] and "End" in row[self.__test]:
						lte_rsrp_buffer.append(row[self.__lte_rsrp])
						if row[self.__data_network_type] not in data_network_buffer and row[self.__data_network_type] != '':
							data_network_buffer.append(row[self.__data_network_type])
						eci_buffer.append(row[self.__lte_eci])

						if "Complete" in row[self.__message]:
							self.__analyzeSpecificBand(row, eci_buffer, data_network_buffer, lte_rsrp_buffer)

						isGatheringDataForATest = False
						current_test_type = ''
						del eci_buffer[:]
						del data_network_buffer[:]
						del lte_rsrp_buffer[:]

					elif substring in current_test_type and isGatheringDataForATest:
						if row[self.__data_network_type] not in data_network_buffer and row[self.__data_network_type] != '':
							data_network_buffer.append(row[self.__data_network_type])
						eci_buffer.append(row[self.__lte_eci])
						lte_rsrp_buffer.append(row[self.__lte_rsrp])

		finally:
			root_csv_file.close()

	def __analyzeSpecificBand(self, row, eci_buffer, data_network_buffer, lte_rsrp_buffer):
		eci_buffer = [enode for enode in eci_buffer if enode != '']
		isMixed, band, isSetOfNoId = self.__checkBand(eci_buffer)

		if isSetOfNoId:
			self.__analyzeTest("Unknown", row, lte_rsrp_buffer, data_network_buffer)
		else:
			if isMixed:
				self.__analyzeTest("Mixed", row, lte_rsrp_buffer, data_network_buffer)
			elif not isMixed:
				self.__analyzeTest(str(band), row, lte_rsrp_buffer, data_network_buffer)

	def __checkBand(self, eci_buffer):
		isMixed = False
		isSetOfNoId = False
		prev_band = -1

		band_list = []
		for enode in eci_buffer:
			band = self.__eci_dict.get(enode)
			if band is not None:
				band_list.append(band)
			else:
				if enode not in self.__enodebid_not_found_list:
					self.__enodebid_not_found_list.append(enode)

		if len(band_list) == 0:
			isSetOfNoId = True
		else:
			isSame = RFReport3.__checkEqual(band_list)
			if not isSame:
				isMixed = True
			else:
				prev_band = band_list[0]

		return isMixed, prev_band, isSetOfNoId 

	def __checkEqual(lst):
		return lst[1:] == lst[:-1]

