import os
from datetime import datetime

import boto3
import pytest
from click.testing import CliRunner
from moto import mock_s3


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"


@pytest.fixture(scope="function")
def bucket_env():
    """Mocked AWS Credentials for moto."""
    os.environ["ALMA_BUCKET"] = "ils-sftp"
    os.environ["DIP_ALEPH_BUCKET"] = "dip-ils-bucket"


@pytest.fixture(scope="function")
def date_today():
    date_today = datetime.today().strftime("%Y%m%d")
    return date_today


@pytest.fixture(scope="function")
def runner():
    return CliRunner()


@pytest.fixture(scope="function")
def s3_session(aws_credentials, date_today):
    with mock_s3():
        session = boto3.session.Session()
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="ils-sftp")
        s3.put_object(
            Bucket="ils-sftp",
            Key=f"exlibris/Timdex/UPDATE/ALMA_UPDATE_EXPORT__{date_today}_marc1.mrc",
            Body="MARC 001",
        )
        s3.put_object(
            Bucket="ils-sftp",
            Key=f"exlibris/Timdex/UPDATE/ALMA_UPDATE_EXPORT__{date_today}_marc2.mrc",
            Body="MARC 002",
        )
        s3.create_bucket(Bucket="dip-ils-bucket")
        yield session
