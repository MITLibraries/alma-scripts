from llama.cli import cli


def test_concat_timdex_export(s3_session, bucket_env, date_today, runner):
    assert len(s3_session.client("s3").list_objects(Bucket="ils-sftp")["Contents"]) == 2
    assert "Contents" not in s3_session.client("s3").list_objects(
        Bucket="dip-ils-bucket"
    )
    result = runner.invoke(
        cli,
        [
            "concat-timdex-export",
            "--export_type",
            "UPDATE",
            "--key_prefix",
            "exlibris/Timdex/UPDATE/ALMA_UPDATE_EXPORT__",
        ],
    )
    assert result.exit_code == 0

    assert (
        len(s3_session.client("s3").list_objects(Bucket="dip-ils-bucket")["Contents"])
        == 1
    )
