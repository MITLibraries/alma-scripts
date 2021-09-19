#!/usr/bin/python3

''' Just a debugging tool. Parse a SAP control file and
    make it human-eyes friendly. '''

import sys
import invoice_sap

file = ''
if len(sys.argv) == 1:
    print("file name expected!")
    sys.exit()
else:
    file = sys.argv[1]

f = open(file)
lines = f.read().splitlines()
f.close()

for line in lines:
    if (line):
        mydict = invoice_sap.get_values_as_dict(line, invoice_sap.CFILE)
        print("Bytes:      " + mydict['bytes'])
        print("Records:    " + mydict['records'])
        print("Credit:     " + mydict['credit'])
        print("Debit:      " + mydict['debit'])
        print("Ctl3:       " + mydict['ctl3'])
        print("Ctl4:       " + mydict['ctl4'])
