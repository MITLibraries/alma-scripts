import os

from s3_concat import S3Concat


def concatenate_files(today, session, key_prefix):
    """Concatenate files into a date-named file. s3Concat function creates the
    concatenated file in the same directory as the source files after which it will be
    copied to the destination directory and deleted in the original directory."""
    job = S3Concat(
        os.environ["ALMA_BUCKET"],
        f"ALMA_UPDATE_EXPORT_{today}.mrc",
        None,
        session=session,
    )
    job.add_files(f"{key_prefix}{today}")
    job.concat()


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
