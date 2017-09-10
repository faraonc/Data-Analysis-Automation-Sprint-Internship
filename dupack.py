#usage: python3 dupack.py <directory name> -v -p -n
#Author: Conard James B. Faraon

"""Generate DUPACK3 Reports using data generated from previous data processing scripts. 
A new folder is generated for this reports.
See official documentations for more details."""

import os
import glob
import argparse
import re
import time
import csv
import sys
import decimal
import copy
from datetime import datetime

#parse arguments here
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", help="Shows various messages from debugging and processing.", action="store_true")
parser.add_argument("-n", "--no_tshark", help="Disables Tshark for processing pcaps files.", action="store_true")
parser.add_argument("-p", "--pause", help="Pausing for each row of data processing.", action="store_true")
parser.add_argument("dir", help="Directory name of small Uplink Throughput pcap files generated from previous data processing scripts.")
args = parser.parse_args()

#constants
PASSED = "passed"
FAILED = "failed"
COMBINED = "COMBINED"
YES = "YES"
NO = "NO"
NA = "    "

#data1.txt indices
FRAME_NUMBER = 0
TIMESTAMP = 1
TCP_STREAM = 2
TCP_ACK = 3
TCP_SACK_LE = 4
TCP_SACK_RE = 5

#sizes
PACKET_SIZE = 1370

"""Review these constants after making changes. Ensure you understand how these numbers are used."""
#report1.csv indices
LE1 = 13
LE2 = 14
LE3 = 15
OOO = 16
#data2.txt indices
TIME = 0
SEQ = 1

#dirname
FIRST_REPORT_DIR = args.dir + "_UL_DUPACK_Reports/" + args.dir
SECOND_REPORT_DIR = args.dir + "_UL_DUPACK_Reports/" + args.dir + "_UL_DUPACK_REPORT#2.csv"

def main():
	start = time.time()

	print("Generating DUPACK#3 Retransmission Time Reports for directory = ", args.dir, "\n")

	#glob paths of Uplink Throughput Tests pcap files.
	passed_ul_pcap_list = findULPcaps(PASSED)
	failed_ul_pcap_list = findULPcaps(FAILED)
	combined_ul_pcap_list = passed_ul_pcap_list + failed_ul_pcap_list

	if args.verbose:
		print("Entries for combined_ul_pcap_list:")
		for e in combined_ul_pcap_list:
			print(e)
		print()

		print("Entries for passed_ul_pcap_list:")
		for e in passed_ul_pcap_list:
			print(e)
		print()

		print("Entries for failed_ul_pcap_list:")
		for e in failed_ul_pcap_list:
			print(e)
		print()

	makeDupAckReportDir()

	#generates data for report#1 using Tshark
	passed_ul_data_path = processULPcaps(passed_ul_pcap_list, PASSED)
	failed_ul_data_path = processULPcaps(failed_ul_pcap_list, FAILED)
	combined_ul_data_path = passed_ul_data_path + failed_ul_data_path

	if args.verbose:
		print("Number of combined UL Tests = ", len(combined_ul_data_path))
		print("Number of passed UL Tests = ", len(passed_ul_data_path))
		print("Number of failed UL Tests = ", len(failed_ul_data_path), "\n")
	
	if args.verbose:
		print("Entries for combined_ul_data:")
		for e in combined_ul_data_path:
			print(e)
		print()

		print("Entries for passed_ul_data_path:")
		for e in passed_ul_data_path:
			print(e)
		print()

		print("Entries for failed_ul_data_path:")
		for e in failed_ul_data_path:
			print(e)
		print()

	#process data for report#1
	passed_pcap_without_dupack3 = getDataForFirstReport(passed_ul_data_path, passed_ul_pcap_list, PASSED)
	failed_pcap_without_dupack3 = getDataForFirstReport(failed_ul_data_path, failed_ul_pcap_list, FAILED)
	combined_pcap_without_dupack3 = getDataForFirstReport(combined_ul_data_path, combined_ul_pcap_list, COMBINED)
	generateFirstReportSummary(passed_pcap_without_dupack3, failed_pcap_without_dupack3, combined_pcap_without_dupack3)

	#process data for report#2
	getDataForSecondReport(passed_ul_data_path, passed_ul_pcap_list, PASSED)
	getDataForSecondReport(failed_ul_data_path, failed_ul_pcap_list, FAILED)
	concatPassedAndFailedSecondReport()

	end = time.time()
	print("dupack.py Elapsed Time: ", (end - start), " s\n")

