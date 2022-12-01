"""Module with functions necessary for processing invoices to send to SAP."""

import collections
import json
import logging
from datetime import datetime
from math import fsum
from typing import List, Literal, Optional, Tuple

import flatdict

from llama import CONFIG
from llama.alma import Alma_API_Client
from llama.email import Email
from llama.sftp import SFTP
from llama.ssm import SSM

logger = logging.getLogger(__name__)

with open("config/countries.json") as f:
    COUNTRIES = json.load(f)


class FundError(Exception):
    """Exception raised for errors when retrieving a fund by code.

    Attributes:
        fund_codes: list of fund codes in an invoice that cause the error
        message: explanation of the error
    """

    def __init__(
        self,
        fund_codes,
        message=("Fund could not be retrieved by " "code, may be overexpended"),
    ):
        self.fund_codes = fund_codes
        self.message = message
        super().__init__(self.message)


class VendorAddressError(Exception):
    """Exception raised when vendor has no addresses"""


def retrieve_sorted_invoices(alma_client):
    """Retrieve sorted invoices from Alma.

    Retrieve invoices from Alma with status 'Waiting to be sent' and return them
    sorted by vendor code.
    """
    data = list(alma_client.get_invoices_by_status("Waiting to be Sent"))
    return sorted(data, key=lambda i: (i["vendor"].get("value", 0), i.get("number", 0)))


def parse_invoice_records(
    alma_client: Alma_API_Client, invoice_records: List[dict]
) -> List[dict]:
    """Parse a list of invoice records from Alma and return extracted SAP data."""
    parsed_invoices = []
    problem_invoices = []
    retrieved_vendors = {}
    retrieved_funds = {}
    for count, invoice_record in enumerate(invoice_records):
        logger.info(
            f"Extracting data for invoice {invoice_record['id']}, "
            f"record {count + 1} of {len(invoice_records)}"
        )
        invoice_data = extract_invoice_data(invoice_record)
        vendor_code = invoice_record["vendor"]["value"]
        try:
            invoice_data["vendor"] = retrieved_vendors[vendor_code]
        except KeyError:
            logger.debug(f"Retrieving data for vendor {vendor_code}")
            try:
                retrieved_vendors[vendor_code] = populate_vendor_data(
                    alma_client, vendor_code
                )
                invoice_data["vendor"] = retrieved_vendors[vendor_code]
            except VendorAddressError:
                invoice_data["vendor_address_error"] = vendor_code
        try:
            invoice_data["funds"], retrieved_funds = populate_fund_data(
                alma_client, invoice_record, retrieved_funds
            )
        except FundError as err:
            invoice_data["fund_errors"] = err.fund_codes
        multibyte_errors = check_for_multibyte(invoice_data)
        if multibyte_errors:
            invoice_data["multibyte_errors"] = multibyte_errors
        if (
            ("vendor_address_error" in invoice_data)
            or ("multibyte_errors" in invoice_data)
            or ("fund_errors" in invoice_data)
        ):
            problem_invoices.append(invoice_data)
        else:
            parsed_invoices.append(invoice_data)
    return problem_invoices, parsed_invoices


def check_for_multibyte(invoice) -> list:
    """checks for the existance of characters which require more than
    one byte to be represented in UTF-8

    WHY?: SAP system does not support multibyte characters
    """
    multibyte_characters = []

    for nested_key, value in flatdict.FlatterDict(invoice).items():
        if isinstance(value, str):
            for char in value:
                if len(char.encode("utf-8")) > 1:
                    multibyte_characters.append(
                        {"field": nested_key, "character": char}
                    )
    return multibyte_characters


