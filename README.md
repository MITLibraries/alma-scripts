# About this project
This repository contains scripts related to the Alma migration, and is primarily used in the alma-sftp-ec2 instance.  

## Important note: How to update files on the alma-sftp-ec2 instance. 
Files in this repo are sync'd to the alma-sftp-ec2 instance on the first deployment of the machine, and from there, are manually synced when needed via `git pull` as the gituser. 

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

## Development  
The following env variables are required and should be set as follows in a `.env` file
for local development:
```
WORKSPACE=dev
SSM_PATH=/dev/
```

Additional env variables may be required depending on the work being done. Check
`EXPECTED_CONFIG_VALUES` in `config.py` for a list of all config variables that may be
needed.

### Using Moto for local development
Certain SSM parameters are for the SAP invoices process, however we don't currently have a dev instance of SSM to work with. [Moto](https://github.com/spulec/moto) should be used in [Standalone Server Mode](https://github.com/spulec/moto#stand-alone-server-mode) during local development to mimic these required SSM parameters rather than using stage or prod SSM Parameter Store.

To use:
  1. Start moto in standalone server mode with `pipenv run moto_server`
  2. Add `SSM_ENDPOINT_URL=http://localhost:5000` to your `.env` file (Note: be sure to comment this out before running tests or they will fail)
  3. Start a Python shell and initialize the SSM client:
     ```
     pipenv run python
     from llama.ssm import SSM
     ssm = SSM()
     ```
  4. Check logging output to confirm that ssm was initialized with endpoint=http://localhost:5000
  5. Still in the Python shell, create initial required values (only one for now):
     ```
     ssm.update_parameter_value("/dev/SAP_SEQUENCE", "1001,20210722000000,ser", "StringList")
      ```

