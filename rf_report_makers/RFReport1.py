#Author: Conard James Faraon

"""This processes the report summary of RF Performance.
See official documentation for more details."""

import threading
import csv
import decimal
import sys

class RFReport1(threading.Thread):
	UL = "Uplink"
	DL = "Downlink"
	DT = "Lite_Data_Test"
	ST = "Lite_Data_Secure_Test"

	EXCELLENT_RSRP = -95.0
	GOOD_RSRP = -105.0
	MARGINAL_RSRP = -115.0
	POOR_RSRP = -120.0 #anything below is bad
	EXCELLENT_SINR = 10.0
	GOOD_SINR = 5.0
	MARGINAL_SINR = 0.0
	POOR_SINR = -5.0 #anything below is bad

	INDEX__numTestWithGoodRF = 0
	INDEX__numTestFailedWithGoodRF = 1
	INDEX__rootEstTaskSuccessWithGoodRF = 2
	INDEX__numTestWithBadRF = 3
	INDEX__numTestFailedWithBadRF = 4
	INDEX__rootEstTaskSuccessWithBadRF = 5

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
		#fields for all bands
		self.__numTestWithGoodRF = 0
		self.__numTestFailedWithGoodRF = 0
		self.__rootEstTaskSuccessWithGoodRF = 0
		self.__rootEstTaskSuccessWithGoodRFMean = 0
		self.__numTestWithBadRF = 0
		self.__numTestFailedWithBadRF = 0
		self.__rootEstTaskSuccessWithBadRF = 0
		self.__rootEstTaskSuccessWithBadRFMean = 0
		#end of fields for all bands
		self.__bandDict = {}
		self.__bandDict["25"] = [0, 0, 0, 0, 0, 0]
		self.__bandDict["26"] = [0, 0, 0, 0, 0, 0]
		self.__bandDict["41"] = [0, 0, 0, 0, 0, 0]
		self.__bandDict["Mixed"] = [0, 0, 0, 0, 0, 0] #mixed bandwidth for LTE ONLY
		self.__bandDict["Unknown"] = [0, 0, 0, 0, 0, 0]
		self.__bandDict["Varied"] = [0, 0, 0, 0, 0, 0] #mixed networks ONLY [LTE, eHRPD, Unknown, etc]

		if RFReport1.UL in self.__test_type:
			self.__globList.append("Uplink")
		if RFReport1.DL in self.__test_type:
			self.__globList.append("Downlink")
		if RFReport1.DT in self.__test_type:
			self.__globList.append("Lite Data Test")
		if RFReport1.ST in self.__test_type:
			self.__globList.append("Lite Data Secure Test")

		print("Created RFReport1 object to make report1 for = ", self.__csv_filename, " ===> with test type = ", self.__test_type)
		print("Report's directory is = ", self.__dirname)
		print(self.__globList, "\n")
		self.__goodRFCountIfNotFound = 0
		self.__badRFCountIfNotFound = 0

	def run(self):
		print("Starting thread for RFReport1 of type = ", self.__test_type, ", using the file ", self.__csv_filename)
		try:
			#filenames
			b25_goodRF_filename = self.__dirname + "/records/" + self.__csv_filename[:-4] + "_B-25_" + self.__test_type + "_GOOD_RF#1.csv"
			b26_goodRF_filename = self.__dirname + "/records/" + self.__csv_filename[:-4] + "_B-26_" + self.__test_type + "_GOOD_RF#1.csv"
			b41_goodRF_filename = self.__dirname + "/records/" + self.__csv_filename[:-4] + "_B-41_" + self.__test_type + "_GOOD_RF#1.csv"
			bMixed_goodRF_filename = self.__dirname + "/records/" + self.__csv_filename[:-4] + "_B-Mixed_" + self.__test_type + "_GOOD_RF#1.csv"
			noMapping_goodRF_filename = self.__dirname + "/records/" +self.__csv_filename[:-4] + "_ECI_NOT_FOUND_" + self.__test_type + "_GOOD_RF#1.csv"

			b25_badRF_filename = self.__dirname + "/records/" + self.__csv_filename[:-4] + "_B-25_" + self.__test_type + "_BELOW_RF#1.csv"
			b26_badRF_filename = self.__dirname + "/records/" + self.__csv_filename[:-4] + "_B-26_" + self.__test_type + "_BELOW_RF#1.csv"
			b41_badRF_filename = self.__dirname + "/records/" + self.__csv_filename[:-4] + "_B-41_" + self.__test_type + "_BELOW_RF#1.csv"
			bMixed_badRF_filename = self.__dirname + "/records/" + self.__csv_filename[:-4] + "_B-Mixed_" + self.__test_type + "_BELOW_RF#1.csv"
			noMapping_badRF_filename = self.__dirname + "/records/" +self.__csv_filename[:-4] + "_ECI_NOT_FOUND_" + self.__test_type + "_BELOW_RF#1.csv"

			#files
			self.__b25_goodRF_file = open(b25_goodRF_filename,'w')
			self.__b26_goodRF_file = open(b26_goodRF_filename,'w')
			self.__b41_goodRF_file = open(b41_goodRF_filename,'w')
			self.__bMixed_goodRF_file = open(bMixed_goodRF_filename,'w')
			self.__noMapping_goodRF_file = open(noMapping_goodRF_filename,'w')

			self.__b25_badRF_file = open(b25_badRF_filename,'w')
			self.__b26_badRF_file = open(b26_badRF_filename,'w')
			self.__b41_badRF_file = open(b41_badRF_filename,'w')
			self.__bMixed_badRF_file = open(bMixed_badRF_filename,'w')
			self.__noMapping_badRF_file = open(noMapping_badRF_filename,'w')

			#writers
			self.__b25_goodRF_writer = csv.writer(self.__b25_goodRF_file,delimiter=",")
			self.__b26_goodRF_writer = csv.writer(self.__b26_goodRF_file,delimiter=",")
			self.__b41_goodRF_writer = csv.writer(self.__b41_goodRF_file,delimiter=",")
			self.__bMixed_goodRF_writer = csv.writer(self.__bMixed_goodRF_file,delimiter=",")
			self.__noMapping_goodRF_writer = csv.writer(self.__noMapping_goodRF_file,delimiter=",")

			self.__b25_badRF_writer = csv.writer(self.__b25_badRF_file,delimiter=",")
			self.__b26_badRF_writer = csv.writer(self.__b26_badRF_file,delimiter=",")
			self.__b41_badRF_writer = csv.writer(self.__b41_badRF_file,delimiter=",")
			self.__bMixed_badRF_writer = csv.writer(self.__bMixed_badRF_file,delimiter=",")
			self.__noMapping_badRF_writer = csv.writer(self.__noMapping_badRF_file,delimiter=",")

			self.__generateAllBandReportFilename()
			self.__generateAllBandReport()
			self.__mapECI()
			self.__generateSpecificBandReport()
			self.__generateSpecificVariedReportIntoFiles("Varied")
			print("self.__goodRFCountIfNotFound = ", self.__goodRFCountIfNotFound)
			print("self.__badRFCountIfNotFound = ", self.__badRFCountIfNotFound)

		finally:

			self.__b25_goodRF_file.close()
			self.__b26_goodRF_file.close()
			self.__b41_goodRF_file.close()
			self.__bMixed_goodRF_file.close()
			self.__noMapping_goodRF_file.close()

			self.__b25_badRF_file.close()
			self.__b26_badRF_file.close()
			self.__b41_badRF_file.close()
			self.__bMixed_badRF_file.close()
			self.__noMapping_badRF_file.close()

	def __writeLogHeader(self, row):
		self.__b25_goodRF_writer.writerow(row)
		self.__b26_goodRF_writer.writerow(row)
		self.__b41_goodRF_writer.writerow(row)
		self.__bMixed_goodRF_writer.writerow(row)
		self.__noMapping_goodRF_writer.writerow(row)

		self.__b25_badRF_writer.writerow(row)
		self.__b26_badRF_writer.writerow(row)
		self.__b41_badRF_writer.writerow(row)
		self.__bMixed_badRF_writer.writerow(row)
		self.__noMapping_badRF_writer.writerow(row)

	def __generateAllBandReportFilename(self):
		self.__reportAllBandFilename = self.__csv_filename[:-4] + "_ALL_BAND_" + self.__test_type +"_RF#1.csv"
		print("Report1 filename = ", self.__reportAllBandFilename )

	def __generateAllBandReport(self):
		print("Generating Band Report1 for = ", self.__csv_filename, " ===> with test type = ", self.__test_type)
		try:
			root_csv_file = open(self.__csv_filename,'r')
			root_csv_reader = csv.reader(root_csv_file)
			report_file_location = self.__dirname + "/" + self.__reportAllBandFilename
			report_file = open(report_file_location,'w')
			report_writer = csv.writer(report_file, delimiter=',')
			RFReport1.__writeHeader(report_writer, None)

			#setup indices
			self.__setupColumnIndicesForAllBand(root_csv_reader)

			lte_rsrp_buffer = []
			lte_rssnr_buffer = []
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
						lte_rssnr_buffer.append(row[self.__lte_rssnr])

					elif substring in current_test_type and substring in row[self.__test] and "End" in row[self.__test]:
						lte_rsrp_buffer.append(row[self.__lte_rsrp])
						lte_rssnr_buffer.append(row[self.__lte_rssnr])

						if row[self.__data_network_type] not in data_network_buffer and row[self.__data_network_type] != '':
							data_network_buffer.append(row[self.__data_network_type])

						if "Complete" in row[self.__message]:
							self.__analyzeBand(row, lte_rsrp_buffer, lte_rssnr_buffer, data_network_buffer)

						del data_network_buffer[:]
						del lte_rsrp_buffer[:]
						del lte_rssnr_buffer[:]
						isGatheringDataForATest = False
						current_test_type = ''

					elif substring in current_test_type and isGatheringDataForATest:
						if row[self.__data_network_type] not in data_network_buffer and row[self.__data_network_type] != '':
							data_network_buffer.append(row[self.__data_network_type])

						lte_rsrp_buffer.append(row[self.__lte_rsrp])
						lte_rssnr_buffer.append(row[self.__lte_rssnr])

			if self.__numTestWithGoodRF != 0:
				self.__rootEstTaskSuccessWithGoodRFMean = round(decimal.Decimal(self.__rootEstTaskSuccessWithGoodRF) / decimal.Decimal(self.__numTestWithGoodRF), 2)
			if self.__numTestWithBadRF != 0:
				self.__rootEstTaskSuccessWithBadRFMean = round(decimal.Decimal(self.__rootEstTaskSuccessWithBadRF) / decimal.Decimal(self.__numTestWithBadRF), 2)

			print("\nGenerating ALL band report = ", self.__reportAllBandFilename, "\n")
			tmp_buffer = []
			tmp_buffer.append("Good RF")
			tmp_buffer.append(self.__numTestWithGoodRF)
			tmp_buffer.append(self.__numTestFailedWithGoodRF)
			tmp_buffer.append(self.__rootEstTaskSuccessWithGoodRFMean)
			report_writer.writerow(tmp_buffer)
			del tmp_buffer[:]
			tmp_buffer.append("Below Good RF")
			tmp_buffer.append(self.__numTestWithBadRF)
			tmp_buffer.append(self.__numTestFailedWithBadRF)
			tmp_buffer.append(self.__rootEstTaskSuccessWithBadRFMean)
			report_writer.writerow(tmp_buffer)

		finally:
			root_csv_file.close()
			report_file.close()

	def __setupColumnIndicesForAllBand(self, root_csv_reader):
		first_row = next(root_csv_reader)
		self.__test = first_row.index("Test")
		self.__task_summary = first_row.index("Task_Summary")
		self.__lte_rsrp = first_row.index("LTE_RSRP")
		self.__lte_rssnr = first_row.index("LTE_RSSNR")
		self.__message = first_row.index("Message")
		self.__lte_eci = first_row.index("LTE_eCI")
		self.__lte_enb_id = first_row.index("LTE_eNB_ID")
		self.__data_network_type = first_row.index("Data_Network_Type")

	def __writeHeader(report_writer, band):
		header = []
		if band is None:
			header.append("All LTE Coverage Bands")
		elif band == "Mixed":
			header.append("Mixed Band Coverage")
		elif band == "Unknown":
			header.append("Unknown Band Coverage")
		elif band == "Varied":
			header.append("Varied Network Coverage (LTE/Non-LTE)")
		else:
			header.append("B" + band.strip() + " Coverage")

		header.append("# Tests")
		header.append("# Tests with Task Failure")
		header.append("# Root Estimated Task Success %")
		report_writer.writerow(header)

	def __analyzeBand(self, row, lte_rsrp_buffer, lte_rssnr_buffer, data_network_buffer):
		#do only data that has a task summary result
		if row[self.__task_summary] != '':
			notPureLTE = self.__checkForOtherDataNetwork(data_network_buffer)
			lte_rsrp_buffer = [float(rsrp) for rsrp in lte_rsrp_buffer if rsrp != '']
			lte_rssnr_buffer = [float(rssnr) for rssnr in lte_rssnr_buffer if rssnr != '']

			isGoodRF = True
			for rsrp,rssnr in zip(lte_rsrp_buffer, lte_rssnr_buffer):
				if rsrp <= RFReport1.GOOD_RSRP or rssnr <= RFReport1.GOOD_SINR:
					isGoodRF = False

			#place data in the proper bin
			if not notPureLTE:
				#passed and failed tests
				if isGoodRF:
					self.__numTestWithGoodRF += 1
					self.__rootEstTaskSuccessWithGoodRF += float(row[self.__task_summary].strip('%'))
				else:
					self.__numTestWithBadRF += 1
					self.__rootEstTaskSuccessWithBadRF += float(row[self.__task_summary].strip('%'))

				#failed tests only
				if float(row[self.__task_summary].strip('%')) < 100:
					if isGoodRF:
						self.__numTestFailedWithGoodRF += 1
					else:
						self.__numTestFailedWithBadRF += 1
			else:
				self.__bandDict["Varied"][RFReport1.INDEX__numTestWithGoodRF] += 1
				self.__bandDict["Varied"][RFReport1.INDEX__rootEstTaskSuccessWithGoodRF] += float(row[self.__task_summary].strip('%'))

				#failed tests only
				if float(row[self.__task_summary].strip('%')) < 100:
					self.__bandDict["Varied"][RFReport1.INDEX__numTestFailedWithGoodRF] += 1
					
	def __mapECI(self):
		self.__eci_dict = {}
		try:
			eci_map_file = open(RFReport1.ECI_MAP_PATH,'r')
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
			supplementary_eci_map_file = open(RFReport1.SUPPLEMENTARY_ECI_MAP_PATH,'r')
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

	def __generateSpecificBandReport(self):
		try:
			root_csv_file = open(self.__csv_filename,'r')
			root_csv_reader = csv.reader(root_csv_file)
			row_buffer_for_a_single_test = [] 
			lte_rsrp_buffer = []
			lte_rssnr_buffer = []
			eci_buffer = []
			data_network_buffer = []
			isGatheringDataForATest = False
			current_test_type = ''
			isFirstRound = True

			for row in root_csv_reader:
				if isFirstRound:
					self.__header = row
					self.__writeLogHeader(row)
					isFirstRound = False
					continue

				for substring in self.__globList:
					if '' in current_test_type and substring in row[self.__test] and "Start" in row[self.__test]:
						row_buffer_for_a_single_test.append(row)
						current_test_type = substring
						isGatheringDataForATest = True
						eci_buffer.append(row[self.__lte_eci])
						if row[self.__data_network_type] not in data_network_buffer and row[self.__data_network_type] != '':
							data_network_buffer.append(row[self.__data_network_type])
						lte_rsrp_buffer.append(row[self.__lte_rsrp])
						lte_rssnr_buffer.append(row[self.__lte_rssnr])

					elif substring in current_test_type and substring in row[self.__test] and "End" in row[self.__test]:
						row_buffer_for_a_single_test.append(row)
						lte_rsrp_buffer.append(row[self.__lte_rsrp])
						lte_rssnr_buffer.append(row[self.__lte_rssnr])
						if row[self.__data_network_type] not in data_network_buffer and row[self.__data_network_type] != '':
							data_network_buffer.append(row[self.__data_network_type])

						eci_buffer.append(row[self.__lte_eci])

						if "Complete" in row[self.__message]:
							self.__analyzeSpecificBand(row, eci_buffer, data_network_buffer, lte_rsrp_buffer, lte_rssnr_buffer, row_buffer_for_a_single_test)

						isGatheringDataForATest = False
						current_test_type = ''
						del eci_buffer[:]
						del data_network_buffer[:]
						del lte_rsrp_buffer[:]
						del lte_rssnr_buffer[:]
						del row_buffer_for_a_single_test[:]

					elif substring in current_test_type and isGatheringDataForATest:
						row_buffer_for_a_single_test.append(row)
						if row[self.__data_network_type] not in data_network_buffer and row[self.__data_network_type] != '':
							data_network_buffer.append(row[self.__data_network_type])
						eci_buffer.append(row[self.__lte_eci])
						lte_rsrp_buffer.append(row[self.__lte_rsrp])
						lte_rssnr_buffer.append(row[self.__lte_rssnr])

		finally:
			root_csv_file.close()

		if len(self.__enodebid_not_found_list) != 0:
			try:
				enodebid_not_in_map_file = open(self.__dirname + "/records/" +self.__csv_filename[:-4] + "_ECI_NOT_FOUND_" + self.__test_type + ".txt",'w')
				self.__writeLogFileForEnodebidNotFound(enodebid_not_in_map_file)
			finally:
				enodebid_not_in_map_file.close()

		self.__generateSpecificBandReportIntoFiles("Mixed")
		self.__generateSpecificBandReportIntoFiles("25")
		self.__generateSpecificBandReportIntoFiles("26")
		self.__generateSpecificBandReportIntoFiles("41")
		self.__generateSpecificBandReportIntoFiles("Unknown")

	def __analyzeSpecificBand(self, row, eci_buffer, data_network_buffer, lte_rsrp_buffer, lte_rssnr_buffer, row_buffer_for_a_single_test):
		eci_buffer = [enode for enode in eci_buffer if enode != '']
		notPureLTE = self.__checkForOtherDataNetwork(data_network_buffer)

		if not notPureLTE:
			isMixed, band, isSetOfNoId = self.__checkBand(eci_buffer)

			if isSetOfNoId:
				self.__processSetOfNoId(row, lte_rsrp_buffer, lte_rssnr_buffer, row_buffer_for_a_single_test)
			else:
				if isMixed:
					self.__processSpecifictBand("Mixed", row, lte_rsrp_buffer, lte_rssnr_buffer, row_buffer_for_a_single_test)
				elif not isMixed:
					self.__processSpecifictBand(str(band), row, lte_rsrp_buffer, lte_rssnr_buffer, row_buffer_for_a_single_test)

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
			isSame = RFReport1.__checkEqual(band_list)
			if not isSame:
				isMixed = True
			else:
				prev_band = band_list[0]

		return isMixed, prev_band, isSetOfNoId 

	def __checkEqual(lst):
		return lst[1:] == lst[:-1]

	def __writeLogFileForEnodebidNotFound(self, enodebid_not_in_map_file):
		print("\nWriting a log file for enodebid not found.\n")
		for enode in self.__enodebid_not_found_list:
			enodebid_not_in_map_file.write(enode + "\n")

		enodebid_not_in_map_file.write("# of LTE with good RF not found from ecgi mapping = " + str(self.__goodRFCountIfNotFound))
		enodebid_not_in_map_file.write("\n")
		enodebid_not_in_map_file.write("# of LTE with BELOW good RF not found from ecgi mapping = " + str(self.__badRFCountIfNotFound))

	def __checkForOtherDataNetwork(self, data_network_buffer):
		notPureLTE = False
		for data_network in data_network_buffer:
			if "LTE" not in data_network:
				notPureLTE = True;
		return notPureLTE

	def __processSetOfNoId(self, row, lte_rsrp_buffer, lte_rssnr_buffer, row_buffer_for_a_single_test):
		if row[self.__task_summary] != '':
			lte_rsrp_buffer = [float(rsrp) for rsrp in lte_rsrp_buffer if rsrp != '']
			lte_rssnr_buffer = [float(rssnr) for rssnr in lte_rssnr_buffer if rssnr != '']

			isGoodRF = True
			for rsrp,rssnr in zip(lte_rsrp_buffer, lte_rssnr_buffer):
				if rsrp <= RFReport1.GOOD_RSRP or rssnr <= RFReport1.GOOD_SINR:
					isGoodRF = False

			#passed and failed tests
			if isGoodRF:
				self.__goodRFCountIfNotFound += 1
				for line in row_buffer_for_a_single_test:
					self.__noMapping_goodRF_writer.writerow(line)
				space = ['']
				self.__noMapping_goodRF_writer.writerow(space)
				self.__bandDict["Unknown"][RFReport1.INDEX__numTestWithGoodRF] += 1
				self.__bandDict["Unknown"][RFReport1.INDEX__rootEstTaskSuccessWithGoodRF] += float(row[self.__task_summary].strip('%'))
			else:
				self.__badRFCountIfNotFound += 1
				for line in row_buffer_for_a_single_test:
					self.__noMapping_badRF_writer.writerow(line)
				space = ['']
				self.__noMapping_badRF_writer.writerow(space)
				self.__bandDict["Unknown"][RFReport1.INDEX__numTestWithBadRF] += 1
				self.__bandDict["Unknown"][RFReport1.INDEX__rootEstTaskSuccessWithBadRF] += float(row[self.__task_summary].strip('%'))

			#failed tests only
			if float(row[self.__task_summary].strip('%')) < 100:
				if isGoodRF:
					self.__bandDict["Unknown"][RFReport1.INDEX__numTestFailedWithGoodRF] += 1
				else:
					self.__bandDict["Unknown"][RFReport1.INDEX__numTestFailedWithBadRF] += 1

	def __processSpecifictBand(self, band, row, lte_rsrp_buffer, lte_rssnr_buffer, row_buffer_for_a_single_test):
		if row[self.__task_summary] != '':
			lte_rsrp_buffer = [float(rsrp) for rsrp in lte_rsrp_buffer if rsrp != '']
			lte_rssnr_buffer = [float(rssnr) for rssnr in lte_rssnr_buffer if rssnr != '']

			isGoodRF = True
			for rsrp,rssnr in zip(lte_rsrp_buffer, lte_rssnr_buffer):
				if rsrp <= RFReport1.GOOD_RSRP or rssnr <= RFReport1.GOOD_SINR:
					isGoodRF = False

			#passed and failed tests
			if isGoodRF:
				self.__bandDict[band][RFReport1.INDEX__numTestWithGoodRF] += 1
				self.__bandDict[band][RFReport1.INDEX__rootEstTaskSuccessWithGoodRF] += float(row[self.__task_summary].strip('%'))
				self.__writeLogFileForBands(isGoodRF, band, row_buffer_for_a_single_test)
			else:
				self.__bandDict[band][RFReport1.INDEX__numTestWithBadRF] += 1
				self.__bandDict[band][RFReport1.INDEX__rootEstTaskSuccessWithBadRF] += float(row[self.__task_summary].strip('%'))
				self.__writeLogFileForBands(isGoodRF, band, row_buffer_for_a_single_test)

			#failed tests only
			if float(row[self.__task_summary].strip('%')) < 100:
				if isGoodRF:
					self.__bandDict[band][RFReport1.INDEX__numTestFailedWithGoodRF] += 1
				else:
					self.__bandDict[band][RFReport1.INDEX__numTestFailedWithBadRF] += 1

	def __writeLogFileForBands(self, isGoodRF, band, row_buffer_for_a_single_test):
		space = ['']
		if isGoodRF:
			for row in row_buffer_for_a_single_test:
				if band == "25":
					self.__b25_goodRF_writer.writerow(row)
				elif band == "26":
					self.__b26_goodRF_writer.writerow(row)
				elif band == "41":
					self.__b41_goodRF_writer.writerow(row)
				elif band == "Mixed":
					self.__bMixed_goodRF_writer.writerow(row)

			if band == "25":
				self.__b25_goodRF_writer.writerow(space)
			elif band == "26":
				self.__b26_goodRF_writer.writerow(space)
			elif band == "41":
				self.__b41_goodRF_writer.writerow(space)
			elif band == "Mixed":
				self.__bMixed_goodRF_writer.writerow(space)

		else:
			for row in row_buffer_for_a_single_test:
				if band == "25":
					self.__b25_badRF_writer.writerow(row)
				elif band == "26":
					self.__b26_badRF_writer.writerow(row)
				elif band == "41":
					self.__b41_badRF_writer.writerow(row)
				elif band == "Mixed":
					self.__bMixed_badRF_writer.writerow(row)

			if band == "25":
				self.__b25_badRF_writer.writerow(space)
			elif band == "26":
				self.__b26_badRF_writer.writerow(space)
			elif band == "41":
				self.__b41_badRF_writer.writerow(space)
			elif band == "Mixed":
				self.__bMixed_badRF_writer.writerow(space)

	def __generateSpecificBandReportIntoFiles(self, band):
		filename = self.__csv_filename[:-4] + "_B-" + band+ "_" + self.__test_type +"_RF#1.csv"
		report_file_location = self.__dirname + "/" + filename
		print("\nGenerating Specific band report = ", filename, ("\n"))
		try:
			report_file = open(report_file_location,'w')
			report_writer = csv.writer(report_file, delimiter=',')
			RFReport1.__writeHeader(report_writer, band)
			taskSuccessWithGoodRFMean = 0
			taskSuccessWithBadRFMean = 0
			if self.__bandDict[band][RFReport1.INDEX__numTestWithGoodRF] != 0:
				taskSuccessWithGoodRFMean = round(decimal.Decimal(self.__bandDict[band][RFReport1.INDEX__rootEstTaskSuccessWithGoodRF]) / decimal.Decimal(self.__bandDict[band][RFReport1.INDEX__numTestWithGoodRF]), 2)
			if self.__bandDict[band][RFReport1.INDEX__numTestWithBadRF] != 0:
				taskSuccessWithBadRFMean = round(decimal.Decimal(self.__bandDict[band][RFReport1.INDEX__rootEstTaskSuccessWithBadRF]) / decimal.Decimal(self.__bandDict[band][RFReport1.INDEX__numTestWithBadRF]), 2)

			tmp_buffer = []
			tmp_buffer.append("Good RF")
			tmp_buffer.append(self.__bandDict[band][RFReport1.INDEX__numTestWithGoodRF])
			tmp_buffer.append(self.__bandDict[band][RFReport1.INDEX__numTestFailedWithGoodRF])
			tmp_buffer.append(taskSuccessWithGoodRFMean)
			report_writer.writerow(tmp_buffer)
			del tmp_buffer[:]
			tmp_buffer.append("Below Good RF")
			tmp_buffer.append(self.__bandDict[band][RFReport1.INDEX__numTestWithBadRF])
			tmp_buffer.append(self.__bandDict[band][RFReport1.INDEX__numTestFailedWithBadRF])
			tmp_buffer.append(taskSuccessWithBadRFMean)
			report_writer.writerow(tmp_buffer)

		finally:
			report_file.close()

	def __generateSpecificVariedReportIntoFiles(self, band):
		filename = self.__csv_filename[:-4] + "_B-" + band+ "_" + self.__test_type +"_RF#1.csv"
		report_file_location = self.__dirname + "/" + filename
		print("\nGenerating Specific band report = ", filename, ("\n"))
		try:
			report_file = open(report_file_location,'w')
			report_writer = csv.writer(report_file, delimiter=',')
			RFReport1.__writeHeader(report_writer, band)
			taskSuccessWithGoodRFMean = 0
			if self.__bandDict[band][RFReport1.INDEX__numTestWithGoodRF] != 0:
				taskSuccessWithGoodRFMean = round(decimal.Decimal(self.__bandDict[band][RFReport1.INDEX__rootEstTaskSuccessWithGoodRF]) / decimal.Decimal(self.__bandDict[band][RFReport1.INDEX__numTestWithGoodRF]), 2)
				
			tmp_buffer = []
			tmp_buffer.append("Undefined RF")
			tmp_buffer.append(self.__bandDict[band][RFReport1.INDEX__numTestWithGoodRF])
			tmp_buffer.append(self.__bandDict[band][RFReport1.INDEX__numTestFailedWithGoodRF])
			tmp_buffer.append(taskSuccessWithGoodRFMean)
			report_writer.writerow(tmp_buffer)
			del tmp_buffer[:]

		finally:
			report_file.close()


