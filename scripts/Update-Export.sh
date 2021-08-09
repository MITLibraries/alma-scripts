#!/bin/bash
#source the environment variables here so that the script runs correctly for the cron user
source /etc/profile

#make the logs dir if it doesn't already exist
mkdir /mnt/alma/logs

#change to the alma-scripts directory
cd /mnt/alma/alma-scripts

#install the dependencies and dev tools for them
/usr/bin/python3.8 -m pipenv --python 3.8 install --dev

#run the update, which automatically only uses the current days files 
/usr/bin/python3.8 -m pipenv run llama concat-timdex-export --export_type UPDATE >> /mnt/alma/logs/timdex-concat.log 2>&1

