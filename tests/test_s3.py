from llama import s3


def test_concatenate_files(s3_session, bucket_env):
    # today's date
    s3.concatenate_files(
        "20210101",
        s3_session,
        "ils-sftp",
        "exlibris/Timdex/UPDATE/ALMA_UPDATE_EXPORT__",
        "ALMA_UPDATE_EXPORT_20210101.mrc",
    )
    concatenated_file = s3_session.client("s3").get_object(
        Bucket="ils-sftp", Key="ALMA_UPDATE_EXPORT_20210101.mrc"
    )
    assert concatenated_file["Body"].read() == b"MARC 001MARC 002"

    # past date
    s3.concatenate_files(
        "20201012",
        s3_session,
        "ils-sftp",
        "exlibris/Timdex/UPDATE/ALMA_UPDATE_EXPORT__",
        "ALMA_UPDATE_EXPORT_20201012.mrc",
    )
    concatenated_file = s3_session.client("s3").get_object(
        Bucket="ils-sftp", Key="ALMA_UPDATE_EXPORT_20201012.mrc"
    )
    assert concatenated_file["Body"].read() == b"MARC 003MARC 004"


def test_move_s3_file(s3_session, bucket_env):
    assert len(s3_session.client("s3").list_objects(Bucket="ils-sftp")["Contents"]) == 4
    assert "Contents" not in s3_session.client("s3").list_objects(
        Bucket="dip-ils-bucket"
    )
    s3.move_s3_file(
        s3_session.client("s3"),
        "ils-sftp",
        "exlibris/Timdex/UPDATE/ALMA_UPDATE_EXPORT__20210101_marc1.mrc",
        "dip-ils-bucket",
        "ARCHIVE/ALMA_UPDATE_EXPORT__20201012_marc1.mrc",
    )
    assert len(s3_session.client("s3").list_objects(Bucket="ils-sftp")["Contents"]) == 3
    assert (
        len(s3_session.client("s3").list_objects(Bucket="dip-ils-bucket")["Contents"])
        == 1
    )
