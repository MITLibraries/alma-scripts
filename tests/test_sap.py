import collections
import json
from datetime import datetime

import pytest

from llama import CONFIG, sap
from llama.ssm import SSM


def test_retrieve_sorted_invoices(mocked_alma, mocked_alma_api_client):
    invoices = sap.retrieve_sorted_invoices(mocked_alma_api_client)
    assert invoices[0]["vendor"]["value"] == "AAA"
    assert invoices[0]["number"] == "0501130656"
    assert invoices[1]["vendor"]["value"] == "AAA"
    assert invoices[1]["number"] == "0501130658"
    assert invoices[2]["vendor"]["value"] == "VEND-S"
    assert invoices[2]["number"] == "0501130657"


def test_parse_invoice_records(mocked_alma, mocked_alma_api_client):
    invoices = sap.retrieve_sorted_invoices(mocked_alma_api_client)
    problem_invoices, parsed_invoices = sap.parse_invoice_records(
        mocked_alma_api_client, invoices
    )
    assert len(parsed_invoices) == 3
    assert len(problem_invoices) == 2
    assert problem_invoices[0]["fund_errors"][0] == "over-encumbered"
    assert problem_invoices[1]["fund_errors"][0] == "over-encumbered"
    assert problem_invoices[1]["multibyte_errors"][0] == {
        "character": "‑",
        "field": "vendor:address:lines:0",
    }


def test_parse_invoice_with_no_address_vendor(mocked_alma, mocked_alma_api_client):
    invoices_with_no_vendor_address = []
    with open("tests/fixtures/invoice_with_no_vendor_address.json") as f:
        invoice_record = json.load(f)
    invoices_with_no_vendor_address.append(invoice_record)
    problem_invoices, parsed_invoices = sap.parse_invoice_records(
        mocked_alma_api_client, invoices_with_no_vendor_address
    )
    assert len(parsed_invoices) == 0
    assert len(problem_invoices) == 1
    assert problem_invoices[0]["vendor_address_error"] == "YBP-no-address"


def test_contains_multibyte():
    invoice_with_multibyte = {
        "id": {
            "level 2": [
                "this is a multibyte character ‑",
                "this is also ‑ a multibyte character",
                "this is not a multibyte character -",
            ]
        }
    }
    has_multibyte = sap.check_for_multibyte(invoice_with_multibyte)
    assert has_multibyte[0]["field"] == "id:level 2:0"
    assert has_multibyte[0]["character"] == "‑"
    assert has_multibyte[1]["field"] == "id:level 2:1"


def test_does_not_contain_multibyte():
    invoice_without_multibyte = {
        "id": {"level 2": ["this is not a multibyte character -"]}
    }
    no_multibyte = sap.check_for_multibyte(invoice_without_multibyte)
    assert len(no_multibyte) == 0


def test_extract_invoice_data_all_present():
    with open("tests/fixtures/invoice_waiting_to_be_sent.json") as f:
        invoice_record = json.load(f)
    invoice_data = sap.extract_invoice_data(invoice_record)
    assert invoice_data == {
        "date": datetime(2021, 9, 27),
        "id": "00000055555000000",
        "number": "123456",
        "type": "monograph",
        "payment method": "ACCOUNTINGDEPARTMENT",
        "total amount": 4056.07,
        "currency": "USD",
    }


def test_extract_invoice_data_missing_data_raises_error():
    with open("tests/fixtures/invoice_waiting_to_be_sent_incomplete.json") as f:
        invoice_record = json.load(f)
    with pytest.raises(KeyError):
        sap.extract_invoice_data(invoice_record)


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


def test_populate_vendor_data_empty_address_list(mocked_alma, mocked_alma_api_client):
    with pytest.raises(sap.VendorAddressError):
        sap.populate_vendor_data(mocked_alma_api_client, "YBP-no-address")


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


def test_no_address_field_in_vendor_data_raises_error():
    vendor_record = {"contact_info": {}}
    with pytest.raises(sap.VendorAddressError):
        sap.determine_vendor_payment_address(vendor_record)


def test_empty_vendor_address_list_raises_error():
    vendor_record = {"contact_info": {"address": []}}
    with pytest.raises(sap.VendorAddressError):
        sap.determine_vendor_payment_address(vendor_record)


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
        "cost object": "1234567",
        "G/L account": "000001",
    }
    fund_data_ordereddict["1234567-000002"] = {
        "amount": 299,
        "cost object": "1234567",
        "G/L account": "000002",
    }
    fund_data_ordereddict["1234567-000003"] = {
        "amount": 69.75,
        "cost object": "1234567",
        "G/L account": "000003",
    }

    assert fund_data == fund_data_ordereddict
    assert list(retrieved_funds) == ["JKL", "ABC", "DEF", "GHI"]


