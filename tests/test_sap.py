import json
from datetime import datetime

import pytest

from llama import sap


def test_retrieve_sorted_invoices(mocked_alma, mocked_alma_api_client):
    invoices = sap.retrieve_sorted_invoices(mocked_alma_api_client)
    assert invoices[0]["vendor"]["value"] == "AAA"
    assert invoices[1]["vendor"]["value"] == "VEND1"


def test_extract_invoice_data_all_present(mocked_alma, mocked_alma_api_client):
    with open("tests/fixtures/invoice_waiting_to_be_sent.json") as f:
        invoice_record = json.load(f)
    invoice_data = sap.extract_invoice_data(mocked_alma_api_client, invoice_record)
    assert invoice_data == {
        "date": datetime(2021, 9, 27),
        "id": "00000055555000000",
        "type": "monograph",
        "payment method": "ACCOUNTINGDEPARTMENT",
        "total amount": 4056.07,
        "currency": "USD",
        "vendor": {
            "name": "The Bookhouse, Inc.",
            "code": "BKHS",
            "address": {
                "lines": ["string", "string", "string", "string", "string"],
                "city": "string",
                "state or province": None,
                "postal code": "string",
                "country": "VU",
            },
        },
    }


def test_extract_invoice_data_missing_data_raises_error(
    mocked_alma, mocked_alma_api_client
):
    with open("tests/fixtures/invoice_waiting_to_be_sent_incomplete.json") as f:
        invoice_record = json.load(f)
    with pytest.raises(KeyError):
        sap.extract_invoice_data(mocked_alma_api_client, invoice_record)


def test_purchase_type_serial():
    purchase_type = sap.purchase_type("Vendor-S")
    assert purchase_type == "serial"


def test_purchase_type_monograph():
    purchase_type = sap.purchase_type("Vendor")
    assert purchase_type == "monograph"


def test_populate_vendor_data(mocked_alma, mocked_alma_api_client):
    vendor_data = sap.populate_vendor_data(mocked_alma_api_client, "BKHS")
    assert {
        "name": "The Bookhouse, Inc.",
        "code": "BKHS",
        "address": {
            "lines": ["string", "string", "string", "string", "string"],
            "city": "string",
            "state or province": None,
            "postal code": "string",
            "country": "VU",
        },
    } == vendor_data


def test_determine_vendor_payment_address_present():
    vendor_record = {
        "contact_info": {
            "address": [
                {"address_type": [{"value": "order", "desc": "Order"}]},
                {"address_type": [{"value": "payment", "desc": "Payment"}]},
                {"address_type": [{"value": "returns", "desc": "Returns"}]},
            ],
        },
    }
    address = sap.determine_vendor_payment_address(vendor_record)
    assert {"address_type": [{"value": "payment", "desc": "Payment"}]} == address


def test_determine_vendor_payment_address_not_present():
    vendor_record = {
        "contact_info": {
            "address": [
                {"address_type": [{"value": "order", "desc": "Order"}]},
                {"address_type": [{"value": "returns", "desc": "Returns"}]},
            ],
        },
    }
    address = sap.determine_vendor_payment_address(vendor_record)
    assert {"address_type": [{"value": "order", "desc": "Order"}]} == address


def test_determine_vendor_payment_address_no_address_field():
    vendor_record = {"contact_info": {}}
    address = sap.determine_vendor_payment_address(vendor_record)
    assert "No vendor address in record" == address


def test_address_lines_from_address_all_present():
    address = {
        "line1": "Line 1 data",
        "line2": "Line 2 data",
        "line3": "Line 3 data",
        "line4": "Line 4 data",
        "line5": "Line 5 data",
    }
    lines = sap.address_lines_from_address(address)
    assert [
        "Line 1 data",
        "Line 2 data",
        "Line 3 data",
        "Line 4 data",
        "Line 5 data",
    ] == lines


def test_address_lines_from_address_some_present():
    address = {
        "line1": "Line 1 data",
        "line2": "Line 2 data",
        "line3": "Line 3 data",
    }
    lines = sap.address_lines_from_address(address)
    assert ["Line 1 data", "Line 2 data", "Line 3 data"] == lines


def test_address_lines_from_address_some_null():
    address = {
        "line1": "Line 1 data",
        "line2": "Line 2 data",
        "line3": "Line 3 data",
        "line4": None,
        "line5": None,
    }
    lines = sap.address_lines_from_address(address)
    assert ["Line 1 data", "Line 2 data", "Line 3 data"] == lines


def test_address_lines_from_address_none_present():
    address = {}
    lines = sap.address_lines_from_address(address)
    assert [] == lines


def test_country_code_from_address_code_present():
    address = {"country": {"value": "USA"}}
    code = sap.country_code_from_address(address)
    assert "US" == code


def test_country_code_from_address_code_not_present():
    address = {"country": {"value": "Not a Country"}}
    code = sap.country_code_from_address(address)
    assert "US" == code


def test_country_code_from_address_country_not_present():
    address = {}
    code = sap.country_code_from_address(address)
    assert "US" == code
