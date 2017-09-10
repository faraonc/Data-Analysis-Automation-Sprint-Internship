#usage: python3 lte_data_test_process.py <dir> -v -f -p
#Author: Conard James B. Faraon

"""Process lite data test pcap files for data analysis.
See official documentation for more details."""

import argparse
import os
import time
import csv
import glob
import decimal
from datetime import datetime


#parse arguments here
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", help="Shows various messages from debugging and processing.", action="store_true")
parser.add_argument("-f", "--failed", help="Generates report for FAILED Lite_Data_Test.", action="store_true")
parser.add_argument("-p", "--passed", help="Generates report for PASSED Lite_Data_Test.", action="store_true")
parser.add_argument("dir", help="Directory Name of small CSV files generated from previous data processing scripts.")
args = parser.parse_args()

CMD_HEAD = "tshark -t ud -2 -nn -r " 

SYN_CMD = " -Y '(tcp.flags.syn == 1 && tcp.flags.ack == 0 && tcp.dstport == 80 && not ip.version == 6)' -T fields -E separator=',' -e frame.number -e _ws.col.Time -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport -e tcp.stream > "

SYNACK_CMD = " -Y '(tcp.flags.syn == 1 && tcp.flags.ack == 1 && tcp.srcport == 80 && not ip.version == 6)' -T fields -E separator=',' -e frame.number -e _ws.col.Time -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport -e tcp.stream > "

GET_CMD = " -Y '(http.request.uri.path contains \"/downloads/ldr_file.txt\")' -T fields -E separator=',' -e frame.number -e _ws.col.Time -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport -e tcp.stream > "

OK_CMD = " -Y '(http.response.code == 200 && http.response.phrase == \"OK\")' -T fields -E separator=',' -e frame.number -e _ws.col.Time -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport -e tcp.stream > "

#file directory
LTE_FOLDER = args.dir + "_LITE_DT_Analysis"

#OK indices
OK_DEVICE_PORT = 5 

INDEX_TIME = 1
INDEX_STREAM = -1
INDEX_DRIVER = 2
INDEX_TEST_ID = 5
INDEX_HO = 4

GOOD_RSRP = -105.0
GOOD_SINR = 5.0

NA = ''

def main():
	start = time.time()

	if args.verbose:
		print("Started running lte_data_test_process.py")
		print("Finding Lite_Data_Test pcap in directory = ", args.dir)
		print("Generating Lite_Data_Test reports in directory = ", LTE_FOLDER, "\n")

	generateReportFolder()

	if args.failed:
		failed_pcap_paths = getPcapPaths("failed")

		if args.verbose:
			print("The following paths are from failed_pcap_paths: ")
			for path in failed_pcap_paths:
				print(path)
			print()

		try:
			csv_report_name = LTE_FOLDER + "/"+ args.dir + "_LITE_DT_FAILED_Report.csv"
			csv_report_file = open(csv_report_name, 'w')
			csv_report_writer = csv.writer(csv_report_file, delimiter=',')
			writeReportHeader(csv_report_writer)
			for path in failed_pcap_paths:
				dt_folder_name = generateDTFolder(path)
				syn_filename = generateCSVReport(path, dt_folder_name, SYN_CMD, "_SYN.csv")
				synack_filename = generateCSVReport(path, dt_folder_name, SYNACK_CMD, "_SYNACK.csv")
				get_filename = generateCSVReport(path, dt_folder_name, GET_CMD, "_GET.csv")
				ok_filename = generateCSVReport(path, dt_folder_name, OK_CMD, "_OK.csv")
				analyzeCSVReports(path, syn_filename, synack_filename, get_filename, ok_filename, csv_report_writer)
				csv_report_writer.writerow([])

		finally:
			csv_report_file.close()

	if args.passed:
		passed_pcap_paths = getPcapPaths("passed")

		if args.verbose:
			print("The following paths are from passed_pcap_paths: ")
			for path in passed_pcap_paths:
				print(path)
			print()

		try:
			csv_report_name = LTE_FOLDER + "/"+ args.dir + "_LITE_DT_PASSED_Report.csv"
			csv_report_file = open(csv_report_name, 'w')
			csv_report_writer = csv.writer(csv_report_file, delimiter=',')
			writeReportHeader(csv_report_writer)
			for path in passed_pcap_paths:
				dt_folder_name = generateDTFolder(path)
				syn_filename = generateCSVReport(path, dt_folder_name, SYN_CMD, "_SYN.csv")
				synack_filename = generateCSVReport(path, dt_folder_name, SYNACK_CMD, "_SYNACK.csv")
				get_filename = generateCSVReport(path, dt_folder_name, GET_CMD, "_GET.csv")
				ok_filename = generateCSVReport(path, dt_folder_name, OK_CMD, "_OK.csv")
				analyzeCSVReports(path, syn_filename, synack_filename, get_filename, ok_filename, csv_report_writer)
				csv_report_writer.writerow([])

		finally:
			csv_report_file.close()

	end = time.time()
	print("Completed lte_data__test_process.py Elapsed Time: ", (end - start), "s\n")

