#!/usr/bin/perl -w
# Force the use of declared/scoped variables
use strict;

# Set variable for working directory to STAFF
my $working_dir = 'STAFF';

# Create date string
my $date = `date +%Y%m%d%H%M%S`;
# Ensure no newline at end of date string
chomp $date;

# Move into working directory (STAFF)
chdir $working_dir;

# Match all XML files in working directory
my @files = glob("*.xml");
# Exit gracefully if there are no matching files
exit if !$files[0];

# Create output file with correctly formatted name
my $outfile = '../SEND/' . lc($working_dir) . '_' . $date . '.xml';
# Open output file or exit script if error
open FH, ">$outfile" or die $!;

# Add XML header and root element to output file and close file
print FH "<?xml version='1.0' encoding='UTF-8'?>\n";
print FH "<userRecords>\n";
close FH;

# Empty variable to store staff records
my %staff;
# Loop through all files in STAFF directory that end with .xml (as identified above).
# There is one staff record per file from a previous script's output.
foreach my $file (@files) {
  # Concatenate the staff record file's contents onto the existing output file's
  # contents
	system ("cat $file >> $outfile");
  # Print to stdout (informational)
	system ("echo >> $outfile");
  # Delete the staff record file that was just added to the output file
	system ("rm -f $file");
  # Also add the staff record to the staff records variable
	$staff{$file}++;
}

# Open outfile file and add closing tag for XML root element, close output file
open FH, ">>$outfile" or die $!;
print FH "</userRecords>\n";

close FH;

# Zip the output file
my $zipfile = $outfile;
$zipfile =~ s/\.xml/.zip/;
system ("zip -q $zipfile $outfile");
# Delete the unzipped output file
system ("rm -f $outfile");

# Print zipped file name to stdout (informational)
$zipfile =~ s|^\.\./||;
print "$zipfile\n";

# Change working directory to STUDENT
$working_dir = 'STUDENT';

# Move to new working directory
chdir '..';
chdir $working_dir;

# Match all XML files in working directory
my @student_files = glob("*.xml");
# Exit gracefully if there are no matching files
exit if !$student_files[0];

# Create new output file name for student records
$outfile = '../SEND/' . lc($working_dir) . '_' . $date . '.xml';
# Open output file or exit script if error
open FH, ">$outfile" or die $!;

# Add XML header and root element to output file and close file
print FH "<?xml version='1.0' encoding='UTF-8'?>\n";
print FH "<userRecords>\n";
close FH;

# Loop through all files in STUDENT directory that end with .xml (as identified above).
# There is one student record per file from a previous script's output.
foreach my $file (@student_files) {
  # Check whether student record already exists in staff records, if it does skip the
  # record (we don't want to import student records twice)
	unless ($staff{$file}) {
      # Concatenate the student record file's contents onto the existing output file's
      # contents
    	system ("cat $file >> $outfile");
      # Print to stdout (informational)
    	system ("echo >> $outfile");
    }
  # Delete the stduent record file (note that this happens whether the record was added
  # to the output file or not)
	system ("rm -f $file");
}

# Open outfile file and add closing tag for XML root element, close output file
open FH, ">>$outfile" or die $!;
print FH "</userRecords>\n";

close FH;

# Zip the output file
$zipfile = $outfile;
$zipfile =~ s/\.xml/.zip/;
system ("zip -q $zipfile $outfile");
# Delete the unzipped output file
system ("rm -f $outfile");

# Print zipped file name to stdout (informational)
$zipfile =~ s|^\.\./||;
print "$zipfile\n";
