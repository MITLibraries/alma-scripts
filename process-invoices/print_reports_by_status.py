#!/usr/bin/python3

"""
Take a file of Alma invoice IDs and create report files
"""

import ast
import sys
import re
import json
import urllib
from urllib.request import urlopen
from datetime import date
from datetime import datetime
import configparser
import invoice_sap


config = configparser.ConfigParser()
config.read('invoice.config')
alma = config['ALMA']

today = date.today().strftime("%m/%d/%Y")
today2 = date.today().strftime("%Y%m%d")
rightnow = datetime.now().strftime("%Y%m%d%H%M%S")

apikey = alma['apikey']
host = alma['apihost']

file = open("countries.txt", "r")

contents = file.read()
countries = ast.literal_eval(contents)

file.close()

mfile = "review_mono_report_" + rightnow + ".txt"
sfile = "review_serial_report_" + rightnow + ".txt"
monos = open(mfile, "w")
serials = open(sfile, "w")

iIDS = "invoice_ids_" + rightnow + ".txt"
invoice_ids = open(iIDS, "w")
print(iIDS)

oIDS = "invoice_special_" + rightnow + ".txt"
other_ids = open(oIDS, "w")
why = "why_" + rightnow + ".txt"
why_note = open(why, "w")

typer = {'S': serials, 'M': monos}

# Valid statuses:
# InReview, InApproval, Waiting to be Sent, Ready to be Paid, ACTIVE, CLOSED
status = ''
if len(sys.argv) == 1:
    status = 'Waiting to be Sent'
else:
    status = sys.argv[1]

# Important! We need to figure out how to handle when there are more than a
# hundred invoices!
url = 'https://' + host
url += '/almaws/v1/acq/invoices?format=json&limit=100'
url += '&apikey=' + apikey
url += '&invoice_workflow_status=' + urllib.parse.quote_plus(status)

response = urlopen(url)
data = json.loads(response.read())
# sort by vendor code
data['invoice'].sort(key=invoice_sap.extract_vendor)

HEAD = """

                             MIT LIBRARIES


"""

