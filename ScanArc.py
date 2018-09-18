#! /usr/bin/env python2.7


import sys
import dicom
import dicomsort
import pydicom
import subprocess
import shlex
import argparse
#from StdSuites.AppleScript_Suite import string
import string
from datetime import timedelta, datetime
import re
import os

#transferUser = 'mrresearch@141.106.208.133'
transferUser = 'ezak@141.106.208.32'

# How to read info from DICOM headers while on the scanner?
# Select dicoms folder to take

args = []

def parseArgs():
    #parse all of the passed in arguments
    
    global args
    parser = argparse.ArgumentParser(description='Input parameters for the desired exam')
    parser.add_argument('-n', '--patientName', help='Patient name')
    parser.add_argument('-t', '--scanStart', help='time scan started')
    parser.add_argument('-s', '--scanner', help='Scanner',default='MR2',choices=['MR1', 'MR2', 'MR3'])

    return parser.parse_args()

def dicom_name(rootDir):
    for dirName, subdirList, fileList in os.walk(rootDir):
        for f in fileList:
            print(dirName,f)
            return(os.path.join(dirName,f))
    return('1')

def main():
    args=parseArgs()

    if args.scanner == 'MR1':
        scan_ip = '10.243.36.16'
        has_archive = 'true'
    elif args.scanner == 'MR2':
        scan_ip = '10.243.34.22'
        has_archive = 'true'
    elif args.scanner == 'MR3':
        scan_ip = '10.243.212.12'
        has_archive = 'false'
        
    lsCmd1 = "ssh scan@192.227.61.217 'ssh sdc@%s 'ls -ltrh /export/home1/sdc_image_pool/images/''" % (scan_ip)

    subprocess_cmd = shlex.split(lsCmd1)
    text=subprocess.check_output(subprocess_cmd)

    # now search in output, find nearest timestamp to scanStart
    times=[]

    for line in text.split('\n'):
        times.append(line[line.find('K')+len('K'):line.rfind('p')])

    del times[0]
    del times[-1]
    time_ob = [datetime.strptime(date_string, ' %b %d %H:%M ') for date_string in times]

    b_d = datetime.strptime(args.scanStart, '%b %d %H:%M')

    def func(x):
        delta =  x - b_d if x > b_d else b_d - x
        return delta
    timeStamp = min(time_ob, key = func)

    # make that a string, search original text for that string
    timeString = datetime.strftime(timeStamp, ' %b %d %H:%M ')

    folder=re.compile('\sp\d{3,}/')

    for line in text.split("\n"):
        if timeString in line:
            newstring=re.search(folder, line).group(0)

    print newstring

    # scp that file from scanner
    scpcmd = "scp -r -oProxyJump=scan@192.227.61.217 sdc@%s:/export/home1/sdc_image_pool/images/%s /data/IMPORT" % (scan_ip, newstring)
    scpcmd = "scp -oProxyCommand = 'ssh -W %h:%p scan@192.227.61.217' sdc@%s:/export/home1/sdc_image_pool/images/%s /data/IMPORT" % (scan_ip, newstring)
    print(scpcmd)
    subprocess_cmd = shlex.split(scpcmd)
    subprocess.check_output(subprocess_cmd)

    # use DicomInfo.py to confirm patient name
    # dir tree = p -> e -> s -> i(file)

    rootDir = '/data/IMPORT/%s' % (newstring)
    dFile=dicom_name(rootDir)

    # use DicomInfo.py to confirm patient name
    infocmd = 'python /home/ezak/DicomInfo.py %s' % (dFile)
    subprocess_cmd = shlex.split(infocmd)
    text=subprocess.check_output(subprocess_cmd)



# ~~~~~~~~~~ working code above ^ ~~~~~~~~~~~~~ to-do code below v ~~~~~~~~~~~~~~~~

scp -oProxyCommand = "ssh -W %h:%p username@B" username@C:/some/path/on/macine/C some/path/on/machine/A



if has_archive == 'true' :
    # get exam number
    # write line of csv to relate patient name to exam number
    # ssh scp vre:Exam to scanner/archives
    # scp scanner:archives/Exam to $HERE






10.243.36.16




# run dicomsort
#then we can run Anonymize_my_v2 on cirxnat1
cmd = "./dicomsort.py -v ../Anonymize\ in\ Pydev/p909 generated_name/%StudyDescription/%SeriesDescription[:13]/IM-%SeriesNumber-%InstanceNumber.dcm"
subprocess.check_output(cmd, shell=True)      




# dicomsort [options...] sourceDir targetDir/<patterns>
# 
# where [options...] can be:
#     [-z,--compressTargets] - create a .zip file in the target directory
#     [-d,--deleteSource] - remove source files/directories after sorting
#     [-f,--forceDelete] - remove source without confirmation
#     [-k,--keepGoing] - report but ignore dupicate target files
#     [-v,--verbose] - print diagnostics while processing
#     [-t,--test] - run the built in self test (requires internet)
#     [--help] - print this message
# 
#  <patterns...> is a string defining the output file and directory
# names based on the dicom tags in the file.
# 
#  Examples:
# 
#   dicomsort data sorted/%PatientName/%StudyDate/%SeriesDescription-%InstanceUID.dcm
# 
#  could create a folder structure like:
# 
#   sorted/JohnDoe/2013-40-18/FLAIR-2.dcm

# Actual process for archives:
# 1.) log into iMac
# 2.) log into lasiked2
# scan@192.227.61.217
# 3.) log on to scanner MR2 (adw)
# 10.243.34.22
# 4.) log into vre
# 5.) copy from vre to MR2
# 6.) copy from MR2 to iMac
# 7.) erase from MR2
