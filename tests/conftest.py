import json
import os
from datetime import datetime

import boto3
import mockssh
import pytest
import requests_mock
from click.testing import CliRunner
from moto import mock_s3, mock_ses, mock_ssm
from requests import HTTPError, Response

from llama.alma import Alma_API_Client
from llama.s3 import S3


@pytest.fixture(scope="function")
def aws_credentials():
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"


@pytest.fixture(scope="function")
def bucket_env():
    os.environ["ALMA_BUCKET"] = "ils-sftp"
    os.environ["DIP_ALEPH_BUCKET"] = "dip-ils-bucket"


@pytest.fixture()
def mocked_alma(po_line_record_all_fields):
    with requests_mock.Mocker() as m:
        # Fund endpoints
        with open("tests/fixtures/funds.json") as f:
            funds = json.load(f)
            m.get(
                "http://example.com/acq/funds?q=fund_code~ABC",
                json={"fund": [funds["fund"][0]], "total_record_count": 1},
            )
            m.get(
                "http://example.com/acq/funds?q=fund_code~DEF",
                json={"fund": [funds["fund"][1]], "total_record_count": 1},
            )
            m.get(
                "http://example.com/acq/funds?q=fund_code~GHI",
                json={"fund": [funds["fund"][2]], "total_record_count": 1},
            )
            m.get(
                "http://example.com/acq/funds?q=fund_code~JKL",
                json={"fund": [funds["fund"][3]], "total_record_count": 1},
            )
            m.get(
                "http://example.com/acq/funds?q=fund_code~over-encumbered",
                json={"total_record_count": 0},
            )
            m.get(
                "http://example.com/acq/funds?q=fund_code~also-over-encumbered",
                json={"total_record_count": 0},
            )

        # Invoice endpoints
        with open("tests/fixtures/invoices.json") as f:
            invoices_json = json.load(f)
        m.get("http://example.com/acq/invoices", json=invoices_json)
        m.get(
            "http://example.com/acq/invoices/558809630001021",
            json=invoices_json["invoice"][0],
        )
        m.post("http://example.com/acq/invoices", json=invoices_json["invoice"][0])
        with open("tests/fixtures/invoice_paid.json") as f:
            data = json.load(f)
            m.post(
                "http://example.com/acq/invoices/0000055555000000?op=paid",
                complete_qs=True,
                json=data,
            )
            m.post("http://example.com/acq/invoices/558809630001021", json=data)
            m.post("http://example.com/acq/invoices/01", json=data)
            m.post("http://example.com/acq/invoices/02", json=data)
        with open("tests/fixtures/invoice_waiting_to_be_sent.json") as f:
            m.post(
                "http://example.com/acq/invoices/00000055555000000", json=json.load(f)
            )
        with open("tests/fixtures/invoice_line.json") as f:
            m.post("http://example.com/acq/invoices/123456789/lines", json=json.load(f))
        m.post(
            "http://example.com/acq/invoices/03",
            json={"payment": {"payment_status": {"desc": "string", "value": "WRONG"}}},
        )
        m.post(
            "http://example.com/acq/invoices/0000055555000001",
            json={"payment": {"payment_status": {"desc": "string", "value": "WRONG"}}},
        )

        # PO Line endpoints
        m.get(
            "http://example.com/acq/po-lines?status=ACTIVE",
            json={
                "total_record_count": 2,
                "po_line": [
                    {"number": "POL-123", "created_date": "2021-05-13Z"},
                    {"number": "POL-456", "created_date": "2021-05-02Z"},
                ],
            },
        )
        m.get(
            (
                "http://example.com/acq/po-lines?status=ACTIVE&"
                "acquisition_method=PURCHASE_NOLETTER"
            ),
            json={
                "total_record_count": 2,
                "po_line": [
                    {"number": "POL-789", "created_date": "2021-05-15Z"},
                ],
            },
        )
        m.get("http://example.com/acq/po-lines/POL-123", json=po_line_record_all_fields)
        m.get("http://example.com/acq/po-lines/POL-456", json=po_line_record_wrong_date)

        # Vendor endpoints
        with open("tests/fixtures/vendor.json") as f:
            vendor_data = json.load(f)
        m.post("http://example.com/acq/vendors", json=vendor_data)
        with open("tests/fixtures/vendor_aaa.json") as f:
            m.get("http://example.com/acq/vendors/AAA", json=json.load(f))
        m.get("http://example.com/acq/vendors/BKHS", json=vendor_data)
        m.get("http://example.com/acq/vendors/BKHS/invoices", json=invoices_json)
        with open("tests/fixtures/vendor_vend-s.json") as f:
            m.get("http://example.com/acq/vendors/VEND-S", json=json.load(f))
        with open("tests/fixtures/vendor_multibyte-address.json") as f:
            m.get("http://example.com/acq/vendors/multibyte-address", json=json.load(f))
        with open("tests/fixtures/vendor_no-address.json") as f:
            m.get("http://example.com/acq/vendors/YBP-no-address", json=json.load(f))

        # General endpoints
        m.get(
            "http://example.com/paged?limit=10&offset=0",
            complete_qs=True,
            json={
                "total_record_count": 15,
                "fake_records": [{"record_number": i} for i in range(10)],
            },
        )
        m.get(
            "http://example.com/paged?limit=10&offset=10",
            complete_qs=True,
            json={
                "total_record_count": 15,
                "fake_records": [{"record_number": i} for i in range(10, 15)],
            },
        )

        yield m