def findULPcaps(type):
	glob_path = args.dir + "/*/*/" + type + "/*/*/*/*UL#*.pcap"
	tmp = glob.glob(glob_path)
	return tmp

def makeDupAckReportDir():
	dirname = args.dir + "_UL_DUPACK_Reports/passed"
	if not os.path.exists(dirname):
		if args.verbose:
			print("Making a directory for ", dirname)
		os.makedirs(dirname)

	dirname = args.dir + "_UL_DUPACK_Reports/failed"
	if not os.path.exists(dirname):
		if args.verbose:
			print("Making a directory for ", dirname)
		os.makedirs(dirname)

def processULPcaps(pcap_path_list, test_status):
	tmp = []
	for e in pcap_path_list:
		output = args.dir + "_UL_DUPACK_Reports/" + test_status + "/" + e.split('/')[-1][:-5] + "_UL_DUPACK_Data1.txt"
		tmp.append(output)
		cmd = "tshark -t ud -r " + e + " -Y \"(tcp.analysis.duplicate_ack_num == 3) && (eth.src == 00:00:00:00:00:01)\" -T fields "\
		+ "-E separator=\"/t\" -e frame.number -e _ws.col.Time -e tcp.stream -e tcp.ack -e tcp.options.sack_le -e tcp.options.sack_re > " + output

		if args.no_tshark is None or not args.no_tshark:
			if args.verbose:
				print(cmd, "\n")
			os.system(cmd)

	return tmp

def getDataForFirstReport(data_paths, pcaps_path, test_status):
	pcap_without_dupack3 = 0
	try:
		data = []
		dirname = FIRST_REPORT_DIR + "_" + test_status.upper() + "_UL_DUPACK_REPORT#1.csv"
		report_file = open(dirname,'w')
		report_writer = csv.writer(report_file, delimiter=",")
		writeHeaderForFirstReport(report_writer)
		for e in data_paths:
			if os.stat(e).st_size == 0:
				pcap_without_dupack3 += 1
				processEmptyDataForFirstReport(e, pcaps_path, report_writer)
				continue
			else:
				try:
					data_file = open(e,'r')

					if args.verbose:
						print("filename = ", e, "\n")
					for line in data_file:
						if args.verbose:	
							print("=====================================================================================")
							print("For Report# 1")
							print("Grabbing data from line = ", line)

						processForFirstReport(e, line, pcaps_path, report_writer)

				finally:
					data_file.close()

	finally:
		report_file.close()

	return pcap_without_dupack3

def writeHeaderForFirstReport(report_writer):
	tmp = []
	tmp.append("Driver_Kit")
	tmp.append("Test_ID")
	tmp.append("Directory")
	tmp.append("Data_Path1")
	tmp.append("Timestamp")
	tmp.append("TCP.stream")
	tmp.append("ACK_Number")
	tmp.append("SACK_LE[1]")
	tmp.append("SACK_RE[1]")
	tmp.append("SACK_LE[2]")
	tmp.append("SACK_RE[2]")
	tmp.append("SACK_LE[3]")
	tmp.append("SACK_RE[3]")
	tmp.append("Lost_Packets[1]")
	tmp.append("Lost_Packets[2]")
	tmp.append("Lost_Packets[3]")
	tmp.append("Out_of_Ordering")
	report_writer.writerow(tmp)

def processEmptyDataForFirstReport(filename, pcaps_path, report_writer):
	print("Processing empty data for First Report with filename = ", filename)
	row = []
	driver_kit = getDriverKit(filename)
	row.append(driver_kit)
	test_id = getTestID(filename)
	row.append(test_id)
	pcap_filename = getPcapFilename(filename, pcaps_path)
	row.append(pcap_filename)
	row.append(filename)
	count = 0
	while count < 13:
		row.append(NA)
		count += 1

	report_writer.writerow(row)

