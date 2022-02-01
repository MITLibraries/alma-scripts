from email.message import EmailMessage
from email.policy import default
from typing import List, Optional

import boto3


class Email(EmailMessage):
    def __init__(self, policy=default):
        super().__init__(policy)

    def populate(
        self,
        from_address: str,
        to_addresses: str,
        subject: str,
        attachments: Optional[List[dict]] = None,
        body: Optional[str] = None,
        bcc: Optional[str] = None,
        cc: Optional[str] = None,
        reply_to: Optional[str] = None,
    ):
        """Populate Email message with addresses and subject.
        Optionally include attachments, body, cc, bcc, and reply-to.

        to_addresses, bcc, and cc parameters can take multiple email addresses as a
            single string of comma-separated values
        Attachments parameter should be structured as follows and must include all
        fields for each attachment:
        [
            {
                "content": "Contents of attachment as it would be written to a file-like
                    object",
                "filename": "File name to use for attachment, e.g. 'a_file.xml'"
            },
            {...repeat above for all attachments...}
        ]
        """
        self["From"] = from_address
        self["To"] = to_addresses
        self["Subject"] = subject
        if cc:
            self["Cc"] = cc
        if bcc:
            self["Bcc"] = bcc
        if reply_to:
            self["Reply-To"] = reply_to
        if body:
            self.set_content(body)
        if attachments:
            for attachment in attachments:
                self.add_attachment(
                    attachment["content"], filename=attachment["filename"]
                )

    def send(self):
        """Send email.

        Currently uses SES but could easily be switched out for another method if needed.
        """
        ses = boto3.client("ses", region_name="us-east-1")
        destinations = self["To"].split(",")
        if self["Cc"]:
            destinations.extend(self["Cc"].split(","))
        if self["Bcc"]:
            destinations.extend(self["Bcc"].split(","))
        response = ses.send_raw_email(
            Source=self["From"],
            Destinations=destinations,
            RawMessage={
                "Data": self.as_bytes(),
            },
        )
        return response