@pytest.fixture()
def mocked_alma_sample_data():
    with requests_mock.Mocker() as m:
        # Get vendor
        response1 = Response()
        response1._content = b'{"errorList": {"error": [{"errorCode":"402880"}]}}'
        m.get(
            "http://example.com/acq/vendors/TestSAPVendor1",
            exc=HTTPError(response=response1),
        )
        m.get(
            "http://example.com/acq/vendors/TestSAPVendor2-S",
            json={"code": "TestSAPVendor2-S"},
        )
        response2 = Response()
        response2._content = (
            b'{"errorList": {"error": [{"errorCode":"a-different-error"}]}}'
        )
        m.get(
            "http://example.com/acq/vendors/not-a-vendor",
            exc=HTTPError(response=response2),
        )

        # Get vendor invoices
        m.get(
            "http://example.com/acq/vendors/TestSAPVendor1/invoices",
            json={
                "total_record_count": 2,
                "invoice": [
                    {"id": "alma_id_0001", "number": "TestSAPInvoiceV1-1"},
                    {"id": "alma_id_0002", "number": "TestSAPInvoiceV1-2"},
                ],
            },
        )
        m.get(
            "http://example.com/acq/vendors/TestSAPVendor2-S/invoices",
            json={"total_record_count": 0, "invoice": []},
        )
        m.get(
            "http://example.com/acq/vendors/TestSAPVendor3/invoices",
            json={
                "total_record_count": 1,
                "invoice": [{"id": "alma_id_0003", "number": "HasNoDash"}],
            },
        )

        # Create vendor
        m.post("http://example.com/acq/vendors", json={"code": "TestSAPVendor1"})

        # Create invoice
        m.post(
            "http://example.com/acq/invoices",
            [{"json": {"id": "alma_id_0001"}}, {"json": {"id": "alma_id_0002"}}],
        )

        # Create invoice lines
        m.post(
            "http://example.com/acq/invoices/alma_id_0001/lines",
            json={"id": "alma_id_0001"},
        )
        m.post(
            "http://example.com/acq/invoices/alma_id_0002/lines",
            json={"id": "alma_id_0002"},
        )
        response3 = Response()
        response3._content = b"Error message"
        m.post(
            "http://example.com/acq/invoices/error_id/lines",
            exc=HTTPError(response=response3),
        )

        # Process invoices
        m.post(
            "http://example.com/acq/invoices/alma_id_0001?op=process_invoice",
            json={"id": "alma_id_0001"},
        )
        m.post(
            "http://example.com/acq/invoices/alma_id_0002?op=process_invoice",
            json={"id": "alma_id_0002"},
        )
        m.post(
            "http://example.com/acq/invoices/alma_id_0003?op=process_invoice",
            json={"id": "alma_id_0003"},
        )
        m.post(
            "http://example.com/acq/invoices/alma_id_0004?op=process_invoice",
            json={"id": "alma_id_0004"},
        )
        response4 = Response()
        response4._content = b"Error message"
        m.post(
            "http://example.com/acq/invoices/error_id?op=process_invoice",
            exc=HTTPError(response=response4),
        )
        yield m


