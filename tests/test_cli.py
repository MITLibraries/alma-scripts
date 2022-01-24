import boto3
from freezegun import freeze_time
from moto import mock_ses

from llama.cli import cli


@mock_ses
def test_cc_slips_date_provided(mocked_alma, mocked_ssm, runner):
    ses_client = boto3.client("ses", region_name="us-east-1")
    ses_client.verify_email_identity(EmailAddress="noreply@example.com")
    result = runner.invoke(
        cli,
        [
            "cc-slips",
            "--date",
            "2021-05-13",
            "--source_email",
            "noreply@example.com",
            "--recipient_email",
            "test1@example.com",
            "--recipient_email",
            "test2@example.com",
        ],
    )
    assert result.exit_code == 0


@mock_ses
@freeze_time("2021-05-14")
def test_cc_slips_no_date_provided(mocked_alma, mocked_ssm, runner):
    ses_client = boto3.client("ses", region_name="us-east-1")
    ses_client.verify_email_identity(EmailAddress="noreply@example.com")
    result = runner.invoke(
        cli,
        [
            "cc-slips",
            "--source_email",
            "noreply@example.com",
            "--recipient_email",
            "test1@example.com",
            "--recipient_email",
            "test2@example.com",
        ],
    )
    assert result.exit_code == 0


@mock_ses
def test_cc_slips_no_records_for_date_provided(mocked_alma, mocked_ssm, runner):
    ses_client = boto3.client("ses", region_name="us-east-1")
    ses_client.verify_email_identity(EmailAddress="noreply@example.com")
    result = runner.invoke(
        cli,
        [
            "cc-slips",
            "--date",
            "2021-03-10",
            "--source_email",
            "noreply@example.com",
            "--recipient_email",
            "test1@example.com",
            "--recipient_email",
            "test2@example.com",
        ],
    )
    assert result.exit_code == 0


def test_concat_timdex_export_all_options_provided_success(mocked_s3, runner, s3):
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
def test_concat_timdex_export_no_options_provided_success(
    bucket_env, mocked_s3, runner, s3
):
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


def test_create_sandbox_sap_data(mocked_alma_sample_data, runner):
    result = runner.invoke(cli, ["create-sandbox-sap-data"])
    assert result.exit_code == 0


def test_sap_invoices_review_run(runner, mocked_alma, mocked_ses):
    result = runner.invoke(cli, ["sap-invoices"])
    assert result.exit_code == 0


def test_sap_invoices_review_run_no_invoices(runner, mocked_alma_no_invoices):
    result = runner.invoke(cli, ["sap-invoices"])
    assert result.exit_code == 1


def test_sap_invoices_review_run_dry_run(runner, mocked_alma):
    result = runner.invoke(cli, ["sap-invoices", "--dry-run"])
    assert result.exit_code == 0


def test_sap_invoices_final_run(runner, mocked_alma, mocked_ses):
    result = runner.invoke(cli, ["sap-invoices", "--final-run"])
    assert result.exit_code == 0


def test_sap_invoices_final_run_dry_run(runner, mocked_alma):
    result = runner.invoke(cli, ["sap-invoices", "--final-run", "--dry-run"])
    assert result.exit_code == 0