def extract_invoice_data(invoice_record: dict) -> dict:
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
    except (IndexError, KeyError):
        raise VendorAddressError


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
    fund_code_errors = []
    for invoice_line in invoice_record["invoice_lines"]["invoice_line"]:
        for fund_distribution in invoice_line["fund_distribution"]:
            fund_code = fund_distribution["fund_code"]["value"]
            amount = fund_distribution["amount"]
            try:
                fund_record = retrieved_funds[fund_code]
            except KeyError:
                logger.debug(f"Retrieving data for fund {fund_code}")
                fund_record = alma_client.get_fund_by_code(fund_code)
                # If alma does not return fund information add the fund code to the
                # list of fund code errors and move on to the next fund code
                if fund_record["total_record_count"] == 0:
                    fund_code_errors.append(fund_code)
                    continue
                retrieved_funds[fund_code] = fund_record
            external_id = fund_record["fund"][0]["external_id"].strip()
            try:
                # Combine amounts for funds that have the same external ID (AKA the
                # same MIT G/L account and cost object)
                fund_data[external_id]["amount"] += amount
            except KeyError:
                fund_data[external_id] = {
                    "amount": amount,
                    "cost object": external_id.split("-")[0],
                    "G/L account": external_id.split("-")[1],
                }
    if fund_code_errors:
        raise FundError(fund_code_errors)
    fund_data = collections.OrderedDict(sorted(fund_data.items()))
    return fund_data, retrieved_funds


def split_invoices_by_field_value(
    invoices: List[dict],
    field: str,
    first_value: str,
    second_value: Optional[str] = None,
) -> List[dict]:
    """Split a list of parsed invoices into two based on an invoice field's value.

    Returns two lists, one of invoice dicts with the first value in the provided
    field, and another of invoice dicts with the second value in the provided field. If
    no second value is provided, the second list returned includes all invoices with
    anything other than the first value in the field.
    """
    invoices_with_first_value = []
    invoices_with_second_value = []
    for invoice in invoices:
        if invoice[field] == first_value:
            invoices_with_first_value.append(invoice)
        elif second_value is not None and invoice[field] == second_value:
            invoices_with_second_value.append(invoice)
        elif second_value is None:
            invoices_with_second_value.append(invoice)
    return invoices_with_first_value, invoices_with_second_value


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
                f"{invoice['funds'][fund]['cost object']} "
                f"{invoice['funds'][fund]['G/L account']}     "
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


def generate_sap_report_email(
    summary: str,
    report: str,
    purchase_type: Literal["mono", "serial"],
    date: datetime,
    final: bool,
):
    report_email = Email()
    if final:
        recipients = CONFIG.SAP_FINAL_RECIPIENT_EMAILS
        subject_string = (
            f"Libraries invoice feed - {purchase_type}s - {date.strftime('%Y%m%d')}"
        )
        attachment_name = (
            f"cover_sheets_{purchase_type}_{date.strftime('%Y%m%d%H%M%S')}.txt"
        )
    else:
        recipients = CONFIG.SAP_REVIEW_RECIPIENT_EMAILS
        subject_string = (
            f"REVIEW libraries invoice feed - {purchase_type}s - "
            f"{date.strftime('%Y%m%d')}"
        )
        attachment_name = (
            f"review_{purchase_type}_report_{date.strftime('%Y%m%d%H%M%S')}.txt"
        )
    report_email.populate(
        from_address=CONFIG.SES_SEND_FROM_EMAIL,
        to_addresses=recipients,
        reply_to=CONFIG.SAP_REPLY_TO_EMAIL,
        subject=subject_string,
        body=summary,
        attachments=[{"content": report, "filename": attachment_name}],
    )
    return report_email


def format_address_for_sap(address_lines: List):
    """Assign payee address information to SAP data file fields"""

    payee_name_line_2 = address_lines[0]

    # if there is a second address line element we
    # assign it to the street_or_po_box_num field
    try:
        street_or_po_box_num = address_lines[1]
    except IndexError:
        street_or_po_box_num = " "

    # if there is a third address lines list element we assign it to payee_name_line_3
    try:
        payee_name_line_3 = address_lines[2]
    except IndexError:
        payee_name_line_3 = " "

    return payee_name_line_2, street_or_po_box_num, payee_name_line_3


