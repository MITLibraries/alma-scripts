import json
import os
from datetime import datetime

import boto3
import pytest
import requests_mock
from click.testing import CliRunner
from moto import mock_s3, mock_ses, mock_ssm

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
        with open("tests/fixtures/funds.json") as f:
            funds = json.load(f)
            m.get(
                "http://example.com/acq/funds?q=fund_code~ABC",
                json={"fund": [funds["fund"][0]]},
            )
            m.get(
                "http://example.com/acq/funds?q=fund_code~DEF",
                json={"fund": [funds["fund"][1]]},
            )
            m.get(
                "http://example.com/acq/funds?q=fund_code~GHI",
                json={"fund": [funds["fund"][2]]},
            )
            m.get(
                "http://example.com/acq/funds?q=fund_code~JKL",
                json={"fund": [funds["fund"][3]]},
            )
        with open("tests/fixtures/invoices.json") as f:
            invoices_json = json.load(f)
        m.get("http://example.com/acq/invoices", json=invoices_json)
        m.get(
            "http://example.com/acq/invoices/558809630001021",
            json=invoices_json["invoice"][0],
        )
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
        m.get("http://example.com/acq/po-lines/POL-123", json=po_line_record_all_fields)
        m.get("http://example.com/acq/po-lines/POL-456", json=po_line_record_wrong_date)
        with open("tests/fixtures/vendor_aaa.json") as f:
            m.get("http://example.com/acq/vendors/AAA", json=json.load(f))
        with open("tests/fixtures/vendor.json") as f:
            m.get("http://example.com/acq/vendors/BKHS", json=json.load(f))
        with open("tests/fixtures/vendor_vend-s.json") as f:
            m.get("http://example.com/acq/vendors/VEND-S", json=json.load(f))
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
        with open("tests/fixtures/invoice_paid.json") as f:
            m.post("http://example.com/acq/invoices/558809630001021", text=f.read())
        yield m


@pytest.fixture()
def mocked_alma_no_invoices():
    with requests_mock.Mocker() as m:
        m.get("http://example.com/acq/invoices", json={"total_record_count": 0})
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


@pytest.fixture(scope="function")
def mocked_ssm(aws_credentials):
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
            Name="/test/example/SAP_REPLY_TO_EMAIL",
            Value="replyto@example.com",
            Type="String",
        )
        ssm.put_parameter(
            Name="/test/example/SAP_REPORT_RECIPIENT_EMAILS",
            Value="report_1@example.com,report_2@example.com",
            Type="StringList",
        )
        ssm.put_parameter(
            Name="/test/example/SAP_SUMMARY_RECIPIENT_EMAILS",
            Value="summary@example.com",
            Type="StringList",
        )
        ssm.put_parameter(
            Name="/test/example/SES_SEND_FROM_EMAIL",
            Value="from@example.com",
            Type="String",
        )
        ssm.put_parameter(
            Name="/test/example/SENTRY_DSN",
            Value="sentry_123456",
            Type="SecureString",
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
    return invoices


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
                    "G/L account": "123456",
                    "cost object": "0000001",
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
    return sap_data