@pytest.fixture()
def mocked_alma_no_invoices():
    with requests_mock.Mocker() as m:
        m.get("http://example.com/acq/invoices", json={"total_record_count": 0})
        yield m


@pytest.fixture()
def mocked_alma_with_errors():
    with requests_mock.Mocker() as m:
        response = Response()
        response._content = b"Error message"
        m.post("http://example.com/acq/invoices", exc=HTTPError(response=response))
        yield m


@pytest.fixture()
def mocked_alma_api_client():
    alma_api_client = Alma_API_Client("abc123", base_api_url="http://example.com/")
    alma_api_client.set_content_headers("application/json", "application/json")
    return alma_api_client


@pytest.fixture(scope="function")
def mocked_s3(aws_credentials):
    with mock_s3():
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="ils-sftp")
        s3.put_object(
            Bucket="ils-sftp",
            Key="exlibris/Timdex/UPDATE/ALMA_UPDATE_EXPORT__20210101_marc1.mrc",
            Body="MARC 001",
        )
        s3.put_object(
            Bucket="ils-sftp",
            Key="exlibris/Timdex/UPDATE/ALMA_UPDATE_EXPORT__20210101_marc2.mrc",
            Body="MARC 002",
        )
        s3.put_object(
            Bucket="ils-sftp",
            Key="exlibris/Timdex/UPDATE/ALMA_UPDATE_EXPORT__20201012_marc1.mrc",
            Body="MARC 003",
        )
        s3.put_object(
            Bucket="ils-sftp",
            Key="exlibris/Timdex/UPDATE/ALMA_UPDATE_EXPORT__20201012_marc2.mrc",
            Body="MARC 004",
        )
        s3.create_bucket(Bucket="dip-ils-bucket")
        yield s3


@pytest.fixture()
def mocked_ses(aws_credentials):
    with mock_ses():
        ses = boto3.client("ses", region_name="us-east-1")
        ses.verify_email_identity(EmailAddress="from@example.com")
        yield ses


@pytest.fixture
def mocked_sftp_server():
    users = {
        "test-dropbox-user": "tests/fixtures/sample-ssh-key",
    }
    with mockssh.Server(users) as s:
        client = s.client("test-dropbox-user")
        client.exec_command("mkdir dropbox")
        yield s
        client.exec_command("rm -r dropbox")


@pytest.fixture
def test_sftp_private_key():
    with open("tests/fixtures/sample-ssh-key", "r") as f:
        yield f.read()


