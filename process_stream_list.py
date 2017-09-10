#usage: python3 process_stream_list.py <stream file.csv> -v
#Author: Conard James B. Faraon

"""Process a csv stream file and large pcap file to smaller pcap files.
See official documentation for more details."""

import argparse
import os
import time
import csv
from datetime import datetime

#parse arguments here
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", help="Shows various messages from debugging and processing.", action="store_true")
parser.add_argument("-g", "--get", help="GET filter.", action="store_true")
parser.add_argument("-p", "--post", help="POST filter.", action="store_true")
parser.add_argument("-d", "--data_test", help="Lite Data Test filter.", action="store_true")
parser.add_argument("-s", "--secure_test", help="Lite Data Secure Test filter.", action="store_true")
parser.add_argument("-u", "--udp", help="UDP Echo Test.", action="store_true")
parser.add_argument("csv_stream", help="StreamList File.")
args = parser.parse_args()

#CSV FROM TSHARK indices
FRAME = 0
TIME = 1
IP_SRC = 2
IP_DST = 3
STREAM = 6

#UTC MATCHER indices
UTC_TIME = 0
TEST = 1
TEST_CYCLE_ID = 2
PATH = 3

#summary files
NONE = args.csv_stream[:-4] + "_NONE.txt"
MATCHED = args.csv_stream[:-4] + "_MATCH.txt"

def main():
	start = time.time()

	if args.verbose:
		print("Started running process_stream_list.py")
		print("StreamList CSV = ", args.csv_stream)
		print("NON-matching timestamp file = ", NONE)
		print("Matching timestamp file = ", MATCHED)
		print("args.get = ", args.get)
		print("args.post = ", args.post)
		print("args.data_test = ", args.data_test)
		print("args.secure_test = ", args.secure_test)
		print("args.udp = ", args.udp, "\n")

	try:
		csv_file = open(args.csv_stream, 'r')
		csv_reader = csv.reader(csv_file)
		streams, times, ip_src, ip_dst = getDataFromCSVStream(csv_reader)

		#group associated streams
		groups = groupStreams(streams)

		#map a group of stream with associated ip addresses
		ip_dict = mapStreamToIp(streams, ip_src, ip_dst)
		if args.verbose:
			print("Groups of streams = ", groups, "\n")

		#start processing small pcaps
		streamsToPcaps(groups, streams, times, ip_dict)

	finally:
		csv_file.close()

	end = time.time()
	print("Complete process_stream_list.py Elapsed Time: ", (end - start), " s\n")

def getDataFromCSVStream(csv_reader):
	tmp_streams = []
	tmp_times = []
	tmp_src = []
	tmp_dst = []

	for row in csv_reader:
		tmp_streams.append(row[STREAM])
		tmp_times.append(row[TIME])
		tmp_src.append(row[IP_SRC])
		tmp_dst.append(row[IP_DST])

	return tmp_streams, tmp_times, tmp_src, tmp_dst

def groupStreams(streams):
	tmp_groups = []
	tmp_set = []

	length = 0
	for stream in streams:
		length += 1
		if not tmp_set:
			tmp_set.append(stream)
		else:
			if abs(int(stream) - int(tmp_set[-1])) <= 10 and length != len(streams):
				tmp_set.append(stream)
			elif abs(int(stream) - int(tmp_set[-1])) <= 10 and length == len(streams):
				tmp_set.append(stream)
				tmp_groups.append(tmp_set[:])
			elif length == len(streams):
				tmp_groups.append(tmp_set[:])
				del tmp_set[:]
				tmp_set.append(stream)
				tmp_groups.append(tmp_set[:])
			else:
				tmp_groups.append(tmp_set[:])
				del tmp_set[:]
				tmp_set.append(stream)

	return tmp_groups

def mapStreamToIp(streams, ip_src, ip_dst):
	temp_dict = {}
	tmp_set = []

	count = 0
	for stream in streams:
		if not tmp_set:
			tmp_set.append(stream)
			tmp_ip = []
			tmp_ip.append(ip_src[count])
			tmp_ip.append(ip_dst[count])
			temp_dict[stream] = tmp_ip

		elif count < len(streams):
			if (int(stream) - int(tmp_set[-1])) > 10:
				del tmp_set[:]
				tmp_set.append(stream) 
				tmp_ip = []
				tmp_ip.append(ip_src[count])
				tmp_ip.append(ip_dst[count])
				temp_dict[stream] = tmp_ip
			else:
				tmp_set.append(stream)

		count += 1

	for e in temp_dict:
		print("Dictionary entry, key = ", e, "value = " ,temp_dict[e])

	return temp_dict

