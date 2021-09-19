#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import re
import os
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

bytes = os.path.getsize(file)

total = 0
howmany = 0
for line in lines:
    if (line):
        howmany += 1
        mydict = invoice_sap.get_values_as_dict(line, invoice_sap.DFILE)
        if mydict['type'] == 'B':
            # we want the amount in pennies, not dollars
            # i.e., floats are evil
            amount = re.sub(r'\.', "", mydict['amount'], 1)
            total += int(amount)

cfile = re.sub("d", "c", file, 1)
c = open(cfile, "w")

c.write('{:016d}'.format(bytes))
c.write('{:016d}'.format(howmany))
c.write('{:020d}'.format(0))

c.write('{:020d}'.format(int(total)))
c.write('{:020d}'.format(int(total)))
c.write("00100100000000000000\n")

c.close()