def generate_sap_data(today: datetime, invoices: List[dict]) -> str:
    """Given a list of pre-processed invoices and a date, returns a string of invoice
    data formatted according to Accounts Payable's specifications.
    See https://docs.google.com/spreadsheets/d/1PSEYSlPaQ0g2LTEIR6hdyBPzWrZLRK2K/
    edit#gid=1667272331 for specifications for data file"""
    today_string = today.strftime("%Y%m%d")
    sap_data = ""
    for invoice in invoices:
        (
            payee_name_line_2,
            street_or_po_box_num,
            payee_name_line_3,
        ) = format_address_for_sap(invoice["vendor"]["address"]["lines"])
        sap_data += "B"
        # date string is supposed to be listed twice
        sap_data += f"{today_string}"  # Document Date
        sap_data += f"{today_string}"  # Baseline Date
        # we add the invoice date to the invoice number to create a hopefully unique
        # External Reference number
        sap_data += f"{invoice['number'] + invoice['date'].strftime('%y%m%d'): <16.16}"
        sap_data += "X000"
        sap_data += "400000"
        sap_data += f"{invoice['total amount']:16.2f}"
        # sign of total amount. we don't send credits
        # so this will always be blank (positive)
        sap_data += " "
        sap_data += " "  # payment method
        sap_data += "  "  # payment method supplement
        sap_data += "    "  # payment terms
        sap_data += " "  # payment block
        sap_data += "X"  # individual payee in document
        sap_data += f"{invoice['vendor']['name']: <35.35}"
        sap_data += f"{invoice['vendor']['address']['city'] or ' ': <35.35}"
        sap_data += f"{payee_name_line_2: <35.35}"
        # We treat all addresses as street addresses.
        # PO Box indicator should always be blank.
        sap_data += " "  # PO Box indicator
        sap_data += f"{street_or_po_box_num: <35.35}"
        sap_data += f"{invoice['vendor']['address']['postal code'] or ' ': <10.10}"
        sap_data += f"{invoice['vendor']['address']['state or province'] or ' ': <3.3}"
        sap_data += f"{invoice['vendor']['address']['country'] or ' ': <3.3}"
        sap_data += f"{' ': <50.50}"  # Text: 50
        sap_data += f"{payee_name_line_3: <35.35}"
        sap_data += "\n"
        # write a line for each fund distribution in the invoice
        # the final line should begin with a "D"
        # all previous lines should begin with a "C"
        for i, fund in enumerate(invoice["funds"]):
            sap_data += "D" if i == len(invoice["funds"]) - 1 else "C"
            sap_data += (
                f"{invoice['funds'][fund]['G/L account']: <10.10}"
                f"{invoice['funds'][fund]['cost object']: <12.12}"
            )
            sap_data += f"{invoice['funds'][fund]['amount']:16.2f}"
            # sign of fund amount. we don't send credits
            # so this will always be blank (positive)
            sap_data += " "
            sap_data += "\n"
    return sap_data


def generate_summary_warning(problem_invoices: list) -> str:
    """Generates a warning messages about invoice problems that need
    to be resolved before a final-run can take place
    """
    warning = ""
    for invoice in problem_invoices:
        warning += f'Warning! Invoice: {invoice["id"]}\n'
        if "fund_errors" in invoice:
            for fund_code in invoice["fund_errors"]:
                warning += (
                    f"There was a problem retrieving data\n"
                    f"for fund: {fund_code}\n\n"
                )
        if "multibyte_errors" in invoice:
            for multibyte in invoice["multibyte_errors"]:
                warning += (
                    f'Invoice field: {multibyte["field"]}\n'
                    f"Contains multibyte "
                    f'character: {multibyte["character"]}\n\n'
                )
        if "vendor_address_error" in invoice:
            warning += (
                f'No addresses found for vendor: {invoice["vendor_address_error"]}\n\n'
            )
    warning += "Please fix the above before starting a final-run\n\n"
    return warning


