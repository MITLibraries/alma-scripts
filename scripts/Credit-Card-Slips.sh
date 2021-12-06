#!/bin/bash
#source the environment variables here so that the script runs correctly for the cron user
source /etc/profile

#make the logs dir if it doesn't already exist
mkdir /home/gituser/logs

#change to the alma-scripts directory
cd /home/gituser/alma-scripts

#install the dependencies
pipenv install

#run the update, which automatically only uses the current days files
# IF its the PROD instance, send it to the prod email address
[[ $WORKSPACE == "prod" ]] && pipenv run llama cc-slips --source_email noreply@libraries.mit.edu --recipient_email ils-lib@mit.edu --recipient_email monoacq@mit.edu > /home/gituser/logs/credit-card-slips.log 2>&1 || /usr/bin/python3.8 -m pipenv run llama cc-slips --source_email noreply@libraries.mit.edu --recipient_email lib-alma-notifications@mit.edu > /home/gituser/logs/credit-card-slips.log 2>&1

aws ses send-email --region us-east-1 --from noreply@libraries.mit.edu --to lib-alma-notifications@mit.edu --subject "Creditcardslips Job Completed" --text file:///home/gituser/logs/credit-card-slips.log
