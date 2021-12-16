import datetime
import json
import logging

import click

from llama import CONFIG, credit_card_slips, sap
from llama.alma import Alma_API_Client
from llama.email import Email
from llama.s3 import S3
from llama.sample_data import load_sample_data

logger = logging.getLogger(__name__)


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
    alma_api_key = CONFIG.get_alma_api_key("ALMA_API_ACQ_READ_KEY")
    alma_api_client = Alma_API_Client(alma_api_key)
    alma_api_client.set_content_headers("application/json", "application/json")
    credit_card_full_po_lines = (
        credit_card_slips.get_credit_card_full_po_lines_from_date(alma_api_client, date)
    )
    if len(credit_card_full_po_lines) > 0:
        po_line_dicts = credit_card_slips.create_po_line_dicts(
            alma_api_client, credit_card_full_po_lines
        )
        credit_card_slip_xml_data = credit_card_slips.xml_data_from_dicts(po_line_dicts)
    else:
        credit_card_slip_xml_data = (
            "<html><p>No credit card orders on this date</p></html>"
        )
    message = Email()
    message.populate(
        source_email,
        list(recipient_email),
        f"Credit card slips {date}",
        attachments=[
            {
                "content": credit_card_slip_xml_data,
                "filename": f"{date}_credit_card_slips.htm",
            }
        ],
    )
    response = message.send()
    logger.info(f'Email sent! Message ID: {response["MessageId"]}')


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


@cli.command()
@click.pass_context
def create_sandbox_sap_data(ctx):
    """Create sample data in the Alma sandbox instance.

    In order to run successfully, the sandbox Acquisitions read/write API key must be
    set in config (in .env if running locally, or in SSM if on stage). This command
    will not run in the production environment, and should never be run with production
    config values.
    """
    if CONFIG.ENV == "prod":
        logger.info(
            "This command may not be run in the production environment, aborting"
        )
        raise click.Abort()
    alma_key = CONFIG.get_alma_api_key("ALMA_API_ACQ_READ_WRITE_KEY")
    alma_client = Alma_API_Client(alma_key)
    alma_client.set_content_headers("application/json", "application/json")
    with open("sample-data/sample-sap-invoice-data.json") as f:
        contents = json.load(f)
    invoices_created = load_sample_data(alma_client, contents)
    logger.info(
        f"{invoices_created} sample invoices created and ready for manual approval "
        "in the Alma sandbox UI"
    )


@cli.command()
@click.option(
    "--final-run",
    is_flag=True,
    help="Flag to indicate this is a final run and should include all steps of the "
    "process. Default if this flag is not passed is to do a review run, which only "
    "creates and sends summary and report files for review by stakeholders. Note: some "
    "steps of a final run will not be completed unless the '--real-run' flag is also "
    "passed, however that will write data to external systems and should thus be used "
    "with caution. See '--real-run' option documentation for details.",
)
@click.option(
    "--real-run",
    is_flag=True,
    help="USE WITH CAUTION. If '--real-run' flag is passed, files will be emailed "
    "to stakeholders and, if the '--final-run' flag is also passed, invoices will be "
    "sent to SAP and marked as paid in Alma. If this flag is not passed, this command "
    "defaults to a dry run, in which files will not be emailed or sent to SAP, instead "
    "their contents will be logged for review, and invoices will also not be marked as "
    "paid in Alma.",
)
@click.pass_context
def sap_invoices(ctx, final_run, real_run):
    """Process invoices for payment via SAP.

    Retrieves "Waiting to be sent" invoices from Alma, extracts and formats data
    needed for submission to SAP for payment. If not a final run, creates and sends
    formatted review reports to Acquisitions staff. If a final run, creates and sends
    formatted cover sheets and summary reports to Acquisitions staff, submits data and
    control files to SAP, and marks invoices as paid in Alma after submission to SAP.
    """
    logger.info(
        f"Starting SAP invoices process with options:\n"
        f"    Date: {ctx.obj['today']}\n"
        f"    Final run: {final_run}\n"
        f"    Real run: {real_run}"
    )

    # Retrieve and sort invoices from Alma, log result or abort process if no invoices
    # retrieved
    alma_client = Alma_API_Client(CONFIG.get_alma_api_key("ALMA_API_ACQ_READ_KEY"))
    alma_client.set_content_headers("application/json", "application/json")
    invoice_records = sap.retrieve_sorted_invoices(alma_client)
    if len(invoice_records) > 0:
        logger.info(f"{len(invoice_records)} invoices retrieved from Alma")
    else:
        logger.info(
            "No invoices waiting to be sent in Alma, aborting SAP invoice process"
        )
        raise click.Abort()

    # Parse retrieved invoices and extract data needed for SAP
    parsed_invoices = sap.parse_invoice_records(alma_client, invoice_records)

    # Split invoices into monographs and serials
    monograph_invoices, serial_invoices = sap.split_invoices_by_field_value(
        parsed_invoices, "type", "monograph", "serial"
    )
    logger.info(f"{len(monograph_invoices)} monograph invoices retrieved and parsed.")
    logger.info(f"{len(serial_invoices)} serial invoices retrieved and parsed.")

    # Do the SAP run for monograph invoices, then serial invoices
    monograph_result = sap.run(
        monograph_invoices, "monograph", ctx.obj["today"], final_run, real_run
    )
    serial_result = sap.run(
        serial_invoices, "serial", ctx.obj["today"], final_run, real_run
    )

    # Log the final outcome
    logger.info(
        f"SAP invoice process completed for a {'final' if final_run else 'review'} "
        f"run\n"
        f"  {monograph_result['total invoices']} monograph invoices retrieved and "
        "processed:\n"
        f"    {monograph_result['sap invoices']} SAP monograph invoices\n"
        f"    {monograph_result['other invoices']} other payment monograph invoices\n"
        f"  {serial_result['total invoices']} serial invoices retrieved and "
        "processed\n"
        f"    {serial_result['sap invoices']} SAP serial invoices\n"
        f"    {serial_result['other invoices']} other payment serial invoices\n"
    )