def generate_summary(
    problem_invoices: list,
    invoices: List[dict],
    data_file_name: str,
    control_file_name: str,
) -> str:
    excluded_invoices = ""
    invoice_count = 0
    sum_of_invoices = 0
    summary = "--- MIT Libraries--- Alma to SAP Invoice Feed\n\n\n\n"
    summary += f"Data file: {data_file_name}\n\n"
    summary += f"Control file: {control_file_name}\n\n\n\n"
    if problem_invoices:
        summary += generate_summary_warning(problem_invoices)
    for invoice in invoices:
        if invoice["payment method"] == "ACCOUNTINGDEPARTMENT":
            summary += f"{invoice['vendor']['name']: <39.39}"
            summary += (
                f"{invoice['number'] + invoice['date'].strftime('%y%m%d'): <20.20}"
            )
            summary += f"{invoice['total amount']:.2f}\n"
            sum_of_invoices += float(invoice["total amount"])
            invoice_count += 1
        else:
            excluded_invoices += f"{invoice['payment method']}:\t"
            excluded_invoices += f"{invoice['number']}\t"
            excluded_invoices += f"{invoice['vendor']['name']}\t"
            excluded_invoices += f"{invoice['vendor']['code']}\n"
    summary += f"\nTotal payment:       ${sum_of_invoices:,.2f}\n\n"
    summary += f"Invoice count:       {invoice_count}\n\n\n"
    summary += "Authorized signature __________________________________\n\n\n"
    summary += f"{excluded_invoices}"
    return summary


def generate_sap_control(sap_data_file: str, invoice_total: float) -> str:
    """Given a string representing the data file to be sent to SAP and the
    total amount of the invoices in that data file, returns a string
    representing the corresponding control file. see
    https://wikis.mit.edu/confluence/display/SAPdev/MIT+SAP+Dropbox for
    control file format"""

    # 0-16 count bytes
    sap_control_file = f"{len(sap_data_file.encode('utf-8')):016}"

    # 17-32 the spec says "record count", but accounts payable says that
    # this should be a count of the number of lines in the data file.
    sap_control_file += f"{len(sap_data_file.splitlines()):016}"

    # 33-52 credit total
    # we don't send credits to SAP so this will always be 20 0's
    sap_control_file += "0" * 20

    # 53-72 debit total - convert invoice total to string
    # remove decimal to convert dollars to cents
    # and 0-pad to 20 characters
    sap_control_file += f"{'{:.2f}'.format(invoice_total).replace('.', ''):0>20}"

    # 73-92 control 3 summarizing the data file
    # we just repeat the invoice total here
    sap_control_file += f"{'{:.2f}'.format(invoice_total).replace('.', ''):0>20}"

    # 93-112 control 4 summarizing the data file
    # Accounts payable told us to use this string
    sap_control_file += "00100100000000000000"

    # control file ends with a new line
    sap_control_file += "\n"

    return sap_control_file


def generate_next_sap_sequence_number() -> str:
    """Get the current SAP sequence parameter from SSM and return only the sequence
    number incremented by 1."""
    ssm = SSM()
    sap_sequence_parameter = ssm.get_parameter_value(CONFIG.SSM_PATH + "SAP_SEQUENCE")
    split_parameter = sap_sequence_parameter.split(",")
    return str(int(split_parameter[0]) + 1)


def update_sap_sequence(
    sap_sequence_number: str, date: datetime, sequence_type: str
) -> str:
    """Update SAP sequence and post it to SSM Parameter Store."""
    ssm = SSM()
    date_string = date.strftime("%Y%m%d").ljust(14, "0")
    new_sap_sequence = f"{sap_sequence_number},{date_string},{sequence_type}"
    response = ssm.update_parameter_value(
        CONFIG.SSM_PATH + "SAP_SEQUENCE", new_sap_sequence, "StringList"
    )
    return response


def calculate_invoices_total_amount(invoices: List[dict]) -> float:
    total_amount = 0
    total_amount = fsum([invoice["total amount"] for invoice in invoices])
    return total_amount


def generate_sap_file_names(sequence_number: str, date: datetime) -> Tuple[str, str]:
    date_string = date.strftime("%Y%m%d000000")
    data_file_name = f"dlibsapg.{sequence_number}.{date_string}"
    control_file_name = f"clibsapg.{sequence_number}.{date_string}"
    return data_file_name, control_file_name