def processForFirstReport(filename, line, pcaps_path, report_writer):
	row = []
	driver_kit = getDriverKit(filename)
	row.append(driver_kit)
	test_id = getTestID(filename)
	row.append(test_id)
	pcap_filename = getPcapFilename(filename, pcaps_path)
	row.append(pcap_filename)
	row.append(filename)
	timestamp = getTimestamp(line)
	row.append(timestamp)
	tcp_stream = getTcpStream(line)
	row.append(tcp_stream)
	tcp_ack = getAckNumber(line)
	row.append(tcp_ack)
	sack_le = getSackLE(line)
	sack_re = getSackRE(line)

	difference = 3
	if sack_le is not None and sack_re is not None:
		for le,re in zip(sack_le,sack_re):
			difference -= 1
			tmp = []
			tmp.append(le)
			tmp.append(re)
			for e in tmp:
				row.append(e)

	count = 0
	limit = difference * 2
	while count < limit:
		count += 1
		row.append(NA)

	block1,block2,block3,ooo_flag = calculateNumberMissingPackets(tcp_ack, sack_le, sack_re)

	row.append(block1)
	row.append(block2)
	row.append(block3)
	if ooo_flag:
		row.append(YES)
	else:
		row.append(NO)

	#write to disk
	report_writer.writerow(row)

	if args.pause:
		print("STOP!")
		wait = input("PRESS ENTER TO CONTINUE.")
		print("RESUME!")

def getDriverKit(filename):
	regex = re.compile(r"\/A-\d_\d")
	driver_kit = re.search(r"\/A-\d_\d", filename).group(0).strip('/')
	if args.verbose:
		print("Extracting Driver Kit from file = ", filename)
		print("driver_kit = ", driver_kit, "\n")

	return driver_kit

def getTestID(filename):
	regex = re.compile(r"_\d\d\d*_")
	testId = re.search(r"_\d\d\d*_", filename).group(0).strip('_')
	if args.verbose:
		print("Extracting Test ID from file = ", filename)
		print("id = ", testId, "\n")

	return testId

def getPcapFilename(filename, pcaps_path):
	pcap_filename = filename.split("/")[-1][:-20] + ".pcap"
	if args.verbose:
		print("Extracting Pcap file name from file = ", filename)
		print("Looking for pcap_filename = ", pcap_filename)

	for e in pcaps_path:
		if pcap_filename in e:
			if args.verbose:
				print("The pcap file is located in ", e, "\n")
			return e

def getTimestamp(line):
	timestamp = line.split("\t")[TIMESTAMP]
	if args.verbose:
		print("timestamp = ", timestamp, "\n")
	return timestamp

def getTcpStream(line):
	tcp_stream = line.split("\t")[TCP_STREAM]
	if args.verbose:
		print("tcp_stream = ", tcp_stream, "\n")
	return tcp_stream

def getAckNumber(line):
	tcp_ack = line.split("\t")[TCP_ACK]
	if args.verbose:
		print("tcp_ack = ", tcp_ack, "\n")
	return tcp_ack

def getSackLE(line):
	sack_le = None
	try:
		sack_le = line.split("\t")[TCP_SACK_LE].split(',')
		if '' in sack_le:
			del sack_le[:]
			sack_le = None
			if args.verbose:
				print("sack_le is Non-Existing!")
		else:
			sack_le = [int(le) for le in sack_le]
			sack_le.sort()
			if args.verbose:
				print("sack_le = ", sack_le)

	except IndexError:
		sack_le = None
		if args.verbose:
			print("sack_le is EMPTY!")

	return sack_le

def getSackRE(line):
	sack_re = None
	try:
		sack_re = line.split("\t")[TCP_SACK_RE].strip().split(',')
		if '' in sack_re:
			del sack_re[:]
			sack_re = None
			if args.verbose:
				print("sack_re is Non-Existing!")
		else:
			sack_re = [int(re) for re in sack_re]
			sack_re.sort()
			if args.verbose:
				print("sack_re = ", sack_re)

	except IndexError:
		sack_re = None
		if args.verbose:
			print("sack_re is EMPTY!")

	return sack_re

