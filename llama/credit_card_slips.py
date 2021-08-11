import os

import requests
from defusedxml import ElementTree as ET


def create_credit_card_slips(date):
    """Create credit card slips XML string."""
    alma_json_headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f'apikey {os.environ["API_KEY"]}',
    }

    po_payload = {"status": "ACTIVE", "limit": "100", "offset": 0}

    credit_card_slips_xml = ET.fromstring("<html></html>")

    po_lines = ""
    while po_lines != []:
        response = requests.get(
            f'{os.environ["API_URL"]}acq/po-lines',
            params=po_payload,
            headers=alma_json_headers,
        ).json()
        po_lines = response.get("po_line", [])
        for po_line_stub in [p for p in po_lines if p["created_date"] == f"{date}Z"]:
            po_line_record = requests.get(
                f'{os.environ["API_URL"]}acq/po-lines/{po_line_stub["number"]}',
                headers=alma_json_headers,
            ).json()
            if (
                "acquisition_method" in po_line_record
                and po_line_record["acquisition_method"]["desc"] == "Credit Card"
            ):
                value_dict = create_dict_from_po_line_record(
                    po_line_record, alma_json_headers
                )
                credit_card_slip = load_xml_template(
                    "config/credit_card_slip_template.xml"
                )
                for k, v in value_dict.items():
                    for element in credit_card_slip.findall(f'.//td[@class="{k}"]'):
                        element.text = v
                credit_card_slips_xml.append(credit_card_slip)
        po_payload["offset"] += 100
    credit_card_slips_xml_string = ET.tostring(
        credit_card_slips_xml, encoding="unicode", method="xml"
    )
    return credit_card_slips_xml_string


def create_dict_from_po_line_record(po_line_record, alma_json_headers):
    """Create dict of the required data for credit card slips from an Alma PO line
    record. The keys of the dict map to the appropriate element classes in the XML
    template."""
    value_dict = {}
    value_dict["vendor"] = po_line_record["vendor_account"]
    value_dict["poline"] = po_line_record["number"]

    title = get_po_title(po_line_record)
    value_dict["item_title"] = title

    price = format(float(po_line_record["price"]["sum"]), ".2f")
    value_dict["price"] = f"${price}"

    # Stakeholder requested format of date
    po_line_created_date = "".join(
        filter(str.isdigit, po_line_record["created_date"][2:])
    )
    value_dict["po_date"] = po_line_created_date
    value_dict["invoice_num"] = f"Invoice #: {po_line_created_date}{title[:3].upper()}"

    fund_code_1 = po_line_record["fund_distribution"][0]["fund_code"]["value"]
    value_dict["account_1"] = get_account_from_fund_code(fund_code_1, alma_json_headers)
    if len(po_line_record["fund_distribution"]) > 1:
        fund_code_2 = po_line_record["fund_distribution"][1]["fund_code"]["value"]
        value_dict["account_2"] = get_account_from_fund_code(
            fund_code_2, alma_json_headers
        )
    value_dict["cardholder"] = get_cardholder_from_notes(po_line_record)
    return value_dict


def get_account_from_fund_code(fund_code, alma_json_headers):
    """Get account number based on a fund code."""
    if fund_code == "":
        account = "No fund code"
    else:
        fund_payload = {"q": f"fund_code~{fund_code}"}
        response = requests.get(
            f'{os.environ["API_URL"]}acq/funds',
            params=fund_payload,
            headers=alma_json_headers,
        ).json()
        account = response["fund"][0]["external_id"]
    return account


def get_cardholder_from_notes(po_line_record):
    """Get cardholder note with CC- prefix from Alma PO line record."""
    cardholder = "No cardholder note"
    for note in [
        n
        for n in po_line_record["note"]
        if "note" in po_line_record and n["note_text"].startswith("CC-")
    ]:
        cardholder = note["note_text"][3:]
    return cardholder


def get_po_title(po_line_record):
    """Retrieve title from Alma PO line record. PO line records store the title as a
    null value if no item is attached but a string is required for the invoice number."""
    title = po_line_record["resource_metadata"]["title"]
    title = "Unknown title" if title is None else title
    return title


def load_xml_template(xml_file):
    """Create an Elementree object from an XML file template."""
    tree = ET.parse(xml_file)
    root = tree.getroot()
    return root
