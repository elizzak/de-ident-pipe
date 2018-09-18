#!/usr/bin/env python
"""
    https://github.com/pieper/dicomsort

    Sorts directories containing dicom files into directories
    with human-readable names for easy organization and manipulation.

    See --help for options

    Steve Pieper pieper@isomics.com
    Stefan Baumann stefan.baumann@novartis.com

    This software is released under the terms of the
    3D Slicer License version 1.0 (December 20, 2005).
    See the License.txt file or http://slicer.org for full text.
"""


# {{{ packages and logging utilities

# standard python includes
import sys, os, traceback
import shutil
import time
import tempfile
import urllib
import zipfile

# special public packages
#sys.path.append('/Users/ezakszewski/anaconda/lib/python3.6/site-packages/pydicom')
sys.path.append('/usr/local/python2.7/lib/python2.7/site-packages/pydicom-0.9.9-py2.7.egg')
import dicom
from dicom.filereader import InvalidDicomError

# }}}

# {{{ DICOMSorter

class DICOMSorter(object):
    """Implements the logic for sorting dicom files from
    a source directory into a target directory tree
    according to a given set of options.
    This is meant to be somewhat independent of the command line
    wrapper so that it could be used as a library in other
    code if needed.
    """

    def __init__(self):

        self.flagToOptions = {
                '-v': 'verbose',
                '--verbose': 'verbose',
                '-z': 'compressTargets',
                '--compressTargets': 'compressTargets',
                '-d': 'deleteSource',
                '--deleteSource': 'deleteSource',
                '-f': 'forceDelete',
                '--forceDelete': 'forceDelete',
                '-k': 'keepGoing',
                '--keepGoing': 'keepGoing',
                '-t': 'test',
                '--test': 'test',
                }

        self.defaultOptions = {
                'sourceDir': None,
                'targetPattern': None,
                'compressTargets': False,
                'deleteSource': False,
                'forceDelete': False,
                'keepGoing': False,
                'verbose': False,
                'test': False,
                }

        self.requiredOptions = [ 'sourceDir', 'targetPattern', ]

        # each dict key is a directory path used while sorting
        # values are lists of new filenames within directory
        self.renamedFiles = {}

    def setOptions(self,options):
        """Set the member variable options based on passed dictionary,
        complaining if require options are missing, and filling in
        optional options with default values if not specified"""
        for option in self.requiredOptions:
            if not option in options:
                return False
        for option in self.defaultOptions:
            if option not in options:
                options[option] = self.defaultOptions[option]

        if '%' not in options['targetPattern']:
            # implement the default sort
            pattern = "%PatientName-%Modality%StudyID-%StudyDescription-%StudyDate/%SeriesNumber_%SeriesDescription-%InstanceNumber.dcm"
            options['targetPattern'] = os.path.join(options['targetPattern'], pattern)

        self.options = options
        return True

    def safeFileName(self,fileName):
        """Remove any potentially dangerous or confusing characters from
        the file name by mapping them to reasonable subsitutes"""
        underscores = r"""+`~!@#$%^&*(){}[]/=\|<>,.":' """
        backslash = "/-"
        safeName = ""
        for c in fileName:
            if c in backslash:
                print('***FOUND A BACKSLASH!!!!!*')
                return safeName
            elif c in underscores:
                c = "_"    
            safeName += c
        return safeName

    def pathFromDatasetPattern(self,ds):
        """Given a dicom dataset, use the targetPattern option
        to define a file path"""
        replacements = {}
        fmt, keys = self.formatFromPattern()
        for key in keys:
            if hasattr(ds,key):
                value = ds.__getattr__(key)
            else:
                value = ""
            if value == "":
                value = "Unknown%s" % key
            replacements[key] = self.safeFileName(str(value))
        return fmt % replacements

    def formatFromPattern(self):
        """Given a dicom dataset, use the targetPattern option
        to define a file path"""
        keys = []
        fmt = ""
        p = self.options['targetPattern']
        end = len(p)
        i = 0
        while i < end:
            c = p[i]
            if c == "%":
                fmt += "%("
                i += 1
                key = ""
                while True:
                    c = p[i]
                    i += 1
                    if not c.isalpha() or i >= end:
                        fmt += ")s"
                        i -= 1
                        break
                    else:
                        fmt += c
                        key += c
                keys.append(key)
            else:
                fmt += c
                i += 1
        return(fmt, keys)

    def renameFiles(self):
        """Perform the sorting operation by sequentially renaming all
        the files in the source directory and all it's children
        """
        self.filesRenamed = 0
        self.filesSkipped = 0
        for root, subFolders, files in os.walk(self.options['sourceDir']):
            for file in files:
                if self.options['verbose']:
                    print("Considering file %s" % file)
                file = os.path.join(root,file)
                if self.renameFile(file):
                    self.filesRenamed += 1
                else:
                    self.filesSkipped += 1
        if self.options['verbose']:
            print("Renamed %d, skipped %d" % (self.filesRenamed, self.filesSkipped))
        return True

    def renameFile(self,file):
        """Rename a single file according to the current options.
        Return true on success"""
        # check for dicom file
        try:
            ds = dicom.read_file(file,stop_before_pixels=True)
        except InvalidDicomError:
            return False
        except KeyError:
            # needed for issue with pydicom 0.9.9 and some dicomdir files
            return False
        # check for valid path - abort program to avoid overwrite
        path = self.pathFromDatasetPattern(ds)
        if os.path.exists(path):
            print('\nSource file: %s' % file)
            print('Target file: %s' % path)
            print('\nTarget file already exists - pattern is probably not unique')
            if not self.options['keepGoing']:
                print('Aborting to avoid data loss.')
                sys.exit(-3)
        # make new directories to hold file if needed
        targetDir = os.path.dirname(path)
        targetFileName = os.path.basename(path)
        if not os.path.exists(targetDir):
            os.makedirs(targetDir)
        shutil.copyfile(file,path)
        if self.options['verbose']:
            print("Copied %s, to %s" % (file,path))
        # keep track of files and new directories
        if targetDir in self.renamedFiles:
            self.renamedFiles[targetDir].append(targetFileName)
        else:
            self.renamedFiles[targetDir] = [targetFileName,]
        return True

    def zipRenamedFiles(self):
        """For each directory that had files added while sorting,
        create a zipfile containing the newly sorted files
        that were added to that directory.
        """
        for targetDir in self.renamedFiles:
            dirBase = os.path.basename(targetDir)
            dirDirname = os.path.dirname(targetDir)
            zipFilePath = dirDirname + '/' + dirBase + ".zip"
            if self.options['verbose']:
                print ('Creating %s' % zipFilePath)
            zfp = zipfile.ZipFile(zipFilePath, "w")
            for name in self.renamedFiles[targetDir]:
                zipPath = dirBase + '/' + name
                filePath = targetDir + '/' + name
                if self.options['verbose']:
                    print ('Adding %s' % zipPath)
                zfp.write(filePath, zipPath, zipfile.ZIP_DEFLATED)
                os.remove(filePath)
            if self.options['verbose']:
                print ('Finished %s' % zipFilePath)
            zfp.close()
            # remove the stub directory - it will only succeed if it is
            # empty, meaning that all the files were moved to the zipfile
            try:
                os.rmdir(targetDir)
            except OSError:
                pass