def calculateNumberMissingPackets(tcp_ack, sack_le,sack_re):
	count = 0
	ooo_flag = False
	blocks  = {}
	blocks[0] = 0
	blocks[1] = 0
	blocks[2] = 0
	prev_re = None
	if sack_le is None:
		blocks[0] = 1
	else:
		for le,re in zip(sack_le, sack_re):
			if count == 0 and int(tcp_ack) > le:
				ooo_flag = True
				blocks[count] = 1

			elif count == 0 and int(tcp_ack) <= le:
				if int(tcp_ack) == le:
					blocks[count] = 1
				elif (le - int(tcp_ack)) <= PACKET_SIZE:
					blocks[count] = 1
				else:
					blocks[count] = (le - int(tcp_ack)) // PACKET_SIZE

			elif prev_re is not None:
				if (le - prev_re) <= PACKET_SIZE:
					blocks[count] = 1
				else:
					blocks[count] = (le - prev_re) // PACKET_SIZE

			prev_re = re
			count += 1

	block1 = blocks[0]
	block2 = blocks[1]
	block3 = blocks[2]

	if args.verbose:
		print("LE [1] missing = ", block1)
		print("LE [2] missing = ", block2)
		print("LE [3] missing = ", block3)
		print("Out of Ordering = ", ooo_flag, "\n")

	return block1,block2,block3,ooo_flag

def generateFirstReportSummary(passed_pcap_without_dupack3, failed_pcap_without_dupack3, combined_pcap_without_dupack3):
	generateFirstSummary(COMBINED, combined_pcap_without_dupack3)
	generateFirstSummary(FAILED, failed_pcap_without_dupack3)
	generateFirstSummary(PASSED, passed_pcap_without_dupack3)

def generateFirstSummary(test_status, pcap_without_dupack3):
	try:
		report_name = FIRST_REPORT_DIR + "_" + test_status.upper() + "_UL_DUPACK_REPORT#1.csv"
		report_file = open(report_name,'r')
		report_reader = csv.reader(report_file, delimiter=',')

		summary_name = FIRST_REPORT_DIR + "_" + test_status.upper() + "_UL_DUPACK_SUMMARY#1.csv"
		summary_file = open(summary_name,'w')
		summary_writer = csv.writer(summary_file, delimiter=',')

		row = []
		row.append("Total_Packets_[1]_Lost")
		row.append("Total_Packets_[2]_Lost")
		row.append("Total_Packets_[3]_Lost")
		row.append("Overall_Total_Packets_Lost")
		row.append("Estimated_Out-Of-Ordering_Packets")
		row.append("Total_PCAP_Without_DUPACK3")
		summary_writer.writerow(row)
		del row[:]

		total_le1 = 0
		total_le2 = 0
		total_le3 = 0
		total_ooo = 0

		first_round = True
		for data_row in report_reader:
			if first_round:
				first_round = False;
				continue
			try:
				total_le1 += int(data_row[LE1])
				total_le2 += int(data_row[LE2])
				total_le3 += int(data_row[LE3])

				if data_row[OOO] == 'YES':
					total_ooo += 1
			except ValueError:
				print("Skipping Packets Lost and OOO")

		data = []
		data.append(total_le1)
		data.append(total_le2)
		data.append(total_le3)
		data.append(total_le1 + total_le2 + total_le3)
		data.append(total_ooo)
		data.append(pcap_without_dupack3)
		summary_writer.writerow(data)

		if args.verbose:
			print(test_status.upper(), "Summary of Total Packets [1] Lost = ", total_le1)
			print(test_status.upper(), "Summary of Total Packets [2] Lost = ",total_le2)
			print(test_status.upper(), "Summary of Total Packets [3] Lost = ", total_le3)
			print(test_status.upper(), "Summary of Overall Total Packets Lost = ", (total_le1 + total_le2 + total_le3))
			print(test_status.upper(), "Summary of Total Estimated Out-Of-Ordering Packets = ", total_ooo)
			print(test_status.upper(), "Summary of of Total PCAP file without DUPACK3 = ", pcap_without_dupack3, "\n")

	finally:
		report_file.close()
		summary_file.close()

def concatPassedAndFailedSecondReport():
	try:
		combined_filename = FIRST_REPORT_DIR + "_COMBINED_UL_DUPACK_REPORT#2.csv"
		passed_filename = FIRST_REPORT_DIR + "_PASSED_UL_DUPACK_REPORT#2.csv"
		failed_filename = FIRST_REPORT_DIR + "_FAILED_UL_DUPACK_REPORT#2.csv"

		combined_file = open(combined_filename,'w')
		passed_file = open(passed_filename,'r')
		failed_file = open(failed_filename,'r')

		for line in passed_file:
			combined_file.write(line)

		isFirstRound = True
		for line in failed_file:
			if isFirstRound:
				isFirstRound = False
				continue
			combined_file.write(line)

	finally:
		combined_file.close()
		passed_file.close()
		failed_file.close()