@pytest.fixture(scope="function")
def mocked_ssm(aws_credentials, test_sftp_private_key):
    with mock_ssm():
        ssm = boto3.client("ssm", region_name="us-east-1")
        ssm.put_parameter(
            Name="/test/example/ALMA_API_ACQ_READ_KEY",
            Value="abc123",
            Type="SecureString",
        )
        ssm.put_parameter(
            Name="/test/example/ALMA_API_URL",
            Value="http://example.com/",
            Type="String",
        )
        ssm.put_parameter(
            Name="/test/example/ALMA_DATA_WAREHOUSE_USER",
            Value="fake_dw_user",
            Type="String",
        )
        ssm.put_parameter(
            Name="/test/example/ALMA_DATA_WAREHOUSE_PASSWORD",
            Value="fake_dw_password",
            Type="SecureString",
        )
        ssm.put_parameter(
            Name="/test/example/ALMA_DATA_WAREHOUSE_HOST",
            Value="dw.fake.edu",
            Type="String",
        )
        ssm.put_parameter(
            Name="/test/example/ALMA_DATA_WAREHOUSE_PORT",
            Value="0000",
            Type="String",
        )
        ssm.put_parameter(
            Name="/test/example/ALMA_DATA_WAREHOUSE_SID",
            Value="ABCDE",
            Type="String",
        )
        ssm.put_parameter(
            Name="/test/example/LLAMA_LOG_LEVEL",
            Value="warning",
            Type="String",
        )
        ssm.put_parameter(
            Name="/test/example/SAP_DROPBOX_HOST",
            Value="stage.host",
            Type="String",
        )
        ssm.put_parameter(
            Name="/test/example/SAP_DROPBOX_KEY",
            Value=test_sftp_private_key,
            Type="SecureString",
        )
        ssm.put_parameter(
            Name="/test/example/SAP_DROPBOX_PORT",
            Value="0000",
            Type="String",
        )
        ssm.put_parameter(
            Name="/test/example/SAP_DROPBOX_USER",
            Value="stage-dropbox-user",
            Type="String",
        )
        ssm.put_parameter(
            Name="/test/example/SAP_FINAL_RECIPIENT_EMAILS",
            Value="final_1@example.com,final_2@example.com",
            Type="StringList",
        )
        ssm.put_parameter(
            Name="/test/example/SAP_REPLY_TO_EMAIL",
            Value="replyto@example.com",
            Type="String",
        )
        ssm.put_parameter(
            Name="/test/example/SAP_REVIEW_RECIPIENT_EMAILS",
            Value="review@example.com",
            Type="StringList",
        )
        ssm.put_parameter(
            Name="/test/example/SAP_SEQUENCE",
            Value="1001,20210722000000,ser",
            Type="StringList",
        )
        ssm.put_parameter(
            Name="/test/example/SENTRY_DSN",
            Value="sentry_123456",
            Type="SecureString",
        )
        ssm.put_parameter(
            Name="/test/example/SES_SEND_FROM_EMAIL",
            Value="from@example.com",
            Type="String",
        )
        yield ssm


@pytest.fixture()
def po_line_record_all_fields():
    po_line_record_all = {
        "acquisition_method": {"desc": "Credit Card"},
        "vendor_account": "Corporation",
        "number": "POL-123",
        "resource_metadata": {"title": "Book title"},
        "price": {"sum": "12.0"},
        "created_date": "2021-05-13Z",
        "fund_distribution": [
            {"fund_code": {"value": "ABC"}, "amount": {"sum": "24.0"}}
        ],
        "note": [{"note_text": "CC-abc"}],
        "location": [{"quantity": 1}, {"quantity": 1}],
    }
    return po_line_record_all


@pytest.fixture()
def po_line_record_multiple_funds():
    po_line_record_multiple_funds = {
        "vendor_account": "Corporation",
        "number": "POL-123",
        "resource_metadata": {"title": "Book title"},
        "price": {"sum": "12.0"},
        "created_date": "2021-05-13Z",
        "fund_distribution": [
            {"fund_code": {"value": "ABC"}, "amount": {"sum": "6.0"}},
            {"fund_code": {"value": "GHI"}, "amount": {"sum": "6.0"}},
        ],
        "note": [{"note_text": ""}],
    }
    return po_line_record_multiple_funds


@pytest.fixture()
def po_line_record_spaces_in_title():
    po_line_record_spaces_in_title = {
        "vendor_account": "Corporation",
        "number": "POL-123",
        "resource_metadata": {"title": "A title"},
        "price": {"sum": "12.0"},
        "created_date": "2021-05-13Z",
        "fund_distribution": [
            {"fund_code": {"value": "ABC"}, "amount": {"sum": "6.0"}},
            {"fund_code": {"value": "DEF"}, "amount": {"sum": "6.0"}},
        ],
        "note": [{"note_text": ""}],
    }
    return po_line_record_spaces_in_title


@pytest.fixture()
def po_line_record_wrong_date():
    """A PO line record with the wrong date that should be filtered out."""
    po_line_record_all = {
        "acquisition_method": {"desc": "Credit Card"},
        "vendor_account": "Another corporation",
        "number": "POL-457",
        "resource_metadata": {"title": "DVD title"},
        "price": {"sum": "24.0"},
        "created_date": "2021-05-02Z",
        "fund_distribution": [{"fund_code": {"value": "DEF"}}],
        "note": [{"note_text": "CC-jkl"}],
    }
    return po_line_record_all


@pytest.fixture(scope="function")
def runner():
    return CliRunner()


