#! /usr/bin/bash

project_name = $1
orig_folder = $2

# create a project subject list key
INC_COUNT_FILE=$project_name".txt"
OLD_INC_COUNTER=$(cat "$INC_COUNT_FILE")  
NEW_INC_COUNTER=$((OLD_INC_Counter+1))


# create a key to initiate anonymization
python key_create.py -N $orig_folder -P $project_name



# move data to leela server for anonymization
# usage: storescu [options] peer port dcmfile-in...
storscu -aec $project_name 141.106.208.32 8105 +sd +r $orig_folder
 




# place copy of myname.cfg in project_name folder on leela
scp myname.cfg

# run scpFwd.exe on leela


# create new folder and store anonymized data