def getDataForSecondReport(data_paths, pcaps_path, test_status):
	try:
		data = []
		dirname = FIRST_REPORT_DIR + "_" + test_status.upper() + "_UL_DUPACK_REPORT#2.csv"
		report_file = open(dirname,'w')
		report_writer = csv.writer(report_file, delimiter=",")
		writeHeaderForSecondReport(report_writer)

		for data1_filename in data_paths:
			if args.verbose:
					print("Processing data from ", data1_filename, "\n")

			if os.stat(data1_filename).st_size == 0:
				processEmptyDataForSecondReport(data1_filename, pcaps_path, report_writer)
				continue
			else:
				try:
					data1_file = open(data1_filename,'r')
					for line_from_data1_file in data1_file:
						if args.verbose:
							processForSecondReport(data1_filename, line_from_data1_file, pcaps_path, report_writer, test_status)
				finally:
						data1_file.close()

	finally:
		report_file.close()

def writeHeaderForSecondReport(report_writer):
	tmp = []
	tmp.append("Driver_Kit")
	tmp.append("Test_ID")
	tmp.append("Directory")
	tmp.append("Timestamp")
	tmp.append("TCP_Stream")
	tmp.append("TCP_Sequence")
	tmp.append("TCP_Seq_List")
	tmp.append("Data_Path_1")
	tmp.append("Data_Path_2")
	tmp.append("Initial_Transmission_Time")
	tmp.append("#_Initial_Transmission_Events")
	tmp.append("First_Retransmission_Time")
	tmp.append("Delta_Time_(s)")
	report_writer.writerow(tmp)

def processEmptyDataForSecondReport(data1_filename, pcaps_path, report_writer):
	print("Processing empty data for Second Report with filename = ", data1_filename)
	#driver kit 
	row = []
	driver_kit = getDriverKit(data1_filename)
	row.append(driver_kit)

	#test id
	test_id = getTestID(data1_filename)
	row.append(test_id)

	#pcap path
	pcap_filename = getPcapFilename(data1_filename, pcaps_path)
	row.append(pcap_filename)

	#skip other fields
	count = 0
	while count < 4:
		row.append(NA)
		count += 1

	#data path1
	row.append(data1_filename)

	#skip other fields
	count = 0
	while count < 5:
		row.append(NA)
		count += 1

	report_writer.writerow(row)

def processForSecondReport(data1_filename, line_from_data1_file, pcaps_path, report_writer, test_status):
	print("=====================================================================================")
	print("For Report# 2")
	print("Grabbing data from line = ", line_from_data1_file)

	tcp_ack = getAckNumber(line_from_data1_file)
	timestamp = getTimestamp(line_from_data1_file)
	tcp_stream = getTcpStream(line_from_data1_file)
	sack_le = getSackLE(line_from_data1_file)
	sack_re = getSackRE(line_from_data1_file)
	tcp_seq_list = getTcpSeq(tcp_stream, tcp_ack, sack_le, sack_re)
	found_seq, path_to_data2_file = findSeq(data1_filename, pcaps_path, tcp_stream, tcp_seq_list, test_status, timestamp)

	for seq in tcp_seq_list:
		writeForSecondReport(seq, timestamp, data1_filename, pcaps_path, tcp_seq_list, report_writer, test_status, tcp_stream)
		if args.pause:
				print("STOP!")
				wait = input("PRESS ENTER TO CONTINUE.")
				print("RESUME!")

