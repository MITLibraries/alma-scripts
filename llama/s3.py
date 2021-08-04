from s3_concat import S3Concat


def concatenate_files(date, session, bucket, key_prefix, output_filename):
    """Concatenates files with the provided key_prefix in the provided bucket in a
    random order"""
    job = S3Concat(
        bucket,
        output_filename,
        None,
        session=session,
    )
    job.add_files(f"{key_prefix}{date}")
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