def getPcapPaths(test_result):
	glob_path = args.dir + "/*/*/" + test_result + "/*/*/*/*DT#*.pcap"
	pcap_path = glob.glob(glob_path)
	return pcap_path 

def generateReportFolder():
	if not os.path.exists(LTE_FOLDER):
		os.makedirs(LTE_FOLDER)

def generateDTFolder(path):
	dt_folder_name = path[:-5]
	if not os.path.exists(dt_folder_name):
		os.makedirs(dt_folder_name)
	return dt_folder_name

def generateCSVReport(path, dt_folder_name, cmd_tail, file_extension):
	report_location = dt_folder_name + "/" + path.split('/')[-1][:-5] + file_extension
	tshark_cmd = CMD_HEAD + path + cmd_tail + report_location

	if args.verbose:
		print(tshark_cmd, "\n")
		os.system(tshark_cmd)

	return report_location 

def analyzeCSVReports(path, syn_filename, synack_filename, get_filename, ok_filename, csv_report_writer):
	try:
		ok_file = open(ok_filename, 'r')
		ok_reader = csv.reader(ok_file)

		syn_file = open(syn_filename, 'r')
		syn_reader = csv.reader(syn_file)

		synack_file = open(synack_filename, 'r')
		synack_reader = csv.reader(synack_file)

		get_file = open(get_filename, 'r')
		get_reader = csv.reader(get_file)

		ok_stream_buffer = []
		for ok_row in ok_reader:
			ok_time, ok_device_port, ok_stream = getOkData(ok_row)

			if ok_stream in ok_stream_buffer:
				continue

			print("****************************************************************************************************************************************")
			report_row_buffer = []
			getDriverKit(report_row_buffer, syn_filename)
			getTestID(report_row_buffer, syn_filename)
			getDirectory(report_row_buffer, path)
			data_network = getDataNetwork(report_row_buffer, path)

			if data_network == "LTE":
				getHOStatus(report_row_buffer, path)
				getRFStatus(report_row_buffer, path)
			else:
				report_row_buffer.append(NA)
				report_row_buffer.append(NA)

			ok_stream_buffer.append(ok_stream)
			report_row_buffer.append(ok_stream)
			report_row_buffer.append(ok_device_port)
			if args.verbose:
				print("ok_row = ", ok_row, "\n")
				print("Calculating SYN -> SYN + ACK delta time.")
			syn_duplicates, tmp1,  syn_synack_delta_time = getTimeDelta(ok_stream, syn_reader, synack_reader)
			syn_file.seek(0)
			synack_file.seek(0)

			if syn_synack_delta_time is not None:
				report_row_buffer.append(syn_synack_delta_time)
			else:
				report_row_buffer.append(NA)

			if args.verbose:
				print("SYN -> SYN + ACK delta time = ", syn_synack_delta_time, "\n")

			if args.verbose:
				print("Calculating SYN + ACK -> GET delta time.")
			tmp1, get_duplicates, synack_get_delta_time = getTimeDelta(ok_stream, synack_reader, get_reader)
			synack_file.seek(0)
			get_file.seek(0)

			if synack_get_delta_time is not None:
				report_row_buffer.append(synack_get_delta_time)
			else:
				report_row_buffer.append(NA)

			if args.verbose:
				print("SYN + ACK -> GET delta time = ", synack_get_delta_time, "\n")

			if args.verbose:
				print("Calculating GET -> OK delta time.")
			get_ok_delta_time = getDeltaTimeWithOk(ok_stream, ok_time, get_reader)
			get_file.seek(0)

			if get_ok_delta_time is not None:
				report_row_buffer.append(get_ok_delta_time)
			else:
				report_row_buffer.append(NA)

			if args.verbose:
				print("GET -> OK delta time. = ", get_ok_delta_time, "\n")

			if args.verbose:
				print("Calculating SYN -> OK delta time.")
			syn_ok_delta_time = getDeltaTimeWithOk(ok_stream, ok_time, syn_reader)
			syn_file.seek(0)
			if syn_ok_delta_time is not None:
				report_row_buffer.append(syn_ok_delta_time)
			else:
				report_row_buffer.append(NA)

			if args.verbose:
				print("SYN -> OK delta time. = ", syn_ok_delta_time, "\n")

			if len(syn_duplicates) == 0:
				report_row_buffer.append(-1)
			elif len(syn_duplicates) > 1:
				report_row_buffer.append(len(syn_duplicates) - 1)
			else:
				report_row_buffer.append(NA)

			if len(get_duplicates) == 0:
				report_row_buffer.append(-1)
			elif len(get_duplicates) > 1:
				report_row_buffer.append(len(get_duplicates) - 1)
			else:
				report_row_buffer.append(NA)

			csv_report_writer.writerow(report_row_buffer)
	finally:
		ok_file.close()
		syn_file.close()
		synack_file.close()
		get_file.close()

