# About this project
This repository contains scripts related to the Alma migration, and is primarily used in the alma-sftp-ec2 instance.  

## Important note: How to update files on the alma-sftp-ec2 instance. 
Files in this repo are sync'd to the alma-sftp-ec2 instance on the first deployment of the machine, and from there, are sync'd once a week via cron job, or manually if the user needs a more urgent update.  

# Directories 
## Cron.d 
This directory contains cron jobs, added to the cron.d directory on alma-sftp-ec2 automatically.  

## scripts
This directory contains the scripts that need to run on alma-sftp-ec2.

