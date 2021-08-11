import boto3
from moto import mock_ses

from llama import ses


@mock_ses
def test_send_credit_card_slips_email():
    ses_client = boto3.client("ses", region_name="us-east-1")
    ses_client.verify_email_identity(EmailAddress="noreply@example.com")
    response = ses.SES().send_email(
        "Email subject",
        "<html/>",
        "attachment",
        "noreply@example.com",
        ["test@example.com"],
    )
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
