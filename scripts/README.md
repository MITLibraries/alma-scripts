# Scripts Directory Contents - 

## Full-Export.sh
This bash script is used to download and combine multiple timdex files into one file, via concatenation and upload the result to the DIP ALEPH bucket
This script is currently run by hand once per month, once we see the export has completed from alma

## Update-Export.sh
This bash script follows the same process as the full update, but only occurs on the "updates" files that are deposited more frequently.  This file is not currently used, and is a template for later use.  

## Patron-load.sh 
This bash script compiles a list of staff and students and sends them to alma so it can create users for them.  

## Credit-card-slips.sh
This script calls the credit card slips function to compile a list of ??