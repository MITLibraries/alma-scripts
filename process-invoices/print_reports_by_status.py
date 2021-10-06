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

sys.path.append("..")
from llama.alma import Alma_API_Client
import llama.config as config

# Create some date variables for later
today = date.today().strftime("%m/%d/%Y")
today2 = date.today().strftime("%Y%m%d")
rightnow = datetime.now().strftime("%Y%m%d%H%M%S")

# Open country code config file and save in memory as a dict
file = open("countries.txt", "r")
contents = file.read()
countries = ast.literal_eval(contents)
file.close()

# Create output filenames for monograph and serials review reports and open them both
# in write mode
mfile = "output-files/review_mono_report_" + rightnow + ".txt"
sfile = "output-files/review_serial_report_" + rightnow + ".txt"
monos = open(mfile, "w")
serials = open(sfile, "w")

# Create output filename for invoice IDs file and open it in write mode
iIDS = "output-files/invoice_ids_" + rightnow + ".txt"
invoice_ids = open(iIDS, "w")
# Print the invoice IDs file filename (why?)
print(iIDS)

# Create output filename for other IDs file and why_note file and open them both in
# write mode
oIDS = "output-files/invoice_special_" + rightnow + ".txt"
other_ids = open(oIDS, "w")
why = "output-files/why_" + rightnow + ".txt"
why_note = open(why, "w")

# Dict to simplify future determination of output file to write to
typer = {"S": serials, "M": monos}

# Comment block in file, is this information used for anything?

# Valid statuses:
# InReview, InApproval, Waiting to be Sent, Ready to be Paid, ACTIVE, CLOSED

# Check command args for this script and set status accordingly. (This is never run
# with args, can be removed.)
status = ""
if len(sys.argv) == 1:
    status = "Waiting to be Sent"
else:
    status = sys.argv[1]

# Create Alma API client
alma_client = Alma_API_Client(config.get_alma_api_key("ALMA_API_ACQ_READ_KEY"))
alma_client.set_content_headers("application/json", "application/json")

# Get invoices waiting to be sent
data = alma_client.get_invoices_by_status("Waiting to be Sent")

# Sort results by vendor code
data["invoice"].sort(key=invoice_sap.extract_vendor)

# HEAD variable used for output reports
HEAD = """

                             MIT LIBRARIES


"""