def writeForSecondReport(seq, timestamp, data1_filename, pcaps_path, tcp_seq_list, report_writer, test_status, tcp_stream):
	row = []

	#driver kit
	driver_kit = getDriverKit(data1_filename)
	row.append(driver_kit)

	#test id
	test_id = getTestID(data1_filename)
	row.append(test_id)

	#pcap path
	pcap_filename = getPcapFilename(data1_filename, pcaps_path)
	row.append(pcap_filename)

	#timestamp
	if args.verbose:
		print("Unix time stamp = ", dateToUnixTime(timestamp), "\n")
	row.append(timestamp)

	#tcp stream
	row.append(tcp_stream)

	#seq
	row.append(seq)

	#tcp seq list
	row.append(tcp_seq_list)
	if len(tcp_seq_list) == 0:
		row.append(NA)
		row.append(NA)
		row.append(NA)
		row.append(NA)
		row.append(NA)
		row.append(NA)
	else:
		data2_from = getData2Path(data1_filename, timestamp, tcp_stream)
		#data 1
		row.append(data1_filename)
		#data 2
		row.append(data2_from)

		initial_transmission_count, initial_transmission_date = findInitialTransmission(seq, data1_filename, timestamp, tcp_stream)
		if initial_transmission_date is None:
			row.append(NA)
		else:
			row.append(initial_transmission_date)
		row.append(initial_transmission_count)

		first_retransmission_date, delta = findFirstRetransmission(seq, data1_filename, timestamp, tcp_stream)
		if first_retransmission_date is None:
			row.append(NA)
		else:
			row.append(first_retransmission_date)
		if delta is None:
			row.append(NA)
		else:
			row.append(delta)

	#write to disk
	report_writer.writerow(row)

def findFirstRetransmission(seq, data1_filename, timestamp, tcp_stream):
	data2_filename = data1_filename[:-19] + str(int(dateToUnixTime(timestamp))) + "_" + tcp_stream + "_" + timestamp.split(':')[-1].replace('.','_')  + "_UL_DUPACK_Data2.txt"
	if args.verbose:
		print("Finding first retransmission from filename = ", data2_filename)
		print("DUPACK3 timestamp = ", timestamp)

	dupack3_time = dateToUnixTime(timestamp)
	dupack3_ms_time = float(timestamp.split(':')[-1])
	retransmision_date = None
	sec_delta = sys.maxsize
	ms_delta = sys.maxsize

	try:
		data2_file = open(data2_filename,'r')
		data2_reader = csv.reader(data2_file, delimiter='\t')

		seq_buffer = []
		for row in data2_reader:
			if int(row[SEQ]) == seq:
				seq_buffer.append(row)

		for row in seq_buffer:
			row_time = dateToUnixTime(row[TIME])
			row_ms_time = float(row[TIME].split(':')[-1])

			if row_time >= dupack3_time and row_ms_time >= dupack3_ms_time:
				if (row_time - dupack3_time) <= sec_delta and (row_ms_time - dupack3_ms_time) <= ms_delta:
					sec_delta = row_time - dupack3_time
					ms_delta = row_ms_time - dupack3_ms_time
					retransmision_date = row[TIME]
	finally:
		data2_file.close()

	if retransmision_date is None:
		if args.verbose:
			print("First Recorded Retransmission Time NOT Found!\n")
		return None, None

	else:
		if args.verbose:
			print("First Recorded Retransmission Time = ", retransmision_date)
			print("Time delta between DUPACK#3 timestamp and First Recorded Retransmission Time = ", ms_delta, " s\n")
		return retransmision_date, ms_delta

def findInitialTransmission(seq, data1_filename, timestamp, tcp_stream):
	data2_filename = data1_filename[:-19] + str(int(dateToUnixTime(timestamp))) + "_" + tcp_stream + "_" + timestamp.split(':')[-1].replace('.','_')  +"_UL_DUPACK_Data2.txt"
	
	if args.verbose:
		print("Finding initial transmission from filename = ", data2_filename)
		print("DUPACK3 timestamp = ", timestamp)

	dupack3_time_epoch = dateToUnixTime(timestamp)
	dupack3_time = dateToUnixMs(dupack3_time_epoch, timestamp)
	print("dupack3_time_epoch = ", dupack3_time_epoch)
	print("dupack3_time = ", dupack3_time)

	count_initial_transmission = 0
	initial_transmission_date = ''
	delta = None

	try:
		data2_file = open(data2_filename,'r')
		data2_reader = csv.reader(data2_file, delimiter='\t')

		seq_buffer = []
		for row in data2_reader:
			if int(row[SEQ]) == seq:
				seq_buffer.append(row)
		
		for row in seq_buffer:
			row_time_epoch = dateToUnixTime(row[TIME])
			row_time = dateToUnixMs(row_time_epoch, row[TIME])
			print("row[TIME] = ", row[TIME])
			print("row_time = ", row_time)

			if row_time < dupack3_time:
				count_initial_transmission += 1

				if delta is None:
					delta = dupack3_time - row_time
					initial_transmission_date = row[TIME]
				else:
					tmp = dupack3_time - row_time
					if tmp > delta:
						delta = dupack3_time - row_time
						initial_transmission_date = row[TIME]

	finally:
		data2_file.close()

	if count_initial_transmission == 0:
		if args.verbose:
			print("Initial Transmission Count = ", count_initial_transmission)
			print("DUPACK3 timestamp = ", timestamp)
			print("Initial Transmission Time NOT Found!\n")
		return count_initial_transmission,None
	else:
		if args.verbose:
			print("Initial Transmission Count = ", count_initial_transmission)
			print("DUPACK3 timestamp = ", timestamp)
			print("Initial Transmission Time = ", initial_transmission_date, "\n")
		return count_initial_transmission, initial_transmission_date

