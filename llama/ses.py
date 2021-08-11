from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart

from boto3 import client


class SES:
    """An SES class that provides a generic boto3 SES client for interacting with SE
    objects, along with specific SES functionality necessary for llama scripts"""

    def __init__(self):
        self.client = client("ses", region_name="us-east-1")

    def send_email(
        self, subject, attachment_content, attachment_name, source_email, recipients
    ):
        """Send email via SES. Recipients parameter must be a list and not a str."""
        message = MIMEMultipart()
        message["Subject"] = subject
        attachment_object = MIMEApplication(attachment_content)
        attachment_object.add_header(
            "Content-Disposition", "attachment", filename=attachment_name
        )
        message.attach(attachment_object)
        response = self.client.send_raw_email(
            Source=source_email,
            Destinations=recipients,
            RawMessage={
                "Data": message.as_string(),
            },
        )
        return response
