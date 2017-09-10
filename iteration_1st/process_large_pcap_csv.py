#usage: python3 process_large_pcap_csv.py <Root file.csv> -v -g -p -d -s -u -i -t 
#Author: Conard James B. Faraon

"""Process large pcap files and the main csv file.
All pcap files should be a folder named pcaps.
See official documentation for more details."""

import argparse
import os
import time
import glob
import csv

#parse arguments here
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", help="Shows various messages from debugging and processing.", action="store_true")
parser.add_argument("-g", "--get", help="GET Filter.", action="store_true")
parser.add_argument("-p", "--post", help="POST Filter.", action="store_true")
parser.add_argument("-d", "--data_test", help="Lite Data Test Filter.", action="store_true")
parser.add_argument("-s", "--secure_test", help="Lite Data Secure Test Filter.", action="store_true")
parser.add_argument("-u", "--udp", help="UDP Echo Test.", action="store_true")
parser.add_argument("-i", "--iog", help="IO Graph.", action="store_true")
parser.add_argument("-t", "--tsg", help="Time Sequence Graph.", action="store_true")
parser.add_argument("root_csv", help="Root Metrics CSV File.")
args = parser.parse_args()

#constants
#commands for running other Python scripts
CSV = "python3 process_root_csv.py -v " + args.root_csv
RESULT_ARG = "python3 find_test_results.py -v " + args.root_csv[:-4]
TO_PCAPS = "python3 process_stream_list.py -v "
IO_GRAPH = "python3 io_graph.py -v "
TS_GRAPH = "python3 tsg.py -v "

#tshark filters
GET = "'(http.request.full_uri contains \"speedtestlg.iso\")'"
POST = "'(tcp.segment_data contains \"POST /legacy_uploads/speedtest/\")'"
DATA_TEST = "'(http.request.full_uri contains \"/downloads/ldr_file.txt\")'"
SECURE_TEST = "'(ssl.handshake.type == 1) && (ip.version == 4) && (ssl.record.length == 171)'"
UDP = "'(udp) && (udp.port == 9005)'"

#arguments for csv processing
DO_GET = 0
DO_POST = 1
DO_DATA_TEST = 2
DO_SECURE_TEST = 3
DO_UDP = 4
DOWNLINK = "Downlink"
UPLINK = "Uplink"
LITE_DATA_TEST = "Lite_Data_Test"
LITE_DATA_SECURE_TEST = "Lite_Data_Secure_Test"
UDP_ECHO_TEST = "UDP_Echo_Test"
UE = 0
SERVER = 1

#paths
PCAP_PATH = "pcaps"

def main():
	start = time.time()

	if args.verbose:
		print("Started Running process_large_pcap_csv.py")
		print("Root Metrics file.csv = ", args.root_csv, "\n")
		print("args.get = ", args.get)
		print("args.post = ", args.post)
		print("args.data_test = ", args.data_test)
		print("args.secure_test = ", args.secure_test)
		print("args.udp = ", args.udp)
		print("args.iog = ", args.iog)
		print("args.tsg = ", args.tsg)
		print()

	#extract all different tests from the main csv file
	setupRootCSV()

	#generate reports of all the tests that passed and failed with network types: LTE, & Other
	setupTestResult()

	#generate the market folder
	marketname = getMarketFolder(args.root_csv)
	
	#get a list of all pcap files by walking the entire directory
	pcap_list = getPcapFiles()

	if args.get or args.post or args.data_test or args.secure_test or args.udp:
		for file in pcap_list:
			if args.verbose:
				print("\nProcessing the pcap file from the \"pcaps\" folder:")
				print(file, "\n")

			#make the directory for the csv stream file
			makeStreamDir(marketname, file)

			#make csv stream file for Downlink Test
			if args.get:
				makeStreamCSV(marketname, file, DO_GET)

			#make csv stream file for Uplink Test
			if args.post:
				makeStreamCSV(marketname, file,  DO_POST)

			#make csv stream file for Lite Data Test
			if args.data_test:
				makeStreamCSV(marketname, file,  DO_DATA_TEST)

			#make csv stream file for Lite Data Secure Test
			if args.secure_test:
				makeStreamCSV(marketname, file,  DO_SECURE_TEST)

			#make csv stream file for UDP
			if args.udp:
				makeStreamCSV(marketname, file,  DO_UDP)

		#TODO make a flag to enable/disable this feature
		#process csv stream file and large pcap file into smaller pcap filess
		for file in pcap_list:
			processStreamToPcaps(marketname, file)

	#make IO Graphs similar to Wireshark's
	if args.iog:
		makeIoGraph()

	#Make Time Sequence Graphs similar to Wireshark's
	if args.tsg:
		makeTsg()

	end = time.time()
	print("process_large_pcap_csv.py Elapsed Time: " , (end - start), " s\n")

#executes the script process_root_csv.py
def setupRootCSV():
	os.system(CSV)

#executes the script find_test_results.py
def setupTestResult():
	os.system(RESULT_ARG)

