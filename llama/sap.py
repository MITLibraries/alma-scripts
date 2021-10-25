"""Module with functions necessary for processing invoices to send to SAP."""

import json
import logging
from datetime import datetime
from typing import List, Tuple

from llama.alma import Alma_API_Client

logger = logging.getLogger(__name__)

with open("config/countries.json") as f:
    COUNTRIES = json.load(f)


def retrieve_sorted_invoices(alma_client):
    """Retrieve sorted invoices from Alma.

    Retrieve invoices from Alma with status 'Waiting to be sent' and return them
    sorted by vendor code.
    """
    data = list(alma_client.get_invoices_by_status("Waiting to be Sent"))
    return sorted(data, key=lambda i: i["vendor"].get("value", 0))


def extract_invoice_data(alma_client: Alma_API_Client, invoice_record: dict) -> dict:
    """Extract data needed for SAP from Alma invoice record and return as a dict.

    Raises:
        KeyError: if any of the mandatory record fields is missing.
    """
    vendor_code = invoice_record["vendor"]["value"]
    invoice_data = {
        "date": datetime.strptime(invoice_record["invoice_date"], "%Y-%m-%dZ"),
        "id": invoice_record["id"],
        "number": invoice_record["number"],
        "type": purchase_type(vendor_code),
        "payment method": invoice_record["payment_method"]["value"],
        "total amount": invoice_record["total_amount"],
        "currency": invoice_record["currency"]["value"],
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


def populate_fund_data(
    alma_client: Alma_API_Client, invoice_record: dict, retrieved_funds: dict
) -> Tuple[dict, dict]:
    """Populate a dict with fund data needed for SAP.

    Given an invoice record, a dict of already retrieved funds, and an authenticated
    Alma client, return a dict populated with the fund data needed for SAP.

    Note: Also returns a dict of all fund records retrieved from Alma so we can pass
    that to subsequent calls to this function. That way we only call the Alma API once
    throughout the entire process for each fund we need, rather than retrieving the
    same fund record every time the fund appears in an invoice.
    """
    fund_data = {}
    invoice_lines_total = 0
    for invoice_line in invoice_record["invoice_lines"]["invoice_line"]:
        for fund_distribution in invoice_line["fund_distribution"]:
            fund_code = fund_distribution["fund_code"]["value"]
            amount = fund_distribution["amount"]
            try:
                fund_record = retrieved_funds[fund_code]
            except KeyError:
                logger.info(f"Retrieving data for fund {fund_code}")
                retrieved_funds[fund_code] = alma_client.get_fund_by_code(fund_code)
                fund_record = retrieved_funds[fund_code]
            external_id = fund_record["fund"][0]["external_id"].strip()
            try:
                # Combine amounts for funds that have the same external ID (AKA the
                # same MIT G/L account and cost object)
                fund_data[external_id]["amount"] += amount
            except KeyError:
                fund_data[external_id] = {
                    "amount": amount,
                    "G/L account": external_id.split("-")[0],
                    "cost object": external_id.split("-")[1],
                }
            invoice_lines_total += amount
    return fund_data, retrieved_funds


def generate_report(today: datetime, invoices: List[dict]) -> str:
    today_string = today.strftime("%m/%d/%Y")
    report = ""
    for invoice in invoices:
        report += f"\n\n{'':33}MIT LIBRARIES\n\n\n"
        report += (
            f"Date: {today_string:<36}Vendor code   : {invoice['vendor']['code']}\n"
        )
        report += f"{'Accounting ID :':>57}\n\n"
        report += f"Vendor:  {invoice['vendor']['name']}\n"
        for line in invoice["vendor"]["address"]["lines"]:
            report += f"         {line}\n"
        report += "         "
        if invoice["vendor"]["address"]["city"]:
            report += f"{invoice['vendor']['address']['city']}, "
        if invoice["vendor"]["address"]["state or province"]:
            report += f"{invoice['vendor']['address']['state or province']} "
        if invoice["vendor"]["address"]["postal code"]:
            report += f"{invoice['vendor']['address']['postal code']}"
        report += f"\n         {invoice['vendor']['address']['country']}\n\n"
        report += (
            "Invoice no.            Fiscal Account     Amount            Inv. Date\n"
        )
        report += (
            "------------------     -----------------  -------------     ----------\n"
        )
        for fund in invoice["funds"]:
            report += f"{invoice['number'] + invoice['date'].strftime('%y%m%d'):<23}"
            report += (
                f"{invoice['funds'][fund]['G/L account']} "
                f"{invoice['funds'][fund]['cost object']}     "
            )
            report += f"{invoice['funds'][fund]['amount']:<18,.2f}"
            report += f"{invoice['date'].strftime('%m/%d/%Y')}\n"
        report += "\n\n"
        report += (
            f"Total/Currency:             {invoice['total amount']:,.2f}      "
            f"{invoice['currency']}\n\n"
        )
        report += f"Payment Method:  {invoice['payment method']}\n\n\n"
        report += f"{'Departmental Approval':>44} {'':_<34}\n\n"
        report += f"{'Financial Services Approval':>50} {'':_<28}\n\n\n"
        report += "\f"
    return report
