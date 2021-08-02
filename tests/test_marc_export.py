import os

import boto3
import pytest
from moto import mock_s3

from llama import marc_export


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
def s3_client(aws_credentials):
    with mock_s3():
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="ils-sftp")
        s3.put_object(
            Bucket="ils-sftp",
            Key="UPDATE/1901-01-01_marc1.mrc",
            Body="MARC 001",
        )
        s3.put_object(
            Bucket="ils-sftp",
            Key="UPDATE/1901-01-01_marc2.mrc",
            Body="MARC 002",
        )
        s3.create_bucket(Bucket="dip-ils-bucket")
        yield s3


def test_get_file_names_from_bucket(s3_client, bucket_env):
    file_keys = marc_export.get_file_keys_from_bucket(
        s3_client,
        "ils-sftp",
        "UPDATE",
        ".mrc",
    )
    assert file_keys == ["UPDATE/1901-01-01_marc1.mrc", "UPDATE/1901-01-01_marc2.mrc"]


def test_marc_update_export(s3_client, bucket_env):
    assert len(s3_client.list_objects(Bucket="ils-sftp")["Contents"]) == 2
    assert "Contents" not in s3_client.list_objects(Bucket="dip-ils-bucket")
    marc_export.marc_update_export("UPDATE/")
    assert len(s3_client.list_objects(Bucket="dip-ils-bucket")["Contents"]) == 1
    for file in s3_client.list_objects(Bucket="ils-sftp")["Contents"]:
        assert "UPDATE" not in file["Key"]
        assert "ARCHIVE" in file["Key"]


def test_move_s3_file(s3_client, bucket_env):
    assert len(s3_client.list_objects(Bucket="ils-sftp")["Contents"]) == 2
    assert "Contents" not in s3_client.list_objects(Bucket="dip-ils-bucket")
    marc_export.move_s3_file(
        s3_client,
        "ils-sftp",
        "UPDATE/1901-01-01_marc1.mrc",
        "dip-ils-bucket",
        "ARCHIVE/1901-01-01_marc1.mrc",
    )
    assert len(s3_client.list_objects(Bucket="ils-sftp")["Contents"]) == 1
    assert len(s3_client.list_objects(Bucket="dip-ils-bucket")["Contents"]) == 1
