import datetime
import glob
import sys

import requests
from defusedxml import ElementTree as ET

sys.path.append("..")
from llama.alma import Alma_API_Client
import llama.config as config

TODAY = datetime.date.today()
count_total_invoices = 0
count_invoices_updated = 0
count_invoice_errors = 0

# Update empty invoice XML file that gets posted to Alma to use today's date
tree = ET.parse("empty_invoice.xml")
root = tree.getroot()
voucher_date = root.find(".//voucher_date")
voucher_date.text = TODAY.strftime("%Y-%m-%dT12:%M:%SZ")
tree.write("output-files/empty.xml")

# Update invoices status in Alma for all invoice IDs in
# output-files/invoice_ids_YYYYMMDDhhmmss.txt and
# output-files/invoice_special_YYYYMMDDhhmmss.txt
alma_client = Alma_API_Client(config.get_alma_api_key("ALMA_API_ACQ_READ_WRITE_KEY"))
alma_client.set_content_headers("application/xml", "application/xml")

today_string = TODAY.strftime("%Y%m%d")
invoice_files = glob.glob(f"output-files/invoice_ids_{today_string}*.txt")
special_invoice_files = glob.glob(f"output-files/invoice_special_{today_string}*.txt")
with open(invoice_files[0]) as f:
    invoice_ids = f.readlines()
with open(special_invoice_files[0]) as f:
    invoice_ids.extend(f.readlines())

for item in invoice_ids:
    count_total_invoices += 1
    invoice_id = item.strip()
    print("Marking invoice as Paid in Alma")
    try:
        paid_xml = alma_client.mark_invoice_paid(
                               invoice_id, "output-files/empty.xml")
        print(f"Invoice #{invoice_id} marked as Paid in Alma\n")
        with open(f"output-files/paid_{invoice_id}.xml", "w") as f:
            f.write(paid_xml)
            count_invoices_updated += 1
    except requests.HTTPError as e:
        print(f"Error marking invoice #{invoice_id} as paid in Alma")
        print(f"{e.response.text}\n")

print("'update_invoice_statuses' process complete")
print("Summary:")
print(f"  Total invoices processed: {count_total_invoices}")
print(f"  Invoices marked as paid in Alma: {count_invoices_updated}")
print(
    f"  Invoices not successfully marked as paid in Alma: {count_invoice_errors}"
)
