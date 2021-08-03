from llama import marc_export


def test_concatenate_files(s3_session, bucket_env, date_today):
    marc_export.concatenate_files(
        date_today, s3_session, "exlibris/Timdex/UPDATE/ALMA_UPDATE_EXPORT__"
    )
    concat = s3_session.client("s3").get_object(
        Bucket="ils-sftp", Key=f"ALMA_UPDATE_EXPORT_{date_today}.mrc"
    )
    assert concat["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_move_s3_file(s3_session, bucket_env, date_today):
    assert len(s3_session.client("s3").list_objects(Bucket="ils-sftp")["Contents"]) == 2
    assert "Contents" not in s3_session.client("s3").list_objects(
        Bucket="dip-ils-bucket"
    )
    marc_export.move_s3_file(
        s3_session.client("s3"),
        "ils-sftp",
        f"exlibris/Timdex/UPDATE/ALMA_UPDATE_EXPORT__{date_today}_marc1.mrc",
        "dip-ils-bucket",
        f"ARCHIVE/ALMA_UPDATE_EXPORT__{date_today}_marc1.mrc",
    )
    assert len(s3_session.client("s3").list_objects(Bucket="ils-sftp")["Contents"]) == 1
    assert (
        len(s3_session.client("s3").list_objects(Bucket="dip-ils-bucket")["Contents"])
        == 1
    )
