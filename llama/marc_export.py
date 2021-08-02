import os
from datetime import datetime

import boto3
from s3_concat import S3Concat


def get_file_keys_from_bucket(client, bucket, key_prefix, file_type=""):
    """Get file keys from bucket that match with key prefix and file type."""
    bucket_file_list = client.list_objects(Bucket=bucket)["Contents"]
    file_keys = []
    for file in [
        f
        for f in bucket_file_list
        if f["Key"].endswith(file_type) and f["Key"].startswith(key_prefix)
    ]:
        file_keys.append(file["Key"])
    return file_keys


def move_s3_file(client, old_bucket, old_key, new_bucket, new_key):
    """Duplicate behavior of AWS CLI mv command by copying the source object to a new key
    and then deleting the source object."""
    client.copy_object(
        Bucket=new_bucket,
        CopySource=f"{old_bucket}/{old_key}",
        Key=new_key,
    )
    client.delete_object(
        Bucket=old_bucket,
        Key=old_key,
    )


def marc_update_export(key_prefix):
    """Concatenate files from UPDATE bucket, move the new file to another bucket, and
    change the keys of the original files from UPDATE to ARCHIVE."""
    session = boto3.session.Session()
    s3 = session.client("s3")
    today = datetime.today().strftime("%Y-%m-%d")

    file_keys = get_file_keys_from_bucket(
        s3, os.environ["ALMA_BUCKET"], key_prefix, ".mrc"
    )
    file_keys.sort()

    job = S3Concat(
        os.environ["ALMA_BUCKET"],
        f"ALMA_UPDATE_EXPORT_{today}.mrc",
        None,
        session=session,
    )
    for file_key in file_keys:
        job.add_file(file_key)
    job.concat()

    move_s3_file(
        s3,
        os.environ["ALMA_BUCKET"],
        f"ALMA_UPDATE_EXPORT_{today}.mrc",
        os.environ["DIP_ALEPH_BUCKET"],
        f"ALMA_UPDATE_EXPORT_{today}.mrc",
    )

    for file_key in file_keys:
        file_name = file_key.replace(key_prefix, "")
        move_s3_file(
            s3,
            os.environ["ALMA_BUCKET"],
            file_key,
            os.environ["ALMA_BUCKET"],
            f"ARCHIVE/{file_name}",
        )
