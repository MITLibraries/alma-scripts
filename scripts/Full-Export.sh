# #!/bin/bash
# #source the environment variables here so that the script runs correctly for the cron user
# source /etc/profile

# #make the logs dir if it doesn't already exist
# mkdir /home/gituser/logs

# #change to the alma-scripts directory
# cd /home/gituser/alma-scripts

# #Get the current date, but dont use the day, we hard code that to use the 1st
# CURRENT_DATE="$(date +"%Y%m")01"

# #install the dependencies
# /usr/local/bin/pipenv install

# #run the full update, this should only happen on the second of the month for files generated on the first. 
# /usr/local/bin/pipenv run llama concat-timdex-export --export_type FULL --date "$CURRENT_DATE" > /home/gituser/logs/timdex-concat.log 2>&1

# # IF its the PROD instance, send it to the prod email address, otherwise, send to just our dev emails
# [[ $WORKSPACE == "prod" ]] && aws ses send-email --region us-east-1 --from noreply@libraries.mit.edu --to lib-alma-timdex-notifications@mit.edu --subject "PROD FULL Concat Job Completed" --text file:///home/gituser/logs/timdex-concat.log || aws ses send-email --region us-east-1 --from noreply@libraries.mit.edu --to lib-alma-notifications@mit.edu --subject "TESTING FULL Concat Job Completed" --text file:///home/gituser/logs/timdex-concat.log