def streamsToPcaps(groups, stream_list, time_list, ip_dict):
	try:
		log_no_time_match = open(NONE, 'w')
		log_none_writer = csv.writer(log_no_time_match, delimiter ='\t')

		log_time_match = open(MATCHED, 'w')
		log_matched_writer = csv.writer(log_time_match, delimiter ='\t')

		csvfile = args.csv_stream.split('/')[-1].strip('_DLStreamList.csv').strip('_ULStreamList.csv').strip('_DataStreamList.csv').strip('_SecureStreamList.csv').strip('_UdpStreamList.csv')
		filename = 'pcaps/_' + csvfile + '.pcap'

		if args.verbose:
			print("Pulling Streams from the pcap file ", filename, "\n")

		counter = 0
		for group in groups:
			tshark_cmd = "tshark -r " + filename + ' -Y "('
			cmds = ''
			pathname = ''
			stream_set = []
			isFirstRound = True
			stream_counter = 0
			for stream in group:
				stream_counter += 1
				if stream not in stream_set:
					stream_set.append(stream)
					if not isFirstRound:
						cmds += " || "
					else:
						isFirstRound = False

					transport_stream = ''
					if args.udp:
						transport_stream = "udp.stream == "
					else:
						transport_stream = "tcp.stream == "
					cmds += transport_stream + stream

				if stream is group[-1] and stream_counter == len(group): #done with the group
					associatedStream = group[0]
					pathname = findAssociatedPath(associatedStream, stream_list, time_list)

					#goes to the log file
					tmp = []
					tmp.append(filename)
					tmp.append(group)

					if not pathname == '':
						path_ext = pathname + "_"
						tshark_cmd += cmds + ')" -w ' + path_ext
						counter += 1
						str_ext = ''
						if args.get:
							str_ext = "DL#" + str(counter)

						elif args.post:
							str_ext = "UL#" + str(counter)

						elif args.data_test:
							str_ext = "DT#" + str(counter)

						elif args.secure_test:
							str_ext = "ST#" + str(counter)

						elif args.udp:
							str_ext = "UDP#" + str(counter)

						tshark_cmd += str_ext + ".pcap"
						tmp.append(path_ext + str_ext + ".pcap")
						log_matched_writer.writerow(tmp)

						ip_log_path = path_ext + str_ext + "_IP.txt"
						try:
							ip_log = open(ip_log_path, 'w')
							ip_log_writer = csv.writer(ip_log, delimiter=' ')
							ip_log_writer.writerow(ip_dict[associatedStream])

						finally:
							ip_log.close()

						print("IP Log path = ", ip_log_path)
						print("tshark cmd in stream_list = ", tshark_cmd, '\n')
						os.system(tshark_cmd)
						
					else:

						print("No matching timestamp for stream # ", group[0].rstrip(), ". Check log file for more details.\n")
						log_none_writer.writerow(tmp)

	finally:
		log_no_time_match.close()
		log_time_match.close()

def findAssociatedPath(associatedStream, stream_list, time_list):
	tmp = args.csv_stream.split('/')
	print("associatedStream = ", associatedStream)

	index = -1
	for i in range(len(stream_list)):
		if stream_list[i] == associatedStream:
			index = i
			break

	stream_time = time_list[index]
	print("stream_time = ", stream_time)
	unix_time = dateToUnixTime(stream_time)
	path = ""

	try:
		failed_report = open(tmp[0] + "_UTC_Matcher/" + tmp[0] + "_FAILED_Report.csv", 'r')
		passed_report = open(tmp[0] + "_UTC_Matcher/" + tmp[0] + "_PASSED_Report.csv", 'r')

		failed_report_reader = csv.reader(failed_report)
		passed_report_reader = csv.reader(passed_report)

		isNotFound = True 

		#TODO
		#refactor into a function
		#compare kits

		if isNotFound:			
			for row in failed_report_reader:
				tmp_time = dateToUnixTime(row[UTC_TIME])
				same_flag = checkDriverKitID(row[3])
				if (abs(unix_time - tmp_time) < 5) and checkDriverKitID(row[3]):
					print("Time from the stream.csv = ", unix_time)
					print("Time from the failed report = ", tmp_time)
					path = row[PATH][:-4]
					isNotFound = False
					break

		if isNotFound:
			for row in passed_report_reader:
				tmp_time = dateToUnixTime(row[UTC_TIME])
				if (abs(unix_time - tmp_time) < 5) and checkDriverKitID(row[3]):
					print("Time from the stream.csv = ", unix_time)
					print("Time from the passed report = ", tmp_time)
					path = row[PATH][:-4]
					isNotFound = False
					break

	finally:
		failed_report.close()
		passed_report.close()

	tmp = path.split('/')

	for i in range(len(tmp)):
		tmp[i] = tmp[i].replace(' ', '\\ ')

	path = str.join('/',tmp)
	return path

def dateToUnixTime(date_string):
	date_object = datetime.strptime(date_string,'%Y-%m-%d %H:%M:%S.%f')
	unix_timestamp = date_object.strftime("%s")

	return float(unix_timestamp)

#check that the driver kit ids are the same
def checkDriverKitID(filename):
	same_flag = False

	if "A-1" in filename and "A_Kit01" in args.csv_stream:
		same_flag = True

	if "A-2" in filename and "A_Kit02" in args.csv_stream:
		same_flag = True

	return same_flag

main()