for invoice in data['invoice']:

    invoice_date = invoice['invoice_date']
    datetime_object = datetime.strptime(invoice_date, '%Y-%m-%dZ')
    num = invoice['number'] + datetime_object.strftime('%y%m%d')
    vendor_info = invoice_sap.get_vendor(invoice['vendor']['value'], host, apikey)

    type = ''
    if re.search("-S$", vendor_info['code']):
        type = 'S'
    else:
        type = 'M'

    if invoice['payment_method']['value'] == 'ACCOUNTINGDEPARTMENT':
        invoice_ids.write(invoice['id'] + "\n")
    else:
        other_ids.write(invoice['id'] + "\n")
        why_note.write("Status not ACCOUNTINGDEPARTMENT:\t")
        why_note.write(invoice['number'] + "\t")
        why_note.write(vendor_info['name'] + "\t")
        why_note.write(vendor_info['code'] + "\n")

    typer[type].write(HEAD)
    typer[type].write("Date: " + today + "                          ")
    typer[type].write("Vendor code   : " + vendor_info['code'])
    typer[type].write("\n")
    typer[type].write("                                          ")
    typer[type].write("Accounting ID : ")
    typer[type].write("\n\n")

    typer[type].write("Vendor:  " + vendor_info['name'])
    typer[type].write("\n")

    address_found = 0
    for address in vendor_info['contact_info']['address']:
        add_type = ''
        for ptype in address['address_type']:
            if ptype['value'] == 'payment':
                add_type = 'payment'
        if add_type == 'payment':
            address_found = 1
            if address['line1']:
                typer[type].write("         " + invoice_sap.xstr(address['line1']))
                typer[type].write("\n")
            if address['line2']:
                typer[type].write("         " + address['line2'])
                typer[type].write("\n")
            if address['line3']:
                typer[type].write("         " + address['line3'])
                typer[type].write("\n")
            if address['line4']:
                typer[type].write("         " + address['line4'])
                typer[type].write("\n")
            if address['line5']:
                typer[type].write("         " + address['line5'])
                typer[type].write("\n")
            if 'state_province' in address:
                typer[type].write("         " + address['city'] + ", ")
                typer[type].write(address['state_province'] + " ")
                typer[type].write(address['postal_code'])
                typer[type].write("\n")
            else:
                if address['city']:
                    typer[type].write("         " + address['city'])
                else:
                    typer[type].write("\n")
                if 'postal_code' in address:
                    typer[type].write("         " + address['postal_code'])
                    typer[type].write("\n")
            country = address['country']['value']
            if not country:
                country = 'US'
            typer[type].write("         " + country)
            typer[type].write("\n")

    if address_found == 0:
        for address in vendor_info['contact_info']['address']:
            my_type = address['address_type'][0]['value']
            typer[type].write("         " + invoice_sap.xstr(address['line1']))
            typer[type].write("\n")
            if address['line2']:
                typer[type].write("         " + address['line2'])
                typer[type].write("\n")
            if address['line3']:
                typer[type].write("         " + address['line3'])
                typer[type].write("\n")
            if address['line4']:
                typer[type].write("         " + address['line4'])
                typer[type].write("\n")
            if address['line5']:
                typer[type].write("         " + address['line5'])
                typer[type].write("\n")
            if 'state_province' in address:
                typer[type].write("         " + address['city'] + ", ")
                typer[type].write(address['state_province'] + " ")
                typer[type].write(address['postal_code'])
                typer[type].write("\n")
            else:
                if address['city']:
                    typer[type].write("         " + address['city'])
                else:
                    typer[type].write("\n")
                if 'postal_code' in address:
                    typer[type].write("         " + address['postal_code'])
                    typer[type].write("\n")
            country = address['country']['value']
            if not country:
                country = 'US'
            country = country.strip()
            country = country.upper()
            country = countries[country]
            typer[type].write("         " + country)
            typer[type].write("\n")

    typer[type].write("\n")
    typer[type].write("Invoice no.            Fiscal Account     Amount" +
                      "            Inv. Date")
    typer[type].write("\n")
    typer[type].write("------------------     -----------------  " +
                      "-------------     ----------")
    typer[type].write("\n")

    total = 0

    # need to combine lines with the same external_id
    funds = {}
    for invoice_line in invoice['invoice_lines']['invoice_line']:
        if (len(invoice_line['fund_distribution']) > 0 and
           invoice_line['fund_distribution'][0]['amount'] > 0):
            for fd in invoice_line['fund_distribution']:
                external_id = invoice_sap.get_fund(fd['fund_code']['value'],
                                                   host, apikey).strip()
                if external_id in funds.keys():
                    funds[external_id] += fd['amount']
                else:
                    funds[external_id] = fd['amount']
                total += fd['amount']
    for fund in funds:
        parts = fund.split("-")
        typer[type].write(f"{num: <22} {parts[0]} {parts[1]}" + "     ")
        typer[type].write("{:,.2f}".format(funds[fund]) + "         ")
        typer[type].write(datetime_object.strftime('%m/%d/%Y'))
        typer[type].write("\n")

    typer[type].write("\n\n")
    typer[type].write("Total/Currency:             " +
                      "{:,.2f}".format(total) +
                      "      " + invoice['currency']['value'])
    typer[type].write("\n\n")
    typer[type].write("Payment Method:  " + invoice['payment_method']['value'])

    typer[type].write("\n\n\n")
    typer[type].write("                       Departmental Approval " +
                      "_________________________________")
    typer[type].write("\n\n")
    typer[type].write("                       Financial Services Approval " +
                      "____________________________")
    typer[type].write("\n\n")

    typer[type].write("\n\f")
