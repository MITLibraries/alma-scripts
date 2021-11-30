import collections
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
        "number": "123456",
        "type": "monograph",
        "payment method": "ACCOUNTINGDEPARTMENT",
        "total amount": 4056.07,
        "currency": "USD",
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


def test_populate_fund_data_success(mocked_alma, mocked_alma_api_client):
    with open("tests/fixtures/invoice_waiting_to_be_sent.json") as f:
        invoice_record = json.load(f)
    retrieved_funds = {}
    fund_data, retrieved_funds = sap.populate_fund_data(
        mocked_alma_api_client, invoice_record, retrieved_funds
    )
    fund_data_ordereddict = collections.OrderedDict()
    fund_data_ordereddict["1234567-000001"] = {
        "amount": 3687.32,
        "G/L account": "1234567",
        "cost object": "000001",
    }
    fund_data_ordereddict["1234567-000002"] = {
        "amount": 299,
        "G/L account": "1234567",
        "cost object": "000002",
    }
    fund_data_ordereddict["1234567-000003"] = {
        "amount": 69.75,
        "G/L account": "1234567",
        "cost object": "000003",
    }

    assert fund_data == fund_data_ordereddict
    assert list(retrieved_funds) == ["JKL", "ABC", "DEF", "GHI"]


def test_generate_report_success():
    invoices = [
        {
            "date": datetime(2021, 9, 27),
            "id": "00000055555000000",
            "number": "123456",
            "type": "monograph",
            "payment method": "ACCOUNTINGDEPARTMENT",
            "total amount": 4056.07,
            "currency": "USD",
            "vendor": {
                "name": "The Bookhouse, Inc.",
                "code": "BKHS",
                "address": {
                    "lines": [
                        "123 Main Street",
                        "Building 4",
                        "Suite 5",
                        "C/O Mickey Mouse",
                    ],
                    "city": "Anytown",
                    "state or province": None,
                    "postal code": "12345",
                    "country": "VU",
                },
            },
            "funds": {
                "1234567-000001": {
                    "amount": 3687.32,
                    "G/L account": "1234567",
                    "cost object": "000001",
                },
                "1234567-000002": {
                    "amount": 299,
                    "G/L account": "1234567",
                    "cost object": "000002",
                },
                "1234567-000003": {
                    "amount": 69.75,
                    "G/L account": "1234567",
                    "cost object": "000003",
                },
            },
        }
    ]
    today = datetime(2021, 10, 1)
    report = sap.generate_report(today, invoices)
    assert (
        report
        == """

                                 MIT LIBRARIES


Date: 10/01/2021                          Vendor code   : BKHS
                                          Accounting ID :

Vendor:  The Bookhouse, Inc.
         123 Main Street
         Building 4
         Suite 5
         C/O Mickey Mouse
         Anytown, 12345
         VU

Invoice no.            Fiscal Account     Amount            Inv. Date
------------------     -----------------  -------------     ----------
123456210927           1234567 000001     3,687.32          09/27/2021
123456210927           1234567 000002     299.00            09/27/2021
123456210927           1234567 000003     69.75             09/27/2021


Total/Currency:             4,056.07      USD

Payment Method:  ACCOUNTINGDEPARTMENT


                       Departmental Approval __________________________________

                       Financial Services Approval ____________________________


\f"""
    )


def test_format_address_street_1_line():
    address_lines = ["123 salad Street"]
    (
        po_box_indicator,
        payee_name_line_2,
        street_or_po_box_num,
        payee_name_line_3,
    ) = sap.format_address_for_sap(address_lines)
    assert po_box_indicator == " "
    assert payee_name_line_2 == address_lines[0]
    assert street_or_po_box_num == " "
    assert payee_name_line_3 == " "


def test_format_address_street_2_lines():
    address_lines = ["123 salad Street", "Second Floor"]
    (
        po_box_indicator,
        payee_name_line_2,
        street_or_po_box_num,
        payee_name_line_3,
    ) = sap.format_address_for_sap(address_lines)
    assert po_box_indicator == " "
    assert payee_name_line_2 == address_lines[0]
    assert street_or_po_box_num == address_lines[1]
    assert payee_name_line_3 == " "


def test_format_address_street_3_lines():
    address_lines = ["123 salad Street", "Second Floor", "c/o salad guy"]
    (
        po_box_indicator,
        payee_name_line_2,
        street_or_po_box_num,
        payee_name_line_3,
    ) = sap.format_address_for_sap(address_lines)
    assert po_box_indicator == " "
    assert payee_name_line_2 == address_lines[0]
    assert street_or_po_box_num == address_lines[1]
    assert payee_name_line_3 == address_lines[2]


def test_format_address_po_box_1_line():
    address_lines = ["P.O. Box 123456"]
    (
        po_box_indicator,
        payee_name_line_2,
        street_or_po_box_num,
        payee_name_line_3,
    ) = sap.format_address_for_sap(address_lines)
    assert po_box_indicator == "X"
    assert payee_name_line_2 == " "
    assert street_or_po_box_num == "123456"
    assert payee_name_line_3 == " "