# DICOMSorter }}}

# {{{ Download helper

class DownloadHelper(object):
    """Class to help download data for testing"""

    def __init__(self):
        self.downloadPercent = 0

    def humanFormatSize(self,size):
        """ from http://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size"""
        for x in ['bytes','KB','MB','GB']:
            if size < 1024.0 and size > -1024.0:
                return "%3.1f%s" % (size, x)
            size /= 1024.0
        return "%3.1f%s" % (size, 'TB')

    def downloadReportHook(self,blocksSoFar,blockSize,totalSize):
        percent = int((100. * blocksSoFar * blockSize) / totalSize)
        if percent == 100 or (percent - self.downloadPercent >= 10):
            humanSizeSoFar = self.humanFormatSize(blocksSoFar * blockSize)
            humanSizeTotal = self.humanFormatSize(totalSize)
            print('Downloaded %s (%d%% of %s)...' %
                    (humanSizeSoFar, percent, humanSizeTotal))
            self.downloadPercent = percent

    def downloadFileIfNeeded(self,url,destination,expectedSize):
        if os.path.exists(destination) and os.stat(destination).st_size == expectedSize:
            print('File exists %s and is correct size, not downloading' % destination)
            return True
        self.downloadPercent = 0
        print('Requesting download of %s from %s...\n' % (destination, url))
        try:
            urllib.urlretrieve(url, destination, self.downloadReportHook)
            print('Download finished')
        except IOError as e:
            print('Download failed: %s' % e)
            return False
        return True

# Download helper}}}

# {{{ main, test, and arg parse

