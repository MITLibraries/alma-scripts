import datetime
import glob
import xml.etree.ElementTree as ET

import llama.config as config
from llama.alma import Alma_API_Client

TODAY = datetime.date.today()

# Update empty invoice XML file that gets posted to Alma to use today's date
tree = ET.parse("empty.xml")
root = tree.getroot()
voucher_date = root.find(".//voucher_date")
voucher_date.text = TODAY.strftime("%Y-%m-%dT12:%M:%SZ")
tree.write("output-files/empty.xml")

# Update invoices status in Alma for all invoice IDs in
# output-files/invoice_ids_YYYYMMDDhhmmss.txt
alma_client = Alma_API_Client(config.get_alma_api_key("ALMA_API_ACQ_READ_WRITE_KEY"))
alma_client.set_content_headers("application/xml", "application/xml")
today_string = TODAY.strftime("%Y%m%d")
files = glob.glob(f"output-files/invoice_ids_{today_string}*.txt")
with open(files[0]) as f:
    for line in f.readlines():
        invoice_id = line.strip()
        paid_xml = alma_client.mark_invoice_paid(invoice_id, "output-files/empty.xml")
        with open(f"output-files/paid_{invoice_id}.xml") as f:
            f.write(paid_xml)
        print(f"Invoice #{invoice_id} marked as Paid in Alma")
