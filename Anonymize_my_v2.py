#! /usr/bin/env python2.7
import sys

#sys.path.append('/usr/local/python2.7/lib/python2.7/site-packages/pydicom-0.9.9-py2.7.egg')


import argparse
import dicom
import os
import glob
import ntpath
import subprocess
import string
import random
import shutil
import fnmatch
import csv

args = []

def parseArgs():
    #parse all of the passed in arguments
    
    global args
    parser = argparse.ArgumentParser(description='Input parameters for where to copy database records.')
    parser.add_argument('-iM', '--iMacFolder', help='Path to folder on iMac', default='/Users/mrResearch/NonMavric/Transfer')
    parser.add_argument('-i', '--ImportXnat', help='Path to the Import folder on CIRXNAT1', default='') #where the files are put when brought in from iMac
    parser.add_argument('-s', '--StoreXnat', help='Path to the Store folder on CIRXNAT1', default='') #place where the anonymized data will be stored
    
    parser.add_argument('-da', '--DestinationAddress', help='Path to the XNAT instance we are copying to.', default='http://cirxnat1.rcc.mcw.edu/xnat')
    parser.add_argument('-dP', '--DestinationProject', help='XNAT project we are copying from.', default='Sandbox')
    parser.add_argument('-du', '--DestinationUser', help='UserName we are using on the destination server.', default='rkarr') #My username
    parser.add_argument('-dp', '--DestinationPassword', help='UserPassword associated with the user name.', default='') #My password
    
    args = parser.parse_args()
    return

def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))
    
    
#SSH into iMac
#Anonymize the files on iMac
#rsync to cirxnat
#Push to Xnat

#
       
    
def dataTransfer():
    global args
#      
#     #TRANSFER USER AND PATH
    transferUser = 'mrresearch@141.106.208.133'
#      
#     #Copy data from iMac to MAV_DATA_IMPORT on cirxnat1
    print "Copy Data"
#     lsCmd = "ssh %s 'ls -ltr %s'" % (transferUser, args.NibblerFolder)
    lsCmd = "ssh %s -p 5004 'ls -ltr %s'" % (transferUser, args.iMacFolder)
    subprocess.check_output(lsCmd, shell=True)
#     copyCmd = "scp -r %s:%s %s" % (transferUser, args.NibblerFolder, args.ImportXnat)
    copyCmd = "scp -r -P 5004 %s:%s %s" % (transferUser, args.iMacFolder, args.ImportXnat)
    subprocess.check_output(copyCmd, shell=True)

#      
#     #Rsync iMac and Xnat folders
    print "RSYNC Directories"
    successfulBackup = True
#     cmd = 'rsync -rcvnP %s:%s %s' % (transferUser, args.NibblerFolder, args.ImportXnat)
    cmd = 'rsync -rcvnP %s:%s %s' % (transferUser, args.iMacFolder, args.ImportXnat)
    rsyncverify = subprocess.check_output(cmd, shell=True)
#      
     #Check if rsync failed
    if( (args.ImportXnat + '/') in rsyncverify):
        print 'Directory NOT successfully transfered'
        successfulBackup = False
        cpCmd = "ssh %s 'cp %s %s'" % (transferUser, args.iMacFolder, '/RAID/data/Anonymize/ERROR_LOG/')
#         mvCmd = "ssh %s 'mv %s %s'" % (transferUser, args.NibblerFolder, '/RAID/data/Anonymize/ERROR_LOG/')
        subprocess.check_output(cpCmd, shell=True)
#      
#     #If rsync is successful 
    if(successfulBackup):
        print 'Directory successfully transfered: %s' % args.ImportXnat
        mvCmd = "ssh %s 'rsync %s %s'" % (transferUser, args.iMacFolder, '/RAID/data/Anonymize/BACKUP_LOG/')
#         mvCmd = "ssh %s 'rsync %s %s'" % (transferUser, args.NibblerFolder, '/RAID/data/Anonymize/BACKUP_LOG/')
        subprocess.check_output(mvCmd, shell=True)
#      
    return
    
def main():
    global args
    parseArgs()
    
    #Transfer data from iMac to XNAT
    dataTransfer()

    root_dir = "/rcc/stor2/depts/radiology/koch_lab/MAV_Anonymization/TEST_IMPORT/Transfer"
    #subjectPath = ImportXnat
    #for subName, subdirList, fileList in os.walk(root_dir):
    for item in os.listdir(root_dir):
        for subName, subdirList, fileList in os.walk(os.path.join(root_dir, item)):
            #Create a Pfile Array for each subject
            pfile = []
                            #os.walk(subjectPath)
       
            line=''
            mrFolder=''
            generatedName = "fmlh_ortho_" + id_generator()
            originalName=''
                  
            for p in fnmatch.filter(fileList, "P*.7"):
                            #for p in glob.glob(os.path.join(subjectPath, "P*.7")):
                pName = path_leaf(p)
                pfile.append(pName)
        
            for mr in fnmatch.filter(subdirList,"Mr_*"):
                
                for folders, scans, files in os.walk(os.path.join(root_dir, item, mr)):
                    #print(scans)
                    for dicoms in fnmatch.filter(files, "*.dcm"):
                        fname = os.path.join(folders, dicoms)
                        ds = dicom.read_file(fname)
                        try:
                            originalName = ds.PatientName
                            #print("Dataset read ok for")
                            #print(originalName)
                                 
                            #Reset/zero these values
                            ds.PatientBirthDate = "8"
                            ds.PatientSex = "8"
                            ds.PatientAge = "8"
                            ds.PatientWeight = "8"
                            ds.PatientSize = "8"
                            ds.OtherPatientIDs = "8"
                               
                            #Coded values
                            ds.PatientName = generatedName
                            ds.PatientID = generatedName
                            ds.StudyID = dicom.UID.generate_uid()
                                     
                            destExperiment = generatedName
                            destSubject = generatedName
                                 
                            #Update dicoms
                            #dicom.write_file(dicoms, ds)
                            ds.save_as(fname)
                            
                        except:
                            print("Dataset Read Error")
                            #shutil.move(subjectPath, "/rcc/stor2/depts/radiology/koch_lab/MAV_Anonymization/TEST_ERROR") 
                            shutil.move(fname, "/rcc/stor2/depts/radiology/koch_lab/MAV_Anonymization/TEST_ERROR") 
                
                            return
    
        
        
            #Write out each pfile and add a new line at the end
            for p in pfile:
                line = line + ",  " + p    
                line = line + "\n"
    
            #Update the association file #this we will turn into a csv
            newFile = os.path.join(args.StoreXnat, "associationFile.txt")
            fileNew = open(newFile, "a+")
            fileNew.write(line)
            fileNew.close() 
        
        shutil.move(os.path.join(root_dir, item), args.StoreXnat)
  
    return
    
#MAIN
if __name__ == '__main__':
    main()
