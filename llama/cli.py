import sys
from datetime import datetime

import boto3
import click

from llama import s3


@click.group()
@click.pass_context
def cli(ctx):
    ctx.obj = {}
    ctx.obj["today"] = datetime.today()


@cli.command()
@click.option(
    "--export_type",
    required=True,
    type=click.Choice(["FULL", "UPDATE"], case_sensitive=False),
)
@click.option("--source_bucket", envvar="ALMA_BUCKET", required=True)
@click.option("--destination_bucket", envvar="DIP_ALEPH_BUCKET", required=True)
@click.option("--date")
@click.pass_context
def concat_timdex_export(
    ctx,
    export_type,
    source_bucket,
    destination_bucket,
    date,
):
    """Concatenate files from UPDATE bucket and move the new file to destination bucket"""
    if date is None:
        date = ctx.obj["today"].strftime("%Y%m%d")
    session = boto3.session.Session()
    s3_client = session.client("s3")
    key_prefix = f"exlibris/Timdex/{export_type}/ALMA_{export_type}_EXPORT__"
    try:
        s3.concatenate_files(
            date,
            session,
            source_bucket,
            key_prefix,
            f"ALMA_UPDATE_EXPORT_{date}.mrc",
        )
    except KeyError:
        print(f"No files with key beginning: {key_prefix}{date}")
        sys.exit(1)
    # S3Concat function creates the concatenated file in the same directory as the source
    # files after which it will be copied to the destination directory and deleted in
    # the original directory
    s3.move_s3_file(
        s3_client,
        source_bucket,
        f"ALMA_{export_type}_EXPORT_{date}.mrc",
        destination_bucket,
        f"ALMA_{export_type}_EXPORT_{date}.mrc",
    )
