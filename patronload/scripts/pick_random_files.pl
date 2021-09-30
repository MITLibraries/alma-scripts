#!/usr/bin/perl -w

# This script is not in use and can be deleted.

use strict;
use List::Util qw(shuffle);

my $working_dir = uc(shift) || 'STAFF';

my $date = `date +%Y%m%d%H%M%S`;
chomp $date;

chdir $working_dir;

my @files = glob("*.xml");
exit if !$files[0];

my @array = shuffle(@files);

my %seen;
my %nums;
my $i = 0;
while ($i < 10) {
	my $num = $array[ int(rand(@array)) ];
	next if ($seen{$num}++);
	$i++;
	$nums{$num}++;	 
}

#my $outfile = '../SEND/' . lc($working_dir) . '_' . $date . '.xml';
#open FH, ">$outfile" or die $!;

#print FH "<?xml version='1.0' encoding='UTF-8'?>\n";
#print FH "<userRecords>\n";
#close FH;

foreach my $file (keys %nums) {
	print ("$file\n");
}

#open FH, ">>$outfile" or die $!;
#print FH "</userRecords>\n";

#close FH;

#print "$outfile\n";
