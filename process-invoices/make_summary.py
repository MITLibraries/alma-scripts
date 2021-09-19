#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import re
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

print("--- MIT Libraries--- Alma to SAP Invoice Feed")
print()
print()
print()
print("Data file: " + file)
print()
cfile = re.sub("d", "c", file, 1)
print("Control file: " + cfile)
print()
print()
print()

howmany = 0
total = 0
for line in lines:
    if (line):
        mydict = invoice_sap.get_values_as_dict(line, invoice_sap.DFILE)
        if mydict['type'] == 'B':
            print(f"{mydict['vname']: <35}", end="    ")
            print(f"{mydict['extref']: <16}", end="    ")
            print(mydict['amount'])
            total += float(mydict['amount'])
            howmany += 1

print()
print()
print("Total payment:", end="       ")
print("${:,.2f}".format(total))
print()
print("Invoice count:", end="       ")
print(howmany)
print()
print()
print("Authorized signature __________________________________")
