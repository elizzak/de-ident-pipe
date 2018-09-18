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
    return parser.parse_args()

def dicom_name(rootDir):
    for dirName, subdirList, fileList in os.walk(rootDir):
        for f in fileList:
            print(dirName,f)
            return(os.path.join(dirName,f))
    return('1')   

def main():

    ## Take in input arguments
    global args
    parseArgs()

    # read project subject list key
    projfile=open(args.projectName+".txt","a+") 
    for line in projfile:
        pass
    newname = line

    dcm=dicom_name(args.patientName)
    dcmfile=pydicom.dcmread(dcm)
    oldname=dcmfile.PatientName

    # create an anonymization key
    keyfile=open("test.map","+a")
    keyfile.write(oldname "=" newname)

    # add to subj list key
    # assign patient name to newname
    projfile.write(", %s \n" %newname)

    # increment number for next patient and add a line
    inc=[int(s) for s in re.findall(r'-?\d+\.?\d*', newname)]
    inc=int(inc[0])
    inc = inc+1
    filled=str(inc).zfill(3)
    nextline=projectName+filled
    projfile.write(nextline)

    # place copy of myname.cfg in project_name folder on leela


    # run scpFwd.exe on leela


    # create new folder and store anonymized data

    
main()