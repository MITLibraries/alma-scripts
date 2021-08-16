from boto3 import client
from s3_concat import S3Concat


class S3:
    """A S3 class that provides a generic boto3 s3 client for interacting with S3
    objects, along with specific S3 functionality necessary for llama scripts"""

    def __init__(self):
        self.client = client("s3")

    def concatenate_files(self, bucket, prefix, output_filename):
        """Concatenate all files with the provided prefix within an S3 bucket into a new
        file with the provided output file name. The source files may be concatenated
        in a random order, and the output file will be created in the same bucket as
        the source files."""
        job = S3Concat(
            bucket=bucket,
            key=output_filename,
            min_file_size=None,
            s3_client=self.client,
        )
        job.add_files(prefix)
        job.concat()

    def move_file(self, key, source_bucket, destination_bucket):
        """Duplicate behavior of AWS CLI mv command by copying the object from the
        source bucket to a destination bucket and then deleting the object from the
        source bucket. Note that if the provided key already exists in the destination
        bucket, this will replace that object with the object from the source bucket."""
        self.client.copy_object(
            Bucket=destination_bucket,
            CopySource=f"{source_bucket}/{key}",
            Key=key,
        )
        self.client.delete_object(
            Bucket=source_bucket,
            Key=key,
        )
