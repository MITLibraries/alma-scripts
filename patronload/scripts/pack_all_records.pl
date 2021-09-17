#!/usr/bin/perl -w
use strict;

my $working_dir = 'STAFF';

my $date = `date +%Y%m%d%H%M%S`;
chomp $date;

chdir $working_dir;

my @files = glob("*.xml");
exit if !$files[0];

my $outfile = '../SEND/' . lc($working_dir) . '_' . $date . '.xml';
open FH, ">$outfile" or die $!;

print FH "<?xml version='1.0' encoding='UTF-8'?>\n";
print FH "<userRecords>\n";
close FH;

my %staff;
foreach my $file (@files) {
	system ("cat $file >> $outfile");
	system ("echo >> $outfile");
	system ("rm -f $file");
	$staff{$file}++;
}

open FH, ">>$outfile" or die $!;
print FH "</userRecords>\n";

close FH;

my $zipfile = $outfile;
$zipfile =~ s/\.xml/.zip/;
system ("zip -q $zipfile $outfile");
system ("rm -f $outfile");

$zipfile =~ s|^\.\./||;
print "$zipfile\n";

$working_dir = 'STUDENT';

chdir '..';
chdir $working_dir;

my @student_files = glob("*.xml");
exit if !$student_files[0];

$outfile = '../SEND/' . lc($working_dir) . '_' . $date . '.xml';
open FH, ">$outfile" or die $!;

print FH "<?xml version='1.0' encoding='UTF-8'?>\n";
print FH "<userRecords>\n";
close FH;

foreach my $file (@student_files) {
	unless ($staff{$file}) {
    	system ("cat $file >> $outfile");
    	system ("echo >> $outfile");
    }
	system ("rm -f $file");
}

open FH, ">>$outfile" or die $!;
print FH "</userRecords>\n";

close FH;

$zipfile = $outfile;
$zipfile =~ s/\.xml/.zip/;
system ("zip -q $zipfile $outfile");
system ("rm -f $outfile");

$zipfile =~ s|^\.\./||;
print "$zipfile\n";
