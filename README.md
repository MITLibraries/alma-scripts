# About this project
This repository contains scripts related to the Alma migration, and is primarily used in the alma-sftp-ec2 instance.  

## Important note: How to update files on the alma-sftp-ec2 instance. 
Files in this repo are sync'd to the alma-sftp-ec2 instance on the first deployment of the machine, and from there, are sync'd once a week via cron job, or manually if the user needs a more urgent update.  

# Directories 
## Cron.d 
This directory contains cron jobs, added to the cron.d directory on alma-sftp-ec2 automatically.  
Cron job files MUST end in a newline. 

## scripts
This directory contains the scripts that need to run on alma-sftp-ec2.
Scripts should be "chmod +x" executable in order to run as a cron job successfully.  

## SSM parameter store usage with alma-scripts
* SSM parameters in the /apps/alma-sftp/ namespace are accessible by scripts in the alma-scripts repo
* Parameters should be placed in the parameter store by developers in that path
  * Secret parameters should be made type - `SecureString` and `Use the default KMS key for this account or specify a customer-managed key for this account.`

## SES usage within alma-scripts
* Emails from the SES service must come from `noreply@libraries.mit.edu` for this app 

