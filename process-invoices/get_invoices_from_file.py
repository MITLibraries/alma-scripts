#!/usr/bin/python3
# -*- coding: utf-8 -*-

import ast
import sys
import os
import re
import json
from urllib.request import urlopen
from datetime import date
from datetime import datetime
import invoice_sap

sys.path.append("..")
from llama.alma import Alma_API_Client
import llama.config as config

# Create Alma API client
alma_client = Alma_API_Client(config.get_alma_api_key("ALMA_API_ACQ_READ_KEY"))
alma_client.set_content_headers("application/json", "application/json")

today = date.today().strftime("%Y%m%d")
rightnow = datetime.now().strftime("%Y%m%d%H%M%S")

count_total_invoices = 0
count_monographs = 0
count_serials = 0

file = open("countries.txt", "r")

contents = file.read()
countries = ast.literal_eval(contents)

file.close()

note = 'alma' + date.today().strftime("%y%m%d")

mcmd = "./ser -f seq-sap -t mono -n " + note + " -i"
mstamp = os.popen(mcmd).read().strip()
mfile = "output-files/dlibsapg." + mstamp
monos = open(mfile, "w")


scmd = "./ser -f seq-sap -t ser -n " + note + " -i"
sstamp = os.popen(scmd).read().strip()
sfile = "output-files/dlibsapg." + sstamp
serials = open(sfile, "w")

typer = {'S': serials, 'M': monos}

file = ''
if len(sys.argv) == 1:
    print("file name expected!")
    sys.exit()
else:
    file = sys.argv[1]

f = open(file)
lines = f.read().splitlines()
f.close()

count_total_invoices = len(lines)
print(f"Begin processing {count_total_invoices} invoices\n")

for line in lines:
    if (line):
        print(f"Processing invoice #{line}")
        print("Retrieving invoice from Alma")
        invoice = alma_client.get_invoice(line)
        print(f"Invoice #{line} retrieved from Alma")
        datetime_object = datetime.strptime(invoice['invoice_date'], '%Y-%m-%dZ')
        invoice_date = datetime_object.strftime('%y%m%d')
        biginvoice = invoice['number'] + invoice_date
        print("Retrieving vendor info from Alma")
        vendor_info = alma_client.get_vendor_details(invoice['vendor']['value'])
        print(f"Vendor {invoice['vendor']['value']} data retrieved from Alma")
        vendornum = '400000'
        netpay = "{:16.2f}".format(invoice['total_amount'])
        netsign = ' '
        pay_meth = ' '
        vname = vendor_info['name']
        some_text = ' '
        city = ' '

        if vendor_info["code"].endswith("-S"):
            type = "S"
            count_serials += 1
        else:
            type = "M"
            count_monographs += 1

        address_found = 0
        for address in vendor_info['contact_info']['address']:
            add_type = ''
            for ptype in address['address_type']:
                if ptype['value'] == 'payment':
                    add_type = 'payment'
            if add_type == 'payment':
                address_found = 1
                add1 = address['line1']
                add2 = address['line2']
                add3 = address['line3']
                if 'city' in address:
                    city = address['city']
                else:
                    city = ' '
                if 'state_province' in address:
                    state = address['state_province']
                else:
                    state = ' '
                if 'postal_code' in address:
                    zip = address['postal_code']
                else:
                    zip = ' '
                country = address['country']['value']
                if not country:
                    country = 'UNITED STATES OF AMERICA'

        if address_found == 0:
            for address in vendor_info['contact_info']['address']:
                add1 = address['line1']
                add2 = address['line2']
                add3 = address['line3']
                if 'city' in address:
                    city = address['city']
                else:
                    city = ' '
                if 'state_province' in address:
                    state = address['state_province']
                else:
                    state = ' '
                if 'postal_code' in address:
                    zip = address['postal_code']
                else:
                    zip = ' '
                country = address['country']['value']
                if not country:
                    country = 'US'

        country = country.upper()
        country = countries[country]
        if not city:
            city = ' '
        ispobox = ' '
        tmp1 = add1.lower()
        tmp1 = tmp1.replace(" ", "")
        tmp1 = tmp1.replace(".", "")
        if re.search("pobox", tmp1):
            tmp1 = tmp1.replace("pobox", "")
            add1 = ' '
            add2 = tmp1
            ispobox = 'X'

        if add2:
            tmp2 = add2.lower()
            tmp2 = tmp2.replace(" ", "")
            tmp2 = tmp2.replace(".", "")
            if re.search("pobox", tmp2):
                tmp2 = tmp2.replace("pobox", "")
                add2 = tmp2
                ispobox = 'X'
        else:
            add2 = " "
        if not add3:
            add3 = " "

        typer[type].write('B')
        typer[type].write(today)
        typer[type].write(today)
        typer[type].write(f"{str(biginvoice): <16.16}")
        typer[type].write('X000')
        typer[type].write(vendornum)
        typer[type].write(netpay)
        typer[type].write(netsign)
        typer[type].write(pay_meth)
        typer[type].write('       X')
        typer[type].write(f"{str(vname): <35.35}")
        typer[type].write(f"{str(city): <35.35}")
        typer[type].write(f"{str(add1): <35.35}")
        typer[type].write(ispobox)
        typer[type].write(f"{str(add2): <35.35}")
        typer[type].write(f"{str(zip): <10.10}")
        typer[type].write(f"{str(state): <3.3}")
        typer[type].write(f"{str(country): <3.3}")
        typer[type].write(f"{str(some_text): <50.50}")
        typer[type].write(f"{str(add3): <35.35}")
        typer[type].write("\n")
        # do we need to combine lines with the same external_id??
        funds = {}
        count = 0
        for invoice_line in invoice['invoice_lines']['invoice_line']:
            if len(invoice_line['fund_distribution']) > 0:
                for fd in invoice_line['fund_distribution']:
                    print("Retrieving fund info from Alma")
                    fund_info = alma_client.get_fund_by_code(fd["fund_code"]["value"])
                    print(f"Fund {fd['fund_code']['value']} data retrieved from Alma")
                    external_id = fund_info["fund"][0]["external_id"].strip()
                    if external_id in funds.keys():
                        funds[external_id] += fd['amount']
                    else:
                        funds[external_id] = fd['amount']
        howmany = len(funds.keys())
        for fund in funds:
            count += 1
            parts = fund.split("-")
            if count == howmany:
                typer[type].write('D')
            else:
                typer[type].write('C')
            typer[type].write(f"{str(parts[1]): <10.10}")
            typer[type].write(f"{str(parts[0]): <12.12}")
            thispay = "{:16.2f}".format(funds[fund])
            typer[type].write(thispay)
            typer[type].write(" ")
            typer[type].write("\n")
        print(f"Finished processing invoice #{invoice['id']}\n")

serials.close()
monos.close()

print("'get_invoices_from_file' process complete")
print("Summary:")
print(f"  Total invoices processed: {count_total_invoices}")
print(f"  Monograph invoices: {count_monographs}")
print(f"  Serial invoices: {count_serials}")
print(f"  SAP sequence numbers added: {mstamp}, {sstamp}")