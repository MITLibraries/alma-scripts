#!/bin/bash
# Create date string
now=$(date +"%Y-%m-%d")

# Make a directory and move to it for this work
mkdir /mnt/alma/DailyUpdate_automated
cd /mnt/alma/DailyUpdate_automated

# Copy down all the MRC files
aws s3 sync s3://$ALMA_BUCKET/exlibris/Timdex/UPDATE/ . --exclude "*" --include "*.mrc"

# Remove the previous run's tmp file
rm result.tmp

# Concat all the mrc files into one file
cat *.mrc >> result.tmp

# Upload the file to s3, name it properly
aws s3 cp result.tmp s3://$DIP_ALEPH_BUCKET/ALMA_UPDATE_EXPORT_$now.mrc

#Test whether the file is valid, if it is, delete the files locally and from s3
sudo docker run mitlibraries/mario:alma-updates ingest --source aleph --consumer silent s3://dip-aleph-s3-stage/ALMA_UPDATE_EXPORT_2021-06-24.mrc

#rm *.mrc
#aws s3 rm s3://$ALMA_BUCKET/exlibris/Timdex/FULL/
