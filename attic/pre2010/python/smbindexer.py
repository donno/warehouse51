import popen2
import re

SMB_LIST_SHARES = "smbclient.exe -L \\\\%s -U GUEST%%"
SMB_LIST_FILES = "smbclient.exe %s -U GUEST%% -c recurse;ls;exit"

# STATE LIST Constants
FIRST_STATE = 0
DIRECTORY_STATE = 1
FILE_STATE = 2
DONE_STATE = 3

def list_shares(ip):
	shares = []
	print SMB_LIST_SHARES % ip
	stdout, stdin, stderr = popen2.popen3(SMB_LIST_SHARES % ip)
	stdin.close()
	stderr.close()
	for line in stdout.readlines():
		x = line.find('Disk')
		if x > 0:
			shares.append(line[:x].strip())
	stdout.close()
	return shares

def list_files(ip, share):
	firstcheck = "directory recursion is now on"
	service = "\\\\%s\\%s" % (ip, share)
	shares = []
	stdout, stdin, stderr = popen2.popen3(SMB_LIST_FILES % service)
	print SMB_LIST_FILES % service
	stdin.close()
	stderr.close()
	STATE = FIRST_STATE
	directory_name = ""
	for line in stdout.readlines():
		if STATE == FIRST_STATE:
			if firstcheck in line:
				STATE = DIRECTORY_STATE
		elif STATE == DIRECTORY_STATE:
			if "blocks available" in line:
				STATE = DONE_STATE
			else:
				directory_name = line.strip().split(" D")[0]
				STATE = FILE_STATE
		elif STATE ==  FILE_STATE:
			if line == "\n":
				STATE = DIRECTORY_STATE
				directory_name = ""
			else:
				print "%s%s\%s" % (service, directory_name, line.strip() )
	stdout.close()
	return shares

shares = list_shares("192.168.0.102")
for share in shares:
	sx = list_files("192.168.0.102" , share)