def writeReportHeader(csv_report_writer):
	header = ["Driver_Kit",
				"Test_ID",
				"Directory",
				"Data_Network",
				"HO_Status",
				"RF_Status",
				"TCP_Stream",
				"TCP_Src_Port",
				"SYN_SYNACK_Delta",
				"SYNACK_GET_Delta",
				"GET_OK_Delta",
				"SYN_OK_Delta",
				"SYN_Duplicates",
				"GET_Duplicates"]
	csv_report_writer.writerow(header)
	del header

def getDriverKit(report_row_buffer, syn_filename):
	report_row_buffer.append(syn_filename.split('/')[INDEX_DRIVER])

def getTestID(report_row_buffer, syn_filename):
	report_row_buffer.append(syn_filename.split('/')[INDEX_TEST_ID])

def getHOStatus(report_row_buffer, path):
	report_row_buffer.append(path.split('/')[INDEX_HO])

def getDataNetwork(report_row_buffer, path):
	data_network = path.split('/')[1]
	report_row_buffer.append(data_network)
	return data_network

def getDirectory(report_row_buffer, path):
	csv_list = path.split('_')
	csv_filename = '_'.join(csv_list[:-1]) + ".csv"
	report_row_buffer.append(csv_filename)

def getRFStatus(report_row_buffer, path):
	isGoodRF = True
	csv_list = path.split('_')
	csv_filename = '_'.join(csv_list[:-1]) + ".csv"
	if args.verbose:
		print("Getting RF Status from csv file = ", csv_filename)
	try:
		csv_file = open(csv_filename, 'r')
		csv_reader = csv.reader(csv_file)

		lte_rsrp_buffer = []
		lte_rssnr_buffer = []
		lte_rsrp_index = 0 
		lte_rssnr_index = 0
		isFirstRound = True
		for row in csv_reader:
			if isFirstRound:
				isFirstRound = False
				lte_rsrp_index = row.index("LTE_RSRP")
				lte_rssnr_index = row.index("LTE_RSSNR")
				continue

			lte_rsrp_buffer.append(row[lte_rsrp_index])
			lte_rssnr_buffer.append(row[lte_rssnr_index])

		lte_rsrp_buffer = [float(rsrp) for rsrp in lte_rsrp_buffer if rsrp != '']
		lte_rssnr_buffer = [float(rssnr) for rssnr in lte_rssnr_buffer if rssnr != '']
		for rsrp,rssnr in zip(lte_rsrp_buffer, lte_rssnr_buffer):
			if rsrp <= GOOD_RSRP or rssnr <= GOOD_SINR:
				isGoodRF = False
	finally:
		csv_file.close()

	if isGoodRF:
		report_row_buffer.append("Good")
	else:
		report_row_buffer.append("Below Good")

def getOkData(ok_row):
	ok_time = ok_row[INDEX_TIME]
	ok_device_port = ok_row[OK_DEVICE_PORT]
	ok_stream = ok_row[INDEX_STREAM]
	return ok_time, ok_device_port, ok_stream

def getDeltaTimeWithOk(ok_stream, ok_time, reader):
	min_time_from_reader = None
	row_buffer = []
	for row in reader:
		if row[INDEX_STREAM] == ok_stream:
			row_buffer.append(row)

	if args.verbose:
		print("row_buffer = ", row_buffer)

	if len(row_buffer) != 0:
		ok_time_epoch = dateToUnixTime(ok_time)
		ok_time_with_ms = dateToUnixMs(ok_time_epoch, ok_time)
		min_time_from_reader = ok_time_with_ms - getMinimumTime(row_buffer)

	return min_time_from_reader

def getTimeDelta(ok_stream, a, b):
	a_buffer = []
	b_buffer = []
	delta_time = None

	for a_row in a:
		if a_row[INDEX_STREAM] == ok_stream:
			a_buffer.append(a_row)

	for b_row in b:
		if b_row[INDEX_STREAM] == ok_stream:
			b_buffer.append(b_row)

	if args.verbose:
		print("a_buffer = ", a_buffer)
		print("b_buffer = ", b_buffer)

	if len(a_buffer) != 0 and len(b_buffer) != 0:
		delta_time = getMinimumTime(b_buffer) - getMinimumTime(a_buffer)

	return a_buffer, b_buffer, delta_time

def getMinimumTime(point_buffer):
	row_time = []
	for row in point_buffer:
		row_time_s = dateToUnixTime(row[INDEX_TIME])
		row_time_with_ms = dateToUnixMs(row_time_s, row[INDEX_TIME])
		row_time.append(row_time_with_ms)
	return min(row_time)

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
