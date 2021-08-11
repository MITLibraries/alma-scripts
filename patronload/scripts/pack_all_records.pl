#!/usr/bin/perl -w
use strict;

my $working_dir = uc(shift) || 'STAFF';

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

foreach my $file (@files) {
	system ("cat $file >> $outfile");
	system ("echo >> $outfile");
}

open FH, ">>$outfile" or die $!;
print FH "</userRecords>\n";

close FH;

my $zipfile = $outfile;
$zipfile =~ s/\.xml/.zip/;
system ("zip $zipfile $outfile");

print "$zipfile\n";
