import os
from datetime import datetime

import boto3
import click

from llama import marc_export


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
@click.option(
    "--key_prefix",
    required=True,
)
@click.pass_context
def concat_timdex_export(ctx, export_type, key_prefix):
    """Concatenate files from UPDATE bucket and move the new file to destination bucket"""
    today = ctx.obj["today"].strftime("%Y%m%d")
    session = boto3.session.Session()
    s3_client = session.client("s3")
    marc_export.concatenate_files(today, session, key_prefix)
    marc_export.move_s3_file(
        s3_client,
        os.environ["ALMA_BUCKET"],
        f"ALMA_UPDATE_EXPORT_{today}.mrc",
        os.environ["DIP_ALEPH_BUCKET"],
        f"ALMA_UPDATE_EXPORT_{today}.mrc",
    )