def test_populate_fund_data_fund_error(mocked_alma, mocked_alma_api_client):
    with open("tests/fixtures/invoice_with_over_encumbrance.json") as f:
        invoice_record = json.load(f)
        retrieved_funds = {}
    with pytest.raises(sap.FundError) as err:
        sap.populate_fund_data(mocked_alma_api_client, invoice_record, retrieved_funds)
    assert err.value.fund_codes == ["also-over-encumbered", "over-encumbered"]


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
                    "cost object": "1234567",
                    "G/L account": "000001",
                },
                "1234567-000002": {
                    "amount": 299,
                    "cost object": "1234567",
                    "G/L account": "000002",
                },
                "1234567-000003": {
                    "amount": 69.75,
                    "cost object": "1234567",
                    "G/L account": "000003",
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


def test_generate_sap_report_email_final_run():
    email = sap.generate_sap_report_email(
        "Summary contents", "Report contents", "mono", datetime(2021, 10, 1), True
    )
    assert email["From"] == "from@example.com"
    assert email["To"] == "final_1@example.com, final_2@example.com"
    assert email["Subject"] == "Libraries invoice feed - monos - 20211001"
    assert email["Reply-To"] == "replyto@example.com"
    assert email.get_content_type() == "multipart/mixed"
    assert email.get_body().get_content() == "Summary contents\n"
    attachment = next(email.iter_attachments())
    assert attachment.get_filename() == "cover_sheets_mono_20211001000000.txt"
    assert attachment.get_content() == "Report contents\n"


def test_generate_sap_report_email_review_run():
    email = sap.generate_sap_report_email(
        "Summary contents", "Report contents", "serial", datetime(2021, 10, 1), False
    )
    assert email["From"] == "from@example.com"
    assert email["To"] == "review@example.com"
    assert email["Subject"] == "REVIEW libraries invoice feed - serials - 20211001"
    assert email["Reply-To"] == "replyto@example.com"
    assert email.get_content_type() == "multipart/mixed"
    assert email.get_body().get_content() == "Summary contents\n"
    attachment = next(email.iter_attachments())
    assert attachment.get_filename() == "review_serial_report_20211001000000.txt"
    assert attachment.get_content() == "Report contents\n"


def test_format_address_street_1_line():
    address_lines = ["123 salad Street"]
    (
        payee_name_line_2,
        street_or_po_box_num,
        payee_name_line_3,
    ) = sap.format_address_for_sap(address_lines)
    assert payee_name_line_2 == address_lines[0]
    assert street_or_po_box_num == " "
    assert payee_name_line_3 == " "


def test_format_address_street_2_lines():
    address_lines = ["123 salad Street", "Second Floor"]
    (
        payee_name_line_2,
        street_or_po_box_num,
        payee_name_line_3,
    ) = sap.format_address_for_sap(address_lines)
    assert payee_name_line_2 == address_lines[0]
    assert street_or_po_box_num == address_lines[1]
    assert payee_name_line_3 == " "


def test_format_address_street_3_lines():
    address_lines = ["123 salad Street", "Second Floor", "c/o salad guy"]
    (
        payee_name_line_2,
        street_or_po_box_num,
        payee_name_line_3,
    ) = sap.format_address_for_sap(address_lines)
    assert payee_name_line_2 == address_lines[0]
    assert street_or_po_box_num == address_lines[1]
    assert payee_name_line_3 == address_lines[2]


def test_format_address_po_box_1_line():
    address_lines = ["P.O. Box 123456"]
    (
        payee_name_line_2,
        street_or_po_box_num,
        payee_name_line_3,
    ) = sap.format_address_for_sap(address_lines)
    assert payee_name_line_2 == address_lines[0]
    assert street_or_po_box_num == " "
    assert payee_name_line_3 == " "


def test_format_address_po_box_2_lines():
    address_lines = ["c/o salad guy", "P.O. Box 123456"]
    (
        payee_name_line_2,
        street_or_po_box_num,
        payee_name_line_3,
    ) = sap.format_address_for_sap(address_lines)
    assert payee_name_line_2 == address_lines[0]
    assert street_or_po_box_num == address_lines[1]
    assert payee_name_line_3 == " "


def test_generate_sap_data_success(invoices_for_sap, sap_data_file):
    today = datetime(2021, 5, 18)
    report = sap.generate_sap_data(today, invoices_for_sap)
    assert report == sap_data_file


def test_calculate_invoices_total_amount():
    invoices = [dict(zip(["total amount"], [0.1])) for x in range(100)]
    total_amount = sap.calculate_invoices_total_amount(invoices)
    assert total_amount == 10


def test_generate_summary_warning(problem_invoices):
    warning_message = sap.generate_summary_warning(problem_invoices)
    assert (
        warning_message
        == """Warning! Invoice: 9991
There was a problem retrieving data
for fund: over-encumbered

There was a problem retrieving data
for fund: also-over-encumbered

Invoice field: vendor:address:lines:0
Contains multibyte character: ‑

Invoice field: vendor:city
Contains multibyte character: ƒ

Warning! Invoice: 9992
There was a problem retrieving data
for fund: also-over-encumbered

Invoice field: vendor:address:lines:0
Contains multibyte character: ‑

Warning! Invoice: 9993
No addresses found for vendor: YBP-no-address

Please fix the above before starting a final-run

"""
    )


def test_generate_summary(invoices_for_sap_with_different_payment_method):
    dfile = "dlibsapg.1001.202110518000000"
    cfile = "clibsapg.1001.202110518000000"
    problem_invoices = []
    summary = sap.generate_summary(
        problem_invoices, invoices_for_sap_with_different_payment_method, dfile, cfile
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


def test_generate_sap_control(sap_data_file):
    invoice_total = 1367.40
    sap_control = sap.generate_sap_control(sap_data_file, invoice_total)
    assert sap_control[0:16] == "0000000000001182"
    assert sap_control[16:32] == "0000000000000009"
    assert sap_control[32:52] == "00000000000000000000"
    assert sap_control[52:72] == "00000000000000136740"
    assert sap_control[72:92] == "00000000000000136740"
    assert sap_control[92:112] == "00100100000000000000"
    assert len(sap_control.encode("utf-8")) == 113


def test_generate_next_sap_sequence_number(mocked_ssm):
    ssm = SSM()
    assert (
        ssm.get_parameter_value("/test/example/SAP_SEQUENCE")
        == "1001,20210722000000,ser"
    )
    new_sap_sequence = sap.generate_next_sap_sequence_number()
    assert new_sap_sequence == "1002"


def test_update_sap_sequence(mocked_ssm):
    ssm = SSM()
    assert (
        ssm.get_parameter_value("/test/example/SAP_SEQUENCE")
        == "1001,20210722000000,ser"
    )
    response = sap.update_sap_sequence("1002", datetime(2021, 7, 23), "mono")
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
    assert (
        ssm.get_parameter_value("/test/example/SAP_SEQUENCE")
        == "1002,20210723000000,mono"
    )


def test_generate_sap_file_names(mocked_ssm):
    data_file_name, control_file_name = sap.generate_sap_file_names(
        "1002", datetime(2021, 12, 17)
    )
    assert data_file_name == "dlibsapg.1002.20211217000000"
    assert control_file_name == "clibsapg.1002.20211217000000"


def test_mark_invoices_paid_all_successful(invoices_for_sap, mocked_alma):
    result = sap.mark_invoices_paid(invoices_for_sap, datetime(2022, 1, 7))
    assert result == 3


def test_mark_invoices_paid_error(
    caplog, invoices_for_sap_with_different_payment_method, mocked_alma
):
    result = sap.mark_invoices_paid(
        invoices_for_sap_with_different_payment_method, datetime(2022, 1, 7)
    )
    assert result == 2
    assert (
        "Something went wrong marking invoice '0000055555000001' paid in Alma, it "
        "should be investigated manually" in caplog.text
    )


def test_run_not_final_not_real(
    caplog,
    invoices_for_sap_with_different_payment_method,
    mocked_alma,
    problem_invoices,
):
    result = sap.run(
        problem_invoices,
        invoices_for_sap_with_different_payment_method,
        "monograph",
        "0003",
        datetime(2022, 1, 11),
        final_run=False,
        real_run=False,
    )
    assert result == {
        "total invoices": 3,
        "sap invoices": 2,
        "other invoices": 1,
    }
    assert "Monographs report:" in caplog.text


def test_run_not_final_real(
    caplog, invoices_for_sap, mocked_alma, mocked_ses, problem_invoices
):
    result = sap.run(
        problem_invoices,
        invoices_for_sap,
        "monograph",
        "0003",
        datetime(2022, 1, 11),
        final_run=False,
        real_run=True,
    )
    assert result == {
        "total invoices": 3,
        "sap invoices": 3,
        "other invoices": 0,
    }
    assert "Monographs email sent with message ID:" in caplog.text


def test_run_final_not_real(caplog, invoices_for_sap, mocked_alma, problem_invoices):
    sap.run(
        problem_invoices,
        invoices_for_sap,
        "monograph",
        "0003",
        datetime(2022, 1, 11),
        final_run=True,
        real_run=False,
    )
    assert "Monographs control file contents:" in caplog.text


def test_run_final_real(
    caplog,
    invoices_for_sap,
    mocked_alma,
    mocked_ses,
    mocked_sftp_server,
    mocked_ssm,
    test_sftp_private_key,
    problem_invoices,
):
    CONFIG.SAP_DROPBOX_HOST = mocked_sftp_server.host
    CONFIG.SAP_DROPBOX_PORT = mocked_sftp_server.port
    CONFIG.SAP_DROPBOX_KEY = test_sftp_private_key
    sap.run(
        problem_invoices,
        invoices_for_sap,
        "monograph",
        "0003",
        datetime(2022, 1, 11),
        final_run=True,
        real_run=True,
    )
    assert (
        "Sent control file 'clibsapg.0003.20220111000000' to SAP dropbox test"
        in caplog.text
    )
    assert (
        "SSM parameter '/test/example/SAP_SEQUENCE' was updated to "
        "'0003,20220111000000,mono' with type=StringList" in caplog.text
    )
    assert "3 monograph invoices successfully marked as paid in Alma" in caplog.text
