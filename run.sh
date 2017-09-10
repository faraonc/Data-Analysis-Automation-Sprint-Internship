#!/bin/bash
#To run in Ubuntu, "bash run.sh <csv file>"
#To run in CentOS, "bash run.sh <csv file> -C"
#Author: Conard James B. Faraon

if [ -d "pcaps" ]; then
	if [ -f $1 ]; then
		if [ "$2" = "-C" ]; then
			echo "Running script in CentOS!"
			python3.6 run.py $1 -v -g -p -d -s -u -i -t -m -C
		else
			echo "Running script in Ubuntu!"
			python3 run.py $1 -v -g -p -d -s -u -i -t -m
		fi
	else
		echo "ERROR: $1 not found!"
	fi
else
	echo "ERROR: The 'pcaps' folder not found!"
fi