def getMarketFolder(marketname):
	if marketname.endswith('.csv'):
		marketname = marketname[:-4]

	if args.verbose:
		print("marketname = ", marketname, "\n")

	return marketname

def makeStreamDir(marketname, pcap):
	path = marketname + "/" + pcap.strip(".pcap")

	if not os.path.exists(path):
		os.makedirs(path)

def makeStreamCSV(marketname, pcap, filter_type):
	tshark_cmd = ''

	if filter_type == DO_GET:
		tshark_cmd =  "tshark -t ud -2 -nn -r " + PCAP_PATH + "/" + pcap + " -Y " + GET + " -T fields -E separator=',' "\
			+ "-e frame.number -e _ws.col.Time -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport -e tcp.stream -e "\
			+ "http.request.method -e http.request.uri > " + marketname + "/" + pcap.strip(".pcap") + "/" + pcap.strip(".pcap")\
			+ "_DLStreamList.csv"

	elif filter_type == DO_POST:
		tshark_cmd =  "tshark -t ud -2 -nn -r " + PCAP_PATH + "/" + pcap + " -Y " + POST + " -T fields -E separator=',' "\
			+ "-e frame.number -e _ws.col.Time -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport -e tcp.stream > "\
			+ marketname + "/" + pcap.strip(".pcap") + "/" + pcap.strip(".pcap") + "_ULStreamList.csv"

	elif filter_type == DO_DATA_TEST:
		tshark_cmd =  "tshark -t ud -2 -nn -r " + PCAP_PATH + "/" + pcap + " -Y " + DATA_TEST + " -T fields -E separator=',' "\
			+ "-e frame.number -e _ws.col.Time -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport -e tcp.stream -e "\
			+ "http.request.method -e http.request.uri > " + marketname + "/" + pcap.strip(".pcap") + "/" + pcap.strip(".pcap")\
			+ "_DataStreamList.csv"

	elif filter_type == DO_SECURE_TEST:
		tshark_cmd =  "tshark -t ud -2 -nn -r " + PCAP_PATH + "/" + pcap + " -Y " + SECURE_TEST + " -T fields -E separator=',' "\
			+ "-e frame.number -e _ws.col.Time -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport -e tcp.stream  > "\
			+ marketname + "/" + pcap.strip(".pcap") + "/" + pcap.strip(".pcap") + "_SecureStreamList.csv"

	elif filter_type == DO_UDP:
		tshark_cmd =  "tshark -t ud -2 -nn -r " + PCAP_PATH + "/" + pcap + " -Y " + UDP + " -T fields -E separator=',' "\
			+ "-e frame.number -e _ws.col.Time -e ip.src -e ip.dst -e udp.srcport -e udp.dstport -e udp.stream  > "\
			+ marketname + "/" + pcap.strip(".pcap") + "/" + pcap.strip(".pcap") + "_UdpStreamList.csv"

	if args.verbose:
		print("tshark_cmd = ", tshark_cmd, "\n")

	os.system(tshark_cmd)

def getPcapFiles():
	tmp = []

	for file in os.listdir(PCAP_PATH):
		if file.endswith(".pcap"):
			tmp.append(file)

	return tmp

#execute the script process_stream_list.py
def processStreamToPcaps(marketname, pcap):
	ul_file = marketname + "/" + pcap.strip(".pcap") + "/" + pcap.strip(".pcap") + "_ULStreamList.csv"
	dl_file = marketname + "/" + pcap.strip(".pcap") + "/" + pcap.strip(".pcap") + "_DLStreamList.csv"
	dt_file = marketname + "/" + pcap.strip(".pcap") + "/" + pcap.strip(".pcap") + "_DataStreamList.csv"
	st_file = marketname + "/" + pcap.strip(".pcap") + "/" + pcap.strip(".pcap") + "_SecureStreamList.csv"
	udp_file = marketname + "/" + pcap.strip(".pcap") + "/" + pcap.strip(".pcap") + "_UdpStreamList.csv"

	if os.path.exists(ul_file) and args.post:
		os.system(TO_PCAPS + ul_file + " -p")

	if os.path.exists(dl_file) and args.get:
		os.system(TO_PCAPS + dl_file + " -g")

	if os.path.exists(dt_file) and args.data_test:
		os.system(TO_PCAPS + dt_file + " -d")

	if os.path.exists(st_file) and args.secure_test:
		os.system(TO_PCAPS + st_file + " -s")

	if os.path.exists(udp_file) and args.udp: #TODO
		print("-u to be implemented for UDP Process Stream List")
		#os.system(TO_PCAPS + udp_file + " -u")

