#!/usr/bin/perl -w

# This script is not in use and can be deleted.

use strict;
use List::Util qw(shuffle);

my $working_dir = uc(shift) || 'STAFF';

my $date = `date +%Y%m%d%H%M%S`;
chomp $date;

chdir $working_dir;


my %nums;
while (<DATA>) {
	chomp;
	$nums{$_}++;	 
}

my $outfile = '../SEND/' . lc($working_dir) . '_' . $date . '_test.xml';
open FH, ">$outfile" or die $!;

print FH "<?xml version='1.0' encoding='UTF-8'?>\n";
print FH "<userRecords>\n";
close FH;

foreach my $file (sort keys %nums) {
	system ("cat $file >> $outfile");
	system ("echo >> $outfile");
}

open FH, ">>$outfile" or die $!;
print FH "</userRecords>\n";

close FH;

print "$outfile\n";
my $zipfile = $outfile;
$zipfile =~ s/\.xml/.zip/;
system ("zip $zipfile $outfile");

print "$zipfile\n";

exit;

__DATA__
919208995.xml
951329256.xml
920158891.xml
919275356.xml
918396138.xml
926651904.xml
912517238.xml
927942343.xml
929026295.xml
927719066.xml
