import requests
from defusedxml import ElementTree as ET


def create_po_line_dict(alma_api_client, po_line_record):
    """Create dict of the required data for credit card slips from a PO line record. The
    keys of the dict map to the appropriate element classes in the XML template."""
    po_line_dict = {}
    po_line_dict["vendor"] = po_line_record["vendor_account"]
    po_line_dict["poline"] = po_line_record["number"]

    title = get_po_title(po_line_record)
    po_line_dict["item_title"] = title

    price = format(float(po_line_record["price"]["sum"]), ".2f")
    po_line_dict["price"] = f"${price}"

    # Stakeholder requested format of date
    po_line_created_date = "".join(
        filter(str.isdigit, po_line_record["created_date"][2:])
    )
    po_line_dict["po_date"] = po_line_created_date
    po_line_dict[
        "invoice_num"
    ] = f"Invoice #: {po_line_created_date}{title[:3].upper()}"

    fund_code_1 = po_line_record["fund_distribution"][0]["fund_code"]["value"]
    po_line_dict["account_1"] = get_account_from_fund_code(alma_api_client, fund_code_1)
    if len(po_line_record["fund_distribution"]) > 1:
        fund_code_2 = po_line_record["fund_distribution"][1]["fund_code"]["value"]
        po_line_dict["account_2"] = get_account_from_fund_code(
            alma_api_client, fund_code_2
        )
    po_line_dict["cardholder"] = get_cardholder_from_notes(po_line_record)
    return po_line_dict


def create_po_line_dicts(alma_api_client, full_po_line_records):
    """Create PO line dicts from a set of full PO line records and return a generator for
    easier use by other functions."""
    for full_po_line_record in full_po_line_records:
        po_line_dict = create_po_line_dict(
            alma_api_client,
            full_po_line_record,
        )
        yield po_line_dict


def get_account_from_fund_code(client, fund_code):
    """Get account number based on a fund code."""
    if fund_code == "":
        account = "No fund code"
    else:
        fund_payload = {"q": f"fund_code~{fund_code}"}
        response = requests.get(
            f"{client.api_url}acq/funds",
            params=fund_payload,
            headers=client.api_headers,
        ).json()
        account = response["fund"][0]["external_id"]
    return account


def get_cardholder_from_notes(po_line_record):
    """Get cardholder note that begins with a CC- prefix from a PO line record."""
    cardholder = "No cardholder note"
    for note in [
        n
        for n in po_line_record["note"]
        if "note" in po_line_record and n["note_text"].startswith("CC-")
    ]:
        cardholder = note["note_text"][3:]
    return cardholder


def get_credit_card_full_po_lines_from_date(alma_api_client, date):
    """Get full PO line records for credit card purchases (acquisition_methood =
    EXCHANGEE) from the specified date and return a generator for easier use by other
    functions."""
    brief_po_lines = alma_api_client.get_brief_po_lines("EXCHANGE")
    for brief_po_line in (p for p in brief_po_lines if p["created_date"] == f"{date}Z"):
        full_po_line = alma_api_client.get_full_po_line(brief_po_line["number"])
        yield full_po_line


def get_po_title(po_line_record):
    """Retrieve title from PO line record. PO line records store the title as a null
    value if no item is attached but a string is required for generating the invoice
    number."""
    title = po_line_record["resource_metadata"]["title"]
    title = "Unknown title" if title is None else title
    return title


def load_xml_template(xml_file):
    """Create Elementree object using XML template."""
    tree = ET.parse(xml_file)
    xml_template = tree.getroot()
    return xml_template


def populate_credit_card_slip(xml_template, po_line_dict):
    """Populate XML template with credit card slip data using a PO line dict with keys
    that correspond to the element classes in the XML template."""
    for k, v in po_line_dict.items():
        for element in xml_template.findall(f'.//td[@class="{k}"]'):
            element.text = v
    return xml_template


def xml_data_from_dicts(po_line_dicts):
    """Create credit card slips XML data from a set of PO line dicts."""
    xml_root = ET.fromstring("<html></html>")
    for po_line_dict in po_line_dicts:
        xml_template = load_xml_template("config/credit_card_slip_template.xml")
        xml_root.append(populate_credit_card_slip(xml_template, po_line_dict))
        credit_card_slips_xml_data = ET.tostring(
            xml_root, encoding="unicode", method="xml"
        )
    return credit_card_slips_xml_data