def makeIoGraph():
	if args.get:
		test_type = DOWNLINK
		lte_failed_pcaps, other_failed_pcaps = getFailedPaths(test_type)
		lte_passed_pcaps, other_passed_pcaps = getPassedPaths(test_type)
		graphIO(test_type, lte_failed_pcaps, other_failed_pcaps, lte_passed_pcaps, other_passed_pcaps)

	if args.post:
		test_type = UPLINK
		lte_failed_pcaps, other_failed_pcaps = getFailedPaths(test_type)
		lte_passed_pcaps, other_passed_pcaps = getPassedPaths(test_type)
		graphIO(test_type, lte_failed_pcaps, other_failed_pcaps, lte_passed_pcaps, other_passed_pcaps)

	if args.data_test: #TODO
		print("-d to be implemented for IO Graph\n")
		# test_type = LITE_DATA_TEST

	if args.secure_test: #TODO
		print("-s to be implemented for IO Graph\n")
		# test_type = LITE_DATA_SECURE_TEST

	if args.udp: #TODO
		print("-u to be implemented for IO Graph\n")
		# test_type = UDP_ECHO_TEST

def getFailedPaths(type):
	lte_tmp_path = args.root_csv[:-4] + "/*/*/failed/*/*/*/*" + type + "*.pcap"
	lte_tmp = glob.glob(lte_tmp_path)

	other_tmp_path = args.root_csv[:-4] + "/Other/*/failed/*/*/*" + type + "*.pcap"
	other_tmp = glob.glob(other_tmp_path)

	return lte_tmp, other_tmp

def getPassedPaths(type):
	lte_tmp_path = args.root_csv[:-4] + "/*/*/passed/*/*/*/*" + type + "*.pcap"
	lte_tmp = glob.glob(lte_tmp_path)

	other_tmp_path = args.root_csv[:-4] + "/Other/*/passed/*/*/*" + type + "*.pcap"
	other_tmp = glob.glob(other_tmp_path)

	return lte_tmp, other_tmp

def graphIO(test_type, lte_failed_pcaps, other_failed_pcaps, lte_passed_pcaps, other_passed_pcaps):
	print("\nProcessing IOG for lte_failed_pcaps\n")
	for path in lte_failed_pcaps:
		doIOG(test_type, path)
	
	print("\nProcessing IOG for other_failed_pcaps\n")
	for path in other_failed_pcaps:
		doIOG(test_type, path)

	print("\nProcessing IOG for lte_passed_pcaps\n")
	for path in lte_passed_pcaps:
		doIOG(test_type, path)

	print("\nProcessing IOG for other_passed_pcaps\n")
	for path in other_passed_pcaps:
		doIOG(test_type, path)

def doIOG(test_type, path):
	print("test_type = ", test_type)
	print("Generating IO Graph for path = ", path)
	ip_path = path[:-5] + "_IP.txt"
	print("Using IP address from = ", ip_path)

	ip_index = 0
	if test_type == UPLINK:
		ip_index = UE
	elif test_type == DOWNLINK:
		ip_index = SERVER
	
	try:
		ip_file = open(ip_path, 'r')
		ip_csv_reader = csv.reader(ip_file, delimiter=' ')

		ip_address = 0

		for ip in ip_csv_reader:
			ip_address = ip[ip_index]

		cmd = IO_GRAPH + path + ' ' + ip_address
		print("IO Graph cmd = ", cmd)
		os.system(IO_GRAPH + path + ' ' + ip_address)

	finally:
		ip_file.close()

def makeTsg():
	if args.get:
		test_type = DOWNLINK
		lte_failed_pcaps, other_failed_pcaps = getFailedPaths(test_type)
		lte_passed_pcaps, other_passed_pcaps = getPassedPaths(test_type)
		graphTS(lte_failed_pcaps, other_failed_pcaps, lte_passed_pcaps, other_passed_pcaps)

	if args.post:
		test_type = UPLINK
		lte_failed_pcaps, other_failed_pcaps = getFailedPaths(test_type)
		lte_passed_pcaps, other_passed_pcaps = getPassedPaths(test_type)
		graphTS(lte_failed_pcaps, other_failed_pcaps, lte_passed_pcaps, other_passed_pcaps)

	if args.data_test: #TODO
		print("-d to be implemented for TSG\n")
		# test_type = LITE_DATA_TEST

	if args.secure_test: #TODO
		print("-s to be implemented for TSG\n")
		# test_type = LITE_DATA_SECURE_TEST

	if args.udp: #TODO
		print("-u to be implemented for TSG\n")
		# test_type = UDP_ECHO_TEST

def graphTS(lte_failed_pcaps, other_failed_pcaps, lte_passed_pcaps, other_passed_pcaps):
	print("\nProcessing TSG for lte_failed_pcaps\n")
	for path in lte_failed_pcaps:
		os.system(TS_GRAPH + path)
	
	print("\nProcessing TSG for other_failed_pcaps\n")
	for path in other_failed_pcaps:
		os.system(TS_GRAPH + path)

	print("\nProcessing TSG for lte_passed_pcaps\n")
	for path in lte_passed_pcaps:
		os.system(TS_GRAPH + path)

	print("\nProcessing TSG for other_passed_pcaps\n")
	for path in other_passed_pcaps:
		os.system(TS_GRAPH + path)


main()