def usage():
    print("dicomsort [options...] sourceDir targetDir/<patterns>")
    print("\n where [options...] can be:")
    print("    [-z,--compressTargets] - create a .zip file in the target directory")
    print("    [-d,--deleteSource] - remove source files/directories after sorting")
    print("    [-f,--forceDelete] - remove source without confirmation")
    print("    [-k,--keepGoing] - report but ignore dupicate target files")
    print("    [-v,--verbose] - print diagnostics while processing")
    print("    [-t,--test] - run the built in self test (requires internet)")
    print("    [--help] - print this message")
    print("\n <patterns...> is a string defining the output file and directory")
    print("names based on the dicom tags in the file.")
    print("\n Examples:")
    print("\n  dicomsort data sorted/%PatientName/%StudyDate/%SeriesDescription-%InstanceUID.dcm")
    print("\n could create a folder structure like:")
    print("\n  sorted/JohnDoe/2013-40-18/FLAIR-2.dcm")
    print("\nIf patterns are not specified, the following default is used:")
    print("\n %PatientName-%Modality%StudyID-%StudyDescription-%StudyDate/%SeriesNumber_%SeriesDescription-%InstanceNumber.dcm")


def selfTest(sorter):
    """Run a self test of the DICOMSorter
    - download a zipfile of test dicom data
    - extract it in a temp location
    - sort it using various options
    - confirm correct results
    """

    # perform the download
    print('Downloading...')
    testDataURL = "https://s3.amazonaws.com/ec2.isomics.com/dicomsort-testdata.zip"
    tempfile.TemporaryFile().close() # to set the tempdir variable
    destination = os.path.join(tempfile.tempdir, 'dicomsort-testdata.zip')
    expectedSize = 65916934
    downloader = DownloadHelper()
    downloader.downloadFileIfNeeded(testDataURL, destination, expectedSize)

    # unzip the data
    print('Extracting...')
    dataDir = os.path.join(tempfile.tempdir, 'dicomsort-testdata')
    fileCount = 0
    if os.path.exists(dataDir):
        for root, subFolders, files in os.walk(dataDir):
            fileCount += len(files)
        print('Found %d files in %s' % (fileCount, dataDir))
    if fileCount != 1062 or not os.path.exists(dataDir):
        if os.path.exists(dataDir):
            shutil.rmtree(dataDir)
        archive = zipfile.ZipFile(destination)
        archive.extractall(dataDir)

    # now run the tests on the downloaded data
    targetDir = os.path.join(tempfile.tempdir, 'dicomsort-output')
    if os.path.exists(targetDir):
        shutil.rmtree(targetDir)
    targetPattern = targetDir + '/%PatientName/%StudyDesciption-%StudyDate/%SeriesDescription-%SeriesNumber-%InstanceNumber.dcm'
    options = sorter.options
    options['sourceDir'] = dataDir
    options['targetPattern'] = targetPattern
    sorter.setOptions(options)
    sorter.renameFiles()
    print('\nSelf-Test Passed!')

def parseArgs(sorter,args):
    """Parse the command line args into the sorter.
    """
    options = {}
    remainingArgs = []
    while args != []:
        arg = args.pop(0)
        if arg == '--help':
            usage()
            sys.exit()
        if arg in sorter.flagToOptions.keys():
            options[sorter.flagToOptions[arg]] = True
        elif arg.startswith('-'):
            usage()
            sys.exit(1)
        else:
            remainingArgs.append(arg)
    if 'test' in options:
        remainingArgs = ["",""]
    if len(remainingArgs) != 2:
        usage()
        sys.exit(1)
    options['sourceDir'], options['targetPattern'] = remainingArgs
    if not sorter.setOptions(options):
        usage()
        sys.exit()
    if not os.path.exists(options['sourceDir']):
        print ("Source directory does not exist: %s" % options['sourceDir'])
        sys.exit(1)


def confirmDelete(sorter):
    if sorter.options['forceDelete']:
        return True
    print("Source directory is: %s" % sorter.options['sourceDir'])
    response = raw_input ('Delete source directory? [y/N] ')
    if response == 'y' or response == 'yes':
        return True
    return False


if __name__ == '__main__':
    sorter = DICOMSorter()
    try:
        parseArgs(sorter,sys.argv[1:])
        if sorter.options['test']:
            selfTest(sorter)
            exit(0)
        if not sorter.renameFiles():
            sys.exit(2)
        print("Files sorted")
        if sorter.options['compressTargets']:
            sorter.zipRenamedFiles()
            print('Target files compressed')
        if sorter.options['deleteSource']:
            if confirmDelete(sorter):
                shutil.rmtree(sorter.options['sourceDir'])
                print ('Source directory deleted')
            else:
                print ('Source directory not deleted')
        sys.exit()
    except KeyboardInterrupt, e: # Ctrl-C
        raise e
    except SystemExit, e: # sys.exit()
        raise e
    except Exception, e:
        print ('ERROR, UNEXPECTED EXCEPTION')
        print (str(e))
        traceback.print_exc()
        os._exit(1)

# }}}

# vim:set sr et ts=4 sw=4 ft=python fenc=utf-8: // See Vim, :help 'modeline
# vim: foldmethod=marker
