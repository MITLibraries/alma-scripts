import os

import boto3
import pytest
import requests_mock
from click.testing import CliRunner
from moto import mock_s3, mock_ssm

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
        fund_code_record_abc = {"fund": [{"external_id": "456"}]}
        fund_code_record_def = {"fund": [{"external_id": "789"}]}
        po_lines = {
            "po_line": [
                {"number": "POL-123", "created_date": "2021-05-13Z"},
                {"number": "POL-456", "created_date": "2021-05-02Z"},
            ]
        }
        m.get("http://example.com/acq/funds?q=fund_code~ABC", json=fund_code_record_abc)
        m.get("http://example.com/acq/funds?q=fund_code~DEF", json=fund_code_record_def)
        m.get(
            "http://example.com/acq/po-lines?status=ACTIVE&limit=100&offset=0",
            json=po_lines,
        )
        m.get(
            "http://example.com/acq/po-lines?status=ACTIVE&limit=100&offset=100",
            json={},
        )
        m.get("http://example.com/acq/po-lines/POL-123", json=po_line_record_all_fields)
        m.get("http://example.com/acq/po-lines/POL-456", json=po_line_record_wrong_date)
        yield m


@pytest.fixture()
def mocked_alma_api_client():
    alma_api_client = Alma_API_Client("abc123", "http://example.com/")
    alma_api_client.create_api_headers("application/json", "application/json")
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


@mock_ssm
@pytest.fixture(scope="function")
def mocked_ssm(aws_credentials):
    with mock_ssm():
        ssm = boto3.client("ssm", region_name="us-east-1")
        ssm.put_parameter(
            Name="/test/example/ALMA_API_PROD_ACQ_KEY",
            Value="abc123",
            Type="SecureString",
        )
        ssm.put_parameter(
            Name="/test/example/ALMA_API_URL",
            Value="http://example.com/",
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
    }
    return po_line_record_all


@pytest.fixture()
def po_line_record_missing_fields():
    po_line_record_missing_fields = {
        "vendor_account": "Corporation",
        "number": "POL-123",
        "resource_metadata": {"title": None},
        "price": {"sum": "0.0"},
        "created_date": "2021-05-13Z",
        "fund_distribution": [{"fund_code": {"value": ""}, "amount": {"sum": ""}}],
        "note": [],
    }
    return po_line_record_missing_fields


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
            {"fund_code": {"value": "DEF"}, "amount": {"sum": "6.0"}},
        ],
        "note": [{"note_text": ""}],
    }
    return po_line_record_multiple_funds


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
