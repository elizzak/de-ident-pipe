#! /usr/bin/env python2.7

import os
import sys
import pydicom
import subprocess
import shlex
import argparse
import re

args = []

def parseArgs():
    #parse all of the passed in arguments
    global args
    parser = argparse.ArgumentParser(description='Input parameters for where to look for dicoms')
    parser.add_argument('-N', '--patientName', help='Patient name as writen on folder containing dicoms')
    parser.add_argument('-P', '--projectName', help='Title of Project data is being pulled under')
    args = parser.parse_args()
    return

def dicom_name(rootDir):
     for dirName, subdirList, fileList in os.walk(rootDir):
         for f in fileList:
             return(os.path.join(dirName,f))



def main():

    ## Take in input arguments
    global args
    parseArgs()

    # read project subject list key
    with open(str(args.projectName)+".txt","r") as pf:
        ll=pf.readlines()
        print(ll)

    # for line in reversed(open(args.projectName+".txt").readlines()):
    #     newname=line.rstrip()
    #     pass
    newname=ll[-1]

    # write new name to text file that can be easily read by wrapper bash script
    text=open('newname.txt', 'w+')
    text.write(newname)
    text.close()

    print("../"+args.patientName)
    dcm=dicom_name("../"+args.patientName)
    print(dcm)
    dcmfile=pydicom.dcmread(dcm)
    oldname=dcmfile.PatientName

    # create an anonymization key
    keyfile=open("patients.map","a+")
    keyfile.write('%s=%s \n' % (oldname, newname))
    keyfile.close()
    # add to subj list key
    # assign patient name to newname
    projfile=open(args.projectName+".txt","a+")
    projfile.write(", %s \n" %oldname)

    # increment number for next patient and add a line
    inc=[int(s) for s in re.findall(r'-?\d+\.?\d*', newname)]
    inc=int(inc[0])
    inc = inc+1
    filled=str(inc).zfill(3)
    nextline=args.projectName+filled
    projfile.write(nextline)
    projfile.close()


main()