@pytest.fixture(scope="function")
def s3():
    return S3()


@pytest.fixture()
def invoices_for_sap():
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
                    "cost object": "123456",
                    "G/L account": "0000001",
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
                    "cost object": "123456",
                    "G/L account": "0000001",
                },
                "123456-0000002": {
                    "amount": 148.50,
                    "cost object": "123456",
                    "G/L account": "0000002",
                },
                "1123456-0000003": {
                    "amount": 235.54,
                    "cost object": "123456",
                    "G/L account": "0000003",
                },
                "123456-0000004": {
                    "amount": 75,
                    "cost object": "123456",
                    "G/L account": "0000004",
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
                    "cost object": "123456",
                    "G/L account": "0000001",
                },
            },
        },
    ]
    return invoices


@pytest.fixture()
def problem_invoices():
    problem_invoices = [
        {
            "fund_errors": ["over-encumbered", "also-over-encumbered"],
            "multibyte_errors": [
                {"field": "vendor:address:lines:0", "character": "‑"},
                {"field": "vendor:city", "character": "ƒ"},
            ],
            "date": datetime(2021, 5, 12),
            "id": "9991",
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
                        "12‑3 salad Street",
                        "Second Floor",
                    ],
                    "city": "San ƒrancisco",
                    "state or province": "CA",
                    "postal code": "94109",
                    "country": "US",
                },
            },
        },
        {
            "fund_errors": ["also-over-encumbered"],
            "multibyte_errors": [{"field": "vendor:address:lines:0", "character": "‑"}],
            "date": datetime(2021, 5, 11),
            "id": "9992",
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
                    "postal code": "30384‑7991",
                    "country": "US",
                },
            },
        },
        {
            "vendor_address_error": "YBP-no-address",
            "date": datetime(2021, 5, 11),
            "id": "9993",
            "number": "444666",
            "type": "monograph",
            "payment method": "ACCOUNTINGDEPARTMENT",
            "total amount": 1067.04,
            "currency": "USD",
        },
    ]
    return problem_invoices


@pytest.fixture()
def invoices_for_sap_with_different_payment_method():
    """a list of invoices which includes an invoice with
    a payment method other than ACCOUNTINGDEPARTMENT which should
    get filtered out when generating summary reports"""
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
                "code": "DANGER",
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
                    "cost object": "123456",
                    "G/L account": "0000001",
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
                    "cost object": "123456",
                    "G/L account": "0000001",
                },
                "123456-0000002": {
                    "amount": 148.50,
                    "cost object": "123456",
                    "G/L account": "0000002",
                },
                "1123456-0000003": {
                    "amount": 235.54,
                    "cost object": "123456",
                    "G/L account": "0000003",
                },
                "123456-0000004": {
                    "amount": 75,
                    "cost object": "123456",
                    "G/L account": "0000004",
                },
            },
        },
        {
            "date": datetime(2021, 5, 12),
            "id": "0000055555000001",
            "number": "12345",
            "type": "monograph",
            "payment method": "BAZ",
            "total amount": 150,
            "currency": "USD",
            "vendor": {
                "name": "Foo Bar Books",
                "code": "FOOBAR",
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
                    "cost object": "123456",
                    "G/L account": "0000001",
                },
            },
        },
    ]
    return invoices


@pytest.fixture()
def sap_data_file():
    """a string representing a datafile of invoices to send to SAP"""
    # this test data is formatted to make it more readable
    # each line corresponds to a field in the SAP data file spec
    # See https://docs.google.com/spreadsheets/d/1PSEYSlPaQ0g2LTEIR6hdyBPzWrZLRK2K/
    # edit#gid=1667272331
    sap_data = "B\
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
0000001   \
123456      \
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
P.O. Box 123456                    \
 \
                                   \
30384-7991\
GA \
US \
                                                  \
                                   \
\n\
C\
0000001   \
123456      \
          608.00\
 \
\n\
C\
0000002   \
123456      \
          148.50\
 \
\n\
C\
0000003   \
123456      \
          235.54\
 \
\n\
D\
0000004   \
123456      \
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
0000001   \
123456      \
          150.00\
 \
\n"
    return sap_data