# Loop through each invoice record in the sorted API response
for invoice in data["invoice"]:

    # Extract invoice_date field and convert to a Python datetime object
    invoice_date = invoice["invoice_date"]
    datetime_object = datetime.strptime(invoice_date, "%Y-%m-%dZ")

    # Extract number field and append the string-converted invoice_date in a specified
    # format
    num = invoice["number"] + datetime_object.strftime("%y%m%d")

    # Calls a function from another module, more details there and sets result to local
    # variable vendor_info
    vendor_info = alma_client.get_vendor_details(invoice["vendor"]["value"])

    # If vendor code ends with -S, set type variable to S (for serials), otherwise set
    # to M (for monographs)
    if vendor_info["code"].endswith("-S"):
        type = "S"
    else:
        type = "M"

    # ?
    if invoice["payment_method"]["value"] == "ACCOUNTINGDEPARTMENT":
        invoice_ids.write(invoice["id"] + "\n")
    else:
        other_ids.write(invoice["id"] + "\n")
        why_note.write("Status not ACCOUNTINGDEPARTMENT:\t")
        why_note.write(invoice["number"] + "\t")
        why_note.write(vendor_info["name"] + "\t")
        why_note.write(vendor_info["code"] + "\n")

    # Write record HEAD string, today's date, vendor code, accounting id (which appears to be blank?), and vendor name to either serials or monos file based on type variable in this loop
    typer[type].write(HEAD)
    typer[type].write("Date: " + today + "                          ")
    typer[type].write("Vendor code   : " + vendor_info["code"])
    typer[type].write("\n")
    typer[type].write("                                          ")
    typer[type].write("Accounting ID : ")
    typer[type].write("\n\n")
    typer[type].write("Vendor:  " + vendor_info["name"])
    typer[type].write("\n")

    # Basically set a truth checker to false
    address_found = 0
    # Loop through addresses in vendor contact info
    for address in vendor_info["contact_info"]["address"]:
        add_type = ""
        # Set empty add_type variable to "payment" if the address type in vendor contact info is "payment"
        for ptype in address["address_type"]:
            if ptype["value"] == "payment":
                add_type = "payment"
        # If above did set add_type to "payment"...
        if add_type == "payment":
            # Update address_found to true
            address_found = 1
            # Write each line of address to either serials or monos file based on type variable in this loop, in order, if the line exists in the vendor info
            if address["line1"]:
                # Convert to empty string if the vendor info record has null value for this field
                typer[type].write("         " + invoice_sap.xstr(address["line1"]))
                typer[type].write("\n")
            if address["line2"]:
                typer[type].write("         " + address["line2"])
                typer[type].write("\n")
            if address["line3"]:
                typer[type].write("         " + address["line3"])
                typer[type].write("\n")
            if address["line4"]:
                typer[type].write("         " + address["line4"])
                typer[type].write("\n")
            if address["line5"]:
                typer[type].write("         " + address["line5"])
                typer[type].write("\n")

            # Write city, state/province, and postal code to either serials or monos file based on type variable in this loop if there is a state/provnce field, otherwise...
            if "state_province" in address:
                typer[type].write("         " + address["city"] + ", ")
                typer[type].write(address["state_province"] + " ")
                typer[type].write(address["postal_code"])
                typer[type].write("\n")
            # Write just the city and postal code to either serials or monos file based on type variable in this loop
            else:
                if address["city"]:
                    typer[type].write("         " + address["city"])
                else:
                    typer[type].write("\n")
                if "postal_code" in address:
                    typer[type].write("         " + address["postal_code"])
                    typer[type].write("\n")
            # Set country value to country field from vendor_info, with a default of US if no value in country field
            country = address["country"]["value"]
            if not country:
                country = "US"
            # Write country code to either serials or monos file based on type variable in this loop
            typer[type].write("         " + country)
            typer[type].write("\n")

    if address_found == 0:
        for address in vendor_info["contact_info"]["address"]:
            my_type = address["address_type"][0]["value"]
            typer[type].write("         " + invoice_sap.xstr(address["line1"]))
            typer[type].write("\n")
            if address["line2"]:
                typer[type].write("         " + address["line2"])
                typer[type].write("\n")
            if address["line3"]:
                typer[type].write("         " + address["line3"])
                typer[type].write("\n")
            if address["line4"]:
                typer[type].write("         " + address["line4"])
                typer[type].write("\n")
            if address["line5"]:
                typer[type].write("         " + address["line5"])
                typer[type].write("\n")
            if "state_province" in address:
                typer[type].write("         " + address["city"] + ", ")
                typer[type].write(address["state_province"] + " ")
                typer[type].write(address["postal_code"])
                typer[type].write("\n")
            else:
                if address["city"]:
                    typer[type].write("         " + address["city"])
                else:
                    typer[type].write("\n")
                if "postal_code" in address:
                    typer[type].write("         " + address["postal_code"])
                    typer[type].write("\n")
            country = address["country"]["value"]
            if not country:
                country = "US"
            country = country.strip()
            country = country.upper()
            country = countries[country]
            typer[type].write("         " + country)
            typer[type].write("\n")

    typer[type].write("\n")
    typer[type].write(
        "Invoice no.            Fiscal Account     Amount" + "            Inv. Date"
    )
    typer[type].write("\n")
    typer[type].write(
        "------------------     -----------------  " + "-------------     ----------"
    )
    typer[type].write("\n")

    total = 0

    # need to combine lines with the same external_id
    funds = {}
    for invoice_line in invoice["invoice_lines"]["invoice_line"]:
        if (
            len(invoice_line["fund_distribution"]) > 0
            and invoice_line["fund_distribution"][0]["amount"] > 0
        ):
            for fd in invoice_line["fund_distribution"]:
                fund_info = alma_client.get_fund_by_code(fd["fund_code"]["value"])
                external_id = fund_info["fund"][0]["external_id"].strip()
                if external_id in funds.keys():
                    funds[external_id] += fd["amount"]
                else:
                    funds[external_id] = fd["amount"]
                total += fd["amount"]
    for fund in funds:
        parts = fund.split("-")
        typer[type].write(f"{num: <22} {parts[0]} {parts[1]}" + "     ")
        formatted = "{:,.2f}".format(funds[fund])
        typer[type].write(formatted + (" " * (18 - len(formatted))))
        typer[type].write(datetime_object.strftime("%m/%d/%Y"))
        typer[type].write("\n")

    typer[type].write("\n\n")
    typer[type].write(
        "Total/Currency:             "
        + "{:,.2f}".format(total)
        + "      "
        + invoice["currency"]["value"]
    )
    typer[type].write("\n\n")
    typer[type].write("Payment Method:  " + invoice["payment_method"]["value"])

    typer[type].write("\n\n\n")
    typer[type].write(
        "                       Departmental Approval "
        + "__________________________________"
    )
    typer[type].write("\n\n")
    typer[type].write(
        "                       Financial Services Approval "
        + "____________________________"
    )
    typer[type].write("\n\n")
    typer[type].write("\n\f")
    typer[type].write("\n\f")