def getData2Path(data1_filename, timestamp, tcp_stream):
	data2_filename = data1_filename[:-19] + str(int(dateToUnixTime(timestamp))) + "_" + tcp_stream + "_" + timestamp.split(':')[-1].replace('.','_') + "_UL_DUPACK_Data2.txt"
	print("data2_filename = ", data2_filename)
	return data2_filename

def getTcpSeq(tcp_stream, tcp_ack, sack_le, sack_re):
	if sack_le is None:
		if args.verbose:
			print("sack_le is None")
		return None

	if sack_re is None:
		if args.verbose:
			print("sack_re is None")
		return None

	tcp_ack_int = int(tcp_ack)
	seq = []
	seq.append(tcp_ack_int)
	count = 0
	prev_re = None
	for le,re in zip(sack_le, sack_re):
		if count == 0:
			while tcp_ack_int < le:
				tcp_ack_int += 1370
				if tcp_ack_int not in seq and tcp_ack_int < le:
					seq.append(tcp_ack_int)
		else:
			while prev_re < le:
				prev_re += 1370
				if prev_re not in seq and prev_re < le:
					seq.append(prev_re)

		prev_re = copy.deepcopy(re)
		count += 1

	if args.verbose:
		print("Sequence numbers for tcp_stream = ", tcp_stream, " tcp_ack = ", tcp_ack, " sack_le = ", sack_le, " sack_re = ", sack_re, " :")
		print(seq,"\n")

	return seq

def findSeq(filename, pcaps_path, tcp_stream, tcp_seq, test_status, timestamp):
	if tcp_seq is None or len(tcp_seq) == 0:
		if args.verbose:
			print("tcp_seq is None")
		return False, None

	pcap_path = getPcapFilename(filename, pcaps_path)
	if args.verbose:
		print("Finding seq from tcp_stream = ", tcp_stream, " in ", pcap_path)

	cmd = "tshark -t ud -r " + pcap_path + " -Y \"tcp.stream == "+ tcp_stream + "  && ("
	output = args.dir + "_UL_DUPACK_Reports/" + pcap_path.split('/')[3] + "/" + pcap_path.split('/')[-1][:-5] + "_" + str(int(dateToUnixTime(timestamp))) \
	+ "_" + tcp_stream + "_" + timestamp.split(':')[-1].replace('.','_')  + "_UL_DUPACK_Data2.txt"

	tail = ")\" -T fields -E separator=\"/t\" -e _ws.col.Time -e tcp.seq -e frame.number -e tcp.stream > " + output

	isFirstRound = True
	for seq in tcp_seq:
		if not isFirstRound:
			cmd += " || "
		else:
			isFirstRound = False

		cmd += "tcp.seq == " + str(seq)

	cmd += tail

	if args.no_tshark is None or not args.no_tshark:
		if args.verbose:
			print("\n", cmd, "\n")
		os.system(cmd)

	return True, output

def dateToUnixTime(date_string):
	date_object = datetime.strptime(date_string,'%Y-%m-%d %H:%M:%S.%f')
	unix_timestamp = date_object.strftime("%s")
	return float(unix_timestamp)

def dateToUnixMs(epoch, date_string):
	decimal.getcontext().prec = 6
	date_string_decimal = float(date_string.split(':')[-1])
	date_string_whole_number = float(date_string.split(':')[-1].split('.')[0])
	date_string_decimal = decimal.Decimal(date_string_decimal) - decimal.Decimal(date_string_whole_number)
	unix_time_ms = epoch + float(date_string_decimal)
	return unix_time_ms

main()

