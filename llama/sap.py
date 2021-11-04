"""Module with functions necessary for processing invoices to send to SAP."""

import json
import logging
from datetime import datetime

from llama.alma import Alma_API_Client
from llama.ssm import SSM

logger = logging.getLogger(__name__)

with open("config/countries.json") as f:
    COUNTRIES = json.load(f)


def retrieve_sorted_invoices(alma_client):
    """Retrieve sorted invoices from Alma.

    Retrieve invoices from Alma with status 'Waiting to be sent' and return them
    sorted by vendor code.
    """
    data = alma_client.get_invoices_by_status("Waiting to be Sent")
    return sorted(data["invoice"], key=lambda i: i["vendor"].get("value", 0))


def extract_invoice_data(alma_client: Alma_API_Client, invoice_record: dict) -> dict:
    """Extract data needed for SAP from Alma invoice record and return as a dict.

    Raises:
        KeyError: if any of the mandatory record fields is missing.
    """
    vendor_code = invoice_record["vendor"]["value"]
    invoice_data = {
        "date": datetime.strptime(invoice_record["invoice_date"], "%Y-%m-%dZ"),
        "id": invoice_record["id"],
        "type": purchase_type(vendor_code),
        "payment method": invoice_record["payment_method"]["value"],
        "total amount": invoice_record["total_amount"],
        "currency": invoice_record["currency"]["value"],
        "vendor": populate_vendor_data(alma_client, vendor_code),
    }
    return invoice_data


def purchase_type(vendor_code: str) -> str:
    """Determine purchase type (serial or monograph) based on vendor code."""
    if vendor_code.endswith("-S"):
        return "serial"
    return "monograph"


def populate_vendor_data(alma_client: Alma_API_Client, vendor_code: str) -> dict:
    """Populate a dict with vendor data needed for SAP.

    Given a vendor code and an authenticated Alma client, retrieve the full vendor
    record from Alma and return a dict populated with the vendor data needed for SAP.
    """
    vendor_record = alma_client.get_vendor_details(vendor_code)
    address = determine_vendor_payment_address(vendor_record)
    vendor_data = {
        "name": vendor_record["name"],
        "code": vendor_code,
        "address": {
            "lines": address_lines_from_address(address),
            "city": address.get("city"),
            "state or province": address.get("state_province"),
            "postal code": address.get("postal_code"),
            "country": country_code_from_address(address),
        },
    }
    return vendor_data


def determine_vendor_payment_address(vendor_record: dict) -> dict:
    """Determine payment address from Alma vendor record.

    Given an Alma vendor record, determines which of the addresses in the record is
    the payment address and returns it. If no address is marked as the payment address,
    returns the first address in the record. If there is no address field in the
    record, returns "No vendor address in record" as a default.
    """
    try:
        for address in vendor_record["contact_info"]["address"]:
            if address["address_type"][0]["value"] == "payment":
                return address
        return vendor_record["contact_info"]["address"][0]
    except KeyError:
        return "No vendor address in record"


def address_lines_from_address(address: dict) -> list:
    """Get non-null address lines from an Alma vendor address.

    Given an address from an Alma vendor record, return a list of the non-null
    address lines from the address.
    """
    line_names = ["line1", "line2", "line3", "line4", "line5"]
    lines = [
        address.get(line_name)
        for line_name in line_names
        if address.get(line_name) is not None
    ]
    return lines


def country_code_from_address(address: dict) -> str:
    """Get SAP country code from an Alma vendor address.

    Returns a country code as required by SAP from a file of country/code
    lookup pairs, given a vendor address dict from an Alma vendor record. If there is
    no country value in the record OR the country value does not exist in the lookup
    file, returns 'US' as a default.
    """
    try:
        country = address["country"]["value"]
        return COUNTRIES[country]
    except KeyError:
        return "US"


def generate_sap_sequence(old_sap_sequence: str, date: str, sequence_type: str) -> str:
    """Generate new SAP sequence by adding 1, adding new date, and a mono or ser type."""
    split_sequence = old_sap_sequence.split(",")
    split_sequence[0] = str(int(split_sequence[0]) + 1)
    split_sequence[1] = date.ljust(14, "0")
    split_sequence[2] = sequence_type
    new_sap_sequence = ",".join(split_sequence)
    return new_sap_sequence


def update_sap_sequence_parameter(
    old_sap_sequence: str,
    date: str,
    sequence_type: str,
    parameter_key: str,
    parameter_type: str,
) -> str:
    """Get SAP sequence parameter, update it according to specified values, and update in
    Parameter Store."""
    ssm = SSM()
    old_sap_sequence = ssm.get_parameter_value(parameter_key)
    new_sap_sequence = generate_sap_sequence(old_sap_sequence, date, sequence_type)
    response = ssm.update_parameter_value(
        parameter_key, new_sap_sequence, parameter_type
    )
    return response
