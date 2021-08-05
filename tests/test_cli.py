import os

from freezegun import freeze_time

from llama.cli import cli
from llama.s3 import S3


def test_concat_timdex_export_all_options_provided_success(mocked_s3, runner):
    s3 = S3()
    assert len(s3.client.list_objects(Bucket="ils-sftp")["Contents"]) == 4
    assert "Contents" not in s3.client.list_objects(Bucket="dip-ils-bucket")
    result = runner.invoke(
        cli,
        [
            "concat-timdex-export",
            "--export_type",
            "UPDATE",
            "--source_bucket",
            "ils-sftp",
            "--destination_bucket",
            "dip-ils-bucket",
            "--date",
            "20210101",
        ],
    )
    assert result.exit_code == 0
    assert (
        "Concatenated file ALMA_UPDATE_EXPORT_20210101.mrc succesfully created"
        in result.output
    )
    concatenated_file = s3.client.get_object(
        Bucket="dip-ils-bucket", Key="ALMA_UPDATE_EXPORT_20210101.mrc"
    )
    assert concatenated_file["Body"].read() == b"MARC 001MARC 002"


@freeze_time("2021-01-01")
def test_concat_timdex_export_no_options_provided_success(mocked_s3, runner):
    os.environ["ALMA_BUCKET"] = "ils-sftp"
    os.environ["DIP_ALEPH_BUCKET"] = "dip-ils-bucket"
    s3 = S3()
    assert len(s3.client.list_objects(Bucket="ils-sftp")["Contents"]) == 4
    assert "Contents" not in s3.client.list_objects(Bucket="dip-ils-bucket")
    result = runner.invoke(
        cli,
        [
            "concat-timdex-export",
            "--export_type",
            "UPDATE",
        ],
    )
    assert result.exit_code == 0
    concatenated_file = s3.client.get_object(
        Bucket="dip-ils-bucket", Key="ALMA_UPDATE_EXPORT_20210101.mrc"
    )
    assert concatenated_file["Body"].read() == b"MARC 001MARC 002"


def test_concat_timdex_export_key_error(mocked_s3, runner):
    result = runner.invoke(
        cli,
        [
            "concat-timdex-export",
            "--export_type",
            "UPDATE",
            "--source_bucket",
            "ils-sftp",
            "--destination_bucket",
            "dip-ils-bucket",
            "--date",
            "20211212",
        ],
    )
    assert result.exit_code == 1
    assert "No files found in bucket ils-sftp with key prefix" in result.output


def test_concat_timdex_export_bucket_error(mocked_s3, runner):
    result = runner.invoke(
        cli,
        [
            "concat-timdex-export",
            "--export_type",
            "UPDATE",
            "--source_bucket",
            "fake-bucket",
            "--destination_bucket",
            "dip-ils-bucket",
            "--date",
            "20210101",
        ],
    )
    assert result.exit_code == 1
    assert "One or more supplied buckets does not exist" in result.output
