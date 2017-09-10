#usage: python3 run.py <Root Main csv file> [-flags]
#Author: Conard James B. Faraon

"""Runs and measures time for Python 3 script "process_large_pcap_csv.py"
See official documentation for more details."""

import argparse
import os
import time
import subprocess

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
parser.add_argument("-m", "--misc", help="Miscellaneous data processing for dupack3, lte_data_test, and RAN.", action="store_true")
parser.add_argument("-C", "--centOS", help="Data processing using CentOS", action="store_true")
parser.add_argument("root_csv", help="Root Metrics CSV File.")
args = parser.parse_args()

cmd = "python3 process_large_pcap_csv.py " + args.root_csv

if args.verbose:
	cmd += " -v"

if args.get:
	cmd += " -g"

if args.post:
	cmd += " -p"

if args.data_test:
	cmd += " -d"

if args.secure_test:
	cmd += " -s"

if args.udp:
	cmd += " -u"

if args.iog:
	cmd += " -i"

if args.tsg:
	cmd += " -t"

print("Processing large pcap files and Root Metrics main csv file.")
print(cmd)
start = time.time()

os.system(cmd)

if args.misc:

	if args.centOS:
		print("\n\n==================================================================================================")
		print("CentOS Data processing!")
		print("==================================================================================================\n\n")

		procs = []

		latency_proc = subprocess.Popen(["python3.6", "ul_latency_graph.py", "-v", args.root_csv[:-4]])
		procs.append(latency_proc)

		latency_proc = subprocess.Popen(["python3.6", "dl_latency_graph.py", "-v", args.root_csv[:-4]])
		procs.append(latency_proc)

		dupack_proc = subprocess.Popen(["python3.6", "dupack.py", "-v", args.root_csv[:-4]])
		procs.append(dupack_proc)

		rf1_proc = subprocess.Popen(["python3.6", "RFReporter1.py", "-v", args.root_csv])
		procs.append(rf1_proc)

		rf2_proc = subprocess.Popen(["python3.6", "RFReporter2.py", "-v", args.root_csv])
		procs.append(rf2_proc)

		rf3_proc = subprocess.Popen(["python3.6", "RFReporter3.py", "-v", args.root_csv])
		procs.append(rf3_proc)

		ho_proc = subprocess.Popen(["python3.6", "HOReporter.py", "-v", args.root_csv])
		procs.append(ho_proc)

		ran_proc = subprocess.Popen(["python3.6", "RANReporter.py", "-v", args.root_csv])
		procs.append(ran_proc)

		lite_proc = subprocess.Popen(["python3.6", "lte_data_test_process.py", "-f", "-p", "-v", args.root_csv[:-4]])
		procs.append(lite_proc)

		count = 1
		for p in procs:
			if p.wait() != 0:
				print("\n\n==================================================================================================")
				print("Error waiting for process ", count)
				print("==================================================================================================\n\n")
			count += 1

	else:

		print("\n==================================================================================================")
		print("Ubuntu/MacOS Data processing!")
		print("==================================================================================================\n")

		latency_cmd = "python3 ul_latency_graph.py -v " + args.root_csv[:-4]
		os.system(latency_cmd)

		latency_cmd = "python3 dl_latency_graph.py -v " + args.root_csv[:-4]
		os.system(latency_cmd)

		dupack_cmd = "python3 dupack.py -v " + args.root_csv[:-4]
		os.system(dupack_cmd)

		rf1_cmd = "python3 RFReporter1.py -v " + args.root_csv
		os.system(rf1_cmd)

		rf2_cmd = "python3 RFReporter2.py -v " + args.root_csv
		os.system(rf2_cmd)

		rf3_cmd = "python3 RFReporter3.py -v " + args.root_csv
		os.system(rf3_cmd)

		ho_cmd = "python3 HOReporter.py -v " + args.root_csv
		os.system(ho_cmd)

		ran_cmd = "python3 RANReporter.py -v " + args.root_csv
		os.system(ran_cmd)

		lite_cmd = "python3 lte_data_test_process.py -f -p -v " + args.root_csv[:-4]
		os.system(lite_cmd)

end = time.time()
print("Completed processing large pcap files and Root Metrics main csv file.")
print("Elapsed Time: ", (end - start), " s\n")
