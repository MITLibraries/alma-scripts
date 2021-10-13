#!/bin/bash
#source the environment variables here so that the script runs correctly for the cron user
source /etc/profile

#make the logs dir if it doesn't already exist
mkdir /mnt/alma/logs

#change to the alma-scripts directory
cd /mnt/alma/alma-scripts/patronload

#install the dependencies and dev tools for them
/usr/bin/python3.8 -m pipenv --python 3.8 install

#Run the staff load
/usr/bin/python3.8 -m pipenv run python staff.py > /mnt/alma/logs/patron-load.log 2>&1

#Run the student load
/usr/bin/python3.8 -m pipenv run python student.py >> /mnt/alma/logs/patron-load.log 2>&1

#make the folder if it doesn't already exist, this perl script errors out without the folder
mkdir SEND

#Run the "zip function" that also does a diff and makes sure the staff files take precedence 
perl scripts/pack_all_records.pl >> /mnt/alma/logs/patron-load.log 2>&1

#Sync to the s3 bucket s3://alma-sftp-prod/exlibris/PatronLoad/
# MV also deletes the zip files if they are succesfully copied
aws s3 mv SEND/ s3://$ALMA_BUCKET/exlibris/PatronLoad/ --exclude "*" --include "*.zip" --recursive  >> /mnt/alma/logs/patron-load.log 2>&1

# Remove the "rejects" files from the filesystem
rm rejects_students_script.txt
rm rejects_staff_script.txt
