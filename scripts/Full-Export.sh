#!/bin/bash
#source the environment variables here so that the script runs correctly for the cron user
source /etc/profile

#make the logs dir if it doesn't already exist
mkdir /mnt/alma/logs

#change to the alma-scripts directory
cd /mnt/alma/alma-scripts

#Get the current date, but dont use the day, we hard code that to use the 1st
CURRENT_DATE="$(date +"%Y%m")01"

#install the dependencies and dev tools for them
/usr/bin/python3.8 -m pipenv --python 3.8 install --dev

#run the full update, this should only happen on the second of the month for files generated on the first. 
/usr/bin/python3.8 -m pipenv run llama concat-timdex-export --export_type FULL --date "$CURRENT_DATE" > /mnt/alma/logs/timdex-concat.log 2>&1

aws ses send-email --region us-east-1 --from noreply@libraries.mit.edu --to zoto@mit.edu --subject "Concat Job Completed" --text file:///mnt/alma/logs/timdex-concat.log