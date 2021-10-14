#!/bin/bash
#source the environment variables here so that the script runs correctly for the cron user
source /etc/profile

#make the logs dir if it doesn't already exist
mkdir /mnt/alma/logs

#change to the alma-scripts directory
cd /mnt/alma/alma-scripts

#install the dependencies
/usr/bin/python3.8 -m pipenv --python 3.8 install

#run the update, which automatically only uses the current days files 
/usr/bin/python3.8 -m pipenv run llama concat-timdex-export --export_type UPDATE > /mnt/alma/logs/timdex-concat.log 2>&1

# IF its the PROD instance, send it to the prod email address, otherwise, send to just our dev emails
[[ $WORKSPACE =~ .*prod* ]] && aws ses send-email --region us-east-1 --from noreply@libraries.mit.edu --to lib-alma-timdex-notifications@mit.edu --subject "PROD UPDATE Concat Job Completed" --text file:///mnt/alma/logs/timdex-concat.log || aws ses send-email --region us-east-1 --from noreply@libraries.mit.edu --to zoto@mit.edu --to hbailey@mit.edu --subject "TESTING UPDATE Concat Job Completed" --text file:///mnt/alma/logs/timdex-concat.log
