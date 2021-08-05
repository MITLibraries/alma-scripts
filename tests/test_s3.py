import pytest

from llama.s3 import S3


def test_concatenate_files_no_files_with_prefix_exist(mocked_s3):
    s3 = S3()
    with pytest.raises(KeyError):
        s3.concatenate_files("ils-sftp", "fake_prefix", "result.mrc")


def test_concatenate_files_bucket_does_not_exist(mocked_s3):
    s3 = S3()
    with pytest.raises(s3.client.exceptions.NoSuchBucket):
        s3.concatenate_files(
            "fake_bucket",
            "exlibris/Timdex/UPDATE/ALMA_UPDATE_EXPORT__20210101",
            "result.mrc",
        )


def test_concatenate_files_output_file_already_exists(mocked_s3):
    s3 = S3()
    s3.concatenate_files(
        "ils-sftp",
        "exlibris/Timdex/UPDATE/ALMA_UPDATE_EXPORT__20210101",
        "exlibris/Timdex/UPDATE/ALMA_UPDATE_EXPORT__20201012_marc1.mrc",
    )
    concatenated_file = s3.client.get_object(
        Bucket="ils-sftp",
        Key="exlibris/Timdex/UPDATE/ALMA_UPDATE_EXPORT__20201012_marc1.mrc",
    )
    assert concatenated_file["Body"].read() == b"MARC 001MARC 002"


def test_concatenate_files_includes_expected_content(mocked_s3):
    s3 = S3()
    s3.concatenate_files(
        "ils-sftp",
        "exlibris/Timdex/UPDATE/ALMA_UPDATE_EXPORT__20210101",
        "result.mrc",
    )
    concatenated_file = s3.client.get_object(Bucket="ils-sftp", Key="result.mrc")
    assert concatenated_file["Body"].read() == b"MARC 001MARC 002"


def test_move_file_key_does_not_exist(mocked_s3):
    s3 = S3()
    with pytest.raises(s3.client.exceptions.ClientError):
        s3.move_file("fake_key", "ils-sftp", "dip-ils-bucket")


def test_move_file_source_bucket_does_not_exist(mocked_s3):
    s3 = S3()
    with pytest.raises(s3.client.exceptions.NoSuchBucket):
        s3.move_file(
            "exlibris/Timdex/UPDATE/ALMA_UPDATE_EXPORT__20210101_marc1.mrc",
            "fake_bucket",
            "dip-ils-bucket",
        )


def test_move_file_destination_bucket_does_not_exist(mocked_s3):
    s3 = S3()
    with pytest.raises(s3.client.exceptions.NoSuchBucket):
        s3.move_file(
            "exlibris/Timdex/UPDATE/ALMA_UPDATE_EXPORT__20210101_marc1.mrc",
            "ils-sftp",
            "fake_bucket",
        )


def test_move_file_replaces_if_key_already_exists_in_destination_bucket(mocked_s3):
    s3 = S3()
    s3.client.put_object(
        Bucket="dip-ils-bucket",
        Key="exlibris/Timdex/UPDATE/ALMA_UPDATE_EXPORT__20210101_marc1.mrc",
        Body="I am already here!",
    )
    s3.move_file(
        "exlibris/Timdex/UPDATE/ALMA_UPDATE_EXPORT__20210101_marc1.mrc",
        "ils-sftp",
        "dip-ils-bucket",
    )
    replaced_file = s3.client.get_object(
        Bucket="dip-ils-bucket",
        Key="exlibris/Timdex/UPDATE/ALMA_UPDATE_EXPORT__20210101_marc1.mrc",
    )
    assert replaced_file["Body"].read() == b"MARC 001"


def test_move_file_copies_and_deletes_file(mocked_s3):
    s3 = S3()
    assert len(s3.client.list_objects(Bucket="ils-sftp")["Contents"]) == 4
    assert "Contents" not in s3.client.list_objects(Bucket="dip-ils-bucket")
    s3.move_file(
        "exlibris/Timdex/UPDATE/ALMA_UPDATE_EXPORT__20210101_marc1.mrc",
        "ils-sftp",
        "dip-ils-bucket",
    )
    assert len(s3.client.list_objects(Bucket="ils-sftp")["Contents"]) == 3
    assert len(s3.client.list_objects(Bucket="dip-ils-bucket")["Contents"]) == 1
