# #!/bin/bash
# #source the environment variables here so that the script runs correctly for the cron user
# source /etc/profile

# #make the logs dir if it doesn't already exist
# mkdir /home/gituser/logs

# #change to the alma-scripts directory
# cd /home/gituser/alma-scripts/patronload

# #install the dependencies
# /usr/local/bin/pipenv install

# #Run the staff load
# /usr/local/bin/pipenv run python staff.py > /home/gituser/logs/patron-load.log 2>&1

# #Run the student load
# /usr/local/bin/pipenv run python student.py >> /home/gituser/logs/patron-load.log 2>&1

# #make the folder if it doesn't already exist, this perl script errors out without the folder
# mkdir SEND

# #Run the "zip function" that also does a diff and makes sure the staff files take precedence 
# perl scripts/pack_all_records.pl >> /home/gituser/logs/patron-load.log 2>&1

# #Delete existing zips if they exist, we cant double up zip files if an alma run fails, files, once used, are renamed to .old
# aws s3 rm s3://$ALMA_BUCKET/exlibris/PatronLoad/ --exclude "*" --include "*.zip" >> /home/gituser/logs/patron-load.log 2>&1

# #Sync to the s3 bucket s3://alma-sftp-prod/exlibris/PatronLoad/
# # MV also deletes the zip files if they are succesfully copied
# aws s3 mv SEND/ s3://$ALMA_BUCKET/exlibris/PatronLoad/ --exclude "*" --include "*.zip" --recursive  >> /home/gituser/logs/patron-load.log 2>&1

# #Send notify of job completion
# aws ses send-email --region us-east-1 --from noreply@libraries.mit.edu --to lib-alma-notifications@mit.edu --subject "Patronload $WORKSPACE Job Completed" --text file:///home/gituser/logs/patron-load.log

# # Remove the "rejects" files from the filesystem
# #rm rejects_students_script.txt
# #rm rejects_staff_script.txt