def mark_invoices_paid(invoices: List[dict], date: datetime):
    paid_invoice_count = 0
    alma_client = Alma_API_Client(
        CONFIG.get_alma_api_key("ALMA_API_ACQ_READ_WRITE_KEY")
    )
    alma_client.set_content_headers("application/json", "application/json")
    for invoice in invoices:
        invoice_id = invoice["id"]
        logger.debug(f"Marking invoice '{invoice_id}' paid")
        response = alma_client.mark_invoice_paid(
            invoice_id, date, invoice["total amount"], invoice["currency"]
        )
        if response["payment"]["payment_status"]["value"] == "PAID":
            logger.debug(f"Invoice '{invoice_id}' marked as paid in Alma")
            paid_invoice_count += 1
        else:
            logger.error(
                f"Something went wrong marking invoice '{invoice_id}' paid in Alma, it "
                "should be investigated manually"
            )
    return paid_invoice_count


def run(
    problem_invoices: dict,
    invoices: List[dict],
    invoices_type: Literal["monograph", "serial"],
    sap_sequence_number: str,  # Just the sequence number, e.g. "0003"
    date: datetime,
    final_run: bool,
    real_run: bool,
):
    logger.info(f"Starting file generation process for {invoices_type} run")
    data_file_name, control_file_name = generate_sap_file_names(
        sap_sequence_number, date
    )
    logger.info(f"Generated next SAP file names: {data_file_name}, {control_file_name}")

    logger.info(f"Generating {invoices_type}s summary")
    summary = generate_summary(
        problem_invoices, invoices, data_file_name, control_file_name
    )

    logger.info(f"Generating {invoices_type}s report")
    report = generate_report(date, invoices)

    sap_invoices, other_payment_invoices = split_invoices_by_field_value(
        invoices, "payment method", "ACCOUNTINGDEPARTMENT"
    )

    if final_run:
        sap_invoices_total_amount = calculate_invoices_total_amount(sap_invoices)

        logger.info("Final run, generating files for SAP")
        data_file_contents = generate_sap_data(date, sap_invoices)
        control_file_contents = generate_sap_control(
            data_file_contents, sap_invoices_total_amount
        )
        logger.info(
            f"{invoices_type.title()}s data file contents:\n{data_file_contents}"
        )
        logger.info(
            f"{invoices_type.title()}s control file contents:\n{control_file_contents}"
        )

        if real_run:
            # Send data and control files to SAP dropbox via SFTP
            logger.info("Real run, sending files to SAP dropbox")
            sftp = SFTP()
            sftp.authenticate(
                CONFIG.SAP_DROPBOX_HOST,
                CONFIG.SAP_DROPBOX_PORT,
                CONFIG.SAP_DROPBOX_USER,
                CONFIG.SAP_DROPBOX_KEY,
            )
            sftp.send_file(data_file_contents, f"dropbox/{data_file_name}")
            logger.info(
                f"Sent data file '{data_file_name}' to SAP dropbox {CONFIG.ENV}"
            )
            sftp.send_file(control_file_contents, f"dropbox/{control_file_name}")
            logger.info(
                f"Sent control file '{control_file_name}' to SAP dropbox {CONFIG.ENV}"
            )
            sftp.client.close()

            # Update sequence numbers in SSM
            logger.info("Real run, updating SAP sequence in Parameter Store")
            update_sap_sequence(
                sap_sequence_number,
                date,
                "mono" if invoices_type == "monograph" else "ser",
            )

            # Update invoice statuses in Alma
            logger.info("Real run, marking invoices PAID in Alma")
            count = mark_invoices_paid(invoices, date)
            logger.info(
                f"{count} {invoices_type} invoices successfully marked as paid in Alma"
            )

    if real_run:
        email = generate_sap_report_email(
            summary,
            report,
            "mono" if invoices_type == "monograph" else invoices_type,
            date,
            final_run,
        )
        response = email.send()
        logger.info(
            f"{invoices_type.title()}s email sent with message ID: "
            f"{response['MessageId']}"
        )
    else:
        logger.info(f"{invoices_type.title()}s summary:\n{summary}\n")
        logger.info(f"{invoices_type.title()}s report:\n{report}\n")

    return {
        "total invoices": len(invoices),
        "sap invoices": len(sap_invoices),
        "other invoices": len(other_payment_invoices),
    }
