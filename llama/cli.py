import datetime

import click
from botocore.exceptions import ClientError

from llama import credit_card_slips
from llama.alma import Alma_API_Client
from llama.s3 import S3
from llama.ses import SES


@click.group()
@click.pass_context
def cli(ctx):
    ctx.ensure_object(dict)
    ctx.obj["today"] = datetime.datetime.today()


@cli.command()
@click.option(
    "--date",
    help=(
        "Optional date of exports to process, in 'YYYY-MM-DD' format. Defaults to "
        "yesterday's date if not provided."
    ),
)
@click.option(
    "--source_email",
    required=True,
    help="The email address sending the credit card slips.",
)
@click.option(
    "--recipient_email",
    required=True,
    multiple=True,
    help="The email address receiving the credit card slips. Repeatable",
)
@click.pass_context
def cc_slips(ctx, date, source_email, recipient_email):
    if date is None:
        date = (ctx.obj["today"] - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    alma_api_client = Alma_API_Client()
    alma_api_client.create_api_headers("application/json", "application/json")
    credit_card_full_po_lines = (
        credit_card_slips.get_credit_card_full_po_lines_from_date(alma_api_client, date)
    )
    po_line_dicts = credit_card_slips.create_po_line_dicts(
        alma_api_client, credit_card_full_po_lines
    )
    credit_card_slip_xml_data = credit_card_slips.xml_data_from_dicts(po_line_dicts)
    ses_client = SES()
    message = ses_client.create_email(
        f"Credit card slips {date}",
        credit_card_slip_xml_data,
        f"{date}_credit_card_slips.htm",
    )
    try:
        response = ses_client.send_email(
            source_email,
            list(recipient_email),
            message,
        )
    except ClientError as e:
        click.echo(e.response["Error"]["Message"])
    else:
        click.echo(f'Email sent! Message ID: {response["MessageId"]}')


@cli.command()
@click.option(
    "--export_type",
    required=True,
    type=click.Choice(["FULL", "UPDATE"], case_sensitive=False),
)
@click.option("--source_bucket", envvar="ALMA_BUCKET", required=True)
@click.option("--destination_bucket", envvar="DIP_ALEPH_BUCKET", required=True)
@click.option(
    "--date",
    help=(
        "Optional date of exports to process, in 'YYYYMMDD' format. Defaults to "
        "today's date if not provided."
    ),
)
@click.pass_context
def concat_timdex_export(ctx, export_type, source_bucket, destination_bucket, date):
    """Concatenate all files with a given date prefix to the source bucket and move the
    new concatenated file to the destination bucket. This command assumes certain file
    naming conventions that are used in the Alma export jobs for TIMDEX exports."""
    if date is None:
        date = ctx.obj["today"].strftime("%Y%m%d")
    s3 = S3()
    key_prefix = f"exlibris/Timdex/{export_type}/ALMA_{export_type}_EXPORT__{date}"
    output_filename = f"ALMA_{export_type}_EXPORT_{date}.mrc"
    try:
        s3.concatenate_files(source_bucket, key_prefix, output_filename)
        s3.move_file(output_filename, source_bucket, destination_bucket)
    except KeyError:
        raise click.ClickException(
            f"No files found in bucket {source_bucket} with key prefix: {key_prefix}"
        )
    except s3.client.exceptions.NoSuchBucket:
        raise click.ClickException(
            "One or more supplied buckets does not exist. Bucket names provided were: "
            f"source_bucket={source_bucket}, destination_bucket={destination_bucket}"
        )
    click.echo(
        f"Concatenated file {output_filename} succesfully created and moved to bucket "
        f"{destination_bucket}."
    )
