from llama.cli import cli


def test_concat_timdex_export(s3_session, bucket_env, date_today, runner):
    # today's date
    assert len(s3_session.client("s3").list_objects(Bucket="ils-sftp")["Contents"]) == 4
    assert "Contents" not in s3_session.client("s3").list_objects(
        Bucket="dip-ils-bucket"
    )
    result = runner.invoke(
        cli,
        [
            "concat-timdex-export",
            "--export_type",
            "UPDATE",
        ],
    )
    assert result.exit_code == 0
    concatenated_file = s3_session.client("s3").get_object(
        Bucket="dip-ils-bucket", Key=f"ALMA_UPDATE_EXPORT_{date_today}.mrc"
    )
    assert concatenated_file["Body"].read() == b"MARC 001MARC 002"

    # past date
    assert len(s3_session.client("s3").list_objects(Bucket="ils-sftp")["Contents"]) == 4
    result = runner.invoke(
        cli,
        [
            "concat-timdex-export",
            "--export_type",
            "UPDATE",
            "--date",
            "20201012",
        ],
    )
    assert result.exit_code == 0
    concatenated_file = s3_session.client("s3").get_object(
        Bucket="dip-ils-bucket", Key="ALMA_UPDATE_EXPORT_20201012.mrc"
    )
    assert concatenated_file["Body"].read() == b"MARC 003MARC 004"

    # no files matching specified date
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
            "19560101",
        ],
    )
    exception_text = (
        "No files with key beginning: "
        "exlibris/Timdex/UPDATE/ALMA_UPDATE_EXPORT__19560101\n"
    )
    assert result.output == exception_text
    assert result.exit_code == 1
