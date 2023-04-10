# About this project

This repository contains scripts related to the Alma migration, and is primarily used in the alma-sftp-ec2 instance. The EC2 instance is currently turned off, and this repo will eventually be archived, but in the meantime, this disables any cron jobs that might get pushed to the EC2 instance if it accidently gets turned back on.

## IMPORTANT NOTE 1

This app is due for retirement. The scripts are all migrated to our AWS Organization as standalone cont

## Important note 2: How to update files on the alma-sftp-ec2 instance.

Files in this repo are sync'd to the alma-sftp-ec2 instance on the first deployment of the machine, and from there, are manually synced when needed via `git pull` as the gituser. 

## Directories 

### Cron.d 

This directory contains cron jobs, added to the cron.d directory on alma-sftp-ec2 automatically.  
Cron job files MUST end in a newline. 

### scripts

This directory contains the scripts that need to run on alma-sftp-ec2.
Scripts should be "chmod +x" executable in order to run as a cron job successfully.  

### SSM parameter store usage with alma-scripts

* SSM parameters in the /apps/alma-sftp/ namespace are accessible by scripts in the alma-scripts repo
* Parameters should be placed in the parameter store by developers in that path
  * Secret parameters should be made type - `SecureString` and `Use the default KMS key for this account or specify a customer-managed key for this account.`

### SES usage within alma-scripts

* Emails from the SES service must come from `noreply@libraries.mit.edu` for this app 

### Development  

The following env variables are required and should be set as follows in a `.env` file
for local development:

```bash
WORKSPACE=dev
SSM_PATH=/dev/
```

Additional env variables may be required depending on the work being done. Check
`EXPECTED_CONFIG_VALUES` in `config.py` for a list of all config variables that may be
needed.

If an multi-line value, such as a private key, is needed in the `.env` file, use single quotes

```bash
SAP_DROPBOX_KEY='-----BEGIN RSA PRIVATE KEY-----
many
lines
-----END RSA PRIVATE KEY-----'
```

#### Using Moto for local development

Certain SSM parameters are for the SAP invoices process, however we don't currently have a dev instance of SSM to work with. [Moto](https://github.com/spulec/moto) should be used in [Standalone Server Mode](https://github.com/spulec/moto#stand-alone-server-mode) during local development to mimic these required SSM parameters rather than using stage or prod SSM Parameter Store.

To use:

1. Start moto in standalone server mode with `pipenv run moto_server`
2. Add `SSM_ENDPOINT_URL=http://localhost:5000` to your `.env` file (Note: be sure to comment this out before running tests or they will fail)
3. Start a Python shell and initialize the SSM client:

```bash
pipenv run python
from llama.ssm import SSM
ssm = SSM()
```

4. Check logging output to confirm that ssm was initialized with endpoint=http://localhost:5000
5. Still in the Python shell, create initial required values (only one for now):

```
ssm.update_parameter_value("/dev/SAP_SEQUENCE", "1001,20210722000000,ser", "StringList")
```

#### Creating sample SAP data

Running the SAP Invoices process during local development or on staging requires that
there be sample invoices ready to be paid in the Alma sandbox. To simplify this, there
is a CLI command that will create four sample invoices in the sandbox. To do this:

1. Make sure the following variables are set in your `.env`:

```bash
WORKSPACE=dev
SSM_PATH=/dev/
ALMA_API_URL=<the Alma API base URL>
ALMA_API_ACQ_READ_WRITE_KEY=<the SANDBOX Alma Acq read/write key>
```

2. Run `pipenv run llama create-sandbox-sap-data`. You should get a final log message saying there are four invoices ready for manual approval in Alma.
3. Go to the Alma sandbox UI > Acquisitions module > Review (Invoice) > Unassigned tab. There should be four invoices listed whose numbers start with TestSAPInvoice.
4. For each of those invoices, click on it and then click "Save and Continue". They will now show up in the Waiting For Approval Invoices queue.
5. From that queue, using the three dots to the right of each invoice, choose "Edit" and then click "Approve" in the upper right corner.
6. Once the invoices have been approved, they are ready to be paid and will be retrieved and processed using the llama sap-invoices CLI command.

Note that sample invoices will remain in the Alma sandbox in the "Waiting to be Sent"
status until a "real", "final" sap-invoices process has been run, at which point they
will be marked as paid and new sample invoices will need to be created.