def test_format_address_po_box_2_lines():
    address_lines = ["c/o salad guy", "P.O. Box 123456"]
    (
        po_box_indicator,
        payee_name_line_2,
        street_or_po_box_num,
        payee_name_line_3,
    ) = sap.format_address_for_sap(address_lines)
    assert po_box_indicator == "X"
    assert payee_name_line_2 == address_lines[0]
    assert street_or_po_box_num == "123456"
    assert payee_name_line_3 == " "


def test_generate_sap_data_success():
    today = datetime(2021, 5, 18)
    invoices = [
        {
            "date": datetime(2021, 5, 12),
            "id": "0000055555000000",
            "number": "456789",
            "type": "monograph",
            "payment method": "ACCOUNTINGDEPARTMENT",
            "total amount": 150,
            "currency": "USD",
            "vendor": {
                "name": "Danger Inc.",
                "code": "FOOBAR-M",
                "address": {
                    "lines": [
                        "123 salad Street",
                        "Second Floor",
                    ],
                    "city": "San Francisco",
                    "state or province": "CA",
                    "postal code": "94109",
                    "country": "US",
                },
            },
            "funds": {
                "123456-0000001": {
                    "amount": 150,
                    "G/L account": "123456",
                    "cost object": "0000001",
                },
            },
        },
        {
            "date": datetime(2021, 5, 11),
            "id": "0000055555000000",
            "number": "444555",
            "type": "monograph",
            "payment method": "ACCOUNTINGDEPARTMENT",
            "total amount": 1067.04,
            "currency": "USD",
            "vendor": {
                "name": "some library solutions from salad",
                "code": "YBPE-M",
                "address": {
                    "lines": [
                        "P.O. Box 123456",
                    ],
                    "city": "Atlanta",
                    "state or province": "GA",
                    "postal code": "30384-7991",
                    "country": "US",
                },
            },
            "funds": {
                "123456-0000001": {
                    "amount": 608,
                    "G/L account": "123456",
                    "cost object": "0000001",
                },
                "123456-0000002": {
                    "amount": 148.50,
                    "G/L account": "123456",
                    "cost object": "0000002",
                },
                "1123456-0000003": {
                    "amount": 235.54,
                    "G/L account": "123456",
                    "cost object": "0000003",
                },
                "123456-0000004": {
                    "amount": 75,
                    "G/L account": "123456",
                    "cost object": "0000004",
                },
            },
        },
        {
            "date": datetime(2021, 5, 12),
            "id": "0000055555000000",
            "number": "456789",
            "type": "monograph",
            "payment method": "ACCOUNTINGDEPARTMENT",
            "total amount": 150,
            "currency": "USD",
            "vendor": {
                "name": "one address line",
                "code": "FOOBAR-M",
                "address": {
                    "lines": [
                        "123 some street",
                    ],
                    "city": "San Francisco",
                    "state or province": "CA",
                    "postal code": "94109",
                    "country": "US",
                },
            },
            "funds": {
                "123456-0000001": {
                    "amount": 150,
                    "G/L account": "123456",
                    "cost object": "0000001",
                },
            },
        },
    ]
    report = sap.generate_sap_data(today, invoices)
    # test data is formatted to make it more readable
    # each line corresponds to a field in the SAP data file spec
    # See https://docs.google.com/spreadsheets/d/1PSEYSlPaQ0g2LTEIR6hdyBPzWrZLRK2K/
    # edit#gid=1667272331
    assert report == (
        "B\
20210518\
20210518\
456789210512    \
X000\
400000\
          150.00\
 \
 \
  \
    \
 \
X\
Danger Inc.                        \
San Francisco                      \
123 salad Street                   \
 \
Second Floor                       \
94109     \
CA \
US \
                                                  \
                                   \
\n\
D\
123456    \
0000001     \
          150.00\
 \
\n\
B\
20210518\
20210518\
444555210511    \
X000\
400000\
         1067.04\
 \
 \
  \
    \
 \
X\
some library solutions from salad  \
Atlanta                            \
                                   \
X\
123456                             \
30384-7991\
GA \
US \
                                                  \
                                   \
\n\
C\
123456    \
0000001     \
          608.00\
 \
\n\
C\
123456    \
0000002     \
          148.50\
 \
\n\
C\
123456    \
0000003     \
          235.54\
 \
\n\
D\
123456    \
0000004     \
           75.00\
 \
\n\
B\
20210518\
20210518\
456789210512    \
X000\
400000\
          150.00\
 \
 \
  \
    \
 \
X\
one address line                   \
San Francisco                      \
123 some street                    \
 \
                                   \
94109     \
CA \
US \
                                                  \
                                   \
\n\
D\
123456    \
0000001     \
          150.00\
 \
\n"
    )


def test_generate_summary(mono_invoices_with_different_payment_method):
    dfile = "dlibsapg.1001.202110518000000"
    cfile = "clibsapg.1001.202110518000000"
    summary = sap.generate_summary(
        mono_invoices_with_different_payment_method, dfile, cfile
    )
    assert (
        summary
        == """--- MIT Libraries--- Alma to SAP Invoice Feed



Data file: dlibsapg.1001.202110518000000

Control file: clibsapg.1001.202110518000000



Danger Inc.                            456789210512        150.00
some library solutions from salad      444555210511        1067.04

Total payment:       $1,217.04

Invoice count:       2


Authorized signature __________________________________


BAZ:\t12345\tFoo Bar Books\tFOOBAR
"""
    )
