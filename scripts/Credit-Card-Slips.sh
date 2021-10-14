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
# IF its the PROD instance, send it to the prod email address
[[ $WORKSPACE =~ .*prod* ]] && /usr/bin/python3.8 -m pipenv run llama cc-slips --source_email noreply@libraries.mit.edu --recipient_email ils-lib@mit.edu --recipient_email monoacq@mit.edu > /mnt/alma/logs/credit-card-slips.log 2>&1 || /usr/bin/python3.8 -m pipenv run llama cc-slips --source_email noreply@libraries.mit.edu --recipient_email zoto@vt.edu --recipient_email ehanson@mit.edu > /mnt/alma/logs/credit-card-slips.log 2>&1

aws ses send-email --region us-east-1 --from noreply@libraries.mit.edu --to zoto@mit.edu --to ehanson@mit.edu --subject "Creditcardslips Job Completed" --text file:///mnt/alma/logs/credit-card-slips.log
