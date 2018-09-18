#! /usr/bin/env python2.7

import os
import sys
import pydicom
#import dicomsort
import pydicom
import subprocess
import shlex
import argparse
#from config import Config
from pydicom.data import get_testdata_files

args = []

def parseArgs():
    #parse all of the passed in arguments
    global args
    parser = argparse.ArgumentParser(description='Input parameters for where to look for dicoms')
    parser.add_argument('-N', '--patientName', help='Patient name as writen on folder containing dicoms')
    args = parser.parse_args()
    return

### Define functions for later use
def hashit(dcmfile,group,element,value):
    #get the original value of whatever key we're updating
    orig = dcmfile[group,element]
  # randomize dicom tag
  # Creates a repeatable value for a given dataset on a given machine
  # this implementation depends on what the user needs are and will need adjustment
    if value == "date":
        # will hash the date and offset by a value consistent within a subject ID
        # Useful to meet C requirements for dates
        pass
    elif value == "uid":
        # creates a crc32 has from the current value as part of a new uid.
        # new uid will be DCMTK uid.machine value.new hash
        pass
    elif value == "time":
        # same as modifying to 120000.000000
        pass
    elif value == "datetime":
        # hash the date portion the same as date, and time to 120000
        pass
    elif value == "other":
        # creates a md5 checksum off of the current value
        pass
    return

def key(dcmfile,group,element,value):
    # create keyed value for patient
    # will need to create a map file to pre-define keys
    print("key placeholder")
    return

def curves_callback(dataset, data_element):
    if data_element.tag.group & 0xFF00 == 0x5000:
        del dataset[data_element.tag]

# def cleanOverlays(dataset, data_element):
#     if data_element.tag.group & 0x60xx == 0x4000:
#         del dataset[data_element.tag] 
#     if data_element.tag.group & 0x60xx == 0x3000:
#         del dataset[data_element.tag] 

def main():

    ## Take in exam folder name as input argument
    global args
    parseArgs()

    ## read in config file
    #cfg = file('myname.cfg')
    #cfg = Config(f)
    fp = open('myname.cfg', 'r') 
    cfile = fp.read

    ## os walk through that folder
    ## encounter a dicom file
    for dirName, subdirList, fileList in os.walk(args.patientName):
        for f in fileList:
            dcmfile=pydicom.dcmread(f)
            ## key and anonymize that dicom file
            key = []
            ## read each line of config file
            for line in cfile:
                if line[0]=="#":
                    pass
                else:    
                    verb, tag = line.split('=')
                    group,element,value = tag.split(',')
                    selvage = value.split(' ')
                    value = selvage[0]

                        ## get instructions from current line and execute
                    if verb=="removePrivateTags" & group=="true":
                        dcmfile.remove_private_tags()
                    elif verb=="removeCurveData" & group=="true":
                        data_element=[group, element]
                        curves_callback(dcmfile,data_element)
                        dcmfile.walk(curves_callback) 
                    # elif verb=="cleanOverlays":
                    #     data_element=[group, element]
                    #     cleanOverlays(dcmfile,data_element)
                    #     dcmfile.walk(cleanOverlays)
                    elif verb=="delete":
                        del(dcmfile[group,element])
                    elif verb=="modify":
                        dcmfile[group,element] = value
                    elif verb=="key":
                        key(dcmfile,group,element,value)
                    elif verb=="hash":
                        hashit(dcmfile,group,element,value)

                    else:
                        pass
                return
            

            ## save anonymized data to new exam folder with patient codename


main()