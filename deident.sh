#! /usr/bin/bash

project_name=$1
orig_folder=$2

# initialize project folder and patient key file
if [ ! -e $1 ]; then
  mkdir $project_name
fi
cd $project_name
pwd
if [ ! -e $project_name.txt ]; then
echo -n $project_name"001" >> $project_name.txt
fi


# # create a key to initiate anonymization
python ../key_create.py -N $orig_folder -P $project_name
cd ../

# move data to leela server for anonymization
# usage: storescu [options] peer port dcmfile-in...
storescu -aec ${project_name}/${orig_folder} --propose-lossless +sd +r 141.106.208.32 8105 $orig_folder

# # place copy of config file and key file in project_name folder on leela
scp ${project_name}/patients.map ezak@141.106.208.32:/data/scpForward/Output/${project_name} ## this line must be first
scp myname.cfg ezak@141.106.208.32:/data/scpForward/Output/${project_name} ## this line must be last

# # create new folder and store anonymized data
# #read file newname.txt and get new name
# cd $project_name
# newname=`cat newname.txt`
# #mkdir newname
# #scp back from leela into newname
