#! /usr/bin/bash

project_name=$1

# initialize project folder and patient key file
  # if [ ! -e $1 ]; then
  #   mkdir $project_name
  # fi
  # cd $project_name
pwd
if [ ! -e $project_name.txt ]; then
echo -n $project_name"001" >> $project_name.txt
fi

# check for myname.cfg in project folder on leela
ssh ezak@141.106.208.32 [ -e /data/scpForward/$project_name/myname.cfg ] && rm /data/scpForward/$project_name/myname.cfg

# loop through all subeject folders that were exported to the de-ident-pipe-master directory
for orig_folder in *; do
    if [ -d ${orig_folder} ]; then
        # Will not run if no directories are available
        echo $orig_folder
        # # create a key to initiate anonymization
        python key_create.py -N $orig_folder -P $project_name


        # move data to leela server for anonymization
        # usage: storescu [options] peer port dcmfile-in...
        storescu -aec ${project_name} --propose-lossless +sd +r 141.106.208.32 8105 $orig_folder
    fi
done


# # place copy of config file and key file in project_name folder on leela
scp patients.map ezak@141.106.208.32:/data/scpForward/Output/${project_name} ## this line must be first
scp myname.cfg ezak@141.106.208.32:/data/scpForward/Output/${project_name} ## this line must be last
