#!/usr/bin/perl
use strict;

my $id = shift or die "invoice number required";
my $op = shift or die "what status?";

my $apikey = 'YOUR_APIKEY_HERE';

$id =~ s/[^0-9]//g;
die "valid invoice number required" unless $id;

$op = lc($op);
my $stub;

if ($op eq 'reject') {
    $stub = 'reject.xml';
} elsif (($op eq 'paid') || ($op eq 'mark_in_erp') || ($op eq 'process_invoice')) {
     $stub = 'empty.xml';
}

die "invalid status!!!" unless $stub;

my $curl = 'curl -s  -H "Content-Type: application/xml" -X POST --data "@';
$curl .= $stub . '"';
my $url = 'https://api-na.hosted.exlibrisgroup.com/almaws/v1/acq/invoices/';
$url .= $id . "?op=$op";
$url .= '&apikey='. $apikey;

my $out = $op . "_$id.xml";
#print "$curl '$url' |xmllint --format - >$out";
system ("$curl '$url' |xmllint --format - >$out");

print "\n$out created\n";
