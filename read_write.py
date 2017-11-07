import csv
import os

def writefile(filename, line):
	if os.path.exists(filename):
		new = max((int(i[0]) for i in readfile(filename)), default=0) + 1
	else:
		new = 1
	with open(filename,'a+') as csv_out:
		writer = csv.writer(csv_out)
		writer.writerow([new] + line)
	return new


def readfile(filename):
	with open(filename,'r') as csv_in:
		return [row for row in csv.reader(csv_in)]
